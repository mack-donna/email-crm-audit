#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail Drafts Manager
Creates email drafts in Gmail for approved outreach emails
"""

import json
import logging
import os
import base64
import pickle
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(level=logging.INFO)

class GmailDraftsManager:
    """
    Manages creation of Gmail drafts for outreach campaigns.
    """
    
    def __init__(self, credentials_file='credentials.json', token_file='token.json'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.logger = logging.getLogger(__name__)
        
    def authenticate(self):
        """Authenticate with Gmail API"""
        try:
            # Try to import Google API libraries
            try:
                from google.auth.transport.requests import Request
                from google.oauth2.credentials import Credentials
                from google_auth_oauthlib.flow import InstalledAppFlow
                from googleapiclient.discovery import build
            except ImportError:
                self.logger.error("Google API libraries not installed. Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
                return False
            
            SCOPES = ['https://www.googleapis.com/auth/gmail.compose']
            creds = None
            
            # Load existing token if available
            if os.path.exists(self.token_file):
                try:
                    with open(self.token_file, 'rb') as token:
                        creds = pickle.load(token)
                except Exception as e:
                    self.logger.warning("Failed to load existing token, will create new one: {}".format(e))
                    # Remove corrupted token file
                    os.remove(self.token_file)
                    creds = None
            
            # If no valid credentials, get them
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        self.logger.error("Gmail credentials file not found: {}".format(self.credentials_file))
                        return False
                        
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
            
            self.service = build('gmail', 'v1', credentials=creds)
            self.logger.info("Gmail authentication successful")
            return True
            
        except Exception as e:
            self.logger.error("Gmail authentication failed: {}".format(str(e)))
            return False
    
    def create_draft(self, to_email, subject, body, from_name="Your Name"):
        """
        Create a Gmail draft for an outreach email.
        """
        if not self.service:
            if not self.authenticate():
                return None
        
        try:
            # Create the email message
            message = MIMEMultipart()
            message['to'] = to_email
            message['subject'] = subject
            
            # Add body
            message.attach(MIMEText(body, 'plain'))
            
            # Encode the message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Create draft
            draft = {
                'message': {
                    'raw': raw_message
                }
            }
            
            result = self.service.users().drafts().create(
                userId='me', 
                body=draft
            ).execute()
            
            draft_id = result.get('id')
            self.logger.info("Created Gmail draft for {}: {}".format(to_email, draft_id))
            
            return {
                'draft_id': draft_id,
                'to_email': to_email,
                'subject': subject,
                'created_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Error creating Gmail draft for {}: {}".format(to_email, str(e)))
            return None
    
    def create_drafts_from_campaign(self, campaign_file):
        """
        Create Gmail drafts from a campaign JSON file.
        """
        try:
            with open(campaign_file, 'r') as f:
                campaign_data = json.load(f)
            
            approved_emails = campaign_data.get('approved_emails', [])
            
            if not approved_emails:
                self.logger.warning("No approved emails found in campaign")
                return []
            
            drafts_created = []
            
            for email_data in approved_emails:
                # Handle the correct data structure
                contact_context = email_data.get('contact_context', {})
                contact = contact_context.get('contact', {})
                email_content = email_data.get('email_content', '')
                
                to_email = contact.get('email')
                subject = self._extract_subject(email_content)
                body = self._extract_body(email_content)
                
                if to_email and body:
                    draft = self.create_draft(to_email, subject, body)
                    if draft:
                        drafts_created.append(draft)
            
            self.logger.info("Created {} Gmail drafts from campaign".format(len(drafts_created)))
            return drafts_created
            
        except Exception as e:
            self.logger.error("Error processing campaign file: {}".format(str(e)))
            return []
    
    def _extract_subject(self, email_content):
        """Extract subject line from email content"""
        lines = email_content.strip().split('\n')
        
        # Look for Subject: line
        for line in lines:
            if line.lower().startswith('subject:'):
                return line.split(':', 1)[1].strip()
        
        # If no subject line found, create one from first line
        first_line = lines[0] if lines else "Outreach Email"
        if len(first_line) > 50:
            first_line = first_line[:47] + "..."
        
        return first_line
    
    def _extract_body(self, email_content):
        """Extract email body (everything after subject line)"""
        lines = email_content.strip().split('\n')
        
        # Skip subject line if present
        start_idx = 0
        for i, line in enumerate(lines):
            if line.lower().startswith('subject:'):
                start_idx = i + 1
                break
        
        # Skip empty lines after subject
        while start_idx < len(lines) and not lines[start_idx].strip():
            start_idx += 1
        
        body_lines = lines[start_idx:]
        return '\n'.join(body_lines)

def main():
    """Main function - can process campaign file or run test"""
    import sys
    
    if len(sys.argv) > 1:
        # Process campaign file
        campaign_file = sys.argv[1]
        if os.path.exists(campaign_file):
            drafts_manager = GmailDraftsManager()
            drafts = drafts_manager.create_drafts_from_campaign(campaign_file)
            if drafts:
                print("Created {} Gmail drafts from campaign!".format(len(drafts)))
                for draft in drafts:
                    print("  - {} (ID: {})".format(draft['to_email'], draft['draft_id']))
            else:
                print("No drafts created from campaign file")
        else:
            print("Campaign file not found: {}".format(campaign_file))
    else:
        # Run test
        test_email = {
            'to': 'test@example.com',
            'subject': 'Test Outreach Email',
            'body': '''Hi John,

I noticed your work at TechCorp and thought you might be interested in discussing how companies like yours are leveraging AI to accelerate development.

As CTO, you're likely evaluating technologies that could give TechCorp a competitive edge. I've helped similar companies reduce time-to-market by 30-40%.

Would you be open to a brief conversation? I'd be happy to share specific examples.

Best regards,
[Your name]'''
        }
        
        drafts_manager = GmailDraftsManager()
        
        if drafts_manager.authenticate():
            print("Gmail authentication successful!")
            
            # Create a test draft
            draft = drafts_manager.create_draft(
                test_email['to'], 
                test_email['subject'], 
                test_email['body']
            )
            
            if draft:
                print("Test draft created successfully!")
                print("Draft ID: {}".format(draft['draft_id']))
            else:
                print("Failed to create test draft")
        else:
            print("Gmail authentication failed")

if __name__ == "__main__":
    main()