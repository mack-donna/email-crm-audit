"""
Gmail OAuth2 Flow for Multi-User Support
Allows each user to authenticate their own Gmail account
"""

import os
import json
import pickle
from pathlib import Path
from flask import url_for, redirect, session
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# Allow insecure transport for local development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# OAuth2 scopes for Gmail
SCOPES = [
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.readonly'
]

class GmailOAuth:
    """Handle Gmail OAuth2 flow for multiple users"""
    
    def __init__(self, app=None):
        self.app = app
        self.client_config = None
        self.load_client_config()
        
    def load_client_config(self):
        """Load OAuth2 client configuration"""
        # Try to load from environment variable first (for production)
        client_config_json = os.environ.get('GOOGLE_OAUTH_CONFIG')
        
        if client_config_json:
            try:
                self.client_config = json.loads(client_config_json)
            except json.JSONDecodeError:
                print("⚠️ Invalid GOOGLE_OAUTH_CONFIG JSON")
                
        # Fallback to credentials.json file
        elif Path('credentials.json').exists():
            with open('credentials.json', 'r') as f:
                self.client_config = json.load(f)
        else:
            print("⚠️ No Gmail OAuth configuration found")
            self.client_config = None
            
    def get_user_token_path(self, user_id):
        """Get token storage path for a specific user"""
        tokens_dir = Path('user_tokens')
        tokens_dir.mkdir(exist_ok=True)
        return tokens_dir / f"token_{user_id}.json"
        
    def get_authorization_url(self, user_id, redirect_uri):
        """Generate OAuth2 authorization URL"""
        if not self.client_config:
            return None
            
        flow = Flow.from_client_config(
            self.client_config,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        
        # Store state in session for verification
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        return authorization_url, state
        
    def handle_callback(self, user_id, authorization_response, state, redirect_uri):
        """Handle OAuth2 callback and store credentials"""
        if not self.client_config:
            return False
            
        try:
            flow = Flow.from_client_config(
                self.client_config,
                scopes=SCOPES,
                redirect_uri=redirect_uri,
                state=state
            )
            
            # Exchange authorization code for tokens
            flow.fetch_token(authorization_response=authorization_response)
            
            # Store credentials for this user
            creds = flow.credentials
            token_path = self.get_user_token_path(user_id)
            
            # Save credentials to file
            token_data = {
                'token': creds.token,
                'refresh_token': creds.refresh_token,
                'token_uri': creds.token_uri,
                'client_id': creds.client_id,
                'client_secret': creds.client_secret,
                'scopes': creds.scopes
            }
            
            with open(token_path, 'w') as token_file:
                json.dump(token_data, token_file)
                
            return True
            
        except Exception as e:
            print(f"❌ OAuth callback error: {e}")
            print(f"❌ OAuth callback error type: {type(e)}")
            import traceback
            print(f"❌ OAuth callback traceback: {traceback.format_exc()}")
            return False
            
    def get_user_credentials(self, user_id):
        """Get stored credentials for a user"""
        token_path = self.get_user_token_path(user_id)
        
        if not token_path.exists():
            return None
            
        try:
            with open(token_path, 'r') as token_file:
                token_data = json.load(token_file)
                
            creds = Credentials(
                token=token_data['token'],
                refresh_token=token_data.get('refresh_token'),
                token_uri=token_data.get('token_uri'),
                client_id=token_data.get('client_id'),
                client_secret=token_data.get('client_secret'),
                scopes=token_data.get('scopes')
            )
            
            # Refresh token if expired
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Save refreshed token
                token_data['token'] = creds.token
                with open(token_path, 'w') as token_file:
                    json.dump(token_data, token_file)
                    
            return creds
            
        except Exception as e:
            print(f"❌ Error loading user credentials: {e}")
            return None
            
    def revoke_user_credentials(self, user_id):
        """Revoke and delete user's Gmail credentials"""
        token_path = self.get_user_token_path(user_id)
        
        if token_path.exists():
            try:
                # TODO: Call Google's revoke endpoint
                token_path.unlink()
                return True
            except Exception as e:
                print(f"❌ Error revoking credentials: {e}")
                return False
        return True
        
    def user_has_gmail_connected(self, user_id):
        """Check if user has connected Gmail"""
        creds = self.get_user_credentials(user_id)
        return creds is not None and creds.valid
        
    def _extract_subject_from_content(self, email_content):
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
    
    def _extract_body_from_content(self, email_content):
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
        
        # Return remaining content as body
        return '\n'.join(lines[start_idx:])
        
    def get_user_signature(self, user_id):
        """Get user's Gmail signature"""
        creds = self.get_user_credentials(user_id)
        
        if not creds or not creds.valid:
            return None
            
        try:
            service = build('gmail', 'v1', credentials=creds)
            
            # Get user's settings, including signature
            settings = service.users().settings().sendAs().list(userId='me').execute()
            
            # Look for the primary address signature
            send_as_list = settings.get('sendAs', [])
            for send_as in send_as_list:
                if send_as.get('isPrimary', False):
                    return send_as.get('signature', '')
            
            # If no primary found, try the first one
            if send_as_list:
                return send_as_list[0].get('signature', '')
                
            return None
            
        except Exception as e:
            print(f"❌ Error retrieving Gmail signature: {e}")
            return None
        
    def create_draft_from_content(self, user_id, to_email, email_content):
        """Create a Gmail draft from email content (with subject line embedded)"""
        if not email_content:
            return None, "No email content provided"
            
        # Extract subject and body from content
        subject = self._extract_subject_from_content(email_content)
        body = self._extract_body_from_content(email_content)
        
        # Get user's signature and append if available
        signature = self.get_user_signature(user_id)
        if signature:
            # Add signature with proper spacing
            if body.strip():
                body = body + "\n\n" + signature
            else:
                body = signature
        
        return self.create_draft_for_user(user_id, to_email, subject, body)
    
    def create_draft_for_user(self, user_id, to, subject, body):
        """Create a Gmail draft for a specific user"""
        creds = self.get_user_credentials(user_id)
        
        if not creds or not creds.valid:
            return None, "Gmail not connected. Please authenticate first."
            
        try:
            service = build('gmail', 'v1', credentials=creds)
            
            # Create message
            message = {
                'to': to,
                'subject': subject,
                'body': body
            }
            
            # Create draft
            draft = {
                'message': {
                    'raw': self._create_message_raw(message)
                }
            }
            
            result = service.users().drafts().create(
                userId='me',
                body=draft
            ).execute()
            
            return result.get('id'), None
            
        except Exception as e:
            return None, f"Failed to create draft: {str(e)}"
            
    def _create_message_raw(self, message):
        """Create base64 encoded email message"""
        import base64
        from email.mime.text import MIMEText
        
        msg = MIMEText(message['body'])
        msg['To'] = message['to']
        msg['Subject'] = message['subject']
        
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        return raw