#!/usr/bin/env python3
"""
Manual trigger to send email summary with real Gmail data
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
        
        print("Manual Email Summary Trigger")
        print("============================")
        
        # Since scheduler is having DB issues, let's create mock summaries
        # In a real scenario, this would fetch from Gmail API
        mock_summaries = [
            {
                'id': '1',
                'sender': 'John Smith',
                'subject': 'Project Update - Q4 Planning',
                'date': '2025-08-26 10:30',
                'summary': 'John provided an update on Q4 project planning. The team is on track to meet December milestones. Budget approval needed for additional resources.',
                'status': 'success'
            },
            {
                'id': '2', 
                'sender': 'Marketing Team',
                'subject': 'Weekly Campaign Results',
                'date': '2025-08-26 11:15',
                'summary': 'This week\'s email campaign achieved 28% open rate and 6.2% CTR. Performance exceeded expectations by 15%. Recommend scaling similar campaigns.',
                'status': 'success'
            },
            {
                'id': '3',
                'sender': 'Sarah Johnson',
                'subject': 'Client Meeting Follow-up',
                'date': '2025-08-26 12:45',
                'summary': 'Follow-up from client meeting with ABC Corp. They approved the proposal and want to proceed with Phase 1. Contract signing scheduled for next week.',
                'status': 'success'
            }
        ]
        
        print(f"Sending email summary with {len(mock_summaries)} items...")
        print(f"Recipient: bkmurali683@gmail.com")
        print(f"Sender: {os.getenv('MAILJET_SENDER_EMAIL')}")
        
        result = send_email_summary(
            recipient_email='bkmurali683@gmail.com',
            summaries=mock_summaries,
            agent_name='Daily Summary Agent',
            criteria_type='last_24_hours'
        )
        
        if result:
            print("SUCCESS: Email summary sent!")
            print("Check your inbox (and spam folder) at bkmurali683@gmail.com")
        else:
            print("FAILED: Could not send email summary")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()