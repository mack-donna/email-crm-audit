#!/usr/bin/env python3
"""
Run outreach automation with Gmail drafts integration using Python 3
"""

import os
import subprocess
import sys

def run_outreach_with_gmail_drafts(csv_file, campaign_name):
    """Run the full outreach automation with Gmail integration"""
    
    print("=== Email Outreach with Gmail Drafts ===")
    print(f"CSV file: {csv_file}")
    print(f"Campaign: {campaign_name}")
    print()
    
    # Set environment variables
    env = os.environ.copy()
    # Use existing ANTHROPIC_API_KEY from environment
    if 'ANTHROPIC_API_KEY' not in env:
        print("Warning: ANTHROPIC_API_KEY not found in environment")
        print("Set it with: export ANTHROPIC_API_KEY='your-key'")
        return False
    
    try:
        # Run the outreach automation with Python 3
        cmd = [
            'python3', 'outreach_automation.py', 
            csv_file, 
            '--campaign', campaign_name,
            '--auto-approve',  # Auto-approve for demo
            '--no-gmail'       # Skip Gmail history for now
        ]
        
        print("Running outreach automation...")
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # If emails were generated, create Gmail drafts
        if result.returncode == 0:
            print("\n=== Creating Gmail Drafts ===")
            
            # Find the latest campaign file
            import glob
            import json
            from datetime import datetime
            
            campaign_files = glob.glob(f"outreach_campaigns/{campaign_name}_*.json")
            if campaign_files:
                latest_file = max(campaign_files, key=os.path.getctime)
                print(f"Processing campaign file: {latest_file}")
                
                # Create Gmail drafts
                subprocess.run(['python3', 'gmail_drafts_manager.py', latest_file], env=env)
            else:
                print("No campaign files found")
        
    except Exception as e:
        print(f"Error running outreach automation: {e}")

def main():
    """Main function"""
    
    # Test with our simple dataset
    csv_file = 'simple_test.csv'
    campaign_name = 'Gmail Integration Test'
    
    if not os.path.exists(csv_file):
        print(f"CSV file not found: {csv_file}")
        return
    
    run_outreach_with_gmail_drafts(csv_file, campaign_name)

if __name__ == "__main__":
    main()