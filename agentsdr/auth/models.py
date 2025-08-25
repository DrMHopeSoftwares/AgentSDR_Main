from flask_login import UserMixin
from agentsdr.core.supabase_client import get_supabase, get_service_supabase
from agentsdr.core.models import User as UserModel
from typing import Optional
import uuid

class User(UserMixin):
    def __init__(self, id: str, email: str, display_name: str = None, is_super_admin: bool = False):
        self.id = id
        self.email = email
        self.display_name = display_name
        self.is_super_admin = is_super_admin
    
    @staticmethod
    def get_by_id(user_id: str) -> Optional['User']:
        """Get user by ID from Supabase"""
        try:
            supabase = get_service_supabase()
            response = supabase.table('users').select('*').eq('id', user_id).execute()
            
            if response.data:
                user_data = response.data[0]
                return User(
                    id=user_data['id'],
                    email=user_data['email'],
                    display_name=user_data.get('display_name'),
                    is_super_admin=user_data.get('is_super_admin', False)
                )
        except Exception as e:
            print(f"Error getting user by ID: {e}")
        return None
    
    @staticmethod
    def get_by_email(email: str) -> Optional['User']:
        """Get user by email from Supabase"""
        try:
            supabase = get_service_supabase()
            response = supabase.table('users').select('*').eq('email', email).execute()
            
            if response.data:
                user_data = response.data[0]
                return User(
                    id=user_data['id'],
                    email=user_data['email'],
                    display_name=user_data.get('display_name'),
                    is_super_admin=user_data.get('is_super_admin', False)
                )
        except Exception as e:
            print(f"Error getting user by email: {e}")
        return None
    
    @staticmethod
    def create_user(email: str, display_name: str = None, is_super_admin: bool = False) -> Optional['User']:
        """Create a new user in Supabase

        Role Hierarchy:
        - Super Admin: Full system access (developer/monitor role)
        - Regular User: Default role for all signups
        - Organization Admin: Becomes admin when creating an organization
        """
        try:
            supabase = get_service_supabase()

            # Only make super admin if explicitly requested (not for regular signups)
            # Regular users who sign up will be normal users
            # They become organization admins only when they create an organization

            user_data = {
                'id': str(uuid.uuid4()),
                'email': email,
                'display_name': display_name,
                'is_super_admin': is_super_admin  # False by default for regular signups
            }

            response = supabase.table('users').insert(user_data).execute()

            if response.data:
                user_role = "Super Admin" if is_super_admin else "User"
                print(f"Created {user_role}: {email}")

                return User(
                    id=user_data['id'],
                    email=email,
                    display_name=display_name,
                    is_super_admin=is_super_admin
                )
        except Exception as e:
            print(f"Error creating user: {e}")
        return None
    
    def get_organizations(self):
        """Get all organizations the user is a member of"""
        try:
            supabase = get_supabase()
            response = supabase.table('organization_members').select('org_id, role').eq('user_id', self.id).execute()
            return response.data
        except Exception as e:
            print(f"Error getting user organizations: {e}")
            return []
    
    def __repr__(self):
        return f'<User {self.email}>'
