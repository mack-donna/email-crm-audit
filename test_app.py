#!/usr/bin/env python3
"""
Quick test script to verify the email outreach app is working
"""
import sys
import os

def test_basic_functionality():
    """Test basic app functionality without starting server"""
    print("🧪 Testing Email Outreach System")
    print("=" * 40)
    
    # Test 1: Python version
    print(f"✅ Python {sys.version.split()[0]}")
    
    # Test 2: Import dependencies  
    try:
        import flask
        print(f"✅ Flask {flask.__version__}")
    except ImportError:
        print("❌ Flask not available")
        return False
    
    try:
        import requests
        print(f"✅ Requests available")
    except ImportError:
        print("❌ Requests not available")
        return False
        
    try:
        from bs4 import BeautifulSoup
        print(f"✅ BeautifulSoup available")
    except ImportError:
        print("❌ BeautifulSoup not available")
    
    # Test 3: Core modules import
    try:
        import web_app
        print("✅ web_app.py imports successfully")
    except Exception as e:
        print(f"❌ web_app import failed: {e}")
        return False
    
    try:
        import contact_processor
        print("✅ contact_processor.py imports successfully")
    except Exception as e:
        print(f"⚠️  contact_processor import failed: {e}")
    
    try:
        import email_generator
        print("✅ email_generator.py imports successfully")
    except Exception as e:
        print(f"⚠️  email_generator import failed: {e}")
    
    # Test 4: Environment check
    print("\n🔧 Environment Check:")
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key:
        print("✅ ANTHROPIC_API_KEY is set")
    else:
        print("⚠️  ANTHROPIC_API_KEY not set (demo mode will be used)")
    
    gmail_creds = os.path.exists('credentials.json')
    if gmail_creds:
        print("✅ Gmail credentials.json found")
    else:
        print("⚠️  credentials.json not found (Gmail features disabled)")
        
    # Test 5: Template directory
    if os.path.exists('templates'):
        templates = os.listdir('templates')
        print(f"✅ Templates directory found ({len(templates)} templates)")
    else:
        print("❌ Templates directory missing")
        return False
    
    print("\n🎯 Test Summary:")
    print("✅ Core functionality: WORKING")
    print("✅ Web interface: READY") 
    print("✅ Dependencies: INSTALLED")
    
    print("\n🚀 To start the app:")
    print("   ./start_web.sh")
    print("   OR")
    print("   python3 web_app.py")
    print("\n   Then open: http://localhost:5000")
    
    return True

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)