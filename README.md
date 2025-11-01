# Email Outreach Automation Platform

## 🚀 From Tool to SaaS Platform

An AI-powered email automation platform evolving from a Salesforce outreach tool into a comprehensive SaaS solution for e-commerce and B2B businesses. Now featuring advanced behavioral triggers, multi-platform integrations, and subscription-based deployment.

## 🎯 Platform Vision

**Current MVP**: Intelligent email generation with Gmail integration
**Target SaaS**: Complete email automation ecosystem with:
- **E-commerce triggers**: Cart abandonment, browse behavior, post-purchase flows
- **Platform integrations**: Shopify, Klaviyo, Google Analytics, and more
- **AI personalization**: Beyond templates - truly personalized content at scale
- **Behavioral automation**: Real-time response to customer actions
- **Multi-tenancy**: Support teams, brands, and enterprise accounts

## ⚡ Quick Start

### 🌐 Local Development
```bash
# Clone and setup
git clone https://github.com/mack-donna/email-crm-audit.git
cd email-crm-audit

# Install dependencies (Python 3.9+ required)
pip install -r requirements.txt

# Set up environment variables
export ANTHROPIC_API_KEY='your-api-key'
export FLASK_SECRET_KEY='your-secure-secret-key'

# Start the application
python3 run.py

# Access at: http://localhost:8080
```

### ☁️ Cloud Deployment (SaaS Mode)
```bash
# Deploy to Render.com (recommended for MVP)
# 1. Fork this repository
# 2. Connect to Render.com
# 3. Deploy using render.yaml configuration
# 4. Set environment variables in Render dashboard
```

### 🌐 Web Interface Features
- **Modern UI**: Tailwind CSS with Alpine.js
- **Campaign Management**: Create, review, and track campaigns
- **Gmail Integration**: One-click draft creation
- **CSV Processing**: Drag-and-drop contact uploads
- **Real-time Status**: API key validation and system health
- **Responsive Design**: Works on desktop and mobile

### Command Line Usage
```bash
# Modern Python 3 entry point
python3 modern_outreach.py

# Original entry point (still works)
python3 outreach_automation.py contacts.csv --campaign "Q1 Outreach"

# With Gmail drafts integration
python3 run_outreach_with_gmail.py
```

### Prerequisites
1. **Python 3.9+** (3.13+ recommended) - **Python 2.7 no longer supported**
2. **API Key**: Set `ANTHROPIC_API_KEY` environment variable
3. **Gmail Setup**: Follow [Gmail API Setup Guide](GMAIL_API_SETUP.md) for automatic drafts creation
4. **LinkedIn Setup (Optional)**: Follow [LinkedIn API Setup Guide](LINKEDIN_API_SETUP.md) for enhanced personalization
5. **Dependencies**: Run `pip install -r requirements.txt`

## 🏗️ Architecture

The system uses a modular design with 9 components:

1. **CSV Contact Processing** ✅ - Import and validate Salesforce exports
2. **Email History Analyzer** ✅ - Gmail API integration for interaction history
3. **Public Information Research** ✅ - Multi-source company/contact research
4. **AI Email Generation** ✅ - Claude API integration with multiple styles
5. **Human Review Interface** ✅ - Streamlined approval workflow
6. **Learning Engine** ✅ - Pattern recognition and continuous improvement
7. **Workflow Orchestrator** ✅ - End-to-end process management
8. **Main Integration** ✅ - Complete system with CLI interface
9. **Klaviyo Integration** 🆕 - E-commerce flow automation and prospect qualification

## 📁 Project Structure

