#!/usr/bin/env python3
"""
Startup script for Email Outreach Automation
Handles environment setup and configuration
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✓ Loaded environment variables from .env file")
except ImportError:
    print("⚠️  python-dotenv not installed. Using system environment variables.")
    print("   Install with: pip install python-dotenv")

def check_requirements():
    """Check if all required environment variables and files are present"""
    issues = []
    warnings = []
    
    # Check for critical environment variables
    if not os.environ.get('ANTHROPIC_API_KEY'):
        issues.append("❌ ANTHROPIC_API_KEY not set - AI email generation will use templates")
        issues.append("   Set it in .env file or environment: export ANTHROPIC_API_KEY='sk-ant-...'")
    else:
        print("✓ Anthropic API key configured")
    
    # Check for Gmail credentials
    if not Path('credentials.json').exists():
        warnings.append("⚠️  credentials.json not found - Gmail draft creation will be disabled")
        warnings.append("   Follow the Gmail API setup guide to enable Gmail integration")
    else:
        print("✓ Gmail credentials found")
    
    # Check Flask secret key
    if os.environ.get('FLASK_SECRET_KEY') == 'dev-secret-key-change-in-production':
        warnings.append("⚠️  Using default Flask secret key - change for production")
    
    return issues, warnings

def main():
    """Main entry point"""
    print("\n🚀 Email Outreach Automation System")
    print("=" * 50)
    
    # Check requirements
    issues, warnings = check_requirements()
    
    # Show issues and warnings
    if issues:
        print("\n⚠️  Configuration Issues:")
        for issue in issues:
            print(issue)
    
    if warnings:
        print("\n📝 Warnings:")
        for warning in warnings:
            print(warning)
    
    # Import and run the Flask app
    print("\n" + "=" * 50)
    print("Starting Flask server...")
    print("=" * 50 + "\n")
    
    # Import here to ensure environment is loaded first
    from web_app import app
    
    # Get configuration from environment
    # Render uses PORT environment variable, default to 8080 for local
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # For production on Render, bind to all interfaces
    if os.environ.get('FLASK_ENV') == 'production':
        host = '0.0.0.0'
    
    print(f"📍 Server running at http://{host}:{port}")
    print("📊 Debug mode:", "ON" if debug else "OFF")
    print("\nPress CTRL+C to stop the server\n")
    
    # Run the Flask app
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    main()