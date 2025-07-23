#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module 6: Learning Engine
Analyzes patterns, tracks success metrics, and continuously improves email generation.
"""

import json
import os
import logging
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re


class LearningEngine:
    """
    Learning system that improves email generation based on feedback and outcomes.
    
    Features:
    - Pattern recognition from successful emails
    - Success metric tracking and analysis
    - Personalization effectiveness measurement
    - Continuous improvement recommendations
    """
    
    def __init__(self, data_dir="learning_data", log_level="INFO"):
        self.data_dir = data_dir
        self.ensure_data_directory()
        self.setup_logging(log_level)
        
        # Learning data structures
        self.success_patterns = []
        self.response_data = []
        self.personalization_effectiveness = defaultdict(list)
        self.style_performance = defaultdict(lambda: {'sent': 0, 'responded': 0})
        
        # Load existing learning data
        self.load_learning_data()
        
    def ensure_data_directory(self):
        """Create data directory if it doesn't exist."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
    def setup_logging(self, level):
        """Configure logging."""
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format='%(asctime)s - LearningEngine - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('learning_engine_{}.log'.format(
                    datetime.now().strftime("%Y%m%d_%H%M%S")
                )),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def record_email_outcome(self, email_data, outcome_data):
        """
        Record the outcome of a sent email for learning.
        
        Args:
            email_data: Original email data with context
            outcome_data: Dict with outcome information
                - was_sent: bool
                - got_response: bool
                - response_time_hours: float (optional)
                - response_sentiment: str (optional)
                - led_to_meeting: bool (optional)
        """
        self.logger.info("Recording outcome for email to: {}".format(
            email_data['contact_context']['contact'].get('name')
        ))
        
        # Create learning record
        learning_record = {
            'timestamp': datetime.now().isoformat(),
            'contact_info': {
                'name': email_data['contact_context']['contact'].get('name'),
                'company': email_data['contact_context']['contact'].get('company'),
                'title': email_data['contact_context']['contact'].get('title')
            },
            'email_metadata': email_data['metadata'],
            'personalization_points': email_data['metadata'].get('personalization_points', []),
            'research_quality': email_data['contact_context'].get('research', {}).get('research_quality_score', 0),
            'outcome': outcome_data,
            'email_length': len(email_data['email_content'].split()),
            'email_style': email_data['metadata'].get('style', 'unknown')
        }
        
        # Update performance tracking
        self._update_performance_metrics(learning_record)
        
        # Extract successful patterns if positive outcome
        if outcome_data.get('got_response'):
            self._extract_success_patterns(email_data, learning_record)
            
        # Save to persistent storage
        self._save_learning_record(learning_record)
        
        return learning_record
        
    def _update_performance_metrics(self, learning_record):
        """Update performance tracking metrics."""
        style = learning_record['email_style']
        
        # Track style performance
        if learning_record['outcome'].get('was_sent'):
            self.style_performance[style]['sent'] += 1
            
        if learning_record['outcome'].get('got_response'):
            self.style_performance[style]['responded'] += 1
            
        # Track personalization effectiveness
        personalization_count = len(learning_record['personalization_points'])
        success = learning_record['outcome'].get('got_response', False)
        
        self.personalization_effectiveness[personalization_count].append(success)
        
    def _extract_success_patterns(self, email_data, learning_record):
        """Extract patterns from successful emails."""
        pattern = {
            'timestamp': learning_record['timestamp'],
            'style': learning_record['email_style'],
            'personalization_count': len(learning_record['personalization_points']),
            'personalization_types': learning_record['personalization_points'],
            'email_length': learning_record['email_length'],
            'research_quality': learning_record['research_quality'],
            'contact_title_level': self._classify_title_level(
                learning_record['contact_info'].get('title', '')
            ),
            'response_time_hours': learning_record['outcome'].get('response_time_hours'),
            'led_to_meeting': learning_record['outcome'].get('led_to_meeting', False)
        }
        
        self.success_patterns.append(pattern)
        self.logger.info("Extracted success pattern: {}".format(pattern))
        
    def _classify_title_level(self, title):
        """Classify contact title into levels."""
        title_lower = title.lower()
        
        if any(exec_title in title_lower for exec_title in ['ceo', 'cto', 'cfo', 'president', 'founder']):
            return 'c_level'
        elif any(vp_title in title_lower for vp_title in ['vp', 'vice president', 'director']):
            return 'vp_director'
        elif any(mgr_title in title_lower for mgr_title in ['manager', 'lead', 'head']):
            return 'manager'
        else:
            return 'individual_contributor'
            
    def analyze_performance(self):
        """
        Analyze overall system performance and generate insights.
        
        Returns:
            Dict with performance analysis and recommendations
        """
        self.logger.info("Analyzing system performance")
        
        analysis = {
            'summary_statistics': self._calculate_summary_stats(),
            'style_analysis': self._analyze_style_performance(),
            'personalization_analysis': self._analyze_personalization_effectiveness(),
            'optimal_patterns': self._identify_optimal_patterns(),
            'recommendations': self._generate_recommendations()
        }
        
        return analysis
        
    def _calculate_summary_stats(self):
        """Calculate summary statistics."""
        total_sent = sum(style['sent'] for style in self.style_performance.values())
        total_responses = sum(style['responded'] for style in self.style_performance.values())
        
        return {
            'total_emails_tracked': total_sent,
            'total_responses': total_responses,
            'overall_response_rate': (total_responses / max(total_sent, 1)),
            'patterns_identified': len(self.success_patterns)
        }
        
    def _analyze_style_performance(self):
        """Analyze performance by email style."""
        style_analysis = {}
        
        for style, metrics in self.style_performance.items():
            if metrics['sent'] > 0:
                style_analysis[style] = {
                    'sent': metrics['sent'],
                    'responses': metrics['responded'],
                    'response_rate': metrics['responded'] / metrics['sent']
                }
                
        # Find best performing style
        if style_analysis:
            best_style = max(style_analysis.items(), 
                           key=lambda x: x[1]['response_rate'])
            style_analysis['best_performing'] = best_style[0]
            
        return style_analysis
        
    def _analyze_personalization_effectiveness(self):
        """Analyze effectiveness of personalization."""
        personalization_analysis = {}
        
        for count, outcomes in self.personalization_effectiveness.items():
            if outcomes:
                success_rate = sum(outcomes) / len(outcomes)
                personalization_analysis[count] = {
                    'emails_sent': len(outcomes),
                    'success_rate': success_rate
                }
                
        # Find optimal personalization level
        if personalization_analysis:
            optimal_count = max(personalization_analysis.items(),
                              key=lambda x: x[1]['success_rate'])
            personalization_analysis['optimal_count'] = optimal_count[0]
            
        return personalization_analysis
        
    def _identify_optimal_patterns(self):
        """Identify the most successful patterns."""
        if not self.success_patterns:
            return {}
            
        # Analyze common characteristics of successful emails
        optimal_patterns = {
            'average_email_length': sum(p['email_length'] for p in self.success_patterns) / len(self.success_patterns),
            'most_effective_personalizations': self._get_most_effective_personalizations(),
            'best_title_levels': self._get_best_title_levels(),
            'optimal_research_quality': sum(p['research_quality'] for p in self.success_patterns) / len(self.success_patterns)
        }
        
        # Quick response patterns
        quick_responses = [p for p in self.success_patterns 
                          if p.get('response_time_hours') and p['response_time_hours'] < 24]
        if quick_responses:
            optimal_patterns['quick_response_characteristics'] = {
                'average_length': sum(p['email_length'] for p in quick_responses) / len(quick_responses),
                'common_style': Counter(p['style'] for p in quick_responses).most_common(1)[0][0]
            }
            
        return optimal_patterns
        
    def _get_most_effective_personalizations(self):
        """Get most effective personalization types."""
        all_personalizations = []
        for pattern in self.success_patterns:
            all_personalizations.extend(pattern['personalization_types'])
            
        if all_personalizations:
            return Counter(all_personalizations).most_common(3)
        return []
        
    def _get_best_title_levels(self):
        """Get title levels with best response rates."""
        title_performance = defaultdict(lambda: {'count': 0, 'meetings': 0})
        
        for pattern in self.success_patterns:
            title_level = pattern['contact_title_level']
            title_performance[title_level]['count'] += 1
            if pattern.get('led_to_meeting'):
                title_performance[title_level]['meetings'] += 1
                
        # Calculate meeting rates
        title_analysis = {}
        for level, metrics in title_performance.items():
            title_analysis[level] = {
                'responses': metrics['count'],
                'meeting_rate': metrics['meetings'] / max(metrics['count'], 1)
            }
            
        return title_analysis
        
    def _generate_recommendations(self):
        """Generate actionable recommendations."""
        recommendations = []
        
        # Style recommendations
        style_perf = self._analyze_style_performance()
        if style_perf and 'best_performing' in style_perf:
            recommendations.append(
                "Use '{}' style for highest response rate ({:.0%})".format(
                    style_perf['best_performing'],
                    style_perf[style_perf['best_performing']]['response_rate']
                )
            )
            
        # Personalization recommendations
        pers_analysis = self._analyze_personalization_effectiveness()
        if pers_analysis and 'optimal_count' in pers_analysis:
            recommendations.append(
                "Include {} personalization points for best results".format(
                    pers_analysis['optimal_count']
                )
            )
            
        # Length recommendations
        if self.success_patterns:
            avg_length = sum(p['email_length'] for p in self.success_patterns) / len(self.success_patterns)
            recommendations.append(
                "Keep emails around {} words for optimal engagement".format(int(avg_length))
            )
            
        # Title-specific recommendations
        title_analysis = self._get_best_title_levels()
        if title_analysis:
            best_title = max(title_analysis.items(), 
                           key=lambda x: x[1]['meeting_rate'])
            if best_title[1]['meeting_rate'] > 0:
                recommendations.append(
                    "Focus on {} for highest meeting conversion rate".format(
                        best_title[0].replace('_', ' ')
                    )
                )
                
        return recommendations
        
    def get_contact_recommendations(self, contact_info):
        """
        Get specific recommendations for a contact based on learning.
        
        Args:
            contact_info: Contact information dict
            
        Returns:
            Dict with personalized recommendations
        """
        title_level = self._classify_title_level(contact_info.get('title', ''))
        
        recommendations = {
            'recommended_style': self._get_recommended_style(title_level),
            'personalization_target': self._get_personalization_target(title_level),
            'timing_recommendation': self._get_timing_recommendation(title_level),
            'confidence_score': self._calculate_recommendation_confidence()
        }
        
        return recommendations
        
    def _get_recommended_style(self, title_level):
        """Get recommended email style for title level."""
        # Default recommendations based on patterns
        style_map = {
            'c_level': 'brief_direct',
            'vp_director': 'professional_friendly',
            'manager': 'professional_friendly',
            'individual_contributor': 'casual_conversational'
        }
        
        # Override with learned patterns if available
        style_perf = self._analyze_style_performance()
        if style_perf and 'best_performing' in style_perf:
            return style_perf['best_performing']
            
        return style_map.get(title_level, 'professional_friendly')
        
    def _get_personalization_target(self, title_level):
        """Get target personalization count."""
        pers_analysis = self._analyze_personalization_effectiveness()
        
        if pers_analysis and 'optimal_count' in pers_analysis:
            return pers_analysis['optimal_count']
            
        # Default based on title level
        return 3 if title_level in ['c_level', 'vp_director'] else 2
        
    def _get_timing_recommendation(self, title_level):
        """Get timing recommendations."""
        # This could be enhanced with actual send time analysis
        return {
            'best_day': 'Tuesday-Thursday',
            'best_time': '9-11 AM or 2-4 PM recipient time',
            'avoid': 'Monday mornings and Friday afternoons'
        }
        
    def _calculate_recommendation_confidence(self):
        """Calculate confidence in recommendations."""
        total_data_points = sum(style['sent'] for style in self.style_performance.values())
        
        if total_data_points >= 100:
            return 0.9
        elif total_data_points >= 50:
            return 0.75
        elif total_data_points >= 20:
            return 0.6
        else:
            return 0.4
            
    def export_learning_report(self, output_file=None):
        """Export comprehensive learning report."""
        if output_file is None:
            output_file = os.path.join(
                self.data_dir,
                'learning_report_{}.json'.format(
                    datetime.now().strftime("%Y%m%d_%H%M%S")
                )
            )
            
        report = {
            'generated_at': datetime.now().isoformat(),
            'performance_analysis': self.analyze_performance(),
            'success_patterns': self.success_patterns,
            'style_performance': dict(self.style_performance),
            'personalization_effectiveness': dict(self.personalization_effectiveness)
        }
        
        try:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
                
            self.logger.info("Learning report exported to: {}".format(output_file))
            return output_file
            
        except Exception as e:
            self.logger.error("Error exporting report: {}".format(str(e)))
            return None
            
    def _save_learning_record(self, record):
        """Save individual learning record."""
        filename = os.path.join(
            self.data_dir,
            'outcome_{}.json'.format(
                datetime.now().strftime("%Y%m%d_%H%M%S%f")
            )
        )
        
        try:
            with open(filename, 'w') as f:
                json.dump(record, f, indent=2)
                
        except Exception as e:
            self.logger.error("Error saving learning record: {}".format(str(e)))
            
    def load_learning_data(self):
        """Load existing learning data from disk."""
        if not os.path.exists(self.data_dir):
            return
            
        self.logger.info("Loading existing learning data")
        
        # Load outcome records
        for filename in os.listdir(self.data_dir):
            if filename.startswith('outcome_') and filename.endswith('.json'):
                try:
                    with open(os.path.join(self.data_dir, filename), 'r') as f:
                        record = json.load(f)
                        
                    # Rebuild performance metrics
                    self._update_performance_metrics(record)
                    
                    # Extract patterns if successful
                    if record['outcome'].get('got_response'):
                        # Reconstruct pattern
                        pattern = {
                            'timestamp': record['timestamp'],
                            'style': record['email_style'],
                            'personalization_count': len(record['personalization_points']),
                            'personalization_types': record['personalization_points'],
                            'email_length': record['email_length'],
                            'research_quality': record['research_quality'],
                            'contact_title_level': self._classify_title_level(
                                record['contact_info'].get('title', '')
                            ),
                            'response_time_hours': record['outcome'].get('response_time_hours'),
                            'led_to_meeting': record['outcome'].get('led_to_meeting', False)
                        }
                        self.success_patterns.append(pattern)
                        
                except Exception as e:
                    self.logger.warning("Error loading {}: {}".format(filename, str(e)))
                    
        self.logger.info("Loaded {} success patterns".format(len(self.success_patterns)))


