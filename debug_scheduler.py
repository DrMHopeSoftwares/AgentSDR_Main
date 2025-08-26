#!/usr/bin/env python3
"""
Debug version of the scheduler to see what's happening
"""

import os
import sys
import time
from datetime import datetime, timezone, timedelta
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

def get_due_schedules():
    """Get all schedules that are due to run"""
    try:
        print(f"[{datetime.now()}] Checking for due schedules...")
        supabase = get_service_supabase()
        
        # Get current time in UTC
        now = datetime.now(timezone.utc)
        print(f"Current UTC time: {now}")
        
        # Get all active schedules that are due
        response = supabase.table('agent_schedules').select('*').eq('is_active', True).execute()
        print(f"Found {len(response.data)} active schedules")
        
        due_schedules = []
        for schedule in response.data:
            next_run_at = schedule.get('next_run_at')
            print(f"Schedule {schedule['id'][:8]}... next run: {next_run_at}")
            
            if next_run_at:
                next_run_dt = datetime.fromisoformat(next_run_at.replace('Z', '+00:00')).replace(tzinfo=timezone.utc)
                print(f"  Parsed next run: {next_run_dt}")
                
                # Check if it's time to run (within 5 minutes of scheduled time)
                time_diff = (next_run_dt - now).total_seconds()
                print(f"  Time difference: {time_diff} seconds")
                
                # Run if within 5 minutes of scheduled time
                if -300 <= time_diff <= 300:  # 5 minutes window
                    print(f"  Schedule is due! (within 5-minute window)")
                    last_run = schedule.get('last_run_at')
                    if last_run:
                        last_run_dt = datetime.fromisoformat(last_run.replace('Z', '+00:00')).replace(tzinfo=timezone.utc)
                        hours_since_last = (now - last_run_dt).total_seconds() / 3600
                        print(f"  Last run: {last_run_dt} ({hours_since_last:.1f} hours ago)")
                        # Only run if last run was more than 1 hour ago (to avoid duplicates)
                        if (now - last_run_dt).total_seconds() > 3600:  # 1 hour
                            print(f"  Adding to due list (last run > 1 hour ago)")
                            due_schedules.append(schedule)
                        else:
                            print(f"  Skipping (last run < 1 hour ago)")
                    else:
                        # Never run before
                        print(f"  Adding to due list (never run before)")
                        due_schedules.append(schedule)
                else:
                    print(f"  Not due yet (outside 5-minute window)")
        
        print(f"Total due schedules: {len(due_schedules)}")
        return due_schedules
        
    except Exception as e:
        print(f"Error getting due schedules: {e}")
        import traceback
        traceback.print_exc()
        return []

# Test once
with app.app_context():
    print("=== DEBUG SCHEDULER RUN ===")
    due_schedules = get_due_schedules()
    
    if due_schedules:
        print("Found due schedules - would execute now!")
        for schedule in due_schedules:
            print(f"Would execute: {schedule['recipient_email']}")
    else:
        print("No schedules due at this time")