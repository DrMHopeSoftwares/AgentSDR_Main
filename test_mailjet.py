#!/usr/bin/env python3
"""
Quick test script for Mailjet integration
"""

import os
import sys
from flask import Flask
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Create Flask app context
app = Flask(__name__)
app.config.from_object('config.Config')

# Test within app context
with app.app_context():
    try:
        from agentsdr.core.email import send_email_summary
        
        # Test data
        test_summaries = [{
            'sender': 'Test User',
            'subject': 'Manual Test Email',
            'date': '2025-08-26 13:57',
            'summary': 'This is a manual test to verify Mailjet integration is working. If you receive this email, the integration is successful!'
        }]
        
        print("Testing Mailjet email sending...")
        print(f"Sender: {os.getenv('MAILJET_SENDER_EMAIL')}")
        print(f"Recipient: bkmurali683@gmail.com")
        
        result = send_email_summary(
            recipient_email='bkmurali683@gmail.com',
            summaries=test_summaries,
            agent_name='Manual Test Agent',
            criteria_type='manual_test'
        )
        
        if result:
            print("SUCCESS: Test email sent successfully!")
            print("Check your inbox at bkmurali683@gmail.com")
        else:
            print("FAILED: Could not send test email")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()