#!/bin/bash
# GitHub Token Update Script
# Use this when your GitHub token expires

echo "GitHub Token Update"
echo "==================="
echo
echo "Steps:"
echo "1. Go to: https://github.com/settings/tokens"
echo "2. Generate new token with 'repo' and 'workflow' scopes"
echo "3. Copy the token (starts with ghp_)"
echo "4. Come back and paste it below"
echo
read -p "Press Enter when ready..."
echo

# Clear old token
echo "Clearing old token from keychain..."
printf "host=github.com\nprotocol=https\n" | git credential-osxkeychain erase
echo "✅ Old token cleared"
echo

# Get new token
read -s -p "Paste your new GitHub token: " token
echo
echo

# Save to keychain using git credential helper
echo "Saving new token to keychain..."
printf "protocol=https\nhost=github.com\nusername=mack-donna\npassword=${token}\n" | git credential-osxkeychain store

# Also save with security command for reliability
security add-internet-password \
  -a "mack-donna" \
  -s "github.com" \
  -w "$token" \
  -U \
  -T /usr/bin/git \
  -T /usr/local/bin/git \
  2>/dev/null

echo "✅ Token saved to keychain"
echo

# Test
echo "Testing authentication..."
git ls-remote https://github.com/mack-donna/email-crm-audit.git HEAD &>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Success! Your new token is working."
    echo
    echo "You can verify in Keychain Access:"
    echo "  1. Open Keychain Access app"
    echo "  2. Search for 'github'"
    echo "  3. You should see github.com entry"
else
    echo "❌ Test failed. Please verify:"
    echo "  - Token has 'repo' permissions"
    echo "  - You copied the entire token"
    echo "  - No extra spaces were included"
fi

# Clear token from memory
unset token