from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timezone
import logging

from agentsdr.services.call_scheduling_service import CallSchedulingService
from agentsdr.core.supabase_client import get_service_supabase
from agentsdr.core.rbac import require_org_member

logger = logging.getLogger(__name__)

# Create blueprint for call scheduling routes
call_scheduling_bp = Blueprint('call_scheduling', __name__)

@call_scheduling_bp.route('/<org_slug>/call-schedules', methods=['GET'])
@login_required
@require_org_member('org_slug')
def get_call_schedules(org_slug):
    """Get all call schedules for an organization"""
    try:
        supabase = get_service_supabase()
        
        # Get organization ID
        org_response = supabase.table('organizations').select('id').eq('slug', org_slug).single().execute()
        if not org_response.data:
            return jsonify({'error': 'Organization not found'}), 404
        
        org_id = org_response.data['id']
        
        # Get call schedules
        response = supabase.table('call_schedules').select('*').eq('org_id', org_id).order('scheduled_at', desc=True).execute()
        
        if response.data:
            return jsonify({
                'success': True,
                'schedules': response.data
            })
        else:
            return jsonify({
                'success': True,
                'schedules': []
            })
            
    except Exception as e:
        logger.error(f"Error getting call schedules: {e}")
        return jsonify({'error': str(e)}), 500

@call_scheduling_bp.route('/<org_slug>/call-schedules', methods=['POST'])
@login_required
@require_org_member('org_slug')
def create_call_schedule(org_slug):
    """Create a new call schedule"""
    try:
        data = request.get_json(silent=True) or request.form.to_dict() or {}
        
        # Validate required fields
        required_fields = ['agent_id', 'contact_id', 'contact_name', 'contact_phone', 'scheduled_at']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        supabase = get_service_supabase()
        
        # Get organization ID
        org_response = supabase.table('organizations').select('id').eq('slug', org_slug).single().execute()
        if not org_response.data:
            return jsonify({'error': 'Organization not found'}), 404
        
        org_id = org_response.data['id']
        
        # Parse scheduled time
        try:
            scheduled_at = datetime.fromisoformat(data['scheduled_at'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'Invalid scheduled_at format. Use ISO 8601 format.'}), 400
        
        # Create call schedule
        scheduling_service = CallSchedulingService()
        schedule = scheduling_service.create_call_schedule(
            org_id=org_id,
            agent_id=data['agent_id'],
            contact_id=data['contact_id'],
            contact_name=data['contact_name'],
            contact_phone=data['contact_phone'],
            scheduled_at=scheduled_at,
            call_topic=data.get('call_topic', 'follow_up'),
            call_language=data.get('call_language', 'en-IN'),
            auto_trigger_enabled=data.get('auto_trigger_enabled', True),
            checkup_threshold_days=data.get('checkup_threshold_days', 5),
            created_by=str(current_user.id),
        )
        
        if schedule:
            return jsonify({
                'success': True,
                'schedule': schedule,
                'message': 'Call schedule created successfully'
            })
        else:
            return jsonify({'error': 'Failed to create call schedule'}), 500
            
    except Exception as e:
        logger.error(f"Error creating call schedule: {e}")
        return jsonify({'error': str(e)}), 500

@call_scheduling_bp.route('/<org_slug>/call-schedules/<schedule_id>', methods=['PUT'])
@login_required
@require_org_member('org_slug')
def update_call_schedule(org_slug, schedule_id):
    """Update an existing call schedule"""
    try:
        data = request.get_json(silent=True) or request.form.to_dict() or {}
        
        supabase = get_service_supabase()
        
        # Get organization ID
        org_response = supabase.table('organizations').select('id').eq('slug', org_slug).single().execute()
        if not org_response.data:
            return jsonify({'error': 'Organization not found'}), 404
        
        org_id = org_response.data['id']
        
        # Validate that the schedule belongs to this organization
        schedule_response = supabase.table('call_schedules').select('*').eq('id', schedule_id).eq('org_id', org_id).single().execute()
        if not schedule_response.data:
            return jsonify({'error': 'Call schedule not found'}), 404
        
        # Prepare update data
        update_data = {}
        
        if 'scheduled_at' in data:
            try:
                scheduled_at = datetime.fromisoformat(data['scheduled_at'].replace('Z', '+00:00'))
                update_data['scheduled_at'] = scheduled_at.isoformat()
            except ValueError:
                return jsonify({'error': 'Invalid scheduled_at format. Use ISO 8601 format.'}), 400
        
        if 'call_topic' in data:
            update_data['call_topic'] = data['call_topic']
        
        if 'call_language' in data:
            update_data['call_language'] = data['call_language']
        
        if 'is_active' in data:
            update_data['is_active'] = data['is_active']
        
        if 'auto_trigger_enabled' in data:
            update_data['auto_trigger_enabled'] = data['auto_trigger_enabled']
        
        if 'checkup_threshold_days' in data:
            update_data['checkup_threshold_days'] = data['checkup_threshold_days']
        
        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        # Update the schedule
        update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        response = supabase.table('call_schedules').update(update_data).eq('id', schedule_id).execute()
        
        if response.data:
            return jsonify({
                'success': True,
                'schedule': response.data[0],
                'message': 'Call schedule updated successfully'
            })
        else:
            return jsonify({'error': 'Failed to update call schedule'}), 500
            
    except Exception as e:
        logger.error(f"Error updating call schedule: {e}")
        return jsonify({'error': str(e)}), 500

