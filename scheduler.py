#!/usr/bin/env python3
"""
Automated Email Summarization Scheduler

This script runs in the background and executes scheduled email summarization tasks.
It should be run as a cron job or background service.
"""

import os
import sys
import time
from datetime import datetime, timedelta
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
from agentsdr.services.gmail_service import GmailService
from agentsdr.core.email import send_email_summary

def get_due_schedules():
    """Get all schedules that are due to run"""
    try:
        supabase = get_service_supabase()
        
        # Get current time in UTC
        now = datetime.utcnow()
        current_time = now.strftime('%H:%M:%S')
        
        # Get all active schedules
        response = supabase.table('agent_schedules').select('*').eq('is_active', True).execute()
        
        due_schedules = []
        for schedule in response.data:
            schedule_time = schedule['schedule_time']
            
            # Check if it's time to run (within 5 minutes of scheduled time)
            scheduled_hour, scheduled_minute = map(int, schedule_time.split(':'))
            scheduled_datetime = now.replace(hour=scheduled_hour, minute=scheduled_minute, second=0, microsecond=0)
            
            # Check if we should run this schedule
            time_diff = abs((now - scheduled_datetime).total_seconds())
            
            # Run if within 5 minutes of scheduled time and hasn't run today
            if time_diff <= 300:  # 5 minutes = 300 seconds
                last_run = schedule.get('last_run_at')
                if last_run:
                    last_run_dt = datetime.fromisoformat(last_run.replace('Z', '+00:00'))
                    # Only run if last run was more than 23 hours ago (to avoid duplicates)
                    if (now - last_run_dt).total_seconds() > 82800:  # 23 hours
                        due_schedules.append(schedule)
                else:
                    # Never run before
                    due_schedules.append(schedule)
        
        return due_schedules
        
    except Exception as e:
        print(f"Error getting due schedules: {e}")
        return []

def execute_schedule(schedule):
    """Execute a single scheduled task"""
    try:
        print(f"Executing schedule for agent {schedule['agent_id']}")
        
        supabase = get_service_supabase()
        
        # Get agent details
        agent_resp = supabase.table('agents').select('*').eq('id', schedule['agent_id']).execute()
        if not agent_resp.data:
            print(f"Agent {schedule['agent_id']} not found")
            return False
        
        agent = agent_resp.data[0]
        
        # Get Gmail refresh token from agent config
        config = agent.get('config', {})
        refresh_token = config.get('gmail_refresh_token')
        
        if not refresh_token:
            print(f"No Gmail refresh token found for agent {schedule['agent_id']}")
            return False
        
        # Initialize Gmail service
        gmail_service = GmailService()
        
        # Fetch and summarize emails
        summaries = gmail_service.fetch_and_summarize_emails(
            refresh_token=refresh_token,
            criteria_type=schedule['criteria_type'],
            count=50  # Default to 50 emails for daily summaries
        )
        
        if not summaries:
            print(f"No emails found for agent {schedule['agent_id']}")
            # Still update last_run_at to avoid repeated attempts
            supabase.table('agent_schedules').update({
                'last_run_at': datetime.utcnow().isoformat()
            }).eq('id', schedule['id']).execute()
            return True
        
        # Send email summary
        success = send_email_summary(
            recipient_email=schedule['recipient_email'],
            summaries=summaries,
            agent_name=agent['name'],
            criteria_type=schedule['criteria_type']
        )
        
        if success:
            # Update last_run_at
            supabase.table('agent_schedules').update({
                'last_run_at': datetime.utcnow().isoformat()
            }).eq('id', schedule['id']).execute()
            
            print(f"Successfully sent email summary to {schedule['recipient_email']}")
            return True
        else:
            print(f"Failed to send email summary to {schedule['recipient_email']}")
            return False
            
    except Exception as e:
        print(f"Error executing schedule {schedule['id']}: {e}")
        return False

def run_scheduler():
    """Main scheduler loop"""
    print(f"Scheduler started at {datetime.now()}")
    
    while True:
        try:
            with app.app_context():
                # Get due schedules
                due_schedules = get_due_schedules()
                
                if due_schedules:
                    print(f"Found {len(due_schedules)} due schedules")
                    
                    for schedule in due_schedules:
                        execute_schedule(schedule)
                else:
                    print("No due schedules found")
            
            # Wait 5 minutes before next check
            time.sleep(300)
            
        except KeyboardInterrupt:
            print("Scheduler stopped by user")
            break
        except Exception as e:
            print(f"Scheduler error: {e}")
            time.sleep(60)  # Wait 1 minute before retrying

if __name__ == '__main__':
    run_scheduler()
