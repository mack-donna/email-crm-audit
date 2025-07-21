#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module 2: Email History Analyzer
Connects to Gmail API to search and analyze interaction history with contacts.
"""

import os
import json
import pickle
import logging
from datetime import datetime, timedelta
import base64
import re
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

class EmailHistoryAnalyzer:
    """
    Gmail API integration for contact interaction history analysis.
    
    Searches both inbox and sent emails to extract:
    - Interaction dates and frequency
    - Email content context
    - Relationship warmth scoring
    """
    
    # If modifying these scopes, delete the token.pickle file
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    def __init__(self, credentials_file='credentials.json', token_file='token.pickle', log_level="INFO"):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.setup_logging(log_level)
        self.search_stats = {
            'total_searches': 0,
            'successful_searches': 0,
            'failed_searches': 0,
            'emails_analyzed': 0,
            'api_errors': 0
        }
        
    def setup_logging(self, level):
        """Configure comprehensive logging for debugging."""
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format='%(asctime)s - EmailHistoryAnalyzer - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('email_history_{}.log'.format(datetime.now().strftime("%Y%m%d_%H%M%S"))),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def authenticate(self):
        """
        Authenticate with Gmail API using OAuth2.
        
        First time: Opens browser for authorization
        Subsequent: Uses saved token
        """
        creds = None
        
        # Token file stores the user's access and refresh tokens
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
                self.logger.info("Loaded existing authentication token")
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                self.logger.info("Refreshing expired token")
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    self.logger.error("credentials.json not found! Please follow setup instructions.")
                    raise FileNotFoundError(
                        "\n\n=== GMAIL API SETUP REQUIRED ===\n"
                        "1. Go to https://console.cloud.google.com/\n"
                        "2. Create a new project or select existing\n"
                        "3. Enable Gmail API\n"
                        "4. Create credentials (OAuth 2.0 Client ID)\n"
                        "5. Download credentials and save as 'credentials.json' in this directory\n"
                        "6. Run this script again\n"
                        "================================\n"
                    )
                    
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
                self.logger.info("Completed new authentication flow")
                
            # Save the credentials for the next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
                self.logger.info("Saved authentication token for future use")
        
        self.service = build('gmail', 'v1', credentials=creds)
        self.logger.info("Gmail API service initialized successfully")
        return True
        
    def test_connection(self):
        """
        Test Gmail API connection by fetching user profile.
        
        Returns:
            dict: User profile info if successful
        """
        try:
            # Call the Gmail API
            results = self.service.users().getProfile(userId='me').execute()
            self.logger.info("Connection test successful. Email: {}".format(results.get('emailAddress')))
            return results
        except Exception as e:
            self.logger.error("Connection test failed: {}".format(str(e)))
            raise
            
    def search_contact_emails(self, email_address, days_back=365, max_results=50):
        """
        Search for all emails to/from a specific contact.
        
        Args:
            email_address: Contact's email address
            days_back: How many days to search back (default: 365)
            max_results: Maximum number of emails to retrieve
            
        Returns:
            dict: Structured interaction history
        """
        self.logger.info("Searching emails for contact: {}".format(email_address))
        self.search_stats['total_searches'] += 1
        
        try:
            # Build search query
            query = 'from:{} OR to:{}'.format(email_address, email_address)
            
            # Add date filter if specified
            if days_back:
                after_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
                query += ' after:{}'.format(after_date)
                
            self.logger.debug("Search query: {}".format(query))
            
            # Execute search
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            self.logger.info("Found {} emails for {}".format(len(messages), email_address))
            
            # Extract detailed information from each email
            interaction_history = {
                'email_address': email_address,
                'total_interactions': len(messages),
                'emails_sent': [],
                'emails_received': [],
                'first_interaction': None,
                'last_interaction': None,
                'interaction_dates': [],
                'subject_lines': [],
                'relationship_warmth': 'cold',
                'key_topics': [],
                'interaction_summary': ''
            }
            
            # Analyze each email
            for msg in messages:
                email_data = self._analyze_email(msg['id'], email_address)
                if email_data:
                    # Categorize as sent or received
                    if email_data['direction'] == 'sent':
                        interaction_history['emails_sent'].append(email_data)
                    else:
                        interaction_history['emails_received'].append(email_data)
                        
                    interaction_history['interaction_dates'].append(email_data['date'])
                    interaction_history['subject_lines'].append(email_data['subject'])
                    
            # Calculate relationship metrics
            if interaction_history['interaction_dates']:
                interaction_history['interaction_dates'].sort()
                interaction_history['first_interaction'] = interaction_history['interaction_dates'][0]
                interaction_history['last_interaction'] = interaction_history['interaction_dates'][-1]
                interaction_history['relationship_warmth'] = self._calculate_relationship_warmth(interaction_history)
                
            self.search_stats['successful_searches'] += 1
            self.search_stats['emails_analyzed'] += len(messages)
            
            return interaction_history
            
        except Exception as e:
            self.logger.error("Error searching emails for {}: {}".format(email_address, str(e)))
            self.search_stats['failed_searches'] += 1
            self.search_stats['api_errors'] += 1
            return None
            
    def _analyze_email(self, msg_id, contact_email):
        """
        Analyze individual email for interaction data.
        
        Args:
            msg_id: Gmail message ID
            contact_email: Contact's email address
            
        Returns:
            dict: Email analysis results
        """
        try:
            # Get email details
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='metadata',
                metadataHeaders=['From', 'To', 'Subject', 'Date']
            ).execute()
            
            headers = message['payload'].get('headers', [])
            email_data = {
                'id': msg_id,
                'date': None,
                'subject': '',
                'from': '',
                'to': '',
                'direction': 'received',  # or 'sent'
                'snippet': message.get('snippet', '')
            }
            
            # Extract header information
            for header in headers:
                name = header['name']
                value = header['value']
                
                if name == 'Date':
                    # Parse date
                    try:
                        # Simple date extraction (Gmail provides RFC 2822 format)
                        email_data['date'] = value
                    except:
                        email_data['date'] = value
                        
                elif name == 'Subject':
                    email_data['subject'] = value
                    
                elif name == 'From':
                    email_data['from'] = value
                    # Check if this is a sent email
                    if contact_email.lower() not in value.lower():
                        email_data['direction'] = 'sent'
                        
                elif name == 'To':
                    email_data['to'] = value
                    
            return email_data
            
        except Exception as e:
            self.logger.error("Error analyzing email {}: {}".format(msg_id, str(e)))
            return None
            
    def _calculate_relationship_warmth(self, interaction_history):
        """
        Calculate relationship warmth based on interaction patterns.
        
        Args:
            interaction_history: Dict with interaction data
            
        Returns:
            str: 'cold', 'warm', or 'existing'
        """
        total_interactions = interaction_history['total_interactions']
        
        if total_interactions == 0:
            return 'cold'
        elif total_interactions < 3:
            return 'warm'
        else:
            # Check recency of last interaction
            if interaction_history['last_interaction']:
                # For now, simple date string comparison
                # In production, would parse dates properly
                return 'existing'
            return 'warm'
            
    def batch_search_contacts(self, email_list, days_back=365, max_results_per_contact=20):
        """
        Search email history for multiple contacts.
        
        Args:
            email_list: List of email addresses
            days_back: How many days to search back
            max_results_per_contact: Max emails per contact
            
        Returns:
            dict: Results indexed by email address
        """
        self.logger.info("Starting batch search for {} contacts".format(len(email_list)))
        results = {}
        
        for email in email_list:
            self.logger.info("Processing {}/{}".format(
                email_list.index(email) + 1, len(email_list)
            ))
            
            history = self.search_contact_emails(email, days_back, max_results_per_contact)
            if history:
                results[email] = history
                
        self.logger.info("Batch search complete. Processed {} contacts".format(len(results)))
        return results
        
    def generate_search_report(self):
        """Generate summary report of search operations."""
        report = """
