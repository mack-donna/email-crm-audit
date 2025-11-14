#!/usr/bin/env python3
"""
Simple Email-to-CRM Audit Tool
Compares Gmail contacts with Salesforce contacts and generates a report
"""

import os
import csv
import json
from datetime import datetime
from collections import defaultdict

# You'll need to install these packages (instructions below)
# pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client simple-salesforce

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from simple_salesforce import Salesforce

# Import shared email retrieval utility
from gmail_email_retriever import GmailEmailRetriever

class EmailCRMAudit:
    def __init__(self):
        self.gmail_service = None
        self.sf = None
        self.email_contacts = []
        self.sf_contacts = []
        self.missing_contacts = []
        self.email_retriever = None  # Will be initialized after Gmail setup

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
        # Initialize shared email retriever utility
        self.email_retriever = GmailEmailRetriever(
            gmail_service=self.gmail_service,
            user_email='stu@sentient-sf.com'
        )
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
    
    def get_recent_emails(self, days_back=30):
        """
        Get emails from the last X days using shared GmailEmailRetriever utility.

        This method now delegates to the shared utility for email retrieval.
        """
        # Use shared email retriever utility
        email_contacts = self.email_retriever.get_recent_emails(
            days_back=days_back,
            max_results=500,
            progress_interval=50
        )

        # Convert to list and store
        self.email_contacts = list(email_contacts.values())
        print("✓ Found {} unique business contacts".format(len(self.email_contacts)))
    
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
