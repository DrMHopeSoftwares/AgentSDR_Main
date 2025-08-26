import uuid
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from flask import current_app
import logging

from .bolna_service import BolnaService
from .openai_service import OpenAIService
from .hubspot_service import HubSpotService
from agentsdr.core.supabase_client import get_service_supabase
from agentsdr.core.models import (
    CallTranscript, CallSummary, CallRecord, 
    CreateCallRecordRequest, UpdateCallTranscriptRequest, CreateCallSummaryRequest
)

logger = logging.getLogger(__name__)

class CallTranscriptService:
    def __init__(self):
        self.bolna_service = BolnaService()
        self.openai_service = OpenAIService()
        self.hubspot_service = HubSpotService()
        self.supabase = get_service_supabase()
    
    def process_call_transcript(self, call_id: str, org_id: str, agent_id: str, transcript_override: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main method to process a call transcript end-to-end
        
        Args:
            call_id: Bolna call ID
            org_id: Organization ID
            agent_id: Agent ID who made the call
            transcript_override: If provided, use this transcript data instead of fetching from Bolna
        
        Returns:
            Dict containing processing results
        """
        try:
            logger.info(f"Starting call transcript processing for call {call_id}")
            
            # Step 1: Get transcript data (from override or Bolna API)
            if transcript_override:
                transcript_data = self._normalize_payload_transcript(transcript_override)
            else:
                transcript_data = self._fetch_transcript_from_bolna(call_id)
            
            if not transcript_data:
                return {
                    'success': False,
                    'error': 'Failed to obtain transcript data'
                }
            
            # Step 2: Create call record in database
            call_record = self._create_call_record(call_id, org_id, agent_id, transcript_data)
            if not call_record:
                return {
                    'success': False,
                    'error': 'Failed to create call record'
                }
            
            # Step 3: Save transcript to database
            transcript_record = self._save_transcript(call_record['id'], org_id, call_id, agent_id, transcript_data)
            if not transcript_record:
                return {
                    'success': False,
                    'error': 'Failed to save transcript'
                }
            
            # Step 4: Generate summary using OpenAI
            summary_data = self._generate_summary(transcript_data['transcript_text'])
            if not summary_data:
                return {
                    'success': False,
                    'error': 'Failed to generate summary'
                }
            
            # Step 5: Save summary to database
            summary_record = self._save_summary(transcript_record['id'], org_id, summary_data)
            if not summary_record:
                return {
                    'success': False,
                    'error': 'Failed to save summary'
                }
            
            # Step 6: Update call record with transcript and summary IDs
            self._update_call_record(call_record['id'], transcript_record['id'], summary_record['id'])
            
            # Step 7: Send summary to HubSpot
            hubspot_result = self._send_to_hubspot(transcript_data, summary_data['summary'])
            
            # Step 8: Update HubSpot status
            self._update_hubspot_status(call_record['id'], hubspot_result['success'])
            
            logger.info(f"Successfully processed call transcript for call {call_id}")
            
            return {
                'success': True,
                'call_record_id': call_record['id'],
                'transcript_id': transcript_record['id'],
                'summary_id': summary_record['id'],
                'summary': summary_data['summary'],
                'hubspot_success': hubspot_result['success'],
                'hubspot_contact_id': hubspot_result.get('contact_id')
            }
            
        except Exception as e:
            logger.error(f"Error processing call transcript for call {call_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _fetch_transcript_from_bolna(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Fetch transcript from Bolna API"""
        try:
            # Get call details first
            call_details = self.bolna_service.get_call_details(call_id)
            if not call_details:
                logger.error(f"Failed to get call details for {call_id}")
                return None
            
            # Get transcript
            transcript_data = self.bolna_service.get_call_transcript(call_id)
            if not transcript_data:
                logger.error(f"Failed to get transcript for {call_id}")
                return None
            
            # Combine call details with transcript
            result = {
                'transcript_text': transcript_data.get('transcript', ''),
                'call_duration': call_details.get('duration', 0),
                'call_status': call_details.get('status', 'completed'),
                'contact_phone': call_details.get('to_number', ''),
                'contact_name': call_details.get('contact_name', '')
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching transcript from Bolna: {e}")
            return None
    
    def _normalize_payload_transcript(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize Bolna webhook payload into transcript_data shape used internally."""
        try:
            transcript_text = payload.get('transcript') or ''
            telephony = payload.get('telephony_data') or {}
            contact_phone = telephony.get('to_number') or payload.get('context_details', {}).get('recipient_phone_number') or ''
            call_duration = int(float(payload.get('conversation_duration') or telephony.get('duration') or 0)) if str(payload.get('conversation_duration') or '').strip() else int(float(telephony.get('duration') or 0))
            status = payload.get('status') or payload.get('smart_status') or 'completed'
            contact_name = None
            return {
                'transcript_text': transcript_text,
                'call_duration': call_duration,
                'call_status': status,
                'contact_phone': contact_phone,
                'contact_name': contact_name
            }
        except Exception as e:
            logger.error(f"Failed to normalize payload: {e}")
            return None
    
    def _create_call_record(self, call_id: str, org_id: str, agent_id: str, transcript_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create call record in database"""
        try:
            call_record_data = {
                'id': str(uuid.uuid4()),
                'org_id': org_id,
                'call_id': call_id,
                'agent_id': agent_id,
                'contact_phone': transcript_data.get('contact_phone', ''),
                'contact_name': transcript_data.get('contact_name'),
                'call_duration': transcript_data.get('call_duration'),
                'call_status': transcript_data.get('call_status', 'completed'),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            response = self.supabase.table('call_records').insert(call_record_data).execute()
            
            if response.data:
                logger.info(f"Created call record: {call_record_data['id']}")
                return response.data[0]
            else:
                logger.error("Failed to create call record")
                return None
                
        except Exception as e:
            logger.error(f"Error creating call record: {e}")
            return None
    
    def _save_transcript(self, call_record_id: str, org_id: str, call_id: str, agent_id: str, transcript_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Save transcript to database"""
        try:
            transcript_record_data = {
                'id': str(uuid.uuid4()),
                'org_id': org_id,
                'call_id': call_id,
                'agent_id': agent_id,
                'contact_phone': transcript_data.get('contact_phone', ''),
                'contact_name': transcript_data.get('contact_name'),
                'transcript_text': transcript_data.get('transcript_text', ''),
                'call_duration': transcript_data.get('call_duration'),
                'call_status': transcript_data.get('call_status', 'completed'),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            response = self.supabase.table('call_transcripts').insert(transcript_record_data).execute()
            
            if response.data:
                logger.info(f"Saved transcript: {transcript_record_data['id']}")
                return response.data[0]
            else:
                logger.error("Failed to save transcript")
                return None
                
        except Exception as e:
            logger.error(f"Error saving transcript: {e}")
            return None
    
    def _generate_summary(self, transcript_text: str) -> Optional[Dict[str, Any]]:
        """Generate summary using OpenAI"""
        try:
            summary_data = self.openai_service.summarize_transcript(transcript_text, max_words=20)
            
            if summary_data:
                logger.info(f"Generated summary with {summary_data['word_count']} words")
                return summary_data
            else:
                logger.error("Failed to generate summary")
                return None
                
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return None
    
    def _save_summary(self, transcript_id: str, org_id: str, summary_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Save summary to database"""
        try:
            summary_record_data = {
                'id': str(uuid.uuid4()),
                'transcript_id': transcript_id,
                'org_id': org_id,
                'summary_text': summary_data['summary'],
                'word_count': summary_data['word_count'],
                'openai_model_used': summary_data['model_used'],
                'openai_tokens_used': summary_data['tokens_used'],
                'created_at': datetime.utcnow().isoformat()
            }
            
            response = self.supabase.table('call_summaries').insert(summary_record_data).execute()
            
            if response.data:
                logger.info(f"Saved summary: {summary_record_data['id']}")
                return response.data[0]
            else:
                logger.error("Failed to save summary")
                return None
                
        except Exception as e:
            logger.error(f"Error saving summary: {e}")
            return None
    
    def _update_call_record(self, call_record_id: str, transcript_id: str, summary_id: str):
        """Update call record with transcript and summary IDs"""
        try:
            update_data = {
                'transcript_id': transcript_id,
                'summary_id': summary_id,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            response = self.supabase.table('call_records').update(update_data).eq('id', call_record_id).execute()
            
            if response.data:
                logger.info(f"Updated call record: {call_record_id}")
            else:
                logger.error(f"Failed to update call record: {call_record_id}")
                
        except Exception as e:
            logger.error(f"Error updating call record: {e}")
    
    def _send_to_hubspot(self, transcript_data: Dict[str, Any], summary: str) -> Dict[str, Any]:
        """Send summary to HubSpot"""
        try:
            contact_phone = transcript_data.get('contact_phone', '')
            if not contact_phone:
                logger.warning("No contact phone number available for HubSpot")
                return {'success': False, 'error': 'No contact phone number'}
            
            # Find existing contact by phone
            contact = self.hubspot_service.find_contact_by_phone(contact_phone)
            
            if contact:
                # Update existing contact
                contact_id = contact['id']
                success = self.hubspot_service.update_contact_summary(contact_id, summary)
                
                if success:
                    logger.info(f"Updated HubSpot contact: {contact_id}")
                    return {
                        'success': True,
                        'contact_id': contact_id,
                        'action': 'updated'
                    }
                else:
                    logger.error(f"Failed to update HubSpot contact: {contact_id}")
                    return {'success': False, 'error': 'Failed to update contact'}
            else:
                # Create new contact
                contact_data = {
                    'phone': contact_phone,
                    'firstname': transcript_data.get('contact_name', 'Unknown'),
                    'call_summary': f"{datetime.now().strftime('%Y-%m-%d %H:%M')}: {summary}"
                }
                
                new_contact = self.hubspot_service.create_contact(contact_data)
                
                if new_contact:
                    contact_id = new_contact['id']
                    logger.info(f"Created new HubSpot contact: {contact_id}")
                    return {
                        'success': True,
                        'contact_id': contact_id,
                        'action': 'created'
                    }
                else:
                    logger.error("Failed to create new HubSpot contact")
                    return {'success': False, 'error': 'Failed to create contact'}
                    
        except Exception as e:
            logger.error(f"Error sending to HubSpot: {e}")
            return {'success': False, 'error': str(e)}
    
    def _update_hubspot_status(self, call_record_id: str, hubspot_success: bool):
        """Update HubSpot status in call record"""
        try:
            update_data = {
                'hubspot_summary_sent': hubspot_success,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            if hubspot_success:
                update_data['hubspot_contact_id'] = None  # Will be updated separately
            
            response = self.supabase.table('call_records').update(update_data).eq('id', call_record_id).execute()
            
            if response.data:
                logger.info(f"Updated HubSpot status for call record: {call_record_id}")
            else:
                logger.error(f"Failed to update HubSpot status for call record: {call_record_id}")
                
        except Exception as e:
            logger.error(f"Error updating HubSpot status: {e}")
    
    def get_call_history(self, org_id: str, limit: int = 50, offset: int = 0) -> Optional[Dict[str, Any]]:
        """Get call history for an organization"""
        try:
            response = self.supabase.table('call_records')\
                .select('*, call_transcripts(*), call_summaries(*)')\
                .eq('org_id', org_id)\
                .order('created_at', desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            if response.data:
                return {
                    'calls': response.data,
                    'total': len(response.data)
                }
            else:
                return {'calls': [], 'total': 0}
                
        except Exception as e:
            logger.error(f"Error getting call history: {e}")
            return None
    
    def get_call_details(self, call_record_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed call information"""
        try:
            response = self.supabase.table('call_records')\
                .select('*, call_transcripts(*), call_summaries(*)')\
                .eq('id', call_record_id)\
                .single()\
                .execute()
            
            if response.data:
                return response.data
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting call details: {e}")
            return None