def main():
    """Test the learning engine with sample data."""
    print("\n=== Learning Engine Test ===\n")
    
    # Initialize engine
    engine = LearningEngine()
    
    # Simulate some email outcomes
    print("Simulating email outcomes...")
    
    # Successful email example
    successful_email = {
        'contact_context': {
            'contact': {
                'name': 'John Smith',
                'company': 'TechCorp',
                'title': 'VP of Engineering'
            },
            'research': {
                'research_quality_score': 0.8
            }
        },
        'email_content': 'Sample email content...',
        'metadata': {
            'style': 'professional_friendly',
            'personalization_points': ['Used recipient name', 'Referenced company', 'Mentioned role']
        }
    }
    
    outcome1 = {
        'was_sent': True,
        'got_response': True,
        'response_time_hours': 18.5,
        'led_to_meeting': True
    }
    
    engine.record_email_outcome(successful_email, outcome1)
    print("✅ Recorded successful outcome")
    
    # Failed email example
    failed_email = {
        'contact_context': {
            'contact': {
                'name': 'Jane Doe',
                'company': 'StartupXYZ',
                'title': 'CEO'
            },
            'research': {
                'research_quality_score': 0.4
            }
        },
        'email_content': 'Generic email content...',
        'metadata': {
            'style': 'brief_direct',
            'personalization_points': ['Used recipient name']
        }
    }
    
    outcome2 = {
        'was_sent': True,
        'got_response': False
    }
    
    engine.record_email_outcome(failed_email, outcome2)
    print("✅ Recorded failed outcome")
    
    # Analyze performance
    print("\nAnalyzing performance...")
    analysis = engine.analyze_performance()
    
    print("\nPERFORMANCE ANALYSIS:")
    print("-" * 50)
    print("Summary: {} emails tracked, {} responses ({:.0%} response rate)".format(
        analysis['summary_statistics']['total_emails_tracked'],
        analysis['summary_statistics']['total_responses'],
        analysis['summary_statistics']['overall_response_rate']
    ))
    
    if analysis['recommendations']:
        print("\nRECOMMENDATIONS:")
        for rec in analysis['recommendations']:
            print("- {}".format(rec))
            
    # Get contact-specific recommendations
    print("\nCONTACT-SPECIFIC RECOMMENDATIONS:")
    test_contact = {
        'name': 'Test User',
        'title': 'CTO',
        'company': 'Example Corp'
    }
    
    recommendations = engine.get_contact_recommendations(test_contact)
    print("For {}: ".format(test_contact['title']))
    print("- Recommended style: {}".format(recommendations['recommended_style']))
    print("- Target personalizations: {}".format(recommendations['personalization_target']))
    print("- Confidence: {:.0%}".format(recommendations['confidence_score']))
    
    # Export report
    report_file = engine.export_learning_report()
    if report_file:
        print("\n✅ Learning report exported to: {}".format(report_file))
        
    print("\n✅ Module 6 Test Complete!")
    print("🧠 Learning engine is ready to make the system smarter")


if __name__ == "__main__":
    main()