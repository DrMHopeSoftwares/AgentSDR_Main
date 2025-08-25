#!/usr/bin/env python3
"""
Script to set up a super admin user and check user roles
"""
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

load_dotenv()

from agentsdr.core.supabase_client import get_service_supabase

def setup_super_admin(email):
    """Set a user as super admin"""
    try:
        supabase = get_service_supabase()
        
        # First, check if user exists
        user_response = supabase.table('users').select('*').eq('email', email).execute()
        
        if not user_response.data:
            print(f"❌ User with email {email} not found!")
            print("Please create an account first through the web interface.")
            return False
        
        user = user_response.data[0]
        
        # Update user to super admin
        update_response = supabase.table('users').update({
            'role': 'super_admin',
            'is_super_admin': True
        }).eq('id', user['id']).execute()
        
        if update_response.data:
            print(f"✅ Successfully set {email} as Super Admin!")
            print(f"User ID: {user['id']}")
            print(f"Role: {update_response.data[0]['role']}")
            return True
        else:
            print("❌ Failed to update user role")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def list_users():
    """List all users and their roles"""
    try:
        supabase = get_service_supabase()
        
        users_response = supabase.table('users').select('id, email, role, is_super_admin, created_at').execute()
        
        if users_response.data:
            print("\n👥 **All Users:**")
            print("-" * 80)
            for user in users_response.data:
                role_icon = "👑" if user.get('is_super_admin') else "👤"
                print(f"{role_icon} {user['email']} - Role: {user['role']} (ID: {user['id']})")
        else:
            print("No users found in the database.")
            
    except Exception as e:
        print(f"❌ Error listing users: {e}")

def check_user_role(email):
    """Check the role of a specific user"""
    try:
        supabase = get_service_supabase()
        
        user_response = supabase.table('users').select('*').eq('email', email).execute()
        
        if user_response.data:
            user = user_response.data[0]
            role_icon = "👑" if user.get('is_super_admin') else "👤"
            print(f"\n{role_icon} **User Details:**")
            print(f"Email: {user['email']}")
            print(f"Role: {user['role']}")
            print(f"Super Admin: {user.get('is_super_admin', False)}")
            print(f"Created: {user['created_at']}")
        else:
            print(f"❌ User {email} not found!")
            
    except Exception as e:
        print(f"❌ Error checking user role: {e}")

if __name__ == "__main__":
    print("🔧 AgentSDR Super Admin Setup")
    print("=" * 50)
    
    # Check if Supabase credentials are configured
    if not os.getenv('SUPABASE_URL') or os.getenv('SUPABASE_URL') == 'https://your-project.supabase.co':
        print("❌ ERROR: Supabase credentials not configured!")
        print("Please update your .env file with your actual Supabase credentials:")
        print("1. Go to your Supabase dashboard")
        print("2. Project Settings > API")
        print("3. Copy Project URL, anon key, and service role key")
        print("4. Update .env file")
        sys.exit(1)
    
    while True:
        print("\n📋 **Options:**")
        print("1. Set user as Super Admin")
        print("2. List all users")
        print("3. Check specific user role")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            email = input("Enter user email: ").strip()
            setup_super_admin(email)
            
        elif choice == "2":
            list_users()
            
        elif choice == "3":
            email = input("Enter user email: ").strip()
            check_user_role(email)
            
        elif choice == "4":
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please try again.")
