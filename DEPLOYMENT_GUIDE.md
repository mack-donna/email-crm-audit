# 🚀 Deployment & Testing Guide

## Quick Start for Testers

### 🔥 One-Command Launch

```bash
# Clone and start in one go
git clone https://github.com/mack-donna/email-crm-audit.git
cd email-crm-audit
chmod +x start_web.sh
./start_web.sh
```

Then open: http://localhost:5000

### 🏃‍♂️ Manual Launch

```bash
# 1. Clone the repository
git clone https://github.com/mack-donna/email-crm-audit.git
cd email-crm-audit

# 2. Install Python dependencies
pip3 install -r requirements.txt

# 3. Set up API key (required for AI email generation)
export ANTHROPIC_API_KEY='your-api-key-here'

# 4. Launch web interface
python3 web_app.py
```

Open http://localhost:5000 in your browser.

## 📋 Complete Setup for Full Testing

### 1. Prerequisites

**Required:**
- Python 3.9+ (Python 3.13+ recommended)
- Internet connection
- Modern web browser

**For AI Email Generation:**
- Anthropic API key (get from: https://console.anthropic.com)

**For Gmail Integration (Optional):**
- Google Cloud Console project
- Gmail API enabled
- OAuth2 credentials downloaded as `credentials.json`

### 2. Environment Setup

#### Option A: Quick Environment Variables
```bash
# Minimum required for AI features
export ANTHROPIC_API_KEY='your-anthropic-api-key'

# Optional: Gmail integration
# (Download credentials.json from Google Cloud Console first)

# Optional: LinkedIn integration (Phase 2)
export LINKEDIN_CLIENT_ID='your-linkedin-client-id'
export LINKEDIN_CLIENT_SECRET='your-linkedin-client-secret'
```

#### Option B: Create .env file (Recommended)
```bash
# Create .env file in project root
cat > .env << 'EOF'
ANTHROPIC_API_KEY=your-anthropic-api-key
LINKEDIN_CLIENT_ID=your-linkedin-client-id
LINKEDIN_CLIENT_SECRET=your-linkedin-client-secret
EOF
```

### 3. Testing Modes

#### 🧪 **Demo Mode (No API Keys Required)**
```bash
# Launch without any setup - uses template fallback
python3 web_app.py
```
- Upload CSV files ✅
- Review interface ✅
- Export functionality ✅
- AI email generation ❌ (shows templates instead)

#### 🤖 **AI Mode (API Key Required)**
```bash
# With Anthropic API key
export ANTHROPIC_API_KEY='your-key'
python3 web_app.py
```
- Full AI email generation ✅
- Personalization features ✅
- All demo mode features ✅

#### 📧 **Full Mode (All APIs)**
```bash
# With all credentials set up
export ANTHROPIC_API_KEY='your-key'
# + credentials.json in project root
python3 web_app.py
```
- Gmail draft creation ✅
- All AI mode features ✅

## ✅ Quick System Test

Before starting, run this test to verify everything works:
```bash
python3 test_app.py
```

This will check:
- ✅ Python version and dependencies
- ✅ Core module imports  
- ✅ Environment setup
- ✅ Template availability

## 🧪 Testing Scenarios

### Basic Functionality Test
1. **Upload CSV**: Use sample contacts with name, email, company columns
2. **Review Interface**: Check email preview and approval workflow
3. **Export**: Download generated emails as CSV/JSON

### Sample CSV Format
```csv
name,email,company,title
John Smith,john@company.com,TechCorp,CTO
Jane Doe,jane@startup.com,StartupInc,CEO
Bob Johnson,bob@enterprise.com,BigCorp,VP Sales
```

### Advanced Testing
1. **Campaign Goals**: Test different campaign objectives
2. **Email Quality**: Review AI-generated personalization
3. **Gmail Integration**: Create drafts in Gmail (requires setup)
4. **Error Handling**: Test with malformed CSV files

## 🔧 Troubleshooting

### Common Issues

**❌ "Module not found" errors**
```bash
pip3 install -r requirements.txt
```

**❌ "Permission denied" on scripts**
```bash
chmod +x start_web.sh
chmod +x setup-auth.sh
```

**❌ "Port already in use"**
```bash
# Kill existing Flask processes
pkill -f "python3 web_app.py"
# Or use different port
python3 web_app.py --port 5001
```

**❌ Gmail authentication issues**
```bash
# Run setup script
./setup-auth.sh
```

### Testing Without Gmail
If you get Gmail errors but want to test other features:
1. Don't worry about `credentials.json` warnings
2. Skip Gmail draft creation features
3. Focus on CSV processing and email generation

## 🌐 Sharing with Testers

### For Internal Testing
```bash
# Share repository access
git clone https://github.com/mack-donna/email-crm-audit.git
cd email-crm-audit
./start_web.sh
```

### For External Demo
```bash
# Run on network-accessible IP
python3 web_app.py --host 0.0.0.0 --port 5000
```
Then share: `http://your-ip-address:5000`

⚠️ **Security Note**: Only expose on trusted networks. The app currently doesn't have authentication.

## 📊 Test Data

### Sample Contacts CSV
Create `test-contacts.csv`:
```csv
name,email,company,title,notes
Sarah Wilson,sarah@techstartup.com,TechStartup Inc,Founder,Met at conference
Mike Chen,mike@retailcorp.com,RetailCorp,CMO,Interested in automation
Lisa Johnson,lisa@consulting.com,ConsultingPro,Partner,Referral from John
```

### Expected Outputs
- **JSON Campaign File**: Contains all contact data and generated emails
- **CSV Export**: Ready-to-import email list
- **Gmail Drafts**: Automatically created in Gmail (if configured)

## 🚀 Production Deployment Considerations

### Security
- [ ] Add authentication/login system
- [ ] Secure API key storage
- [ ] HTTPS/SSL certificates
- [ ] Rate limiting

### Performance
- [ ] Database storage (currently JSON files)
- [ ] Async processing for large contact lists
- [ ] Caching for repeated research

### Monitoring
- [ ] Logging system
- [ ] Error tracking
- [ ] Usage analytics

---

## 📞 Support

**For Testing Issues:**
1. Check logs in terminal where you started the app
2. Try demo mode first (no API keys)
3. Review troubleshooting section above

**For Development:**
- See [ARCHITECTURAL_DECISIONS.md](ARCHITECTURAL_DECISIONS.md) for technical details
- Check [SESSION_LOG.md](SESSION_LOG.md) for development history
- Review [PHASE_2_ENHANCEMENTS.md](PHASE_2_ENHANCEMENTS.md) for upcoming features

---

**Happy Testing!** 🎉