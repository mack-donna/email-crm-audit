# 🛡️ Claude Code Security Review - Quick Start

## One-Time Setup (5 minutes)

### 1. Add API Key to GitHub Secrets
```
Repository → Settings → Secrets and variables → Actions → New repository secret
Name: ANTHROPIC_API_KEY
Value: your-anthropic-api-key
```

### 2. Verify Configuration
```bash
# Test your local setup
./scripts/test_security_review.sh

# Install security tools (optional, for local testing)
pip install bandit safety
```

### 3. Done!
Security review now runs automatically on all pull requests.

---

## How to Use

### Automatic Review (Recommended)
1. Create a pull request
2. Security review runs automatically
3. View results in PR comments
4. Address any findings before merging

### Manual Review
```
GitHub → Actions → "Claude Code Security Review" → Run workflow
Choose scope: changed_files or all_files
```

### Local Testing Before PR
```bash
# Quick security check
bandit -r . -f screen

# Check dependencies
safety check -r requirements.txt

# Find hardcoded secrets
grep -rn "api_key\|password\|secret" . --include="*.py"
```

---

## Understanding Results

### 🔴 CRITICAL - Must Fix
- Hardcoded secrets (API keys, passwords)
- SQL/Command injection vulnerabilities
- Insecure deserialization

### 🟡 MEDIUM - Should Fix Soon
- Missing input validation
- Path traversal risks
- Weak cryptography

### 🟢 LOW - Consider Fixing
- Security best practices
- Verbose error messages
- Missing security headers

---

## Common Fixes

### Hardcoded Secrets ❌→✅
```python
# ❌ Bad
api_key = "sk-ant-1234567890"

# ✅ Good
api_key = os.environ.get('ANTHROPIC_API_KEY')
```

### SQL Injection ❌→✅
```python
# ❌ Bad
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# ✅ Good
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

### Command Injection ❌→✅
```python
# ❌ Bad
os.system(f"ls {user_input}")

# ✅ Good
subprocess.run(['ls', user_input], check=True)
```

---

## Configuration

### Block PRs with Critical Issues
Edit `.github/security-review-config.yml`:
```yaml
severity:
  critical:
    fail_build: true  # Change from false
```

### Exclude Files from Review
```yaml
review:
  exclude:
    - "**/tests/**"
    - "**/migrations/**"
```

### Suppress False Positives
```yaml
false_positives:
  suppress:
    - file: "path/to/file.py"
      rule: "B101"
      reason: "Intentional usage"
```

---

## Troubleshooting

### "API key not found"
→ Verify ANTHROPIC_API_KEY is in GitHub Secrets

### "Too many files"
→ Add exclusions to `.github/security-review-config.yml`

### "False positives"
→ Document suppressions in config file

### "Workflow not running"
→ Check that file paths match workflow triggers

---

## Resources

📖 **Full Documentation**: `SECURITY_REVIEW_SETUP.md`
🔧 **Configuration**: `.github/security-review-config.yml`
🧪 **Test Setup**: `./scripts/test_security_review.sh`
📚 **Security Best Practices**: `README.md` (Security section)

---

## Quick Commands

```bash
# Test security review setup
./scripts/test_security_review.sh

# Run Bandit locally
bandit -r . -f screen

# Check dependencies for vulnerabilities
safety check

# Find potential secrets
grep -rn "password\|api_key\|secret" . --include="*.py"

# View workflow logs
# GitHub → Actions → Latest security review run
```

---

## Need Help?

1. Check `SECURITY_REVIEW_SETUP.md` for detailed guidance
2. Review workflow logs in GitHub Actions
3. Create an issue in the repository
4. Contact the security team

---

**Remember**: This tool helps catch common issues, but secure coding is still essential! 🔒
