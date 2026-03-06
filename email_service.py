"""
Email Service - SendGrid Integration
Handles all email sending functionality
"""

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import sqlite3
from datetime import datetime
import uuid

class EmailService:
    def __init__(self, api_key=None):
        """Initialize SendGrid client"""
        self.api_key = api_key or os.getenv('SENDGRID_API_KEY')
        if not self.api_key:
            raise ValueError("SendGrid API key not found!")
        
        self.sg = SendGridAPIClient(self.api_key)
        self.from_email = "jabeenshagufta93@gmail.com"  # Replace with your verified sender
    
    def send_agent_invitation(self, to_email, agent_data, template_name="professional"):
        """Send agent invitation email"""
        
        try:
            # Get template content
            subject, html_content = self._get_template(template_name, agent_data)
            
            # Create email
            message = Mail(
                from_email=Email(self.from_email, "Umrah Pro Partnerships"),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            # Send email
            response = self.sg.send(message)
            
            # Log to database
            self._log_email(to_email, agent_data, template_name, "sent", response.status_code)
            
            return {
                "success": True,
                "status_code": response.status_code,
                "message": "Email sent successfully!"
            }
        
        except Exception as e:
            # Log error
            self._log_email(to_email, agent_data, template_name, "failed", 0, str(e))
            
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to send email"
            }
    
    def _get_template(self, template_name, agent_data):
        """Get email template content"""
        
        company = agent_data.get('company_name', '[Company Name]')
        contact = agent_data.get('contact_name', '[Contact Name]')
        commission = agent_data.get('commission_rate', 25.0)
        
        if template_name == "professional":
            subject = f"Invitation to Join Umrah Pro - Premium Travel Partner Program"
            
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #059669, #10b981);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .content {{
            background: #ffffff;
            padding: 30px;
            border-radius: 10px;
        }}
        .benefits {{
            background: #f0fdf4;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .benefit-item {{
            padding: 10px 0;
            border-bottom: 1px solid #d1fae5;
        }}
        .cta-button {{
            display: inline-block;
            background: #059669;
            color: white;
            padding: 15px 40px;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
            font-weight: bold;
        }}
        .footer {{
            text-align: center;
            color: #666;
            font-size: 12px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🕌 Umrah Pro</h1>
        <p>Premium Travel Partner Program</p>
    </div>
    
    <div class="content">
        <p>Dear {contact},</p>
        
        <p><strong>As-salamu alaykum wa rahmatullahi wa barakatuh!</strong></p>
        
        <p>I hope this message finds you in the best of health and Iman.</p>
        
        <p>I'm reaching out to invite <strong>{company}</strong> to join <strong>Umrah Pro</strong>, 
        the fastest-growing digital platform connecting Umrah travelers with trusted travel agencies worldwide.</p>
        
        <div class="benefits">
            <h3>🌟 Why Partner with Umrah Pro?</h3>
            
            <div class="benefit-item">
                <strong>✅ Reach Thousands of Customers</strong><br>
                Our platform attracts pilgrims from 50+ countries
            </div>
            
            <div class="benefit-item">
                <strong>✅ Zero Listing Fees</strong><br>
                List unlimited packages at no cost
            </div>
            
            <div class="benefit-item">
                <strong>✅ Direct Customer Inquiries</strong><br>
                Get qualified leads delivered to your inbox
            </div>
            
            <div class="benefit-item">
                <strong>✅ Competitive Commission</strong><br>
                We offer {commission}% commission on bookings
            </div>
            
            <div class="benefit-item">
                <strong>✅ Easy Package Management</strong><br>
                Update packages in real-time through your dashboard
            </div>
        </div>
        
        <h3>🎁 Special Offer for Early Partners</h3>
        <p>As one of our founding partners, you'll receive:</p>
        <ul>
            <li>Featured listing for your first 3 packages (FREE)</li>
            <li>Priority placement in search results for 6 months</li>
            <li>Dedicated account manager</li>
        </ul>
        
        <center>
            <a href="https://umrahpro.com/agent/register" class="cta-button">
                🚀 Join Umrah Pro Now
            </a>
        </center>
        
        <p><strong>JazakAllahu Khair,</strong><br>
        Umrah Pro Partnership Team</p>
    </div>
    
    <div class="footer">
        <p>© 2024 Umrah Pro. All rights reserved.</p>
    </div>
</body>
</html>
"""
        
        elif template_name == "premium":
            subject = f"🌟 Exclusive Premium Partnership - Umrah Pro"
            
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .premium-badge {{
            background: white;
            color: #f59e0b;
            padding: 10px 20px;
            border-radius: 20px;
            display: inline-block;
            font-weight: bold;
            margin-top: 10px;
        }}
        .earnings-box {{
            background: #fffbeb;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border: 2px solid #fbbf24;
        }}
        .highlight {{
            background: #fef3c7;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: bold;
        }}
        .cta-button {{
            display: inline-block;
            background: #f59e0b;
            color: white;
            padding: 15px 40px;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>⭐ PREMIUM PARTNER INVITATION</h1>
        <div class="premium-badge">EXCLUSIVE OFFER</div>
    </div>
    
    <div class="content">
        <p>Dear {contact},</p>
        
        <p><strong>As-salamu alaykum!</strong></p>
        
        <p>I'm excited to extend an <strong>exclusive Premium Partnership invitation</strong> 
        to {company}.</p>
        
        <div class="earnings-box">
            <h3>💰 YOUR ESTIMATED EARNINGS:</h3>
            <p><strong>Conservative:</strong> ${int(20 * 2500 * commission / 100):,}/month</p>
            <p><strong>Moderate:</strong> ${int(35 * 3000 * commission / 100):,}/month</p>
            <p><strong>Optimistic:</strong> ${int(50 * 4000 * commission / 100):,}/month</p>
        </div>
        
        <center>
            <a href="https://umrahpro.com/agent/premium-register" class="cta-button">
                ⭐ CLAIM YOUR PREMIUM SPOT
            </a>
        </center>
        
        <p><strong>Best regards,</strong><br>
        Partnership Director<br>
        Umrah Pro</p>
    </div>
</body>
</html>
"""
        
        else:  # early_bird
            subject = f"🎁 Early Bird Offer: Join Umrah Pro (Limited Time)"
            
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .urgent-banner {{
            background: #dc2626;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .countdown {{
            font-size: 32px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .cta-button {{
            display: inline-block;
            background: #dc2626;
            color: white;
            padding: 18px 50px;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="urgent-banner">
        <h2>⏰ LIMITED TIME OFFER</h2>
        <div class="countdown">7 DAYS ONLY</div>
    </div>
    
    <div class="content">
        <p>As-salamu alaykum <strong>{contact}</strong>!</p>
        
        <p>We're launching Umrah Pro officially next month, and we're inviting 
        <strong>{company}</strong> to join as an <strong>Early Bird Partner</strong>.</p>
        
        <h3>🎁 EARLY BIRD BONUSES:</h3>
        <ul>
            <li>FREE Featured Listings ($500 value)</li>
            <li>Higher Commission Forever ({commission}%)</li>
            <li>Priority Support</li>
            <li>Marketing Package</li>
        </ul>
        
        <center>
            <a href="https://umrahpro.com/agent/early-bird" class="cta-button">
                🎁 CLAIM YOUR EARLY BIRD SPOT
            </a>
        </center>
        
        <p><strong>JazakAllahu Khair,</strong><br>
        Umrah Pro Team</p>
    </div>
</body>
</html>
"""
        
        return subject, html_content
    
    def _log_email(self, to_email, agent_data, template, status, status_code, error=None):
        """Log email sending to database - FIXED VERSION"""
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Create email_logs table with correct structure (8 columns)
        c.execute('''CREATE TABLE IF NOT EXISTS email_logs
                    (log_id TEXT PRIMARY KEY,
                     to_email TEXT,
                     company_name TEXT,
                     template_used TEXT,
                     status TEXT,
                     status_code INTEGER,
                     error TEXT,
                     sent_at TIMESTAMP)''')
        
        log_id = str(uuid.uuid4())
        
        # Insert with 8 values matching 8 columns
        c.execute("""INSERT INTO email_logs VALUES (?,?,?,?,?,?,?,?)""",
                 (log_id, 
                  to_email, 
                  agent_data.get('company_name', ''),
                  template, 
                  status, 
                  status_code, 
                  error, 
                  datetime.now()))
        
        conn.commit()
        conn.close()
    
    def send_bulk_invitations(self, agents_list, template_name="professional"):
        """Send emails to multiple agents"""
        results = {
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        for agent in agents_list:
            result = self.send_agent_invitation(
                agent.get('email'),
                agent,
                template_name
            )
            
            if result['success']:
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'email': agent.get('email'),
                    'error': result.get('error')
                })
        
        return results
    
    def send_welcome_email(self, to_email, agent_data):
        """Send welcome email to new agent after signup"""
        
        try:
            company = agent_data.get('company_name', '[Company Name]')
            contact = agent_data.get('contact_name', '[Contact Name]')
            username = agent_data.get('username', '[Username]')
            
            subject = f"Welcome to Umrah Pro! 🎉 Your Account is Active"
            
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #059669, #10b981);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .welcome-badge {{
            background: white;
            color: #059669;
            padding: 10px 20px;
            border-radius: 20px;
            display: inline-block;
            font-weight: bold;
            margin-top: 10px;
        }}
        .content {{
            background: #ffffff;
            padding: 30px;
            border-radius: 10px;
        }}
        .steps {{
            background: #f0fdf4;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .step {{
            padding: 15px;
            margin: 10px 0;
            background: white;
            border-radius: 8px;
            border-left: 4px solid #059669;
        }}
        .cta-button {{
            display: inline-block;
            background: #059669;
            color: white;
            padding: 15px 40px;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎉 Welcome to Umrah Pro!</h1>
        <div class="welcome-badge">ACCOUNT ACTIVE</div>
    </div>
    
    <div class="content">
        <p>Dear {contact},</p>
        
        <p><strong>As-salamu alaykum and welcome to the Umrah Pro family!</strong></p>
        
        <p>Your agent account for <strong>{company}</strong> is now active and ready to use!</p>
        
        <div class="steps">
            <h3>📋 YOUR NEXT STEPS:</h3>
            
            <div class="step">
                <h4>1️⃣ Login to Your Dashboard (5 min)</h4>
                <p>Username: <strong>{username}</strong></p>
                <p>Access your agent dashboard to get started</p>
            </div>
            
            <div class="step">
                <h4>2️⃣ Complete Your Profile (5 min)</h4>
                <p>• Add company logo</p>
                <p>• Fill in business details</p>
                <p>• Verify bank information for commission payments</p>
            </div>
            
            <div class="step">
                <h4>3️⃣ Create Your First Package (10 min)</h4>
                <p>• Use our easy package builder</p>
                <p>• Add photos and details</p>
                <p>• Set your pricing</p>
            </div>
            
            <div class="step">
                <h4>4️⃣ Start Getting Inquiries!</h4>
                <p>• Your packages go live immediately</p>
                <p>• We'll send you email notifications</p>
                <p>• Track everything in your dashboard</p>
            </div>
        </div>
        
        <center>
            <a href="http://localhost:8503" class="cta-button">
                🚀 Access Your Dashboard
            </a>
        </center>
        
        <h3>🆘 NEED HELP?</h3>
        <p>
            📚 Getting Started Guide: [Link]<br>
            📹 Video Tutorial: [Link]<br>
            💬 WhatsApp Support: +966 XX XXX XXXX<br>
            📧 Email: support@umrahpro.com
        </p>
        
        <h3>🎁 EXCLUSIVE LAUNCH BONUS:</h3>
        <p>As promised, your <strong>first 3 packages will be featured for FREE!</strong></p>
        
        <p>We're excited to have you on board. Let's make this a successful partnership!</p>
        
        <p><strong>JazakAllahu Khair,</strong><br>
        The Umrah Pro Team</p>
    </div>
    
    <div style="text-align: center; color: #666; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
        <p>Umrah Pro - Connecting Pilgrims with Trusted Travel Agencies</p>
        <p>© 2024 Umrah Pro. All rights reserved.</p>
    </div>
</body>
</html>
"""
            
            # Create email
            message = Mail(
                from_email=Email(self.from_email, "Umrah Pro"),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            # Send email
            response = self.sg.send(message)
            
            # Log to database
            self._log_email(to_email, agent_data, "welcome", "sent", response.status_code)
            
            return {
                "success": True,
                "status_code": response.status_code,
                "message": "Welcome email sent successfully!"
            }
        
        except Exception as e:
            # Log error
            self._log_email(to_email, agent_data, "welcome", "failed", 0, str(e))
            
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to send welcome email"
            }