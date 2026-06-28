"""SQLAlchemy models for the multi-tenant account system."""
import uuid
from datetime import datetime, timezone, timedelta

import bcrypt
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def _uuid():
    return str(uuid.uuid4())


# ── Plans ─────────────────────────────────────────────────────────────────────

class Plan(db.Model):
    __tablename__ = "plans"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    name = db.Column(db.String(50), unique=True, nullable=False)  # trial, starter, growth, scale
    display_name = db.Column(db.String(100), nullable=False)
    price_monthly_cents = db.Column(db.Integer, nullable=False, default=0)
    price_annual_cents = db.Column(db.Integer, nullable=False, default=0)

    # Feature flags — checked at runtime by require_plan() decorator
    max_contacts_per_campaign = db.Column(db.Integer, nullable=False, default=250)
    max_campaigns_per_month = db.Column(db.Integer, nullable=False, default=3)
    gmail_accounts_limit = db.Column(db.Integer, nullable=False, default=1)
    linkedin_enabled = db.Column(db.Boolean, nullable=False, default=False)
    research_depth = db.Column(db.Integer, nullable=False, default=1)   # sources: 1 / 3 / -1 (unlimited)
    history_days = db.Column(db.Integer, nullable=False, default=30)     # -1 = unlimited
    team_seats = db.Column(db.Integer, nullable=False, default=1)
    api_access = db.Column(db.Boolean, nullable=False, default=False)
    custom_prompts = db.Column(db.Boolean, nullable=False, default=False)

    # Stripe price IDs — populated when billing is activated
    stripe_price_id_monthly = db.Column(db.String(100), nullable=True)
    stripe_price_id_annual = db.Column(db.String(100), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    users = db.relationship("User", backref="plan", lazy="dynamic")


# ── Users ─────────────────────────────────────────────────────────────────────

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(255), nullable=True)
    # Nullable: OAuth-only users have no password
    password_hash = db.Column(db.LargeBinary, nullable=True)

    # Account state
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    # Plan / subscription
    plan_id = db.Column(db.String(36), db.ForeignKey("plans.id"), nullable=True)
    trial_expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    stripe_customer_id = db.Column(db.String(100), nullable=True)

    # TOTP 2FA
    mfa_secret = db.Column(db.String(64), nullable=True)
    mfa_enabled = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relationships
    oauth_connections = db.relationship(
        "OAuthConnection", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    sessions = db.relationship(
        "UserSession", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    audit_logs = db.relationship("AuditLog", backref="user", lazy="dynamic")
    email_tokens = db.relationship(
        "EmailToken", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    # ── Password helpers ──────────────────────────────────────────────────────

    def set_password(self, password: str):
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt(rounds=12)
        )

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return bcrypt.checkpw(password.encode("utf-8"), self.password_hash)

    # Required by Flask-Login
    def get_id(self):
        return self.id

    # ── Plan helpers ──────────────────────────────────────────────────────────

    @property
    def is_on_trial(self) -> bool:
        if not self.trial_expires_at:
            return False
        return datetime.now(timezone.utc) < self.trial_expires_at

    @property
    def trial_expired(self) -> bool:
        if not self.trial_expires_at:
            return False
        return datetime.now(timezone.utc) >= self.trial_expires_at

    @property
    def trial_days_remaining(self) -> int:
        if not self.trial_expires_at:
            return 0
        delta = self.trial_expires_at - datetime.now(timezone.utc)
        return max(0, delta.days)

    _ALLOWED_FEATURES = frozenset({
        "max_contacts_per_campaign", "max_campaigns_per_month",
        "gmail_accounts_limit", "linkedin_enabled", "research_depth",
        "history_days", "team_seats", "api_access", "custom_prompts",
    })

    def get_feature(self, feature_name):
        if feature_name not in self._ALLOWED_FEATURES:
            raise ValueError(f"Unknown feature: {feature_name!r}")
        if not self.plan:
            return None
        return getattr(self.plan, feature_name, None)

    def can_use_feature(self, feature_name) -> bool:
        """Boolean check: is this feature enabled on the user's current plan?"""
        value = self.get_feature(feature_name)
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value != 0  # -1 = unlimited, >0 = allowed
        return bool(value)


# ── OAuth connections ─────────────────────────────────────────────────────────

class OAuthConnection(db.Model):
    """Stores provider identity links (Google, Microsoft).
    Access/refresh tokens are stored here — encrypt at rest before GA."""

    __tablename__ = "oauth_connections"
    __table_args__ = (
        db.UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_user"),
    )

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    user_id = db.Column(
        db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider = db.Column(db.String(50), nullable=False)         # 'google', 'microsoft'
    provider_user_id = db.Column(db.String(255), nullable=False)
    provider_email = db.Column(db.String(255), nullable=True)
    # TODO: encrypt at rest with app-level KMS before GA
    access_token = db.Column(db.Text, nullable=True)
    refresh_token = db.Column(db.Text, nullable=True)
    token_expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    scopes = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


# ── Server-side sessions ──────────────────────────────────────────────────────

class UserSession(db.Model):
    """Server-side session records. Cookie holds only a signed reference to this."""

    __tablename__ = "user_sessions"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    user_id = db.Column(
        db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # SHA-256 hash of the raw token stored in the cookie — never store raw token
    session_token_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    last_seen_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    revoked = db.Column(db.Boolean, nullable=False, default=False)

    @property
    def is_valid(self) -> bool:
        if self.revoked:
            return False
        return datetime.now(timezone.utc) < self.expires_at


# ── Audit log ─────────────────────────────────────────────────────────────────

class AuditLog(db.Model):
    """Immutable append-only log of security-relevant events."""

    __tablename__ = "audit_logs"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    user_id = db.Column(
        db.String(36), db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(100), nullable=True)
    resource_id = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    details = db.Column(db.JSON, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )


# ── Email tokens ──────────────────────────────────────────────────────────────

class EmailToken(db.Model):
    """Short-lived tokens for email verification and password reset."""

    __tablename__ = "email_tokens"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    user_id = db.Column(
        db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    purpose = db.Column(db.String(50), nullable=False)  # 'verify_email' | 'reset_password'
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    used_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    @property
    def is_valid(self) -> bool:
        if self.used_at:
            return False
        return datetime.now(timezone.utc) < self.expires_at
