#!/usr/bin/env python3
"""
Klaviyo Integration Module for Email Outreach Automation
Connects Klaviyo flows with the outreach system for qualified lead processing
"""

import json
import csv
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import requests
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'klaviyo_sync_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

@dataclass
class KlaviyoContact:
    """Represents a qualified contact from Klaviyo flows"""
    email: str
    source_flow: str
    engagement_score: float
    last_activity: datetime
    products_interested: List[str]
    cart_value: float = 0.0
    browse_count: int = 0
    abandon_count: int = 0
    purchase_history: List[Dict] = None
    tags: List[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for CSV export"""
        return {
            'email': self.email,
            'source_flow': self.source_flow,
            'engagement_score': self.engagement_score,
            'last_activity': self.last_activity.isoformat(),
            'products_interested': '|'.join(self.products_interested),
            'cart_value': self.cart_value,
            'browse_count': self.browse_count,
            'abandon_count': self.abandon_count,
            'tags': '|'.join(self.tags or [])
        }

class KlaviyoIntegration:
    """Handles Klaviyo API integration and data export"""
    
    def __init__(self, api_key: str, private_key: str = None):
        self.api_key = api_key
        self.private_key = private_key
        self.base_url = "https://a.klaviyo.com/api"
        self.headers = {
            "Authorization": f"Klaviyo-API-Key {api_key}",
            "revision": "2024-10-15",
            "Accept": "application/json"
        }
        
    def fetch_flow_members(self, flow_id: str, status: str = "completed") -> List[Dict]:
        """Fetch members who completed or exited a specific flow"""
        endpoint = f"{self.base_url}/flows/{flow_id}/flow-actions"
        
        params = {
            "filter": f"equals(status,'{status}')",
            "page[size]": 100
        }
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json().get('data', [])
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching flow members: {e}")
            return []
    
    def get_profile_metrics(self, profile_id: str) -> Dict:
        """Get detailed metrics for a specific profile"""
        endpoint = f"{self.base_url}/profiles/{profile_id}"
        
        params = {
            "fields[profile]": "email,first_name,last_name,phone_number,created,updated",
            "include": "lists,segments"
        }
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json().get('data', {})
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching profile metrics: {e}")
            return {}
    
    def calculate_engagement_score(self, profile_data: Dict) -> float:
        """Calculate engagement score based on Klaviyo metrics"""
        score = 0.0
        
        # Email engagement
        metrics = profile_data.get('attributes', {}).get('metrics', {})
        
        # Opens (weighted 20%)
        opens = metrics.get('email_opens', 0)
        score += min(opens * 2, 20)
        
        # Clicks (weighted 30%)
        clicks = metrics.get('email_clicks', 0)
        score += min(clicks * 5, 30)
        
        # Site activity (weighted 25%)
        views = metrics.get('product_views', 0)
        score += min(views * 2.5, 25)
        
        # Cart activity (weighted 25%)
        cart_value = metrics.get('abandoned_cart_value', 0)
        if cart_value > 0:
            score += min(cart_value / 10, 25)
        
        return round(score, 2)
    
    def qualify_for_outreach(self, contact: KlaviyoContact) -> bool:
        """Determine if contact qualifies for outreach automation"""
        
        # Qualification criteria
        if contact.source_flow == "browse_abandon":
            return (
                contact.engagement_score >= 40 and
                contact.browse_count >= 3 and
                len(contact.products_interested) >= 2
            )
        
        elif contact.source_flow == "cart_abandon":
            return (
                contact.cart_value >= 100 and
                contact.abandon_count >= 2 and
                contact.engagement_score >= 50
            )
        
        elif contact.source_flow == "post_purchase":
            # Reactivation candidates
            days_since_activity = (datetime.now() - contact.last_activity).days
            return (
                days_since_activity >= 60 and
                contact.engagement_score >= 30
            )
        
        return False

class FlowProcessor:
    """Process specific Klaviyo flows and export qualified contacts"""
    
    def __init__(self, klaviyo: KlaviyoIntegration):
        self.klaviyo = klaviyo
        self.qualified_contacts = []
        
    def process_browse_abandon(self, flow_id: str):
        """Process Browse Abandon + Dynamic Social Proof flow"""
        logging.info("Processing Browse Abandon flow...")
        
        members = self.klaviyo.fetch_flow_members(flow_id)
        
        for member in members:
            profile_id = member.get('relationships', {}).get('profile', {}).get('data', {}).get('id')
            if not profile_id:
                continue
                
            profile = self.klaviyo.get_profile_metrics(profile_id)
            attributes = profile.get('attributes', {})
            
            # Extract product interests from custom properties
            products = attributes.get('custom_properties', {}).get('viewed_products', [])
            
            contact = KlaviyoContact(
                email=attributes.get('email'),
                source_flow='browse_abandon',
                engagement_score=self.klaviyo.calculate_engagement_score(profile),
                last_activity=datetime.fromisoformat(attributes.get('updated')),
                products_interested=products,
                browse_count=len(products),
                tags=['browse_abandon_qualified', 'social_proof_responsive']
            )
            
            if self.klaviyo.qualify_for_outreach(contact):
                self.qualified_contacts.append(contact)
                logging.info(f"Qualified contact: {contact.email}")
    
    def process_cart_abandon(self, flow_id: str):
        """Process Cart Abandon + Creator Video flow"""
        logging.info("Processing Cart Abandon flow...")
        
        members = self.klaviyo.fetch_flow_members(flow_id)
        
        for member in members:
            profile_id = member.get('relationships', {}).get('profile', {}).get('data', {}).get('id')
            if not profile_id:
                continue
                
            profile = self.klaviyo.get_profile_metrics(profile_id)
            attributes = profile.get('attributes', {})
            
            # Extract cart information
            cart_data = attributes.get('custom_properties', {}).get('abandoned_cart', {})
            
            contact = KlaviyoContact(
                email=attributes.get('email'),
                source_flow='cart_abandon',
                engagement_score=self.klaviyo.calculate_engagement_score(profile),
                last_activity=datetime.fromisoformat(attributes.get('updated')),
                products_interested=[item.get('product_name') for item in cart_data.get('items', [])],
                cart_value=cart_data.get('value', 0),
                abandon_count=attributes.get('custom_properties', {}).get('abandon_count', 1),
                tags=['high_intent_abandon', 'video_engaged']
            )
            
            if self.klaviyo.qualify_for_outreach(contact):
                self.qualified_contacts.append(contact)
                logging.info(f"Qualified contact: {contact.email}")
    
    def process_post_purchase(self, flow_id: str):
        """Process Post-Purchase + Referral Loop flow"""
        logging.info("Processing Post-Purchase flow...")
        
        members = self.klaviyo.fetch_flow_members(flow_id)
        
        for member in members:
            profile_id = member.get('relationships', {}).get('profile', {}).get('data', {}).get('id')
            if not profile_id:
                continue
                
            profile = self.klaviyo.get_profile_metrics(profile_id)
            attributes = profile.get('attributes', {})
            
            # Check for repeat purchase
            purchase_count = attributes.get('custom_properties', {}).get('purchase_count', 1)
            last_purchase = attributes.get('custom_properties', {}).get('last_purchase_date')
            
            if purchase_count == 1 and last_purchase:
                last_purchase_date = datetime.fromisoformat(last_purchase)
                days_since_purchase = (datetime.now() - last_purchase_date).days
                
                if days_since_purchase >= 60:
                    contact = KlaviyoContact(
                        email=attributes.get('email'),
                        source_flow='post_purchase',
                        engagement_score=self.klaviyo.calculate_engagement_score(profile),
                        last_activity=last_purchase_date,
                        products_interested=attributes.get('custom_properties', {}).get('purchased_products', []),
                        tags=['reactivation_candidate', 'single_purchase']
                    )
                    
                    if self.klaviyo.qualify_for_outreach(contact):
                        self.qualified_contacts.append(contact)
                        logging.info(f"Qualified contact: {contact.email}")
    
    def export_to_csv(self, filename: str = None):
        """Export qualified contacts to CSV for outreach system"""
        if not self.qualified_contacts:
            logging.warning("No qualified contacts to export")
            return None
            
        if not filename:
            filename = f"klaviyo_qualified_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = [
                'email', 'source_flow', 'engagement_score', 'last_activity',
                'products_interested', 'cart_value', 'browse_count', 
                'abandon_count', 'tags'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for contact in self.qualified_contacts:
                writer.writerow(contact.to_dict())
        
        logging.info(f"Exported {len(self.qualified_contacts)} contacts to {filename}")
        return filename
    
    def generate_outreach_insights(self) -> Dict:
        """Generate insights for outreach personalization"""
        insights = {
            'total_qualified': len(self.qualified_contacts),
            'by_source': {},
            'avg_engagement': 0,
            'top_products': {},
            'high_value_prospects': []
        }
        
        if not self.qualified_contacts:
            return insights
        
        # Aggregate by source
        for contact in self.qualified_contacts:
            source = contact.source_flow
            if source not in insights['by_source']:
                insights['by_source'][source] = 0
            insights['by_source'][source] += 1
            
            # Track product interest
            for product in contact.products_interested:
                if product not in insights['top_products']:
                    insights['top_products'][product] = 0
                insights['top_products'][product] += 1
            
            # Identify high-value prospects
            if contact.cart_value >= 200 or contact.engagement_score >= 70:
                insights['high_value_prospects'].append({
                    'email': contact.email,
                    'value': contact.cart_value,
                    'score': contact.engagement_score
                })
        
        # Calculate average engagement
        total_score = sum(c.engagement_score for c in self.qualified_contacts)
        insights['avg_engagement'] = round(total_score / len(self.qualified_contacts), 2)
        
        # Sort products by popularity
        insights['top_products'] = dict(
            sorted(insights['top_products'].items(), 
                   key=lambda x: x[1], reverse=True)[:10]
        )
        
        return insights

def main():
    """Main execution function"""
    # Configuration (would typically come from environment variables)
    KLAVIYO_API_KEY = "your_klaviyo_api_key"
    
    # Flow IDs (would be configured per account)
    FLOWS = {
        'browse_abandon': 'flow_id_1',
        'cart_abandon': 'flow_id_2',
        'post_purchase': 'flow_id_3'
    }
    
    # Initialize integration
    klaviyo = KlaviyoIntegration(KLAVIYO_API_KEY)
    processor = FlowProcessor(klaviyo)
    
    # Process each flow
    processor.process_browse_abandon(FLOWS['browse_abandon'])
    processor.process_cart_abandon(FLOWS['cart_abandon'])
    processor.process_post_purchase(FLOWS['post_purchase'])
    
    # Export qualified contacts
    csv_file = processor.export_to_csv()
    
    # Generate insights
    insights = processor.generate_outreach_insights()
    
    # Save insights
    with open('klaviyo_insights.json', 'w') as f:
        json.dump(insights, f, indent=2, default=str)
    
    logging.info(f"Processing complete. Insights saved to klaviyo_insights.json")
    logging.info(f"Summary: {insights['total_qualified']} qualified contacts")
    
    return csv_file, insights

if __name__ == "__main__":
    main()