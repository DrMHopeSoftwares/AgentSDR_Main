from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from agentsdr.main import main_bp
from agentsdr.core.supabase_client import get_supabase, get_service_supabase
from agentsdr.core.rbac import get_user_organizations

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('main/index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard route with robust error handling"""
    organizations = []
    recent_records = []
    error_message = None

    try:
        # Check if user is authenticated
        if not current_user or not current_user.is_authenticated:
            flash('Please log in to access the dashboard.', 'error')
            return redirect(url_for('auth.login'))

        print(f"🔍 Dashboard: User {current_user.email} (ID: {current_user.id})")

        # Get Supabase client
        from agentsdr.core.supabase_client import get_service_supabase
        supabase = get_service_supabase()

        # Get user's organization memberships
        memberships_response = supabase.table('organization_members').select('org_id, role').eq('user_id', current_user.id).execute()
        memberships = memberships_response.data or []

        print(f"🔍 Dashboard: Found {len(memberships)} memberships")

        # Get organization details
        for membership in memberships:
            try:
                org_id = membership['org_id']
                role = membership['role']

                # Get organization details
                org_response = supabase.table('organizations').select('*').eq('id', org_id).execute()

                if org_response.data:
                    org_data = org_response.data[0]
                    organizations.append({
                        'org': org_data,
                        'role': role
                    })
                    print(f"✅ Added: {org_data['name']} (role: {role})")
                else:
                    print(f"⚠️ Organization not found: {org_id}")

            except Exception as org_error:
                print(f"❌ Error processing org {membership}: {org_error}")
                continue

        print(f"🔍 Dashboard: Final count: {len(organizations)} organizations")

    except Exception as e:
        error_message = str(e)
        print(f"❌ Dashboard error: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Error loading dashboard: {error_message}', 'error')

    # Always return a response, even if there are errors
    return render_template('main/dashboard_simple.html',
                         organizations=organizations,
                         recent_records=recent_records,
                         error_message=error_message)

@main_bp.route('/org/<org_slug>')
@login_required
def org_dashboard(org_slug):
    try:
        supabase = get_supabase()
        
        # Get organization details
        org_response = supabase.table('organizations').select('*').eq('slug', org_slug).execute()
        if not org_response.data:
            flash('Organization not found.', 'error')
            return redirect(url_for('main.dashboard'))
        
        organization = org_response.data[0]
        
        # Check if user is a member
        member_response = supabase.table('organization_members').select('*').eq('org_id', organization['id']).eq('user_id', current_user.id).execute()
        if not member_response.data and not current_user.is_super_admin:
            flash('Access denied.', 'error')
            return redirect(url_for('main.dashboard'))
        
        # Get organization stats
        records_count = supabase.table('records').select('id', count='exact').eq('org_id', organization['id']).execute()
        members_count = supabase.table('organization_members').select('id', count='exact').eq('org_id', organization['id']).execute()
        
        # Get recent records
        recent_records = supabase.table('records').select('*').eq('org_id', organization['id']).order('created_at', desc=True).limit(10).execute()
        
        # Get members
        members_response = supabase.table('organization_members').select('user_id, role, joined_at').eq('org_id', organization['id']).execute()
        members = []
        for member in members_response.data:
            user_response = supabase.table('users').select('email, display_name').eq('id', member['user_id']).execute()
            if user_response.data:
                user_data = user_response.data[0]
                members.append({
                    'email': user_data['email'],
                    'display_name': user_data.get('display_name'),
                    'role': member['role'],
                    'joined_at': member['joined_at']
                })
        
        return render_template('main/org_dashboard.html',
                             organization=organization,
                             records_count=records_count.count if records_count.count else 0,
                             members_count=members_count.count if members_count.count else 0,
                             recent_records=recent_records.data,
                             members=members)
    
    except Exception as e:
        flash('Error loading organization dashboard.', 'error')
        return redirect(url_for('main.dashboard'))


@main_bp.route('/agents')
@login_required
def all_agents():
    """Show all agents across all organizations the user has access to"""
    try:
        supabase = get_service_supabase()

        # Get all organizations where user is a member
        memberships = supabase.table('organization_members').select('org_id, role').eq('user_id', current_user.id).execute()

        if not memberships.data and not current_user.is_super_admin:
            flash('You are not a member of any organizations.', 'info')
            return render_template('main/all_agents.html', agents=[], organizations={})

        # Collect organization IDs
        org_ids = [m['org_id'] for m in memberships.data] if memberships.data else []

        # If super admin, get all organizations
        if current_user.is_super_admin:
            all_orgs = supabase.table('organizations').select('id').execute()
            org_ids.extend([org['id'] for org in all_orgs.data if org['id'] not in org_ids])

        # Get organization details
        organizations = {}
        if org_ids:
            orgs_response = supabase.table('organizations').select('id, name, slug').in_('id', org_ids).execute()
            for org in orgs_response.data:
                organizations[org['id']] = org

        # Get all agents from these organizations
        agents = []
        if org_ids:
            agents_response = supabase.table('agents').select('*').in_('org_id', org_ids).order('created_at', desc=True).execute()
            agents = agents_response.data or []

        # Add organization info to each agent
        for agent in agents:
            agent['organization'] = organizations.get(agent['org_id'], {'name': 'Unknown', 'slug': 'unknown'})

        return render_template('main/all_agents.html', agents=agents, organizations=organizations)

    except Exception as e:
        flash('Error loading agents.', 'error')
        return redirect(url_for('main.dashboard'))
