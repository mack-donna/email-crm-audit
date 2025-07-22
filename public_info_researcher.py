#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module 3: Public Information Research System
Multi-source information gathering with graceful degradation for personalized outreach.
"""

import json
import logging
import re
import time
from datetime import datetime
try:
    # Python 3
    from urllib.parse import urlparse, quote_plus
    from urllib.request import urlopen, Request
    from urllib.error import URLError, HTTPError
except ImportError:
    # Python 2
    from urlparse import urlparse
    from urllib import quote_plus
    from urllib2 import urlopen, Request, URLError, HTTPError

# BeautifulSoup is optional - graceful degradation if not installed
try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False
    print("Warning: BeautifulSoup not installed. Web scraping will be limited.")


class PublicInfoResearcher:
    """
    Multi-source public information gathering system.
    
    Tiers:
    1. Company websites (high reliability)
    2. News and press releases (medium reliability)
    3. Additional sources as available
    
    Features graceful degradation when sources are unavailable.
    """
    
    def __init__(self, log_level="INFO"):
        self.setup_logging(log_level)
        self.research_stats = {
            'total_searches': 0,
            'successful_searches': 0,
            'failed_searches': 0,
            'sources_accessed': {},
            'rate_limits_hit': 0
        }
        
        # User agent for web requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; EmailOutreachBot/1.0; +http://example.com/bot)'
        }
        
    def setup_logging(self, level):
        """Configure comprehensive logging for debugging."""
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format='%(asctime)s - PublicInfoResearcher - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('public_research_{}.log'.format(
                    datetime.now().strftime("%Y%m%d_%H%M%S")
                )),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def research_contact(self, contact_info):
        """
        Research a contact across multiple sources.
        
        Args:
            contact_info: Dict with 'name', 'email', 'company', 'title' (optional)
            
        Returns:
            Dict with research findings from all available sources
        """
        self.logger.info("Starting research for: {} at {}".format(
            contact_info.get('name'), contact_info.get('company')
        ))
        self.research_stats['total_searches'] += 1
        
        research_results = {
            'contact': contact_info,
            'company_research': {},
            'person_research': {},
            'industry_insights': {},
            'recent_news': [],
            'research_quality_score': 0.0,
            'sources_accessed': [],
            'research_timestamp': datetime.now().isoformat()
        }
        
        # Tier 1: Company Website Research
        company_info = self._research_company_website(contact_info.get('company'))
        if company_info:
            research_results['company_research'] = company_info
            research_results['sources_accessed'].append('company_website')
            
        # Tier 2: News and Press Releases
        news_info = self._search_recent_news(contact_info.get('company'))
        if news_info:
            research_results['recent_news'] = news_info
            research_results['sources_accessed'].append('news_search')
            
        # Tier 3: Industry Context
        industry_info = self._research_industry_context(contact_info.get('company'))
        if industry_info:
            research_results['industry_insights'] = industry_info
            research_results['sources_accessed'].append('industry_research')
            
        # Calculate research quality score
        research_results['research_quality_score'] = self._calculate_quality_score(research_results)
        
        if research_results['sources_accessed']:
            self.research_stats['successful_searches'] += 1
        else:
            self.research_stats['failed_searches'] += 1
            
        self.logger.info("Research complete. Quality score: {:.2f}".format(
            research_results['research_quality_score']
        ))
        
        return research_results
        
    def _research_company_website(self, company_name):
        """
        Extract information from company website.
        
        Args:
            company_name: Name of the company
            
        Returns:
            Dict with company information or None
        """
        if not company_name:
            return None
            
        self.logger.info("Researching company website: {}".format(company_name))
        
        # Clean company name for URL construction
        clean_name = re.sub(r'[^\w\s-]', '', company_name.lower())
        clean_name = re.sub(r'[-\s]+', '-', clean_name)
        
        # Try common domain patterns
        potential_urls = [
            'https://www.{}.com'.format(clean_name),
            'https://{}.com'.format(clean_name),
            'https://www.{}.io'.format(clean_name),
            'https://{}.io'.format(clean_name)
        ]
        
        for url in potential_urls:
            try:
                company_info = self._scrape_website(url)
                if company_info:
                    self.logger.info("Successfully scraped: {}".format(url))
                    self._update_source_stats('company_website', True)
                    return company_info
            except Exception as e:
                self.logger.debug("Failed to scrape {}: {}".format(url, str(e)))
                continue
                
        self._update_source_stats('company_website', False)
        return None
        
    def _scrape_website(self, url):
        """
        Scrape basic information from a website.
        
        Args:
            url: Website URL
            
        Returns:
            Dict with scraped information
        """
        try:
            # Rate limiting
            time.sleep(1)  # Be respectful to servers
            
            req = Request(url, headers=self.headers)
            response = urlopen(req, timeout=10)
            
            if response.getcode() != 200:
                return None
                
            html = response.read()
            
            # If BeautifulSoup is available, use it for better parsing
            if BEAUTIFULSOUP_AVAILABLE:
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract basic information
                info = {
                    'url': url,
                    'title': self._extract_title(soup),
                    'description': self._extract_description(soup),
                    'keywords': self._extract_keywords(soup),
                    'about_snippet': self._extract_about_snippet(soup)
                }
                
                return info if any(info.values()) else None
            else:
                # Fallback: Basic regex extraction
                return self._basic_html_extraction(html.decode('utf-8', errors='ignore'))
                
        except (URLError, HTTPError) as e:
            self.logger.debug("URL error for {}: {}".format(url, str(e)))
            return None
        except Exception as e:
            self.logger.debug("Error scraping {}: {}".format(url, str(e)))
            return None
            
    def _extract_title(self, soup):
        """Extract page title."""
        if soup.title:
            return soup.title.string.strip()
        return None
        
    def _extract_description(self, soup):
        """Extract meta description."""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            return meta_desc.get('content', '').strip()
        return None
        
    def _extract_keywords(self, soup):
        """Extract meta keywords."""
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            return meta_keywords.get('content', '').strip()
        return None
        
    def _extract_about_snippet(self, soup):
        """Try to extract about/mission text."""
        # Look for common about section indicators
        about_patterns = ['about', 'mission', 'who we are', 'what we do']
        
        for pattern in about_patterns:
            # Try to find headings with these patterns
            for heading in soup.find_all(['h1', 'h2', 'h3']):
                if heading.string and pattern in heading.string.lower():
                    # Get the next paragraph
                    next_p = heading.find_next_sibling('p')
                    if next_p:
                        return next_p.get_text().strip()[:500]  # Limit length
                        
        return None
        
    def _basic_html_extraction(self, html_text):
        """Fallback HTML extraction without BeautifulSoup."""
        info = {}
        
        # Extract title
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_text, re.IGNORECASE)
        if title_match:
            info['title'] = title_match.group(1).strip()
            
        # Extract meta description
        desc_match = re.search(
            r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']',
            html_text, re.IGNORECASE
        )
        if desc_match:
            info['description'] = desc_match.group(1).strip()
            
        return info if info else None
        
    def _search_recent_news(self, company_name):
        """
        Search for recent news about the company.
        
        For now, this is a placeholder that demonstrates the architecture.
        In production, this could integrate with news APIs.
        """
        if not company_name:
            return []
            
        self.logger.info("Searching for news about: {}".format(company_name))
        
        # Placeholder for news search
        # In production, integrate with:
        # - Google News API
        # - NewsAPI.org
        # - RSS feeds
        # - Press release sites
        
        news_results = []
        
        # Simulate finding some news
        # In real implementation, this would make actual API calls
        self._update_source_stats('news_search', False)
        
        return news_results
        
    def _research_industry_context(self, company_name):
        """
        Research industry context and trends.
        
        Placeholder for industry research functionality.
        """
        if not company_name:
            return {}
            
        self.logger.info("Researching industry context for: {}".format(company_name))
        
        # Placeholder for industry research
        # Could integrate with:
        # - Industry databases
        # - Trade publications
        # - Market research reports
        
        industry_info = {}
        
        self._update_source_stats('industry_research', False)
        
        return industry_info
        
    def _calculate_quality_score(self, research_results):
        """
        Calculate quality score for research results.
        
        Args:
            research_results: Research findings
            
        Returns:
            Float score between 0.0 and 1.0
        """
        score = 0.0
        max_score = 0.0
        
        # Company research (weight: 0.4)
        max_score += 0.4
        if research_results['company_research']:
            company_score = 0.0
            if research_results['company_research'].get('title'):
                company_score += 0.1
            if research_results['company_research'].get('description'):
                company_score += 0.2
            if research_results['company_research'].get('about_snippet'):
                company_score += 0.1
            score += company_score
            
        # News (weight: 0.3)
        max_score += 0.3
        if research_results['recent_news']:
            news_score = min(len(research_results['recent_news']) * 0.1, 0.3)
            score += news_score
            
        # Industry insights (weight: 0.3)
        max_score += 0.3
        if research_results['industry_insights']:
            score += 0.3
            
        return score / max_score if max_score > 0 else 0.0
        
    def _update_source_stats(self, source_name, success):
        """Update statistics for source access."""
        if source_name not in self.research_stats['sources_accessed']:
            self.research_stats['sources_accessed'][source_name] = {
                'attempts': 0,
                'successes': 0
            }
            
        self.research_stats['sources_accessed'][source_name]['attempts'] += 1
        if success:
            self.research_stats['sources_accessed'][source_name]['successes'] += 1
            
    def generate_research_report(self):
        """Generate summary report of research operations."""
        report = """
