"""Auth decorators and per-user data isolation helpers."""
import os
import re
from functools import wraps
from pathlib import Path

from flask import abort, jsonify, redirect, request, url_for
from flask_login import current_user

_USER_DATA_ROOT = Path(os.environ.get("USER_DATA_DIR", "user_data"))


# ── Filesystem isolation ──────────────────────────────────────────────────────

def user_data_path(user_id: str, *subpath: str) -> Path:
    """Return (and create) a path scoped to one user's data directory.

    Raises ValueError on path-traversal attempts or invalid user_id.
    Always use this instead of building paths manually.
    """
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", str(user_id)):
        raise ValueError(f"Invalid user_id: {user_id!r}")

    user_dir = (_USER_DATA_ROOT / user_id).resolve()
    user_dir.mkdir(parents=True, exist_ok=True)

    if not subpath:
        return user_dir

    target = (user_dir / Path(*subpath)).resolve()
    if not str(target).startswith(str(user_dir) + os.sep) and target != user_dir:
        raise ValueError("Path traversal detected")
    return target


# ── Auth decorators ───────────────────────────────────────────────────────────

def _is_json_request() -> bool:
    return request.is_json or request.path.startswith("/api/")


def require_auth(f):
    """Require an authenticated session. Redirects HTML, 401s JSON/API."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            if _is_json_request():
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)
    return decorated


def require_verified(f):
    """Require authenticated + email-verified account."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            if _is_json_request():
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for("auth.login", next=request.path))
        if not current_user.is_verified:
            if _is_json_request():
                return jsonify({"error": "Email not verified"}), 403
            return redirect(url_for("auth.unverified"))
        return f(*args, **kwargs)
    return decorated


def require_plan(feature: str, error_message: str | None = None):
    """Decorator factory: gate a route on a plan feature flag.

    Usage::

        @app.route('/api/linkedin/...')
        @require_plan('linkedin_enabled', 'LinkedIn requires Growth or higher.')
        def my_route(): ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                if _is_json_request():
                    return jsonify({"error": "Authentication required"}), 401
                return redirect(url_for("auth.login"))

            if current_user.trial_expired and not current_user.plan_id:
                msg = "Your trial has expired. Please choose a plan to continue."
                if _is_json_request():
                    return jsonify({"error": msg, "upgrade_required": True}), 402
                return redirect(url_for("billing.upgrade"))

            if not current_user.can_use_feature(feature):
                msg = error_message or "This feature requires a higher plan."
                if _is_json_request():
                    return jsonify({"error": msg, "upgrade_required": True}), 402
                abort(402)

            return f(*args, **kwargs)
        return decorated
    return decorator
