#!/usr/bin/env python3
"""
Enhanced Gmail Contact Extractor
Includes both received AND sent emails to capture outreach prospects
"""

import os
import csv
import re
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

class EnhancedEmailContactExtractor:
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
        
        email_match = re.search(r'<([^>]+)>', email_string)
        if email_match:
            return email_match.group(1).lower()
        
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
    
    def is_prospect_client_email(self, email, subject=""):
        """Enhanced filter to identify actual prospects and clients"""
        if not email:
            return False
        
        email_lower = email.lower()
        subject_lower = subject.lower()
        
        # Filter out your own company
        if 'sentient-sf.com' in email_lower:
            return False
        
        # Filter out obvious non-business emails
        exclude_patterns = [
            'noreply', 'no-reply', 'automated', 'notification', 'support',
            'newsletter', 'unsubscribe', 'marketing', 'promo', 'donotreply',
            'info@', 'admin@', 'contact@', 'hello@'
        ]
        
        for pattern in exclude_patterns:
            if pattern in email_lower or pattern in subject_lower:
                return False
        
        # Filter out service providers and tools
        exclude_domains = [
            'anthropic.com', 'gusto.com', 'stripe.com', 'quickbooks',
            'mercury.com', 'ziptie.dev', 'google.com', 'apple.com',
            'microsoft.com', 'adobe.com', 'zoom.us', 'calendly.com',
            'typeform.com', 'mailchimp.com', 'constant-contact.com'
        ]
        
        for domain in exclude_domains:
            if domain in email_lower:
                return False
        
        # Filter out non-profits, associations, and educational institutions
        nonprofit_indicators = [
            '.org', '.edu', '.gov', 'school', 'university', 'college',
            'foundation', 'association', 'society', 'institute', 'council',
            'chamber', 'alliance', 'nonprofit', 'charity'
        ]
        
        for indicator in nonprofit_indicators:
            if indicator in email_lower:
                return False
        
        # Filter out personal email domains
        personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'aol.com', 'icloud.com']
        domain = email.split('@')[1]
        if domain in personal_domains:
            return False
        
        # Look for business-oriented subject lines
        business_subjects = [
            'proposal', 'quote', 'pricing', 'project', 'contract', 'agreement',
            'consultation', 'meeting', 'call', 'business', 'services', 'partnership',
            'collaboration', 'opportunity', 'discussion', 'presentation', 'deck',
            'strategy', 'marketing', 'brand', 'campaign', 'creative', 'design'
        ]
        
        # Only include if there's business context in subjects OR it's a business domain
        has_business_context = any(term in subject_lower for term in business_subjects)
        is_business_domain = not any(personal in domain for personal in ['gmail', 'yahoo', 'hotmail', 'aol'])
        
        return has_business_context or is_business_domain
    
    def get_recent_emails(self, days_back=60):
        """Get emails from the last X days with refined filtering - INCLUDING SENT EMAILS"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Search both inbox AND sent emails
            query = f'after:{start_date.strftime("%Y/%m/%d")}'
            
            print(f"🔍 Searching emails from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            print("📧 Including both received AND sent emails...")
            
            results = self.gmail_service.users().messages().list(
                userId='me', q=query, maxResults=2000  # Increased limit for sent+received
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
                    to_emails = ""
                    cc_emails = ""
                    date_header = ""
                    
                    for header in headers:
                        name = header['name'].lower()
                        value = header['value']
                        
                        if name == 'subject':
                            subject = value
                        elif name == 'from':
                            from_email = value
                        elif name == 'to':
                            to_emails = value
                        elif name == 'cc':
                            cc_emails = value
                        elif name == 'date':
                            date_header = value
                    
                    # Check if this is a sent email (from your domain)
                    is_sent_email = 'sentient-sf.com' in from_email
                    
                    # Process contacts differently based on email direction
                    contact_emails = []
                    email_type = ""
                    
                    if is_sent_email:
                        # For sent emails, look at TO and CC recipients
                        email_type = "Outreach"
                        all_recipients = []
                        if to_emails:
                            all_recipients.extend(to_emails.split(','))
                        if cc_emails:
                            all_recipients.extend(cc_emails.split(','))
                        contact_emails = all_recipients
                    else:
                        # For received emails, look at FROM sender
                        email_type = "Inbound"
                        contact_emails = [from_email]
                    
                    # Process each contact email
                    for email_string in contact_emails:
                        email = self.extract_email_address(email_string.strip())
                        name = self.extract_name_from_email(email_string.strip())
                        
                        if email and self.is_prospect_client_email(email, subject):
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
                                    'inbound_count': 0,
                                    'outreach_count': 0,
                                    'subjects': [],
                                    'email_types': set(),
                                    'category': 'Unknown'
                                }
                            
                            contact = email_contacts[email]
                            contact['email_count'] += 1
                            contact['last_seen'] = date_header or datetime.now().strftime('%Y-%m-%d')
                            contact['email_types'].add(email_type)
                            
                            if email_type == "Outreach":
                                contact['outreach_count'] += 1
                            else:
                                contact['inbound_count'] += 1
                            
                            if subject and subject not in contact['subjects']:
                                contact['subjects'].append(subject[:100])
                            
                            if name and len(name) > len(contact['name']):
                                contact['name'] = name
                            
                            contact['category'] = self.categorize_contact(contact)
                
                except Exception as e:
                    print(f"   Error processing email {i+1}: {e}")
                    continue
            
            # Convert email_types set to list for JSON serialization
            for contact in email_contacts.values():
                contact['email_types'] = list(contact['email_types'])
            
            self.email_contacts = list(email_contacts.values())
            print(f"✓ Found {len(self.email_contacts)} potential prospect/client contacts")
            
            # Print breakdown of contact types
            inbound_only = sum(1 for c in self.email_contacts if c['inbound_count'] > 0 and c['outreach_count'] == 0)
            outreach_only = sum(1 for c in self.email_contacts if c['outreach_count'] > 0 and c['inbound_count'] == 0)
            both_directions = sum(1 for c in self.email_contacts if c['outreach_count'] > 0 and c['inbound_count'] > 0)
            
            print(f"   📩 Inbound only: {inbound_only}")
            print(f"   📤 Outreach only (no response): {outreach_only}")
            print(f"   🔄 Both directions: {both_directions}")
            
        except Exception as e:
            print(f"❌ Error fetching emails: {e}")
    
    def categorize_contact(self, contact):
        """Enhanced categorization including outreach status"""
        subjects = ' '.join(contact['subjects']).lower()
        domain = contact['domain'].lower()
        
        # Check if they've responded to outreach
        has_outreach = contact['outreach_count'] > 0
        has_inbound = contact['inbound_count'] > 0
        
        # High-value indicators
        if any(word in subjects for word in ['proposal', 'quote', 'pricing', 'contract', 'agreement', 'sow']):
            return 'Active Prospect'
        elif any(word in subjects for word in ['project', 'campaign', 'presentation', 'deck', 'strategy']):
            return 'Project Opportunity'
        elif any(word in subjects for word in ['meeting', 'call', 'discussion', 'consultation']):
            return 'Engaged Prospect'
        elif any(word in subjects for word in ['invoice', 'payment', 'billing']):
            return 'Current Client'
        elif has_outreach and not has_inbound:
            return 'Cold Outreach (No Response)'
        elif has_outreach and has_inbound:
            return 'Responded to Outreach'
        elif any(word in subjects for word in ['introduction', 'connect', 'partnership', 'collaboration']):
            return 'Network/Partnership'
        else:
            return 'General Business Contact'
    
    def score_contact(self, contact):
        """Enhanced scoring including outreach analysis"""
        score = 0
        
        # Base email frequency
        score += min(contact['email_count'] * 8, 50)
        
        # Category-based scoring (heavily weighted toward prospects)
        category_scores = {
            'Active Prospect': 60,
            'Current Client': 55,
            'Project Opportunity': 50,
            'Engaged Prospect': 45,
            'Responded to Outreach': 40,  # Good sign they're engaged
            'Network/Partnership': 30,
            'General Business Contact': 20,
            'Cold Outreach (No Response)': 15  # Lower but still valuable for follow-up
        }
        score += category_scores.get(contact['category'], 0)
        
        # Response rate bonus (if they replied to outreach)
        if contact['outreach_count'] > 0 and contact['inbound_count'] > 0:
            response_rate = contact['inbound_count'] / contact['outreach_count']
            score += min(response_rate * 25, 25)
        
        # Business domain bonus
        if not any(personal in contact['domain'] for personal in ['gmail', 'yahoo', 'hotmail', 'aol']):
            score += 20
        
        # High-value keywords
        subjects_text = ' '.join(contact['subjects']).lower()
        high_value_keywords = [
            'proposal', 'quote', 'pricing', 'budget', 'contract', 'agreement',
            'project', 'campaign', 'strategy', 'consultation', 'partnership'
        ]
        keyword_count = sum(1 for keyword in high_value_keywords if keyword in subjects_text)
        score += keyword_count * 5
        
        return score
    
    def generate_contact_export(self):
        """Generate enhanced CSV export with outreach analysis"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enhanced_prospects_export_{timestamp}.csv"
        
        for contact in self.email_contacts:
            contact['priority_score'] = self.score_contact(contact)
        
        # Filter and sort
        filtered_contacts = [c for c in self.email_contacts if c['priority_score'] > 20]
        filtered_contacts.sort(key=lambda x: x['priority_score'], reverse=True)
        
        print(f"📄 Generating enhanced contact export: {filename}")
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'Priority', 'Name', 'Email', 'Company', 'Category', 
                'Total_Emails', 'Outreach_Sent', 'Inbound_Received', 'Response_Rate',
                'Last_Contact', 'Priority_Score', 'Sample_Subjects', 'Sales_Notes'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for contact in filtered_contacts:
                priority = "High" if contact['priority_score'] > 70 else "Medium" if contact['priority_score'] > 45 else "Low"
                
                # Calculate response rate
                response_rate = ""
                if contact['outreach_count'] > 0:
                    rate = (contact['inbound_count'] / contact['outreach_count']) * 100
                    response_rate = f"{rate:.0f}%"
                
                # Generate enhanced sales notes
                notes = []
                if contact['outreach_count'] > 0 and contact['inbound_count'] == 0:
                    notes.append("🔄 FOLLOW UP NEEDED - No response to outreach")
                elif contact['outreach_count'] > 0 and contact['inbound_count'] > 0:
                    notes.append("✅ ENGAGED - Responded to outreach")
                elif contact['inbound_count'] > 0 and contact['outreach_count'] == 0:
                    notes.append("📥 INBOUND LEAD")
                
                if contact['category'] in ['Active Prospect', 'Current Client', 'Project Opportunity']:
                    notes.append(f"HIGH VALUE: {contact['category']}")
                
                writer.writerow({
                    'Priority': priority,
                    'Name': contact['name'],
                    'Email': contact['email'],
                    'Company': contact['company'],
                    'Category': contact['category'],
                    'Total_Emails': contact['email_count'],
                    'Outreach_Sent': contact['outreach_count'],
                    'Inbound_Received': contact['inbound_count'],
                    'Response_Rate': response_rate,
                    'Last_Contact': contact['last_seen'],
                    'Priority_Score': contact['priority_score'],
                    'Sample_Subjects': '; '.join(contact['subjects'][:3]),
                    'Sales_Notes': ' | '.join(notes)
                })
        
        self.print_enhanced_summary(filtered_contacts)
        print(f"✓ Enhanced contact export saved as: {filename}")
        return filename, filtered_contacts
    
    def print_enhanced_summary(self, filtered_contacts):
        """Print enhanced summary with outreach analysis"""
        print("\n" + "="*70)
        print("📊 ENHANCED PROSPECT/CLIENT EXTRACTION SUMMARY")
        print("="*70)
        
        # Basic counts
        total = len(filtered_contacts)
        high_priority = sum(1 for c in filtered_contacts if c.get('priority_score', 0) > 70)
        
        # Outreach analysis
        no_response = sum(1 for c in filtered_contacts if c['outreach_count'] > 0 and c['inbound_count'] == 0)
        responded = sum(1 for c in filtered_contacts if c['outreach_count'] > 0 and c['inbound_count'] > 0)
        inbound_only = sum(1 for c in filtered_contacts if c['outreach_count'] == 0 and c['inbound_count'] > 0)
        
        print(f"🎯 Total qualified contacts: {total}")
        print(f"🔴 High priority prospects: {high_priority}")
        print(f"\n📤 OUTREACH ANALYSIS:")
        print(f"   🔄 Need follow-up (no response): {no_response}")
        print(f"   ✅ Responded to outreach: {responded}")
        print(f"   📥 Inbound leads only: {inbound_only}")
        
        if no_response > 0:
            print(f"\n🔄 TOP PROSPECTS NEEDING FOLLOW-UP:")
            follow_ups = [c for c in filtered_contacts 
                         if c['outreach_count'] > 0 and c['inbound_count'] == 0][:5]
            for contact in follow_ups:
                print(f"   • {contact['name']} ({contact['email']}) - {contact['outreach_count']} emails sent")
        
        print("\n" + "="*70)
    
    def run_extraction(self):
        """Run the enhanced contact extraction process"""
        print("🚀 Starting ENHANCED Gmail Contact Extraction")
        print("(Including both received AND sent emails)")
        print("-" * 70)
        
        self.setup_gmail()
        self.get_recent_emails(days_back=60)
        filename, contacts = self.generate_contact_export()
        
        print(f"\n✅ Enhanced extraction completed!")
        print(f"\n💡 This now includes your outreach efforts and response tracking")

if __name__ == "__main__":
    extractor = EnhancedEmailContactExtractor()
    extractor.run_extraction()