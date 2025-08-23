# Email Outreach Automation System

An intelligent system that transforms cold Salesforce contacts into personalized email outreach campaigns by analyzing Gmail interaction history and researching public information.

## 🎯 Project Overview

This tool helps business development professionals:
- **Save time**: Reduce contact research from 15-30 minutes to 2-3 minutes per contact
- **Personalize at scale**: Generate tailored emails for 50+ contacts daily
- **Improve response rates**: Target 15-25% response rates through intelligent personalization
- **Learn and improve**: System gets smarter with each use through feedback capture
- **E-commerce integration**: Convert browse/cart abandoners into customers with Klaviyo flows

## ⚡ Quick Start

### Installation & Setup
```bash
# Clone the repository
git clone https://github.com/mack-donna/email-crm-audit.git
cd email-crm-audit

# Install dependencies (Python 3.9+ required)
pip install -r requirements.txt

# Set up API key
export ANTHROPIC_API_KEY='your-api-key'

# Configure Gmail (follow GMAIL_API_SETUP.md)
# Download credentials.json from Google Cloud Console
```

### Simple Usage
```bash
# Modern Python 3 entry point (recommended)
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
4. **Dependencies**: Run `pip install -r requirements.txt`

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

## 📊 Current Status

### ✅ **COMPLETE** - All Core Modules + Klaviyo Integration!
- **Phase 1**: Solution design and architecture ✅
- **Module 1**: CSV contact processing with validation ✅
- **Module 2**: Gmail API integration and email analysis ✅  
- **Module 3**: Public information research system ✅
- **Module 4**: AI-powered email generation ✅
- **Module 5**: Human review interface ✅
- **Module 6**: Learning engine ✅
- **Module 7**: Workflow orchestrator ✅
- **Module 8**: Full system integration ✅
- **Module 9**: Klaviyo e-commerce flow integration 🆕

### 🎯 **Ready for Production Use**
The system successfully:
- Processes CSV contacts with validation
- Analyzes Gmail interaction history
- Researches public company information  
- Generates personalized emails with AI
- Provides streamlined review workflow
- Learns from successful patterns
- Coordinates end-to-end campaigns
- Exports ready-to-send emails
- **NEW**: Integrates with Klaviyo for e-commerce prospect qualification

## 🔧 Technical Details

### GitHub Actions
The repository includes automated CI/CD workflows that:
- Test Python compatibility across versions 2.7-3.10
- Validate documentation completeness
- Run weekly security scans on dependencies
- Generate test reports and code metrics

### Design Principles
- **Modular**: Each component works independently for easy testing
- **Learning-ready**: Data structures designed for future ML enhancement
- **Execution-focused**: Working system first, sophistication later
- **Human-in-the-loop**: AI assists but humans maintain control

### Technology Stack
- **Language**: Python (stdlib focus for compatibility)
- **APIs**: Gmail API, Claude API, Klaviyo API
- **Storage**: JSON files → SQLite (future)
- **Logging**: Comprehensive debugging support
- **E-commerce**: Klaviyo, Shopify metafields, HeyGen video API

## 📝 Documentation

- [Solution Specification](OUTREACH_AUTOMATION_SOLUTION_SPEC.md) - Detailed system design
- [Architecture Decisions](ARCHITECTURAL_DECISIONS.md) - Technical choices explained
- [Gmail Setup Guide](GMAIL_API_SETUP.md) - Step-by-step API configuration
- [Klaviyo Flows Specification](KLAVIYO_FLOWS_SPEC.md) - E-commerce automation flows
- [Session Logs](SESSION_LOG.md) - Development history and decisions

## 🤝 Contributing

This is currently a private project in active development. The modular architecture makes it easy to contribute to individual components.

## 📄 License

Private project - All rights reserved

## 🙏 Acknowledgments

Built with assistance from Claude Code (Anthropic) using a collaborative human-AI development approach.