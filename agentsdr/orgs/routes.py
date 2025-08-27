from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from agentsdr.orgs import orgs_bp
from agentsdr.core.supabase_client import get_supabase, get_service_supabase
from agentsdr.core.rbac import require_org_admin, require_org_member, is_org_admin
from agentsdr.core.email import get_email_service
from agentsdr.core.models import CreateOrganizationRequest, UpdateOrganizationRequest, CreateInvitationRequest
from agentsdr.services.gmail_service import fetch_and_summarize_emails

from datetime import datetime, timedelta, timezone
import uuid
import secrets
import json

def calculate_next_run_time(schedule_time, frequency_type, day_of_week=None, day_of_month=None, one_time_datetime=None):
    """Calculate the next run time based on frequency and current time"""
    now = datetime.now(timezone.utc)
    
    if frequency_type == 'once':
        # For one-time schedules, use the specified datetime
        if one_time_datetime:
            if isinstance(one_time_datetime, str):
                return datetime.fromisoformat(one_time_datetime.replace('Z', '+00:00'))
            return one_time_datetime
        else:
            # Fallback to now + 1 hour if no datetime specified
            return now + timedelta(hours=1)
    
    hour, minute = map(int, schedule_time.split(':'))
    
    # Convert local time to UTC (assuming IST timezone UTC+5:30)
    # User enters local time, we need to convert to UTC for storage
    IST_OFFSET = timedelta(hours=5, minutes=30)
    
    if frequency_type == 'daily':
        # Calculate next run in local time first, then convert to UTC
        now_local = now + IST_OFFSET  # Convert UTC to local
        next_run_local = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if next_run_local <= now_local:
            next_run_local += timedelta(days=1)
            
        # Convert back to UTC for storage
        next_run = next_run_local - IST_OFFSET
    
    elif frequency_type == 'weekly':
        # Calculate in local time first, then convert to UTC
        now_local = now + IST_OFFSET
        next_run_local = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)
        current_weekday = now_local.weekday() + 1  # Convert to 1=Monday format
        
        days_until_target = (day_of_week - current_weekday) % 7
        if days_until_target == 0 and next_run_local <= now_local:
            days_until_target = 7
        
        next_run_local += timedelta(days=days_until_target)
        # Convert back to UTC
        next_run = next_run_local - IST_OFFSET
    
    elif frequency_type == 'monthly':
        # Calculate in local time first, then convert to UTC
        now_local = now + IST_OFFSET
        next_run_local = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if now_local.day < day_of_month:
            # This month
            next_run_local = next_run_local.replace(day=day_of_month)
        elif now_local.day == day_of_month and next_run_local > now_local:
            # Today but time hasn't passed
            next_run_local = next_run_local.replace(day=day_of_month)
        else:
            # Next month
            if now_local.month == 12:
                next_run_local = next_run_local.replace(year=now_local.year + 1, month=1, day=min(day_of_month, 31))
            else:
                next_month = now_local.month + 1
                # Handle months with fewer than 31 days
                import calendar
                max_day = calendar.monthrange(now_local.year, next_month)[1]
                next_run_local = next_run_local.replace(month=next_month, day=min(day_of_month, max_day))
        
        # Convert back to UTC
        next_run = next_run_local - IST_OFFSET
    
    return next_run

@orgs_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_organization():
    if request.method == 'POST':
        try:
            # Handle both JSON and form data
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()

            current_app.logger.info(f"Creating organization with data: {data}")
            current_app.logger.info(f"Current user: {current_user.id} ({current_user.email})")

            # Remove CSRF token from data before validation
            org_data = {k: v for k, v in data.items() if k != 'csrf_token'}
            current_app.logger.info(f"Filtered organization data: {org_data}")

            try:
                org_request = CreateOrganizationRequest(**org_data)
                current_app.logger.info(f"Validation successful: name={org_request.name}, slug={org_request.slug}")
            except Exception as validation_error:
                current_app.logger.error(f"Validation error: {validation_error}")
                raise validation_error

            supabase = get_service_supabase()

            # Check if slug is unique
            existing_org = supabase.table('organizations').select('id').eq('slug', org_request.slug).execute()
            if existing_org.data:
                current_app.logger.warning(f"Organization slug already exists: {org_request.slug}")
                return jsonify({'error': 'Organization slug already exists'}), 400

            # Create organization
            org_data = {
                'id': str(uuid.uuid4()),
                'name': org_request.name,
                'slug': org_request.slug,
                'owner_user_id': current_user.id,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }

            current_app.logger.info(f"Inserting organization data: {org_data}")
            org_response = supabase.table('organizations').insert(org_data).execute()

            if org_response.data:
                current_app.logger.info("Organization created successfully")

                # Add creator as admin
                member_data = {
                    'id': str(uuid.uuid4()),
                    'org_id': org_data['id'],
                    'user_id': current_user.id,
                    'role': 'admin',
                    'joined_at': datetime.utcnow().isoformat()
                }

                current_app.logger.info(f"Adding organization member: {member_data}")
                member_response = supabase.table('organization_members').insert(member_data).execute()

                if member_response.data:
                    current_app.logger.info("Organization member added successfully")
                    flash('Organization created successfully!', 'success')
                    return jsonify({
                        'success': True,
                        'message': 'Organization created successfully!',
                        'redirect': url_for('main.dashboard')  # Redirect to dashboard for now
                    })
                else:
                    current_app.logger.error("Failed to add organization member")
                    return jsonify({'error': 'Failed to add organization member'}), 500
            else:
                current_app.logger.error("Failed to create organization")
                return jsonify({'error': 'Failed to create organization'}), 500

        except Exception as e:
            current_app.logger.error(f"Error creating organization: {e}")
            import traceback
            traceback.print_exc()

            # Handle Pydantic validation errors specifically
            if hasattr(e, 'errors'):
                validation_errors = []
                for error in e.errors():
                    field = error.get('loc', ['unknown'])[0]
                    message = error.get('msg', 'Invalid value')
                    validation_errors.append(f"{field}: {message}")
                return jsonify({'error': f'Validation error: {", ".join(validation_errors)}'}), 400

            return jsonify({'error': f'Error creating organization: {str(e)}'}), 500

    return render_template('orgs/create.html')

@orgs_bp.route('/<org_slug>/edit', methods=['GET', 'POST'])
@require_org_admin('org_slug')
def edit_organization(org_slug):
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
                update_request = UpdateOrganizationRequest(**data)

                update_data = {}
                if update_request.name:
                    update_data['name'] = update_request.name
                if update_request.slug:
                    # Check if new slug is unique
                    if update_request.slug != org_slug:
                        existing_org = supabase.table('organizations').select('id').eq('slug', update_request.slug).execute()
                        if existing_org.data:
                            return jsonify({'error': 'Organization slug already exists'}), 400
                    update_data['slug'] = update_request.slug

                if update_data:
                    update_data['updated_at'] = datetime.utcnow().isoformat()
                    supabase.table('organizations').update(update_data).eq('id', organization['id']).execute()

                flash('Organization updated successfully!', 'success')
                return jsonify({'redirect': url_for('main.org_dashboard', org_slug=update_data.get('slug', org_slug))})

            except Exception as e:
                return jsonify({'error': str(e)}), 400

        return render_template('orgs/edit.html', organization=organization)

    except Exception as e:
        flash('Error loading organization.', 'error')
        return redirect(url_for('main.dashboard'))
