#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Review Interface - Non-interactive demo
"""

from review_interface import ReviewInterface
import json

def demo_review_interface():
    """Demonstrate the review interface functionality."""
    print("\n=== Human Review Interface Demo ===\n")
    
    # Initialize interface
    interface = ReviewInterface()
    
    # Sample email data
    sample_email = {
        'contact_context': {
            'contact': {
                'name': 'John Smith',
                'email': 'john.smith@techcorp.com',
                'company': 'TechCorp',
                'title': 'CTO'
            },
            'research': {
                'company_research': {
                    'description': 'Leading software company specializing in AI solutions'
                },
                'research_quality_score': 0.8
            }
        },
        'email_content': """Hi John,

I noticed that TechCorp is leading the way in AI solutions. I'm reaching out because I believe we could help accelerate your development cycles.

We've helped similar tech companies reduce deployment time by 40% while improving code quality. 

Would you be open to a brief conversation to explore if there's a fit?

Best regards,
[Your name]""",
        'metadata': {
            'style': 'professional_friendly',
            'confidence_score': 0.85,
            'personalization_points': ['Used recipient name', 'Referenced company research']
        }
    }
    
    # Demonstrate display format
    print("SAMPLE EMAIL REVIEW DISPLAY:")
    print("="*60)
    print("\nCONTACT INFORMATION:")
    print("-" * 30)
    print("Name: {}".format(sample_email['contact_context']['contact'].get('name')))
    print("Company: {}".format(sample_email['contact_context']['contact'].get('company')))
    print("Title: {}".format(sample_email['contact_context']['contact'].get('title')))
    print("Email: {}".format(sample_email['contact_context']['contact'].get('email')))
    
    print("\nRESEARCH CONTEXT:")
    print("-" * 30)
    print("Company: {}".format(
        sample_email['contact_context']['research']['company_research']['description']
    ))
    print("Research Quality: {:.1f}/5".format(
        sample_email['contact_context']['research'].get('research_quality_score', 0) * 5
    ))
    
    print("\nGENERATED EMAIL:")
    print("-" * 30)
    print(sample_email['email_content'])
    print("-" * 30)
    
    print("\nEMAIL METADATA:")
    print("Style: {}".format(sample_email['metadata'].get('style')))
    print("Confidence: {:.0%}".format(sample_email['metadata'].get('confidence_score')))
    print("Personalization: {}".format(', '.join(sample_email['metadata'].get('personalization_points'))))
    
    print("\n" + "="*60)
    print("AVAILABLE ACTIONS:")
    print("[A]pprove - Send as-is")
    print("[E]dit - Make changes before sending")
    print("[R]eject - Don't send, provide feedback")
    print("[S]kip - Review later")
    print("[Q]uit - End session")
    
    # Demonstrate approval
    print("\n\nDEMO: Simulating email approval...")
    interface.approve_email(sample_email)
    
    # Show export format
    print("\nEXPORT FORMAT (approved_emails_TIMESTAMP.json):")
    print("-" * 60)
    export_sample = {
        'session_info': {
            'start_time': '2025-01-21T16:00:00',
            'total_reviewed': 5,
            'total_approved': 4
        },
        'approved_emails': [sample_email]
    }
    print(json.dumps(export_sample, indent=2)[:500] + "...")
    
    print("\n✅ Review Interface Features:")
    print("- Clear presentation of all context")
    print("- Quick keyboard-based workflow")
    print("- Edit capability for fine-tuning")
    print("- Session statistics tracking")
    print("- JSON export for integration")
    print("- Suitable for 50+ emails per session")

if __name__ == "__main__":
    demo_review_interface()