"""Authentication blueprint — /auth/*

Covers:
  - Email + password registration, verification, login, logout
  - Forgot-password / reset-password
  - TOTP 2FA (optional, per-user)
  - OAuth SSO: Google, Microsoft (identity only — Gmail API OAuth is separate)
"""
import hashlib
import os
import secrets
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, urljoin

from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_user, logout_user, login_required
from authlib.integrations.flask_client import OAuth

from models import db, AuditLog, EmailToken, OAuthConnection, Plan, User, UserSession
from services.email_service import EmailService

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# Authlib OAuth registry — configured in create_app()
oauth = OAuth()

TRIAL_DAYS = 14
SESSION_TTL_DAYS_REMEMBER = 30
SESSION_TTL_HOURS_TRANSIENT = 24

# ── Internal helpers ──────────────────────────────────────────────────────────


def _hash(token: str) -> str:
    """SHA-256 hex digest — used for tokens stored in DB."""
    return hashlib.sha256(token.encode()).hexdigest()


def _safe_redirect(target: str) -> str:
    """Return target only if it is a same-origin relative URL, else /."""
    if not target:
        return url_for("index")
    ref = urlparse(request.host_url)
    test = urlparse(urljoin(request.host_url, target))
    if test.scheme in ("http", "https") and ref.netloc == test.netloc:
        return target
    return url_for("index")


def _audit(action: str, *, resource_type=None, resource_id=None, details=None, user_id=None):
    uid = user_id
    if uid is None and current_user and not current_user.is_anonymous:
        uid = current_user.id
    log = AuditLog(
        user_id=uid,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=request.remote_addr,
        user_agent=(request.headers.get("User-Agent") or "")[:255],
        details=details,
    )
    db.session.add(log)


def _create_db_session(user: User, remember: bool = False) -> str:
    """Persist a server-side session record and return the raw (unsaved) token."""
    raw = secrets.token_urlsafe(32)
    ttl = timedelta(days=SESSION_TTL_DAYS_REMEMBER if remember else 1)
    record = UserSession(
        user_id=user.id,
        session_token_hash=_hash(raw),
        expires_at=datetime.now(timezone.utc) + ttl,
        ip_address=request.remote_addr,
        user_agent=(request.headers.get("User-Agent") or "")[:255],
    )
    db.session.add(record)
    return raw


def _assign_trial(user: User):
    """Give a new user a 14-day trial at Growth-tier features."""
    growth = Plan.query.filter_by(name="growth").first()
    user.plan_id = growth.id if growth else None
    user.trial_expires_at = datetime.now(timezone.utc) + timedelta(days=TRIAL_DAYS)


def _complete_login(user: User, remember: bool = False):
    """Finalise login after all credential + MFA checks pass."""
    raw_token = _create_db_session(user, remember)
    # Store the raw token in the (Flask-signed) cookie session
    session["db_session_token"] = raw_token
    # Backward-compat: existing routes read session['user_id']
    session["user_id"] = user.id

    user.last_login_at = datetime.now(timezone.utc)
    _audit("user.login", resource_type="user", resource_id=user.id, user_id=user.id)
    db.session.commit()
    login_user(user, remember=remember)