@orgs_bp.route('/<org_slug>/manage', methods=['GET'])
@require_org_admin('org_slug')
def manage_organization(org_slug):
    """Organization admin overview page with management actions"""
    try:
        supabase = get_service_supabase()

        # Get organization
        org_response = supabase.table('organizations').select('*').eq('slug', org_slug).execute()
        if not org_response.data:
            flash('Organization not found.', 'error')
            return redirect(url_for('main.dashboard'))
        organization = org_response.data[0]

        # Counts and recent
        members_count = supabase.table('organization_members').select('id', count='exact').eq('org_id', organization['id']).execute()
        records_count = supabase.table('records').select('id', count='exact').eq('org_id', organization['id']).execute()
        invites_count = supabase.table('invitations').select('id', count='exact').eq('org_id', organization['id']).execute()

        recent_records = supabase.table('records').select('*').eq('org_id', organization['id']).order('created_at', desc=True).limit(5).execute()
        # Agents count may fail if table not yet migrated
        try:
            agents_count_resp = supabase.table('agents').select('id', count='exact').eq('org_id', organization['id']).execute()
            agents_count_val = agents_count_resp.count or 0
        except Exception:
            agents_count_val = 0

        return render_template('orgs/manage.html',
                               organization=organization,
                               members_count=members_count.count or 0,
                               records_count=records_count.count or 0,
                               invites_count=invites_count.count or 0,
                               agents_count=agents_count_val,
                               recent_records=recent_records.data or [])
    except Exception as e:
        flash('Error loading organization.', 'error')
        return redirect(url_for('main.dashboard'))


@orgs_bp.route('/<org_slug>', methods=['DELETE'])
@require_org_admin('org_slug')
def delete_organization(org_slug):
    """Delete organization and related data (admin only)."""
    try:
        supabase = get_service_supabase()
        org_resp = supabase.table('organizations').select('id').eq('slug', org_slug).execute()
        if not org_resp.data:
            return jsonify({'error': 'Organization not found'}), 404
        org_id = org_resp.data[0]['id']

        # Delete related rows first (basic cascade)
        supabase.table('organization_members').delete().eq('org_id', org_id).execute()
        supabase.table('invitations').delete().eq('org_id', org_id).execute()
        supabase.table('records').delete().eq('org_id', org_id).execute()

        # Delete organization
        supabase.table('organizations').delete().eq('id', org_id).execute()

        flash('Organization deleted successfully.', 'success')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orgs_bp.route('/<org_slug>/agents', methods=['POST'])
@require_org_admin('org_slug')
def create_agent(org_slug):
    """Create an agent for the organization. Types: email_summarizer | hubspot_data | custom"""
    try:
        current_app.logger.info(f"Creating agent for org: {org_slug}")
        current_app.logger.info(f"Request content type: {request.content_type}")
        current_app.logger.info(f"Request is_json: {request.is_json}")

        # Accept JSON or form-encoded payloads robustly
        if request.is_json:
            data = request.get_json(silent=True) or {}
        else:
            data = request.form.to_dict() or {}

        current_app.logger.info(f"Received data: {data}")

        name = (data.get('name') or '').strip()
        agent_type = (data.get('type') or '').strip()

        current_app.logger.info(f"Parsed name: '{name}', agent_type: '{agent_type}'")

        if not name or not agent_type:
            current_app.logger.error(f"Missing required fields: name='{name}', type='{agent_type}'")
            return jsonify({'error': 'Name and type are required'}), 400
        if agent_type not in ['email_summarizer', 'hubspot_data', 'custom']:
            current_app.logger.error(f"Invalid agent type: '{agent_type}'")
            return jsonify({'error': 'Invalid agent type'}), 400

        supabase = get_service_supabase()
        # Resolve slug -> id
        org_resp = supabase.table('organizations').select('id').eq('slug', org_slug).limit(1).execute()
        if not org_resp.data:
            current_app.logger.error(f"Organization not found: {org_slug}")
            return jsonify({'error': 'Organization not found'}), 404
        org_id = org_resp.data[0]['id']
        current_app.logger.info(f"Found organization ID: {org_id}")

        # Create agent record
        import json, uuid
        now = datetime.now(timezone.utc).isoformat()
        agent = {
            'id': str(uuid.uuid4()),
            'org_id': org_id,
            'name': name,
            'agent_type': agent_type,
            'config': {},
            'created_by': current_user.id,
            'created_at': now,
            'updated_at': now
        }
        current_app.logger.info(f"Creating agent: {agent}")

        result = supabase.table('agents').insert(agent).execute()
        current_app.logger.info(f"Agent created successfully: {result}")

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@orgs_bp.route('/<org_slug>/agents', methods=['GET'])
@require_org_member('org_slug')
def list_agents(org_slug):
    """List agents for an organization (records tagged as agents)."""
    try:
        supabase = get_service_supabase()
        org_resp = supabase.table('organizations').select('*').eq('slug', org_slug).limit(1).execute()
        if not org_resp.data:
            flash('Organization not found.', 'error')
            return redirect(url_for('main.dashboard'))
        organization = org_resp.data[0]

        # For now: agents are records whose content JSON has agent_type
        agents_resp = supabase.table('agents').select('*').eq('org_id', organization['id']).order('created_at', desc=True).execute()
        agents = agents_resp.data or []
        return render_template('orgs/agents.html', organization=organization, agents=agents)
    except Exception as e:
        flash('Error loading agents.', 'error')
        return redirect(url_for('main.dashboard'))



@orgs_bp.route('/<org_slug>/members')
@require_org_member('org_slug')
def list_members(org_slug):
    try:
        supabase = get_supabase()
        # Get organization
        org_response = supabase.table('organizations').select('*').eq('slug', org_slug).execute()
        if not org_response.data:
            flash('Organization not found.', 'error')
            return redirect(url_for('main.dashboard'))
        organization = org_response.data[0]

        # Get members
        members_response = supabase.table('organization_members').select('user_id, role, joined_at').eq('org_id', organization['id']).execute()
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

        return render_template('orgs/members.html', organization=organization, members=members)

    except Exception as e:
        flash('Error loading members.', 'error')
        return redirect(url_for('main.dashboard'))


@orgs_bp.route('/<org_slug>/agents/<agent_id>', methods=['PATCH'])
@require_org_admin('org_slug')
def update_agent(org_slug, agent_id):
    try:
        data = request.get_json() or {}
        updates = {}
        if 'name' in data and data['name']:
            updates['name'] = data['name']
        if not updates:
            return jsonify({'error': 'No changes provided'}), 400
        updates['updated_at'] = datetime.utcnow().isoformat()
        supabase = get_service_supabase()
        supabase.table('agents').update(updates).eq('id', agent_id).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orgs_bp.route('/<org_slug>/agents/<agent_id>', methods=['GET'])
@require_org_member('org_slug')
def view_agent(org_slug, agent_id):
    """View individual agent details and handle Email Summarizer functionality"""
    try:
        current_app.logger.info(f"Viewing agent: org_slug={org_slug}, agent_id={agent_id}")
        supabase = get_service_supabase()

        # Get organization
        org_resp = supabase.table('organizations').select('*').eq('slug', org_slug).limit(1).execute()
        if not org_resp.data:
            flash('Organization not found.', 'error')
            return redirect(url_for('main.dashboard'))
        organization = org_resp.data[0]

        # Get agent
        agent_resp = supabase.table('agents').select('*').eq('id', agent_id).eq('org_id', organization['id']).execute()
        if not agent_resp.data:
            flash('Agent not found.', 'error')
            return redirect(url_for('orgs.list_agents', org_slug=org_slug))
        agent = agent_resp.data[0]

        # Check if Gmail is connected for email_summarizer agents
        gmail_connected = False
        if agent['agent_type'] == 'email_summarizer':
            config = agent.get('config', {})
            gmail_connected = bool(config.get('gmail_refresh_token'))

        # Check if Hubspot is connected for hubspot_data agents
        hubspot_connected = False
        if agent['agent_type'] == 'hubspot_data':
            config = agent.get('config', {})
            hubspot_connected = bool(config.get('hubspot_access_token'))

        return render_template('orgs/agent_detail.html',
                             organization=organization,
                             agent=agent,
                             gmail_connected=gmail_connected,
                             hubspot_connected=hubspot_connected)

    except Exception as e:
        current_app.logger.error(f"Error viewing agent: {e}")
        flash('Error loading agent.', 'error')
        return redirect(url_for('orgs.list_agents', org_slug=org_slug))

