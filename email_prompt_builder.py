"""
Email Prompt Builder

Extracted from EmailGenerator to follow Single Responsibility Principle.
Handles all prompt engineering logic for email generation.
"""

import json


class EmailPromptBuilder:
    """
    Builds comprehensive prompts for AI email generation.

    Separates prompt engineering concerns from the main EmailGenerator class.
    This class encapsulates all the logic for constructing prompts based on:
    - Contact context
    - Campaign settings
    - Email style preferences
    - LinkedIn data
    - Research findings
    """

    # Campaign goal mappings
    GOAL_MAPPING = {
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

    # Length preference mappings
    LENGTH_MAPPING = {
        'concise': '2-3 short paragraphs (100-150 words)',
        'medium': '3-4 paragraphs (150-200 words)',
        'detailed': '4-5 paragraphs with more detail (200-300 words)'
    }

    def __init__(self):
        """Initialize the prompt builder."""
        pass

    def build_generation_prompt(self, contact_context, email_style, campaign_settings=None):
        """
        Build a comprehensive prompt for email generation.

        Args:
            contact_context (dict): Contact information, research, and history
            email_style (str): Style of email to generate
            campaign_settings (dict): Campaign goal, tone, length, message

        Returns:
            str: Complete prompt for AI email generation
        """
        # Extract context components
        contact = contact_context.get('contact', {})
        email_history = contact_context.get('email_history', {})
        research = contact_context.get('research', {})
        linkedin_data = contact_context.get('linkedin_data', {})
        linkedin_context = contact_context.get('linkedin_context', {})

        # Extract campaign settings with defaults
        campaign_goal, campaign_tone, campaign_length, campaign_message = \
            self._extract_campaign_settings(campaign_settings)

        # Get goal-specific information
        goal_info = self.GOAL_MAPPING.get(campaign_goal, self.GOAL_MAPPING['first_meeting'])

        # Get length guide
        length_guide = self.LENGTH_MAPPING.get(campaign_length, self.LENGTH_MAPPING['medium'])

        # Build the complete prompt
        prompt = self._build_prompt_template(
            contact=contact,
            email_history=email_history,
            research=research,
            linkedin_context=linkedin_context,
            campaign_goal=campaign_goal,
            campaign_tone=campaign_tone,
            campaign_message=campaign_message,
            email_style=email_style,
            goal_info=goal_info,
            length_guide=length_guide
        )

        return prompt

    def _extract_campaign_settings(self, campaign_settings):
        """
        Extract campaign settings with defaults.

        Args:
            campaign_settings (dict): Campaign configuration

        Returns:
            tuple: (goal, tone, length, message)
        """
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

        return campaign_goal, campaign_tone, campaign_length, campaign_message

    def _build_prompt_template(self, contact, email_history, research, linkedin_context,
                               campaign_goal, campaign_tone, campaign_message, email_style,
                               goal_info, length_guide):
        """
        Build the complete prompt template with all context filled in.

        Args:
            All context variables needed for prompt construction

        Returns:
            str: Complete formatted prompt
        """
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

CRITICAL FACTUAL ACCURACY REQUIREMENTS:
- NEVER fabricate or invent previous conversations, meetings, or interactions that didn't happen
- NEVER reference specific dates, calls, or discussions unless they are documented in the interaction history
- NEVER claim "we previously discussed" or "our last conversation" unless there is actual evidence
- NEVER invent mutual connections, shared experiences, or past communications
- If there are 0 previous interactions or "None" last interaction, treat this as a completely cold outreach
- Only reference factual information provided in the research findings and LinkedIn insights
- When in doubt about a fact, do NOT include it - err on the side of honesty

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
            relationship=email_history.get('relationship_warmth', 'No prior relationship - this is cold outreach'),
            interaction_count=email_history.get('total_interactions', 0),
            last_interaction=email_history.get('last_interaction', 'None - no previous interactions recorded'),
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
