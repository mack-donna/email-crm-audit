#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Outreach Automation System - Main Entry Point
Complete end-to-end personalized email generation for business development.
"""

import argparse
import os
import sys
import json
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflow_orchestrator import WorkflowOrchestrator


def print_banner():
    """Print welcome banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║          EMAIL OUTREACH AUTOMATION SYSTEM                    ║
║  Transform Cold Contacts into Personalized Outreach          ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_capabilities():
    """Print system capabilities."""
    print("\n📋 SYSTEM CAPABILITIES:")
    print("  ✓ Process Salesforce CSV exports")
    print("  ✓ Analyze Gmail interaction history")
    print("  ✓ Research public company information")
    print("  ✓ Generate personalized emails with AI")
    print("  ✓ Review and approve interface")
    print("  ✓ Learn from successful patterns")
    print("  ✓ Export ready-to-send campaigns\n")


def load_config(config_file=None):
    """Load configuration from file or use defaults."""
    default_config = {
        'gmail_credentials': 'credentials.json',
        'gmail_token': 'token.pickle',
        'anthropic_api_key': os.environ.get('ANTHROPIC_API_KEY'),
        'batch_size': 10,
        'rate_limit_delay': 1.0,
        'enable_learning': True,
        'enable_email_history': True,
        'output_dir': 'outreach_campaigns'
    }
    
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
                print("✅ Loaded configuration from: {}".format(config_file))
        except Exception as e:
            print("⚠️  Error loading config file: {}".format(e))
            
    return default_config


def check_prerequisites(config):
    """Check if all prerequisites are met."""
    issues = []
    
    # Check for API key
    if not config.get('anthropic_api_key'):
        issues.append("❌ ANTHROPIC_API_KEY environment variable not set")
        issues.append("   Set it with: export ANTHROPIC_API_KEY='your-api-key'")
        
    # Check for Gmail credentials if enabled
    if config.get('enable_email_history'):
        if not os.path.exists(config['gmail_credentials']):
            issues.append("❌ Gmail credentials.json not found")
            issues.append("   Follow setup instructions in GMAIL_API_SETUP.md")
            
    # Create output directory if needed
    if not os.path.exists(config['output_dir']):
        os.makedirs(config['output_dir'])
        print("📁 Created output directory: {}".format(config['output_dir']))
        
    if issues:
        print("\n⚠️  PREREQUISITES CHECK:")
        for issue in issues:
            print(issue)
        print("\nNote: System will work with limited functionality")
        
    return len(issues) == 0


def interactive_mode():
    """Run the system in interactive mode."""
    print_banner()
    print_capabilities()
    
    # Get CSV file
    print("📄 STEP 1: Select CSV file")
    csv_file = input("Enter path to CSV file (or drag & drop): ").strip().strip("'\"")
    
    if not os.path.exists(csv_file):
        print("❌ Error: CSV file not found")
        return
        
    # Get campaign name
    print("\n📝 STEP 2: Name your campaign")
    campaign_name = input("Campaign name (press Enter for auto): ").strip()
    if not campaign_name:
        campaign_name = "campaign_{}".format(datetime.now().strftime("%Y%m%d_%H%M%S"))
        
    # Configuration options
    print("\n⚙️  STEP 3: Configuration")
    print("1. Use default settings")
    print("2. Customize settings")
    choice = input("Choice [1/2]: ").strip()
    
    config = load_config()
    
    if choice == "2":
        # Batch size
        batch_size = input("Batch size [{}]: ".format(config['batch_size'])).strip()
        if batch_size.isdigit():
            config['batch_size'] = int(batch_size)
            
        # Gmail integration
        use_gmail = input("Enable Gmail history analysis? [Y/n]: ").strip().lower()
        config['enable_email_history'] = use_gmail != 'n'
        
        # Learning system
        use_learning = input("Enable learning system? [Y/n]: ").strip().lower()
        config['enable_learning'] = use_learning != 'n'
        
    # Check prerequisites
    check_prerequisites(config)
    
    # Confirm start
    print("\n" + "="*60)
    print("📊 READY TO START:")
    print("  CSV File: {}".format(csv_file))
    print("  Campaign: {}".format(campaign_name))
    print("  Batch Size: {}".format(config['batch_size']))
    print("  Gmail Integration: {}".format("Enabled" if config['enable_email_history'] else "Disabled"))
    print("  Learning System: {}".format("Enabled" if config['enable_learning'] else "Disabled"))
    print("="*60)
    
    proceed = input("\nStart campaign? [Y/n]: ").strip().lower()
    if proceed == 'n':
        print("Campaign cancelled")
        return
        
    # Run campaign
    try:
        orchestrator = WorkflowOrchestrator(config)
        summary = orchestrator.run_campaign(csv_file, campaign_name)
        
        # Show results location
        if summary['emails_approved'] > 0:
            print("\n📍 RESULTS LOCATION:")
            print("  Campaign files saved in: {}".format(config['output_dir']))
            print("  Look for: {}_{}.json".format(campaign_name, datetime.now().strftime("%Y%m%d")))
            
    except Exception as e:
        print("\n❌ Error running campaign: {}".format(e))
        raise


def batch_mode(args):
    """Run the system in batch mode with command-line arguments."""
    print_banner()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override with command-line options
    if args.batch_size:
        config['batch_size'] = args.batch_size
    if args.no_gmail:
        config['enable_email_history'] = False
    if args.no_learning:
        config['enable_learning'] = False
    if args.output_dir:
        config['output_dir'] = args.output_dir
        
    # Set auto-approve if specified
    if args.auto_approve:
        os.environ['AUTO_APPROVE_EMAILS'] = 'true'
        
    # Check prerequisites
    check_prerequisites(config)
    
    # Run campaign
    try:
        orchestrator = WorkflowOrchestrator(config)
        summary = orchestrator.run_campaign(args.csv_file, args.campaign)
        
        # Exit with appropriate code
        sys.exit(0 if summary['success'] else 1)
        
    except Exception as e:
        print("\n❌ Error: {}".format(e))
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Email Outreach Automation System - Transform cold contacts into personalized outreach',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (recommended for first use)
  python outreach_automation.py
  
  # Process contacts with default settings
  python outreach_automation.py contacts.csv
  
  # Custom campaign with options
  python outreach_automation.py contacts.csv --campaign "Q1 Outreach" --batch-size 20
  
  # Fully automated mode
  python outreach_automation.py contacts.csv --auto-approve --no-gmail
  
For setup instructions, see README.md
        """
    )
    
    # Positional arguments
    parser.add_argument('csv_file', nargs='?', 
                      help='Path to CSV file with contacts')
    
    # Optional arguments
    parser.add_argument('-c', '--campaign', 
                      help='Campaign name')
    parser.add_argument('-b', '--batch-size', type=int,
                      help='Number of contacts per batch (default: 10)')
    parser.add_argument('--config', 
                      help='Path to configuration file')
    parser.add_argument('-o', '--output-dir',
                      help='Output directory for results')
    
    # Feature flags
    parser.add_argument('--no-gmail', action='store_true',
                      help='Disable Gmail integration')
    parser.add_argument('--no-learning', action='store_true',
                      help='Disable learning system')
    parser.add_argument('--auto-approve', action='store_true',
                      help='Auto-approve all generated emails (for automation)')
    
    # Utility commands
    parser.add_argument('--version', action='version', 
                      version='Email Outreach Automation v1.0')
    
    args = parser.parse_args()
    
    # Decide mode based on arguments
    if args.csv_file:
        # Batch mode with command-line arguments
        batch_mode(args)
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()