```
email-crm-audit/
├── README.md                              # This file
├── outreach_automation.py                 # 🚀 MAIN ENTRY POINT
│
├── OUTREACH_AUTOMATION_SOLUTION_SPEC.md   # Solution specification
├── ARCHITECTURAL_DECISIONS.md             # Technical architecture
├── GMAIL_API_SETUP.md                     # Gmail API setup guide
├── SESSION_LOG.md                         # Development history
│
├── contact_processor.py                   # Module 1: CSV processing
├── email_history_analyzer.py              # Module 2: Gmail integration
├── public_info_researcher.py              # Module 3: Web research
├── email_generator.py                     # Module 4: AI generation
├── review_interface.py                    # Module 5: Human review
├── learning_engine.py                     # Module 6: Pattern learning
├── workflow_orchestrator.py               # Module 7: Coordination
├── klaviyo_integration.py                 # Module 9: Klaviyo flows
├── gmail_drafts_manager.py                # Gmail integration for drafts
│
├── modern_outreach.py                     # 🆕 Modern Python 3 entry point
├── run_outreach_with_gmail.py             # Gmail integration runner
├── test_modern_system.py                  # Python 3 modernization tests
│
├── KLAVIYO_FLOWS_SPEC.md                  # Klaviyo flow specifications
├── GITHUB_TOKEN_UPDATE.md                 # GitHub token management
├── requirements.txt                       # 🆕 Python dependencies
│
└── [output directories]                   # Campaign results, logs, data
```

## 🚀 Usage Examples

### Interactive Mode (Recommended)
```bash
python outreach_automation.py
```
Follow the prompts to:
1. Select your CSV file
2. Name your campaign  
3. Configure settings
4. Review and approve emails

### Command Line Mode
```bash
# Basic usage
python outreach_automation.py contacts.csv

# Custom campaign with options
python outreach_automation.py contacts.csv \
  --campaign "Q1 Outreach" \
  --batch-size 20 \
  --output-dir campaigns/

# Fully automated (for integration)
python outreach_automation.py contacts.csv \
  --auto-approve \
  --no-gmail
```

### Configuration File
Create `config.json`:
```json
{
  "anthropic_api_key": "your-api-key",
  "batch_size": 15,
  "enable_email_history": true,
  "enable_learning": true,
  "output_dir": "my_campaigns"
}
```

Then run: `python outreach_automation.py --config config.json contacts.csv`

### Gmail Integration (New!)
```bash
# Full automation with Gmail drafts creation
python3 run_outreach_with_gmail.py

# Manual Gmail drafts from campaign results
python3 gmail_drafts_manager.py "outreach_campaigns/My_Campaign.json"

# Test Gmail authentication
python3 gmail_drafts_manager.py
```

### Klaviyo Integration
```bash
# Process qualified prospects from Klaviyo flows
python3 klaviyo_integration.py

# Import Klaviyo exports into outreach system
python3 outreach_automation.py klaviyo_qualified_contacts.csv \
  --campaign "Klaviyo Re-engagement" \
  --source klaviyo
```

## 📊 Current Status & Roadmap

### ✅ **Phase 1: MVP Foundation (COMPLETED)**
- **Web Interface**: Flask app with modern UI ✅
- **AI Email Generation**: Claude API integration ✅
- **Gmail Integration**: Draft creation and API setup ✅
- **CSV Processing**: Contact import and validation ✅
- **Campaign Management**: History and tracking ✅
- **Deployment Ready**: Docker + Render.com configuration ✅

### 🔄 **Phase 2: Core Integrations (IN PROGRESS)**
- **Shopify Integration**: E-commerce data and triggers 🔄
- **Klaviyo Integration**: Email platform sync 🔄
- **Google Analytics**: Behavioral data collection 🔄
- **PostgreSQL Migration**: From file storage to database 🔄
- **Authentication System**: Multi-user support 🔄

### 🎯 **Phase 3: SaaS Features (PLANNED)**
- **Subscription Management**: Stripe integration ⬜
- **Multi-tenancy**: Workspace and team management ⬜
- **Behavioral Triggers**: Cart abandonment, browse behavior ⬜
- **Advanced Analytics**: Campaign performance metrics ⬜
- **API Platform**: Developer integrations ⬜

### 📈 **SaaS Pricing Tiers (Planned)**
- **Starter**: $49/month - 1,000 emails, 1 store
- **Growth**: $199/month - 10,000 emails, 3 stores  
- **Scale**: $499/month - 50,000 emails, unlimited stores
- **Enterprise**: Custom pricing with SLA and support

## 🔧 Technical Details

### Security Best Practices ⚠️
**CRITICAL:** Never commit API keys or secrets to the repository!

✅ **Do:**
- Use environment variables: `export ANTHROPIC_API_KEY='your-key'`
- Store tokens in macOS Keychain or secure credential managers
- Use `.gitignore` for sensitive files (`token.json`, `credentials.json`, etc.)
- Rotate API keys regularly (every 90 days recommended)

