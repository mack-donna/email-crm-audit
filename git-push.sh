#!/bin/bash
# Primary GitHub push script
# 
# Usage: ./git-push.sh
# 
# If authentication fails, run: ./update-github-token.sh first

echo "🚀 Pushing to GitHub..."
echo "======================"

# Check if there are commits to push
if git status | grep -q "nothing to commit, working tree clean"; then
    echo "ℹ️  No changes to push"
    exit 0
fi

# Ensure proper git configuration  
git config credential.helper osxkeychain

# Set remote URL with username for keychain lookup
git remote set-url origin https://mack-donna@github.com/mack-donna/email-crm-audit.git

# Attempt push using stored credentials
echo "Attempting push with stored credentials..."
if git push origin main; then
    echo "✅ Successfully pushed to GitHub!"
    echo "📝 Changes are now live at: https://github.com/mack-donna/email-crm-audit"
else
    echo "❌ Push failed - credentials may be expired or missing"
    echo "💡 Fix: Run './update-github-token.sh' to refresh authentication"
    echo "📚 Then try './git-push.sh' again"
    exit 1
fi