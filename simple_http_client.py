#!/usr/bin/env python3
"""
Simple HTTP client for Claude API that works around SSL issues
"""

import json
import os
import subprocess
import tempfile

import config

def call_claude_api_via_curl(prompt):
    """Call Claude API using curl to bypass SSL issues"""
    
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return None
        
    # Prepare the request data
    data = {
        'model': config.CLAUDE_MODEL,
        'max_tokens': config.CLAUDE_MAX_TOKENS,
        'output_config': {'effort': config.CLAUDE_EFFORT},
        'fallbacks': 'default',
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
            '-H', 'anthropic-beta: {}'.format(config.CLAUDE_FALLBACK_BETA),
            '-H', 'content-type: application/json',
            '-d', '@{}'.format(temp_file),
            '--silent'
        ]
        
        result = subprocess.check_output(cmd)
        response = json.loads(result.decode('utf-8'))
        
        if response.get('stop_reason') == 'refusal':
            print("Claude declined the request")
            return None
        if response.get('stop_reason') == 'max_tokens':
            print("Claude hit max_tokens; response would be cut off")
            return None
        # Read by block type: a thinking block can come before the text.
        text = next((b.get('text') for b in response.get('content', []) if b.get('type') == 'text'), None)
        if text:
            return text
        print("API Error: {}".format(response.get('error', response.get('stop_reason'))))
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
        except (OSError, FileNotFoundError) as e:
            print("Failed to cleanup temp file {}: {}".format(temp_file, str(e)))

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