# ── Registration ──────────────────────────────────────────────────────────────


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        name = request.form.get("name", "").strip()

        if not email or "@" not in email or "." not in email.split("@")[-1]:
            flash("Please enter a valid email address.", "error")
            return render_template("auth/register.html")

        if len(password) < 12 or len(password) > 128:
            flash("Password must be between 12 and 128 characters.", "error")
            return render_template("auth/register.html")

        # Constant-time: don't reveal whether email is taken
        if User.query.filter_by(email=email).first():
            flash(
                "If that email is available you'll receive a verification link shortly.",
                "info",
            )
            return render_template("auth/register.html")

        user = User(email=email, display_name=name or email.split("@")[0])
        user.set_password(password)
        _assign_trial(user)
        db.session.add(user)
        db.session.flush()  # get user.id before adding dependent records

        raw = secrets.token_urlsafe(32)
        db.session.add(
            EmailToken(
                user_id=user.id,
                token_hash=_hash(raw),
                purpose="verify_email",
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            )
        )

        _audit("user.register", resource_type="user", resource_id=user.id, user_id=user.id)
        db.session.commit()

        verify_url = url_for("auth.verify_email", token=raw, _external=True)
        EmailService.send_verification(email, user.display_name, verify_url)

        flash("Check your email for a verification link.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


# ── Email verification ────────────────────────────────────────────────────────


@auth_bp.route("/verify-email")
def verify_email():
    token = request.args.get("token", "")
    if not token:
        flash("Invalid verification link.", "error")
        return redirect(url_for("auth.login"))

    record = EmailToken.query.filter_by(
        token_hash=_hash(token), purpose="verify_email"
    ).first()

    if not record or not record.is_valid:
        flash("Verification link is invalid or has expired.", "error")
        return redirect(url_for("auth.login"))

    record.used_at = datetime.now(timezone.utc)
    record.user.is_verified = True
    _audit("user.verify_email", resource_type="user", resource_id=record.user_id,
           user_id=record.user_id)
    db.session.commit()

    flash("Email verified — you can now log in.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/unverified")
def unverified():
    return render_template("auth/unverified.html")


# ── Login ─────────────────────────────────────────────────────────────────────


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(email=email).first()

        # Timing-safe: always run check_password even on miss (dummy hash)
        dummy = b"$2b$12$000000000000000000000000000000000000000000000000000000"
        valid = user.check_password(password) if user else (
            __import__("bcrypt").checkpw(b"x", dummy) and False
        )

        if not valid or not user:
            _audit("user.login_failed", details={"email": email, "reason": "bad_credentials"})
            db.session.commit()
            flash("Invalid email or password.", "error")
            return render_template("auth/login.html")

        if not user.is_active:
            flash("This account has been disabled. Please contact support.", "error")
            return render_template("auth/login.html")

        if not user.is_verified:
            flash("Please verify your email before logging in.", "warning")
            return render_template("auth/login.html")

        if user.mfa_enabled:
            session["mfa_pending_user_id"] = user.id
            session["mfa_remember"] = remember
            return redirect(url_for("auth.mfa_verify"))

        _complete_login(user, remember)
        return redirect(_safe_redirect(request.args.get("next", "")))

    return render_template("auth/login.html")


# ── MFA (TOTP) ────────────────────────────────────────────────────────────────


@auth_bp.route("/mfa", methods=["GET", "POST"])
def mfa_verify():
    pending_id = session.get("mfa_pending_user_id")
    if not pending_id:
        return redirect(url_for("auth.login"))

    user = User.query.get(pending_id)
    if not user:
        session.pop("mfa_pending_user_id", None)
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        import pyotp  # type: ignore[import]
        code = request.form.get("code", "").strip().replace(" ", "")
        totp = pyotp.TOTP(user.mfa_secret)
        if totp.verify(code, valid_window=1):
            session.pop("mfa_pending_user_id", None)
            remember = session.pop("mfa_remember", False)
            _complete_login(user, remember)
            return redirect(url_for("index"))
        _audit("user.mfa_failed", resource_type="user", resource_id=user.id, user_id=user.id)
        db.session.commit()
        flash("Invalid code. Please try again.", "error")

    return render_template("auth/mfa_verify.html")


@auth_bp.route("/mfa/setup", methods=["GET", "POST"])
@login_required
def mfa_setup():
    """TOTP enrolment — generates a secret and QR code."""
    import pyotp
    import qrcode
    import io
    import base64

    if request.method == "POST":
        secret = session.pop("mfa_pending_secret", None)
        if not secret:
            flash("Session expired. Please restart MFA setup.", "error")
            return redirect(url_for("auth.mfa_setup"))
        code = request.form.get("code", "").strip()
        totp = pyotp.TOTP(secret)
        if not totp.verify(code, valid_window=1):
            flash("Code didn't match. Try again.", "error")
            return redirect(url_for("auth.mfa_setup"))
        current_user.mfa_secret = secret
        current_user.mfa_enabled = True
        _audit("user.mfa_enabled", resource_type="user", resource_id=current_user.id)
        db.session.commit()
        flash("Two-factor authentication is now active.", "success")
        return redirect(url_for("auth.account"))

    secret = pyotp.random_base32()
    session["mfa_pending_secret"] = secret  # never round-trip through client
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=current_user.email, issuer_name="Outreach AI")
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    return render_template("auth/mfa_setup.html", secret=secret, qr_b64=qr_b64)


@auth_bp.route("/mfa/disable", methods=["POST"])
@login_required
def mfa_disable():
    import pyotp
    code = request.form.get("code", "").strip()
    totp = pyotp.TOTP(current_user.mfa_secret)
    if not totp.verify(code, valid_window=1):
        flash("Invalid TOTP code. 2FA was not disabled.", "error")
        return redirect(url_for("auth.account"))
    current_user.mfa_secret = None
    current_user.mfa_enabled = False
    _audit("user.mfa_disabled", resource_type="user", resource_id=current_user.id)
    db.session.commit()
    flash("Two-factor authentication disabled.", "info")
    return redirect(url_for("auth.account"))


# ── Logout ────────────────────────────────────────────────────────────────────


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    raw_token = session.get("db_session_token")
    if raw_token:
        record = UserSession.query.filter_by(session_token_hash=_hash(raw_token)).first()
        if record:
            record.revoked = True

    _audit("user.logout", resource_type="user", resource_id=current_user.id)
    db.session.commit()
    logout_user()
    session.clear()
    return redirect(url_for("auth.login"))


