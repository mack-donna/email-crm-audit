#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module 1: CSV Contact Processing Foundation
Handles Salesforce CSV import, validation, and standardization for outreach automation.
"""

import csv
import json
import logging
import re
from datetime import datetime
import os
try:
    from typing import Dict, List, Optional, Tuple, Any
except ImportError:
    # Fallback for older Python versions
    pass

class ContactProcessor:
    """
    CSV Contact Processing with validation and learning-ready data structures.
    
    Required fields: Name, Email, Company
    Optional fields: Title, Phone, Last_Activity_Date, Lead_Source, etc.
    """
    
    def __init__(self, log_level="INFO"):
        self.setup_logging(log_level)
        self.processed_contacts = []
        self.validation_errors = []
        self.processing_stats = {
            'total_rows': 0,
            'valid_contacts': 0,
            'invalid_contacts': 0,
            'missing_required_fields': 0,
            'invalid_emails': 0,
            'duplicate_emails': 0,
            'processing_time': None
        }
        
    def setup_logging(self, level):
        """Configure comprehensive logging for debugging."""
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format='%(asctime)s - ContactProcessor - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('contact_processing_{}.log'.format(datetime.now().strftime("%Y%m%d_%H%M%S"))),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_csv(self, csv_path):
        """
        Load CSV with flexible field name matching.
        
        Args:
            csv_path: Path to Salesforce CSV export
            
        Returns:
            List of dictionaries with standardized column names
        """
        try:
            with open(csv_path, 'r') as csvfile:
                # Detect CSV format
                sample = csvfile.read(1024)
                csvfile.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                # Read CSV data
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                rows = list(reader)
                
            self.logger.info("Loaded CSV with {} rows and columns: {}".format(len(rows), list(rows[0].keys()) if rows else []))
            
            # Standardize column names
            rows = self._standardize_column_names(rows)
            
            self.processing_stats['total_rows'] = len(rows)
            return rows
            
        except IOError:
            self.logger.error("CSV file not found: {}".format(csv_path))
            raise
        except Exception as e:
            self.logger.error("Error loading CSV: {}".format(str(e)))
            raise
            
    def _standardize_column_names(self, rows):
        """
        Map various Salesforce field names to standardized format.
        """
        if not rows:
            return rows
            
        column_mapping = {
            # Name variations
            'full_name': 'name',
            'full name': 'name',
            'contact_name': 'name',
            'first_name': 'first_name',  # Keep separate if available
            'last_name': 'last_name',    # Keep separate if available
            
            # Email variations
            'email_address': 'email',
            'email_address__c': 'email',
            'contact_email': 'email',
            
            # Company variations
            'company': 'company',
            'account_name': 'company',
            'account name': 'company',
            'company_name': 'company',
            'organization': 'company',
            
            # Optional fields
            'title': 'title',
            'job_title': 'title',
            'role': 'title',
            'phone': 'phone',
            'phone_number': 'phone',
            'mobile': 'phone',
            'last_activity_date': 'last_activity_date',
            'last_activity': 'last_activity_date',
            'lead_source': 'lead_source',
            'source': 'lead_source'
        }
        
        # Standardize each row
        standardized_rows = []
        for row in rows:
            new_row = {}
            # Create mapping for actual columns (case insensitive)
            for col, value in row.items():
                col_lower = col.lower().strip()
                new_col = column_mapping.get(col_lower, col_lower)
                new_row[new_col] = value
                
            # Handle case where we have first_name + last_name but no name
            # Check both underscore and space versions
            if ('first_name' in new_row or 'first name' in new_row) and \
               ('last_name' in new_row or 'last name' in new_row) and \
               'name' not in new_row:
                fname = new_row.get('first_name', new_row.get('first name', '')).strip()
                lname = new_row.get('last_name', new_row.get('last name', '')).strip()
                new_row['name'] = (fname + ' ' + lname).strip()
                
            standardized_rows.append(new_row)
            
        if standardized_rows:
            self.logger.info("Standardized columns: {}".format(list(standardized_rows[0].keys())))
        return standardized_rows
        
    def validate_contact(self, contact_row):
        """
        Validate individual contact for required fields and data quality.
        
        Args:
            contact_row: Single contact row from DataFrame
            
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        required_fields = ['name', 'email', 'company']
        for field in required_fields:
            if field not in contact_row or not contact_row[field] or not str(contact_row[field]).strip():
                errors.append("Missing required field: {}".format(field))
                
        # Validate email format
        if 'email' in contact_row and contact_row['email']:
            if not self._is_valid_email(str(contact_row['email'])):
                errors.append("Invalid email format: {}".format(contact_row['email']))
                
        # Clean and validate name
        if 'name' in contact_row and contact_row['name']:
            name = str(contact_row['name']).strip()
            if len(name) < 2:
                errors.append("Name too short: {}".format(name))
            if not re.match(r'^[a-zA-Z\s\-\.\']+$', name):
                errors.append("Name contains invalid characters: {}".format(name))
                
        return len(errors) == 0, errors
        
    def _is_valid_email(self, email):
        """Validate email format using regex."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email.strip()) is not None
        
    def create_contact_object(self, contact_row):
        """
        Create learning-ready contact data structure.
        
        Args:
            contact_row: Validated contact row
            
        Returns:
            Standardized contact object with metadata
        """
        # Core contact information
        contact = {
            'id': self._generate_contact_id(contact_row),
            'basic_info': {
                'name': str(contact_row['name']).strip(),
                'email': str(contact_row['email']).strip().lower(),
                'company': str(contact_row['company']).strip(),
                'title': str(contact_row.get('title', '')).strip() if contact_row.get('title') else None,
                'phone': str(contact_row.get('phone', '')).strip() if contact_row.get('phone') else None
            },
            
            # Learning-ready structure for future AI enhancement
            'interaction_history': {
                'emails_sent': [],
                'emails_received': [], 
                'last_interaction_date': None,
                'relationship_warmth': 'cold',  # cold, warm, existing
                'interaction_count': 0
            },
            
            'research_findings': {
                'company_info': {},
                'role_details': {},
                'recent_activity': [],
                'mutual_connections': [],
                'research_quality_score': 0.0
            },
            
            'personalization_data': {
                'interests': [],
                'pain_points': [],
                'recent_achievements': [],
                'personalization_opportunities': []
            },
            
            'success_metrics': {
                'emails_sent': 0,
                'emails_opened': 0,
                'emails_responded': 0,
                'meetings_booked': 0,
                'conversion_rate': 0.0
            },
            
            'learning_metadata': {
                'successful_elements': [],
                'failed_approaches': [],
                'user_feedback': [],
                'improvement_suggestions': []
            },
            
            # Processing metadata
            'processing_info': {
                'created_date': datetime.now().isoformat(),
                'source_file': None,  # Will be set during processing
                'data_quality_score': self._calculate_data_quality(contact_row),
                'optional_fields_available': self._get_available_optional_fields(contact_row)
            }
        }
        
        # Add optional fields if available
        optional_fields = ['last_activity_date', 'lead_source']
        for field in optional_fields:
            if field in contact_row and contact_row[field]:
                contact['basic_info'][field] = str(contact_row[field]).strip()
                
        return contact
        
    def _generate_contact_id(self, contact_row):
        """Generate unique contact ID based on email."""
        email = str(contact_row['email']).strip().lower()
        # Use email as primary ID, but make it safe for filenames
        return re.sub(r'[^a-zA-Z0-9]', '_', email)
        
    def _calculate_data_quality(self, contact_row):
        """Calculate data quality score (0-1) based on available information."""
        score = 0.0
        total_possible = 0.0
        
        # Required fields (weight: 0.6)
        required_fields = ['name', 'email', 'company']
        for field in required_fields:
            total_possible += 0.2
            if field in contact_row and contact_row[field] and str(contact_row[field]).strip():
                score += 0.2
                
        # Optional valuable fields (weight: 0.4)
        optional_fields = ['title', 'phone', 'last_activity_date', 'lead_source']
        for field in optional_fields:
            total_possible += 0.1
            if field in contact_row and contact_row[field] and str(contact_row[field]).strip():
                score += 0.1
                
        return score / total_possible if total_possible > 0 else 0.0
        
    def _get_available_optional_fields(self, contact_row):
        """Return list of available optional fields for this contact."""
        optional_fields = ['title', 'phone', 'last_activity_date', 'lead_source']
        available = []
        for field in optional_fields:
            if field in contact_row and contact_row[field] and str(contact_row[field]).strip():
                available.append(field)
        return available
        
    def process_csv(self, csv_path):
        """
        Main processing function - load, validate, and create contact objects.
        
        Args:
            csv_path: Path to Salesforce CSV file
            
        Returns:
            Processing results with contacts and statistics
        """
        start_time = datetime.now()
        self.logger.info("Starting contact processing for: {}".format(csv_path))
        
        try:
            # Load CSV
            df = self.load_csv(csv_path)
            
            # Track duplicates
            seen_emails = set()
            
            # Process each contact
            for index, row in enumerate(df):
                self.logger.debug("Processing contact {}/{}".format(index + 1, len(df)))
                
                # Validate contact
                is_valid, errors = self.validate_contact(row)
                
                if not is_valid:
                    self.validation_errors.append({
                        'row_number': index + 1,
                        'errors': errors,
                        'data': row
                    })
                    self.processing_stats['invalid_contacts'] += 1
                    
                    # Log specific error types
                    if any('Missing required field' in error for error in errors):
                        self.processing_stats['missing_required_fields'] += 1
                    if any('Invalid email format' in error for error in errors):
                        self.processing_stats['invalid_emails'] += 1
                        
                    continue
                
                # Check for duplicate emails
                email = str(row['email']).strip().lower()
                if email in seen_emails:
                    self.logger.warning("Duplicate email found: {}".format(email))
                    self.processing_stats['duplicate_emails'] += 1
                    continue
                    
                seen_emails.add(email)
                
                # Create contact object
                contact = self.create_contact_object(row)
                contact['processing_info']['source_file'] = csv_path
                
                self.processed_contacts.append(contact)
                self.processing_stats['valid_contacts'] += 1
                
            # Calculate processing time
            end_time = datetime.now()
            self.processing_stats['processing_time'] = (end_time - start_time).total_seconds()
            
            self.logger.info("Processing completed: {} valid contacts, {} invalid contacts".format(
                           self.processing_stats['valid_contacts'], self.processing_stats['invalid_contacts']))
            
            return {
                'contacts': self.processed_contacts,
                'statistics': self.processing_stats,
                'validation_errors': self.validation_errors,
                'processing_metadata': {
                    'source_file': csv_path,
                    'processing_date': start_time.isoformat(),
                    'processor_version': '1.0',
                    'total_processing_time': self.processing_stats['processing_time']
                }
            }
            
        except Exception as e:
            self.logger.error("Critical error during processing: {}".format(str(e)))
            raise
            
    def save_results(self, results, output_path=None):
        """
        Save processing results to JSON file.
        
        Args:
            results: Processing results from process_csv()
            output_path: Optional custom output path
            
        Returns:
            Path to saved file
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = "processed_contacts_{}.json".format(timestamp)
            
        try:
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
                
            self.logger.info("Results saved to: {}".format(output_path))
            return output_path
            
        except Exception as e:
            self.logger.error("Error saving results: {}".format(str(e)))
            raise
            
    def generate_quality_report(self, results):
        """
        Generate human-readable quality report for debugging.
        """
        stats = results['statistics']
        errors = results['validation_errors']
        
        report = """
=== CONTACT PROCESSING QUALITY REPORT ===

SUMMARY:
- Total rows processed: {}
- Valid contacts: {}
- Invalid contacts: {}
- Success rate: {:.1f}%

VALIDATION ISSUES:
- Missing required fields: {}
- Invalid email formats: {}
- Duplicate emails: {}

PROCESSING PERFORMANCE:
- Processing time: {:.2f} seconds
- Contacts per second: {:.1f}

DATA QUALITY INSIGHTS:
""".format(
            stats['total_rows'],
            stats['valid_contacts'],
            stats['invalid_contacts'],
            (stats['valid_contacts'] / stats['total_rows'] * 100),
            stats['missing_required_fields'],
            stats['invalid_emails'],
            stats['duplicate_emails'],
            stats['processing_time'],
            (stats['valid_contacts'] / stats['processing_time'])
        )
        
        if results['contacts']:
            quality_scores = [c['processing_info']['data_quality_score'] for c in results['contacts']]
            avg_quality = sum(quality_scores) / len(quality_scores)
            report += "- Average data quality score: {:.2f}/1.0\n".format(avg_quality)
            
            # Optional fields availability
            optional_field_counts = {}
            for contact in results['contacts']:
                for field in contact['processing_info']['optional_fields_available']:
                    optional_field_counts[field] = optional_field_counts.get(field, 0) + 1
                    
            report += "- Optional field availability:\n"
            for field, count in optional_field_counts.items():
                percentage = (count / stats['valid_contacts']) * 100
                report += "  - {}: {}/{} ({:.1f}%)\n".format(field, count, stats['valid_contacts'], percentage)
        
        if errors:
            report += "\nFIRST 5 VALIDATION ERRORS:\n"
            for error in errors[:5]:
                report += "- Row {}: {}\n".format(error['row_number'], ', '.join(error['errors']))
                
        return report


def main():
    """Test the contact processor with sample data."""
    # Create sample CSV for testing
    sample_csv_path = "sample_contacts.csv"
    sample_data = """Name,Email,Company,Title,Phone
John Smith,john.smith@acmecorp.com,ACME Corporation,VP Sales,555-0123
Jane Doe,jane.doe@techstart.io,TechStart Inc,Marketing Director,
,invalid.email@,MissingName Corp,CEO,555-0456
Bob Johnson,bob@example.com,Example LLC,Developer,555-0789"""
    
    with open(sample_csv_path, 'w') as f:
        f.write(sample_data)
    
    # Test the processor
    processor = ContactProcessor()
    results = processor.process_csv(sample_csv_path)
    
    # Save results
    output_file = processor.save_results(results)
    
    # Generate and print report
    report = processor.generate_quality_report(results)
    print(report)
    
    print("\n✅ Module 1 Test Complete!")
    print("📁 Results saved to: {}".format(output_file))
    print("📊 Processed {} valid contacts".format(results['statistics']['valid_contacts']))


if __name__ == "__main__":
    main()