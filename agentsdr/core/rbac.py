from functools import wraps
from flask import abort, current_app, session, redirect, url_for, flash
from flask_login import current_user, login_required
from agentsdr.core.supabase_client import get_supabase, get_service_supabase
from agentsdr.core.models import UserRole, OrganizationMemberRole
from typing import Optional

def require_super_admin(f):
    """Decorator to require super admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if not current_user.is_super_admin:
            abort(403, description="Super admin access required")
        
        return f(*args, **kwargs)
    return decorated_function

def require_org_admin(org_slug_param='org_slug'):
    """Decorator to require organization admin access"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            # Super admins bypass org checks
            if current_user.is_super_admin:
                return f(*args, **kwargs)
            
            org_slug = kwargs.get(org_slug_param)
            if not org_slug:
                abort(400, description="Organization slug required")

            # Resolve slug -> org_id first
            supabase = get_service_supabase()
            org_resp = supabase.table('organizations').select('id').eq('slug', org_slug).limit(1).execute()
            if not org_resp.data:
                abort(404, description="Organization not found")
            org_id = org_resp.data[0]['id']

            # Check if user is admin of the organization
            response = supabase.table('organization_members').select('id').eq('org_id', org_id).eq('user_id', current_user.id).eq('role', 'admin').limit(1).execute()
            if not response.data:
                abort(403, description="Organization admin access required")

            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_org_member(org_slug_param='org_slug'):
    """Decorator to require organization membership"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            # Super admins bypass org checks
            if current_user.is_super_admin:
                return f(*args, **kwargs)
            
            org_slug = kwargs.get(org_slug_param)
            if not org_slug:
                abort(400, description="Organization slug required")

            # Resolve slug -> org_id
            supabase = get_service_supabase()
            org_resp = supabase.table('organizations').select('id').eq('slug', org_slug).limit(1).execute()
            if not org_resp.data:
                abort(404, description="Organization not found")
            org_id = org_resp.data[0]['id']

            # Check if user is a member of the organization
            response = supabase.table('organization_members').select('id').eq('org_id', org_id).eq('user_id', current_user.id).limit(1).execute()

            if not response.data:
                abort(403, description="Organization membership required")

            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_user_org_role(user_id: str, org_id: str) -> Optional[OrganizationMemberRole]:
    """Get the user's role in a specific organization"""
    supabase = get_supabase()
    response = supabase.table('organization_members').select('role').eq('org_id', org_id).eq('user_id', user_id).execute()
    
    if response.data:
        return OrganizationMemberRole(response.data[0]['role'])
    return None

def is_org_admin(user_id: str, org_id: str) -> bool:
    """Check if user is admin of the organization"""
    role = get_user_org_role(user_id, org_id)
    return role == OrganizationMemberRole.ADMIN

def is_org_member(user_id: str, org_id: str) -> bool:
    """Check if user is a member of the organization"""
    return get_user_org_role(user_id, org_id) is not None

def get_user_organizations(user_id: str):
    """Get all organizations the user is a member of (server-side, bypass RLS)"""
    supabase = get_service_supabase()
    response = supabase.table('organization_members').select('org_id, role').eq('user_id', user_id).execute()
    return response.data or []

def can_access_org_data(user_id: str, org_id: str) -> bool:
    """Check if user can access data from the organization"""
    if not current_user.is_authenticated:
        return False
    
    # Super admins can access all data
    if current_user.is_super_admin:
        return True
    
    # Check if user is a member of the organization
    return is_org_member(user_id, org_id)
