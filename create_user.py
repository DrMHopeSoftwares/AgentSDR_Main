#!/usr/bin/env python3
"""
Direct user creation script that bypasses Supabase auth
"""
import os
import sys
import uuid
from dotenv import load_dotenv

sys.path.insert(0, '.')
load_dotenv()

def create_user_directly(email, display_name, password, is_super_admin=False):
    """Create user directly in the database"""
    try:
        from supabase import create_client
        
        url = os.getenv('SUPABASE_URL')
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        anon_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not url or not service_key:
            print("ERROR: Missing Supabase credentials in .env file")
            return False
        
        # First try to create auth user
        print("Step 1: Creating Supabase auth user...")
        try:
            auth_client = create_client(url, anon_key)
            auth_response = auth_client.auth.sign_up({
                'email': email,
                'password': password
            })
            print(f"Auth user created: {auth_response.user.id if auth_response.user else 'None'}")
            auth_user_id = auth_response.user.id if auth_response.user else None
        except Exception as auth_error:
            print(f"Auth creation failed: {auth_error}")
            print("Will create user in database only...")
            auth_user_id = None
        
        # Create user in our users table
        print("Step 2: Creating user in database...")
        service_client = create_client(url, service_key)
        
        user_id = auth_user_id if auth_user_id else str(uuid.uuid4())
        user_data = {
            'id': user_id,
            'email': email,
            'display_name': display_name,
            'is_super_admin': is_super_admin
        }
        
        response = service_client.table('users').insert(user_data).execute()
        
        if response.data:
            print(f"SUCCESS: User created!")
            print(f"  Email: {email}")
            print(f"  Display Name: {display_name}")
            print(f"  Super Admin: {is_super_admin}")
            print(f"  User ID: {user_id}")
            
            if not auth_user_id:
                print("NOTE: User was created in database only. Auth signup failed.")
                print("You may need to use the 'Reset Password' feature to set up login.")
            
            return True
        else:
            print("ERROR: Failed to create user in database")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("AgentSDR - Direct User Creation")
    print("=" * 35)
    
    if len(sys.argv) < 4:
        print("Usage: python create_user.py <email> <display_name> <password> [super_admin]")
        print("Example: python create_user.py admin@company.com 'Admin User' mypassword123 true")
        sys.exit(1)
    
    email = sys.argv[1].strip()
    display_name = sys.argv[2].strip()
    password = sys.argv[3].strip()
    is_super_admin = len(sys.argv) > 4 and sys.argv[4].lower() in ['true', '1', 'yes']
    
    if not email or not display_name or not password:
        print("ERROR: Email, display name, and password are required")
        sys.exit(1)
    
    print(f"Creating user: {email}")
    print(f"Display name: {display_name}")
    print(f"Super admin: {is_super_admin}")
    print()
    
    success = create_user_directly(email, display_name, password, is_super_admin)
    
    if success:
        print(f"\nUser {email} created successfully!")
        if is_super_admin:
            print("This user has super admin privileges.")
        print("You can now try to log in at http://127.0.0.1:5000/login")
    else:
        print("\nFailed to create user. Please check the errors above.")