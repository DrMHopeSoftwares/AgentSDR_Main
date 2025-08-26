from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from agentsdr.orgs import orgs_bp
from agentsdr.core.rbac import require_org_member
from agentsdr.services.call_transcript_service import CallTranscriptService
from agentsdr.core.supabase_client import get_service_supabase
import logging
import hmac
import hashlib
import json

logger = logging.getLogger(__name__)

# Create a sub-blueprint for call-related routes
call_bp = Blueprint('call', __name__, url_prefix='/<org_slug>/calls')

@call_bp.route('/process-transcript', methods=['POST'])
@login_required
@require_org_member
def process_call_transcript(org_slug):
    """
    Process a call transcript from Bolna API
    
    Expected JSON payload:
    {
        "call_id": "bolna_call_id",
        "agent_id": "agent_user_id"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        call_id = data.get('call_id')
        agent_id = data.get('agent_id')
        
        if not call_id:
            return jsonify({'error': 'call_id is required'}), 400
        
        if not agent_id:
            return jsonify({'error': 'agent_id is required'}), 400
        
        # Get organization ID from the org_slug
        supabase = get_service_supabase()
        org_response = supabase.table('organizations').select('id').eq('slug', org_slug).single().execute()
        
        if not org_response.data:
            return jsonify({'error': 'Organization not found'}), 404
        
        org_id = org_response.data['id']
        
        # Process the call transcript
        call_service = CallTranscriptService()
        result = call_service.process_call_transcript(call_id, org_id, agent_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Call transcript processed successfully',
                'data': result
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error occurred')
            }), 500
            
    except Exception as e:
        logger.error(f"Error processing call transcript: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@call_bp.route('/history', methods=['GET'])
@login_required
@require_org_member
def get_call_history(org_slug):
    """
    Get call history for an organization
    
    Query parameters:
    - limit: Number of calls to return (default: 50)
    - offset: Number of calls to skip (default: 0)
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Validate parameters
        if limit > 100:
            limit = 100
        if limit < 1:
            limit = 50
        if offset < 0:
            offset = 0
        
        # Get organization ID from the org_slug
        supabase = get_service_supabase()
        org_response = supabase.table('organizations').select('id').eq('slug', org_slug).single().execute()
        
        if not org_response.data:
            return jsonify({'error': 'Organization not found'}), 404
        
        org_id = org_response.data['id']
        
        # Get call history
        call_service = CallTranscriptService()
        history = call_service.get_call_history(org_id, limit, offset)
        
        if history is not None:
            return jsonify({
                'success': True,
                'data': history
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to retrieve call history'
            }), 500
            
    except Exception as e:
        logger.error(f"Error getting call history: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@call_bp.route('/<call_record_id>', methods=['GET'])
@login_required
@require_org_member
def get_call_details(org_slug, call_record_id):
    """
    Get detailed information about a specific call
    """
    try:
        # Get organization ID from the org_slug
        supabase = get_service_supabase()
        org_response = supabase.table('organizations').select('id').eq('slug', org_slug).single().execute()
        
        if not org_response.data:
            return jsonify({'error': 'Organization not found'}), 404
        
        org_id = org_response.data['id']
        
        # Get call details
        call_service = CallTranscriptService()
        call_details = call_service.get_call_details(call_record_id)
        
        if call_details:
            # Verify the call belongs to the organization
            if call_details['org_id'] != org_id:
                return jsonify({'error': 'Call not found'}), 404
            
            return jsonify({
                'success': True,
                'data': call_details
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Call not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting call details: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@call_bp.route('/<call_record_id>/retry-hubspot', methods=['POST'])
@login_required
@require_org_member
def retry_hubspot_sync(org_slug, call_record_id):
    """
    Retry sending call summary to HubSpot
    """
    try:
        # Get organization ID from the org_slug
        supabase = get_service_supabase()
        org_response = supabase.table('organizations').select('id').eq('slug', org_slug).single().execute()
        
        if not org_response.data:
            return jsonify({'error': 'Organization not found'}), 404
        
        org_id = org_response.data['id']
        
        # Get call details
        call_service = CallTranscriptService()
        call_details = call_service.get_call_details(call_record_id)
        
        if not call_details:
            return jsonify({'error': 'Call not found'}), 404
        
        # Verify the call belongs to the organization
        if call_details['org_id'] != org_id:
            return jsonify({'error': 'Call not found'}), 404
        
        # Check if call has transcript and summary
        if not call_details.get('transcript_id') or not call_details.get('summary_id'):
            return jsonify({'error': 'Call transcript or summary not found'}), 400
        
        # Get transcript and summary data
        transcript_response = supabase.table('call_transcripts').select('*').eq('id', call_details['transcript_id']).single().execute()
        summary_response = supabase.table('call_summaries').select('*').eq('id', call_details['summary_id']).single().execute()
        
        if not transcript_response.data or not summary_response.data:
            return jsonify({'error': 'Transcript or summary data not found'}), 404
        
        transcript_data = transcript_response.data
        summary_data = summary_response.data
        
        # Retry HubSpot sync
        hubspot_result = call_service._send_to_hubspot(
            {
                'contact_phone': transcript_data['contact_phone'],
                'contact_name': transcript_data['contact_name']
            },
            summary_data['summary_text']
        )
        
        # Update HubSpot status
        call_service._update_hubspot_status(call_record_id, hubspot_result['success'])
        
        if hubspot_result['success']:
            return jsonify({
                'success': True,
                'message': 'Successfully synced with HubSpot',
                'data': hubspot_result
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': hubspot_result.get('error', 'Failed to sync with HubSpot')
            }), 500
            
    except Exception as e:
        logger.error(f"Error retrying HubSpot sync: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@call_bp.route('/sync-status', methods=['GET'])
@login_required
@require_org_member
def get_sync_status(org_slug):
    """
    Get HubSpot sync status for calls in an organization
    """
    try:
        # Get organization ID from the org_slug
        supabase = get_service_supabase()
        org_response = supabase.table('organizations').select('id').eq('slug', org_slug).single().execute()
        
        if not org_response.data:
            return jsonify({'error': 'Organization not found'}), 404
        
        org_id = org_response.data['id']
        
        # Get sync status
        response = supabase.table('call_records')\
            .select('id, call_id, contact_phone, contact_name, hubspot_summary_sent, created_at')\
            .eq('org_id', org_id)\
            .order('created_at', desc=True)\
            .execute()
        
        if response.data:
            # Count sync status
            total_calls = len(response.data)
            synced_calls = len([call for call in response.data if call.get('hubspot_summary_sent')])
            failed_calls = total_calls - synced_calls
            
            return jsonify({
                'success': True,
                'data': {
                    'total_calls': total_calls,
                    'synced_calls': synced_calls,
                    'failed_calls': failed_calls,
                    'sync_rate': round((synced_calls / total_calls * 100), 2) if total_calls > 0 else 0,
                    'calls': response.data
                }
            }), 200
        else:
            return jsonify({
                'success': True,
                'data': {
                    'total_calls': 0,
                    'synced_calls': 0,
                    'failed_calls': 0,
                    'sync_rate': 0,
                    'calls': []
                }
            }), 200
            
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

# Register the call blueprint with the orgs blueprint
def init_call_routes(app):
    """Initialize call routes with the main app"""
    app.register_blueprint(call_bp)

bolna_bp = Blueprint('bolna', __name__, url_prefix='/<org_slug>/bolna')

def _verify_bolna_signature(secret: str, raw_body: bytes, signature: str) -> bool:
	try:
		digest = hmac.new(secret.encode('utf-8'), raw_body, hashlib.sha256).hexdigest()
		return hmac.compare_digest(signature or '', digest)
	except Exception:
		return False

@bolna_bp.route('/webhook', methods=['POST'])
def bolna_webhook(org_slug):
	"""Webhook endpoint to receive call completion events from Bolna."""
	secret = current_app.config.get('BOLNA_WEBHOOK_SECRET')
	if not secret:
		return jsonify({'error': 'Webhook secret not configured'}), 500
	
	raw = request.get_data()
	sig = request.headers.get('X-Bolna-Signature') or request.headers.get('X-Bolna-Secret')
	# If only a shared secret header is used, compare directly
	valid = False
	if request.headers.get('X-Bolna-Secret'):
		valid = hmac.compare_digest(request.headers['X-Bolna-Secret'], secret)
	else:
		valid = _verify_bolna_signature(secret, raw, sig or '')
	if not valid:
		return jsonify({'error': 'Invalid signature'}), 401
	
	try:
		payload = request.get_json(force=True, silent=False) or {}
		call_id = payload.get('id')
		if not call_id:
			return jsonify({'error': 'Missing call id'}), 400
		
		# Resolve org_id from slug
		supabase = get_service_supabase()
		org_resp = supabase.table('organizations').select('id').eq('slug', org_slug).single().execute()
		if not org_resp.data:
			return jsonify({'error': 'Organization not found'}), 404
		org_id = org_resp.data['id']
		
		# Resolve agent_id: prefer existing mapping in call_records; fallback to org owner
		rec = supabase.table('call_records').select('agent_id').eq('call_id', call_id).eq('org_id', org_id).order('created_at', desc=True).limit(1).execute()
		if rec.data:
			agent_id = rec.data[0]['agent_id']
		else:
			# fallback: first org member
			m = supabase.table('organization_members').select('user_id').eq('org_id', org_id).limit(1).execute()
			if not m.data:
				return jsonify({'error': 'No agent found for org'}), 404
			agent_id = m.data[0]['user_id']
		
		service = CallTranscriptService()
		result = service.process_call_transcript(call_id=call_id, org_id=org_id, agent_id=agent_id, transcript_override=payload)
		status = 200 if result.get('success') else 500
		return jsonify(result), status
	except Exception as e:
		return jsonify({'success': False, 'error': str(e)}), 500
