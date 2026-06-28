#!/usr/bin/env python3
"""
Flask Web Application for Email Outreach Automation
Multi-tenant, auth-gated. All data is scoped per authenticated user.
"""

import csv
import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    session,
    url_for,
)
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Allow OAuth over HTTP for local development only
if os.environ.get("FLASK_ENV", "development") != "production":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

from config import get_config
from models import db, User
from auth import auth_bp, oauth
from middleware import require_auth, require_plan, user_data_path
from seed_plans import seed_plans_command

# ── Existing integrations ─────────────────────────────────────────────────────
from workflow_orchestrator import WorkflowOrchestrator
from gmail_drafts_manager import GmailDraftsManager
from gmail_oauth import GmailOAuth

try:
    from linkedin_client import LinkedInClient
    LINKEDIN_AVAILABLE = True
except ImportError:
    LINKEDIN_AVAILABLE = False

ALLOWED_EXTENSIONS = {"csv"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ── App factory ───────────────────────────────────────────────────────────────

def create_app():
    application = Flask(__name__)
    application.wsgi_app = ProxyFix(application.wsgi_app, x_proto=1, x_host=1)
    application.config.from_object(get_config())

    # ── Extensions ────────────────────────────────────────────────────────────
    db.init_app(application)
    Migrate(application, db)
    CSRFProtect(application)

    limiter = Limiter(
        get_remote_address,
        app=application,
        storage_uri=application.config.get("RATELIMIT_STORAGE_URI", "memory://"),
        default_limits=["200 per day", "50 per hour"],
    )
    # Tighter limits on auth endpoints
    limiter.limit("10 per minute")(auth_bp)

    # Flask-Login
    login_manager = LoginManager(application)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please sign in to continue."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    # Authlib OAuth (Google + Microsoft SSO)
    oauth.init_app(application)
    oauth.register(
        name="google",
        client_id=application.config.get("GOOGLE_CLIENT_ID"),
        client_secret=application.config.get("GOOGLE_CLIENT_SECRET"),
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
    tenant = application.config.get("MICROSOFT_TENANT_ID", "common")
    oauth.register(
        name="microsoft",
        client_id=application.config.get("MICROSOFT_CLIENT_ID"),
        client_secret=application.config.get("MICROSOFT_CLIENT_SECRET"),
        server_metadata_url=(
            f"https://login.microsoftonline.com/{tenant}/v2.0/.well-known/openid-configuration"
        ),
        client_kwargs={"scope": "openid email profile User.Read"},
    )

    # ── Blueprints ────────────────────────────────────────────────────────────
    application.register_blueprint(auth_bp)

    # ── CLI commands ──────────────────────────────────────────────────────────
    application.cli.add_command(seed_plans_command)

    # ── Security headers ──────────────────────────────────────────────────────
    @application.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if os.environ.get("FLASK_ENV") == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response

    return application


app = create_app()

# ── Gmail OAuth (initialised after app) ───────────────────────────────────────
gmail_oauth = GmailOAuth(app)

# LinkedIn client
linkedin_client = None
if LINKEDIN_AVAILABLE:
    try:
        linkedin_client = LinkedInClient()
    except Exception as e:
        app.logger.warning("LinkedIn client init failed: %s", e)


# ── Per-user file path helpers ────────────────────────────────────────────────

def _uploads_dir() -> Path:
    """Return (and create) the current user's uploads directory."""
    return user_data_path(current_user.id, "uploads")


def _campaigns_dir() -> Path:
    """Return (and create) the current user's campaigns directory."""
    return user_data_path(current_user.id, "campaigns")


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def safe_session_path(raw_path, *_ignored_bases):
    """Resolve a session-stored path and verify it stays within the
    current user's data directory. Replaces the old multi-base variant."""
    if not raw_path or not current_user.is_authenticated:
        return None
    try:
        user_root = user_data_path(current_user.id)
        resolved = Path(raw_path).resolve()
        if str(resolved).startswith(str(user_root)):
            return resolved
    except (ValueError, OSError):
        pass
    app.logger.warning("Path boundary violation: %s", raw_path)
    return None


# ── Static / misc ─────────────────────────────────────────────────────────────

@app.route("/favicon.ico")
def favicon():
    ico = os.path.join(app.root_path, "static", "favicon.ico")
    if os.path.exists(ico):
        return send_from_directory(
            os.path.join(app.root_path, "static"),
            "favicon.ico",
            mimetype="image/vnd.microsoft.icon",
        )
    return ("", 204)


@app.route("/clear")
@require_auth
def clear_session():
    # Preserve auth-related session keys; only clear workflow state
    for key in ("csv_file", "cleaned_csv_file", "campaign_results",
                 "campaign_id", "removed_rows", "pending_drafts",
                 "oauth_state", "oauth_code_verifier"):
        session.pop(key, None)
    return redirect(url_for("index"))


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route("/")
@require_auth
def index():
    return render_template("index.html")


# ── CSV upload & validation ───────────────────────────────────────────────────

@app.route("/upload", methods=["GET", "POST"])
@require_auth
def upload_csv():
    if request.method == "POST":
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": "No file selected"}), 400

        if not (file and allowed_file(file.filename)):
            return jsonify({"error": "Only .csv files are allowed"}), 400

        # Check plan contact limit (we'll verify the actual count after parse)
        uploads = _uploads_dir()
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = uploads / unique_filename
        file.save(filepath)

        session["csv_file"] = str(filepath)
        session["original_filename"] = filename

        contacts = []
        total = 0
        with open(filepath, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                total = i + 1
                if i < 5:
                    contacts.append(row)

        # Enforce plan contact limit
        limit = current_user.get_feature("max_contacts_per_campaign")
        if limit and limit > 0 and total > limit:
            filepath.unlink(missing_ok=True)
            session.pop("csv_file", None)
            return jsonify({
                "error": (
                    f"Your {current_user.plan.display_name} plan allows up to {limit} contacts "
                    f"per campaign. This file has {total}. Please upgrade or reduce the file."
                ),
                "upgrade_required": True,
            }), 402

        return jsonify({
            "success": True,
            "filename": filename,
            "preview": contacts,
            "total_rows": total,
            "redirect": url_for("validate_csv"),
        })

    return render_template("upload.html")


@app.route("/validate")
@require_auth
def validate_csv():
    if "csv_file" not in session:
        return redirect(url_for("upload_csv"))
    csv_file = session.get("csv_file")
    validation_results = _validate_csv_file(csv_file)
    return render_template("validate.html", validation=validation_results)


@app.route("/process-validated", methods=["POST"])
@require_auth
def process_validated():
    if "csv_file" not in session:
        return jsonify({"error": "No CSV file in session"}), 400

    data = request.json
    removed_rows = data.get("removed_rows", [])
    session["removed_rows"] = removed_rows
    cleaned = _create_cleaned_csv(session["csv_file"], removed_rows)
    session["cleaned_csv_file"] = str(cleaned)
    return jsonify({"success": True, "redirect": url_for("campaign_setup")})


@app.route("/campaign-setup")
@require_auth
def campaign_setup():
    if "cleaned_csv_file" not in session and "csv_file" not in session:
        return redirect(url_for("upload_csv"))
    csv_file = session.get("cleaned_csv_file", session.get("csv_file"))
    contact_count = _count_csv_contacts(csv_file)
    return render_template("campaign_setup.html", contact_count=contact_count)


# ── CSV helpers ───────────────────────────────────────────────────────────────

def _create_cleaned_csv(original_path: str, removed_row_ids: list) -> Path:
    removed = set()
    for row_id in removed_row_ids:
        if row_id.startswith("row_"):
            try:
                removed.add(int(row_id.split("_")[1]))
            except (IndexError, ValueError):
                pass

    uploads = _uploads_dir()
    cleaned_path = uploads / f"cleaned_{os.path.basename(original_path)}"

    with open(original_path, "r", encoding="utf-8-sig") as infile:
        reader = csv.reader(infile)
        with open(cleaned_path, "w", newline="", encoding="utf-8") as outfile:
            writer = csv.writer(outfile)
            writer.writerow(next(reader))
            for row_num, row in enumerate(reader, start=2):
                if row_num not in removed:
                    writer.writerow(row)
    return cleaned_path


def _count_csv_contacts(csv_path: str) -> int:
    try:
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader)
            return sum(1 for _ in reader)
    except Exception:
        return 0


def _validate_csv_file(filepath: str) -> dict:
    email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    valid_records, invalid_records, seen_emails = [], [], set()

    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            errors = []
            row_data = {}
            for key, value in row.items():
                if not key:
                    continue
                ck = key.lower().strip()
                if "first" in ck and "name" in ck:
                    row_data["first_name"] = value
                elif "last" in ck and "name" in ck:
                    row_data["last_name"] = value
                elif "account" in ck:
                    row_data["company"] = value
                else:
                    row_data[ck] = value

            if "first_name" in row_data and "last_name" in row_data and "name" not in row_data:
                row_data["name"] = f"{row_data.get('first_name','')} {row_data.get('last_name','')}".strip()

            if not row_data.get("name") or len(row_data["name"].strip()) < 2:
                errors.append("Missing or invalid name (minimum 2 characters)")

            email = row_data.get("email", "").strip()
            if not email:
                errors.append("Missing email address")
            elif not email_regex.match(email):
                errors.append(f"Invalid email format: {email}")
            elif email in seen_emails:
                errors.append(f"Duplicate email: {email}")
            else:
                seen_emails.add(email)

            if not row_data.get("company", "").strip():
                errors.append("Missing company name")

            record = {
                "row_number": row_num,
                "row_id": f"row_{row_num}",
                "data": {
                    "name": row_data.get("name", ""),
                    "email": email,
                    "company": row_data.get("company", ""),
                    "title": row_data.get("title", ""),
                },
                "errors": errors,
            }
            if errors:
                invalid_records.append(record)
            else:
                valid_records.append(record["data"])

    return {
        "total_records": len(valid_records) + len(invalid_records),
        "valid_count": len(valid_records),
        "invalid_records": invalid_records,
        "valid_preview": valid_records,
    }


# ── Email generation & review ─────────────────────────────────────────────────

@app.route("/generate", methods=["POST"])
@require_auth
def generate_emails():
    csv_file = safe_session_path(
        session.get("cleaned_csv_file", session.get("csv_file"))
    )
    if not csv_file:
        return jsonify({"error": "No CSV file uploaded"}), 400

    try:
        data = request.json
        raw_name = data.get(
            "campaign_name",
            f"Campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        )
        campaign_name = raw_name.replace("/", "-").replace("\\", "-")
        campaign_settings = {
            "goal": data.get("campaign_goal", "first_meeting"),
            "tone": data.get("tone", "professional"),
            "length": data.get("email_length", "medium"),
            "message": data.get("message", ""),
            # Write campaign output to user's campaigns directory
            "output_dir": str(_campaigns_dir()),
        }

        user_id = current_user.id

        def linkedin_enrichment_func(contact_info):
            try:
                if not linkedin_client or not linkedin_client.is_configured():
                    return None
                token_key = f"linkedin_token_{user_id}"
                token_info = session.get(token_key)
                if not token_info:
                    return None
                linkedin_client.access_token = token_info.get("access_token")
                return linkedin_client.enhance_contact_with_linkedin(contact_info)
            except Exception as e:
                app.logger.error("LinkedIn enrichment failed: %s", e)
                return None

        orchestrator = WorkflowOrchestrator(linkedin_enrichment_func=linkedin_enrichment_func)
        campaign_id = str(uuid.uuid4())
        session["campaign_id"] = campaign_id
        os.environ["AUTO_APPROVE_EMAILS"] = "true"

        results = orchestrator.run_campaign(
            csv_file=csv_file,
            campaign_name=campaign_name,
            campaign_settings=campaign_settings,
        )
        os.environ.pop("AUTO_APPROVE_EMAILS", None)

        if results and "campaign_file" in results:
            campaign_file = results["campaign_file"]
            # If orchestrator wrote outside user dir, move it in
            campaign_path = Path(campaign_file)
            user_campaigns = _campaigns_dir()
            if not str(campaign_path.resolve()).startswith(str(user_campaigns)):
                dest = user_campaigns / campaign_path.name
                campaign_path.rename(dest)
                campaign_file = str(dest)

            session["campaign_results"] = campaign_file
            approved = results.get("approved_emails", [])
            template_count = sum(
                1 for e in approved
                if e.get("metadata", {}).get("generation_method") == "template"
            )
            resp = {
                "success": True,
                "campaign_id": campaign_id,
                "emails_generated": len(approved),
                "redirect": url_for("review_emails"),
            }
            if template_count:
                resp["template_warning"] = {
                    "template_count": template_count,
                    "ai_count": len(approved) - template_count,
                    "message": (
                        f"{template_count} emails used templates. "
                        "Set ANTHROPIC_API_KEY for full AI generation."
                    ),
                }
            return jsonify(resp)

        error_msg = (results or {}).get("error") or "No valid contacts found in CSV."
        return jsonify({"error": error_msg}), 500

    except Exception:
        app.logger.exception("Error generating emails")
        return jsonify({"error": "Email generation failed. Please try again."}), 500


@app.route("/review")
@require_auth
def review_emails():
    if "campaign_results" not in session:
        return redirect(url_for("upload_csv"))
    campaign_file = safe_session_path(session.get("campaign_results"))
    if not campaign_file or not campaign_file.exists():
        return redirect(url_for("upload_csv"))
    with open(campaign_file) as f:
        campaign_data = json.load(f)
    return render_template("review.html", campaign=campaign_data)


@app.route("/approve", methods=["POST"])
@require_auth
def approve_emails():
    try:
        data = request.json
        approved_ids = data.get("approved_ids", [])
        create_drafts = data.get("create_drafts", False)

        if not approved_ids:
            return jsonify({"error": "No emails selected"}), 400

        campaign_file = safe_session_path(session.get("campaign_results"))
        if not campaign_file or not campaign_file.exists():
            return jsonify({"error": "Campaign not found"}), 404

        with open(campaign_file) as f:
            campaign_data = json.load(f)

        all_emails = campaign_data.get("approved_emails", [])
        approved_emails = []
        for id_str in approved_ids:
            try:
                idx = int(id_str) - 1
                if 0 <= idx < len(all_emails):
                    approved_emails.append(all_emails[idx])
            except (ValueError, IndexError):
                for email in all_emails:
                    if email.get("id") == id_str:
                        approved_emails.append(email)
                        break

        campaign_data["approved_emails"] = approved_emails
        campaign_data["approval_timestamp"] = datetime.now().isoformat()
        with open(str(campaign_file), "w") as f:
            json.dump(campaign_data, f, indent=2)

        drafts_created, draft_error = [], None
        if create_drafts:
            user_id = current_user.id
            if not gmail_oauth.user_has_gmail_connected(user_id):
                session["pending_drafts"] = {
                    "campaign_file": str(campaign_file),
                    "approved_ids": approved_ids,
                }
                return jsonify({
                    "success": False,
                    "needs_gmail_auth": True,
                    "auth_url": url_for("gmail_connect"),
                    "message": "Gmail connection required. You will be redirected.",
                })
            for email in approved_emails:
                to_email = (
                    email.get("contact_context", {}).get("contact", {}).get("email")
                    or email.get("to_email")
                )
                if not to_email:
                    continue
                draft_id, error = gmail_oauth.create_draft_from_content(
                    user_id, to_email, email.get("email_content")
                )
                if draft_id:
                    drafts_created.append(draft_id)
                elif error and not draft_error:
                    draft_error = error

        resp = {
            "success": True,
            "approved_count": len(approved_emails),
            "drafts_created": len(drafts_created),
            "redirect": url_for("campaign_complete"),
        }
        if draft_error:
            resp["draft_error"] = draft_error
        return jsonify(resp)

    except Exception:
        app.logger.exception("Error approving emails")
        return jsonify({"error": "Failed to approve emails. Please try again."}), 500


@app.route("/complete")
@require_auth
def campaign_complete():
    campaign_file = safe_session_path(session.get("campaign_results"))
    if not campaign_file or not campaign_file.exists():
        return redirect(url_for("index"))
    with open(campaign_file) as f:
        campaign_data = json.load(f)
    for key in ("csv_file", "cleaned_csv_file", "campaign_results",
                 "campaign_id", "removed_rows", "pending_drafts"):
        session.pop(key, None)
    return render_template("complete.html", campaign=campaign_data)


# ── Campaign history ──────────────────────────────────────────────────────────

@app.route("/campaigns")
@require_auth
def list_campaigns():
    campaigns = []
    campaigns_dir = _campaigns_dir()
    for file in sorted(campaigns_dir.glob("*.json"),
                        key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            with open(file) as f:
                data = json.load(f)
            info = data.get("campaign_info", {})
            name = info.get("name") or data.get("campaign_name") or file.stem.replace("_", " ")
            ts = info.get("timestamp") or data.get("timestamp", "")
            if ts and len(ts) >= 13:
                try:
                    formatted_date = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]} {ts[9:11]}:{ts[11:13]}"
                except (IndexError, TypeError):
                    formatted_date = ts
            else:
                formatted_date = datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            campaigns.append({
                "name": name,
                "date": formatted_date,
                "emails_count": len(data.get("approved_emails", [])),
                "file": file.name,
                "file_stem": file.stem,
            })
        except Exception as e:
            app.logger.warning("Error reading campaign %s: %s", file, e)
    return render_template("campaigns.html", campaigns=campaigns)


@app.route("/campaign/<campaign_id>")
@require_auth
def view_campaign(campaign_id):
    if not re.fullmatch(r"[a-zA-Z0-9_\-]{1,128}", campaign_id):
        return "Invalid campaign ID", 400
    campaigns_dir = _campaigns_dir()
    json_file = next((f for f in campaigns_dir.glob("*.json") if f.stem == campaign_id), None)
    if not json_file:
        return "Campaign not found", 404
    with open(json_file) as f:
        campaign_data = json.load(f)
    return render_template("view_campaign.html", campaign=campaign_data, campaign_id=campaign_id)


@app.route("/download/<filename>")
@require_auth
def download_campaign(filename):
    safe = secure_filename(filename)
    file_path = _campaigns_dir() / safe
    if file_path.exists():
        return send_file(file_path, as_attachment=True, download_name=f"campaign_{safe}")
    return "File not found", 404


# ── API status ────────────────────────────────────────────────────────────────

@app.route("/api/status")
@require_auth
def api_status():
    return jsonify({
        "anthropic_api_key": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "gmail_credentials": os.path.exists("credentials.json"),
        "system_ready": True,
    })


# ── Gmail OAuth routes ────────────────────────────────────────────────────────

@app.route("/gmail/connect")
@require_auth
def gmail_connect():
    try:
        user_id = current_user.id
        scheme = "https" if os.environ.get("FLASK_ENV") == "production" else "http"
        redirect_uri = url_for("gmail_callback", _external=True, _scheme=scheme)
        result = gmail_oauth.get_authorization_url(user_id, redirect_uri)
        if not result or result == (None, None):
            return jsonify({"error": "Gmail OAuth not configured."}), 500
        auth_url, state, code_verifier = result
        if not auth_url:
            return jsonify({"error": "Gmail OAuth not configured."}), 500
        session["oauth_state"] = state
        if code_verifier:
            session["oauth_code_verifier"] = code_verifier
        return redirect(auth_url)
    except Exception:
        app.logger.exception("Gmail connect error")
        return jsonify({"error": "Gmail OAuth initialization failed."}), 500


@app.route("/gmail/callback")
@require_auth
def gmail_callback():
    try:
        if "oauth_state" not in session:
            return jsonify({"error": "Invalid session state"}), 400
        state = session.get("oauth_state")
        user_id = current_user.id
        scheme = "https" if os.environ.get("FLASK_ENV") == "production" else "http"
        redirect_uri = url_for("gmail_callback", _external=True, _scheme=scheme)
        authorization_response = request.url
        if os.environ.get("FLASK_ENV") == "production" and authorization_response.startswith("http://"):
            authorization_response = "https://" + authorization_response[7:]
        code_verifier = session.pop("oauth_code_verifier", None)
        success = gmail_oauth.handle_callback(
            user_id, authorization_response, state, redirect_uri, code_verifier=code_verifier
        )
        if success:
            if "pending_drafts" in session:
                session.pop("pending_drafts")
                return redirect(url_for("resume_draft_creation"))
            return redirect(url_for("index", connected="gmail"))
        return redirect(url_for("gmail_status", status="error"))
    except Exception:
        app.logger.exception("Gmail callback error")
        return jsonify({"error": "Gmail OAuth callback failed."}), 500


@app.route("/gmail/status")
@require_auth
def gmail_status():
    status = request.args.get("status", "unknown")
    connected = gmail_oauth.user_has_gmail_connected(current_user.id)
    return render_template("gmail_status.html", status=status, connected=connected)


@app.route("/gmail/disconnect")
@require_auth
def gmail_disconnect():
    gmail_oauth.revoke_user_credentials(current_user.id)
    return redirect(url_for("gmail_status", status="disconnected"))


@app.route("/resume_draft_creation")
@require_auth
def resume_draft_creation():
    pending = session.get("pending_drafts")
    campaign_file = pending.get("campaign_file") if pending else session.get("campaign_results")
    approved_ids = pending.get("approved_ids") if pending else None
    if campaign_file and Path(campaign_file).exists():
        return render_template("resume_drafts.html",
                                campaign_file=campaign_file, approved_ids=approved_ids)
    return redirect(url_for("index"))


@app.route("/api/gmail/status")
@require_auth
def api_gmail_status():
    connected = gmail_oauth.user_has_gmail_connected(current_user.id)
    return jsonify({"connected": connected})


# ── LinkedIn OAuth routes ─────────────────────────────────────────────────────

@app.route("/linkedin/connect")
@require_auth
@require_plan("linkedin_enabled", "LinkedIn enrichment requires the Growth plan or higher.")
def linkedin_connect():
    if not linkedin_client or not linkedin_client.is_configured():
        return jsonify({"error": "LinkedIn OAuth not configured."}), 500
    user_id = current_user.id
    scheme = "https" if os.environ.get("FLASK_ENV") == "production" else "http"
    redirect_uri = url_for("linkedin_callback", _external=True, _scheme=scheme)
    try:
        auth_url = linkedin_client.get_authorization_url(redirect_uri, state=user_id)
        return redirect(auth_url)
    except Exception:
        app.logger.exception("LinkedIn connect error")
        return jsonify({"error": "Failed to create LinkedIn auth URL."}), 500


@app.route("/linkedin/callback")
@require_auth
def linkedin_callback():
    if not linkedin_client:
        return "LinkedIn integration not available", 500
    user_id = current_user.id
    code = request.args.get("code")
    state = request.args.get("state")
    error = request.args.get("error")
    if error:
        return f"LinkedIn authorization failed: {error}", 400
    if not code:
        return "Authorization code not received", 400
    if state != user_id:
        return "Invalid state parameter", 400
    scheme = "https" if os.environ.get("FLASK_ENV") == "production" else "http"
    redirect_uri = url_for("linkedin_callback", _external=True, _scheme=scheme)
    try:
        token_data = linkedin_client.exchange_code_for_token(code, redirect_uri)
        session[f"linkedin_token_{user_id}"] = {
            "access_token": token_data.get("access_token"),
            "expires_in": token_data.get("expires_in"),
            "connected_at": datetime.now().isoformat(),
        }
        return redirect(url_for("index", connected="linkedin"))
    except Exception:
        app.logger.exception("LinkedIn callback error")
        return "Failed to complete LinkedIn authorization.", 500


@app.route("/linkedin/status")
@require_auth
def linkedin_status():
    user_id = current_user.id
    token_info = session.get(f"linkedin_token_{user_id}")
    connected = bool(token_info and token_info.get("access_token"))
    return render_template("linkedin_status.html",
                            status=request.args.get("status", "unknown"),
                            connected=connected, token_info=token_info)


@app.route("/linkedin/disconnect")
@require_auth
def linkedin_disconnect():
    session.pop(f"linkedin_token_{current_user.id}", None)
    return redirect(url_for("linkedin_status", status="disconnected"))


@app.route("/api/linkedin/status")
@require_auth
def api_linkedin_status():
    user_id = current_user.id
    token_info = session.get(f"linkedin_token_{user_id}")
    connected = bool(token_info and token_info.get("access_token"))
    return jsonify({
        "connected": connected,
        "available": LINKEDIN_AVAILABLE,
        "configured": linkedin_client.is_configured() if linkedin_client else False,
    })


# ── Dev entrypoint ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🚀 Email Outreach Web App — http://127.0.0.1:8080")
    if not os.environ.get("ANTHROPIC_API_KEY", "").startswith("sk-"):
        print("⚠️  Set ANTHROPIC_API_KEY for AI generation")
    app.run(
        debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true",
        host="127.0.0.1",
        port=8080,
    )
