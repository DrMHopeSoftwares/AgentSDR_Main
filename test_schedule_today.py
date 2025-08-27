#!/usr/bin/env python3
"""
Set up a test schedule for TODAY to verify scheduler is working
"""

import os
import sys
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

def setup_test_schedule_today():
    """Set up a test schedule for 10 minutes from now"""
    print("=== SETTING UP TEST SCHEDULE FOR TODAY ===")
    
    with app.app_context():
        from agentsdr.core.supabase_client import get_service_supabase
        
        try:
            supabase = get_service_supabase()
            
            # Get current schedule
            response = supabase.table('agent_schedules').select('*').execute()
            if not response.data:
                print("ERROR: No schedules found")
                return False
            
            schedule = response.data[0]
            print(f"Found schedule: {schedule['id'][:8]}...")
            
            # Calculate a time 10 minutes from now (in UTC)
            now_utc = datetime.now(timezone.utc)
            test_time_utc = now_utc + timedelta(minutes=10)
            
            # Also calculate local time for display
            now_local = datetime.now()
            test_time_local = now_local + timedelta(minutes=10)
            
            print(f"Current UTC time: {now_utc}")
            print(f"Current local time: {now_local}")
            print(f"Test schedule UTC time: {test_time_utc}")
            print(f"Test schedule local time: {test_time_local}")
            print()
            
            # Update the schedule for testing
            update_data = {
                'next_run_at': test_time_utc.isoformat(),
                'is_active': True,  # Make sure it's active
                'updated_at': now_utc.isoformat(),
                'schedule_time': f"{test_time_local.hour:02d}:{test_time_local.minute:02d}:00"  # Update display time
            }
            
            result = supabase.table('agent_schedules').update(update_data).eq('id', schedule['id']).execute()
            
            if result.data:
                print("SUCCESS: Test schedule set!")
                print(f"Email should be sent at: {test_time_local.strftime('%H:%M:%S')} local time")
                print(f"That's in about 10 minutes")
                print()
                print("IMPORTANT:")
                print("1. Make sure Railway has ENABLE_SCHEDULER=true")
                print("2. Check Railway logs for scheduler messages")
                print("3. Watch your email (and spam folder) in 10 minutes")
                return True
            else:
                print("ERROR: Failed to update schedule")
                return False
                
        except Exception as e:
            print(f"ERROR: {e}")
            return False

if __name__ == "__main__":
    setup_test_schedule_today()