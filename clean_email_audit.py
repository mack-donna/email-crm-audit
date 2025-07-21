#!/usr/bin/env python3
print("🚀 Starting Gmail Contact Extraction")
print("Script is running...")

try:
    import os
    import csv
    import re
    from datetime import datetime, timedelta
    print("✓ Basic imports successful")
    
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    print("✓ Google API imports successful")
    
except Exception as e:
    print(f"❌ Import error: {e}")
    exit(1)

print("✓ All imports successful - script should work")
print("Now testing Gmail connection...")

try:
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    creds = None
    
    if os.path.exists('token.json'):
        print("✓ Found existing token.json")
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        print("❌ No token.json found")
    
    if not creds or not creds.valid:
        print("❌ Need to refresh or create new credentials")
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("Creating new token...")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        print("✓ Token saved")
    
    print("✓ Credentials valid, building Gmail service...")
    gmail_service = build('gmail', 'v1', credentials=creds)
    print("✓ Gmail API connected successfully!")
    
    # Test a simple API call
    print("Testing Gmail API with a simple call...")
    results = gmail_service.users().messages().list(userId='me', maxResults=1).execute()
    messages = results.get('messages', [])
    print(f"✓ Test successful - found {len(messages)} message(s) in first batch")
    
except Exception as e:
    print(f"❌ Gmail connection error: {e}")
    import traceback
    traceback.print_exc()

print("✅ Debug test completed!")
