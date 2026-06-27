"""Transactional email via Resend.

Configure with env vars:
  RESEND_API_KEY   — from resend.com dashboard
  EMAIL_FROM       — verified sender address  e.g. noreply@yourdomain.com
  EMAIL_FROM_NAME  — display name             e.g. Outreach AI

If RESEND_API_KEY is absent (local dev), emails are logged to stdout
instead of sent so the app never crashes without credentials.
"""
import logging
import os

logger = logging.getLogger(__name__)


class EmailService:
    @classmethod
    def _from_address(cls) -> str:
        name = os.environ.get("EMAIL_FROM_NAME", "Outreach AI")
        addr = os.environ.get("EMAIL_FROM", "noreply@example.com")
        return f"{name} <{addr}>"

    @classmethod
    def _send(cls, to_email: str, subject: str, html_body: str) -> bool:
        api_key = os.environ.get("RESEND_API_KEY", "")
        if not api_key:
            logger.warning(
                "[email] RESEND_API_KEY not set — printing instead of sending\n"
                "  To: %s\n  Subject: %s", to_email, subject
            )
            return False
        try:
            import resend  # type: ignore[import]
            resend.api_key = api_key
            resend.Emails.send({
                "from": cls._from_address(),
                "to": to_email,
                "subject": subject,
                "html": html_body,
            })
            logger.info("[email] Sent '%s' to %s", subject, to_email)
            return True
        except Exception:
            logger.exception("[email] Failed to send to %s", to_email)
            return False

    # ── Template methods ──────────────────────────────────────────────────────

    @classmethod
    def send_verification(cls, email: str, name: str, verify_url: str):
        cls._send(
            email,
            "Verify your email — Outreach AI",
            f"""
            <div style="font-family:sans-serif;max-width:480px;margin:0 auto">
              <h2 style="color:#4f46e5">Welcome to Outreach AI</h2>
              <p>Hi {name},</p>
              <p>Click below to verify your email address. This link expires in <strong>24 hours</strong>.</p>
              <p style="margin:24px 0">
                <a href="{verify_url}"
                   style="background:#4f46e5;color:#fff;padding:12px 24px;
                          border-radius:6px;text-decoration:none;font-weight:600">
                  Verify Email
                </a>
              </p>
              <p style="color:#6b7280;font-size:13px">
                If you didn't create an account, you can safely ignore this email.
              </p>
            </div>
            """,
        )

    @classmethod
    def send_password_reset(cls, email: str, name: str, reset_url: str):
        cls._send(
            email,
            "Reset your password — Outreach AI",
            f"""
            <div style="font-family:sans-serif;max-width:480px;margin:0 auto">
              <h2 style="color:#4f46e5">Password reset</h2>
              <p>Hi {name},</p>
              <p>Click below to reset your password. This link expires in <strong>1 hour</strong>.</p>
              <p style="margin:24px 0">
                <a href="{reset_url}"
                   style="background:#4f46e5;color:#fff;padding:12px 24px;
                          border-radius:6px;text-decoration:none;font-weight:600">
                  Reset Password
                </a>
              </p>
              <p style="color:#6b7280;font-size:13px">
                If you didn't request this, ignore this email — your password won't change.
              </p>
            </div>
            """,
        )

    @classmethod
    def send_trial_expiry_warning(cls, email: str, name: str, days_left: int, upgrade_url: str):
        cls._send(
            email,
            f"Your trial ends in {days_left} day{'s' if days_left != 1 else ''} — Outreach AI",
            f"""
            <div style="font-family:sans-serif;max-width:480px;margin:0 auto">
              <h2 style="color:#4f46e5">Trial ending soon</h2>
              <p>Hi {name},</p>
              <p>Your 14-day trial expires in <strong>{days_left} day{'s' if days_left != 1 else ''}</strong>.
                 After that your account switches to read-only mode.</p>
              <p style="margin:24px 0">
                <a href="{upgrade_url}"
                   style="background:#4f46e5;color:#fff;padding:12px 24px;
                          border-radius:6px;text-decoration:none;font-weight:600">
                  Choose a Plan
                </a>
              </p>
            </div>
            """,
        )
