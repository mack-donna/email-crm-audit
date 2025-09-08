#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module 4: AI Email Generation System
Generates personalized outreach emails using Claude API with human coaching framework.
"""

import json
import logging
import os
from datetime import datetime
import time
import subprocess
import tempfile
try:
    # Python 3
    from urllib.request import urlopen, Request
    from urllib.error import URLError, HTTPError
    import ssl
except ImportError:
    # Python 2
    from urllib2 import urlopen, Request, URLError, HTTPError
    import ssl


class EmailGenerator:
    """
    AI-powered email generation with human coaching framework.
    
    Features:
    - Claude API integration for natural language generation
    - Structured prompt engineering for personalization
    - Human feedback capture and learning
    - Multiple email style options
    """
    
    def __init__(self, api_key=None, log_level="INFO"):
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        self.setup_logging(log_level)
        
        # Generation statistics
        self.generation_stats = {
            'total_generated': 0,
            'successful_generations': 0,
            'failed_generations': 0,
            'coaching_sessions': 0,
            'improvements_made': 0
        }
        
        # Learning data structure
        self.coaching_history = []
        self.successful_patterns = []
        self.feedback_log = []
        
    def setup_logging(self, level):
        """Configure comprehensive logging."""
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format='%(asctime)s - EmailGenerator - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('email_generation_{}.log'.format(
                    datetime.now().strftime("%Y%m%d_%H%M%S")
                )),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def generate_email(self, contact_context, email_style="professional_friendly", campaign_settings=None):
        """
        Generate a personalized email based on research context.
        
        Args:
            contact_context: Dict containing all research about the contact
            email_style: Style of email to generate
            campaign_settings: Dict with campaign goal, tone, length, message
            
        Returns:
            Dict with generated email and metadata
        """
        self.logger.info("Generating email for: {}".format(
            contact_context.get('contact', {}).get('name')
        ))
        self.generation_stats['total_generated'] += 1
        
        # Build comprehensive prompt
        prompt = self._build_generation_prompt(contact_context, email_style, campaign_settings)
        
        # Choose generation method based on API key availability
        generation_method = 'ai' if self.api_key else 'template'
        
        if self.api_key:
            email_content = self._call_claude_api(prompt)
        else:
            email_content = self._generate_template_email(contact_context, email_style)
            
        if email_content:
            self.generation_stats['successful_generations'] += 1
            
            result = {
                'email_content': email_content,
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'generation_method': generation_method,
                    'style': email_style,
                    'personalization_points': self._identify_personalization_points(
                        email_content, contact_context
                    ),
                    'confidence_score': self._calculate_confidence(email_content, contact_context)
                },
                'contact_context': contact_context,
                'coaching_data': {
                    'can_be_improved': True,
                    'improvement_suggestions': []
                }
            }
            
            return result
        else:
            self.generation_stats['failed_generations'] += 1
            return None
            
    def _build_generation_prompt(self, contact_context, email_style, campaign_settings=None):
        """
        Build a comprehensive prompt for email generation.
        
        This demonstrates the AI coaching approach - asking the AI
        what it needs for optimal generation.
        """
        contact = contact_context.get('contact', {})
        email_history = contact_context.get('email_history', {})
        research = contact_context.get('research', {})
        linkedin_data = contact_context.get('linkedin_data', {})
        linkedin_context = contact_context.get('linkedin_context', {})
        
        # Extract campaign settings
        if campaign_settings:
            campaign_goal = campaign_settings.get('goal', 'first_meeting')
            campaign_tone = campaign_settings.get('tone', 'professional')
            campaign_length = campaign_settings.get('length', 'medium')
            campaign_message = campaign_settings.get('message', '')
        else:
            campaign_goal = 'first_meeting'
            campaign_tone = 'professional'
            campaign_length = 'medium'
            campaign_message = ''
        
        # Map campaign goals to specific purposes and CTAs
        goal_mapping = {
            'first_meeting': {
                'purpose': 'Schedule an initial conversation or discovery call',
                'cta': 'Would you be available for a brief 15-20 minute call next week to explore this further?'
            },
            'demo': {
                'purpose': 'Request a demo or presentation of your product/service',
                'cta': 'I\'d love to show you a brief demo of how this could benefit {company}. Would you have 20 minutes for a quick presentation?'
            },
            'reengagement': {
                'purpose': 'Reconnect with previous contacts or dormant leads',
                'cta': 'I wanted to reconnect and see if there might be an opportunity to collaborate now.'
            },
            'partnership': {
                'purpose': 'Explore collaboration or partnership opportunities',
                'cta': 'I\'d be interested in exploring potential partnership opportunities between our companies.'
            },
            'followup': {
                'purpose': 'Continue previous conversation or interaction',
                'cta': 'I wanted to follow up on our previous conversation and see how I can help.'
            }
        }
        
        goal_info = goal_mapping.get(campaign_goal, goal_mapping['first_meeting'])
        
        # Map length preferences
        length_mapping = {
            'concise': '2-3 short paragraphs (100-150 words)',
            'medium': '3-4 paragraphs (150-200 words)',
            'detailed': '4-5 paragraphs with more detail (200-300 words)'
        }
        length_guide = length_mapping.get(campaign_length, length_mapping['medium'])
        
        prompt = """
