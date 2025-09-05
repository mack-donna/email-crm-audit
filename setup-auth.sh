#!/bin/bash
# One-time GitHub authentication setup
# Run this once to store credentials securely

echo "🔐 GitHub Authentication Setup"
echo "=============================="
echo ""
echo "This will set up secure authentication for automated pushes."
echo ""
echo "You need a GitHub Personal Access Token (PAT):"
echo "1. Go to: https://github.com/settings/tokens"
echo "2. Click 'Generate new token (classic)'"
echo "3. Select scopes: 'repo' (for private repos) or 'public_repo'"
echo "4. Copy the token (starts with 'ghp_')"
echo ""
read -p "Press Enter when you have your token ready..."
echo ""

# Configure credential helper
git config --global credential.helper osxkeychain
echo "✅ Configured macOS keychain as credential helper"

# Set remote URL
git remote set-url origin https://github.com/mack-donna/email-crm-audit.git
echo "✅ Set remote URL"

echo ""
echo "Now attempting to push - you'll be prompted for credentials:"
echo "  Username: mack-donna"
echo "  Password: [paste your PAT here]"
echo ""

# This will prompt for credentials and store them in keychain
if git push origin main; then
    echo ""
    echo "🎉 SUCCESS! Authentication is now set up."
    echo "✅ Your credentials are stored securely in macOS keychain"
    echo "✅ Future pushes with ./push.sh will work automatically"
    echo ""
    echo "🚀 You can now use: ./push.sh"
else
    echo ""
    echo "❌ Setup failed. Please check:"
    echo "  - PAT has 'repo' scope"
    echo "  - Username is correct: mack-donna"
    echo "  - Token was pasted correctly"
    echo ""
    echo "Run this script again to retry: ./setup-auth.sh"
fi