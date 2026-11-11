"""Centralised application configuration."""
import os
import pathlib

# ── Claude API ────────────────────────────────────────────────────────────────
# The one place the model ID lives (tests/test_claude_models.py enforces this).
# Override with the CLAUDE_MODEL env var; never hardcode an ID elsewhere.
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5")
CLAUDE_MAX_TOKENS = 4000  # covers thinking + a short email; thinking counts toward this
CLAUDE_EFFORT = "low"  # short emails; Sonnet 5.5 skips thinking on most simple requests at low
# Server-side refusal fallback (routes declines to another model in the same call).
CLAUDE_FALLBACK_BETA = "server-side-fallback-2026-07-01"


def _fix_db_url(url: str) -> str:
    """Render injects postgres:// but SQLAlchemy 2.x requires postgresql://."""
    if url and url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url


class Config:
    # ── Core ──────────────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY") or "dev-secret-change-me"
    FLASK_ENV = os.environ.get("FLASK_ENV", "development")

    # ── Database ──────────────────────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = _fix_db_url(
        os.environ.get("DATABASE_URL", "sqlite:///dev.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # ── Session cookie ────────────────────────────────────────────────────────
    SESSION_COOKIE_SECURE = True  # overridden to False in DevelopmentConfig
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 86400 * 30  # 30 days

    # ── Rate limiting ─────────────────────────────────────────────────────────
    RATELIMIT_STORAGE_URI = os.environ.get("REDIS_URL", "memory://")
    RATELIMIT_DEFAULT = "200 per day;50 per hour"

    # ── OAuth: Google (SSO identity — separate from Gmail API OAuth) ──────────
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

    # ── OAuth: Microsoft ──────────────────────────────────────────────────────
    MICROSOFT_CLIENT_ID = os.environ.get("MICROSOFT_CLIENT_ID", "")
    MICROSOFT_CLIENT_SECRET = os.environ.get("MICROSOFT_CLIENT_SECRET", "")
    # 'common' = accept any Microsoft / Azure AD account (multi-tenant SaaS)
    MICROSOFT_TENANT_ID = os.environ.get("MICROSOFT_TENANT_ID", "common")

    # ── Resend (transactional email) ──────────────────────────────────────────
    RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
    EMAIL_FROM = os.environ.get("EMAIL_FROM", "noreply@example.com")
    EMAIL_FROM_NAME = os.environ.get("EMAIL_FROM_NAME", "Outreach AI")

    # ── Stripe (wired, not yet active) ───────────────────────────────────────
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")

    # ── User data storage ─────────────────────────────────────────────────────
    USER_DATA_DIR = str(pathlib.Path(os.environ.get("USER_DATA_DIR", "user_data")).resolve())


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


_config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}


def get_config():
    env = os.environ.get("FLASK_ENV", "development")
    cfg = _config_map.get(env)
    if cfg is None:
        raise RuntimeError(
            f"Unknown FLASK_ENV value: {env!r}. Must be one of: {list(_config_map)}"
        )
    if env == "production" and cfg.SECRET_KEY == "dev-secret-change-me":
        raise RuntimeError(
            "FLASK_SECRET_KEY environment variable must be set in production. "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    return cfg