=== EMAIL HISTORY SEARCH REPORT ===

SEARCH STATISTICS:
- Total searches performed: {}
- Successful searches: {}
- Failed searches: {}
- Total emails analyzed: {}
- API errors encountered: {}

SUCCESS RATE: {:.1f}%
""".format(
            self.search_stats['total_searches'],
            self.search_stats['successful_searches'],
            self.search_stats['failed_searches'],
            self.search_stats['emails_analyzed'],
            self.search_stats['api_errors'],
            (self.search_stats['successful_searches'] / max(self.search_stats['total_searches'], 1)) * 100
        )
        return report


def main():
    """Test the email history analyzer independently."""
    print("\n=== Gmail Email History Analyzer Test ===\n")
    
    # Initialize analyzer
    analyzer = EmailHistoryAnalyzer()
    
    # Step 1: Authenticate
    print("Step 1: Authenticating with Gmail API...")
    try:
        analyzer.authenticate()
        print("✅ Authentication successful!")
    except Exception as e:
        print("❌ Authentication failed: {}".format(str(e)))
        return
        
    # Step 2: Test connection
    print("\nStep 2: Testing Gmail API connection...")
    try:
        profile = analyzer.test_connection()
        print("✅ Connected to Gmail account: {}".format(profile.get('emailAddress')))
        print("   Total messages: {}".format(profile.get('messagesTotal')))
        print("   Total threads: {}".format(profile.get('threadsTotal')))
    except Exception as e:
        print("❌ Connection test failed: {}".format(str(e)))
        return
        
    # Step 3: Test search for a single contact
    print("\nStep 3: Testing email search...")
    print("Enter an email address to search for (or press Enter to skip): ")
    test_email = input().strip()
    
    if test_email:
        print("\nSearching for emails with {}...".format(test_email))
        history = analyzer.search_contact_emails(test_email, days_back=365, max_results=10)
        
        if history:
            print("\n✅ Search Results:")
            print("   Total interactions: {}".format(history['total_interactions']))
            print("   Emails sent: {}".format(len(history['emails_sent'])))
            print("   Emails received: {}".format(len(history['emails_received'])))
            print("   Relationship warmth: {}".format(history['relationship_warmth']))
            
            if history['subject_lines']:
                print("\n   Recent subjects:")
                for subject in history['subject_lines'][:5]:
                    print("   - {}".format(subject[:60]))
        else:
            print("❌ No results found or search failed")
            
    # Step 4: Generate report
    print("\n" + analyzer.generate_search_report())
    
    print("\n✅ Module 2 Test Complete!")
    print("🔑 Authentication token saved as: token.pickle")
    print("📊 Next: Integration with contact processor")


if __name__ == "__main__":
    main()