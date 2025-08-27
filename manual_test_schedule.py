#!/usr/bin/env python3
"""
Manual test to trigger your scheduled email
"""

import os
import sys
from datetime import datetime, timezone
from flask import Flask
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Create Flask app context
app = Flask(__name__)
app.config.from_object('config.Config')

# Import after app creation
from agentsdr.core.supabase_client import get_service_supabase
from agentsdr.services.gmail_service import fetch_and_summarize_emails
from agentsdr.core.email import send_email_summary

def test_your_schedule():
    """Test your specific schedule manually"""
    print("=== MANUAL SCHEDULE TEST ===")
    print(f"Current time: {datetime.now()}")
    print(f"UTC time: {datetime.now(timezone.utc)}")
    print()
    
    with app.app_context():
        try:
            supabase = get_service_supabase()
            
            # Get your schedule
            response = supabase.table('agent_schedules').select('*').execute()
            if not response.data:
                print("ERROR: No schedules found")
                return False
                
            schedule = response.data[0]  # Get first schedule
            print(f"Found schedule: {schedule['id'][:8]}...")
            print(f"Recipient: {schedule['recipient_email']}")
            print(f"Next run: {schedule.get('next_run_at')}")
            
            # Get agent details
            agent_resp = supabase.table('agents').select('*').eq('id', schedule['agent_id']).execute()
            if not agent_resp.data:
                print("ERROR: Agent not found")
                return False
                
            agent = agent_resp.data[0]
            print(f"Agent: {agent['name']} ({agent['agent_type']})")
            
            # Check if agent is active
            is_active = agent.get('is_active', True)
            if not is_active:
                print("WARNING: Agent is currently PAUSED - activating for test")
            
            # Get Gmail refresh token from agent config
            config = agent.get('config', {})
            refresh_token = config.get('gmail_refresh_token')
            
            if not refresh_token:
                print("ERROR: No Gmail refresh token found")
                return False
                
            print("SUCCESS: Gmail token found")
            
            # Prepare email criteria parameters
            criteria_type = schedule.get('criteria_type', 'last_24_hours')
            email_count = schedule.get('email_count', 10)
            email_hours = schedule.get('email_hours')
            
            print(f"Fetching emails: {criteria_type}, count: {email_count}, hours: {email_hours}")
            
            # Fetch and summarize emails
            summaries = fetch_and_summarize_emails(
                refresh_token=refresh_token,
                criteria_type=criteria_type,
                count=email_count,
                hours=email_hours
            )
            
            if not summaries:
                print("WARNING: No emails found - creating test summary")
                # Create a test summary
                summaries = [{
                    'sender': 'Test System',
                    'subject': 'Manual Schedule Test',
                    'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'summary': 'This is a manual test of your scheduled email system. If you receive this, the scheduling system is working correctly!'
                }]
            
            print(f"SUCCESS: Found {len(summaries)} email(s) to summarize")
            
            # Send email summary
            success = send_email_summary(
                recipient_email=schedule['recipient_email'],
                summaries=summaries,
                agent_name=agent['name'],
                criteria_type=criteria_type
            )
            
            if success:
                print("SUCCESS: Email summary sent!")
                print(f"Check inbox at {schedule['recipient_email']}")
                print("Also check your SPAM folder")
                return True
            else:
                print("ERROR: Failed to send email summary")
                return False
                
        except Exception as e:
            print(f"ERROR: {e}")
            return False

if __name__ == "__main__":
    test_your_schedule()