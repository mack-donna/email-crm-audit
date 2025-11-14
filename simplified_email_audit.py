#!/usr/bin/env python3
"""
Gmail Contact Extractor - Clean Version
Extracts business contacts from Gmail for manual Salesforce comparison
"""

import os
import csv
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Import shared email retrieval utility
from gmail_email_retriever import GmailEmailRetriever

class EmailContactExtractor:
    def __init__(self):
        self.gmail_service = None
        self.email_contacts = []
        self.email_retriever = None  # Will be initialized after Gmail setup

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
        # Initialize shared email retriever utility
        self.email_retriever = GmailEmailRetriever(
            gmail_service=self.gmail_service,
            user_email='stu@sentient-sf.com'
        )
        print("✓ Gmail API connected successfully")
    
    def get_recent_emails(self, days_back=60):
        """
        Get emails from the last X days using shared GmailEmailRetriever utility.

        This method now delegates to the shared utility and adds custom
        categorization logic specific to this extractor.
        """
        # Additional exclude domains specific to simplified audit
        additional_exclude_domains = [
            'google.com', 'apple.com', 'microsoft.com', 'adobe.com', 'zoom.us'
        ]

        # Use shared email retriever utility
        email_contacts = self.email_retriever.get_recent_emails(
            days_back=days_back,
            max_results=1000,
            progress_interval=100,
            exclude_domains=additional_exclude_domains
        )

        # Add custom categorization for each contact
        for email, contact in email_contacts.items():
            contact['category'] = self.categorize_contact(contact)

        # Convert to list and store
        self.email_contacts = list(email_contacts.values())
        print("✓ Found {} unique business contacts".format(len(self.email_contacts)))
    
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