❌ **Don't:**
- Hardcode API keys in Python files
- Commit `token.json` or authentication files
- Share tokens in chat or documentation
- Use the same token across multiple projects

### GitHub Authentication Issues
If you encounter authentication problems:
1. **Test token validity:** `curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user`
2. **Check token scopes:** Ensure `repo` scope is enabled for private repositories
3. **Reset credential helper:** See [GITHUB_TOKEN_UPDATE.md](GITHUB_TOKEN_UPDATE.md) for detailed troubleshooting

### GitHub Actions
The repository includes automated CI/CD workflows that:
- Test Python compatibility across versions 3.9-3.13
- Validate documentation completeness
- Run weekly security scans on dependencies
- Generate test reports and code metrics

#### 🛡️ Claude Code Security Review (NEW!)
Automated security review powered by Claude Code runs on every pull request:
- **OWASP Top 10 vulnerability detection** - SQL injection, XSS, authentication issues
- **Python-specific security checks** - Command injection, path traversal, unsafe deserialization
- **Hardcoded secrets detection** - API keys, passwords, tokens
- **Dependency vulnerability scanning** - Automated checks with Bandit and Safety
- **AI-powered code analysis** - Claude reviews code for subtle security issues
- **PR comments** - Security findings posted directly to pull requests
- **Configurable severity thresholds** - Optional build blocking on critical issues

**Setup Requirements:**
1. Add `ANTHROPIC_API_KEY` to GitHub repository secrets
2. Configure security rules in `.github/security-review-config.yml`
3. Security review runs automatically on all PRs affecting code files

**Manual Trigger:**
```bash
# From GitHub Actions tab, run "Claude Code Security Review" workflow manually
# Choose scope: changed_files (default) or all_files
```

**View Results:**
- Security findings appear as PR comments
- Detailed reports available in Actions artifacts
- Critical vulnerabilities trigger build warnings (configurable)

### Design Principles
- **Security-first**: Environment variables and proper credential management
- **Modular**: Each component works independently for easy testing
- **Learning-ready**: Data structures designed for future ML enhancement
- **Execution-focused**: Working system first, sophistication later
- **Human-in-the-loop**: AI assists but humans maintain control

### Current Technology Stack
- **Backend**: Flask (Python 3.9+) → FastAPI (planned)
- **Frontend**: HTML/CSS/JavaScript with Tailwind CSS + Alpine.js
- **AI**: Anthropic Claude API for email generation
- **Email**: Gmail API for draft creation
- **Storage**: JSON files → PostgreSQL (migrating)
- **Deployment**: Docker + Render.com
- **CI/CD**: GitHub Actions

### Target SaaS Stack
- **Backend**: FastAPI with async operations
- **Frontend**: React/Next.js with TypeScript
- **Database**: PostgreSQL + TimescaleDB for analytics
- **Cache**: Redis for performance
- **Queue**: Celery + RabbitMQ for background jobs
- **Auth**: Auth0 for enterprise SSO
- **Payments**: Stripe for subscriptions
- **Integrations**: Shopify, Klaviyo, Google Analytics
- **Monitoring**: DataDog + Sentry

## 📝 Documentation

**Core Documentation**
- [SaaS Development Roadmap](SAAS_ROADMAP.md) - Complete platform evolution plan
- [Gmail Setup Guide](GMAIL_API_SETUP.md) - API configuration for email drafts
- [Render Deployment Guide](render.yaml) - Cloud deployment configuration

**Legacy Documentation**
- [Original Solution Spec](OUTREACH_AUTOMATION_SOLUTION_SPEC.md) - Initial CRM-focused design
- [Architecture Decisions](ARCHITECTURAL_DECISIONS.md) - Technical choices explained
- [Session Logs](SESSION_LOG.md) - Development history and decisions

## 🚀 Next Steps

1. **Deploy MVP**: Get the current system live on Render.com
2. **Add Integrations**: Shopify, Klaviyo, Google Analytics
3. **Database Migration**: Move from JSON to PostgreSQL
4. **Authentication**: Multi-user and team support
5. **Subscription Model**: Stripe integration and pricing tiers

## 📄 License

**Sentient SF** - All rights reserved

## 🙏 Built With

Developed with **Claude Code** (Anthropic) using collaborative human-AI development.
<\!-- Testing security review workflow -->
