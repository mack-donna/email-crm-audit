#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module 5: Human Review Interface
Streamlined command-line interface for reviewing and approving generated emails.
"""

import json
import os
import sys
import time
from datetime import datetime
import logging
try:
    # Python 3
    input = input
except NameError:
    # Python 2
    input = raw_input


class ReviewInterface:
    """
    Human review interface for email approval workflow.
    
    Features:
    - Clear presentation of contact context and email
    - Quick approve/edit/reject workflow
    - Batch processing with progress tracking
    - Export approved emails for sending
    """
    
    def __init__(self, log_level="INFO"):
        self.setup_logging(log_level)
        self.review_stats = {
            'total_reviewed': 0,
            'approved': 0,
            'edited': 0,
            'rejected': 0,
            'review_time_total': 0,
            'average_review_time': 0
        }
        
        # Session data
        self.current_session = {
            'start_time': datetime.now(),
            'emails_to_review': [],
            'approved_emails': [],
            'rejected_emails': [],
            'feedback_log': []
        }
        
    def setup_logging(self, level):
        """Configure logging."""
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format='%(asctime)s - ReviewInterface - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('review_session_{}.log'.format(
                    datetime.now().strftime("%Y%m%d_%H%M%S")
                )),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def start_review_session(self, generated_emails):
        """
        Start a new review session with generated emails.
        
        Args:
            generated_emails: List of email dicts from EmailGenerator
        """
        self.logger.info("Starting review session with {} emails".format(
            len(generated_emails)
        ))
        
        self.current_session['emails_to_review'] = generated_emails
        self.clear_screen()
        
        print("\n" + "="*60)
        print("  EMAIL REVIEW SESSION")
        print("="*60)
        print("\nEmails to review: {}".format(len(generated_emails)))
        print("Commands: [A]pprove, [E]dit, [R]eject, [S]kip, [Q]uit")
        print("="*60)
        
        # Review each email
        for idx, email_data in enumerate(generated_emails):
            if not self.review_single_email(idx, email_data):
                break  # User quit
                
        # Show session summary
        self.show_session_summary()
        
    def review_single_email(self, index, email_data):
        """
        Review a single email with full context.
        
        Args:
            index: Email index in batch
            email_data: Generated email with metadata
            
        Returns:
            bool: True to continue, False to quit
        """
        start_time = time.time()
        self.clear_screen()
        
        # Extract data
        contact = email_data['contact_context']['contact']
        research = email_data['contact_context'].get('research', {})
        email_content = email_data['email_content']
        metadata = email_data['metadata']
        
        # Display header
        print("\n" + "="*60)
        print("  EMAIL {} of {}".format(index + 1, len(self.current_session['emails_to_review'])))
        print("="*60)
        
        # Display contact info
        print("\nCONTACT INFORMATION:")
        print("-" * 30)
        print("Name: {}".format(contact.get('name', 'Unknown')))
        print("Company: {}".format(contact.get('company', 'Unknown')))
        print("Title: {}".format(contact.get('title', 'Not specified')))
        print("Email: {}".format(contact.get('email', 'Unknown')))
        
        # Display research context
        if research:
            print("\nRESEARCH CONTEXT:")
            print("-" * 30)
            if research.get('company_research', {}).get('description'):
                print("Company: {}".format(
                    research['company_research']['description'][:100] + '...'
                ))
            print("Research Quality: {:.1f}/5".format(
                research.get('research_quality_score', 0) * 5
            ))
            
        # Display email
        print("\nGENERATED EMAIL:")
        print("-" * 30)
        print(email_content)
        print("-" * 30)
        
        # Display metadata
        print("\nEMAIL METADATA:")
        print("Style: {}".format(metadata.get('style', 'Unknown')))
        print("Confidence: {:.0%}".format(metadata.get('confidence_score', 0)))
        print("Personalization: {}".format(
            ', '.join(metadata.get('personalization_points', []))
        ))
        
        # Get user action
        print("\n" + "="*60)
        action = self.get_user_action()
        
        # Process action
        review_time = time.time() - start_time
        self.review_stats['review_time_total'] += review_time
        self.review_stats['total_reviewed'] += 1
        
        if action == 'A':  # Approve
            self.approve_email(email_data)
            return True
            
        elif action == 'E':  # Edit
            edited_email = self.edit_email(email_data)
            if edited_email:
                self.approve_email(edited_email)
            return True
            
        elif action == 'R':  # Reject
            self.reject_email(email_data)
            return True
            
        elif action == 'S':  # Skip
            return True
            
        elif action == 'Q':  # Quit
            return False
            
        return True
        
    def get_user_action(self):
        """Get user action with validation."""
        valid_actions = ['A', 'E', 'R', 'S', 'Q']
        
        while True:
            action = input("\nAction [A/E/R/S/Q]: ").upper()
            
            if action in valid_actions:
                return action
            else:
                print("Invalid action. Please choose: A)pprove, E)dit, R)eject, S)kip, Q)uit")
                
    def approve_email(self, email_data):
        """Approve an email for sending."""
        self.logger.info("Email approved for: {}".format(
            email_data['contact_context']['contact'].get('name')
        ))
        
        self.review_stats['approved'] += 1
        email_data['review_status'] = 'approved'
        email_data['review_timestamp'] = datetime.now().isoformat()
        
        self.current_session['approved_emails'].append(email_data)
        
        print("\n✅ Email APPROVED")
        time.sleep(1)
        
    def edit_email(self, email_data):
        """Edit an email before approval."""
        print("\n" + "="*60)
        print("  EDIT EMAIL")
        print("="*60)
        print("\nCurrent email:")
        print("-" * 30)
        print(email_data['email_content'])
        print("-" * 30)
        
        print("\nEdit options:")
        print("1. Quick edit (line by line)")
        print("2. Full rewrite")
        print("3. Cancel edit")
        
        choice = input("\nChoice [1/2/3]: ")
        
        if choice == '1':
            edited_content = self.quick_edit(email_data['email_content'])
        elif choice == '2':
            edited_content = self.full_rewrite()
        else:
            return None
            
        if edited_content:
            self.review_stats['edited'] += 1
            email_data['email_content'] = edited_content
            email_data['was_edited'] = True
            email_data['edit_timestamp'] = datetime.now().isoformat()
            
            # Show edited version
            print("\nEDITED EMAIL:")
            print("-" * 30)
            print(edited_content)
            print("-" * 30)
            
            confirm = input("\nApprove edited version? [Y/N]: ").upper()
            if confirm == 'Y':
                return email_data
                
        return None
        
    def quick_edit(self, original_email):
        """Quick line-by-line edit."""
        lines = original_email.split('\n')
        edited_lines = []
        
        print("\nEdit each line (press Enter to keep, or type new text):")
        print("-" * 60)
        
        for i, line in enumerate(lines):
            print("\nLine {}: {}".format(i + 1, line))
            new_line = input("Edit: ")
            
            if new_line:
                edited_lines.append(new_line)
            else:
                edited_lines.append(line)
                
        return '\n'.join(edited_lines)
        
    def full_rewrite(self):
        """Full email rewrite."""
        print("\nEnter new email content (type 'END' on a new line when done):")
        print("-" * 60)
        
        lines = []
        while True:
            line = input()
            if line.upper() == 'END':
                break
            lines.append(line)
            
        return '\n'.join(lines) if lines else None
        
    def reject_email(self, email_data):
        """Reject an email with feedback."""
        self.logger.info("Email rejected for: {}".format(
            email_data['contact_context']['contact'].get('name')
        ))
        
        print("\nReason for rejection (optional):")
        feedback = input("> ")
        
        self.review_stats['rejected'] += 1
        email_data['review_status'] = 'rejected'
        email_data['rejection_reason'] = feedback
        email_data['review_timestamp'] = datetime.now().isoformat()
        
        self.current_session['rejected_emails'].append(email_data)
        self.current_session['feedback_log'].append({
            'contact': email_data['contact_context']['contact'].get('name'),
            'reason': feedback,
            'timestamp': datetime.now().isoformat()
        })
        
        print("\n❌ Email REJECTED")
        time.sleep(1)
        
    def show_session_summary(self):
        """Display session summary."""
        self.clear_screen()
        
        # Calculate statistics
        if self.review_stats['total_reviewed'] > 0:
            self.review_stats['average_review_time'] = (
                self.review_stats['review_time_total'] / 
                self.review_stats['total_reviewed']
            )
            
        session_duration = (datetime.now() - self.current_session['start_time']).total_seconds()
        
        print("\n" + "="*60)
        print("  SESSION SUMMARY")
        print("="*60)
        
        print("\nREVIEW STATISTICS:")
        print("-" * 30)
        print("Total reviewed: {}".format(self.review_stats['total_reviewed']))
        print("Approved: {} ({:.0%})".format(
            self.review_stats['approved'],
            self.review_stats['approved'] / max(self.review_stats['total_reviewed'], 1)
        ))
        print("Edited: {}".format(self.review_stats['edited']))
        print("Rejected: {}".format(self.review_stats['rejected']))
        
        print("\nTIME STATISTICS:")
        print("-" * 30)
        print("Session duration: {:.1f} minutes".format(session_duration / 60))
        print("Average review time: {:.1f} seconds".format(
            self.review_stats['average_review_time']
        ))
        print("Emails per hour: {:.0f}".format(
            (self.review_stats['total_reviewed'] / max(session_duration, 1)) * 3600
        ))
        
        # Export option
        if self.current_session['approved_emails']:
            print("\n" + "="*60)
            export = input("\nExport approved emails? [Y/N]: ").upper()
            
            if export == 'Y':
                self.export_approved_emails()
                
    def export_approved_emails(self):
        """Export approved emails to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = "approved_emails_{}.json".format(timestamp)
        
        export_data = {
            'session_info': {
                'start_time': self.current_session['start_time'].isoformat(),
                'total_reviewed': self.review_stats['total_reviewed'],
                'total_approved': len(self.current_session['approved_emails'])
            },
            'approved_emails': self.current_session['approved_emails']
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
                
            print("\n✅ Exported {} approved emails to: {}".format(
                len(self.current_session['approved_emails']),
                filename
            ))
            
            # Show sample for manual sending
            print("\nSAMPLE EMAIL FOR MANUAL SENDING:")
            print("-" * 60)
            if self.current_session['approved_emails']:
                first_email = self.current_session['approved_emails'][0]
                print("To: {}".format(
                    first_email['contact_context']['contact'].get('email')
                ))
                print("Subject: [Your subject line]")
                print("\n{}".format(first_email['email_content']))
                
        except Exception as e:
            self.logger.error("Error exporting emails: {}".format(str(e)))
            print("\n❌ Error exporting emails")
            
    def clear_screen(self):
        """Clear terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')
        
    def load_emails_for_review(self, filename):
        """Load generated emails from file for review."""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'generated_emails' in data:
                return data['generated_emails']
            else:
                self.logger.error("Invalid email data format")
                return []
                
        except Exception as e:
            self.logger.error("Error loading emails: {}".format(str(e)))
            return []


def main():
    """Test the review interface with sample data."""
    print("\n=== Human Review Interface Test ===\n")
    
    # Initialize interface
    interface = ReviewInterface()
    
    # Create sample generated emails
    sample_emails = [
        {
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
        },
        {
            'contact_context': {
                'contact': {
                    'name': 'Sarah Johnson',
                    'email': 'sarah@startup.io',
                    'company': 'StartupXYZ',
                    'title': 'CEO'
                },
                'research': {
                    'company_research': {
                        'description': 'Early-stage startup in fintech space'
                    },
                    'research_quality_score': 0.6
                }
            },
            'email_content': """Hi Sarah,

Quick question - are you currently looking for ways to scale your engineering team efficiently?

We specialize in helping fintech startups build robust infrastructure without breaking the bank.

Worth a quick chat?

Thanks,
[Your name]""",
            'metadata': {
                'style': 'brief_direct',
                'confidence_score': 0.75,
                'personalization_points': ['Used recipient name', 'Referenced industry']
            }
        }
    ]
    
    # Start review session
    print("Starting review session with {} sample emails...".format(len(sample_emails)))
    print("\nInstructions:")
    print("- Review each email and choose an action")
    print("- Try approving, editing, and rejecting emails")
    print("- Session summary will show at the end")
    
    input("\nPress Enter to start...")
    
    interface.start_review_session(sample_emails)
    
    print("\n✅ Module 5 Test Complete!")
    print("📋 Review interface is ready for production use")


if __name__ == "__main__":
    main()