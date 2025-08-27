#!/usr/bin/env python3
"""
Update schedule to tomorrow 8:00 AM local time
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

def update_schedule_for_tomorrow():
    """Update your schedule for tomorrow 8:00 AM"""
    print("=== UPDATING SCHEDULE FOR TOMORROW ===")
    
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
            print(f"Current next_run_at: {schedule.get('next_run_at')}")
            
            # Calculate tomorrow 8:00 AM local time in UTC
            # You're in UTC+5:30, so 8:00 AM local = 2:30 AM UTC
            tomorrow = datetime.now().date() + timedelta(days=1)
            tomorrow_8am_local = datetime.combine(tomorrow, datetime.min.time().replace(hour=8, minute=0))
            
            # Convert to UTC (subtract 5 hours 30 minutes)
            tomorrow_8am_utc = tomorrow_8am_local - timedelta(hours=5, minutes=30)
            
            print(f"Tomorrow 8:00 AM local: {tomorrow_8am_local}")
            print(f"Tomorrow 8:00 AM UTC   : {tomorrow_8am_utc}")
            
            # Update the schedule
            update_data = {
                'next_run_at': tomorrow_8am_utc.isoformat(),
                'is_active': True,  # Make sure it's active
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            result = supabase.table('agent_schedules').update(update_data).eq('id', schedule['id']).execute()
            
            if result.data:
                print("SUCCESS: Schedule updated!")
                print(f"Next email will be sent at: {tomorrow_8am_local} (local time)")
                print("Make sure your Railway app has ENABLE_SCHEDULER=true")
                return True
            else:
                print("ERROR: Failed to update schedule")
                return False
                
        except Exception as e:
            print(f"ERROR: {e}")
            return False

if __name__ == "__main__":
    update_schedule_for_tomorrow()