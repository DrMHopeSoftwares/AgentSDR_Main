import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, render_template_string
from typing import Optional
import os
from datetime import datetime
from mailjet_rest import Client


class EmailService:
    def __init__(self):
        self.smtp_host = current_app.config.get('SMTP_HOST')
        self.smtp_port = current_app.config.get('SMTP_PORT')
        self.smtp_user = current_app.config.get('SMTP_USER')
        self.smtp_pass = current_app.config.get('SMTP_PASS')
        self.smtp_use_tls = current_app.config.get('SMTP_USE_TLS', True)
    
    def send_invitation_email(self, email: str, org_name: str, role: str, token: str, invited_by: str) -> bool:
        """Send invitation email to user"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Invitation to join {org_name} on AgentSDR"
            msg['From'] = self.smtp_user
            msg['To'] = email
            
            # Create the HTML content
            html_content = self._get_invitation_email_template(org_name, role, token, invited_by)
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                if self.smtp_user and self.smtp_pass:
                    server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)
            
            return True
        except Exception as e:
            current_app.logger.error(f"Failed to send invitation email: {e}")
            return False
    
    def _get_invitation_email_template(self, org_name: str, role: str, token: str, invited_by: str) -> str:
        """Get the invitation email HTML template"""
        base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
        accept_url = f"{base_url}/invite/accept?token={token}"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Invitation to join {org_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #3b82f6; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
                .button {{ display: inline-block; background: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>AgentSDR</h1>
                </div>
                <div class="content">
                    <h2>You're invited to join {org_name}</h2>
                    <p>Hello!</p>
                    <p>You've been invited by <strong>{invited_by}</strong> to join <strong>{org_name}</strong> on AgentSDR as a <strong>{role}</strong>.</p>
                    <p>AgentSDR is a powerful platform for managing your organization's data and workflows.</p>
                    <p style="text-align: center;">
                        <a href="{accept_url}" class="button">Accept Invitation</a>
                    </p>
                    <p><strong>What happens next?</strong></p>
                    <ul>
                        <li>Click the button above to accept the invitation</li>
                        <li>If you don't have an account, you'll be guided to create one</li>
                        <li>Once you accept, you'll have access to {org_name}'s workspace</li>
                    </ul>
                    <p><strong>Important:</strong> This invitation will expire in 72 hours for security reasons.</p>
                    <p>If you have any questions, please contact the person who invited you.</p>
                </div>
                <div class="footer">
                    <p>This invitation was sent from AgentSDR</p>
                    <p>If you didn't expect this invitation, you can safely ignore this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def send_welcome_email(self, email: str, org_name: str) -> bool:
        """Send welcome email after invitation acceptance"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Welcome to {org_name} on AgentSDR"
            msg['From'] = self.smtp_user
            msg['To'] = email
            
            html_content = self._get_welcome_email_template(org_name)
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                if self.smtp_user and self.smtp_pass:
                    server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)
            
            return True
        except Exception as e:
            current_app.logger.error(f"Failed to send welcome email: {e}")
            return False
    
    def _get_welcome_email_template(self, org_name: str) -> str:
        """Get the welcome email HTML template"""
        base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to {org_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #10b981; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
                .button {{ display: inline-block; background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to AgentSDR!</h1>
                </div>
                <div class="content">
                    <h2>You're now a member of {org_name}</h2>
                    <p>Congratulations! You've successfully joined <strong>{org_name}</strong> on AgentSDR.</p>
                    <p>You can now access your organization's workspace and start collaborating with your team.</p>
                    <p style="text-align: center;">
                        <a href="{base_url}/dashboard" class="button">Go to Dashboard</a>
                    </p>
                    <p><strong>What you can do now:</strong></p>
                    <ul>
                        <li>View and manage your organization's records</li>
                        <li>Collaborate with team members</li>
                        <li>Access organization settings (if you're an admin)</li>
                        <li>Invite new members (if you're an admin)</li>
                    </ul>
                    <p>If you have any questions or need help getting started, don't hesitate to reach out to your organization's admin.</p>
                </div>
                <div class="footer">
                    <p>Welcome to the AgentSDR community!</p>
                </div>
            </div>
        </body>
        </html>
        """

# Global email service instances - will be initialized when needed
email_service = None
mailjet_service = None

def get_email_service():
    global email_service
    if email_service is None:
        email_service = EmailService()
    return email_service

def get_mailjet_service():
    global mailjet_service
    if mailjet_service is None:
        mailjet_service = MailjetService()
    return mailjet_service

class MailjetService:
    def __init__(self):
        self.api_key = os.getenv('MAILJET_API_KEY')
        self.api_secret = os.getenv('MAILJET_API_SECRET')
        self.sender_email = os.getenv('MAILJET_SENDER_EMAIL')
        self.sender_name = os.getenv('MAILJET_SENDER_NAME', 'AgentSDR')
        
        if self.api_key and self.api_secret:
            self.client = Client(auth=(self.api_key, self.api_secret), version='v3.1')
        else:
            self.client = None
            current_app.logger.warning("Mailjet credentials not configured")
    
    def send_email_summary(self, recipient_email, summaries, agent_name, criteria_type):
        """Send email summary using Mailjet API"""
        if not self.client:
            current_app.logger.error("Mailjet client not initialized - check API credentials")
            return False
        
        try:
            # Generate HTML content
            html_content = self._generate_summary_html(summaries, agent_name, criteria_type)
            
            # Prepare email data
            data = {
                'Messages': [
                    {
                        "From": {
                            "Email": self.sender_email,
                            "Name": self.sender_name
                        },
                        "To": [
                            {
                                "Email": recipient_email
                            }
                        ],
                        "Subject": f"📧 Email Summary - {agent_name}",
                        "HTMLPart": html_content,
                        "CustomID": f"EmailSummary-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                    }
                ]
            }
            
            # Send email
            result = self.client.send.create(data=data)
            
            if result.status_code == 200:
                current_app.logger.info(f"Email summary sent successfully to {recipient_email}")
                return True
            else:
                current_app.logger.error(f"Failed to send email: {result.status_code} - {result.json()}")
                return False
                
        except Exception as e:
            current_app.logger.error(f"Error sending email with Mailjet: {e}")
            return False
    
    def _generate_summary_html(self, summaries, agent_name, criteria_type):
        """Generate HTML content for email summary"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Email Summary - {agent_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px; }}
                .summary-item {{ background: #f8f9fa; border-left: 4px solid #667eea; padding: 20px; margin-bottom: 20px; border-radius: 5px; }}
                .sender {{ font-weight: bold; color: #667eea; margin-bottom: 5px; }}
                .subject {{ font-weight: bold; margin-bottom: 10px; }}
                .date {{ color: #666; font-size: 0.9em; margin-bottom: 10px; }}
                .summary {{ background: white; padding: 15px; border-radius: 5px; border: 1px solid #e9ecef; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 0.9em; }}
                .stats {{ background: #e3f2fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; text-align: center; }}
                .powered-by {{ background: #f0f0f0; padding: 10px; border-radius: 5px; text-align: center; margin-top: 20px; font-size: 0.8em; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📧 Email Summary</h1>
                <p>Your automated email digest from {agent_name}</p>
            </div>
            
            <div class="stats">
                <h3>📊 Summary Statistics</h3>
                <p><strong>{len(summaries)} emails</strong> summarized from the <strong>{criteria_type.replace('_', ' ').title()}</strong></p>
                <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            </div>
        """
        
        # Add each summary
        for i, summary in enumerate(summaries, 1):
            html_content += f"""
            <div class="summary-item">
                <div class="sender">👤 {summary.get('sender', 'Unknown Sender')}</div>
                <div class="subject">📝 {summary.get('subject', 'No Subject')}</div>
                <div class="date">📅 {summary.get('date', 'Unknown Date')}</div>
                <div class="summary">
                    {summary.get('summary', 'No summary available')}
                </div>
            </div>
            """
        
        html_content += """
            <div class="footer">
                <p>This is an automated summary generated by your AgentSDR email summarizer.</p>
                <p>You can manage your email preferences in your AgentSDR dashboard.</p>
            </div>
            <div class="powered-by">
                <p>📧 Powered by Mailjet Email Service</p>
            </div>
        </body>
        </html>
        """
        
        return html_content


def send_email_summary(recipient_email, summaries, agent_name, criteria_type):
    """Send email summary to user using Mailjet (with SMTP fallback)"""
    try:
        # Try Mailjet first
        use_mailjet = os.getenv('USE_MAILJET', 'true').lower() == 'true'
        
        if use_mailjet:
            mailjet_service = MailjetService()
            result = mailjet_service.send_email_summary(recipient_email, summaries, agent_name, criteria_type)
            if result:
                return True
            else:
                current_app.logger.warning("Mailjet failed, falling back to SMTP")
        
        # Fallback to SMTP
        return _send_email_summary_smtp(recipient_email, summaries, agent_name, criteria_type)
        
    except Exception as e:
        current_app.logger.error(f"Failed to send email summary: {e}")
        return False


def _send_email_summary_smtp(recipient_email, summaries, agent_name, criteria_type):
    """Send email summary using SMTP (fallback method)"""
    try:
        # Email configuration
        smtp_host = os.getenv('SMTP_HOST', 'localhost')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_user = os.getenv('SMTP_USER')
        smtp_pass = os.getenv('SMTP_PASS')
        smtp_use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        
        if not all([smtp_host, smtp_user, smtp_pass]):
            current_app.logger.error("SMTP configuration incomplete")
            return False
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"📧 Email Summary - {agent_name}"
        msg['From'] = smtp_user
        msg['To'] = recipient_email
        
        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Email Summary</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px; }}
                .summary-item {{ background: #f8f9fa; border-left: 4px solid #667eea; padding: 20px; margin-bottom: 20px; border-radius: 5px; }}
                .sender {{ font-weight: bold; color: #667eea; margin-bottom: 5px; }}
                .subject {{ font-weight: bold; margin-bottom: 10px; }}
                .date {{ color: #666; font-size: 0.9em; margin-bottom: 10px; }}
                .summary {{ background: white; padding: 15px; border-radius: 5px; border: 1px solid #e9ecef; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 0.9em; }}
                .stats {{ background: #e3f2fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📧 Email Summary</h1>
                <p>Your automated email digest from {agent_name}</p>
            </div>
            
            <div class="stats">
                <h3>📊 Summary Statistics</h3>
                <p><strong>{len(summaries)} emails</strong> summarized from the <strong>{criteria_type.replace('_', ' ').title()}</strong></p>
                <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            </div>
        """
        
        # Add each summary
        for i, summary in enumerate(summaries, 1):
            html_content += f"""
            <div class="summary-item">
                <div class="sender">👤 {summary.get('sender', 'Unknown Sender')}</div>
                <div class="subject">📝 {summary.get('subject', 'No Subject')}</div>
                <div class="date">📅 {summary.get('date', 'Unknown Date')}</div>
                <div class="summary">
                    {summary.get('summary', 'No summary available')}
                </div>
            </div>
            """
        
        html_content += """
            <div class="footer">
                <p>This is an automated summary generated by your AgentSDR email summarizer.</p>
                <p>You can manage your email preferences in your AgentSDR dashboard.</p>
            </div>
        </body>
        </html>
        """
        
        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if smtp_use_tls:
                server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        
        current_app.logger.info(f"Email summary sent via SMTP to {recipient_email}")
        return True
        
    except Exception as e:
        current_app.logger.error(f"Failed to send email summary via SMTP: {e}")
        return False
