from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from agentsdr.records import records_bp
from agentsdr.core.supabase_client import get_supabase
from agentsdr.core.rbac import require_org_member, can_access_org_data
from agentsdr.core.models import CreateRecordRequest, UpdateRecordRequest
from datetime import datetime
import uuid

@records_bp.route('/<org_slug>')
@require_org_member('org_slug')
def list_records(org_slug):
    try:
        supabase = get_supabase()
        
        # Get organization
        org_response = supabase.table('organizations').select('*').eq('slug', org_slug).execute()
        if not org_response.data:
            flash('Organization not found.', 'error')
            return redirect(url_for('main.dashboard'))
        
        organization = org_response.data[0]
        
        # Get records
        records_response = supabase.table('records').select('*').eq('org_id', organization['id']).order('created_at', desc=True).execute()
        
        return render_template('records/list.html', organization=organization, records=records_response.data)
    
    except Exception as e:
        flash('Error loading records.', 'error')
        return redirect(url_for('main.dashboard'))

@records_bp.route('/<org_slug>/create', methods=['GET', 'POST'])
@require_org_member('org_slug')
def create_record(org_slug):
    try:
        supabase = get_supabase()
        
        # Get organization
        org_response = supabase.table('organizations').select('*').eq('slug', org_slug).execute()
        if not org_response.data:
            flash('Organization not found.', 'error')
            return redirect(url_for('main.dashboard'))
        
        organization = org_response.data[0]
        
        if request.method == 'POST':
            try:
                data = request.get_json()
                record_request = CreateRecordRequest(**data)
                
                # Create record
                record_data = {
                    'id': str(uuid.uuid4()),
                    'org_id': organization['id'],
                    'title': record_request.title,
                    'content': record_request.content,
                    'created_by': current_user.id,
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
                
                record_response = supabase.table('records').insert(record_data).execute()
                
                if record_response.data:
                    flash('Record created successfully!', 'success')
                    return jsonify({'redirect': url_for('records.list_records', org_slug=org_slug)})
                else:
                    return jsonify({'error': 'Failed to create record'}), 500
            
            except Exception as e:
                return jsonify({'error': str(e)}), 400
        
        return render_template('records/create.html', organization=organization)
    
    except Exception as e:
        flash('Error loading create record page.', 'error')
        return redirect(url_for('main.dashboard'))

@records_bp.route('/<org_slug>/<record_id>')
@require_org_member('org_slug')
def view_record(org_slug, record_id):
    try:
        supabase = get_supabase()
        
        # Get organization
        org_response = supabase.table('organizations').select('*').eq('slug', org_slug).execute()
        if not org_response.data:
            flash('Organization not found.', 'error')
            return redirect(url_for('main.dashboard'))
        
        organization = org_response.data[0]
        
        # Get record
        record_response = supabase.table('records').select('*').eq('id', record_id).eq('org_id', organization['id']).execute()
        if not record_response.data:
            flash('Record not found.', 'error')
            return redirect(url_for('records.list_records', org_slug=org_slug))
        
        record = record_response.data[0]
        
        # Get creator info
        creator_response = supabase.table('users').select('email, display_name').eq('id', record['created_by']).execute()
        creator = creator_response.data[0] if creator_response.data else None
        
        return render_template('records/view.html', organization=organization, record=record, creator=creator)
    
    except Exception as e:
        flash('Error loading record.', 'error')
        return redirect(url_for('main.dashboard'))

@records_bp.route('/<org_slug>/<record_id>/edit', methods=['GET', 'POST'])
@require_org_member('org_slug')
def edit_record(org_slug, record_id):
    try:
        supabase = get_supabase()
        
        # Get organization
        org_response = supabase.table('organizations').select('*').eq('slug', org_slug).execute()
        if not org_response.data:
            flash('Organization not found.', 'error')
            return redirect(url_for('main.dashboard'))
        
        organization = org_response.data[0]
        
        # Get record
        record_response = supabase.table('records').select('*').eq('id', record_id).eq('org_id', organization['id']).execute()
        if not record_response.data:
            flash('Record not found.', 'error')
            return redirect(url_for('records.list_records', org_slug=org_slug))
        
        record = record_response.data[0]
        
        if request.method == 'POST':
            try:
                data = request.get_json()
                update_request = UpdateRecordRequest(**data)
                
                update_data = {}
                if update_request.title:
                    update_data['title'] = update_request.title
                if update_request.content:
                    update_data['content'] = update_request.content
                
                if update_data:
                    update_data['updated_at'] = datetime.utcnow().isoformat()
                    supabase.table('records').update(update_data).eq('id', record_id).execute()
                
                flash('Record updated successfully!', 'success')
                return jsonify({'redirect': url_for('records.view_record', org_slug=org_slug, record_id=record_id)})
            
            except Exception as e:
                return jsonify({'error': str(e)}), 400
        
        return render_template('records/edit.html', organization=organization, record=record)
    
    except Exception as e:
        flash('Error loading record.', 'error')
        return redirect(url_for('main.dashboard'))

@records_bp.route('/<org_slug>/<record_id>', methods=['DELETE'])
@require_org_member('org_slug')
def delete_record(org_slug, record_id):
    try:
        supabase = get_supabase()
        
        # Get organization
        org_response = supabase.table('organizations').select('*').eq('slug', org_slug).execute()
        if not org_response.data:
            return jsonify({'error': 'Organization not found'}), 404
        
        organization = org_response.data[0]
        
        # Delete record
        supabase.table('records').delete().eq('id', record_id).eq('org_id', organization['id']).execute()
        
        flash('Record deleted successfully.', 'success')
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
