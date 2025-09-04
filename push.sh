#!/bin/bash
# Automated Git Push Script
# Uses macOS keychain for secure credential storage

set -e  # Exit on any error

echo "🚀 Automated Git Push"
echo "===================="

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Configure credential helper (idempotent)
git config --global credential.helper osxkeychain

# Check if there are changes to commit
if git diff-index --quiet HEAD --; then
    echo "ℹ️  No changes to commit"
else
    echo "📝 Found uncommitted changes, adding them..."
    git add .
    
    # Generate commit message
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    git commit -m "Automated commit - $TIMESTAMP

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
fi

# Check if there are commits to push
UNPUSHED=$(git log origin/main..HEAD --oneline | wc -l | tr -d ' ')
if [ "$UNPUSHED" -eq 0 ]; then
    echo "✅ Repository is up to date"
    exit 0
fi

echo "📤 Found $UNPUSHED commit(s) to push"

# Set remote URL (ensures correct format)
git remote set-url origin https://github.com/mack-donna/email-crm-audit.git

# Attempt push
echo "🔄 Pushing to GitHub..."
if git push origin main; then
    echo "✅ Successfully pushed to GitHub!"
    echo "🌐 View at: https://github.com/mack-donna/email-crm-audit"
else
    echo "❌ Push failed"
    echo ""
    echo "🔧 Troubleshooting steps:"
    echo "1. Ensure you have a GitHub Personal Access Token"
    echo "2. On first use, you'll be prompted for username/token"
    echo "3. Username: mack-donna"
    echo "4. Password: [paste your PAT - starts with ghp_]"
    echo ""
    echo "💡 Create PAT at: https://github.com/settings/tokens"
    echo "   Required scopes: 'repo'"
    exit 1
fi