"""
Webhook endpoint for external cron services to trigger scheduled emails
This allows external services like cron-job.org to trigger email scheduling
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timezone, timedelta
from agentsdr.core.supabase_client import get_service_supabase
from agentsdr.services.gmail_service import fetch_and_summarize_emails
from agentsdr.core.email import send_email_summary
# from agentsdr.auth.decorators import require_api_key  # Not needed for now

scheduler_webhook_bp = Blueprint('scheduler_webhook', __name__)

@scheduler_webhook_bp.route('/webhook/trigger-schedules', methods=['POST'])
def trigger_schedules():
    """
    Webhook endpoint to trigger scheduled emails
    Can be called by external cron services every minute
    """
    try:
        # Optional API key check for security
        api_key = request.headers.get('X-API-Key') or request.json.get('api_key')
        expected_key = current_app.config.get('SCHEDULER_WEBHOOK_KEY', 'agentsdr-scheduler-2024')
        
        if api_key != expected_key:
            return jsonify({'error': 'Invalid API key'}), 401
        
        current_app.logger.info("🔄 Webhook scheduler triggered")
        
        supabase = get_service_supabase()
        now = datetime.now(timezone.utc)
        
        # Get all active schedules that are due
        response = supabase.table('agent_schedules').select('*').eq('is_active', True).execute()
        
        executed_count = 0
        for schedule in response.data:
            if _is_schedule_due(schedule, now):
                success = _execute_schedule(schedule, supabase)
                if success:
                    executed_count += 1
                    current_app.logger.info(f"✅ Executed schedule {schedule['id'][:8]}...")
        
        return jsonify({
            'success': True,
            'executed_schedules': executed_count,
            'timestamp': now.isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Webhook scheduler error: {e}")
        return jsonify({'error': str(e)}), 500

def _is_schedule_due(schedule, now):
    """Check if a schedule is due to run"""
    next_run_at = schedule.get('next_run_at')
    
    if not next_run_at:
        return False
    
    try:
        next_run_dt = datetime.fromisoformat(next_run_at.replace('Z', '+00:00')).replace(tzinfo=timezone.utc)
        time_diff = (next_run_dt - now).total_seconds()
        
        # Run if within 5 minutes of scheduled time
        if -300 <= time_diff <= 300:  # 5 minutes window
            # Check if already run recently to avoid duplicates
            last_run = schedule.get('last_run_at')
            if last_run:
                last_run_dt = datetime.fromisoformat(last_run.replace('Z', '+00:00')).replace(tzinfo=timezone.utc)
                if (now - last_run_dt).total_seconds() < 600:  # Don't run if ran in last 10 minutes
                    return False
            return True
            
    except Exception as e:
        current_app.logger.error(f"Error parsing schedule time: {e}")
        return False
    
    return False

def _execute_schedule(schedule, supabase):
    """Execute a single schedule"""
    try:
        # Get agent details
        agent_resp = supabase.table('agents').select('*').eq('id', schedule['agent_id']).execute()
        if not agent_resp.data:
            current_app.logger.error(f"Agent {schedule['agent_id']} not found")
            return False
        
        agent = agent_resp.data[0]
        
        # Check if agent is active
        is_active = agent.get('is_active', True)
        if not is_active:
            current_app.logger.info(f"Agent {schedule['agent_id']} is paused - skipping")
            return False
        
        # Get Gmail refresh token
        config = agent.get('config', {})
        refresh_token = config.get('gmail_refresh_token')
        
        if not refresh_token:
            current_app.logger.error(f"No Gmail token for agent {schedule['agent_id']}")
            return False
        
        # Fetch and summarize emails
        criteria_type = schedule.get('criteria_type', 'last_24_hours')
        email_count = schedule.get('email_count', 50)
        email_hours = schedule.get('email_hours')
        
        summaries = fetch_and_summarize_emails(
            refresh_token=refresh_token,
            criteria_type=criteria_type,
            count=email_count,
            hours=email_hours
        )
        
        if not summaries:
            current_app.logger.info(f"No emails found for schedule {schedule['id']}")
            _update_schedule_after_run(supabase, schedule)
            return True
        
        # Send email summary
        success = send_email_summary(
            recipient_email=schedule['recipient_email'],
            summaries=summaries,
            agent_name=agent['name'],
            criteria_type=criteria_type
        )
        
        if success:
            _update_schedule_after_run(supabase, schedule)
            current_app.logger.info(f"Email sent to {schedule['recipient_email']}")
            return True
        else:
            current_app.logger.error(f"Failed to send email to {schedule['recipient_email']}")
            return False
            
    except Exception as e:
        current_app.logger.error(f"Error executing schedule: {e}")
        return False

def _update_schedule_after_run(supabase, schedule):
    """Update schedule after successful execution"""
    try:
        now = datetime.now(timezone.utc)
        
        # Calculate next run time based on frequency
        next_run_time = _calculate_next_run_time(schedule)
        
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
        current_app.logger.error(f"Error updating schedule: {e}")

def _calculate_next_run_time(schedule):
    """Calculate next run time for recurring schedules"""
    schedule_time = schedule['schedule_time']
    frequency_type = schedule.get('frequency_type', 'daily')
    
    now = datetime.now(timezone.utc)
    
    if frequency_type == 'once':
        return None
    
    try:
        hour, minute = map(int, schedule_time.split(':'))
        
        if frequency_type == 'daily':
            # Next run is tomorrow at the same time
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=1)
        elif frequency_type == 'weekly':
            # Next run is next week
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=7)
        else:
            # Default to daily
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=1)
        
        return next_run
        
    except Exception:
        return None