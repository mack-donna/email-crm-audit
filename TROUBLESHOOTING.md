# Troubleshooting Guide

## Common Issues and Solutions

### 🔐 Authentication & Security Issues

#### GitHub Push Rejected - "Repository rule violations"
**Error:** `Push cannot contain secrets`  
**Cause:** GitHub detected API keys or tokens in your commit  
**Solution:**
```bash
# 1. Check what GitHub detected
git log --oneline -5

# 2. Reset to before the problematic commit
git reset --soft COMMIT_HASH_BEFORE_SECRET

# 3. Remove secrets from code, then commit clean
git add .
git commit -m "Clean commit without secrets"

# 4. Push the clean version
git push origin main
```

#### Git Authentication Fails Despite Valid Token
**Error:** `Authentication failed` or `Invalid username or token`  
**Diagnosis:** Test if token works with API:
```bash
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
```

**If token works but git doesn't:**
```bash
# Method 1: Reset credential helper
git config --global credential.helper osxkeychain
git credential-osxkeychain erase < /dev/null

# Method 2: Direct push with token
git push https://USERNAME:TOKEN@github.com/owner/repo.git main

# Method 3: Store in credentials
echo "https://USERNAME:TOKEN@github.com" > ~/.git-credentials
git config --global credential.helper store
```

#### "Device not configured" Error
**Cause:** macOS credential helper issues  
**Solution:**
```bash
git config --global credential.helper osxkeychain
# Then retry your git command
```

### 🐍 Python & SSL Issues

#### SSL Certificate Errors with Claude API
**Error:** `SSL: CERTIFICATE_VERIFY_FAILED`  
**Cause:** Python 2.7 SSL/TLS incompatibility  
**Solution:** Upgrade to Python 3.9+
```bash
# Check Python version
python3 --version

# Install dependencies
pip3 install -r requirements.txt

# Use Python 3 entry point
python3 modern_outreach.py
```

#### Module Import Errors
**Error:** `ModuleNotFoundError: No module named 'google'`  
**Solution:**
```bash
pip3 install -r requirements.txt

# If still failing, install individually:
pip3 install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### 📧 Gmail Integration Issues

#### Gmail Authentication Failed
**Error:** `Gmail credentials file not found`  
**Solution:**
1. Download `credentials.json` from Google Cloud Console
2. Follow [Gmail API Setup Guide](GMAIL_API_SETUP.md)
3. Place file in project root directory

#### Token Corruption
**Error:** `invalid load key` when loading token  
**Solution:**
```bash
# Delete corrupted token
rm token.json token.pickle

# Re-authenticate (will open browser)
python3 gmail_drafts_manager.py
```

### 🤖 AI Generation Issues

#### No API Key Found
**Error:** `No ANTHROPIC_API_KEY found`  
**Solution:**
```bash
export ANTHROPIC_API_KEY='sk-ant-api03-...'

# Add to your shell profile for persistence
echo 'export ANTHROPIC_API_KEY="sk-ant-api03-..."' >> ~/.zshrc
source ~/.zshrc
```

#### Template Fallback Mode
**Behavior:** System generates template emails instead of AI  
**Cause:** API key missing or invalid  
**Solution:**
1. Check API key is set: `echo $ANTHROPIC_API_KEY`
2. Test API access: See authentication troubleshooting above
3. Verify Claude API quota/billing

### 📊 CSV Processing Issues

#### CSV Delimiter Detection Failed
**Error:** `Could not determine delimiter`  
**Solution:**
1. Ensure CSV uses standard delimiters (comma, semicolon, tab)
2. Check for proper headers: `name,email,company`
3. Use simple test CSV format:
```csv
name,email,company
John Doe,john@techcorp.com,TechCorp
```

#### Contact Validation Errors
**Behavior:** Contacts skipped during processing  
**Cause:** Missing required fields  
**Solution:** Ensure CSV has these minimum columns:
- `name` or `first_name`/`last_name`  
- `email`
- `company` (optional but recommended)

## 🔍 Debugging Tips

### Enable Verbose Logging
```bash
export DEBUG=1
python3 modern_outreach.py
```

### Check System Status
```bash
# Test Python 3 modernizations
python3 test_modern_system.py

# Verify Gmail authentication
python3 gmail_drafts_manager.py

# Test AI generation (requires API key)
python3 test_simple_ai.py
```

### Common File Locations
- **Credentials:** `credentials.json` (root directory)
- **Tokens:** `token.json`, `token.pickle` (root directory)  
- **Campaigns:** `outreach_campaigns/*.json`
- **Logs:** `outreach_automation.log`

## 🆘 When All Else Fails

1. **Clean slate approach:**
```bash
# Remove all authentication files
rm token.json token.pickle ~/.git-credentials

# Clear git credential cache
git credential-osxkeychain erase < /dev/null

# Re-run setup from scratch
```

2. **Check the basics:**
   - Python 3.9+ installed?
   - Required dependencies installed?
   - API keys properly set?
   - Internet connectivity working?

3. **Review recent changes:**
```bash
git log --oneline -10
git status
```

## 📞 Getting Help

If you're still stuck:
1. Check the error message against this guide
2. Review the specific module documentation
3. Verify your environment setup matches the README
4. Consider reverting to the last working state

**Remember:** Most issues are authentication or environment-related. The core system is robust once properly configured!