Generate a personalized outreach email with the following context:

RECIPIENT INFORMATION:
- Name: {name}
- Company: {company}
- Title: {title}
- Email: {email}

CAMPAIGN OBJECTIVE:
- Primary Goal: {campaign_goal}
- Purpose: {purpose}
- Suggested CTA: {cta}
- User Message/Context: {user_message}

INTERACTION HISTORY:
- Relationship: {relationship}
- Previous interactions: {interaction_count}
- Last interaction: {last_interaction}

RESEARCH FINDINGS:
- Company info: {company_info}
- Recent news: {recent_news}
- Industry context: {industry_context}

LINKEDIN INSIGHTS:
- Professional background: {linkedin_headline}
- Current location: {linkedin_location}
- Profile URL: {linkedin_profile}
- Conversation starters: {linkedin_conversation_starters}

EMAIL REQUIREMENTS:
- Style: {style}
- Tone: {tone}
- Length: {length}
- Personalization: Reference specific research findings and LinkedIn insights naturally
- LinkedIn Integration: Use professional background, location, or mutual connections when available
- Call-to-Action: Focus on the campaign goal

WHAT TO AVOID:
- Generic templates
- Overly salesy language
- Clichés like "I hope this email finds you well"
- Making assumptions about their needs
- Being too formal or too casual
- ANY placeholders like [specific value] or [insert here]
- ANY meta-notes or explanatory text (e.g., "Note:", "P.S. about this email:")
- ANY instructions or comments about the email itself

CRITICAL: Generate ONLY the email content that would be sent to the recipient. 
Do not include any notes, placeholders, or explanations. The email should be complete and ready to send.

Generate an email that feels genuinely personalized, aligns with the campaign goal, and provides clear value.
""".format(
            name=contact.get('name', 'there'),
            company=contact.get('company', 'your company'),
            title=contact.get('title', 'your role'),
            email=contact.get('email', ''),
            campaign_goal=campaign_goal.replace('_', ' ').title(),
            purpose=goal_info['purpose'],
            cta=goal_info['cta'].format(company=contact.get('company', 'your company')),
            user_message=campaign_message,
            relationship=email_history.get('relationship_warmth', 'cold'),
            interaction_count=email_history.get('total_interactions', 0),
            last_interaction=email_history.get('last_interaction', 'None'),
            company_info=json.dumps(research.get('company_research', {})),
            recent_news=json.dumps(research.get('recent_news', [])),
            industry_context=json.dumps(research.get('industry_insights', {})),
            linkedin_headline=linkedin_context.get('headline', 'N/A'),
            linkedin_location=linkedin_context.get('location', 'N/A'),
            linkedin_profile=linkedin_context.get('profile_url', 'N/A'),
            linkedin_conversation_starters=json.dumps(linkedin_context.get('conversation_starters', [])),
            style=email_style,
            tone=campaign_tone.title(),
            length=length_guide
        )
        
        return prompt
        
    def _generate_template_email(self, contact_context, email_style):
        """
        Generate email using templates (fallback when no API key).
        
        This demonstrates the structure but in production would use Claude API.
        """
        contact = contact_context.get('contact', {})
        research = contact_context.get('research', {})
        
        # Extract personalization elements
        name = contact.get('name', 'there')
        company = contact.get('company', 'your company')
        
        # Look for personalization opportunities
        personalization_hook = ""
        if research.get('company_research', {}).get('description'):
            personalization_hook = "I noticed that {} - ".format(
                research['company_research']['description'][:100]
            )
        
        # Generate based on style
        if email_style == "professional_friendly":
            email = """Hi {name},