# ── Forgot / reset password ───────────────────────────────────────────────────


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()

        if user and user.is_active:
            raw = secrets.token_urlsafe(32)
            db.session.add(
                EmailToken(
                    user_id=user.id,
                    token_hash=_hash(raw),
                    purpose="reset_password",
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
                )
            )
            _audit("user.password_reset_requested", resource_type="user",
                   resource_id=user.id, user_id=user.id)
            db.session.commit()

            reset_url = url_for("auth.reset_password", token=raw, _external=True)
            EmailService.send_password_reset(user.email, user.display_name or user.email, reset_url)

        # Same message regardless — prevents email enumeration
        flash(
            "If an account with that email exists you'll receive a reset link shortly.",
            "info",
        )
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    token = request.args.get("token", "")
    record = EmailToken.query.filter_by(
        token_hash=_hash(token), purpose="reset_password"
    ).first()

    if not record or not record.is_valid:
        flash("This reset link is invalid or has expired.", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        if len(password) < 12:
            flash("Password must be at least 12 characters.", "error")
            return render_template("auth/reset_password.html", token=token)

        record.user.set_password(password)
        record.used_at = datetime.now(timezone.utc)

        # Revoke all existing sessions (password changed — force re-auth everywhere)
        UserSession.query.filter_by(
            user_id=record.user_id, revoked=False
        ).update({"revoked": True})

        _audit("user.password_reset", resource_type="user", resource_id=record.user_id,
               user_id=record.user_id)
        db.session.commit()
        flash("Password updated. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)


# ── Account settings ──────────────────────────────────────────────────────────


@auth_bp.route("/account")
@login_required
def account():
    return render_template("auth/account.html")


# ── OAuth: Google (SSO identity only) ────────────────────────────────────────


@auth_bp.route("/oauth/google")
def oauth_google():
    redirect_uri = url_for("auth.oauth_google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route("/oauth/google/callback")
def oauth_google_callback():
    try:
        token = oauth.google.authorize_access_token()
    except Exception:
        current_app.logger.exception("Google OAuth token exchange failed")
        flash("Google sign-in failed. Please try again.", "error")
        return redirect(url_for("auth.login"))

    userinfo = token.get("userinfo") or {}
    return _handle_oauth_callback(
        provider="google",
        provider_user_id=userinfo.get("sub", ""),
        email=userinfo.get("email", ""),
        name=userinfo.get("name", ""),
        token=token,
    )


# ── OAuth: Microsoft ──────────────────────────────────────────────────────────


@auth_bp.route("/oauth/microsoft")
def oauth_microsoft():
    redirect_uri = url_for("auth.oauth_microsoft_callback", _external=True)
    return oauth.microsoft.authorize_redirect(redirect_uri)


@auth_bp.route("/oauth/microsoft/callback")
def oauth_microsoft_callback():
    try:
        token = oauth.microsoft.authorize_access_token()
    except Exception:
        current_app.logger.exception("Microsoft OAuth token exchange failed")
        flash("Microsoft sign-in failed. Please try again.", "error")
        return redirect(url_for("auth.login"))

    try:
        resp = oauth.microsoft.get("https://graph.microsoft.com/v1.0/me")
        profile = resp.json()
    except Exception:
        profile = {}

    return _handle_oauth_callback(
        provider="microsoft",
        provider_user_id=profile.get("id", ""),
        email=profile.get("mail") or profile.get("userPrincipalName", ""),
        name=profile.get("displayName", ""),
        token=token,
    )


# ── Shared OAuth callback logic ───────────────────────────────────────────────


def _handle_oauth_callback(
    provider: str,
    provider_user_id: str,
    email: str,
    name: str,
    token: dict,
):
    if not provider_user_id:
        flash("Sign-in failed: provider did not return a user ID.", "error")
        return redirect(url_for("auth.login"))

    email = (email or "").lower().strip()

    connection = OAuthConnection.query.filter_by(
        provider=provider, provider_user_id=str(provider_user_id)
    ).first()

    if connection:
        user = connection.user
        connection.access_token = token.get("access_token")
        connection.refresh_token = token.get("refresh_token")
        if token.get("expires_at"):
            connection.token_expires_at = datetime.fromtimestamp(
                token["expires_at"], tz=timezone.utc
            )
    else:
        user = User.query.filter_by(email=email).first() if email else None
        if not user:
            user = User(
                email=email,
                display_name=name or (email.split("@")[0] if email else "User"),
                is_verified=True,   # OAuth provider has verified the email
            )
            _assign_trial(user)
            db.session.add(user)
            db.session.flush()

        scopes = token.get("scope", "")
        if isinstance(scopes, list):
            scopes = " ".join(scopes)

        connection = OAuthConnection(
            user_id=user.id,
            provider=provider,
            provider_user_id=str(provider_user_id),
            provider_email=email,
            access_token=token.get("access_token"),
            refresh_token=token.get("refresh_token"),
            scopes=scopes,
        )
        if token.get("expires_at"):
            connection.token_expires_at = datetime.fromtimestamp(
                token["expires_at"], tz=timezone.utc
            )
        db.session.add(connection)

    if not user.is_active:
        db.session.rollback()
        flash("This account has been disabled. Please contact support.", "error")
        return redirect(url_for("auth.login"))

    _audit("user.login_oauth", resource_type="user", resource_id=user.id,
           details={"provider": provider}, user_id=user.id)
    _complete_login(user, remember=True)
    return redirect(_safe_redirect(request.args.get("next", "")))
