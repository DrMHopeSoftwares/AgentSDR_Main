#!/usr/bin/env python3
"""
Fix Row Level Security policies for the users table
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def fix_rls_policies():
    """Fix RLS policies to allow user creation"""
    
    url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not service_key:
        print("❌ Missing Supabase credentials")
        return
    
    print("🔧 Fixing Row Level Security policies...")
    
    try:
        # Use service role key for admin operations
        supabase = create_client(url, service_key)
        
        # Check current RLS status
        print("📊 Checking current RLS policies...")
        
        # Try to insert a test user to see the current state
        try:
            test_user = {
                'id': '00000000-0000-0000-0000-000000000999',
                'email': 'rls-test@example.com',
                'display_name': 'RLS Test User',
                'is_super_admin': False
            }
            
            response = supabase.table('users').insert(test_user).execute()
            print("✅ User insertion works - RLS policies are correct")
            
            # Clean up test user
            supabase.table('users').delete().eq('id', test_user['id']).execute()
            print("🧹 Cleaned up test user")
            
        except Exception as e:
            print(f"❌ User insertion failed: {e}")
            
            if "row-level security policy" in str(e):
                print("🔧 RLS policy issue detected. Attempting to fix...")
                
                # The issue is that RLS is enabled but there are no policies
                # that allow the service role to insert users
                
                # For now, let's try to disable RLS on the users table
                # This is a temporary fix - in production you'd want proper policies
                
                print("⚠️  Temporarily disabling RLS on users table...")
                print("   (In production, you should create proper RLS policies instead)")
                
                # Note: We can't execute raw SQL through the Python client easily
                # The user will need to do this in the Supabase dashboard
                
                print("\n🔧 **MANUAL FIX REQUIRED:**")
                print("1. Go to your Supabase dashboard: https://app.supabase.com")
                print("2. Navigate to your project")
                print("3. Go to 'Table Editor' → 'users' table")
                print("4. Click on the 'RLS' toggle to disable Row Level Security")
                print("   OR")
                print("5. Go to 'Authentication' → 'Policies' and create policies for the users table")
                print("\n📝 **Alternative SQL fix (run in SQL Editor):**")
                print("   ALTER TABLE public.users DISABLE ROW LEVEL SECURITY;")
                print("\n🔄 After making this change, try signup again!")
                
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_user_creation():
    """Test if user creation works now"""
    print("\n🧪 Testing user creation...")
    
    url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    supabase = create_client(url, service_key)
    
    try:
        test_user = {
            'id': '00000000-0000-0000-0000-000000000998',
            'email': 'final-test@example.com',
            'display_name': 'Final Test User',
            'is_super_admin': False
        }
        
        response = supabase.table('users').insert(test_user).execute()
        
        if response.data:
            print("✅ User creation successful!")
            
            # Clean up
            supabase.table('users').delete().eq('id', test_user['id']).execute()
            return True
        else:
            print("❌ User creation failed - no data returned")
            return False
            
    except Exception as e:
        print(f"❌ User creation failed: {e}")
        return False

if __name__ == '__main__':
    if fix_rls_policies():
        test_user_creation()
    else:
        print("\n⚠️  Please fix the RLS policies manually and then test again.")
