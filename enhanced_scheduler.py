#!/usr/bin/env python3
"""
Enhanced Automated Email Summarization Scheduler

This script runs in the background and executes scheduled email summarization tasks
with support for daily, weekly, and monthly schedules with flexible email criteria.
"""

import os
import sys
import time
from datetime import datetime, timedelta, timezone
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
from agentsdr.services.gmail_service import GmailService, fetch_and_summarize_emails
from agentsdr.core.email import send_email_summary

def get_due_schedules():
    """Get all schedules that are due to run"""
    try:
        supabase = get_service_supabase()
        
        # Get current time in UTC
        now = datetime.now(timezone.utc)
        
        # Get all active schedules that are due
        response = supabase.table('agent_schedules').select('*').eq('is_active', True).execute()
        
        due_schedules = []
        for schedule in response.data:
            next_run_at = schedule.get('next_run_at')
            
            if next_run_at:
                next_run_dt = datetime.fromisoformat(next_run_at.replace('Z', '+00:00')).replace(tzinfo=timezone.utc)
                
                # Check if it's time to run (within 5 minutes of scheduled time)
                time_diff = (next_run_dt - now).total_seconds()
                
                # Run if within 5 minutes of scheduled time
                if -300 <= time_diff <= 300:  # 5 minutes window
                    last_run = schedule.get('last_run_at')
                    if last_run:
                        last_run_dt = datetime.fromisoformat(last_run.replace('Z', '+00:00')).replace(tzinfo=timezone.utc)
                        # Only run if last run was more than 10 minutes ago (to avoid duplicates)
                        if (now - last_run_dt).total_seconds() > 600:  # 10 minutes
                            due_schedules.append(schedule)
                    else:
                        # Never run before
                        due_schedules.append(schedule)
        
        return due_schedules
        
    except Exception as e:
        print(f"Error getting due schedules: {e}")
        return []

def calculate_next_run_time(schedule):
    """Calculate the next run time for a schedule after execution"""
    schedule_time = schedule['schedule_time']
    frequency_type = schedule.get('frequency_type', 'daily')
    day_of_week = schedule.get('day_of_week')
    day_of_month = schedule.get('day_of_month')
    
    now = datetime.now(timezone.utc)
    
    if frequency_type == 'once':
        # One-time schedules don't repeat - set to None to disable
        return None
    
    hour, minute = map(int, schedule_time.split(':'))
    
    if frequency_type == 'daily':
        # Next run is tomorrow
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=1)
    
    elif frequency_type == 'weekly':
        # Next run is next week on the same day
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=7)
    
    elif frequency_type == 'monthly':
        # Next run is next month on the same day
        if now.month == 12:
            next_run = now.replace(year=now.year + 1, month=1, hour=hour, minute=minute, second=0, microsecond=0)
        else:
            next_month = now.month + 1
            # Handle months with fewer than 31 days
            import calendar
            max_day = calendar.monthrange(now.year, next_month)[1]
            day = min(day_of_month, max_day)
            next_run = now.replace(month=next_month, day=day, hour=hour, minute=minute, second=0, microsecond=0)
    
    return next_run

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
        
        # Prepare email criteria parameters
        criteria_type = schedule.get('criteria_type', 'last_24_hours')
        email_count = schedule.get('email_count', 50)  # Default to 50 emails
        email_hours = schedule.get('email_hours')
        
        print(f"Fetching emails with criteria: {criteria_type}, count: {email_count}, hours: {email_hours}")
        
        # Fetch and summarize emails with new parameters
        summaries = fetch_and_summarize_emails(
            refresh_token=refresh_token,
            criteria_type=criteria_type,
            count=email_count,
            hours=email_hours
        )
        
        if not summaries:
            print(f"No emails found for agent {schedule['agent_id']}")
            # Still update timestamps to avoid repeated attempts
            update_schedule_after_run(supabase, schedule)
            return True
        
        # Send email summary
        success = send_email_summary(
            recipient_email=schedule['recipient_email'],
            summaries=summaries,
            agent_name=agent['name'],
            criteria_type=criteria_type
        )
        
        if success:
            update_schedule_after_run(supabase, schedule)
            print(f"Successfully sent email summary to {schedule['recipient_email']}")
            return True
        else:
            print(f"Failed to send email summary to {schedule['recipient_email']}")
            return False
            
    except Exception as e:
        print(f"Error executing schedule {schedule['id']}: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_schedule_after_run(supabase, schedule):
    """Update schedule timestamps and calculate next run time"""
    try:
        now = datetime.now(timezone.utc)
        next_run = calculate_next_run_time(schedule)
        
        update_data = {
            'last_run_at': now.isoformat()
        }
        
        if next_run is None:
            # One-time schedule - disable after execution
            update_data['is_active'] = False
            update_data['next_run_at'] = None
            print(f"One-time schedule {schedule['id']} completed and disabled")
        else:
            update_data['next_run_at'] = next_run.isoformat()
            print(f"Updated schedule {schedule['id']} - next run: {next_run}")
        
        supabase.table('agent_schedules').update(update_data).eq('id', schedule['id']).execute()
        
    except Exception as e:
        print(f"Error updating schedule timestamps: {e}")

def run_scheduler():
    """Main scheduler loop"""
    print(f"Enhanced Scheduler started at {datetime.now()}")
    print("Monitoring for daily, weekly, and monthly schedules...")
    
    while True:
        try:
            with app.app_context():
                # Get due schedules
                due_schedules = get_due_schedules()
                
                if due_schedules:
                    print(f"Found {len(due_schedules)} due schedules")
                    
                    for schedule in due_schedules:
                        frequency = schedule.get('frequency_type', 'daily')
                        criteria = schedule.get('criteria_type', 'last_24_hours')
                        print(f"Executing {frequency} {criteria} schedule for agent {schedule['agent_id']}")
                        execute_schedule(schedule)
                else:
                    print("No due schedules found")
            
            # Wait 2 minutes before next check (more frequent than original)
            time.sleep(120)
            
        except KeyboardInterrupt:
            print("Enhanced scheduler stopped by user")
            break
        except Exception as e:
            print(f"Scheduler error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(60)  # Wait 1 minute before retrying

if __name__ == '__main__':
    run_scheduler()