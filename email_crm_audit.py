#!/usr/bin/env python3
"""
Simple Email-to-CRM Audit Tool
Compares Gmail contacts with Salesforce contacts and generates a report
"""

import os
import csv
import json
from datetime import datetime, timedelta
from collections import defaultdict
import re

# You'll need to install these packages (instructions below)
# pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client simple-salesforce

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from simple_salesforce import Salesforce

class EmailCRMAudit:
    def __init__(self):
        self.gmail_service = None
        self.sf = None
        self.email_contacts = []
        self.sf_contacts = []
        self.missing_contacts = []
        
    def setup_gmail(self):
        """Setup Gmail API connection"""
        SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
        creds = None
        
        # Token file stores the user's access and refresh tokens
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        self.gmail_service = build('gmail', 'v1', credentials=creds)
        print("✓ Gmail API connected successfully")
    
    def setup_salesforce(self):
        """Setup Salesforce connection"""
        # Read Salesforce credentials from environment variables or config
        username = os.getenv('SF_USERNAME') or input("Enter Salesforce username: ")
        password = os.getenv('SF_PASSWORD') or input("Enter Salesforce password: ")
        security_token = os.getenv('SF_SECURITY_TOKEN') or input("Enter Salesforce security token: ")
        
        try:
            self.sf = Salesforce(username=username, password=password, security_token=security_token)
            print("✓ Salesforce connected successfully")
        except Exception as e:
            print(f"❌ Salesforce connection failed: {e}")
            return False
        return True
    
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
        
        # Handle formats like "John Doe <john@example.com>"
        name_match = re.search(r'^([^<]+)<', email_string)
        if name_match:
            return name_match.group(1).strip().strip('"')
        
        return None
    
    def is_business_email(self, email, subject=""):
        """Simple filter to identify business emails"""
        if not email:
            return False
        
        # Filter out obvious non-business emails
        exclude_patterns = [
            'noreply', 'no-reply', 'automated', 'notification', 'support',
            'newsletter', 'unsubscribe', 'marketing', 'promo'
        ]
        
        email_lower = email.lower()
        subject_lower = subject.lower()
        
        # Check if email contains exclude patterns
        for pattern in exclude_patterns:
            if pattern in email_lower or pattern in subject_lower:
                return False
        
        # Filter out common non-business domains
        exclude_domains = [
            'anthropic.com', 'gusto.com', 'stripe.com', 'quickbooks',
            'mercury.com', 'ziptie.dev'  # Add your service provider domains
        ]
        
        for domain in exclude_domains:
            if domain in email_lower:
                return False
        
        return True
    
    def get_recent_emails(self, days_back=30):
        """Get emails from the last X days"""
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Format for Gmail API
            query = f'after:{start_date.strftime("%Y/%m/%d")}'
            
            print(f"🔍 Searching emails from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            
            # Get message list
            results = self.gmail_service.users().messages().list(
                userId='me', q=query, maxResults=500
            ).execute()
            
            messages = results.get('messages', [])
            print(f"📧 Found {len(messages)} emails to analyze")
            
            email_contacts = {}
            
            for i, message in enumerate(messages):
                if i % 50 == 0:
                    print(f"   Processing email {i+1}/{len(messages)}")
                
                try:
                    # Get full message
                    msg = self.gmail_service.users().messages().get(
                        userId='me', id=message['id']
                    ).execute()
                    
                    headers = msg['payload'].get('headers', [])
                    
                    # Extract relevant headers
                    subject = ""
                    from_email = ""
                    to_emails = []
                    cc_emails = []
                    
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
                    
                    # Process all email addresses found
                    all_emails = [from_email] + to_emails + cc_emails
                    
                    for email_string in all_emails:
                        email = self.extract_email_address(email_string)
                        name = self.extract_name_from_email(email_string)
                        
                        if email and email != 'stu@sentient-sf.com' and self.is_business_email(email, subject):
                            if email not in email_contacts:
                                email_contacts[email] = {
                                    'email': email,
                                    'name': name or email.split('@')[0],
                                    'domain': email.split('@')[1],
                                    'first_seen': datetime.now(),
                                    'last_seen': datetime.now(),
                                    'email_count': 0,
                                    'subjects': []
                                }
                            
                            # Update contact info
                            contact = email_contacts[email]
                            contact['email_count'] += 1
                            contact['last_seen'] = datetime.now()
                            if subject and subject not in contact['subjects']:
                                contact['subjects'].append(subject[:100])  # Limit length
                            
                            # Update name if we have a better one
                            if name and len(name) > len(contact['name']):
                                contact['name'] = name
                
                except Exception as e:
                    print(f"   Error processing email {i+1}: {e}")
                    continue
            
            self.email_contacts = list(email_contacts.values())
            print(f"✓ Found {len(self.email_contacts)} unique business contacts")
            
        except Exception as e:
            print(f"❌ Error fetching emails: {e}")
    
    def get_salesforce_contacts(self):
        """Get all contacts from Salesforce"""
        try:
            print("🔍 Fetching Salesforce contacts...")
            
            # Query all contacts with email addresses
            query = "SELECT Id, Name, Email, Title, Account.Name FROM Contact WHERE Email != null"
            results = self.sf.query_all(query)
            
            self.sf_contacts = []
            for record in results['records']:
                self.sf_contacts.append({
                    'id': record['Id'],
                    'name': record['Name'],
                    'email': record['Email'].lower() if record['Email'] else '',
                    'title': record.get('Title', ''),
                    'company': record['Account']['Name'] if record.get('Account') else ''
                })
            
            print(f"✓ Found {len(self.sf_contacts)} Salesforce contacts")
            
        except Exception as e:
            print(f"❌ Error fetching Salesforce contacts: {e}")
    
    def compare_contacts(self):
        """Compare email contacts with Salesforce contacts"""
        print("🔄 Comparing contacts...")
        
        # Create lookup of Salesforce emails
        sf_emails = {contact['email'] for contact in self.sf_contacts}
        
        # Find missing contacts
        self.missing_contacts = []
        for email_contact in self.email_contacts:
            if email_contact['email'] not in sf_emails:
                # Score the contact based on email frequency and recency
                score = self.score_contact(email_contact)
                email_contact['priority_score'] = score
                self.missing_contacts.append(email_contact)
        
        # Sort by priority score
        self.missing_contacts.sort(key=lambda x: x['priority_score'], reverse=True)
        
        print(f"✓ Found {len(self.missing_contacts)} contacts missing from Salesforce")
    
    def score_contact(self, contact):
        """Score contact based on interaction frequency and recency"""
        score = 0
        
        # Email frequency (0-40 points)
        score += min(contact['email_count'] * 5, 40)
        
        # Recency (0-30 points)
        days_since_last = (datetime.now() - contact['last_seen']).days
        if days_since_last <= 7:
            score += 30
        elif days_since_last <= 30:
            score += 20
        elif days_since_last <= 90:
            score += 10
        
        # Domain credibility (0-30 points)
        business_domains = ['.com', '.org', '.net', '.gov', '.edu']
        if any(contact['domain'].endswith(d) for d in business_domains):
            score += 20
        
        # Professional email patterns (bonus points)
        if not any(personal in contact['domain'] for personal in ['gmail', 'yahoo', 'hotmail', 'aol']):
            score += 10
        
        return score
    
    def categorize_contact(self, contact):
        """Simple categorization based on email content"""
        subjects = ' '.join(contact['subjects']).lower()
        
        if any(word in subjects for word in ['project', 'proposal', 'presentation', 'deck']):
            return 'Client/Prospect'
        elif any(word in subjects for word in ['invoice', 'payment', 'billing']):
            return 'Vendor/Service'
        elif any(word in subjects for word in ['team', 'schedule', 'meeting']):
            return 'Team/Internal'
        else:
            return 'Network/Other'
    
    def generate_report(self):
        """Generate a simple report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"email_crm_audit_{timestamp}.csv"
        
        print(f"📄 Generating report: {filename}")
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Priority', 'Name', 'Email', 'Domain', 'Category', 'Email_Count', 'Last_Contact', 'Sample_Subjects', 'Recommended_Action']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for contact in self.missing_contacts[:50]:  # Top 50 contacts
                priority = "High" if contact['priority_score'] > 60 else "Medium" if contact['priority_score'] > 30 else "Low"
                category = self.categorize_contact(contact)
                
                writer.writerow({
                    'Priority': priority,
                    'Name': contact['name'],
                    'Email': contact['email'],
                    'Domain': contact['domain'],
                    'Category': category,
                    'Email_Count': contact['email_count'],
                    'Last_Contact': contact['last_seen'].strftime('%Y-%m-%d'),
                    'Sample_Subjects': '; '.join(contact['subjects'][:3]),
                    'Recommended_Action': 'Add to Salesforce' if priority in ['High', 'Medium'] else 'Review'
                })
        
        # Generate summary report
        self.print_summary()
        print(f"✓ Detailed report saved as: {filename}")
    
    def print_summary(self):
        """Print a summary to console"""
        print("\n" + "="*60)
        print("📊 EMAIL-TO-CRM AUDIT SUMMARY")
        print("="*60)
        print(f"📧 Total email contacts analyzed: {len(self.email_contacts)}")
        print(f"🏢 Salesforce contacts found: {len(self.sf_contacts)}")
        print(f"❌ Missing from Salesforce: {len(self.missing_contacts)}")
        
        high_priority = sum(1 for c in self.missing_contacts if c['priority_score'] > 60)
        medium_priority = sum(1 for c in self.missing_contacts if 30 < c['priority_score'] <= 60)
        low_priority = sum(1 for c in self.missing_contacts if c['priority_score'] <= 30)
        
        print(f"🔴 High priority additions: {high_priority}")
        print(f"🟡 Medium priority additions: {medium_priority}")
        print(f"⚪ Low priority additions: {low_priority}")
        
        if high_priority > 0:
            print("\n🔴 TOP HIGH PRIORITY CONTACTS TO ADD:")
            for contact in self.missing_contacts[:5]:
                if contact['priority_score'] > 60:
                    print(f"   • {contact['name']} ({contact['email']}) - {contact['email_count']} emails")
        
        print("\n" + "="*60)
    
    def run_audit(self):
        """Run the complete audit process"""
        print("🚀 Starting Email-to-CRM Audit")
        print("-" * 40)
        
        # Setup connections
        self.setup_gmail()
        if not self.setup_salesforce():
            return
        
        # Fetch data
        self.get_recent_emails()
        self.get_salesforce_contacts()
        
        # Analyze
        self.compare_contacts()
        
        # Report
        self.generate_report()
        
        print("\n✅ Audit completed successfully!")

if __name__ == "__main__":
    audit = EmailCRMAudit()
    audit.run_audit()
