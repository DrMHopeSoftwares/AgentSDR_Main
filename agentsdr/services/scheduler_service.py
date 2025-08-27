"""
Background Email Scheduler Service for Railway Deployment
"""

import threading
import time
import logging
from datetime import datetime, timezone, timedelta
from flask import current_app
from agentsdr.core.supabase_client import get_service_supabase
from agentsdr.services.gmail_service import fetch_and_summarize_emails
from agentsdr.core.email import send_email_summary

class SchedulerService:
    def __init__(self, app=None):
        self.app = app
        self.running = False
        self.thread = None
        self.logger = None
        
    def init_app(self, app):
        """Initialize the scheduler with Flask app"""
        self.app = app
        self.logger = app.logger
        
    def start(self):
        """Start the background scheduler"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.thread.start()
        
        if self.logger:
            self.logger.info("✅ Email Scheduler Service started")
        
    def stop(self):
        """Stop the background scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        if self.logger:
            self.logger.info("⏹️ Email Scheduler Service stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop - runs every minute"""
        while self.running:
            try:
                with self.app.app_context():
                    self._check_and_execute_schedules()
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Scheduler error: {e}")
            
            # Sleep for 60 seconds between checks
            time.sleep(60)
    
    def _check_and_execute_schedules(self):
        """Check for due schedules and execute them"""
        try:
            supabase = get_service_supabase()
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
            
            # Execute due schedules
            for schedule in due_schedules:
                success = self._execute_schedule(schedule)
                if success and self.logger:
                    self.logger.info(f"✅ Executed schedule {schedule['id'][:8]}... for {schedule['recipient_email']}")
                    
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error checking schedules: {e}")
    
    def _execute_schedule(self, schedule):
        """Execute a single schedule"""
        try:
            supabase = get_service_supabase()
            
            # Get agent details
            agent_resp = supabase.table('agents').select('*').eq('id', schedule['agent_id']).execute()
            if not agent_resp.data:
                if self.logger:
                    self.logger.error(f"Agent {schedule['agent_id']} not found")
                return False
            
            agent = agent_resp.data[0]
            
            # Check if agent is active
            is_active = agent.get('is_active', True)
            if not is_active:
                if self.logger:
                    self.logger.info(f"Agent {schedule['agent_id']} is paused - skipping execution")
                return False
            
            # Get Gmail refresh token from agent config
            config = agent.get('config', {})
            refresh_token = config.get('gmail_refresh_token')
            
            if not refresh_token:
                if self.logger:
                    self.logger.error(f"No Gmail refresh token found for agent {schedule['agent_id']}")
                return False
            
            # Prepare email criteria parameters
            criteria_type = schedule.get('criteria_type', 'last_24_hours')
            email_count = schedule.get('email_count', 50)
            email_hours = schedule.get('email_hours')
            
            # Fetch and summarize emails
            summaries = fetch_and_summarize_emails(
                refresh_token=refresh_token,
                criteria_type=criteria_type,
                count=email_count,
                hours=email_hours
            )
            
            if not summaries:
                if self.logger:
                    self.logger.info(f"No emails found for agent {schedule['agent_id']}")
                # Still update timestamps to avoid repeated attempts
                self._update_schedule_after_run(supabase, schedule)
                return True
            
            # Send email summary
            success = send_email_summary(
                recipient_email=schedule['recipient_email'],
                summaries=summaries,
                agent_name=agent['name'],
                criteria_type=criteria_type
            )
            
            if success:
                self._update_schedule_after_run(supabase, schedule)
                if self.logger:
                    self.logger.info(f"Successfully sent email summary to {schedule['recipient_email']}")
                return True
            else:
                if self.logger:
                    self.logger.error(f"Failed to send email summary to {schedule['recipient_email']}")
                return False
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error executing schedule {schedule.get('id', 'unknown')}: {e}")
            return False
    
    def _update_schedule_after_run(self, supabase, schedule):
        """Update schedule timestamps after execution"""
        try:
            now = datetime.now(timezone.utc)
            
            # Calculate next run time
            next_run_time = self._calculate_next_run_time(schedule)
            
            update_data = {
                'last_run_at': now.isoformat(),
                'updated_at': now.isoformat()
            }
            
            if next_run_time:
                update_data['next_run_at'] = next_run_time.isoformat()
            else:
                # One-time schedule - disable it
                update_data['is_active'] = False
            
            supabase.table('agent_schedules').update(update_data).eq('id', schedule['id']).execute()
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error updating schedule: {e}")
    
    def _calculate_next_run_time(self, schedule):
        """Calculate the next run time for a schedule after execution"""
        schedule_time = schedule['schedule_time']
        frequency_type = schedule.get('frequency_type', 'daily')
        
        now = datetime.now(timezone.utc)
        
        if frequency_type == 'once':
            # One-time schedules don't repeat
            return None
        
        hour, minute = map(int, schedule_time.split(':'))
        
        if frequency_type == 'daily':
            # Next run is tomorrow at the same time
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
                day = min(schedule.get('day_of_month', now.day), max_day)
                next_run = now.replace(month=next_month, day=day, hour=hour, minute=minute, second=0, microsecond=0)
        else:
            # Default to daily
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=1)
        
        return next_run

# Global scheduler instance
scheduler_service = SchedulerService()