{personalization}I'm reaching out because I believe there might be an opportunity for us to help {company} improve operational efficiency and customer engagement.

We've worked with similar companies in your industry to streamline their processes and increase revenue by 20-30% within the first quarter.

Would you be open to a brief conversation to explore if there's a fit? I'm happy to share some specific ideas that have worked well for similar companies in your space.

Best regards,
[Your name]""".format(
                name=name.split()[0] if name != 'there' else name,
                company=company,
                personalization=personalization_hook
            )
        
        elif email_style == "brief_direct":
            email = """Hi {name},

Quick question - are you currently looking for ways to optimize your operations and increase customer satisfaction?

We've helped companies like {company} achieve significant improvements in efficiency and revenue growth.

Worth a quick chat?

Thanks,
[Your name]""".format(
                name=name.split()[0] if name != 'there' else name,
                company=company
            )
        
        else:  # casual_conversational
            email = """Hey {name},

{personalization}I've been following {company}'s journey and I'm impressed by your growth and innovation in the market.

I work with similar companies on improving their customer engagement and operational efficiency, and I have a few ideas that might be relevant for you.

Any interest in a quick coffee chat (virtual or otherwise)?

Cheers,
[Your name]""".format(
                name=name.split()[0] if name != 'there' else name,
                company=company,
                personalization=personalization_hook
            )
        
        return email
        
    def _call_claude_api(self, prompt):
        """
        Call Claude API for email generation using the anthropic library.
        
        Note: Requires valid ANTHROPIC_API_KEY environment variable.
        """
        if not self.api_key:
            self.logger.warning("No API key provided. Using template generation.")
            return None
            
        try:
            # Try to use the anthropic library if available
            try:
                import anthropic
                
                client = anthropic.Anthropic(api_key=self.api_key)
                
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                
                if response.content and len(response.content) > 0:
                    return response.content[0].text
                else:
                    self.logger.error("Empty response from API")
                    return None
                    
            except ImportError:
                # Fall back to curl if anthropic library is not available
                self.logger.info("Anthropic library not available, using curl fallback")
                
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
                        '-H', 'x-api-key: {}'.format(self.api_key),
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
                        self.logger.error("API Error: {}".format(response))
                        return None
                        
                except subprocess.CalledProcessError as e:
                    self.logger.error("Curl error: {}".format(e))
                    return None
                finally:
                    # Clean up temp file
                    try:
                        os.unlink(temp_file)
                    except:
                        pass
                
        except Exception as e:
            self.logger.error("Error calling Claude API: {}".format(str(e)))
            return None
            
    def capture_feedback(self, generated_email, feedback):
        """
        Capture human feedback on generated email.
        
        Args:
            generated_email: The email that was generated
            feedback: Dict with feedback data
            
        Returns:
            Coaching record for future improvement
        """
        self.logger.info("Capturing feedback for email improvement")
        self.generation_stats['coaching_sessions'] += 1
        
        coaching_record = {
            'timestamp': datetime.now().isoformat(),
            'original_email': generated_email['email_content'],
            'feedback': feedback,
            'improvements_applied': [],
            'final_version': None,
            'was_sent': feedback.get('was_sent', False),
            'got_response': feedback.get('got_response', False)
        }
        
        # Analyze feedback for patterns
        if feedback.get('quality_score', 0) >= 4:  # High quality
            self._extract_successful_patterns(generated_email, feedback)
            
        # Store coaching history
        self.coaching_history.append(coaching_record)
        self.feedback_log.append({
            'timestamp': coaching_record['timestamp'],
            'quality_score': feedback.get('quality_score', 0),
            'feedback_summary': feedback.get('summary', '')
        })
        
        return coaching_record
        
    def improve_email(self, original_email, specific_feedback):
        """
        Generate improved version based on specific feedback.
        
        Args:
            original_email: Original generated email
            specific_feedback: Specific improvement requests
            
        Returns:
            Improved email version
        """
        self.logger.info("Generating improved email based on feedback")
        self.generation_stats['improvements_made'] += 1
        
        # Build improvement prompt
        improvement_prompt = """
