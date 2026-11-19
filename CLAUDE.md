# email-crm-audit: notes for Claude

Start with `NEXT_SESSION.md` for current status. Full history: `SESSION_LOG.md`.

## Checks
One command runs every repo check:

```bash
bash scripts/check.sh
```

Use it as the `done_when` in PROGRESS.md. It needs `.venv` on the same Python as Render (3.13):

```bash
uv venv --python 3.13 .venv && uv pip install --python .venv/bin/python -r requirements.txt "bandit>=1.9,<2"
```

CI runs the same script (`.github/workflows/checks.yml`).

## Known pitfalls (each is a check now)
| Past incident | Guard |
|---|---|
| Session 9: unbounded `SQLAlchemy>=2.0` pulled 2.1, which maps `postgresql://` to psycopg v3; we ship psycopg2. Deploy failed. | `scripts/check_requirements.py`: every requirement needs an upper bound. `tests/test_regressions.py::test_postgres_url_resolves_to_psycopg2` |
| Render injects `postgres://`; SQLAlchemy 2.x needs `postgresql://`. | `test_render_postgres_scheme_is_rewritten` |
| Bad dummy bcrypt hash in login -> `ValueError: Invalid salt` -> 500 for unknown emails. | `test_login_with_unknown_email_fails_cleanly` |
| Logout left the `remember_token` cookie; user stayed signed in. | `test_logout_deletes_remember_token` |

When a mistake happens a second time here, add a test or lint rule for it and a row above.

## Dependencies
- Render builds with **no cache**: every deploy installs the newest version inside each bound.
  Raising an upper bound is a deliberate change: do it in its own PR and run the checks.
- Render's Python is not what `render.yaml` says (it lists `PYTHON_VERSION=3.9.18`, but prod
  installed SQLAlchemy 2.1, which needs >=3.11; Render's default is 3.13.x). Treat 3.13 as prod.

## Bandit
Known false positives (do not "fix"): B107/B105 (token filenames, guarded dev secret),
B104 (`0.0.0.0` in `run.py`, production-only), B404/B603 (list-form subprocess), B607.
`scripts/check.sh` runs bandit at medium+. The B104 line in `run.py` carries `# nosec B104`.

## Git
- Commit as `--author="mack-donna <68201041+mack-donna@users.noreply.github.com>"`.
- `main` is branch-protected: feature branch + PR.