@orgs_bp.route('/<org_slug>/agents/<agent_id>/gmail/auth')
@require_org_member('org_slug')
def gmail_auth(org_slug, agent_id):
    """Initiate Gmail OAuth flow"""
    try:
        from urllib.parse import urlencode
        import os

        # Gmail OAuth configuration
        client_id = os.getenv('GMAIL_CLIENT_ID')
        if not client_id:
            flash('Gmail OAuth not configured. Please contact administrator.', 'error')
            return redirect(url_for('orgs.view_agent', org_slug=org_slug, agent_id=agent_id))

        # OAuth parameters - use a fixed callback URL
        # Auto-detect Railway deployment or use BASE_URL
        base_url = os.getenv('BASE_URL')
        if not base_url:
            if os.getenv('RAILWAY_ENVIRONMENT'):
                # Railway deployment - construct URL from Railway environment
                service_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN')
                if service_domain:
                    base_url = f"https://{service_domain}"
                else:
                    # Fallback to request host for Railway
                    base_url = f"{request.scheme}://{request.host}"
            else:
                # Local development
                base_url = 'http://localhost:5000'
        
        redirect_uri = f"{base_url.rstrip('/')}/orgs/gmail/callback"
        current_app.logger.info(f"Gmail OAuth redirect URI: {redirect_uri}")
        current_app.logger.info(f"Request host: {request.host}")
        current_app.logger.info(f"Request scheme: {request.scheme}")
        current_app.logger.info(f"BASE_URL env: {os.getenv('BASE_URL')}")
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': 'https://www.googleapis.com/auth/gmail.readonly',
            'response_type': 'code',
            'access_type': 'offline',
            'prompt': 'consent',
            'state': f"{org_slug}:{agent_id}"
        }

        auth_url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"
        return redirect(auth_url)

    except Exception as e:
        current_app.logger.error(f"Error initiating Gmail auth: {e}")
        flash('Error connecting to Gmail.', 'error')
        return redirect(url_for('orgs.view_agent', org_slug=org_slug, agent_id=agent_id))

