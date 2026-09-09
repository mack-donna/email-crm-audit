# Next Session - Start Here

**Last Updated:** 2026-09-08
**Status:** Production recovered — login + Gmail connect working after DB expiry & OAuth scope fixes (Session 8) ✅

---

## 🎉 Recent Completions (Sessions ~June 2026)

### ✅ Security Fixes (all on branch `fix/linkedin-nav-api-leaks`, PR #2)
- **LinkedIn nav bug** — Alpine.js showed "💼 LinkedIn Unavailable" for unauthenticated users. Fixed by adding `available` and `configured` fields to the no-session branch of `/api/linkedin/status`.
- **API info leaks** — removed `user_id` (session ID) from `/api/gmail/status` and `/api/linkedin/status` responses.
- **Favicon 404** — added `/favicon.ico` route that returns 204 if no file exists.
- **Bandit B605** — replaced `os.system('clear')` with `subprocess.run(['clear'], check=False)` in `review_interface.py`.
- **Bandit B113** — added `timeout=30` to all `requests.get/post` calls in `klaviyo_integration.py` and `linkedin_client.py`.
- **Dead pickle import** — removed `import pickle` from `gmail_oauth.py` (was unused; token storage was already 100% JSON). Updated stale `token.pickle` string references in `outreach_automation.py`, `workflow_orchestrator.py`, and `email_history_analyzer.py`.
- **Claude security review model** — updated `.github/scripts/claude_security_review.py` from retired `claude-3-opus-20240229` to `claude-sonnet-4-6`.

### ✅ GitHub Actions Security CI
- Bandit + Safety scans run on every PR
- Claude API security analysis runs on PRs (changed files) and workflow_dispatch (all files)
- All High severity findings resolved; remaining findings are confirmed Low-severity false positives

---

## ✅ Session 8 (2026-09-08) — Production recovery

Two production outages found via a Google "inactive OAuth client" email and fixed (infra/config only, no code):
- **Login 500** — free Postgres expired (2026-07-27) and was auto-deleted → provisioned paid `basic_256mb` DB (`dpg-dagcclqjnfac739k2q60-a`), relinked `DATABASE_URL`.
- **Gmail connect error** — oauthlib "Scope has changed" (Google returns scope superset for signed-in users) → set `OAUTHLIB_RELAX_TOKEN_SCOPE=1`.

`render.yaml` updated to match (paid DB plan + the new env var). Old DB data was lost with the expired instance. (PR #2 was merged back in June.)

## ⚠️ Watch-outs
- **Don't downgrade the DB to free** — that's exactly what broke login this session.
- **Dev server in prod** — `run.py` uses Flask's dev server; Render logs warn against it. Consider gunicorn.
- **render.yaml drift** — live `PYTHON_VERSION` (3.13.4) and build command (`FLASK_APP=` prefixes) differ from the blueprint; a full blueprint re-sync could revert them.

---

## 📋 Remaining Work (from CODE_AUDIT_WEEK1.md)

### Medium Priority Refactors
1. **Bare exception handlers** — 6 instances across `email_generator.py`, `email_history_analyzer.py`, `simple_http_client.py`, `web_app.py`, `workflow_orchestrator.py`. Replace with specific exception types.
2. **Duplicate email extraction logic** — ~500 lines of near-identical Gmail retrieval code spread across 5+ files. Consolidate into a single shared utility.
3. **External service error handling** — create shared utilities for consistent error handling across API integrations.

### Pending Security Plan Items (from plan `lets-plan-to-make-glimmering-bonbon.md`)
Items 4, 5, 6 from the plan are NOT YET DONE:
- Item 4: Replace pickle with JSON in `gmail_drafts_manager.py` (still uses `pickle.load/dump`)
- Item 5: `email_history_analyzer.py` already done ✅
- Item 6: Remove curl/subprocess fallback in `email_generator.py` (dead code, `anthropic` is in requirements.txt)

### Node.js Deprecation
- `node@20` — deprecated 2026-10-28; migrate to `node` (LTS) or `node@22`
- `icu4c@77` — deprecated 2026-10-30

---

## 🔧 Key Files

| File | Purpose |
|------|---------|
| `web_app.py` | Flask app — main entry point for Render deployment |
| `gmail_oauth.py` | Multi-user Gmail OAuth2 flow |
| `gmail_drafts_manager.py` | Gmail draft creation (still uses pickle — needs fix) |
| `email_generator.py` | Claude API email generation |
| `workflow_orchestrator.py` | End-to-end campaign orchestration |
| `.github/workflows/security-review.yml` | CI: Bandit + Claude security scan |
| `.github/scripts/claude_security_review.py` | Claude analysis script (model: claude-sonnet-4-6) |

---

## 📍 Where Things Live

- **Repo:** https://github.com/mack-donna/email-crm-audit
- **Live app:** https://email-outreach-automation.onrender.com
- **Open PR:** https://github.com/mack-donna/email-crm-audit/pull/2
- **Working branch:** `fix/linkedin-nav-api-leaks`
- **Anthropic API key:** stored in Render environment variables (not local)

---

## ⚡ Quick Commands

```bash
# Check PR status
gh pr status --repo mack-donna/email-crm-audit

# Merge PR #2
gh pr merge 2 --squash --repo mack-donna/email-crm-audit

# Clone/update local copy
cd /tmp/email-crm-audit && git pull

# Run Bandit locally
cd /tmp/email-crm-audit && bandit -r . -ll -f screen
```

---

*Last updated: 2026-06-27 — Session: Security hardening + pickle cleanup complete*
