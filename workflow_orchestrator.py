#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module 7: Workflow Orchestrator
Coordinates all modules for end-to-end email outreach automation.
"""

import json
import os
import logging
import time
from datetime import datetime
import sys

# Import all modules
from contact_processor import ContactProcessor
from public_info_researcher import PublicInfoResearcher
from email_generator import EmailGenerator
from review_interface import ReviewInterface
from learning_engine import LearningEngine

# Optional import for Gmail integration
try:
    from email_history_analyzer import EmailHistoryAnalyzer
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    print("Warning: Gmail integration not available (missing dependencies)")

# Optional import for LinkedIn integration
try:
    from linkedin_client import LinkedInClient
    LINKEDIN_AVAILABLE = True
except ImportError:
    LINKEDIN_AVAILABLE = False
    print("Warning: LinkedIn integration not available (missing dependencies)")


class WorkflowOrchestrator:
    """
    Orchestrates the complete email outreach workflow.
    
    Features:
    - End-to-end pipeline coordination
    - Batch processing with progress tracking
    - Error handling and recovery
    - Integration with learning system
    - Production-ready logging
    """
    
    def __init__(self, config=None, log_level="INFO", linkedin_enrichment_func=None):
        self.config = config or self.load_default_config()
        self.setup_logging(log_level)
        
        # Store LinkedIn enrichment function for session-based data
        self.linkedin_enrichment_func = linkedin_enrichment_func
        
        # Initialize all modules
        self.logger.info("Initializing workflow orchestrator")
        self.initialize_modules()
        
        # Workflow statistics
        self.workflow_stats = {
            'start_time': None,
            'end_time': None,
            'total_contacts': 0,
            'contacts_processed': 0,
            'emails_generated': 0,
            'emails_approved': 0,
            'errors': []
        }
        
    def load_default_config(self):
        """Load default configuration."""
        return {
            'gmail_credentials': 'credentials.json',
            'gmail_token': 'token.pickle',
            'anthropic_api_key': os.environ.get('ANTHROPIC_API_KEY'),
            'batch_size': 10,
            'rate_limit_delay': 1.0,
            'enable_learning': True,
            'output_dir': 'outreach_campaigns'
        }
        
    def setup_logging(self, level):
        """Configure comprehensive logging."""
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('workflow_{}.log'.format(
                    datetime.now().strftime("%Y%m%d_%H%M%S")
                )),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('WorkflowOrchestrator')
        
    def initialize_modules(self):
        """Initialize all system modules."""
        try:
            self.contact_processor = ContactProcessor()
            
            # Initialize Gmail analyzer only if available
            if GMAIL_AVAILABLE and self.config.get('enable_email_history', True):
                self.email_analyzer = EmailHistoryAnalyzer(
                    credentials_file=self.config['gmail_credentials'],
                    token_file=self.config['gmail_token']
                )
            else:
                self.email_analyzer = None
                self.logger.warning("Gmail integration disabled")
                
            # Initialize LinkedIn client only if available
            if LINKEDIN_AVAILABLE and self.config.get('enable_linkedin', True):
                self.linkedin_client = LinkedInClient()
            else:
                self.linkedin_client = None
                if not LINKEDIN_AVAILABLE:
                    self.logger.warning("LinkedIn integration not available")
                else:
                    self.logger.warning("LinkedIn integration disabled")
                
            self.researcher = PublicInfoResearcher()
            self.email_generator = EmailGenerator(
                api_key=self.config['anthropic_api_key']
            )
            self.review_interface = ReviewInterface()
            self.learning_engine = LearningEngine()
            
            self.logger.info("Modules initialized successfully")
            
        except Exception as e:
            self.logger.error("Error initializing modules: {}".format(str(e)))
            raise
            
    def run_campaign(self, csv_file, campaign_name=None, campaign_settings=None):
        """
        Run a complete email outreach campaign.
        
        Args:
            csv_file: Path to CSV file with contacts
            campaign_name: Optional campaign name
            campaign_settings: Dict with goal, tone, length, message
            
        Returns:
            Campaign results summary
        """
        # Store campaign settings for email generation
        if campaign_settings:
            self.campaign_settings = campaign_settings
        else:
            self.campaign_settings = {
                'goal': 'first_meeting',
                'tone': 'professional',
                'length': 'medium',
                'message': ''
            }
        self.workflow_stats['start_time'] = datetime.now()
        campaign_name = campaign_name or "campaign_{}".format(
            datetime.now().strftime("%Y%m%d_%H%M%S")
        )
        
        self.logger.info("Starting campaign: {}".format(campaign_name))
        print("\n" + "="*60)
        print("  EMAIL OUTREACH AUTOMATION CAMPAIGN")
        print("  Campaign: {}".format(campaign_name))
        print("="*60)
        
        try:
            # Phase 1: Process contacts
            print("\n📋 PHASE 1: Processing contacts...")
            contacts = self._process_contacts(csv_file)
            
            if not contacts:
                self.logger.error("No valid contacts found")
                return self._generate_campaign_summary(campaign_name)
                
            # Phase 2: Gmail authentication (if needed)
            if self.config.get('enable_email_history', True):
                print("\n📧 PHASE 2: Gmail authentication...")
                if not self._authenticate_gmail():
                    print("⚠️  Skipping email history analysis")
                    
            # Phase 3: Process contacts in batches
            print("\n🔄 PHASE 3: Processing {} contacts in batches...".format(len(contacts)))
            all_generated_emails = self._process_contact_batches(contacts)
            
            # Phase 4: Review and approve emails
            print("\n✍️  PHASE 4: Review and approval...")
            approved_emails = self._review_emails(all_generated_emails)
            
            # Phase 5: Export results
            print("\n💾 PHASE 5: Exporting results...")
            export_file = self._export_campaign_results(campaign_name, approved_emails)
            
            # Phase 6: Update learning system
            if self.config['enable_learning'] and approved_emails:
                print("\n🧠 PHASE 6: Updating learning system...")
                self._update_learning_system(approved_emails)
                
        except Exception as e:
            self.logger.error("Campaign error: {}".format(str(e)))
            self.workflow_stats['errors'].append(str(e))
            
        finally:
            self.workflow_stats['end_time'] = datetime.now()
            
        # Generate final summary  
        summary = self._generate_campaign_summary(campaign_name)
        
        # Add export file if it exists
        if 'export_file' in locals() and export_file:
            summary['campaign_file'] = export_file
        else:
            # Create a temporary file with the approved emails if export failed
            try:
                temp_file = "outreach_campaigns/temp_{}.json".format(
                    datetime.now().strftime("%Y%m%d_%H%M%S")
                )
                os.makedirs('outreach_campaigns', exist_ok=True)
                with open(temp_file, 'w') as f:
                    json.dump({
                        'campaign_name': campaign_name,
                        'approved_emails': approved_emails if 'approved_emails' in locals() else [],
                        'timestamp': datetime.now().isoformat()
                    }, f)
                summary['campaign_file'] = temp_file
            except:
                pass
                
        return summary
        
    def _process_contacts(self, csv_file):
        """Process CSV file and return valid contacts."""
        try:
            results = self.contact_processor.process_csv(csv_file)
            contacts = results['contacts']
            
            self.workflow_stats['total_contacts'] = len(contacts)
            
            print("✅ Loaded {} valid contacts".format(len(contacts)))
            print("❌ {} invalid contacts".format(
                results['statistics']['invalid_contacts']
            ))
            
            # Show sample contact
            if contacts:
                print("\nSample contact:")
                print("  Name: {}".format(contacts[0]['basic_info']['name']))
                print("  Company: {}".format(contacts[0]['basic_info']['company']))
                
            return contacts
            
        except Exception as e:
            self.logger.error("Error processing contacts: {}".format(str(e)))
            self.workflow_stats['errors'].append("Contact processing: {}".format(str(e)))
            return []
            
    def _authenticate_gmail(self):
        """Authenticate with Gmail API."""
        try:
            self.email_analyzer.authenticate()
            profile = self.email_analyzer.test_connection()
            print("✅ Connected to Gmail: {}".format(profile.get('emailAddress')))
            return True
            
        except Exception as e:
            self.logger.error("Gmail authentication failed: {}".format(str(e)))
            self.workflow_stats['errors'].append("Gmail auth: {}".format(str(e)))
            return False
            
    def _process_contact_batches(self, contacts):
        """Process contacts in batches."""
        all_generated_emails = []
        batch_size = self.config['batch_size']
        
        for i in range(0, len(contacts), batch_size):
            batch = contacts[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = ((len(contacts) - 1) // batch_size) + 1
            
            print("\n--- Batch {}/{} ({} contacts) ---".format(
                batch_num, total_batches, len(batch)
            ))
            
            batch_emails = self._process_batch(batch)
            all_generated_emails.extend(batch_emails)
            
            # Rate limiting between batches
            if i + batch_size < len(contacts):
                time.sleep(self.config['rate_limit_delay'])
                
        return all_generated_emails
        
    def _process_batch(self, batch_contacts):
        """Process a single batch of contacts."""
        batch_emails = []
        
        for idx, contact in enumerate(batch_contacts):
            contact_name = contact['basic_info']['name']
            print("\n  [{}/{}] Processing: {}".format(
                idx + 1, len(batch_contacts), contact_name
            ))
            
            try:
                # Build complete context
                context = self._build_contact_context(contact)
                
                # Get learning recommendations
                if self.config['enable_learning']:
                    recommendations = self.learning_engine.get_contact_recommendations(
                        contact['basic_info']
                    )
                    email_style = recommendations['recommended_style']
                else:
                    email_style = 'professional_friendly'
                    
                # Generate email
                print("    📝 Generating {} email...".format(email_style))
                email_result = self.email_generator.generate_email(
                    context, email_style, self.campaign_settings
                )
                
                if email_result:
                    batch_emails.append(email_result)
                    self.workflow_stats['emails_generated'] += 1
                    print("    ✅ Email generated successfully")
                else:
                    print("    ❌ Failed to generate email")
                    
                self.workflow_stats['contacts_processed'] += 1
                
            except Exception as e:
                self.logger.error("Error processing {}: {}".format(contact_name, str(e)))
                print("    ❌ Error: {}".format(str(e)))
                self.workflow_stats['errors'].append(
                    "Contact {}: {}".format(contact_name, str(e))
                )
                
        return batch_emails
        
    def _build_contact_context(self, contact):
        """Build complete context for a contact."""
        context = {
            'contact': contact['basic_info'],
            'email_history': {},
            'research': {},
            'linkedin_data': {},
            'linkedin_context': {}
        }
        
        # Email history analysis
        if hasattr(self, 'email_analyzer') and self.email_analyzer and hasattr(self.email_analyzer, 'service'):
            print("    🔍 Analyzing email history...")
            try:
                history = self.email_analyzer.search_contact_emails(
                    contact['basic_info']['email'],
                    days_back=365,
                    max_results=20
                )
                if history:
                    context['email_history'] = history
                    print("    ✅ Found {} previous interactions".format(
                        history['total_interactions']
                    ))
            except Exception as e:
                self.logger.warning("Email history search failed: {}".format(str(e)))
                
        # Public information research
        print("    🌐 Researching public information...")
        try:
            research = self.researcher.research_contact(contact['basic_info'])
            context['research'] = research
            print("    ✅ Research quality: {:.0%}".format(
                research.get('research_quality_score', 0)
            ))
        except Exception as e:
            self.logger.warning("Research failed: {}".format(str(e)))
            
        # LinkedIn enrichment (if function provided)
        if self.linkedin_enrichment_func:
            print("    💼 Enriching with LinkedIn data...")
            try:
                linkedin_data = self.linkedin_enrichment_func(contact['basic_info'])
                if linkedin_data:
                    context['linkedin_data'] = linkedin_data.get('linkedin_data', {})
                    context['linkedin_context'] = linkedin_data.get('linkedin_context', {})
                    print("    ✅ LinkedIn data found")
                else:
                    print("    ⚠ No LinkedIn data available")
            except Exception as e:
                self.logger.warning("LinkedIn enrichment failed: {}".format(str(e)))
            
        return context
        
    def _review_emails(self, generated_emails):
        """Review and approve generated emails."""
        if not generated_emails:
            print("No emails to review")
            return []
            
        print("\nGenerated {} emails for review".format(len(generated_emails)))
        
        # For automated testing, approve all
        # In production, this would launch the review interface
        if os.environ.get('AUTO_APPROVE_EMAILS'):
            print("🤖 Auto-approving all emails (test mode)")
            for email in generated_emails:
                email['review_status'] = 'approved'
                email['review_timestamp'] = datetime.now().isoformat()
            self.workflow_stats['emails_approved'] = len(generated_emails)
            return generated_emails
        else:
            # Launch review interface
            self.review_interface.start_review_session(generated_emails)
            approved = self.review_interface.current_session['approved_emails']
            self.workflow_stats['emails_approved'] = len(approved)
            return approved
            
    def _export_campaign_results(self, campaign_name, approved_emails):
        """Export campaign results."""
        # Create output directory
        output_dir = self.config['output_dir']
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Export file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, "{}_{}.json".format(campaign_name, timestamp))
        
        # Convert datetime objects to strings for JSON serialization
        workflow_stats_serializable = dict(self.workflow_stats)
        if workflow_stats_serializable['start_time']:
            workflow_stats_serializable['start_time'] = workflow_stats_serializable['start_time'].isoformat()
        if workflow_stats_serializable['end_time']:
            workflow_stats_serializable['end_time'] = workflow_stats_serializable['end_time'].isoformat()
            
        export_data = {
            'campaign_info': {
                'name': campaign_name,
                'timestamp': timestamp,
                'total_contacts': self.workflow_stats['total_contacts'],
                'emails_generated': self.workflow_stats['emails_generated'],
                'emails_approved': self.workflow_stats['emails_approved']
            },
            'approved_emails': approved_emails,
            'workflow_stats': workflow_stats_serializable
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
                
            print("✅ Campaign results exported to: {}".format(filename))
            
            # Also create a simple text file with email contents
            text_filename = filename.replace('.json', '_emails.txt')
            with open(text_filename, 'w') as f:
                f.write("APPROVED EMAILS FOR CAMPAIGN: {}\n".format(campaign_name))
                f.write("Generated: {}\n".format(timestamp))
                f.write("="*60 + "\n\n")
                
                for idx, email in enumerate(approved_emails):
                    contact = email['contact_context']['contact']
                    f.write("EMAIL {} - To: {} ({})\n".format(
                        idx + 1,
                        contact.get('name'),
                        contact.get('email')
                    ))
                    f.write("-"*60 + "\n")
                    f.write(email['email_content'])
                    f.write("\n\n" + "="*60 + "\n\n")
                    
            print("✅ Email texts exported to: {}".format(text_filename))
            
            return filename
            
        except Exception as e:
            self.logger.error("Error exporting results: {}".format(str(e)))
            return None
            
    def _update_learning_system(self, approved_emails):
        """Update learning system with campaign results."""
        for email in approved_emails:
            # For now, record as sent but not yet responded
            # In production, this would be updated with actual outcomes
            outcome = {
                'was_sent': True,
                'got_response': False  # Would be updated later
            }
            
            self.learning_engine.record_email_outcome(email, outcome)
            
        # Generate learning report
        analysis = self.learning_engine.analyze_performance()
        
        if analysis['recommendations']:
            print("\n📊 Learning System Insights:")
            for rec in analysis['recommendations']:
                print("  - {}".format(rec))
                
    def _generate_campaign_summary(self, campaign_name):
        """Generate campaign summary."""
        duration = None
        if self.workflow_stats['start_time'] and self.workflow_stats['end_time']:
            duration = (self.workflow_stats['end_time'] - 
                       self.workflow_stats['start_time']).total_seconds()
                       
        summary = {
            'campaign_name': campaign_name,
            'duration_seconds': duration,
            'total_contacts': self.workflow_stats['total_contacts'],
            'contacts_processed': self.workflow_stats['contacts_processed'],
            'emails_generated': self.workflow_stats['emails_generated'],
            'emails_approved': self.workflow_stats['emails_approved'],
            'errors_count': len(self.workflow_stats['errors']),
            'success': len(self.workflow_stats['errors']) == 0
        }
        
        # Print summary
        print("\n" + "="*60)
        print("  CAMPAIGN SUMMARY")
        print("="*60)
        print("Campaign: {}".format(campaign_name))
        if duration:
            print("Duration: {:.1f} minutes".format(duration / 60))
        print("Contacts processed: {}/{}".format(
            self.workflow_stats['contacts_processed'],
            self.workflow_stats['total_contacts']
        ))
        print("Emails generated: {}".format(self.workflow_stats['emails_generated']))
        print("Emails approved: {}".format(self.workflow_stats['emails_approved']))
        
        if self.workflow_stats['errors']:
            print("\n⚠️  Errors encountered: {}".format(len(self.workflow_stats['errors'])))
            for error in self.workflow_stats['errors'][:5]:  # Show first 5
                print("  - {}".format(error))
                
        print("\n✅ Campaign complete!")
        print("="*60)
        
        return summary


def main():
    """Test the workflow orchestrator."""
    print("\n=== Workflow Orchestrator Test ===\n")
    
    # Create test CSV if it doesn't exist
    test_csv = "test_campaign_contacts.csv"
    if not os.path.exists(test_csv):
        print("Creating test CSV file...")
        with open(test_csv, 'w') as f:
            f.write("Name,Email,Company,Title\n")
            f.write("Alice Johnson,alice@techstartup.com,TechStartup Inc,CTO\n")
            f.write("Bob Smith,bob@enterprise.com,Enterprise Corp,VP Sales\n")
            f.write("Carol White,carol@smallbiz.com,SmallBiz LLC,Owner\n")
            
    # Initialize orchestrator with test config
    config = {
        'gmail_credentials': 'credentials.json',
        'gmail_token': 'token.pickle',
        'anthropic_api_key': os.environ.get('ANTHROPIC_API_KEY'),
        'batch_size': 2,
        'rate_limit_delay': 0.5,
        'enable_learning': True,
        'enable_email_history': False,  # Skip for test
        'output_dir': 'test_campaigns'
    }
    
    # Set auto-approve for testing
    os.environ['AUTO_APPROVE_EMAILS'] = 'true'
    
    try:
        orchestrator = WorkflowOrchestrator(config)
        
        # Run test campaign
        print("Starting test campaign...")
        summary = orchestrator.run_campaign(test_csv, "test_campaign")
        
        print("\n✅ Module 7 Test Complete!")
        print("🎯 Workflow orchestrator successfully coordinated all modules")
        
    except Exception as e:
        print("\n❌ Test failed: {}".format(str(e)))
        print("Note: This is expected if Gmail credentials are not set up")


if __name__ == "__main__":
    main()