#!/usr/bin/env python3
"""
Simple HTTP client for Claude API that works around SSL issues
"""

import json
import os
import subprocess
import tempfile

def call_claude_api_via_curl(prompt):
    """Call Claude API using curl to bypass SSL issues"""
    
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return None
        
    # Prepare the request data
    data = {
        'model': 'claude-3-5-sonnet-20241022',
        'max_tokens': 1000,
        'messages': [{
            'role': 'user',
            'content': prompt
        }]
    }
    
    # Write data to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        temp_file = f.name
    
    try:
        # Use curl to make the API call
        cmd = [
            'curl', '-X', 'POST',
            'https://api.anthropic.com/v1/messages',
            '-H', 'x-api-key: {}'.format(api_key),
            '-H', 'anthropic-version: 2023-06-01', 
            '-H', 'content-type: application/json',
            '-d', '@{}'.format(temp_file),
            '--silent'
        ]
        
        result = subprocess.check_output(cmd)
        response = json.loads(result.decode('utf-8'))
        
        if 'content' in response and len(response['content']) > 0:
            return response['content'][0]['text']
        else:
            print("API Error: {}".format(response))
            return None
            
    except subprocess.CalledProcessError as e:
        print("Curl error: {}".format(e))
        return None
    except Exception as e:
        print("Unexpected error: {}".format(e))
        return None
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_file)
        except:
            pass

if __name__ == "__main__":
    # Test the function
    test_prompt = """Generate a personalized outreach email with the following context:

RECIPIENT INFORMATION:
- Name: Sarah Chen
- Company: InnovateTech Solutions
- Title: Chief Technology Officer
- Email: sarah.chen@innovatetech.com

EMAIL REQUIREMENTS:
- Style: professional_friendly
- Purpose: Initial outreach for business development
- Keep it under 150 words
- Include a specific value proposition

Please generate only the email content, no subject line needed."""

    result = call_claude_api_via_curl(test_prompt)
    if result:
        print("SUCCESS! Generated email:")
        print("=" * 50)
        print(result)
        print("=" * 50)
    else:
        print("Failed to generate email")