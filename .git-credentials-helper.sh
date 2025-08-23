#!/bin/bash
# This script helps you store GitHub credentials securely

echo "GitHub Personal Access Token Setup"
echo "================================="
echo
read -p "Enter your GitHub username: " github_username
read -s -p "Enter your personal access token: " github_token
echo

# Store credentials using macOS keychain
git config --global credential.helper osxkeychain

# Set the remote URL with username (token will be stored in keychain)
git remote set-url origin https://${github_username}@github.com/mack-donna/email-crm-audit.git

# Trigger credential storage by attempting to push
echo
echo "Attempting to push to trigger credential storage..."
echo "When prompted for a password, paste your personal access token:"
git push -u origin main

echo
echo "If successful, your credentials are now stored in the macOS keychain!"
echo "Future pushes won't require authentication."