#!/usr/bin/env python3
"""
Create Super Admin Script for AgentSDR
This script helps you create a super admin user for your application.
"""

import os
import sys
from dotenv import load_dotenv

def create_super_admin():
    """Create a super admin user"""
    print("👑 Creating Super Admin User")
    print("=" * 40)
    
    # Load environment variables
    load_dotenv()
    
    # Check if required environment variables are set
    required_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY']
    for var in required_vars:
        if not os.getenv(var):
            print(f"❌ Missing required environment variable: {var}")
            print("Please set up your .env file first.")
            return
    
    try:
        from agentsdr.auth.models import User
        
        # Get user input
        print("\n📝 Please enter the details for your super admin account:")
        email = input("Email address: ").strip()
        display_name = input("Display name (optional): ").strip()
        
        if not email:
            print("❌ Email is required!")
            return
        
        if not display_name:
            display_name = email.split('@')[0]
        
        # Check if user already exists
        existing_user = User.get_by_email(email)
        if existing_user:
            print(f"⚠️ User with email {email} already exists!")
            response = input("Do you want to make this user a super admin? (y/n): ").strip().lower()
            if response != 'y':
                return
            
            # Update existing user to be super admin
            try:
                from agentsdr.core.supabase_client import get_service_supabase
                supabase = get_service_supabase()
                
                response = supabase.table('users').update({
                    'is_super_admin': True
                }).eq('email', email).execute()
                
                if response.data:
                    print("✅ User updated to super admin!")
                else:
                    print("❌ Failed to update user.")
            except Exception as e:
                print(f"❌ Error updating user: {e}")
            return
        
        # Create new super admin user
        user = User.create_user(
            email=email,
            display_name=display_name,
            is_super_admin=True
        )
        
        if user:
            print(f"✅ Super admin user created successfully!")
            print(f"Email: {email}")
            print(f"Display Name: {display_name}")
            print("\n🔐 You can now log in with this account.")
        else:
            print("❌ Failed to create super admin user.")
            
    except Exception as e:
        print(f"❌ Error creating super admin: {e}")
        print("\n🔧 Make sure:")
        print("1. Your .env file is set up correctly")
        print("2. Your Supabase database is running")
        print("3. The database tables have been created")

if __name__ == '__main__':
    create_super_admin()
