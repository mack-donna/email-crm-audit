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
                'total_rows': i + 1,
                'redirect': url_for('validate_csv')  # Redirect to validation
            })
        
        return jsonify({'error': 'Invalid file type'}), 400
    
    return render_template('upload.html')

@app.route('/validate')
def validate_csv():
    """Validate uploaded CSV and show report"""
    if 'csv_file' not in session:
        return redirect(url_for('upload_csv'))
    
    csv_file = session.get('csv_file')
    
    # Import contact processor for validation
    from contact_processor import ContactProcessor
    processor = ContactProcessor()
    
    # Process and validate the CSV
    validation_results = validate_csv_file(csv_file)
    
    return render_template('validate.html', validation=validation_results)

@app.route('/process-validated', methods=['POST'])
def process_validated():
    """Process CSV after removing invalid records"""
    if 'csv_file' not in session:
        return jsonify({'error': 'No CSV file in session'}), 400
    
    data = request.json
    removed_rows = data.get('removed_rows', [])
    
    # Store removed rows in session for processing
    session['removed_rows'] = removed_rows
    
    # Create a cleaned CSV with only valid records
    cleaned_csv_path = create_cleaned_csv(session['csv_file'], removed_rows)
    session['cleaned_csv_file'] = cleaned_csv_path
    
    # Redirect to campaign setup page
    return jsonify({
        'success': True,
        'redirect': url_for('campaign_setup')
    })

@app.route('/campaign-setup')
def campaign_setup():
    """Campaign configuration page"""
    if 'cleaned_csv_file' not in session and 'csv_file' not in session:
        return redirect(url_for('upload_csv'))
    
    # Count valid contacts after cleaning
    csv_file = session.get('cleaned_csv_file', session.get('csv_file'))
    contact_count = count_csv_contacts(csv_file)
    
    return render_template('campaign_setup.html', contact_count=contact_count)

def create_cleaned_csv(original_csv_path, removed_row_ids):
    """Create a new CSV file with invalid records removed"""
    import csv
    
    # Extract row numbers from removed_row_ids (format: "row_N")
    removed_row_numbers = set()
    for row_id in removed_row_ids:
        if row_id.startswith('row_'):
            try:
                row_num = int(row_id.split('_')[1])
                removed_row_numbers.add(row_num)
            except (IndexError, ValueError):
                continue
    
    # Create cleaned CSV
    cleaned_filename = f"cleaned_{os.path.basename(original_csv_path)}"
    cleaned_path = os.path.join(UPLOAD_FOLDER, cleaned_filename)
    
    with open(original_csv_path, 'r', encoding='utf-8-sig') as infile:
        reader = csv.reader(infile)
        
        with open(cleaned_path, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            
            # Copy header
            headers = next(reader)
            writer.writerow(headers)
            
            # Copy valid rows only
            for row_num, row in enumerate(reader, start=2):
                if row_num not in removed_row_numbers:
                    writer.writerow(row)
    
    return cleaned_path

def count_csv_contacts(csv_path):
    """Count the number of contacts in CSV file"""
    import csv
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            return sum(1 for _ in reader)
    except:
        return 0

def validate_csv_file(filepath):
    """Validate CSV file and return detailed report"""
    import csv
    import re
    
    valid_records = []
    invalid_records = []
    all_records = []
    
    # Email validation regex
    email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 because row 1 is headers
            errors = []
            row_data = {}
            
            # Standardize column names
            for key, value in row.items():
                if key:
                    clean_key = key.lower().strip()
                    # Map common variations
                    if 'first' in clean_key and 'name' in clean_key:
                        row_data['first_name'] = value
                    elif 'last' in clean_key and 'name' in clean_key:
                        row_data['last_name'] = value
                    elif 'account' in clean_key:
                        row_data['company'] = value
                    else:
                        row_data[clean_key] = value
            
            # Combine first and last name if needed
            if 'first_name' in row_data and 'last_name' in row_data and 'name' not in row_data:
                fname = row_data.get('first_name', '').strip()
                lname = row_data.get('last_name', '').strip()
                row_data['name'] = f"{fname} {lname}".strip()
            
            # Validate required fields
            if not row_data.get('name') or len(row_data.get('name', '').strip()) < 2:
                errors.append('Missing or invalid name (must be at least 2 characters)')
            
            if not row_data.get('email'):
                errors.append('Missing email address')
            elif not email_regex.match(row_data.get('email', '').strip()):
                errors.append(f"Invalid email format: {row_data.get('email')}")
            
            if not row_data.get('company') or not row_data.get('company', '').strip():
                errors.append('Missing company name')
            
            # Check for duplicates
            if row_data.get('email') in [r.get('email') for r in all_records]:
                errors.append(f"Duplicate email: {row_data.get('email')}")
            
            record = {
                'row_number': row_num,
                'row_id': f"row_{row_num}",
                'data': {
                    'name': row_data.get('name', ''),
                    'email': row_data.get('email', ''),
                    'company': row_data.get('company', ''),
                    'title': row_data.get('title', '')
                },
                'errors': errors
            }
            
            all_records.append(row_data)
            
            if errors:
                invalid_records.append(record)
            else:
                valid_records.append(record['data'])
    
    return {
        'total_records': len(all_records),
        'valid_count': len(valid_records),
        'invalid_records': invalid_records,
        'valid_preview': valid_records[:5]  # First 5 valid records for preview
    }

@app.route('/generate', methods=['POST'])
def generate_emails():
    """Generate emails for uploaded contacts"""
    # Use cleaned CSV if available, otherwise fall back to original
    csv_file = session.get('cleaned_csv_file', session.get('csv_file'))
    if not csv_file:
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
        
        # Run campaign with correct arguments (using cleaned CSV)
        results = orchestrator.run_campaign(
            csv_file=csv_file,  # Use cleaned CSV if available
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