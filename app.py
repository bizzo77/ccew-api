import os
import json
import requests
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import io
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')

# In-memory session storage (use database in production)
sessions = {}

@app.route('/')
def index():
    return jsonify({
        "status": "online",
        "service": "CCEW API",
        "version": "1.0"
    })

@app.route('/api/ccew/generate', methods=['POST'])
def generate_ccew():
    """Generate a new CCEW form session from SimPro job data"""
    try:
        job_data = request.json
        
        # Create unique session ID
        session_id = str(uuid.uuid4())
        
        # Store job data in session
        sessions[session_id] = {
            'job_data': job_data,
            'created_at': datetime.now().isoformat(),
            'status': 'pending'
        }
        
        # Return form URL
        form_url = f"{request.host_url}form/{session_id}"
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "form_url": form_url
        })
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/form/<session_id>')
def show_form(session_id):
    """Display CCEW form for technician to complete"""
    if session_id not in sessions:
        return "Invalid or expired session", 404
    
    job_data = sessions[session_id]['job_data']
    
    # Simple HTML form (in production, use the Vue.js frontend)
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>CCEW Form - Job #{job_data.get('ID', 'N/A')}</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }}
            h1 {{ color: #333; }}
            .info {{ background: #f0f0f0; padding: 15px; margin: 20px 0; border-radius: 5px; }}
            form {{ margin-top: 30px; }}
            label {{ display: block; margin: 15px 0 5px; font-weight: bold; }}
            input, select, textarea {{ width: 100%; padding: 8px; margin-bottom: 10px; }}
            button {{ background: #007bff; color: white; padding: 12px 30px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }}
            button:hover {{ background: #0056b3; }}
        </style>
    </head>
    <body>
        <h1>CCEW Form</h1>
        <div class="info">
            <p><strong>Job Number:</strong> {job_data.get('ID', 'N/A')}</p>
            <p><strong>Customer:</strong> {job_data.get('Customer', {}).get('CompanyName', 'N/A')}</p>
            <p><strong>Site:</strong> {job_data.get('Site', {}).get('Name', 'N/A')}</p>
        </div>
        
        <form id="ccewForm">
            <h2>Equipment Details</h2>
            <label>Equipment Installed:</label>
            <textarea name="equipment" rows="4" required></textarea>
            
            <h2>Test Results</h2>
            <label>Test Completion Date:</label>
            <input type="date" name="test_date" required>
            
            <label>Tester License Number:</label>
            <input type="text" name="license_number" required>
            
            <label>License Expiry Date:</label>
            <input type="date" name="license_expiry" required>
            
            <h2>Energy Provider</h2>
            <label>Select Provider:</label>
            <select name="energy_provider" required>
                <option value="">-- Select --</option>
                <option value="ausgrid">Ausgrid</option>
                <option value="endeavour">Endeavour Energy</option>
                <option value="essential">Essential Energy</option>
            </select>
            
            <button type="submit">Submit CCEW</button>
        </form>
        
        <script>
            document.getElementById('ccewForm').addEventListener('submit', async (e) => {{
                e.preventDefault();
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData);
                
                const response = await fetch('/api/ccew/submit/{session_id}', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify(data)
                }});
                
                const result = await response.json();
                if (result.success) {{
                    alert('CCEW submitted successfully!');
                    window.location.href = '/success';
                }} else {{
                    alert('Error: ' + result.error);
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    return render_template_string(html)

@app.route('/api/ccew/submit/<session_id>', methods=['POST'])
def submit_ccew(session_id):
    """Submit completed CCEW form"""
    try:
        if session_id not in sessions:
            return jsonify({"success": False, "error": "Invalid session"}), 404
        
        form_data = request.json
        job_data = sessions[session_id]['job_data']
        
        # TODO: Generate PDF with ReportLab
        # TODO: Email to energy supplier
        # TODO: Upload to SimPro
        
        sessions[session_id]['status'] = 'completed'
        sessions[session_id]['form_data'] = form_data
        sessions[session_id]['completed_at'] = datetime.now().isoformat()
        
        return jsonify({"success": True, "message": "CCEW submitted successfully"})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/success')
def success():
    return "<h1>CCEW Submitted Successfully</h1><p>Thank you! The certificate has been sent to the energy supplier.</p>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
