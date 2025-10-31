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
        "version": "2.0"
    })

@app.route('/api/ccew/generate', methods=['POST'])
def generate_ccew():
    """Generate a new CCEW form session from SimPro job data"""
    try:
        simpro_data = request.json
        
        # Create unique session ID
        session_id = str(uuid.uuid4())
        
        # Extract and pre-fill available fields from SimPro
        prefilled_data = {
            # Serial Number (Job ID)
            'serialNo': str(simpro_data.get('job_id', '')),
            
            # Installation Address
            'propertyName': simpro_data.get('site_address', ''),
            
            # Customer Details
            'customerCompanyName': simpro_data.get('customer_name', ''),
            'customerFirstName': simpro_data.get('customer_first_name', ''),
            'customerLastName': simpro_data.get('customer_last_name', ''),
            
            # Installer License Details (hardcoded for Karl Knopp)
            'installerFirstName': 'Karl',
            'installerLastName': 'Knopp',
            'installerStreetNumber': '177',
            'installerStreetName': 'Bringelly Road',
            'installerSuburb': 'Leppington',
            'installerState': 'NSW',
            'installerPostCode': '2179',
            'installerEmail': 'admin@proformelec.com.au',
            'installerOfficeNo': '47068270',
            'installerContractorLicenseNo': '292339C',
            'installerContractorExpiryDate': '2027-02-02',
            
            # Tester License Details (from technician + hardcoded)
            'testerFirstName': simpro_data.get('technician_first_name', simpro_data.get('technician_name', '').split()[0] if simpro_data.get('technician_name') else ''),
            'testerLastName': simpro_data.get('technician_last_name', ' '.join(simpro_data.get('technician_name', '').split()[1:]) if simpro_data.get('technician_name') and len(simpro_data.get('technician_name', '').split()) > 1 else ''),
            'testerStreetNumber': '177',
            'testerStreetName': 'Bringelly Road',
            'testerSuburb': 'Leppington',
            'testerState': 'NSW',
            'testerPostCode': '2179',
            'testerEmail': 'admin@proformelec.com.au',
            'testerOfficeNo': '47068270',
            'testerContractorLicenseNo': simpro_data.get('technician_license_number', ''),
            'testerContractorExpiryDate': simpro_data.get('technician_license_expiry', ''),
        }
        
        # Store session data
        sessions[session_id] = {
            'simpro_data': simpro_data,
            'prefilled_data': prefilled_data,
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
    
    session_data = sessions[session_id]
    prefilled = session_data['prefilled_data']
    simpro_data = session_data['simpro_data']
    
    # Enhanced HTML form with pre-filled fields
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>CCEW Form - Job #{prefilled.get('serialNo', 'N/A')}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                background: #f5f5f5;
                padding: 20px;
                line-height: 1.6;
            }}
            .container {{ 
                max-width: 900px; 
                margin: 0 auto; 
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1 {{ 
                color: #d32f2f; 
                margin-bottom: 10px;
                font-size: 24px;
            }}
            h2 {{ 
                background: #4caf50;
                color: white;
                padding: 12px 15px;
                margin: 25px 0 15px;
                border-radius: 4px;
                font-size: 16px;
            }}
            .info {{ 
                background: #e3f2fd; 
                padding: 15px; 
                margin: 20px 0; 
                border-left: 4px solid #2196f3;
                border-radius: 4px;
            }}
            .info p {{ margin: 5px 0; }}
            .form-group {{ margin-bottom: 20px; }}
            label {{ 
                display: block; 
                margin-bottom: 6px; 
                font-weight: 600;
                color: #333;
            }}
            label.required:after {{ content: " *"; color: #d32f2f; }}
            input[type="text"],
            input[type="date"],
            input[type="email"],
            select,
            textarea {{ 
                width: 100%; 
                padding: 10px; 
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                font-family: inherit;
            }}
            input[type="text"]:focus,
            input[type="date"]:focus,
            input[type="email"]:focus,
            select:focus,
            textarea:focus {{
                outline: none;
                border-color: #4caf50;
                box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.1);
            }}
            input:read-only {{
                background-color: #f5f5f5;
                cursor: not-allowed;
            }}
            .checkbox-group {{ margin: 10px 0; }}
            .checkbox-item {{ 
                margin: 8px 0;
                display: flex;
                align-items: center;
            }}
            .checkbox-item input {{ 
                width: auto; 
                margin-right: 8px;
            }}
            .grid {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                gap: 15px;
            }}
            button {{ 
                background: #4caf50; 
                color: white; 
                padding: 14px 30px; 
                border: none; 
                border-radius: 4px; 
                cursor: pointer; 
                font-size: 16px;
                font-weight: 600;
                width: 100%;
                margin-top: 20px;
            }}
            button:hover {{ background: #45a049; }}
            button:disabled {{ background: #ccc; cursor: not-allowed; }}
            .readonly-note {{ 
                font-size: 12px; 
                color: #666; 
                font-style: italic; 
                margin-top: 5px;
            }}
            .section-note {{
                background: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 12px;
                margin: 15px 0;
                border-radius: 4px;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>NSW Fair Trading - Certificate Compliance Electrical Work (CCEW)</h1>
            
            <div class="info">
                <p><strong>Serial No (Job Number):</strong> {prefilled.get('serialNo', 'N/A')}</p>
                <p><strong>Customer:</strong> {prefilled.get('customerCompanyName', 'N/A')}</p>
                <p><strong>Site:</strong> {prefilled.get('propertyName', 'N/A')}</p>
            </div>
            
            <div class="section-note">
                <strong>Note:</strong> Fields marked with gray background are pre-filled from SimPro and cannot be edited. 
                Fields marked with <span style="color: #d32f2f;">*</span> are required.
            </div>
            
            <form id="ccewForm">
                <h2>Installation Address</h2>
                <div class="form-group">
                    <label class="required">Serial No (Job Number)</label>
                    <input type="text" name="serialNo" value="{prefilled.get('serialNo', '')}" readonly required>
                    <div class="readonly-note">Auto-filled from SimPro</div>
                </div>
                
                <div class="form-group">
                    <label class="required">Property Name</label>
                    <input type="text" name="propertyName" value="{prefilled.get('propertyName', '')}" readonly required>
                    <div class="readonly-note">Auto-filled from SimPro</div>
                </div>
                
                <div class="grid">
                    <div class="form-group">
                        <label>Floor</label>
                        <input type="text" name="floor">
                    </div>
                    <div class="form-group">
                        <label>Unit</label>
                        <input type="text" name="unit">
                    </div>
                </div>
                
                <div class="grid">
                    <div class="form-group">
                        <label class="required">Street Number</label>
                        <input type="text" name="streetNumber" required>
                    </div>
                    <div class="form-group">
                        <label class="required">Street Name</label>
                        <input type="text" name="streetName" required>
                    </div>
                </div>
                
                <div class="grid">
                    <div class="form-group">
                        <label class="required">Suburb</label>
                        <input type="text" name="suburb" required>
                    </div>
                    <div class="form-group">
                        <label class="required">State</label>
                        <input type="text" name="state" value="NSW" readonly required>
                    </div>
                    <div class="form-group">
                        <label class="required">Post Code</label>
                        <input type="text" name="postCode" required>
                    </div>
                </div>
                
                <div class="grid">
                    <div class="form-group">
                        <label>Pit/Pillar/Pole Number</label>
                        <input type="text" name="pitPillarPoleNumber">
                    </div>
                    <div class="form-group">
                        <label>NMI</label>
                        <input type="text" name="nmi">
                    </div>
                    <div class="form-group">
                        <label>Meter Number</label>
                        <input type="text" name="meterNumber">
                    </div>
                </div>
                
                <div class="form-group">
                    <label class="required">AEMO Metering Provider ID</label>
                    <input type="text" name="aemoMeteringProviderId" required>
                </div>
                
                <h2>Customer Details</h2>
                <div class="grid">
                    <div class="form-group">
                        <label class="required">First Name</label>
                        <input type="text" name="customerFirstName" value="{prefilled.get('customerFirstName', '')}" required>
                    </div>
                    <div class="form-group">
                        <label class="required">Last Name</label>
                        <input type="text" name="customerLastName" value="{prefilled.get('customerLastName', '')}" required>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>Company Name</label>
                    <input type="text" name="customerCompanyName" value="{prefilled.get('customerCompanyName', '')}" readonly>
                    <div class="readonly-note">Auto-filled from SimPro</div>
                </div>
                
                <div class="grid">
                    <div class="form-group">
                        <label>Floor</label>
                        <input type="text" name="customerFloor">
                    </div>
                    <div class="form-group">
                        <label>Unit</label>
                        <input type="text" name="customerUnit">
                    </div>
                </div>
                
                <div class="grid">
                    <div class="form-group">
                        <label class="required">Street Number</label>
                        <input type="text" name="customerStreetNumber" required>
                    </div>
                    <div class="form-group">
                        <label class="required">Street Name</label>
                        <input type="text" name="customerStreetName" required>
                    </div>
                </div>
                
                <div class="grid">
                    <div class="form-group">
                        <label class="required">Suburb</label>
                        <input type="text" name="customerSuburb" required>
                    </div>
                    <div class="form-group">
                        <label class="required">State</label>
                        <input type="text" name="customerState" required>
                    </div>
                    <div class="form-group">
                        <label class="required">Post Code</label>
                        <input type="text" name="customerPostCode" required>
                    </div>
                </div>
                
                <div class="grid">
                    <div class="form-group">
                        <label>Email</label>
                        <input type="email" name="customerEmail">
                    </div>
                    <div class="form-group">
                        <label>Office Number</label>
                        <input type="text" name="customerOfficeNo">
                    </div>
                    <div class="form-group">
                        <label>Mobile Number</label>
                        <input type="text" name="customerMobileNo">
                    </div>
                </div>
                
                <h2>Installation Details</h2>
                <div class="form-group">
                    <label class="required">Type of Installation</label>
                    <select name="installationType" required>
                        <option value="">-- Select --</option>
                        <option value="Residential">Residential</option>
                        <option value="Commercial">Commercial</option>
                        <option value="Industrial">Industrial</option>
                        <option value="Rural">Rural</option>
                        <option value="Mixed Development">Mixed Development</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label class="required">Work Carried Out (select at least one)</label>
                    <div class="checkbox-group">
                        <div class="checkbox-item">
                            <input type="checkbox" name="workCarriedOut" value="New Work" id="work1">
                            <label for="work1">New Work</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" name="workCarriedOut" value="Installed Meter" id="work2">
                            <label for="work2">Installed Meter</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" name="workCarriedOut" value="Network connection" id="work3">
                            <label for="work3">Network Connection</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" name="workCarriedOut" value="Addition/alteration to existing" id="work4">
                            <label for="work4">Addition/Alteration to Existing</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" name="workCarriedOut" value="Install Advanced Meter" id="work5">
                            <label for="work5">Install Advanced Meter</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" name="workCarriedOut" value="EV Connection" id="work6">
                            <label for="work6">EV Connection</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" name="workCarriedOut" value="Re-inspection of non-compliant work" id="work7">
                            <label for="work7">Re-inspection of Non-Compliant Work</label>
                        </div>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>Non-Compliance Number (if applicable)</label>
                    <input type="text" name="nonComplianceNo">
                </div>
                
                <div class="form-group">
                    <label>Special Conditions (optional)</label>
                    <div class="checkbox-group">
                        <div class="checkbox-item">
                            <input type="checkbox" name="specialConditions" value="Over 100 amps" id="special1">
                            <label for="special1">Over 100 Amps</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" name="specialConditions" value="Hazardous Area" id="special2">
                            <label for="special2">Hazardous Area</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" name="specialConditions" value="Off Grid Installation" id="special3">
                            <label for="special3">Off Grid Installation</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" name="specialConditions" value="High Voltage" id="special4">
                            <label for="special4">High Voltage</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" name="specialConditions" value="Unmetered Supply" id="special5">
                            <label for="special5">Unmetered Supply</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" name="specialConditions" value="Secondary Power Supply" id="special6">
                            <label for="special6">Secondary Power Supply</label>
                        </div>
                    </div>
                </div>
                
                <h2>Installer License Details</h2>
                <div class="section-note">
                    All installer details are pre-filled for Karl Knopp
                </div>
                <div class="grid">
                    <div class="form-group">
                        <label>First Name</label>
                        <input type="text" name="installerFirstName" value="{prefilled.get('installerFirstName', '')}" readonly>
                    </div>
                    <div class="form-group">
                        <label>Last Name</label>
                        <input type="text" name="installerLastName" value="{prefilled.get('installerLastName', '')}" readonly>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>Contractor License Number</label>
                    <input type="text" name="installerContractorLicenseNo" value="{prefilled.get('installerContractorLicenseNo', '')}" readonly>
                </div>
                
                <div class="form-group">
                    <label>License Expiry Date</label>
                    <input type="date" name="installerContractorExpiryDate" value="{prefilled.get('installerContractorExpiryDate', '')}" readonly>
                </div>
                
                <h2>Tester License Details</h2>
                <div class="grid">
                    <div class="form-group">
                        <label class="required">First Name</label>
                        <input type="text" name="testerFirstName" value="{prefilled.get('testerFirstName', '')}" required>
                    </div>
                    <div class="form-group">
                        <label class="required">Last Name</label>
                        <input type="text" name="testerLastName" value="{prefilled.get('testerLastName', '')}" required>
                    </div>
                </div>
                
                <div class="form-group">
                    <label class="required">Contractor License Number</label>
                    <input type="text" name="testerContractorLicenseNo" required>
                </div>
                
                <div class="form-group">
                    <label class="required">License Expiry Date</label>
                    <input type="date" name="testerContractorExpiryDate" required>
                </div>
                
                <div class="form-group">
                    <label class="required">Test Completion Date</label>
                    <input type="date" name="testCompletedDate" required>
                </div>
                
                <h2>Submit CCEW</h2>
                <div class="form-group">
                    <label class="required">Energy Provider</label>
                    <select name="energyProvider" required>
                        <option value="">-- Select --</option>
                        <option value="Ausgrid">Ausgrid</option>
                        <option value="Endeavour Energy">Endeavour Energy</option>
                        <option value="Essential Energy">Essential Energy</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Meter Provider Email</label>
                    <input type="email" name="meterProviderEmail" placeholder="Email to send copy to meter provider">
                </div>
                
                <div class="form-group">
                    <label>Owner Email</label>
                    <input type="email" name="ownerEmail" placeholder="Email to send copy to property owner">
                </div>
                
                <div class="form-group">
                    <div class="checkbox-item">
                        <input type="checkbox" name="certificationStatement" id="certify" required>
                        <label for="certify" class="required">I certify that the information provided in this CCEW is true and correct</label>
                    </div>
                </div>
                
                <button type="submit" id="submitBtn">Submit CCEW</button>
            </form>
        </div>
        
        <script>
            document.getElementById('ccewForm').addEventListener('submit', async (e) => {{
                e.preventDefault();
                
                const submitBtn = document.getElementById('submitBtn');
                submitBtn.disabled = true;
                submitBtn.textContent = 'Submitting...';
                
                const formData = new FormData(e.target);
                const data = {{}};
                
                // Handle regular fields
                for (const [key, value] of formData.entries()) {{
                    if (key === 'workCarriedOut' || key === 'specialConditions') {{
                        if (!data[key]) data[key] = [];
                        data[key].push(value);
                    }} else {{
                        data[key] = value;
                    }}
                }}
                
                // Ensure arrays exist even if empty
                if (!data.workCarriedOut) data.workCarriedOut = [];
                if (!data.specialConditions) data.specialConditions = [];
                
                try {{
                    const response = await fetch('/api/ccew/submit/{session_id}', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify(data)
                    }});
                    
                    const result = await response.json();
                    if (result.success) {{
                        alert('CCEW submitted successfully! The certificate has been sent to the energy supplier.');
                        window.location.href = '/success';
                    }} else {{
                        alert('Error: ' + (result.error || result.message));
                        submitBtn.disabled = false;
                        submitBtn.textContent = 'Submit CCEW';
                    }}
                }} catch (error) {{
                    alert('Error submitting form: ' + error.message);
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Submit CCEW';
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
        session_data = sessions[session_id]
        
        # Merge prefilled data with form data
        complete_data = {**session_data['prefilled_data'], **form_data}
        
        # Determine email recipient based on energy provider
        energy_provider = form_data.get('energyProvider', '')
        if energy_provider == 'Ausgrid':
            primary_email = 'datanorth@ausgrid.com.au'
        else:
            primary_email = 'metercrew@finance.nsw.gov.au'
        
        # TODO: Generate PDF with complete_data
        # TODO: Send email to primary_email, meter provider, and owner
        
        sessions[session_id]['status'] = 'completed'
        sessions[session_id]['form_data'] = complete_data
        sessions[session_id]['completed_at'] = datetime.now().isoformat()
        sessions[session_id]['email_sent_to'] = primary_email
        
        return jsonify({
            "success": True, 
            "message": "CCEW submitted successfully",
            "email_sent_to": primary_email
        })
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/success')
def success():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CCEW Submitted</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                background: #f5f5f5;
            }}
            .success-container {{
                text-align: center;
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                max-width: 500px;
            }}
            h1 {{ color: #4caf50; margin-bottom: 20px; }}
            p {{ color: #666; line-height: 1.6; }}
            .checkmark {{
                width: 80px;
                height: 80px;
                border-radius: 50%;
                display: block;
                stroke-width: 2;
                stroke: #4caf50;
                stroke-miterlimit: 10;
                margin: 20px auto;
                box-shadow: inset 0px 0px 0px #4caf50;
                animation: fill .4s ease-in-out .4s forwards, scale .3s ease-in-out .9s both;
            }}
            .checkmark__circle {{
                stroke-dasharray: 166;
                stroke-dashoffset: 166;
                stroke-width: 2;
                stroke-miterlimit: 10;
                stroke: #4caf50;
                fill: none;
                animation: stroke 0.6s cubic-bezier(0.65, 0, 0.45, 1) forwards;
            }}
            .checkmark__check {{
                transform-origin: 50% 50%;
                stroke-dasharray: 48;
                stroke-dashoffset: 48;
                animation: stroke 0.3s cubic-bezier(0.65, 0, 0.45, 1) 0.8s forwards;
            }}
            @keyframes stroke {{
                100% {{ stroke-dashoffset: 0; }}
            }}
            @keyframes scale {{
                0%, 100% {{ transform: none; }}
                50% {{ transform: scale3d(1.1, 1.1, 1); }}
            }}
            @keyframes fill {{
                100% {{ box-shadow: inset 0px 0px 0px 30px #4caf50; }}
            }}
        </style>
    </head>
    <body>
        <div class="success-container">
            <svg class="checkmark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                <circle class="checkmark__circle" cx="26" cy="26" r="25" fill="none"/>
                <path class="checkmark__check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
            </svg>
            <h1>CCEW Submitted Successfully!</h1>
            <p>Thank you! The Certificate of Compliance for Electrical Work has been sent to the energy supplier and relevant parties.</p>
            <p style="margin-top: 20px; font-size: 14px; color: #999;">You can now close this window.</p>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