@call_scheduling_bp.route('/<org_slug>/call-schedules/<schedule_id>', methods=['DELETE'])
@login_required
@require_org_member('org_slug')
def delete_call_schedule(org_slug, schedule_id):
    """Delete a call schedule"""
    try:
        supabase = get_service_supabase()
        
        # Get organization ID
        org_response = supabase.table('organizations').select('id').eq('slug', org_slug).single().execute()
        if not org_response.data:
            return jsonify({'error': 'Organization not found'}), 404
        
        org_id = org_response.data['id']
        
        # Validate that the schedule belongs to this organization
        schedule_response = supabase.table('call_schedules').select('*').eq('id', schedule_id).eq('org_id', org_id).single().execute()
        if not schedule_response.data:
            return jsonify({'error': 'Call schedule not found'}), 404
        
        # Delete the schedule
        response = supabase.table('call_schedules').delete().eq('id', schedule_id).execute()
        
        if response.data:
            return jsonify({
                'success': True,
                'message': 'Call schedule deleted successfully'
            })
        else:
            return jsonify({'error': 'Failed to delete call schedule'}), 500
            
    except Exception as e:
        logger.error(f"Error deleting call schedule: {e}")
        return jsonify({'error': str(e)}), 500

@call_scheduling_bp.route('/<org_slug>/call-schedules/<schedule_id>/execute', methods=['POST'])
@login_required
@require_org_member('org_slug')
def execute_call_schedule(org_slug, schedule_id):
    """Execute a scheduled call immediately"""
    try:
        supabase = get_service_supabase()
        
        # Get organization ID
        org_response = supabase.table('organizations').select('id').eq('slug', org_slug).single().execute()
        if not org_response.data:
            return jsonify({'error': 'Organization not found'}), 404
        
        org_id = org_response.data['id']
        
        # Execute the scheduled call
        scheduling_service = CallSchedulingService()
        result = scheduling_service.execute_scheduled_call(schedule_id)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'result': result,
                'message': 'Call executed successfully'
            })
        else:
            # Bubble up more context (url/payload/details) to help diagnose 500s
            error_payload = {
                'success': False,
                'error': result.get('error', 'Failed to execute call')
            }
            if 'url' in result:
                error_payload['url'] = result['url']
            if 'details' in result:
                error_payload['details'] = result['details']
            if 'payload' in result:
                error_payload['payload'] = result['payload']
            current_app.logger.error(f"Execute call failed: {error_payload}")
            return jsonify(error_payload), 500
            
    except Exception as e:
        logger.error(f"Error executing call schedule: {e}")
        return jsonify({'error': str(e)}), 500

@call_scheduling_bp.route('/<org_slug>/call-schedules/statistics', methods=['GET'])
@login_required
@require_org_member('org_slug')
def get_call_scheduling_statistics(org_slug):
    """Get call scheduling statistics for an organization"""
    try:
        supabase = get_service_supabase()
        
        # Get organization ID
        org_response = supabase.table('organizations').select('id').eq('slug', org_slug).single().execute()
        if not org_response.data:
            return jsonify({'error': 'Organization not found'}), 404
        
        org_id = org_response.data['id']
        
        # Get statistics
        scheduling_service = CallSchedulingService()
        stats = scheduling_service.get_call_scheduling_statistics(org_id)
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting call scheduling statistics: {e}")
        return jsonify({'error': str(e)}), 500

@call_scheduling_bp.route('/<org_slug>/call-schedules/trigger-overdue', methods=['POST'])
@login_required
@require_org_member('org_slug')
def trigger_overdue_calls(org_slug):
    """Manually trigger overdue calls based on check-up dates"""
    try:
        supabase = get_service_supabase()
        
        # Get organization ID
        org_response = supabase.table('organizations').select('id').eq('slug', org_slug).single().execute()
        if not org_response.data:
            return jsonify({'error': 'Organization not found'}), 404
        
        org_id = org_response.data['id']
        
        # Trigger overdue calls
        scheduling_service = CallSchedulingService()
        triggered_calls = scheduling_service.check_and_trigger_overdue_calls(org_id)
        
        return jsonify({
            'success': True,
            'triggered_calls': triggered_calls,
            'count': len(triggered_calls),
            'message': f'Triggered {len(triggered_calls)} overdue calls'
        })
        
    except Exception as e:
        logger.error(f"Error triggering overdue calls: {e}")
        return jsonify({'error': str(e)}), 500

@call_scheduling_bp.route('/<org_slug>/call-schedules/due', methods=['GET'])
@login_required
@require_org_member('org_slug')
def get_due_call_schedules(org_slug):
    """Get all call schedules that are due to be executed"""
    try:
        supabase = get_service_supabase()
        
        # Get organization ID
        org_response = supabase.table('organizations').select('id').eq('slug', org_slug).single().execute()
        if not org_response.data:
            return jsonify({'error': 'Organization not found'}), 404
        
        org_id = org_response.data['id']
        
        # Get due schedules
        scheduling_service = CallSchedulingService()
        due_schedules = scheduling_service.get_due_call_schedules(org_id)
        
        return jsonify({
            'success': True,
            'due_schedules': due_schedules,
            'count': len(due_schedules)
        })
        
    except Exception as e:
        logger.error(f"Error getting due call schedules: {e}")
        return jsonify({'error': str(e)}), 500
