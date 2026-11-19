"""Regression tests for bugs that have already shipped once in this repo.

Each test names the past incident it guards against. Keep them fast and offline.
"""
import os
import pathlib
import secrets
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Must be set before web_app is imported: it builds the app at import time.
os.environ["FLASK_ENV"] = "development"
os.environ["DATABASE_URL"] = "sqlite://"  # in-memory
# Fresh random key per run; never a fixed guessable value, and never overrides a real one.
os.environ.setdefault("FLASK_SECRET_KEY", secrets.token_hex(32))


@pytest.fixture(scope="module")
def app():
    import web_app
    from models import db

    application = web_app.app
    application.config.update(TESTING=True, WTF_CSRF_ENABLED=False, RATELIMIT_ENABLED=False)
    # Push app contexts only around setup/teardown. Holding one open across tests
    # makes requests reuse it, so Flask-Login's cached user in `g` leaks between tests.
    with application.app_context():
        db.create_all()
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


# ── Session 9: SQLAlchemy 2.1 mapped postgresql:// to psycopg v3; we ship psycopg2 ──

def test_postgres_url_resolves_to_psycopg2():
    from sqlalchemy.engine import make_url

    assert make_url("postgresql://u:p@host/db").get_dialect().driver == "psycopg2"


def test_render_postgres_scheme_is_rewritten():
    from config import _fix_db_url

    assert _fix_db_url("postgres://u:p@host/db") == "postgresql://u:p@host/db"
    assert _fix_db_url("sqlite:///dev.db") == "sqlite:///dev.db"


# ── Dummy bcrypt hash had the wrong length -> ValueError: Invalid salt -> 500 ──

def test_login_with_unknown_email_fails_cleanly(client):
    resp = client.post(
        "/auth/login",
        data={"email": "nobody@example.com", "password": "wrong"},
    )
    assert resp.status_code == 200
    assert b"Invalid email or password" in resp.data


# ── Logout left the remember_token cookie, so the user stayed signed in ──

def test_logout_deletes_remember_token(app, client):
    from models import User, db

    with app.app_context():
        user = User(email="logout@example.com", is_verified=True)
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    client.set_cookie("remember_token", "stale-token")
    with client.session_transaction() as sess:
        sess["_user_id"] = user_id
        sess["_fresh"] = True

    resp = client.post("/auth/logout")
    # Must land on the login page itself, not a login_required bounce (?next=...),
    # otherwise the test never reached the logout view.
    assert resp.status_code in (301, 302, 303), resp.status_code
    assert resp.location.endswith("/auth/login"), resp.location

    cleared = [
        h for h in resp.headers.getlist("Set-Cookie")
        if h.startswith("remember_token=") and ("Max-Age=0" in h or "1970" in h)
    ]
    assert cleared, f"remember_token not cleared; Set-Cookie: {resp.headers.getlist('Set-Cookie')}"


# ── CSRF is disabled in the fixture for convenience; prove the real app still enforces it ──

def test_csrf_rejects_post_without_token(app, client, monkeypatch):
    # Flask-WTF reads this per request; monkeypatch restores it after the test, even on error.
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", True)
    resp = client.post(
        "/auth/login",
        data={"email": "nobody@example.com", "password": "wrong"},
    )
    assert resp.status_code == 400, resp.status_code
    assert b"CSRF" in resp.data
