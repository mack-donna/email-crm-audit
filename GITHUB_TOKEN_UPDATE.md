# GitHub Token Update Instructions

## When Your Token Expires

GitHub personal access tokens expire based on the expiration date you set. You'll receive an email warning before expiration.

## Step-by-Step Token Update Process

### 1. Generate New Token on GitHub

1. Go to GitHub token settings: https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Give it a descriptive name (e.g., "email-crm-audit-2025")
4. Select expiration (recommend 90 days for security)
5. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `workflow` (Update GitHub Action workflows)
   - ✅ `read:user` (Read user profile data)
   - ✅ `user:email` (Access user email addresses)
6. Click **"Generate token"**
7. **COPY THE TOKEN IMMEDIATELY** (you won't see it again!)

### 2. Remove Old Token from Keychain

```bash
# Remove old token from keychain
printf "host=github.com\nprotocol=https\n" | git credential-osxkeychain erase
```

Or manually via Keychain Access app:
1. Open Keychain Access (Cmd+Space, type "Keychain Access")
2. Search for "github"
3. Delete the old `github.com` entry

### 3. Save New Token to Keychain

Run the provided script:
```bash
./save-to-keychain.sh
```

Or manually:
```bash
# Method 1: Let git prompt you
git push origin main
# Enter username: mack-donna
# Enter password: [paste your new token]

# Method 2: Direct save
printf "protocol=https\nhost=github.com\nusername=mack-donna\npassword=YOUR_NEW_TOKEN\n" | git credential-osxkeychain store
```

### 4. Verify Token is Working

```bash
# Test authentication
git pull origin main

# If successful, you'll see:
# "Already up to date." or pulled changes
```

## Troubleshooting

### Token not working?
1. Verify token has correct permissions (especially `repo` scope)
2. Check you copied the entire token (starts with `ghp_`)
3. Ensure no extra spaces when pasting

### Complex Authentication Issues (Lessons Learned)
Based on real troubleshooting experience:

**Problem:** Git authentication keeps failing despite valid token
**Solution Steps:**
1. Test token validity first:
   ```bash
   curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
   ```
2. If token works but git doesn't, try multiple approaches:
   ```bash
   # Method 1: Reset credential helper
   git config --global credential.helper ""
   git config --global credential.helper osxkeychain
   
   # Method 2: Manual URL with token
   git push https://USERNAME:TOKEN@github.com/owner/repo.git main
   
   # Method 3: Environment variable
   export GITHUB_TOKEN=your_token
   git push origin main
   ```

**Problem:** "Device not configured" errors
**Solution:** Usually indicates credential helper issues
```bash
git config --global credential.helper osxkeychain
git credential-osxkeychain erase < /dev/null
```

**Problem:** GitHub blocks push with "Repository rule violations"  
**Solution:** Remove secrets from commit history:
1. Find the problematic commit: `git log --oneline`
2. Reset to before the bad commit: `git reset --soft COMMIT_HASH`
3. Re-commit without secrets: `git commit -m "Clean commit"`
4. Force push: `git push --force origin main`

**Key Lesson:** Always use environment variables for API keys - never hardcode them in files!

### Keychain not saving?
```bash
# Force keychain to save
security add-internet-password \
  -a "mack-donna" \
  -s "github.com" \
  -w "YOUR_TOKEN" \
  -U \
  -T /usr/bin/git
```

### Still having issues?
```bash
# Check current git config
git config --list | grep credential

# Should show:
# credential.helper=osxkeychain

# If not, set it:
git config --global credential.helper osxkeychain
```

## Security Best Practices

1. **Never commit tokens to code** - They should only exist in your keychain
2. **Set expiration dates** - 90 days is a good balance
3. **Rotate immediately if exposed** - If you accidentally share a token, revoke it immediately
4. **Use minimum required scopes** - Only grant permissions you actually need
5. **Different tokens for different projects** - Don't reuse tokens across projects

## Quick Reference Script

Save this as `update-github-token.sh`:

```bash
#!/bin/bash
# GitHub Token Update Script

echo "GitHub Token Update"
echo "==================="
echo
echo "Steps:"
echo "1. Go to: https://github.com/settings/tokens"
echo "2. Generate new token with 'repo' and 'workflow' scopes"
echo "3. Copy the token"
echo "4. Come back and paste it below"
echo
read -p "Press Enter when ready..."

# Clear old token
printf "host=github.com\nprotocol=https\n" | git credential-osxkeychain erase
echo "✅ Old token cleared"

# Get new token
read -s -p "Paste new token: " token
echo

# Save to keychain
printf "protocol=https\nhost=github.com\nusername=mack-donna\npassword=${token}\n" | git credential-osxkeychain store

# Also save with security command for reliability
security add-internet-password \
  -a "mack-donna" \
  -s "github.com" \
  -w "$token" \
  -U \
  -T /usr/bin/git \
  2>/dev/null

# Test
echo "Testing authentication..."
git ls-remote https://github.com/mack-donna/email-crm-audit.git HEAD &>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Success! Token updated and working."
else
    echo "❌ Test failed. Please check your token."
fi

unset token
```

Make it executable:
```bash
chmod +x update-github-token.sh
```

## Notes

- The `save-to-keychain.sh` script in this repository can be reused for token updates
- Tokens are stored encrypted in macOS Keychain
- Each push/pull uses the stored token automatically
- You only need to update when the token expires or is revoked