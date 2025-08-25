from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from agentsdr.admin import admin_bp
from agentsdr.core.supabase_client import get_service_supabase
from agentsdr.core.rbac import require_super_admin
from datetime import datetime

@admin_bp.route('/')
@require_super_admin
def index():
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/dashboard')
@require_super_admin
def dashboard():
    try:
        supabase = get_service_supabase()

        # Get platform stats
        orgs_count = supabase.table('organizations').select('id', count='exact').execute()
        users_count = supabase.table('users').select('id', count='exact').execute()
        records_count = supabase.table('records').select('id', count='exact').execute()

        # Get recent organizations
        recent_orgs = supabase.table('organizations').select('*').order('created_at', desc=True).limit(5).execute()

        # Get recent users
        recent_users = supabase.table('users').select('*').order('created_at', desc=True).limit(5).execute()

        return render_template('admin/dashboard.html',
                             orgs_count=orgs_count.count if orgs_count.count else 0,
                             users_count=users_count.count if users_count.count else 0,
                             records_count=records_count.count if records_count.count else 0,
                             recent_orgs=recent_orgs.data,
                             recent_users=recent_users.data)

    except Exception as e:
        flash('Error loading admin dashboard.', 'error')
        return redirect(url_for('main.dashboard'))

@admin_bp.route('/organizations')
@require_super_admin
def list_organizations():
    try:
        supabase = get_service_supabase()

        # Get all organizations with member counts
        orgs_response = supabase.table('organizations').select('*').order('created_at', desc=True).execute()

        organizations = []
        for org in orgs_response.data:
            # Get member count for each org
            members_count = supabase.table('organization_members').select('id', count='exact').eq('org_id', org['id']).execute()
            org['member_count'] = members_count.count if members_count.count else 0
            organizations.append(org)

        return render_template('admin/organizations.html', organizations=organizations)

    except Exception as e:
        flash('Error loading organizations.', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/organizations/<org_id>')
@require_super_admin
def view_organization(org_id):
    try:
        supabase = get_service_supabase()

        # Get organization
        org_response = supabase.table('organizations').select('*').eq('id', org_id).execute()
        if not org_response.data:
            flash('Organization not found.', 'error')
            return redirect(url_for('admin.list_organizations'))

        organization = org_response.data[0]

        # Get members
        members_response = supabase.table('organization_members').select('user_id, role, joined_at').eq('org_id', org_id).execute()
        members = []
        for member in members_response.data:
            user_response = supabase.table('users').select('email, display_name').eq('id', member['user_id']).execute()
            if user_response.data:
                user_data = user_response.data[0]
                members.append({
                    'user_id': member['user_id'],
                    'email': user_data['email'],
                    'display_name': user_data.get('display_name'),
                    'role': member['role'],
                    'joined_at': member['joined_at']
                })

        # Get records count
        records_count = supabase.table('records').select('id', count='exact').eq('org_id', org_id).execute()

        # Get recent records
        recent_records = supabase.table('records').select('*').eq('org_id', org_id).order('created_at', desc=True).limit(10).execute()

        return render_template('admin/organization_detail.html',
                             organization=organization,
                             members=members,
                             records_count=records_count.count if records_count.count else 0,
                             recent_records=recent_records.data)

    except Exception as e:
        flash('Error loading organization details.', 'error')
        return redirect(url_for('admin.list_organizations'))

@admin_bp.route('/users')
@require_super_admin
def list_users():
    try:
        supabase = get_service_supabase()

        # Get all users with organization counts
        users_response = supabase.table('users').select('*').order('created_at', desc=True).execute()

        users = []
        for user in users_response.data:
            # Get organization count for each user
            orgs_count = supabase.table('organization_members').select('id', count='exact').eq('user_id', user['id']).execute()
            user['org_count'] = orgs_count.count if orgs_count.count else 0
            users.append(user)

        return render_template('admin/users.html', users=users)

    except Exception as e:
        flash('Error loading users.', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/users/<user_id>')
@require_super_admin
def view_user(user_id):
    try:
        supabase = get_service_supabase()

        # Get user
        user_response = supabase.table('users').select('*').eq('id', user_id).execute()
        if not user_response.data:
            flash('User not found.', 'error')
            return redirect(url_for('admin.list_users'))

        user = user_response.data[0]

        # Get user's organizations
        orgs_response = supabase.table('organization_members').select('org_id, role, joined_at').eq('user_id', user_id).execute()
        organizations = []
        for org_member in orgs_response.data:
            org_response = supabase.table('organizations').select('*').eq('id', org_member['org_id']).execute()
            if org_response.data:
                org_data = org_response.data[0]
                organizations.append({
                    'org': org_data,
                    'role': org_member['role'],
                    'joined_at': org_member['joined_at']
                })

        # Get user's records count
        records_count = supabase.table('records').select('id', count='exact').eq('created_by', user_id).execute()

        # Get recent records
        recent_records = supabase.table('records').select('*').eq('created_by', user_id).order('created_at', desc=True).limit(10).execute()

        return render_template('admin/user_detail.html',
                             user=user,
                             organizations=organizations,
                             records_count=records_count.count if records_count.count else 0,
                             recent_records=recent_records.data)

    except Exception as e:
        flash('Error loading user details.', 'error')
        return redirect(url_for('admin.list_users'))

@admin_bp.route('/users/<user_id>/toggle-super-admin', methods=['POST'])
@require_super_admin
def toggle_super_admin(user_id):
    try:
        supabase = get_service_supabase()

        # Get current user status
        user_response = supabase.table('users').select('is_super_admin').eq('id', user_id).execute()
        if not user_response.data:
            return jsonify({'error': 'User not found'}), 404

        current_status = user_response.data[0]['is_super_admin']
        new_status = not current_status

        # Update user
        supabase.table('users').update({'is_super_admin': new_status}).eq('id', user_id).execute()

        status_text = 'Super Admin' if new_status else 'Regular User'
        flash(f'User status updated to {status_text}.', 'success')
        return jsonify({'success': True, 'is_super_admin': new_status})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
