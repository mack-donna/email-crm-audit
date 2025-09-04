#!/usr/bin/env python3
"""
Simple test of AI email generation with proper error handling
"""

import os
import json

# Test data
contact = {
    'name': 'Sarah Chen',
    'email': 'sarah.chen@innovatetech.com',
    'company': 'InnovateTech Solutions', 
    'title': 'Chief Technology Officer'
}

research = {
    'company_info': 'Technology company focused on innovation',
    'industry_context': 'Tech startup space'
}

def generate_test_email():
    """Generate a test email with AI"""
    
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("No API key found")
        return None
        
    print("Found API key: {}...".format(api_key[:20]))
    
    # For now, let's create a mock AI response to test the flow
    mock_ai_email = """Subject: Exploring AI innovation opportunities with {company}

Hi {name},

I noticed {company}'s focus on technology innovation, and I thought you might be interested in discussing how companies like yours are leveraging AI to accelerate their development cycles.

As {title}, you're likely evaluating emerging technologies that could give {company} a competitive edge. I've been working with similar tech companies to implement AI-powered solutions that have reduced their time-to-market by 30-40%.

Would you be open to a brief conversation about how this might apply to your current initiatives? I'd be happy to share some specific examples from companies in your space.

Best regards,
[Your name]

P.S. I saw that innovation is core to your company's mission - I think you'd find these case studies particularly relevant.""".format(
        company=contact['company'],
        name=contact['name'], 
        title=contact['title']
    )

    print("Generated AI email:")
    print("=" * 50)
    print(mock_ai_email)
    print("=" * 50)
    
    return mock_ai_email

if __name__ == "__main__":
    generate_test_email()