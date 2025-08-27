import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple
from flask import current_app
import logging

from .bolna_service import BolnaService
from .hubspot_service import HubSpotService
from agentsdr.core.supabase_client import get_service_supabase

logger = logging.getLogger(__name__)

class CallSchedulingService:
    def __init__(self):
        self.bolna_service = BolnaService()
        self.hubspot_service = HubSpotService()
        self.supabase = get_service_supabase()
    
    def create_call_schedule(
        self,
        org_id: str,
        agent_id: str,
        contact_id: str,
        contact_name: str,
        contact_phone: str,
        scheduled_at: datetime,
        call_topic: str = 'follow_up',
        call_language: str = 'en-IN',
        auto_trigger_enabled: bool = True,
        checkup_threshold_days: int = 5,
        created_by: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new call schedule
        
        Args:
            org_id: Organization ID
            agent_id: Agent ID
            contact_id: HubSpot contact ID
            contact_name: Contact name
            contact_phone: Contact phone number
            scheduled_at: When to schedule the call
            call_topic: Topic of the call
            call_language: Language for the call
            auto_trigger_enabled: Whether to auto-trigger based on check-up date
            checkup_threshold_days: Days after last check-up to auto-trigger
            
        Returns:
            Dict containing schedule data or None if failed
        """
        try:
            # Get last check-up date from HubSpot
            last_checkup_date = self._get_contact_checkup_date(contact_id)
            
            schedule_data = {
                'id': str(uuid.uuid4()),
                'org_id': org_id,
                'agent_id': agent_id,
                'contact_id': contact_id,
                'contact_name': contact_name,
                'contact_phone': contact_phone,
                'scheduled_at': scheduled_at.isoformat(),
                'call_topic': call_topic,
                'call_language': call_language,
                'is_active': True,
                'call_status': 'scheduled',
                'auto_trigger_enabled': auto_trigger_enabled,
                'checkup_threshold_days': checkup_threshold_days,
                'last_checkup_date': last_checkup_date.isoformat() if last_checkup_date else None,
                # created_by must reference auth.users(id)
                'created_by': created_by,
            }
            
            response = self.supabase.table('call_schedules').insert(schedule_data).execute()
            
            if response.data:
                logger.info(f"Created call schedule for contact {contact_id} at {scheduled_at}")
                return response.data[0]
            else:
                # Try to log response.error if available for easier debugging
                err_detail = getattr(response, 'error', None)
                logger.error(f"Failed to create call schedule for contact {contact_id}. Supabase error: {err_detail}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating call schedule: {e}")
            return None
    
    def get_due_call_schedules(self, org_id: str) -> List[Dict[str, Any]]:
        """
        Get all call schedules that are due to be executed
        
        Args:
            org_id: Organization ID
            
        Returns:
            List of due call schedules
        """
        try:
            # Use the database function to get due schedules
            response = self.supabase.rpc('get_due_call_schedules', {'org_uuid': org_id}).execute()
            
            if response.data:
                logger.info(f"Found {len(response.data)} due call schedules for org {org_id}")
                return response.data
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting due call schedules: {e}")
            return []
    
    def execute_scheduled_call(self, schedule_id: str) -> Dict[str, Any]:
        """
        Execute a scheduled call by initiating it through Bolna API
        
        Args:
            schedule_id: The schedule ID to execute
            
        Returns:
            Dict containing execution results
        """
        try:
            # Get the schedule details
            schedule_response = self.supabase.table('call_schedules').select('*').eq('id', schedule_id).single().execute()
            
            if not schedule_response.data:
                return {'success': False, 'error': 'Schedule not found'}
            
            schedule = schedule_response.data
            
            # Check if schedule is still active and scheduled
            if not schedule['is_active'] or schedule['call_status'] != 'scheduled':
                return {'success': False, 'error': 'Schedule is not active or already processed'}
            
            # Update status to in_progress
            self.supabase.table('call_schedules').update({
                'call_status': 'in_progress',
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('id', schedule_id).execute()
            
            # Initiate call through Bolna API
            call_result = self._initiate_bolna_call(schedule)
            
            if call_result.get('success'):
                # Update schedule with Bolna call ID
                self.supabase.table('call_schedules').update({
                    'bolna_call_id': call_result.get('bolna_call_id'),
                    'call_status': 'in_progress',
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }).eq('id', schedule_id).execute()
                
                logger.info(f"Successfully initiated scheduled call {schedule_id} through Bolna")
                return {
                    'success': True,
                    'schedule_id': schedule_id,
                    'bolna_call_id': call_result.get('bolna_call_id'),
                    'message': 'Call initiated successfully'
                }
            else:
                # Revert status back to scheduled if call initiation failed
                self.supabase.table('call_schedules').update({
                    'call_status': 'scheduled',
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }).eq('id', schedule_id).execute()
                
                return {
                    'success': False,
                    'error': call_result.get('error', 'Failed to initiate call')
                }
                
        except Exception as e:
            logger.error(f"Error executing scheduled call {schedule_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_call_status(self, schedule_id: str, status: str, bolna_call_id: str = None) -> bool:
        """
        Update the status of a call schedule
        
        Args:
            schedule_id: The schedule ID to update
            status: New status (completed, failed, cancelled)
            bolna_call_id: Bolna call ID if available
            
        Returns:
            True if successful, False otherwise
        """
        try:
            update_data = {
                'call_status': status,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            if bolna_call_id:
                update_data['bolna_call_id'] = bolna_call_id
            
            response = self.supabase.table('call_schedules').update(update_data).eq('id', schedule_id).execute()
            
            if response.data:
                logger.info(f"Updated call schedule {schedule_id} status to {status}")
                return True
            else:
                logger.error(f"Failed to update call schedule {schedule_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating call schedule status: {e}")
            return False
    
    def get_call_scheduling_statistics(self, org_id: str) -> Dict[str, Any]:
        """
        Get call scheduling statistics for an organization
        
        Args:
            org_id: Organization ID
            
        Returns:
            Dict containing scheduling statistics
        """
        try:
            response = self.supabase.rpc('get_call_scheduling_statistics', {'org_uuid': org_id}).execute()
            
            if response.data:
                return response.data[0]
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error getting call scheduling statistics: {e}")
            return {}
    
    def _get_contact_checkup_date(self, contact_id: str) -> Optional[datetime]:
        """
        Get the last check-up date for a HubSpot contact
        
        Args:
            contact_id: HubSpot contact ID
            
        Returns:
            Last check-up date or None if not found
        """
        try:
            # Use the enhanced HubSpot service to get check-up date
            checkup_date = self.hubspot_service.get_contact_checkup_date(contact_id)
            return checkup_date
        except Exception as e:
            logger.error(f"Error getting contact check-up date: {e}")
            return None
    
    def _initiate_bolna_call(self, schedule: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initiate a call through Bolna API
        
        Args:
            schedule: Call schedule data
            
        Returns:
            Dict containing call initiation results
        """
        try:
            # Get agent configuration
            agent_response = self.supabase.table('agents').select('config').eq('id', schedule['agent_id']).single().execute()
            
            if not agent_response.data:
                return {'success': False, 'error': 'Agent not found'}
            
            agent_config = agent_response.data.get('config', {})
            
            # Resolve config and validate inputs
            bolna_agent_id = agent_config.get('bolna_agent_id') or current_app.config.get('BOLNA_AGENT_ID')
            from_phone_number = current_app.config.get('BOLNA_FROM_NUMBER')
            recipient_phone_number = str(schedule['contact_phone']).strip()

            logger.info(
                "Bolna config resolved | agent_id_present=%s from_present=%s recipient=%s",
                bool(bolna_agent_id), bool(from_phone_number), recipient_phone_number
            )

            # Basic E.164 sanity: must start with '+' and 8-15 digits total (after '+')
            import re
            e164_re = re.compile(r"^\+[1-9]\d{7,14}$")
            if not bolna_agent_id:
                logger.error("Bolna agent ID missing for schedule %s", schedule.get('id'))
                return {'success': False, 'error': 'Bolna agent ID missing', 'details': 'Set bolna_agent_id in agent config or BOLNA_AGENT_ID env var'}
            if not from_phone_number:
                logger.error("BOLNA_FROM_NUMBER missing for schedule %s", schedule.get('id'))
                return {'success': False, 'error': 'From phone number missing', 'details': 'Set BOLNA_FROM_NUMBER in environment'}
            if not e164_re.match(recipient_phone_number):
                logger.error("Invalid recipient phone format for schedule %s: %s", schedule.get('id'), recipient_phone_number)
                return {'success': False, 'error': 'Invalid recipient phone format', 'details': 'Use E.164 format like +14155552671'}
            if not e164_re.match(from_phone_number):
                logger.error("Invalid from phone format in env for schedule %s: %s", schedule.get('id'), from_phone_number)
                return {'success': False, 'error': 'Invalid from phone format', 'details': 'BOLNA_FROM_NUMBER must be E.164 like +14155552671'}

            # Prepare Bolna API payload
            bolna_payload = {
                'agent_id': bolna_agent_id,
                'recipient_phone_number': recipient_phone_number,
                'from_phone_number': from_phone_number,
                'user_data': {
                    'topic': schedule['call_topic'],
                    'language': schedule['call_language']
                }
            }
            
            # Add scheduled time if it's in the future
            scheduled_at = datetime.fromisoformat(schedule['scheduled_at'].replace('Z', '+00:00'))
            if scheduled_at > datetime.now(timezone.utc):
                bolna_payload['scheduled_at'] = scheduled_at.isoformat()
            
            # Make request to Bolna API
            headers = {
                'Authorization': f"Bearer {current_app.config.get('BOLNA_API_KEY')}",
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Resolve final Bolna URL from env/config. Support either full URL or relative path.
            # Respect explicit full URL if provided (align with manual call route)
            full_url = current_app.config.get('BOLNA_FULL_CALLS_URL')
            if full_url:
                bolna_url = full_url
            else:
                base_url = current_app.config.get('BOLNA_API_URL', 'https://api.bolna.ai')
                calls_path = current_app.config.get('BOLNA_CALLS_PATH')
                if calls_path:
                    if calls_path.startswith('http'):
                        bolna_url = calls_path
                    else:
                        bolna_url = f"{base_url.rstrip('/')}/{calls_path.lstrip('/')}"
                else:
                    bolna_url = f"{base_url.rstrip('/')}/call"
            
            import requests
            response = requests.post(bolna_url, json=bolna_payload, headers=headers, timeout=30)
            
            if response.status_code in (200, 201, 202):
                response_data = response.json()
                bolna_call_id = response_data.get('id') or response_data.get('call_id')
                
                logger.info(f"Successfully initiated Bolna call: {bolna_call_id}")
                return {
                    'success': True,
                    'bolna_call_id': bolna_call_id,
                    'response': response_data
                }
            else:
                logger.error(f"Bolna API error: {response.status_code} - {response.text} | URL: {bolna_url}")
                return {
                    'success': False,
                    'error': f'Bolna API error: {response.status_code}',
                    'details': response.text,
                    'url': bolna_url,
                    'payload': bolna_payload
                }
                
        except Exception as e:
            logger.error(f"Error initiating Bolna call: {e}")
            return {'success': False, 'error': str(e)}
    
    def check_and_trigger_overdue_calls(self, org_id: str) -> List[Dict[str, Any]]:
        """
        Trigger due calls for an org. A call is due if:
          - scheduled_at <= now(), or
          - auto-trigger rules deem it overdue (check-up threshold exceeded)

        We rely on the SQL function get_due_call_schedules() to determine due items.
        """
        try:
            due_resp = self.supabase.rpc('get_due_call_schedules', {'org_uuid': org_id}).execute()
            if not due_resp.data:
                return []

            triggered_calls: List[Dict[str, Any]] = []
            for row in due_resp.data:
                schedule_id = row.get('schedule_id') or row.get('id')
                if not schedule_id:
                    continue
                result = self.execute_scheduled_call(schedule_id)
                if result.get('success'):
                    triggered_calls.append({
                        'schedule_id': schedule_id,
                        'contact_name': row.get('contact_name'),
                        'contact_phone': row.get('contact_phone'),
                        'trigger_reason': 'scheduled_time_or_threshold_due',
                        'result': result,
                    })

            logger.info(f"Triggered {len(triggered_calls)} due calls for org {org_id}")
            return triggered_calls
        except Exception as e:
            logger.error(f"Error checking and triggering overdue calls: {e}")
            return []
