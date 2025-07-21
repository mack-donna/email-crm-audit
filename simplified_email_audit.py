#!/usr/bin/env python3
"""
Gmail Contact Extractor - Clean Version
Extracts business contacts from Gmail for manual Salesforce comparison
"""

import os
import csv
import re
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

class EmailContactExtractor:
    def __init__(self):
        self.gmail_service = None
        self.email_contacts = []
        
    def setup_gmail(self):
        """Setup Gmail API connection"""
        SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
        creds = None
        
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        self.gmail_service = build('gmail', 'v1', credentials=creds)
        print("✓ Gmail API connected successfully")
    
    def extract_email_address(self, email_string):
        """Extract clean email address from various formats"""
        if not email_string:
            return None
        
        # Handle formats like "John Doe <john@example.com>"
        email_match = re.search(r'<([^>]+)>', email_string)
        if email_match:
            return email_match.group(1).lower()
        
        # Handle direct email addresses
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', email_string)
        if email_match:
            return email_match.group(0).lower()
        
        return None
    
    def extract_name_from_email(self, email_string):
        """Extract name from email string"""
        if not email_string:
            return None
        
        name_match = re.search(r'^([^<]+)<', email_string)
        if name_match:
            return name_match.group(1).strip().strip('"')
        
        return None
    
    def extract_company_from_email(self, email):
        """Extract likely company name from email domain"""
        if not email or '@' not in email:
            return ""
        
        domain = email.split('@')[1]
        domain = domain.replace('www.', '')
        domain = domain.split('.')[0]
        company = domain.replace('-', ' ').replace('_', ' ').title()
        
        return company
    
    def is_business_email(self, email, subject=""):
        """Simple filter to identify business emails"""
        if not email:
            return False
        
        exclude_patterns = [
            'noreply', 'no-reply', 'automated', 'notification', 'support',
            'newsletter', 'unsubscribe', 'marketing', 'promo', 'donotreply'
        ]
        
        email_lower = email.lower()
        subject_lower = subject.lower()
        
        for pattern in exclude_patterns:
            if pattern in email_lower or pattern in subject_lower:
                return False
        
        exclude_domains = [
            'anthropic.com', 'gusto.com', 'stripe.com', 'quickbooks',
            'mercury.com', 'ziptie.dev', 'google.com', 'apple.com',
            'microsoft.com', 'adobe.com', 'zoom.us'
        ]
        
        for domain in exclude_domains:
            if domain in email_lower:
                return False
        
        return True
    
    def get_recent_emails(self, days_back=60):
        """Get emails from the last X days"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            query = f'after:{start_date.strftime("%Y/%m/%d")}'
            
            print(f"🔍 Searching emails from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            
            results = self.gmail_service.users().messages().list(
                userId='me', q=query, maxResults=1000
            ).execute()
            
            messages = results.get('messages', [])
            print(f"📧 Found {len(messages)} emails to analyze")
            
            email_contacts = {}
            
            for i, message in enumerate(messages):
                if i % 100 == 0:
                    print(f"   Processing email {i+1}/{len(messages)}")
                
                try:
                    msg = self.gmail_service.users().messages().get(
                        userId='me', id=message['id']
                    ).execute()
                    
                    headers = msg['payload'].get('headers', [])
                    
                    subject = ""
                    from_email = ""
                    to_emails = []
                    cc_emails = []
                    date_header = ""
                    
                    for header in headers:
                        name = header['name'].lower()
                        value = header['value']
                        
                        if name == 'subject':
                            subject = value
                        elif name == 'from':
                            from_email = value
                        elif name == 'to':
                            to_emails = value.split(',')
                        elif name == 'cc':
                            cc_emails = value.split(',')
                        elif name == 'date':
                            date_header = value
                    
                    all_emails = [from_email] + to_emails + cc_emails
                    
                    for email_string in all_emails:
                        email = self.extract_email_address(email_string)
                        name = self.extract_name_from_email(email_string)
                        
                        if email and email != 'stu@sentient-sf.com' and self.is_business_email(email, subject):
                            if email not in email_contacts:
                                company = self.extract_company_from_email(email)
                                email_contacts[email] = {
                                    'name': name or email.split('@')[0].title(),
                                    'email': email,
                                    'company': company,
                                    'domain': email.split('@')[1],
                                    'first_seen': date_header or datetime.now().strftime('%Y-%m-%d'),
                                    'last_seen': date_header or datetime.now().strftime('%Y-%m-%d'),
                                    'email_count': 0,
                                    'subjects': [],
                                    'category': 'Unknown'
                                }
                            
                            contact = email_contacts[email]
                            contact['email_count'] += 1
                            contact['last_seen'] = date_header or datetime.now().strftime('%Y-%m-%d')
                            if subject and subject not in contact['subjects']:
                                contact['subjects'].append(subject[:100])
                            
                            if name and len(name) > len(contact['name']):
                                contact['name'] = name
                            
                            contact['category'] = self.categorize_contact(contact)
                
                except Exception as e:
                    print(f"   Error processing email {i+1}: {e}")
                    continue
            
            self.email_contacts = list(email_contacts.values())
            print(f"✓ Found {len(self.email_contacts)} unique business contacts")
            
        except Exception as e:
            print(f"❌ Error fetching emails: {e}")
    
    def categorize_contact(self, contact):
        """Simple categorization based on email content"""
        subjects = ' '.join(contact['subjects']).lower()
        domain = contact['domain'].lower()
        
        if any(word in subjects for word in ['project', 'proposal', 'presentation', 'deck', 'contract', 'sow']):
            return 'Client/Prospect'
        elif any(word in subjects for word in ['invoice', 'payment', 'billing', 'receipt']):
            return 'Vendor/Service'
        elif any(word in subjects for word in ['schedule', 'meeting', 'call', 'zoom']):
            return 'Business Contact'
        elif any(word in subjects for word in ['introduction', 'connect', 'networking']):
            return 'Network/Referral'
        elif any(personal in domain for personal in ['gmail', 'yahoo', 'hotmail', 'aol', 'icloud']):
            return 'Personal/Network'
        else:
            return 'Business Contact'
    
    def score_contact(self, contact):
        """Score contact based on interaction frequency and business potential"""
        score = 0
        
        score += min(contact['email_count'] * 5, 40)
        
        category_scores = {
            'Client/Prospect': 30,
            'Business Contact': 20,
            'Network/Referral': 15,
            'Vendor/Service': 10,
            'Personal/Network': 5
        }
        score += category_scores.get(contact['category'], 0)
        
        if not any(personal in contact['domain'] for personal in ['gmail', 'yahoo', 'hotmail', 'aol']):
            score += 20
        
        subjects_text = ' '.join(contact['subjects']).lower()
        professional_keywords = ['meeting', 'project', 'business', 'proposal', 'contract', 'partnership']
        keyword_count = sum(1 for keyword in professional_keywords if keyword in subjects_text)
        score += min(keyword_count * 2, 10)
        
        return score
    
    def generate_contact_export(self):
        """Generate CSV export for manual Salesforce comparison"""
        timestamp = dateti