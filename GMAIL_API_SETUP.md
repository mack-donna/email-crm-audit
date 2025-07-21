# Gmail API Setup Guide

## Quick Setup Steps

### 1. Enable Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Click "Enable APIs and Services"
4. Search for "Gmail API"
5. Click on Gmail API and press "Enable"

### 2. Create OAuth 2.0 Credentials

1. In the left sidebar, click "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" user type
   - Fill in required fields (app name, email)
   - Add your email to test users
   - Save and continue through all steps

4. Back in Create OAuth client ID:
   - Application type: "Desktop app"
   - Name: "Email CRM Audit Tool" (or your preference)
   - Click "Create"

### 3. Download Credentials

1. Click the download button (⬇️) next to your new OAuth 2.0 Client ID
2. Save the file as `credentials.json` in this directory (email-crm-audit/)

### 4. First Run Authentication

When you run the email analyzer for the first time:
1. Your browser will open automatically
2. Log in with your Google account
3. Grant permission to read Gmail messages
4. The script will save authentication token as `token.pickle`

## Testing the Module

Run the test script:
```bash
python email_history_analyzer.py
```

The test will:
1. ✅ Authenticate with Gmail API
2. ✅ Test the connection
3. ✅ Let you search for a specific email address
4. ✅ Generate a summary report

## Important Notes

- **First time only**: Browser authentication required
- **Subsequent runs**: Uses saved token (no browser needed)
- **Token expiry**: Automatically refreshes when needed
- **Scope**: Read-only access to Gmail (safe)

## Troubleshooting

**"credentials.json not found"**
- Make sure you downloaded and saved the OAuth credentials file
- Check it's named exactly `credentials.json`
- Ensure it's in the same directory as the script

**"Access blocked" error**
- Make sure you added your email as a test user in OAuth consent screen
- Check that Gmail API is enabled in your Google Cloud project

**Browser doesn't open**
- Try running with `python3` instead of `python`
- Check you have a default browser set
- Manually open the URL shown in the terminal

## Security Notes

- `credentials.json`: Contains your app's OAuth settings (keep private)
- `token.pickle`: Contains your personal access token (NEVER share)
- Add both files to `.gitignore` to prevent accidental commits