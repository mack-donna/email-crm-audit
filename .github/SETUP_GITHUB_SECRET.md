# Setting Up GitHub Secret for Security Review

## Quick Setup (5 minutes)

### Step 1: Get Your Anthropic API Key
1. Go to https://console.anthropic.com/
2. Sign in to your account
3. Navigate to **API Keys** section
4. Click **Create Key** (if you don't have one)
5. Copy the API key (starts with `sk-ant-`)

### Step 2: Add Secret to GitHub Repository

#### Option A: Via GitHub Web Interface (Recommended)
1. Open your repository in a web browser:
   ```
   https://github.com/YOUR_USERNAME/email-crm-audit
   ```

2. Click on **Settings** (top navigation bar)

3. In the left sidebar, click **Secrets and variables** → **Actions**

4. Click the green **New repository secret** button

5. Fill in the form:
   - **Name**: `ANTHROPIC_API_KEY`
   - **Secret**: Paste your API key (the one starting with `sk-ant-`)

6. Click **Add secret**

7. ✅ Done! The secret is now available to your GitHub Actions workflows

#### Option B: Via GitHub CLI (Advanced)
```bash
# Install GitHub CLI if you haven't: https://cli.github.com/

# Login to GitHub
gh auth login

# Add the secret (you'll be prompted to enter the value)
gh secret set ANTHROPIC_API_KEY

# Or set it directly
gh secret set ANTHROPIC_API_KEY -b "your-api-key-here"
```

### Step 3: Verify the Secret Was Added

1. Go back to **Settings** → **Secrets and variables** → **Actions**
2. You should see `ANTHROPIC_API_KEY` in the list of repository secrets
3. The value will be hidden for security (shows as `***`)

### Step 4: Test the Workflow

#### Trigger a Test Run
1. Go to **Actions** tab in your repository
2. Select **Claude Code Security Review** workflow
3. Click **Run workflow** dropdown
4. Choose:
   - Branch: `main`
   - Review scope: `changed_files`
5. Click **Run workflow**

The workflow will now have access to your API key and can run the security review!

## Security Best Practices

### ✅ DO:
- Use GitHub Secrets for all API keys and sensitive data
- Rotate API keys regularly (every 90 days recommended)
- Use different API keys for development and production
- Limit API key permissions to only what's needed
- Monitor API usage in Anthropic console

### ❌ DON'T:
- Commit API keys to the repository
- Share API keys in chat, email, or documentation
- Use the same API key across multiple projects
- Store API keys in code or configuration files
- Leave unused API keys active

## Troubleshooting

### "Secret not found" Error
- **Solution**: Verify the secret name is exactly `ANTHROPIC_API_KEY` (case-sensitive)
- Check that you're in the correct repository
- Ensure the secret is in **Actions** secrets, not environment secrets

### "Invalid API key" Error
- **Solution**: Verify the key starts with `sk-ant-`
- Check for extra spaces when copying/pasting
- Ensure the key is still active in Anthropic console
- Try creating a new API key

### Workflow Doesn't Run
- **Solution**: Check that the workflow file is in `.github/workflows/security-review.yml`
- Verify GitHub Actions are enabled for your repository
- Check workflow permissions in Settings → Actions → General

## Additional Security Features

Once the secret is set up, your security review workflow will:
- ✅ Run automatically on every pull request
- ✅ Post findings as PR comments
- ✅ Check for OWASP Top 10 vulnerabilities
- ✅ Scan for hardcoded secrets
- ✅ Validate dependencies with Bandit & Safety
- ✅ Use AI-powered analysis with Claude Code

## Next Steps

After setting up the secret:
1. ✅ Create a test pull request to see the review in action
2. 📖 Review findings and address any security issues
3. ⚙️ Customize security rules in `.github/security-review-config.yml`
4. 📊 Check security reports in Actions artifacts

## Need Help?

- 📚 Full documentation: `SECURITY_REVIEW_SETUP.md`
- 🚀 Quick reference: `.github/SECURITY_REVIEW_QUICKSTART.md`
- 🧪 Test setup: `./scripts/test_security_review.sh`
- 🐛 Issues: Create a GitHub issue in the repository

---

**Remember**: Never commit secrets to your repository. Always use GitHub Secrets or environment variables!
