#!/usr/bin/env python3
"""
Flask Web Application for Email Outreach Automation
Phase 1: Simple functional interface
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from werkzeug.utils import secure_filename
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
import traceback

# Import existing modules
from workflow_orchestrator import WorkflowOrchestrator
from gmail_drafts_manager import GmailDraftsManager

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Configuration
UPLOAD_FOLDER = 'uploads'
CAMPAIGNS_FOLDER = 'outreach_campaigns'
ALLOWED_EXTENSIONS = {'csv'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Ensure folders exist
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
Path(CAMPAIGNS_FOLDER).mkdir(exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')

@app.route('/clear')
def clear_session():
    """Clear session and redirect to home"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
def upload_csv():
    """Handle CSV file upload"""
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            # Save file with unique name
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(filepath)
            
            # Store in session
            session['csv_file'] = filepath
            session['original_filename'] = filename
            
            # Parse CSV to show preview
            import csv
            contacts = []
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if i < 5:  # Preview first 5 contacts
                        contacts.append(row)
            
            return jsonify({
                'success': True,
                'filename': filename,
                'preview': contacts,
                'total_rows': i + 1
            })
        
        return jsonify({'error': 'Invalid file type'}), 400
    
    return render_template('upload.html')

@app.route('/generate', methods=['POST'])
def generate_emails():
    """Generate emails for uploaded contacts"""
    if 'csv_file' not in session:
        return jsonify({'error': 'No CSV file uploaded'}), 400
    
    try:
        data = request.json
        # Sanitize campaign name to avoid filesystem issues
        raw_name = data.get('campaign_name', f'Campaign_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        campaign_name = raw_name.replace('/', '-').replace('\\', '-')
        
        # Initialize orchestrator
        orchestrator = WorkflowOrchestrator()
        
        # Store campaign ID in session
        campaign_id = str(uuid.uuid4())
        session['campaign_id'] = campaign_id
        
        # Set auto-approve to skip CLI review (we'll review in web UI)
        os.environ['AUTO_APPROVE_EMAILS'] = 'true'
        
        # Run campaign with correct arguments
        results = orchestrator.run_campaign(
            csv_file=session['csv_file'],  # Pass the file path
            campaign_name=campaign_name
        )
        
        # Clean up the environment variable
        os.environ.pop('AUTO_APPROVE_EMAILS', None)
        
        if results and 'campaign_file' in results:
            # Store results for review
            session['campaign_results'] = results['campaign_file']
            
            return jsonify({
                'success': True,
                'campaign_id': campaign_id,
                'emails_generated': len(results.get('approved_emails', [])),
                'redirect': url_for('review_emails')
            })
        else:
            # Check for specific error messages
            error_msg = 'Failed to generate emails'
            if results and 'error' in results:
                error_msg = results['error']
            elif not results:
                error_msg = 'No valid contacts found in CSV. Please check that your CSV has name/email/company columns.'
            return jsonify({'error': error_msg}), 500
            
    except Exception as e:
        print(f"Error generating emails: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/review')
def review_emails():
    """Review and approve generated emails"""
    if 'campaign_results' not in session:
        return redirect(url_for('upload_csv'))
    
    # Load campaign results
    campaign_file = session.get('campaign_results')
    if not campaign_file or not os.path.exists(campaign_file):
        return redirect(url_for('upload_csv'))
    
    with open(campaign_file, 'r') as f:
        campaign_data = json.load(f)
    
    return render_template('review.html', campaign=campaign_data)

@app.route('/approve', methods=['POST'])
def approve_emails():
    """Approve selected emails and create Gmail drafts"""
    try:
        data = request.json
        approved_ids = data.get('approved_ids', [])
        create_drafts = data.get('create_drafts', False)
        
        if not approved_ids:
            return jsonify({'error': 'No emails selected'}), 400
        
        # Load campaign data
        campaign_file = session.get('campaign_results')
        with open(campaign_file, 'r') as f:
            campaign_data = json.load(f)
        
        # Get all emails from campaign data and filter by approved IDs
        all_emails = campaign_data.get('approved_emails', [])
        
        # If no emails in approved_emails, the IDs might be 1-based indices
        # Convert string IDs to integers and use as indices
        approved_emails = []
        for id_str in approved_ids:
            try:
                # Try to use as 1-based index
                index = int(id_str) - 1
                if 0 <= index < len(all_emails):
                    approved_emails.append(all_emails[index])
            except (ValueError, IndexError):
                # If that fails, try to match by email id
                for email in all_emails:
                    if email.get('id') == id_str:
                        approved_emails.append(email)
                        break
        
        # Update campaign with only approved emails
        campaign_data['approved_emails'] = approved_emails
        campaign_data['approval_timestamp'] = datetime.now().isoformat()
        
        # Save updated campaign
        with open(campaign_file, 'w') as f:
            json.dump(campaign_data, f, indent=2)
        
        # Create Gmail drafts if requested
        drafts_created = []
        if create_drafts:
            gmail_manager = GmailDraftsManager()
            drafts_created = gmail_manager.create_drafts_from_campaign(campaign_file)
        
        return jsonify({
            'success': True,
            'approved_count': len(approved_emails),
            'drafts_created': len(drafts_created),
            'redirect': url_for('campaign_complete')
        })
        
    except Exception as e:
        print(f"Error approving emails: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/complete')
def campaign_complete():
    """Campaign completion page"""
    campaign_file = session.get('campaign_results')
    if not campaign_file or not os.path.exists(campaign_file):
        return redirect(url_for('index'))
    
    with open(campaign_file, 'r') as f:
        campaign_data = json.load(f)
    
    # Clear session
    session.clear()
    
    return render_template('complete.html', campaign=campaign_data)

@app.route('/api/status')
def api_status():
    """API endpoint to check system status"""
    status = {
        'anthropic_api_key': bool(os.environ.get('ANTHROPIC_API_KEY')),
        'gmail_credentials': os.path.exists('credentials.json'),
        'python_version': '3.9+',
        'system_ready': True
    }
    return jsonify(status)

@app.route('/campaigns')
def list_campaigns():
    """List all previous campaigns"""
    campaigns = []
    campaign_files = Path(CAMPAIGNS_FOLDER).glob('*.json')
    
    for file in sorted(campaign_files, key=lambda x: x.stat().st_mtime, reverse=True):
        with open(file, 'r') as f:
            data = json.load(f)
            campaigns.append({
                'name': data.get('campaign_name', 'Unnamed'),
                'date': data.get('timestamp', ''),
                'emails_count': len(data.get('approved_emails', [])),
                'file': file.name
            })
    
    return render_template('campaigns.html', campaigns=campaigns)

@app.route('/download/<filename>')
def download_campaign(filename):
    """Download campaign results as JSON"""
    file_path = os.path.join(CAMPAIGNS_FOLDER, secure_filename(filename))
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=f"campaign_{filename}")
    return "File not found", 404

if __name__ == '__main__':
    print("🚀 Email Outreach Web App")
    print("📍 Running at http://127.0.0.1:8080")
    print("⚠️  Set ANTHROPIC_API_KEY environment variable for AI generation")
    print("📧 Ensure credentials.json exists for Gmail integration")
    app.run(debug=True, host='127.0.0.1', port=8080)