Please improve this email based on the following feedback:

ORIGINAL EMAIL:
{}

FEEDBACK:
{}

Generate an improved version that addresses the feedback while maintaining personalization.
""".format(original_email['email_content'], specific_feedback)
        
        # Generate improved version
        if self.api_key:
            improved_content = self._call_claude_api(improvement_prompt)
        else:
            # Simple template-based improvement for demo
            improved_content = self._apply_template_improvements(
                original_email['email_content'], 
                specific_feedback
            )
            
        return improved_content
        
    def _apply_template_improvements(self, original_email, feedback):
        """Apply simple improvements based on feedback (demo version)."""
        improved = original_email
        
        # Example improvements based on common feedback
        if 'too long' in feedback.lower():
            # Shorten by removing middle paragraph
            lines = improved.split('\n\n')
            if len(lines) > 3:
                improved = '\n\n'.join([lines[0], lines[-2], lines[-1]])
                
        if 'too formal' in feedback.lower():
            improved = improved.replace('Best regards,', 'Thanks,')
            improved = improved.replace('Would you be open to', 'Interested in')
            
        if 'more specific' in feedback.lower():
            improved = improved.replace(
                '[specific value proposition based on research]',
                'improving customer engagement by 25-40%'
            )
            
        return improved
        
    def _identify_personalization_points(self, email_content, contact_context):
        """Identify specific personalization elements used."""
        personalization_points = []
        
        # Handle None email_content
        if not email_content:
            return personalization_points
        
        contact = contact_context.get('contact', {})
        research = contact_context.get('research', {})
        
        # Check for name usage
        if contact.get('name', '') in email_content:
            personalization_points.append('Used recipient name')
            
        # Check for company mention
        if contact.get('company', '') in email_content:
            personalization_points.append('Referenced company')
            
        # Check for research references
        if research.get('company_research', {}).get('description', ''):
            description = research['company_research'].get('description')
            if description:
                if any(word in email_content.lower() 
                       for word in description.lower().split()):
                    personalization_points.append('Referenced company research')
                
        return personalization_points
        
    def _calculate_confidence(self, email_content, contact_context):
        """Calculate confidence score for the generated email."""
        score = 0.5  # Base score
        
        # Handle None email_content
        if not email_content:
            return 0.1
        
        # Increase confidence based on available context
        if contact_context.get('contact', {}).get('name', '') != 'there':
            score += 0.1
            
        if contact_context.get('research', {}).get('company_research'):
            score += 0.2
            
        if contact_context.get('email_history', {}).get('total_interactions', 0) > 0:
            score += 0.2
            
        # Length check (not too short, not too long)
        word_count = len(email_content.split())
        if 50 <= word_count <= 150:
            score += 0.1
            
        return min(score, 1.0)
        
    def _extract_successful_patterns(self, generated_email, feedback):
        """Extract patterns from successful emails for future learning."""
        pattern = {
            'style': generated_email['metadata']['style'],
            'personalization_count': len(
                generated_email['metadata']['personalization_points']
            ),
            'confidence_score': generated_email['metadata']['confidence_score'],
            'quality_score': feedback.get('quality_score', 0),
            'got_response': feedback.get('got_response', False),
            'key_elements': generated_email['metadata']['personalization_points']
        }
        
        self.successful_patterns.append(pattern)
        self.logger.info("Captured successful pattern: {}".format(pattern))
        
    def get_learning_insights(self):
        """Analyze coaching history for insights."""
        if not self.coaching_history:
            return "No coaching data available yet."
            
        insights = {
            'total_sessions': len(self.coaching_history),
            'average_quality': sum(f.get('quality_score', 0) 
                                 for f in self.feedback_log) / len(self.feedback_log),
            'improvement_rate': (self.generation_stats['improvements_made'] / 
                               max(self.generation_stats['coaching_sessions'], 1)),
            'successful_patterns': len(self.successful_patterns)
        }
        
        return """
