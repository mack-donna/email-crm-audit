#!/usr/bin/env python3
"""
Refined Gmail Contact Extractor
Focuses on actual prospects and clients, filters out internal/non-profit/personal contacts
"""

import os
import csv
import re
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

class RefinedEmailContactExtractor:
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
        """Get emails from the last X days with refined filtering"""
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
                    
                    # Only look at external contacts (from emails, not to emails)
                    for email_string in [from_email]:  # Focus on who's emailing YOU
                        email = self.extract_email_address(email_string)
                        name = self.extract_name_from_email(email_string)
                        
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
            print(f"✓ Found {len(self.email_contacts)} potential prospect/client contacts")
            
        except Exception as e:
            print(f"❌ Error fetching emails: {e}")
    
    def categorize_contact(self, contact):
        """Enhanced categorization focused on business value"""
        subjects = ' '.join(contact['subjects']).lower()
        domain = contact['domain'].lower()
        
        # High-value indicators
        if any(word in subjects for word in ['proposal', 'quote', 'pricing', 'contract', 'agreement', 'sow']):
            return 'Active Prospect'
        elif any(word in subjects for word in ['project', 'campaign', 'presentation', 'deck', 'strategy']):
            return 'Project Opportunity'
        elif any(word in subjects for word in ['meeting', 'call', 'discussion', 'consultation']):
            return 'Engaged Prospect'
        elif any(word in subjects for word in ['introduction', 'connect', 'partnership', 'collaboration']):
            return 'Network/Partnership'
        elif any(word in subjects for word in ['invoice', 'payment', 'billing']):
            return 'Current Client'
        else:
            return 'General Business Contact'
    
    def score_contact(self, contact):
        """Enhanced scoring focused on sales potential"""
        score = 0
        
        # Email frequency (higher weight for recent activity)
        score += min(contact['email_count'] * 10, 60)  # Increased weight
        
        # Category-based scoring (heavily weighted toward prospects)
        category_scores = {
            'Active Prospect': 50,
            'Current Client': 45,
            'Project Opportunity': 40,
            'Engaged Prospect': 35,
            'Network/Partnership': 25,
            'General Business Contact': 15
        }
        score += category_scores.get(contact['category'], 0)
        
        # Business domain bonus (corporate emails)
        if not any(personal in contact['domain'] for personal in ['gmail', 'yahoo', 'hotmail', 'aol']):
            score += 25
        
        # High-value keywords in subjects
        subjects_text = ' '.join(contact['subjects']).lower()
        high_value_keywords = [
            'proposal', 'quote', 'pricing', 'budget', 'contract', 'agreement',
            'project', 'campaign', 'strategy', 'consultation', 'partnership'
        ]
        keyword_count = sum(1 for keyword in high_value_keywords if keyword in subjects_text)
        score += keyword_count * 5
        
        return score
    
    def generate_contact_export(self):
        """Generate refined CSV export focused on sales prospects"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"prospects_clients_export_{timestamp}.csv"
        
        for contact in self.email_contacts:
            contact['priority_score'] = self.score_contact(contact)
        
        # Only include contacts with meaningful scores
        filtered_contacts = [c for c in self.email_contacts if c['priority_score'] > 25]
        filtered_contacts.sort(key=lambda x: x['priority_score'], reverse=True)
        
        print(f"📄 Generating refined contact export: {filename}")
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'Priority', 'Name', 'Email', 'Company', 'Category', 
                'Email_Count', 'Last_Contact', 'Priority_Score', 
                'Sample_Subjects', 'Sales_Notes'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for contact in filtered_contacts:
                priority = "High" if contact['priority_score'] > 70 else "Medium" if contact['priority_score'] > 50 else "Low"
                
                # Generate sales-focused notes
                notes = f"Contacted {contact['email_count']}x"
                if contact['category'] in ['Active Prospect', 'Current Client', 'Project Opportunity']:
                    notes += f" | HIGH VALUE: {contact['category']}"
                
                writer.writerow({
                    'Priority': priority,
                    'Name': contact['name'],
                    'Email': contact['email'],
                    'Company': contact['company'],
                    'Category': contact['category'],
                    'Email_Count': contact['email_count'],
                    'Last_Contact': contact['last_seen'],
                    'Priority_Score': contact['priority_score'],
                    'Sample_Subjects': '; '.join(contact['subjects'][:3]),
                    'Sales_Notes': notes
                })
        
        self.print_summary(filtered_contacts)
        print(f"✓ Refined contact export saved as: {filename}")
        print(f"\n📋 NEXT STEPS:")
        print(f"1. Open {filename} - focus on 'Active Prospect' and 'Current Client' categories")
        print(f"2. Review contacts scoring 70+ first")
        print(f"3. Add high-priority prospects to Salesforce with context from 'Sample_Subjects'")
        
        return filename, filtered_contacts
    
    def print_summary(self, filtered_contacts):
        """Print refined summary focused on sales value"""
        high_priority = sum(1 for c in filtered_contacts if c.get('priority_score', 0) > 70)
        medium_priority = sum(1 for c in filtered_contacts if 50 < c.get('priority_score', 0) <= 70)
        low_priority = sum(1 for c in filtered_contacts if c.get('priority_score', 0) <= 50)
        
        print("\n" + "="*60)
        print("📊 REFINED PROSPECT/CLIENT EXTRACTION SUMMARY")
        print("="*60)
        print(f"🎯 Qualified business contacts found: {len(filtered_contacts)}")
        print(f"🔴 High priority prospects/clients: {high_priority}")
        print(f"🟡 Medium priority prospects: {medium_priority}")
        print(f"⚪ Lower priority contacts: {low_priority}")
        
        # Category breakdown
        categories = {}
        for contact in filtered_contacts:
            cat = contact.get('category', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"\n📋 BUSINESS CATEGORY BREAKDOWN:")
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"   {category}: {count}")
        
        if high_priority > 0:
            print(f"\n🔴 TOP PROSPECTS/CLIENTS TO ADD:")
            high_contacts = [c for c in filtered_contacts if c.get('priority_score', 0) > 70][:8]
            for contact in high_contacts:
                print(f"   • {contact['name']} ({contact['email']}) - {contact['category']} - Score: {contact['priority_score']}")
        
        print("\n" + "="*60)
    
    def run_extraction(self):
        """Run the refined contact extraction process"""
        print("🚀 Starting REFINED Gmail Contact Extraction")
        print("(Focused on prospects and clients only)")
        print("-" * 60)
        
        self.setup_gmail()
        self.get_recent_emails(days_back=60)
        filename, contacts = self.generate_contact_export()
        
        print(f"\n✅ Refined extraction completed!")
        print(f"\n💡 This list should contain mostly genuine prospects and clients")

if __name__ == "__main__":
    extractor = RefinedEmailContactExtractor()
    extractor.run_extraction()
