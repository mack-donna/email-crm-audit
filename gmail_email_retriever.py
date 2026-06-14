"""
Shared Gmail Email Retrieval Utility

Consolidates duplicate get_recent_emails() implementations from:
- email_crm_audit.py
- simplified_email_audit.py
- enhanced_email_extractor.py
- full_email_extraction.py
- refined_email_extraction.py
"""

from datetime import datetime, timedelta
import re


class GmailEmailRetriever:
    """
    Shared utility for retrieving and processing Gmail emails.

    Reduces code duplication by providing a single implementation
    of email retrieval logic used across multiple modules.
    """

    def __init__(self, gmail_service, user_email=None, logger=None):
        """
        Initialize the Gmail email retriever.

        Args:
            gmail_service: Authenticated Gmail API service object
            user_email: User's email address to filter out (optional)
            logger: Logger instance for debug/error logging (optional)
        """
        self.gmail_service = gmail_service
        self.user_email = user_email or 'stu@sentient-sf.com'
        self.logger = logger

    def get_recent_emails(self,
                         days_back=30,
                         max_results=500,
                         progress_interval=50,
                         query_filter=None,
                         exclude_domains=None):
        """
        Retrieve recent emails from Gmail and extract contact information.

        Args:
            days_back (int): Number of days to look back (default: 30)
            max_results (int): Maximum number of emails to retrieve (default: 500)
            progress_interval (int): How often to print progress (default: 50)
            query_filter (str): Additional Gmail query filter (default: None)
            exclude_domains (list): Additional domains to exclude (default: None)

        Returns:
            dict: Dictionary of email contacts with contact data
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            # Build Gmail query
            query = 'after:{}'.format(start_date.strftime("%Y/%m/%d"))
            if query_filter:
                query = '{} {}'.format(query, query_filter)

            self._log_info("Searching emails from {} to {}".format(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            ))

            # Get message list from Gmail API
            results = self.gmail_service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            self._log_info("Found {} emails to analyze".format(len(messages)))

            # Process emails and extract contacts
            email_contacts = {}

            for i, message in enumerate(messages):
                if i % progress_interval == 0:
                    self._log_info("Processing email {}/{}".format(i+1, len(messages)))

                try:
                    # Get full message details
                    msg = self.gmail_service.users().messages().get(
                        userId='me',
                        id=message['id']
                    ).execute()

                    # Extract contact information from this email
                    contacts = self._extract_contacts_from_message(
                        msg,
                        exclude_domains=exclude_domains
                    )

                    # Merge contacts into main dictionary
                    self._merge_contacts(email_contacts, contacts)

                except Exception as e:
                    self._log_error("Error processing message {}: {}".format(
                        message.get('id', 'unknown'), str(e)
                    ))
                    continue

            self._log_info("Extraction complete. Found {} unique contacts".format(
                len(email_contacts)
            ))

            return email_contacts

        except Exception as e:
            self._log_error("Error retrieving emails: {}".format(str(e)))
            return {}

    def _extract_contacts_from_message(self, msg, exclude_domains=None):
        """
        Extract contact information from a single Gmail message.

        Args:
            msg (dict): Gmail message object
            exclude_domains (list): Additional domains to exclude

        Returns:
            dict: Dictionary of contacts found in this message
        """
        headers = msg['payload'].get('headers', [])
        contacts = {}

        # Extract email headers
        subject = ""
        from_email = ""
        to_emails = []
        cc_emails = []
        date_header = ""

        for header in headers:
            name = header['name'].lower()
            value = header['value']

            if name == 'subject':
                subject = value
            elif name == 'from':
                from_email = value
            elif name == 'to':
                to_emails = value.split(',')
            elif name == 'cc':
                cc_emails = value.split(',')
            elif name == 'date':
                date_header = value

        # Process all email addresses found
        all_email_strings = [from_email] + to_emails + cc_emails

        for email_string in all_email_strings:
            email = self._extract_email_address(email_string)
            name = self._extract_name_from_email(email_string)

            # Filter out user's own email and non-business emails
            if not email or email == self.user_email:
                continue

            if not self._is_business_email(email, subject, exclude_domains):
                continue

            # Create or update contact record
            if email not in contacts:
                domain = email.split('@')[1] if '@' in email else ''
                company = self._extract_company_from_email(email)

                contacts[email] = {
                    'email': email,
                    'name': name or email.split('@')[0].title(),
                    'domain': domain,
                    'company': company,
                    'first_seen': date_header or datetime.now().strftime('%Y-%m-%d'),
                    'last_seen': date_header or datetime.now().strftime('%Y-%m-%d'),
                    'email_count': 1,
                    'subjects': [subject] if subject else []
                }
            else:
                # Update existing contact
                contacts[email]['email_count'] += 1
                contacts[email]['last_seen'] = date_header or datetime.now().strftime('%Y-%m-%d')
                if subject and subject not in contacts[email]['subjects']:
                    contacts[email]['subjects'].append(subject)

        return contacts

    def _merge_contacts(self, target, source):
        """
        Merge source contacts into target contacts dictionary.

        Args:
            target (dict): Target contacts dictionary to merge into
            source (dict): Source contacts dictionary to merge from
        """
        for email, contact_data in source.items():
            if email not in target:
                target[email] = contact_data
            else:
                # Merge data for existing contact
                target[email]['email_count'] += contact_data.get('email_count', 1)
                target[email]['last_seen'] = contact_data.get('last_seen', target[email]['last_seen'])

                # Merge subjects list
                for subject in contact_data.get('subjects', []):
                    if subject not in target[email]['subjects']:
                        target[email]['subjects'].append(subject)

    def _extract_email_address(self, email_string):
        """
        Extract clean email address from string like 'Name <email@domain.com>'.

        Args:
            email_string (str): Email string to parse

        Returns:
            str: Clean email address or empty string
        """
        if not email_string:
            return ""

        # Look for email in angle brackets
        match = re.search(r'<([^>]+)>', email_string)
        if match:
            return match.group(1).strip().lower()

        # Otherwise treat whole string as email
        email = email_string.strip().lower()

        # Validate it looks like an email
        if '@' in email and '.' in email:
            return email

        return ""

    def _extract_name_from_email(self, email_string):
        """
        Extract name from email string like 'John Doe <john@example.com>'.

        Args:
            email_string (str): Email string to parse

        Returns:
            str: Extracted name or empty string
        """
        if not email_string or '<' not in email_string:
            return ""

        # Extract name before angle bracket
        name = email_string.split('<')[0].strip()

        # Clean up quotes
        name = name.replace('"', '').replace("'", '')

        return name

    def _extract_company_from_email(self, email):
        """
        Extract company name from email domain.

        Args:
            email (str): Email address

        Returns:
            str: Company name derived from domain
        """
        if not email or '@' not in email:
            return "Unknown"

        domain = email.split('@')[1]

        # Remove common TLDs and convert to title case
        company = domain.split('.')[0]
        company = company.replace('-', ' ').replace('_', ' ')

        return company.title()

    def _is_business_email(self, email, subject="", exclude_domains=None):
        """
        Determine if email is a business contact (not automated/marketing).

        Args:
            email (str): Email address to check
            subject (str): Email subject line for context
            exclude_domains (list): Additional domains to exclude

        Returns:
            bool: True if business email, False otherwise
        """
        if not email:
            return False

        email_lower = email.lower()
        subject_lower = subject.lower() if subject else ""

        # Skip common automated email patterns
        automated_patterns = [
            'noreply', 'no-reply', 'donotreply', 'do-not-reply',
            'notifications', 'alerts', 'automated', 'mailer-daemon',
            'postmaster', 'bounce', 'calendar', 'marketing'
        ]

        for pattern in automated_patterns:
            if pattern in email_lower:
                return False

        # Skip marketing/newsletter subjects
        marketing_keywords = [
            'newsletter', 'unsubscribe', 'subscription',
            'promotional', 'sale', 'discount', 'offer'
        ]

        for keyword in marketing_keywords:
            if keyword in subject_lower:
                return False

        # Default exclude domains (service providers)
        default_exclude_domains = [
            'google.com', 'gmail.com', 'facebook.com', 'linkedin.com',
            'twitter.com', 'github.com', 'slack.com', 'notion.so',
            'atlassian.com', 'salesforce.com', 'hubspot.com',
            'mailchimp.com', 'sendgrid.com', 'postmarkapp.com',
            'anthropic.com', 'gusto.com', 'stripe.com', 'quickbooks',
            'mercury.com', 'ziptie.dev'
        ]

        # Merge with additional exclude domains
        all_exclude_domains = default_exclude_domains
        if exclude_domains:
            all_exclude_domains = default_exclude_domains + exclude_domains

        for domain in all_exclude_domains:
            if domain in email_lower:
                return False

        return True

    def _log_info(self, message):
        """Log info message using logger or print."""
        if self.logger:
            self.logger.info(message)
        else:
            print("🔍 {}".format(message))

    def _log_error(self, message):
        """Log error message using logger or print."""
        if self.logger:
            self.logger.error(message)
        else:
            print("❌ ERROR: {}".format(message))