=== PUBLIC INFORMATION RESEARCH REPORT ===

RESEARCH STATISTICS:
- Total searches performed: {}
- Successful searches: {}
- Failed searches: {}
- Success rate: {:.1f}%

SOURCE ACCESS STATISTICS:
""".format(
            self.research_stats['total_searches'],
            self.research_stats['successful_searches'],
            self.research_stats['failed_searches'],
            (self.research_stats['successful_searches'] / 
             max(self.research_stats['total_searches'], 1)) * 100
        )
        
        for source, stats in self.research_stats['sources_accessed'].items():
            success_rate = (stats['successes'] / max(stats['attempts'], 1)) * 100
            report += "- {}: {}/{} attempts successful ({:.1f}%)\n".format(
                source, stats['successes'], stats['attempts'], success_rate
            )
            
        return report


def main():
    """Test the public information researcher independently."""
    print("\n=== Public Information Research System Test ===\n")
    
    # Initialize researcher
    researcher = PublicInfoResearcher()
    
    # Test data
    test_contacts = [
        {
            'name': 'John Smith',
            'email': 'john.smith@google.com',
            'company': 'Google',
            'title': 'Software Engineer'
        },
        {
            'name': 'Jane Doe',
            'email': 'jane@startupxyz.com',
            'company': 'StartupXYZ',
            'title': 'CEO'
        }
    ]
    
    # Test research for each contact
    for contact in test_contacts:
        print("\nResearching: {} at {}".format(
            contact['name'], contact['company']
        ))
        print("-" * 50)
        
        results = researcher.research_contact(contact)
        
        print("Sources accessed: {}".format(', '.join(results['sources_accessed'])))
        print("Research quality score: {:.2f}".format(results['research_quality_score']))
        
        if results['company_research']:
            print("\nCompany research findings:")
            for key, value in results['company_research'].items():
                if value:
                    print("  - {}: {}".format(key, value[:100] + '...' if len(str(value)) > 100 else value))
                    
    # Generate report
    print("\n" + researcher.generate_research_report())
    
    print("\n✅ Module 3 Test Complete!")
    print("🔍 Public information research system is operational")
    print("📊 Note: This is a foundation - additional data sources can be added")


if __name__ == "__main__":
    main()