@orgs_bp.route('/<org_slug>/agents/<agent_id>/gmail/callback')
@require_org_member('org_slug')
def gmail_callback(org_slug, agent_id):
    """Handle Gmail OAuth callback"""
    try:
        import requests
        import os

        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')

        if error:
            flash(f'Gmail authorization failed: {error}', 'error')
            return redirect(url_for('orgs.view_agent', org_slug=org_slug, agent_id=agent_id))

        if not code:
            flash('No authorization code received.', 'error')
            return redirect(url_for('orgs.view_agent', org_slug=org_slug, agent_id=agent_id))

        # Verify state parameter
        expected_state = f"{org_slug}:{agent_id}"
        if state != expected_state:
            flash('Invalid state parameter.', 'error')
            return redirect(url_for('orgs.view_agent', org_slug=org_slug, agent_id=agent_id))

        # Exchange code for tokens
        client_id = os.getenv('GMAIL_CLIENT_ID')
        client_secret = os.getenv('GMAIL_CLIENT_SECRET')

        # Auto-detect Railway deployment or use BASE_URL
        base_url = os.getenv('BASE_URL')
        if not base_url:
            if os.getenv('RAILWAY_ENVIRONMENT'):
                # Railway deployment - construct URL from Railway environment
                service_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN')
                if service_domain:
                    base_url = f"https://{service_domain}"
                else:
                    # Fallback to request host for Railway
                    base_url = f"{request.scheme}://{request.host}"
            else:
                # Local development
                base_url = 'http://localhost:5000'
        
        redirect_uri = f"{base_url.rstrip('/')}/orgs/gmail/callback"
        current_app.logger.info(f"Token exchange redirect URI: {redirect_uri}")
        token_data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }

        token_response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
        token_json = token_response.json()

        if 'error' in token_json:
            flash(f'Token exchange failed: {token_json["error"]}', 'error')
            return redirect(url_for('orgs.view_agent', org_slug=org_slug, agent_id=agent_id))

        # Store refresh token in agent config
        supabase = get_service_supabase()
        config_update = {
            'gmail_refresh_token': token_json.get('refresh_token'),
            'gmail_access_token': token_json.get('access_token'),
            'gmail_connected_at': datetime.utcnow().isoformat()
        }

        supabase.table('agents').update({
            'config': config_update,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', agent_id).execute()

        flash('Gmail connected successfully!', 'success')
        return redirect(url_for('orgs.view_agent', org_slug=org_slug, agent_id=agent_id))

    except Exception as e:
        current_app.logger.error(f"Error in Gmail callback: {e}")
        flash('Error connecting Gmail account.', 'error')
        return redirect(url_for('orgs.view_agent', org_slug=org_slug, agent_id=agent_id))

@orgs_bp.route('/gmail/callback')
def gmail_callback_handler():
    """Fixed Gmail OAuth callback handler - No auth required for OAuth callback"""
    try:
        import requests
        import os

        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')

        current_app.logger.info(f"Gmail callback received: code={bool(code)}, state={state}, error={error}")

        if error:
            flash(f'Gmail authorization failed: {error}', 'error')
            # Redirect to login with message to try again
            return redirect(url_for('auth.login') + '?message=gmail_auth_failed')

        if not code or not state:
            flash('Invalid OAuth response.', 'error')
            return redirect(url_for('auth.login') + '?message=invalid_oauth_response')

        # Parse state to get org_slug and agent_id
        try:
            org_slug, agent_id = state.split(':', 1)
            current_app.logger.info(f"Parsed state: org_slug={org_slug}, agent_id={agent_id}")
        except ValueError:
            flash('Invalid state parameter.', 'error')
            return redirect(url_for('auth.login') + '?message=invalid_state')

        # Exchange code for tokens
        client_id = os.getenv('GMAIL_CLIENT_ID')
        client_secret = os.getenv('GMAIL_CLIENT_SECRET')

        # Auto-detect Railway deployment or use BASE_URL
        base_url = os.getenv('BASE_URL')
        if not base_url:
            if os.getenv('RAILWAY_ENVIRONMENT'):
                # Railway deployment - construct URL from Railway environment
                service_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN')
                if service_domain:
                    base_url = f"https://{service_domain}"
                else:
                    # Fallback to request host for Railway
                    base_url = f"{request.scheme}://{request.host}"
            else:
                # Local development
                base_url = 'http://localhost:5000'
        
        redirect_uri = f"{base_url.rstrip('/')}/orgs/gmail/callback"
        current_app.logger.info(f"Main callback redirect URI: {redirect_uri}")
        
        token_data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }

        current_app.logger.info(f"Attempting token exchange with Google")
        token_response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
        current_app.logger.info(f"Token response status: {token_response.status_code}")
        
        if token_response.status_code != 200:
            current_app.logger.error(f"Token exchange failed: {token_response.text}")
            return redirect(url_for('auth.login') + f'?message=token_exchange_failed&org_slug={org_slug}&agent_id={agent_id}')

        token_json = token_response.json()

        if 'error' in token_json:
            current_app.logger.error(f'Token exchange error: {token_json}')
            return redirect(url_for('auth.login') + f'?message=token_error&org_slug={org_slug}&agent_id={agent_id}')

        # Store refresh token in agent config (using service supabase to bypass RLS)
        try:
            supabase = get_service_supabase()
            config_update = {
                'gmail_refresh_token': token_json.get('refresh_token'),
                'gmail_access_token': token_json.get('access_token'),
                'gmail_connected_at': datetime.utcnow().isoformat()
            }

            current_app.logger.info(f"Updating agent {agent_id} with Gmail tokens")
            result = supabase.table('agents').update({
                'config': config_update,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('id', agent_id).execute()
            
            current_app.logger.info(f"Agent update result: {result}")

            # Redirect to login with success message and redirect info
            return redirect(url_for('auth.login') + f'?message=gmail_connected&org_slug={org_slug}&agent_id={agent_id}')
            
        except Exception as db_error:
            current_app.logger.error(f"Database update error: {db_error}")
            return redirect(url_for('auth.login') + f'?message=db_error&org_slug={org_slug}&agent_id={agent_id}')

    except Exception as e:
        current_app.logger.error(f"Error in Gmail callback: {e}")
        flash('Error connecting Gmail account.', 'error')
        return redirect(url_for('main.dashboard'))





@orgs_bp.route('/<org_slug>/agents/<agent_id>/emails/test', methods=['POST'])
@require_org_member('org_slug')
def test_gmail_connection(org_slug, agent_id):
    """Test Gmail connection without full email processing"""
    try:
        current_app.logger.info(f"Testing Gmail connection for agent {agent_id}")
        supabase = get_service_supabase()

        # Get agent and verify it's an email_summarizer
        agent_resp = supabase.table('agents').select('*').eq('id', agent_id).execute()
        if not agent_resp.data:
            return jsonify({'error': 'Agent not found'}), 404

        agent = agent_resp.data[0]
        if agent['agent_type'] != 'email_summarizer':
            return jsonify({'error': 'Agent is not an email summarizer'}), 400

        config = agent.get('config', {})
        refresh_token = config.get('gmail_refresh_token')

        if not refresh_token:
            return jsonify({'error': 'Gmail not connected'}), 400

        # Just test the connection by getting basic profile info
        from agentsdr.services.gmail_service import GmailService
        gmail_service = GmailService()
        service = gmail_service.build_gmail_service(refresh_token)
        
        # Test with a simple profile call
        profile = service.users().getProfile(userId='me').execute()
        
        return jsonify({
            'success': True,
            'message': 'Gmail connection working',
            'email': profile.get('emailAddress'),
            'total_messages': profile.get('messagesTotal', 0)
        })

    except Exception as e:
        current_app.logger.error(f"Error testing Gmail connection: {e}")
        import traceback
        current_app.logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@orgs_bp.route('/<org_slug>/agents/<agent_id>/emails/summarize', methods=['POST'])
@require_org_member('org_slug')
def summarize_emails(org_slug, agent_id):
    """Fetch and summarize emails based on criteria"""
    try:
        current_app.logger.info(f"Email summarize request: org_slug={org_slug}, agent_id={agent_id}")

        data = request.get_json()
        if not data:
            current_app.logger.error("No JSON data received, using defaults")
            data = {'type': 'last_24_hours', 'count': 10}

        # Normalize inputs coming from the UI (which may be strings)
        criteria_type = str(data.get('type', 'last_24_hours')).strip() or 'last_24_hours'
        try:
            count = int(data.get('count', 10))
        except (ValueError, TypeError):
            count = 10
        # Keep count within a reasonable range for Gmail API
        if count <= 0:
            count = 10
        if count > 100:
            count = 100
        current_app.logger.info(f"Raw data received: {data}")
        current_app.logger.info(f"Criteria: type={criteria_type}, count={count}")

        supabase = get_service_supabase()

        # Get agent and verify it's an email_summarizer
        agent_resp = supabase.table('agents').select('*').eq('id', agent_id).execute()
        if not agent_resp.data:
            return jsonify({'error': 'Agent not found'}), 404

        agent = agent_resp.data[0]
        if agent['agent_type'] != 'email_summarizer':
            return jsonify({'error': 'Agent is not an email summarizer'}), 400

        config = agent.get('config', {})
        refresh_token = config.get('gmail_refresh_token')

        if not refresh_token:
            return jsonify({'error': 'Gmail not connected'}), 400

        # Check required environment variables
        import os
        if not os.getenv('GMAIL_CLIENT_ID'):
            return jsonify({'error': 'Gmail OAuth not configured (missing GMAIL_CLIENT_ID)'}), 500
        if not os.getenv('GMAIL_CLIENT_SECRET'):
            return jsonify({'error': 'Gmail OAuth not configured (missing GMAIL_CLIENT_SECRET)'}), 500
        if not os.getenv('OPENAI_API_KEY'):
            return jsonify({'error': 'OpenAI API not configured. Please set the OPENAI_API_KEY environment variable.'}), 500

        # Fetch and summarize emails
        try:
            current_app.logger.info(f"Starting email summarization for agent {agent_id}")
            summaries = fetch_and_summarize_emails(refresh_token, criteria_type, count)
            
            current_app.logger.info(f"Email summarization completed successfully with {len(summaries)} summaries")

            current_app.logger.info(f"Returning {len(summaries)} summaries directly")

            return jsonify({
                'success': True,
                'summaries': summaries,
                'criteria_type': criteria_type,
                'count': len(summaries)
            })
            
        except Exception as fetch_error:
            current_app.logger.error(f"Error in email fetching/summarization: {fetch_error}")
            # Check if it's a token-related error
            if 'token' in str(fetch_error).lower() or 'auth' in str(fetch_error).lower():
                return jsonify({'error': 'Gmail authentication failed. Please reconnect your Gmail account.'}), 401
            elif 'quota' in str(fetch_error).lower() or 'insufficient' in str(fetch_error).lower():
                return jsonify({'error': 'OpenAI API quota exceeded. Please add credits to your OpenAI account.'}), 429
            elif 'rate' in str(fetch_error).lower():
                return jsonify({'error': 'Rate limit exceeded. Please try again in a few minutes.'}), 429
            else:
                return jsonify({'error': f'Failed to fetch emails: {str(fetch_error)}'}), 500

    except Exception as e:
        current_app.logger.error(f"Error in summarize_emails endpoint: {e}")
        import traceback
        current_app.logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500


@orgs_bp.route('/<org_slug>/agents/<agent_id>/summaries', methods=['GET'])
@require_org_member('org_slug')
def view_summaries(org_slug, agent_id):
    """View email summaries page"""
    try:
        supabase = get_service_supabase()

        # Get organization
        org_resp = supabase.table('organizations').select('*').eq('slug', org_slug).limit(1).execute()
        if not org_resp.data:
            flash('Organization not found.', 'error')
            return redirect(url_for('main.dashboard'))
        organization = org_resp.data[0]

        # Get agent
        agent_resp = supabase.table('agents').select('*').eq('id', agent_id).eq('org_id', organization['id']).execute()
        if not agent_resp.data:
            flash('Agent not found.', 'error')
            return redirect(url_for('orgs.list_agents', org_slug=org_slug))
        agent = agent_resp.data[0]

        # Check if Gmail is connected for email_summarizer agents
        gmail_connected = False
        if agent['agent_type'] == 'email_summarizer':
            config = agent.get('config', {})
            gmail_connected = bool(config.get('gmail_refresh_token'))

        # Get summaries from database using session ID
        from flask import session
        session_id = session.get(f'summaries_{agent_id}')
        
        if session_id:
            # Retrieve from database
            supabase = get_service_supabase()
            record_resp = supabase.table('records').select('*').eq('session_id', session_id).eq('record_type', 'email_summaries').limit(1).execute()
            
            if record_resp.data:
                record = record_resp.data[0]
                summaries_data = record['data']
                summaries = summaries_data.get('summaries', [])
                criteria_type = summaries_data.get('criteria_type', 'last_24_hours')
                
                current_app.logger.info(f"Retrieved {len(summaries)} summaries from database for agent {agent_id}")
                current_app.logger.info(f"Session ID: {session_id}")
                if summaries:
                    current_app.logger.info(f"First summary sender: {summaries[0].get('sender', 'Unknown')}")
                    current_app.logger.info(f"Last summary sender: {summaries[-1].get('sender', 'Unknown')}")
            else:
                current_app.logger.warning(f"No record found for session_id: {session_id}")
                summaries = []
                criteria_type = 'last_24_hours'
        else:
            current_app.logger.warning(f"No session_id found for agent {agent_id}")
            summaries = []
            criteria_type = 'last_24_hours'

        return render_template('orgs/email_summaries.html',
                             organization=organization,
                             agent=agent,
                             gmail_connected=gmail_connected,
                             summaries=summaries,
                             criteria_type=criteria_type)

    except Exception as e:
        current_app.logger.error(f"Error viewing summaries: {e}")
        flash('Error loading summaries.', 'error')
        return redirect(url_for('orgs.view_agent', org_slug=org_slug, agent_id=agent_id))


@orgs_bp.route('/<org_slug>/agents/<agent_id>/schedule', methods=['GET', 'POST'])
@require_org_member('org_slug')
def manage_schedule(org_slug, agent_id):
    """Get or create/update agent schedule"""
    try:
        current_app.logger.info(f"Managing schedule for org: {org_slug}, agent: {agent_id}")
        supabase = get_service_supabase()

        # Get organization
        org_resp = supabase.table('organizations').select('*').eq('slug', org_slug).limit(1).execute()
        if not org_resp.data:
            current_app.logger.error(f"Organization not found: {org_slug}")
            return jsonify({'error': 'Organization not found'}), 404
        organization = org_resp.data[0]
        current_app.logger.info(f"Found organization: {organization['id']}")

        # Get agent
        agent_resp = supabase.table('agents').select('*').eq('id', agent_id).eq('org_id', organization['id']).execute()
        if not agent_resp.data:
            current_app.logger.error(f"Agent not found: {agent_id}")
            return jsonify({'error': 'Agent not found'}), 404
        agent = agent_resp.data[0]
        current_app.logger.info(f"Found agent: {agent['name']}")

        if request.method == 'GET':
            # Get current schedule
            try:
                schedule_resp = supabase.table('agent_schedules').select('*').eq('agent_id', agent_id).limit(1).execute()
                schedule = schedule_resp.data[0] if schedule_resp.data else None
                current_app.logger.info(f"Retrieved schedule: {schedule}")
                
                # Get the agent's is_active status to return it
                agent_resp = supabase.table('agents').select('is_active').eq('id', agent_id).execute()
                agent_is_active = agent_resp.data[0]['is_active'] if agent_resp.data else False
                
                return jsonify({
                    'success': True,
                    'schedule': schedule,
                    'agent_is_active': agent_is_active
                })
            except Exception as e:
                current_app.logger.error(f"Error getting schedule: {e}")
                return jsonify({'error': f'Failed to get schedule: {str(e)}'}), 500
        
        elif request.method == 'POST':
            data = request.get_json()
            current_app.logger.info(f"Received schedule data: {data}")
            
            schedule_time = data.get('schedule_time')
            recipient_email = data.get('recipient_email')
            criteria_type = data.get('criteria_type', 'last_24_hours')
            frequency_type = data.get('frequency_type', 'daily')
            email_count = data.get('email_count')
            email_hours = data.get('email_hours')
            day_of_week = data.get('day_of_week')
            day_of_month = data.get('day_of_month')
            one_time_datetime = data.get('one_time_datetime')
            
            if not schedule_time or not recipient_email:
                current_app.logger.error("Missing required fields")
                return jsonify({'error': 'Schedule time and recipient email are required'}), 400
            
            # Check if schedule exists
            try:
                existing_resp = supabase.table('agent_schedules').select('*').eq('agent_id', agent_id).limit(1).execute()
                current_app.logger.info(f"Existing schedules: {existing_resp.data}")
                
                if existing_resp.data:
                    # Update existing schedule
                    schedule_id = existing_resp.data[0]['id']
                    update_data = {
                        'schedule_time': schedule_time,
                        'recipient_email': recipient_email,
                        'criteria_type': criteria_type,
                        'frequency_type': frequency_type,
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    }
                    
                    # Add optional fields if provided
                    if email_count is not None:
                        update_data['email_count'] = email_count
                    if email_hours is not None:
                        update_data['email_hours'] = email_hours
                    if day_of_week is not None:
                        update_data['day_of_week'] = day_of_week
                    if day_of_month is not None:
                        update_data['day_of_month'] = day_of_month
                    if one_time_datetime is not None:
                        update_data['one_time_datetime'] = one_time_datetime
                    
                    # Calculate next run time
                    update_data['next_run_at'] = calculate_next_run_time(
                        schedule_time, frequency_type, day_of_week, day_of_month, one_time_datetime
                    ).isoformat()
                    
                    current_app.logger.info(f"Updating schedule {schedule_id} with data: {update_data}")
                    result = supabase.table('agent_schedules').update(update_data).eq('id', schedule_id).execute()
                    current_app.logger.info(f"Update result: {result}")
                else:
                    # Create new schedule
                    schedule_data = {
                        'agent_id': agent_id,
                        'org_id': organization['id'],
                        'schedule_time': schedule_time,
                        'recipient_email': recipient_email,
                        'criteria_type': criteria_type,
                        'frequency_type': frequency_type,
                        'created_by': current_user.id,
                        'is_active': True
                    }
                    
                    # Add optional fields if provided
                    if email_count is not None:
                        schedule_data['email_count'] = email_count
                    if email_hours is not None:
                        schedule_data['email_hours'] = email_hours
                    if day_of_week is not None:
                        schedule_data['day_of_week'] = day_of_week
                    if day_of_month is not None:
                        schedule_data['day_of_month'] = day_of_month
                    if one_time_datetime is not None:
                        schedule_data['one_time_datetime'] = one_time_datetime
                    
                    # Calculate next run time
                    schedule_data['next_run_at'] = calculate_next_run_time(
                        schedule_time, frequency_type, day_of_week, day_of_month, one_time_datetime
                    ).isoformat()
                    
                    current_app.logger.info(f"Creating new schedule with data: {schedule_data}")
                    result = supabase.table('agent_schedules').insert(schedule_data).execute()
                    current_app.logger.info(f"Insert result: {result}")
                
                # Get the agent's is_active status to return it
                agent_resp = supabase.table('agents').select('is_active').eq('id', agent_id).execute()
                agent_is_active = agent_resp.data[0]['is_active'] if agent_resp.data else False
                
                return jsonify({
                    'success': True,
                    'message': 'Schedule saved successfully',
                    'agent_is_active': agent_is_active
                })
                
            except Exception as e:
                current_app.logger.error(f"Error saving schedule: {e}")
                return jsonify({'error': f'Failed to save schedule: {str(e)}'}), 500
    
    except Exception as e:
        current_app.logger.error(f"Error managing schedule: {e}")
        return jsonify({'error': f'Failed to manage schedule: {str(e)}'}), 500


@orgs_bp.route('/<org_slug>/agents/<agent_id>/schedule/toggle', methods=['POST'])
@require_org_member('org_slug')
def toggle_schedule(org_slug, agent_id):
    """Toggle agent active/inactive"""
    try:
        supabase = get_service_supabase()

        # Get organization
        org_resp = supabase.table('organizations').select('*').eq('slug', org_slug).limit(1).execute()
        if not org_resp.data:
            return jsonify({'error': 'Organization not found'}), 404
        organization = org_resp.data[0]

        # Get current agent
        agent_resp = supabase.table('agents').select('is_active').eq('id', agent_id).execute()
        if not agent_resp.data:
            return jsonify({'error': 'Agent not found'}), 404
        
        agent = agent_resp.data[0]
        new_status = not agent['is_active']
        
        # Update agent status
        supabase.table('agents').update({
            'is_active': new_status,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', agent_id).execute()
        
        return jsonify({
            'success': True,
            'is_active': new_status,
            'message': f"Agent {'activated' if new_status else 'paused'}"
        })
    
    except Exception as e:
        current_app.logger.error(f"Error toggling agent: {e}")
        return jsonify({'error': 'Failed to toggle agent'}), 500


@orgs_bp.route('/<org_slug>/agents/<agent_id>', methods=['DELETE'])
@require_org_admin('org_slug')
def delete_agent(org_slug, agent_id):
    try:
        supabase = get_service_supabase()
        supabase.table('agents').delete().eq('id', agent_id).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orgs_bp.route('/<org_slug>/members/<user_id>/remove', methods=['POST'])
@require_org_admin('org_slug')
def remove_member(org_slug, user_id):
    try:
        supabase = get_supabase()

        # Get organization
        org_response = supabase.table('organizations').select('*').eq('slug', org_slug).execute()
        if not org_response.data:
            return jsonify({'error': 'Organization not found'}), 404

        organization = org_response.data[0]

        # Check if user is trying to remove themselves
        if user_id == current_user.id:
            return jsonify({'error': 'Cannot remove yourself from the organization'}), 400

        # Remove member
        supabase.table('organization_members').delete().eq('org_id', organization['id']).eq('user_id', user_id).execute()

        flash('Member removed successfully.', 'success')
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orgs_bp.route('/<org_slug>/members/<user_id>/role', methods=['POST'])
@require_org_admin('org_slug')
def update_member_role(org_slug, user_id):
    try:
        data = request.get_json()
        new_role = data.get('role')

        if new_role not in ['admin', 'member']:
            return jsonify({'error': 'Invalid role'}), 400

        supabase = get_supabase()

        # Get organization
        org_response = supabase.table('organizations').select('*').eq('slug', org_slug).execute()
        if not org_response.data:
            return jsonify({'error': 'Organization not found'}), 404

        organization = org_response.data[0]

        # Update member role
        supabase.table('organization_members').update({'role': new_role}).eq('org_id', organization['id']).eq('user_id', user_id).execute()

        flash('Member role updated successfully.', 'success')
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orgs_bp.route('/<org_slug>/invites')
@require_org_admin('org_slug')
def list_invitations(org_slug):
    try:
        supabase = get_supabase()

        # Get organization
        org_response = supabase.table('organizations').select('*').eq('slug', org_slug).execute()
        if not org_response.data:
            flash('Organization not found.', 'error')
            return redirect(url_for('main.dashboard'))

        organization = org_response.data[0]

        # Get invitations
        invitations_response = supabase.table('invitations').select('*').eq('org_id', organization['id']).order('created_at', desc=True).execute()

        return render_template('orgs/invitations.html', organization=organization, invitations=invitations_response.data)

    except Exception as e:
        flash('Error loading invitations.', 'error')
        return redirect(url_for('main.dashboard'))

@orgs_bp.route('/<org_slug>/invites', methods=['POST'])
@require_org_admin('org_slug')
def create_invitation(org_slug):
    try:
        data = request.get_json()
        invite_request = CreateInvitationRequest(**data)

        supabase = get_supabase()

        # Get organization
        org_response = supabase.table('organizations').select('*').eq('slug', org_slug).execute()
        if not org_response.data:
            return jsonify({'error': 'Organization not found'}), 404

        organization = org_response.data[0]

        # Check if user is already a member
        existing_member = supabase.table('organization_members').select('*').eq('org_id', organization['id']).eq('user_id', invite_request.email).execute()
        if existing_member.data:
            return jsonify({'error': 'User is already a member of this organization'}), 400

        # Check if invitation already exists
        existing_invite = supabase.table('invitations').select('*').eq('org_id', organization['id']).eq('email', invite_request.email).eq('accepted_at', None).execute()
        if existing_invite.data:
            return jsonify({'error': 'Invitation already sent to this email'}), 400

        # Create invitation
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=72)

        invitation_data = {
            'id': str(uuid.uuid4()),
            'org_id': organization['id'],
            'email': invite_request.email,
            'role': invite_request.role,
            'token': token,
            'expires_at': expires_at.isoformat(),
            'invited_by': current_user.id,
            'created_at': datetime.utcnow().isoformat()
        }

        invitation_response = supabase.table('invitations').insert(invitation_data).execute()

        if invitation_response.data:
            # Send invitation email
            email_sent = get_email_service().send_invitation_email(
                invite_request.email,
                organization['name'],
                invite_request.role,
                token,
                current_user.display_name or current_user.email
            )

            if email_sent:
                flash('Invitation sent successfully!', 'success')
            else:
                flash('Invitation created but email failed to send.', 'warning')

            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to create invitation'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@orgs_bp.route('/<org_slug>/invites/<invitation_id>/resend', methods=['POST'])
@require_org_admin('org_slug')
def resend_invitation(org_slug, invitation_id):
    try:
        supabase = get_supabase()

        # Get invitation
        invitation_response = supabase.table('invitations').select('*').eq('id', invitation_id).execute()
        if not invitation_response.data:
            return jsonify({'error': 'Invitation not found'}), 404

        invitation = invitation_response.data[0]

        # Get organization
        org_response = supabase.table('organizations').select('*').eq('id', invitation['org_id']).execute()
        if not org_response.data:
            return jsonify({'error': 'Organization not found'}), 404

        organization = org_response.data[0]

        # Resend invitation email
        email_sent = get_email_service().send_invitation_email(
            invitation['email'],
            organization['name'],
            invitation['role'],
            invitation['token'],
            current_user.display_name or current_user.email
        )

        if email_sent:
            flash('Invitation resent successfully!', 'success')
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to send invitation email'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@orgs_bp.route('/mine', methods=['GET'])
@login_required
def my_organizations():
    """List organizations where the current user is admin"""
    try:
        supabase = get_service_supabase()

        # Get memberships where user is admin
        memberships = supabase.table('organization_members').select('org_id, role').eq('user_id', current_user.id).eq('role', 'admin').execute()

        # Collect org details
        orgs = []
        for m in memberships.data or []:
            org_resp = supabase.table('organizations').select('id, name, slug, owner_user_id, created_at').eq('id', m['org_id']).execute()
            if org_resp.data:
                orgs.append({
                    'org': org_resp.data[0],
                    'role': m['role']
                })

        return render_template('orgs/mine.html', organizations=orgs)
    except Exception as e:
        flash(f'Failed to load organizations: {e}', 'error')
        return render_template('orgs/mine.html', organizations=[])



@orgs_bp.route('/<org_slug>/invites/<invitation_id>', methods=['DELETE'])
@require_org_admin('org_slug')
def revoke_invitation(org_slug, invitation_id):
    try:
        supabase = get_supabase()

        # Delete invitation
        supabase.table('invitations').delete().eq('id', invitation_id).execute()

        flash('Invitation revoked successfully.', 'success')
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
# Hubspot OAuth Routes
@orgs_bp.route('/<org_slug>/agents/<agent_id>/hubspot/auth')
@require_org_member('org_slug')
def hubspot_auth(org_slug, agent_id):
    """Initiate Hubspot OAuth flow"""
    try:
        from urllib.parse import urlencode
        import os

        # Hubspot OAuth configuration
        client_id = os.getenv('HUBSPOT_CLIENT_ID')
        if not client_id:
            flash('Hubspot OAuth not configured. Please contact administrator.', 'error')
            return redirect(url_for('orgs.view_agent', org_slug=org_slug, agent_id=agent_id))

        # OAuth parameters - build redirect URI from BASE_URL to avoid host mismatch
        import os
        # Prefer explicit BASE_URL; fall back to localhost to avoid 127.0.0.1 mismatches
        base_url = os.getenv('BASE_URL') or 'http://localhost:5000'
        redirect_uri = base_url.rstrip('/') + '/orgs/hubspot/callback'
        current_app.logger.info(f"Hubspot OAuth redirect URI: {redirect_uri}")
        # Minimal scopes to avoid subscription-gated failures
        scopes = [
            'crm.objects.contacts.read',
            'oauth'
        ]

        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': ' '.join(scopes),
            'response_type': 'code',
            'state': f"{org_slug}:{agent_id}"
        }

        auth_url = f"https://app.hubspot.com/oauth/authorize?{urlencode(params)}"
        current_app.logger.info(f"HubSpot authorize URL: {auth_url}")
        return redirect(auth_url)

    except Exception as e:
        current_app.logger.error(f"Error initiating Hubspot auth: {e}")
        flash('Error connecting to Hubspot.', 'error')
        return redirect(url_for('orgs.view_agent', org_slug=org_slug, agent_id=agent_id))

@orgs_bp.route('/hubspot/callback')
def hubspot_callback_handler():
    """Handle Hubspot OAuth callback"""
    try:
        import requests
        import os

        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')

        if error:
            flash(f'Hubspot authorization failed: {error}', 'error')
            return redirect(url_for('main.dashboard'))

        if not code or not state:
            flash('Invalid OAuth response.', 'error')
            return redirect(url_for('main.dashboard'))

        # Parse state to get org_slug and agent_id
        try:
            org_slug, agent_id = state.split(':', 1)
        except ValueError:
            flash('Invalid state parameter.', 'error')
            return redirect(url_for('main.dashboard'))

        # Exchange code for tokens
        client_id = os.getenv('HUBSPOT_CLIENT_ID')
        client_secret = os.getenv('HUBSPOT_CLIENT_SECRET')

        # Build redirect URI from BASE_URL to avoid host mismatch
        # Prefer explicit BASE_URL; fall back to localhost to avoid 127.0.0.1 mismatches
        base_url = os.getenv('BASE_URL') or 'http://localhost:5000'
        redirect_uri = base_url.rstrip('/') + '/orgs/hubspot/callback'
        current_app.logger.info(f"Hubspot callback redirect URI: {redirect_uri}")
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'code': code
        }

        token_response = requests.post('https://api.hubapi.com/oauth/v1/token', data=token_data)
        token_json = token_response.json()

        if 'error' in token_json:
            flash(f'Token exchange failed: {token_json["error"]}', 'error')
            return redirect(url_for('orgs.view_agent', org_slug=org_slug, agent_id=agent_id))

        # Store access token in agent config
        supabase = get_service_supabase()
        config_update = {
            'hubspot_access_token': token_json.get('access_token'),
            'hubspot_refresh_token': token_json.get('refresh_token'),
            'hubspot_connected_at': datetime.utcnow().isoformat()
        }

        supabase.table('agents').update({
            'config': config_update,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', agent_id).execute()

        flash('Hubspot connected successfully!', 'success')
        return redirect(url_for('orgs.view_agent', org_slug=org_slug, agent_id=agent_id))

    except Exception as e:
        current_app.logger.error(f"Error in Hubspot callback: {e}")
        flash('Error connecting Hubspot account.', 'error')
        return redirect(url_for('main.dashboard'))

@orgs_bp.route('/<org_slug>/agents/<agent_id>/hubspot/test', methods=['POST'])
@require_org_member('org_slug')
def test_hubspot_connection(org_slug, agent_id):
    """Test Hubspot connection by fetching basic contact info"""
    try:
        supabase = get_service_supabase()
        
        # Get agent config
        agent_resp = supabase.table('agents').select('config').eq('id', agent_id).execute()
        if not agent_resp.data:
            return jsonify({'error': 'Agent not found'}), 404
            
        agent = agent_resp.data[0]
        config = agent.get('config', {})
        access_token = config.get('hubspot_access_token')
        
        if not access_token:
            return jsonify({'error': 'Hubspot not connected'}), 400

        # Test Hubspot API connection
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Try to fetch contacts count
        response = requests.get('https://api.hubapi.com/crm/v3/objects/contacts', headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            total_contacts = data.get('total', 0)
            return jsonify({
                'success': True,
                'total_contacts': total_contacts,
                'message': f'Successfully connected to Hubspot! Found {total_contacts} contacts.'
            })
        else:
            return jsonify({
                'error': f'Hubspot API error: {response.status_code} - {response.text}'
            }), 400

    except Exception as e:
        current_app.logger.error(f"Error testing Hubspot connection: {e}")
        return jsonify({'error': str(e)}), 500


@orgs_bp.route('/<org_slug>/agents/<agent_id>/hubspot/contacts')
@require_org_member('org_slug')
def get_hubspot_contacts(org_slug: str, agent_id: str):
    """Return a list of contacts from HubSpot for display in the UI."""
    try:
        import requests
        import os

        supabase = get_service_supabase()

        # Load agent config to get stored access token
        agent_resp = supabase.table('agents').select('config').eq('id', agent_id).execute()
        if not agent_resp.data:
            return jsonify({'error': 'Agent not found'}), 404

        config = (agent_resp.data[0] or {}).get('config', {})
        access_token = config.get('hubspot_access_token')
        refresh_token = config.get('hubspot_refresh_token')
        if not access_token:
            return jsonify({'error': 'Hubspot not connected'}), 400

        # Properties we want to pull; custom ones will be returned if present
        properties = [
            'firstname',
            'lastname',
            'email',
            'phone',
            'mobilephone',
            'check_up_date',  # custom property if exists
            'lead_summary'    # custom property if exists
        ]

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        params = {
            'limit': 25,
            'properties': ','.join(properties)
        }

        def fetch_contacts(headers_to_use):
            return requests.get('https://api.hubapi.com/crm/v3/objects/contacts', headers=headers_to_use, params=params)

        resp = fetch_contacts(headers)

        # If unauthorized/forbidden, try to refresh token once
        if resp.status_code in (401, 403) and refresh_token:
            client_id = os.getenv('HUBSPOT_CLIENT_ID')
            client_secret = os.getenv('HUBSPOT_CLIENT_SECRET')
            redirect_uri = os.getenv('HUBSPOT_REDIRECT_URI')
            try:
                token_resp = requests.post(
                    'https://api.hubapi.com/oauth/v1/token',
                    headers={'Content-Type': 'application/x-www-form-urlencoded'},
                    data={
                        'grant_type': 'refresh_token',
                        'client_id': client_id,
                        'client_secret': client_secret,
                        'redirect_uri': redirect_uri or '',
                        'refresh_token': refresh_token
                    }
                )
                if token_resp.status_code == 200:
                    token_json = token_resp.json()
                    new_access = token_json.get('access_token')
                    new_refresh = token_json.get('refresh_token') or refresh_token
                    if new_access:
                        # Persist new tokens
                        config['hubspot_access_token'] = new_access
                        config['hubspot_refresh_token'] = new_refresh
                        supabase.table('agents').update({'config': config}).eq('id', agent_id).execute()
                        # Retry with new token
                        headers_retry = {
                            'Authorization': f'Bearer {new_access}',
                            'Content-Type': 'application/json'
                        }
                        resp = fetch_contacts(headers_retry)
                else:
                    current_app.logger.warning(f"HubSpot token refresh failed: {token_resp.status_code} - {token_resp.text}")
            except Exception as refresh_err:
                current_app.logger.error(f"Error refreshing HubSpot token: {refresh_err}")

        if resp.status_code != 200:
            return jsonify({'error': f'Hubspot API error: {resp.status_code}', 'details': resp.text}), 400

        data = resp.json()
        results = []
        for item in data.get('results', []):
            props = item.get('properties', {}) or {}
            name_parts = [p for p in [props.get('firstname'), props.get('lastname')] if p]
            name = ' '.join(name_parts) if name_parts else (props.get('email') or 'Unknown')
            phone = props.get('phone') or props.get('mobilephone')
            results.append({
                'id': item.get('id'),
                'name': name,
                'phone': phone,
                'checkup_date': props.get('check_up_date'),
                'summary': props.get('lead_summary')
            })

        return jsonify({'success': True, 'contacts': results})

    except Exception as e:
        current_app.logger.error(f"Error fetching Hubspot contacts: {e}")
        return jsonify({'error': str(e)}), 500


@orgs_bp.route('/<org_slug>/agents/<agent_id>/hubspot/call', methods=['POST'])
@require_org_member('org_slug')
def hubspot_call_contact(org_slug: str, agent_id: str):
    """Initiate a call via Bolna using the provided payload contract."""
    try:
        import os
        import requests
        import json

        data = request.get_json(silent=True) or request.form.to_dict() or {}

        # Determine effective agent id: env > request > route agent_id
        req_agent_id = (data.get('agent_id') or '').strip()
        env_agent_id_raw = (os.getenv('BOLNA_AGENT_ID') or '').strip()
        # If env contains a full URL, extract the last non-empty path segment
        env_agent_id = env_agent_id_raw
        if env_agent_id_raw.startswith('http'):
            parts = [p for p in env_agent_id_raw.split('/') if p]
            env_agent_id = parts[-1] if parts else ''
        effective_agent_id = env_agent_id or req_agent_id or (agent_id or '').strip()

        recipient_phone = (data.get('recipient_phone_number') or data.get('phone_number') or data.get('phone') or '').strip()
        scheduled_at = (data.get('scheduled_at') or '').strip()
        # user_data object or flat fields
        user_data = data.get('user_data') if isinstance(data.get('user_data'), dict) else {}
        topic = (data.get('topic') or user_data.get('topic') or 'follow_up')
        language = (data.get('language') or user_data.get('language') or 'en-IN')

        if not recipient_phone:
            return jsonify({'error': 'recipient_phone_number is required'}), 400

        bolna_api_key = os.getenv('BOLNA_API_KEY')
        if not bolna_api_key:
            return jsonify({'error': 'Bolna API not configured'}), 400

        # Defaults per spec; allow env overrides
        bolna_url = (os.getenv('BOLNA_FULL_CALLS_URL') or 'https://api.bolna.ai/call').strip()
        from_number = (data.get('from_phone_number') or os.getenv('BOLNA_FROM_NUMBER') or '+918035315328')

        # Build exact payload
        bolna_payload = {
            'agent_id': effective_agent_id,
            'recipient_phone_number': recipient_phone,
            'from_phone_number': from_number,
            'user_data': { 'topic': topic, 'language': language }
        }
        if scheduled_at:
            bolna_payload['scheduled_at'] = scheduled_at

        headers = {
            'Authorization': f"Bearer {bolna_api_key}",
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        current_app.logger.info(f"Bolna request → POST {bolna_url} | Payload: {bolna_payload}")
        resp = requests.post(bolna_url, json=bolna_payload, headers=headers)
        current_app.logger.info(f"Bolna response ← Status: {resp.status_code} | Body: {resp.text}")

        if resp.status_code not in (200, 201, 202):
            return jsonify({'error': f'Bolna API error: {resp.status_code}', 'details': resp.text}), 400

        try:
            response_json = resp.json()
        except Exception:
            response_json = {'raw': resp.text}

        return jsonify({'success': True, 'provider': 'bolna', 'data': response_json})

    except Exception as e:
        current_app.logger.error(f"Error initiating call: {e}")
        return jsonify({'error': str(e)}), 500

@orgs_bp.route('/<org_slug>/agents/<agent_id>/bolna/debug', methods=['GET'])
@require_org_member('org_slug')
def bolna_debug(org_slug: str, agent_id: str):
    try:
        import os
        base = os.getenv('BOLNA_BASE_URL', 'https://api.bolna.ai')
        path = os.getenv('BOLNA_CALLS_PATH', '/v1/calls')
        method = (os.getenv('BOLNA_CALLS_METHOD', 'POST') or 'POST').upper()
        api_key_present = bool(os.getenv('BOLNA_API_KEY'))
        final_url = f"{base.rstrip('/')}{path}"
        return jsonify({
            'base_url': base,
            'calls_path': path,
            'method': method,
            'api_key_present': api_key_present,
            'final_url': final_url
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orgs_bp.route('/<org_slug>/agents/<agent_id>/toggle-state', methods=['POST'])
@require_org_member('org_slug')
def toggle_agent_state(org_slug, agent_id):
    """Toggle agent active/paused state"""
    try:
        data = request.get_json()
        is_active = data.get('is_active', True)
        agent_type = data.get('agent_type', 'unknown')
        
        current_app.logger.info(f"Toggling agent state: org_slug={org_slug}, agent_id={agent_id}, is_active={is_active}")
        
        supabase = get_service_supabase()
        
        # Get agent first to verify it exists
        agent_resp = supabase.table('agents').select('*').eq('id', agent_id).execute()
        if not agent_resp.data:
            return jsonify({'error': 'Agent not found'}), 404
            
        agent = agent_resp.data[0]
        
        # Update agent state
        update_data = {
            'is_active': is_active,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        result = supabase.table('agents').update(update_data).eq('id', agent_id).execute()
        
        if result.data:
            current_app.logger.info(f"Agent {agent_id} state updated to {'active' if is_active else 'paused'}")
            
            # If agent is being paused, also pause any active schedules for email_summarizer
            if not is_active and agent_type == 'email_summarizer':
                schedule_result = supabase.table('email_schedules').update({
                    'is_active': False,
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }).eq('agent_id', agent_id).execute()
                current_app.logger.info(f"Paused email schedules for agent {agent_id}")
                
            return jsonify({
                'success': True,
                'is_active': is_active,
                'message': f"Agent {'activated' if is_active else 'paused'} successfully"
            })
        else:
            return jsonify({'error': 'Failed to update agent state'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error toggling agent state: {e}")
        return jsonify({'error': str(e)}), 500

@orgs_bp.route('/<org_slug>/agents/<agent_id>/state', methods=['GET'])
@require_org_member('org_slug')
def get_agent_state(org_slug, agent_id):
    """Get current agent state (active/paused)"""
    try:
        current_app.logger.info(f"Getting agent state: org_slug={org_slug}, agent_id={agent_id}")
        
        supabase = get_service_supabase()
        
        # Get agent state
        agent_resp = supabase.table('agents').select('is_active, agent_type').eq('id', agent_id).execute()
        if not agent_resp.data:
            return jsonify({'error': 'Agent not found'}), 404
            
        agent = agent_resp.data[0]
        is_active = agent.get('is_active', True)  # Default to active if not set
        
        return jsonify({
            'success': True,
            'is_active': is_active,
            'agent_type': agent.get('agent_type')
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting agent state: {e}")
        return jsonify({'error': str(e)}), 500


