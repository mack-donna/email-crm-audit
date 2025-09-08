#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn API Client for B2B Contact Enhancement
Integrates with LinkedIn API to gather professional context for email personalization.
"""

import os
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from urllib.parse import urlencode

class LinkedInClient:
    """
    LinkedIn API client for gathering professional context about contacts.
    
    Features:
    - OAuth2 authentication flow
    - Profile data extraction
    - Company information gathering
    - Recent activity insights
    - Rate limiting and error handling
    """
    
    def __init__(self, client_id=None, client_secret=None, log_level="INFO"):
        self.client_id = client_id or os.getenv('LINKEDIN_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('LINKEDIN_CLIENT_SECRET')
        self.access_token = None
        self.token_expires_at = None
        
        # API endpoints
        self.base_url = "https://api.linkedin.com/v2"
        self.oauth_url = "https://www.linkedin.com/oauth/v2"
        
        # Rate limiting
        self.requests_made = 0
        self.last_request_time = None
        self.rate_limit_window = 3600  # 1 hour
        self.max_requests_per_hour = 100
        
        self.setup_logging(log_level)
        
        # Cache for profile data to minimize API calls
        self.profile_cache = {}
        self.cache_ttl = 3600  # 1 hour cache
        
    def setup_logging(self, level):
        """Configure logging for LinkedIn API operations."""
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format='%(asctime)s - LinkedInClient - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def is_configured(self):
        """Check if LinkedIn API credentials are configured."""
        return bool(self.client_id and self.client_secret)
        
    def get_authorization_url(self, redirect_uri, state=None, scopes=None):
        """
        Generate LinkedIn OAuth authorization URL.
        
        Args:
            redirect_uri: URL to redirect to after authorization
            state: CSRF protection state parameter
            scopes: List of requested permissions
            
        Returns:
            Authorization URL string
        """
        if not self.is_configured():
            raise ValueError("LinkedIn API credentials not configured")
            
        default_scopes = ['r_liteprofile', 'r_emailaddress']
        scopes = scopes or default_scopes
        
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'state': state or 'linkedin_oauth_state',
            'scope': ' '.join(scopes)
        }
        
        return f"{self.oauth_url}/authorization?{urlencode(params)}"
        
    def exchange_code_for_token(self, code, redirect_uri):
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from LinkedIn
            redirect_uri: Same redirect URI used in authorization
            
        Returns:
            Dict with token information
        """
        if not self.is_configured():
            raise ValueError("LinkedIn API credentials not configured")
            
        token_url = f"{self.oauth_url}/accessToken"
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            response = requests.post(token_url, data=data, headers=headers)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            
            # Calculate expiration time
            expires_in = token_data.get('expires_in', 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            self.logger.info("LinkedIn access token obtained successfully")
            return token_data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to exchange code for token: {e}")
            raise
            
    def _check_rate_limit(self):
        """Check if we're within rate limits."""
        now = time.time()
        
        if self.last_request_time is None:
            self.last_request_time = now
            self.requests_made = 0
            return True
            
        # Reset counter if window has passed
        if now - self.last_request_time >= self.rate_limit_window:
            self.requests_made = 0
            self.last_request_time = now
            
        if self.requests_made >= self.max_requests_per_hour:
            self.logger.warning("LinkedIn API rate limit reached")
            return False
            
        return True
        
    def _make_api_request(self, endpoint, params=None):
        """
        Make authenticated API request to LinkedIn.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            JSON response data
        """
        if not self.access_token:
            raise ValueError("No access token available. Complete OAuth flow first.")
            
        if not self._check_rate_limit():
            raise Exception("Rate limit exceeded. Try again later.")
            
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            self.requests_made += 1
            self.last_request_time = time.time()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"LinkedIn API request failed: {e}")
            if hasattr(e.response, 'status_code') and e.response.status_code == 429:
                self.logger.warning("LinkedIn API rate limit hit")
            raise
            
    def get_profile_by_email(self, email):
        """
        Get LinkedIn profile information by email address.
        Note: This requires special API permissions that may not be available.
        
        Args:
            email: Email address to look up
            
        Returns:
            Profile information dict or None
        """
        # Check cache first
        cache_key = f"email_{email}"
        if cache_key in self.profile_cache:
            cached_data, cached_time = self.profile_cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                self.logger.info(f"Using cached profile data for {email}")
                return cached_data
                
        self.logger.warning("Email lookup requires special LinkedIn API permissions")
        self.logger.info("Consider using profile URL lookup instead")
        return None
        
    def get_profile_by_url(self, profile_url):
        """
        Extract profile information from LinkedIn profile URL.
        
        Args:
            profile_url: LinkedIn profile URL
            
        Returns:
            Profile information dict
        """
        # Check cache first
        cache_key = f"url_{profile_url}"
        if cache_key in self.profile_cache:
            cached_data, cached_time = self.profile_cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                self.logger.info(f"Using cached profile data for {profile_url}")
                return cached_data
                
        try:
            # Extract LinkedIn username from URL
            username = self._extract_username_from_url(profile_url)
            if not username:
                self.logger.error(f"Could not extract username from URL: {profile_url}")
                return None
                
            # With basic API access, we can only get limited public profile info
            # For enhanced data, API partnership is required
            profile_data = self._get_basic_profile_info(username)
            
            # Cache the result
            self.profile_cache[cache_key] = (profile_data, time.time())
            
            return profile_data
            
        except Exception as e:
            self.logger.error(f"Failed to get profile by URL: {e}")
            return None
            
    def _extract_username_from_url(self, profile_url):
        """Extract LinkedIn username from profile URL."""
        import re
        
        # Handle various LinkedIn URL formats
        patterns = [
            r'linkedin\.com/in/([^/\?]+)',
            r'linkedin\.com/pub/([^/\?]+)',
            r'linkedin\.com/profile/view\?id=([^&]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, profile_url)
            if match:
                return match.group(1)
                
        return None
        
    def _get_basic_profile_info(self, username):
        """
        Get basic profile information using available API endpoints.
        
        Args:
            username: LinkedIn username
            
        Returns:
            Basic profile information dict
        """
        try:
            # Use the lite profile endpoint (available with basic API access)
            profile_data = self._make_api_request('/me')
            
            # Structure the data for our email generation system
            return {
                'id': profile_data.get('id'),
                'first_name': profile_data.get('localizedFirstName'),
                'last_name': profile_data.get('localizedLastName'),
                'headline': profile_data.get('localizedHeadline'),
                'profile_url': f"https://linkedin.com/in/{username}",
                'profile_picture': profile_data.get('profilePicture', {}).get('displayImage'),
                'location': self._extract_location(profile_data),
                'data_source': 'linkedin_api',
                'retrieved_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get basic profile info: {e}")
            return self._get_fallback_profile_info(username)
            
    def _extract_location(self, profile_data):
        """Extract location information from profile data."""
        try:
            return profile_data.get('location', {}).get('preferredLocale', {}).get('country')
        except (AttributeError, KeyError):
            return None
            
    def _get_fallback_profile_info(self, username):
        """
        Provide basic profile structure when API calls fail.
        
        Args:
            username: LinkedIn username
            
        Returns:
            Basic profile structure
        """
        return {
            'username': username,
            'profile_url': f"https://linkedin.com/in/{username}",
            'data_source': 'fallback',
            'retrieved_at': datetime.now().isoformat(),
            'note': 'Limited data - LinkedIn API access required for full profile'
        }
        
    def enhance_contact_with_linkedin(self, contact_info):
        """
        Enhance contact information with LinkedIn data.
        
        Args:
            contact_info: Dict with contact information
            
        Returns:
            Enhanced contact dict with LinkedIn context
        """
        if not self.is_configured():
            self.logger.warning("LinkedIn API not configured - skipping LinkedIn enhancement")
            return contact_info
            
        enhanced_contact = contact_info.copy()
        linkedin_data = {}
        
        try:
            # Try to find LinkedIn profile URL in contact info
            linkedin_url = contact_info.get('linkedin_url') or contact_info.get('linkedin_profile')
            
            if linkedin_url:
                profile_data = self.get_profile_by_url(linkedin_url)
                if profile_data:
                    linkedin_data = profile_data
            else:
                # Try email lookup (requires special permissions)
                email = contact_info.get('email')
                if email:
                    profile_data = self.get_profile_by_email(email)
                    if profile_data:
                        linkedin_data = profile_data
                        
            # Add LinkedIn data to contact
            if linkedin_data:
                enhanced_contact['linkedin_data'] = linkedin_data
                
                # Extract key information for email personalization
                personalization_context = self._extract_personalization_context(linkedin_data)
                enhanced_contact['linkedin_context'] = personalization_context
                
                self.logger.info(f"Enhanced contact {contact_info.get('name')} with LinkedIn data")
            else:
                self.logger.info(f"No LinkedIn data found for {contact_info.get('name')}")
                
        except Exception as e:
            self.logger.error(f"Failed to enhance contact with LinkedIn data: {e}")
            
        return enhanced_contact
        
    def _extract_personalization_context(self, linkedin_data):
        """
        Extract key information for email personalization.
        
        Args:
            linkedin_data: LinkedIn profile data
            
        Returns:
            Dict with personalization context
        """
        context = {
            'full_name': f"{linkedin_data.get('first_name', '')} {linkedin_data.get('last_name', '')}".strip(),
            'headline': linkedin_data.get('headline'),
            'location': linkedin_data.get('location'),
            'profile_url': linkedin_data.get('profile_url'),
            'conversation_starters': []
        }
        
        # Generate conversation starters based on available data
        if linkedin_data.get('headline'):
            context['conversation_starters'].append(
                f"I noticed you're {linkedin_data['headline'].lower()}"
            )
            
        if linkedin_data.get('location'):
            context['conversation_starters'].append(
                f"I see you're based in {linkedin_data['location']}"
            )
            
        return context
        
    def get_client_stats(self):
        """Get usage statistics for the LinkedIn client."""
        return {
            'configured': self.is_configured(),
            'requests_made': self.requests_made,
            'cache_entries': len(self.profile_cache),
            'token_expires_at': self.token_expires_at.isoformat() if self.token_expires_at else None,
            'rate_limit_remaining': max(0, self.max_requests_per_hour - self.requests_made)
        }


# Usage example and testing
if __name__ == "__main__":
    # Test the LinkedIn client
    client = LinkedInClient()
    
    print("LinkedIn API Configuration:")
    print(f"- Configured: {client.is_configured()}")
    print(f"- Client ID: {'Set' if client.client_id else 'Not set'}")
    print(f"- Client Secret: {'Set' if client.client_secret else 'Not set'}")
    
    if client.is_configured():
        # Test contact enhancement (without API token)
        test_contact = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'company': 'Tech Corp',
            'linkedin_url': 'https://linkedin.com/in/johndoe'
        }
        
        enhanced = client.enhance_contact_with_linkedin(test_contact)
        print("\nEnhanced contact:")
        print(json.dumps(enhanced, indent=2))
    else:
        print("\nTo use LinkedIn integration:")
        print("1. Set LINKEDIN_CLIENT_ID environment variable")
        print("2. Set LINKEDIN_CLIENT_SECRET environment variable")
        print("3. Complete OAuth flow to get access token")