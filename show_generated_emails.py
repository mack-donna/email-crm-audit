#!/usr/bin/env python3
"""
Show Generated Emails
Extract and display the AI-generated emails from the test run
"""

import json
import os

def show_emails_from_latest_campaign():
    """Show emails from the most recent campaign test"""
    
    # The emails are generated but not saved to files because the review process is interrupted
    # Let me create a simple test to show what the AI generated
    
    print("=== AI-GENERATED EMAILS FROM LATEST TEST ===\n")
    
    # These are the emails that were generated in our test (shown in terminal output)
    emails = [
        {
            'contact': 'Sarah Chen - InnovateTech Solutions - CTO',
            'subject': 'Your perspective on enterprise innovation challenges',
            'body': '''Hi Sarah,

I came across your work at InnovateTech Solutions and noticed your leadership in driving technological transformation. As someone who follows developments in the enterprise tech space, I'm particularly interested in how CTOs like yourself are navigating the current wave of AI and automation integration.

I'm reaching out because our organization has developed some interesting insights around the challenges technology leaders face when balancing innovation with operational stability. Given your role at InnovateTech, I imagine you might have some unique perspectives on this, especially considering the rapid pace of change in the industry.

I'd welcome the opportunity to have a brief conversation to learn more about your priorities at InnovateTech and share some relevant findings from our recent work with similar organizations. Would you be open to a 15-minute call next week? I'm happy to work around your schedule.

Best regards,
[Your name]

Note: I kept this email deliberately broad but genuine since we don't have specific research findings to reference. With actual company information, recent news, or industry context, we could make this much more targeted and relevant to Sarah's specific situation.'''
        },
        {
            'contact': 'Michael Rodriguez - Global Manufacturing Inc - VP Operations',
            'subject': 'Manufacturing operations efficiency insights',
            'body': '''Hi Michael,

I noticed your role as VP Operations at Global Manufacturing Inc and your work in optimizing manufacturing processes. Given the current focus on operational efficiency and automation in manufacturing, I thought you might be interested in some insights we've developed around operational transformation.

We've been working with manufacturing leaders who are facing similar challenges around balancing efficiency improvements with quality standards. Many are exploring how new technologies can streamline operations without disrupting proven processes.

I'd be interested to learn more about Global Manufacturing's current operational priorities and share some relevant case studies from companies in similar situations. Would you be open to a brief conversation? I could share some specific examples of efficiency improvements we've seen in the manufacturing sector.

Best regards,
[Your name]'''
        },
        {
            'contact': 'Jennifer Walsh - HealthCare Innovations - Director of Strategy',
            'subject': 'Healthcare innovation strategy discussion',
            'body': '''Hi Jennifer,

I came across your work at HealthCare Innovations and was impressed by your strategic approach to healthcare technology advancement. As someone focused on strategy in the healthcare space, you're likely seeing interesting developments in how technology is transforming patient care and operational efficiency.

I'm reaching out because we've been working with healthcare organizations on strategic initiatives around technology adoption and innovation management. Given your role as Director of Strategy, I imagine you have valuable insights into the challenges and opportunities in healthcare innovation.

I'd welcome the opportunity to discuss HealthCare Innovations' strategic priorities and share some relevant findings from our work with similar healthcare organizations. Would you be open to a brief conversation next week? I'm happy to accommodate your schedule.

Best regards,
[Your name]'''
        }
    ]
    
    for i, email in enumerate(emails, 1):
        print("=" * 60)
        print("EMAIL {} of 3".format(i))
        print("=" * 60)
        print("CONTACT: {}".format(email['contact']))
        print("SUBJECT: {}".format(email['subject']))
        print("\nBODY:\n{}".format(email['body']))
        print("\n" + "=" * 60 + "\n")

def create_gmail_draft_instructions():
    """Show instructions for getting emails into Gmail"""
    
    print("""
NEXT STEPS: Getting Emails into Gmail Drafts

OPTION 1: Quick Manual Method (Immediate)
=========================================
1. Copy the email content above
2. Open Gmail in your browser  
3. Click "Compose"
4. Paste the content
5. Add recipient email
6. Save as draft

OPTION 2: Automated Gmail Integration (Better)
==============================================
1. Install Google API libraries:
   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

2. Run the Gmail drafts manager:
   python gmail_drafts_manager.py
   
3. Follow OAuth flow to authorize Gmail access
4. Drafts will be created automatically

OPTION 3: Email Client Integration
==================================
Export emails to:
- Apple Mail (.eml format)
- Outlook (.msg format) 
- Thunderbird
- Any IMAP client

OPTION 4: CRM Integration (Klaviyo/Salesforce)
==============================================
- Export to CSV with email content
- Import into CRM email templates
- Use CRM's email sending features
""")

if __name__ == "__main__":
    show_emails_from_latest_campaign()
    create_gmail_draft_instructions()