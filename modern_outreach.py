#!/usr/bin/env python3
"""
Modern Python 3 Entry Point for Email Outreach Automation
Uses f-strings, type hints, pathlib, and modern Python features
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
import os
import sys
import asyncio
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from workflow_orchestrator import WorkflowOrchestrator
from gmail_drafts_manager import GmailDraftsManager

def print_banner() -> None:
    """Print welcome banner with modern string formatting."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║    🚀 EMAIL OUTREACH AUTOMATION SYSTEM (Python 3.13)        ║
║         Transform Cold Contacts into Warm Conversations      ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_requirements() -> Dict[str, bool]:
    """Check system requirements and API keys."""
    requirements = {
        'anthropic_api_key': bool(os.environ.get('ANTHROPIC_API_KEY')),
        'gmail_credentials': Path('credentials.json').exists(),
        'beautifulsoup': True,  # Now installed
        'python_version': sys.version_info >= (3, 9)
    }
    
    print("\n📋 SYSTEM REQUIREMENTS CHECK:")
    
    for requirement, status in requirements.items():
        status_icon = "✅" if status else "❌"
        requirement_name = requirement.replace('_', ' ').title()
        print(f"  {status_icon} {requirement_name}")
        
        if requirement == 'anthropic_api_key' and not status:
            print("    💡 Set with: export ANTHROPIC_API_KEY='your-key'")
        elif requirement == 'gmail_credentials' and not status:
            print("    💡 Download from Google Cloud Console")
    
    return requirements

async def run_campaign_async(
    csv_file: Path, 
    campaign_name: str, 
    create_gmail_drafts: bool = True,
    auto_approve: bool = False
) -> Optional[Dict[str, Any]]:
    """Run campaign asynchronously (future enhancement)."""
    # For now, run synchronously, but structure is ready for async
    return run_campaign_sync(csv_file, campaign_name, create_gmail_drafts, auto_approve)

def run_campaign_sync(
    csv_file: Path, 
    campaign_name: str, 
    create_gmail_drafts: bool = True,
    auto_approve: bool = False
) -> Optional[Dict[str, Any]]:
    """Run outreach campaign with modern Python features."""
    
    if not csv_file.exists():
        print(f"❌ CSV file not found: {csv_file}")
        return None
    
    print(f"\n🎯 STARTING CAMPAIGN: {campaign_name}")
    print(f"📄 Processing: {csv_file}")
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Initialize orchestrator
        orchestrator = WorkflowOrchestrator()
        
        # Configure for Python 3
        config = {
            'csv_file': str(csv_file),
            'campaign_name': campaign_name,
            'batch_size': 5,
            'enable_gmail_history': True,
            'enable_learning': True,
            'auto_approve': auto_approve
        }
        
        # Run the campaign
        results = orchestrator.run_campaign(config)
        
        # Create Gmail drafts if requested
        if create_gmail_drafts and results:
            create_gmail_drafts_from_results(results)
        
        return results
        
    except Exception as e:
        print(f"❌ Campaign failed: {e}")
        return None

def create_gmail_drafts_from_results(results: Dict[str, Any]) -> None:
    """Create Gmail drafts from campaign results."""
    print("\n📧 CREATING GMAIL DRAFTS...")
    
    # Find the latest campaign file
    campaign_files = list(Path('outreach_campaigns').glob('*.json'))
    
    if not campaign_files:
        print("❌ No campaign files found")
        return
    
    latest_file = max(campaign_files, key=lambda p: p.stat().st_mtime)
    print(f"📁 Using: {latest_file}")
    
    # Create drafts
    drafts_manager = GmailDraftsManager()
    drafts = drafts_manager.create_drafts_from_campaign(str(latest_file))
    
    if drafts:
        print(f"✅ Created {len(drafts)} Gmail drafts:")
        for draft in drafts:
            print(f"   📧 {draft['to_email']} (ID: {draft['draft_id']})")
    else:
        print("❌ No drafts created")

def main() -> None:
    """Modern main function with type hints and f-strings."""
    print_banner()
    
    # Check requirements
    requirements = check_requirements()
    
    if not requirements['python_version']:
        print("❌ Python 3.9+ required")
        sys.exit(1)
    
    # Set API key if available
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("\n⚠️  No ANTHROPIC_API_KEY found. Using template fallbacks.")
        response = input("Continue anyway? (y/n): ").lower()
        if response != 'y':
            sys.exit(1)
    
    # Get CSV file
    if len(sys.argv) > 1:
        csv_file = Path(sys.argv[1])
    else:
        csv_path = input("\n📄 Enter CSV file path (or press Enter for simple_test.csv): ").strip()
        csv_file = Path(csv_path) if csv_path else Path('simple_test.csv')
    
    # Get campaign name
    if len(sys.argv) > 2:
        campaign_name = sys.argv[2]
    else:
        campaign_name = input("📝 Campaign name (or press Enter for default): ").strip()
        if not campaign_name:
            campaign_name = f"Python 3 Campaign {datetime.now().strftime('%m/%d %H:%M')}"
    
    # Options
    create_drafts = input("📧 Create Gmail drafts? (Y/n): ").lower() != 'n'
    auto_approve = input("🤖 Auto-approve emails for testing? (y/N): ").lower() == 'y'
    
    # Run campaign
    print("\n" + "="*60)
    results = run_campaign_sync(csv_file, campaign_name, create_drafts, auto_approve)
    
    if results:
        print(f"\n🎉 Campaign '{campaign_name}' completed successfully!")
        print(f"📊 Check outreach_campaigns/ folder for results")
        if create_drafts:
            print(f"📧 Check Gmail drafts folder")
    else:
        print("\n❌ Campaign failed")

if __name__ == "__main__":
    main()