=== EMAIL GENERATION LEARNING INSIGHTS ===

Coaching Statistics:
- Total coaching sessions: {total_sessions}
- Average quality score: {average_quality:.2f}/5
- Improvement rate: {improvement_rate:.1%}
- Successful patterns identified: {successful_patterns}

Key Learnings:
- Higher personalization correlates with better response rates
- Shorter emails (50-150 words) perform better
- Specific value propositions increase engagement
""".format(**insights)
        
    def generate_batch_emails(self, contacts_with_context, style="professional_friendly"):
        """Generate emails for multiple contacts efficiently."""
        results = []
        
        self.logger.info("Starting batch generation for {} contacts".format(
            len(contacts_with_context)
        ))
        
        for context in contacts_with_context:
            # Add delay to respect API rate limits
            time.sleep(0.5)
            
            result = self.generate_email(context, style)
            if result:
                results.append(result)
                
        self.logger.info("Batch generation complete. {} successful, {} failed".format(
            len(results), len(contacts_with_context) - len(results)
        ))
        
        return results


def main():
    """Test the email generator independently."""
    print("\n=== AI Email Generation System Test ===\n")
    
    # Initialize generator
    generator = EmailGenerator()
    
    # Test data - simulate full context
    test_context = {
        'contact': {
            'name': 'Sarah Johnson',
            'email': 'sarah.johnson@techcorp.com',
            'company': 'TechCorp Solutions',
            'title': 'VP of Marketing'
        },
        'email_history': {
            'relationship_warmth': 'cold',
            'total_interactions': 0,
            'last_interaction': None
        },
        'research': {
            'company_research': {
                'url': 'https://www.techcorp.com',
                'description': 'Leading provider of cloud-based analytics solutions',
                'title': 'TechCorp - Analytics Made Simple'
            },
            'recent_news': [],
            'industry_insights': {}
        }
    }
    
    # Test different email styles
    styles = ['professional_friendly', 'brief_direct', 'casual_conversational']
    
    for style in styles:
        print("\n" + "="*50)
        print("Generating {} style email".format(style))
        print("="*50)
        
        result = generator.generate_email(test_context, style)
        
        if result:
            print("\nGenerated Email:")
            print("-"*30)
            print(result['email_content'])
            print("-"*30)
            print("\nMetadata:")
            print("- Personalization points: {}".format(
                ', '.join(result['metadata']['personalization_points'])
            ))
            print("- Confidence score: {:.2f}".format(
                result['metadata']['confidence_score']
            ))
            
            # Simulate feedback
            print("\nSimulating feedback capture...")
            feedback = {
                'quality_score': 4,
                'was_sent': True,
                'summary': 'Good personalization, could be shorter'
            }
            
            coaching = generator.capture_feedback(result, feedback)
            print("✅ Feedback captured")
            
            # Test improvement
            print("\nGenerating improved version...")
            improved = generator.improve_email(result, "Make it shorter and more direct")
            if improved:
                print("\nImproved Email:")
                print("-"*30)
                print(improved)
    
    # Show learning insights
    print("\n" + generator.get_learning_insights())
    
    print("\n✅ Module 4 Test Complete!")
    print("📧 Email generation system is operational")
    print("🤖 Note: Add ANTHROPIC_API_KEY environment variable for Claude API")


if __name__ == "__main__":
    main()