# Git Workflow Documentation

## 📋 Current Status

✅ **CSV Validation Feature**: Complete and committed
✅ **All Changes**: Committed locally, ready for push

## 🚀 Quick Start

### First Time Setup (One-time only)
```bash
./setup-auth.sh
```
This will:
- Configure macOS keychain for secure credential storage
- Prompt for your GitHub Personal Access Token (PAT)
- Test the authentication and store credentials

### Daily Usage
```bash
./push.sh
```
Automatically commits changes and pushes to GitHub.

## 🔧 Scripts Overview

- **`setup-auth.sh`** - One-time authentication setup
- **`push.sh`** - Daily automated add/commit/push script

## 📋 Requirements

- **GitHub PAT**: Create at https://github.com/settings/tokens
  - Scope needed: `repo` (for private repos) or `public_repo`
  - Token format: `ghp_...`

## 🔒 Security Features

- ✅ Uses macOS keychain for credential storage
- ✅ No hardcoded tokens in scripts
- ✅ Standard Git credential helper
- ✅ Secure HTTPS authentication

## 📝 What's Ready to Push

- CSV validation and error reporting system
- Interactive UI for removing invalid records  
- Campaign setup page for validated contacts
- Cleaned up GitHub authentication scripts