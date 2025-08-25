from flask import render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from agentsdr.auth import auth_bp
from agentsdr.auth.forms import LoginForm, SignupForm, ForgotPasswordForm, ResetPasswordForm
from agentsdr.auth.models import User
from agentsdr.core.supabase_client import get_supabase, supabase
from agentsdr.core.email import get_email_service
from agentsdr.core.rbac import require_super_admin
from datetime import datetime, timedelta
import uuid
import secrets

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        try:
            supabase_client = get_supabase()
            response = supabase_client.auth.sign_in_with_password({
                'email': form.email.data,
                'password': form.password.data
            })
            
            if response.user:
                # Get or create user in our app
                user = User.get_by_email(form.email.data)
                if not user:
                    user = User.create_user(
                        email=form.email.data,
                        display_name=form.email.data.split('@')[0]
                    )
                
                if user:
                    login_user(user, remember=form.remember_me.data)
                    
                    # Store Supabase tokens in session
                    supabase.set_session(
                        response.session.access_token,
                        response.session.refresh_token
                    )
                    
                    next_page = request.args.get('next')
                    if not next_page or not next_page.startswith('/'):
                        next_page = url_for('main.dashboard')
                    
                    flash('Login successful!', 'success')
                    return redirect(next_page)
                else:
                    flash('Failed to create user profile.', 'error')
            else:
                flash('Invalid email or password.', 'error')
        except Exception as e:
            current_app.logger.error(f"Login error: {e}")
            print(f"DEBUG - Login error: {e}")  # Debug logging
            flash('Login failed. Please try again.', 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = SignupForm()
    print(f"DEBUG - Signup route accessed, method: {request.method}")  # Debug logging
    if form.validate_on_submit():
        print(f"DEBUG - Signup form submitted for: {form.email.data}")  # Debug logging
        try:
            supabase_client = get_supabase()

            # Try to create user in Supabase Auth
            try:
                print(f"DEBUG - Attempting Supabase signup for: {form.email.data}")  # Debug logging
                response = supabase_client.auth.sign_up({
                    'email': form.email.data,
                    'password': form.password.data
                })
                
                if response.user:
                    print(f"DEBUG - Supabase user created: {response.user.id}")  # Debug logging
                    # Create user in our app
                    print(f"DEBUG - About to call User.create_user with email: {form.email.data}")  # Debug logging
                    user = User.create_user(
                        email=form.email.data,
                        display_name=form.display_name.data
                    )
                    print(f"DEBUG - User.create_user returned: {user}")  # Debug logging

                    if user:
                        print(f"DEBUG - App user created successfully: {user.id}")  # Debug logging
                        login_user(user)

                        # Store Supabase tokens in session
                        supabase.set_session(
                            response.session.access_token,
                            response.session.refresh_token
                        )

                        flash('Account created successfully!', 'success')
                        return redirect(url_for('main.dashboard'))
                    else:
                        print("DEBUG - Failed to create user in app database")  # Debug logging
                        flash('Failed to create user profile.', 'error')
                else:
                    print(f"DEBUG - Supabase signup failed: {response}")  # Debug logging
                    flash('Failed to create account.', 'error')
                    
            except Exception as auth_error:
                print(f"DEBUG - Supabase auth error: {auth_error}")  # Debug logging
                # Check if the error is about user already existing
                if "User already registered" in str(auth_error):
                    print("DEBUG - User already registered error")  # Debug logging
                    # User exists in Auth, check if they exist in our database
                    existing_user = User.get_by_email(form.email.data)
                    if existing_user:
                        flash('An account with this email already exists. Please sign in instead.', 'error')
                        return redirect(url_for('auth.login'))
                    else:
                        # User exists in Auth but not in our database - sync them
                        try:
                            # Get user from Auth and create in database
                            auth_users = supabase_client.auth.admin.list_users()
                            for auth_user in auth_users:
                                if auth_user.email == form.email.data:
                                    # Create user in database with the Auth user's ID
                                    from agentsdr.core.supabase_client import get_service_supabase
                                    service_supabase = get_service_supabase()
                                    
                                    user_data = {
                                        'id': auth_user.id,
                                        'email': auth_user.email,
                                        'display_name': form.display_name.data,
                                        'is_super_admin': False
                                    }
                                    
                                    result = service_supabase.table('users').insert(user_data).execute()
                                    if result.data:
                                        user = User(
                                            id=auth_user.id,
                                            email=auth_user.email,
                                            display_name=form.display_name.data
                                        )
                                        login_user(user)
                                        flash('Account synced successfully! Welcome back!', 'success')
                                        return redirect(url_for('main.dashboard'))
                                    break
                        except Exception as sync_error:
                            current_app.logger.error(f"Error syncing user: {sync_error}")
                        
                        flash('An account with this email already exists. Please sign in instead.', 'error')
                        return redirect(url_for('auth.login'))
                else:
                    # Re-raise other auth errors
                    raise auth_error
                    
        except Exception as e:
            current_app.logger.error(f"Signup error: {e}")
            print(f"DEBUG - General signup error: {e}")  # Debug logging
            flash('Account creation failed. Please try again.', 'error')
    else:
        print(f"DEBUG - Form validation failed. Errors: {form.errors}")  # Debug logging

    return render_template('auth/signup.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    supabase.clear_session()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/invite/accept', methods=['GET', 'POST'])
def accept_invitation():
    token = request.args.get('token')
    if not token:
        flash('Invalid invitation link.', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        supabase_client = get_supabase()
        
        # Get invitation details
        response = supabase_client.table('invitations').select('*').eq('token', token).execute()
        
        if not response.data:
            flash('Invalid or expired invitation.', 'error')
            return redirect(url_for('auth.login'))
        
        invitation = response.data[0]
        
        # Check if invitation is expired
        expires_at = datetime.fromisoformat(invitation['expires_at'].replace('Z', '+00:00'))
        if datetime.now(expires_at.tzinfo) > expires_at:
            flash('This invitation has expired.', 'error')
            return redirect(url_for('auth.login'))
        
        # Check if already accepted
        if invitation['accepted_at']:
            flash('This invitation has already been accepted.', 'error')
            return redirect(url_for('auth.login'))
        
        # Get organization details
        org_response = supabase_client.table('organizations').select('*').eq('id', invitation['org_id']).execute()
        if not org_response.data:
            flash('Organization not found.', 'error')
            return redirect(url_for('auth.login'))
        
        organization = org_response.data[0]
        
        if request.method == 'POST':
            # Handle invitation acceptance
            if current_user.is_authenticated:
                # User is already logged in, accept invitation
                return _accept_invitation_for_user(current_user, invitation, organization)
            else:
                # User needs to sign up or log in
                form = SignupForm()
                if form.validate_on_submit():
                    # Create new user
                    supabase_auth = get_supabase()
                    auth_response = supabase_auth.auth.sign_up({
                        'email': form.email.data,
                        'password': form.password.data
                    })
                    
                    if auth_response.user:
                        user = User.create_user(
                            email=form.email.data,
                            display_name=form.display_name.data
                        )
                        
                        if user:
                            login_user(user)
                            supabase.set_session(
                                auth_response.session.access_token,
                                auth_response.session.refresh_token
                            )
                            
                            return _accept_invitation_for_user(user, invitation, organization)
                
                return render_template('auth/accept_invitation.html', 
                                     invitation=invitation, 
                                     organization=organization, 
                                     form=form)
        
        # GET request - show invitation details
        if current_user.is_authenticated:
            # Check if user email matches invitation
            if current_user.email != invitation['email']:
                flash('This invitation is for a different email address.', 'error')
                return redirect(url_for('main.dashboard'))
            
            return render_template('auth/accept_invitation.html', 
                                 invitation=invitation, 
                                 organization=organization)
        else:
            # Show signup form
            form = SignupForm()
            form.email.data = invitation['email']
            return render_template('auth/accept_invitation.html', 
                                 invitation=invitation, 
                                 organization=organization, 
                                 form=form)
    
    except Exception as e:
        current_app.logger.error(f"Invitation acceptance error: {e}")
        flash('Failed to process invitation.', 'error')
        return redirect(url_for('auth.login'))

def _accept_invitation_for_user(user, invitation, organization):
    """Helper function to accept invitation for a user"""
    try:
        supabase_client = get_supabase()
        
        # Add user to organization
        member_data = {
            'org_id': invitation['org_id'],
            'user_id': user.id,
            'role': invitation['role'],
            'joined_at': datetime.utcnow().isoformat()
        }
        
        supabase_client.table('organization_members').insert(member_data).execute()
        
        # Mark invitation as accepted
        supabase_client.table('invitations').update({
            'accepted_at': datetime.utcnow().isoformat()
        }).eq('id', invitation['id']).execute()
        
        # Send welcome email
        get_email_service().send_welcome_email(user.email, organization['name'])
        
        flash(f'Welcome to {organization["name"]}!', 'success')
        return redirect(url_for('main.dashboard'))
    
    except Exception as e:
        current_app.logger.error(f"Error accepting invitation: {e}")
        flash('Failed to accept invitation.', 'error')
        return redirect(url_for('main.dashboard'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        try:
            supabase_client = get_supabase()
            supabase_client.auth.reset_password_email(form.email.data)
            flash('Password reset email sent. Please check your inbox.', 'info')
            return redirect(url_for('auth.login'))
        except Exception as e:
            current_app.logger.error(f"Password reset error: {e}")
            flash('Failed to send reset email. Please try again.', 'error')
    
    return render_template('auth/forgot_password.html', form=form)
