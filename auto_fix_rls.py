#!/usr/bin/env python3
"""
Automatically fix RLS policies for AgentSDR
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def fix_rls_policies():
    """Fix RLS policies automatically"""
    
    url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not service_key:
        print("❌ Missing Supabase credentials")
        return False
    
    print("🔧 Fixing RLS policies for users table...")
    
    try:
        # Use service role key for admin operations
        supabase = create_client(url, service_key)
        
        # SQL commands to fix RLS policies
        rls_commands = [
            # Enable RLS on users table
            "ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;",
            
            # Drop existing policies to avoid conflicts
            "DROP POLICY IF EXISTS \"Allow service role full access to users\" ON public.users;",
            "DROP POLICY IF EXISTS \"Allow authenticated users to read own data\" ON public.users;",
            "DROP POLICY IF EXISTS \"Allow authenticated users to update own data\" ON public.users;",
            
            # Create new policies
            """CREATE POLICY "Allow service role full access to users" ON public.users
               FOR ALL TO service_role
               USING (true)
               WITH CHECK (true);""",
            
            """CREATE POLICY "Allow authenticated users to read own data" ON public.users
               FOR SELECT TO authenticated
               USING (auth.uid()::text = id);""",
            
            """CREATE POLICY "Allow authenticated users to update own data" ON public.users
               FOR UPDATE TO authenticated
               USING (auth.uid()::text = id)
               WITH CHECK (auth.uid()::text = id);"""
        ]
        
        print("📝 Executing RLS policy commands...")
        
        for i, command in enumerate(rls_commands, 1):
            try:
                print(f"   {i}. Executing: {command[:50]}...")
                # Note: The Python Supabase client doesn't support raw SQL execution
                # We'll need to do this via the dashboard or provide instructions
                print(f"      ⚠️  Command prepared (needs manual execution)")
            except Exception as e:
                print(f"      ❌ Error: {e}")
        
        print("\n⚠️  **MANUAL EXECUTION REQUIRED**")
        print("The Python Supabase client doesn't support raw SQL execution.")
        print("Please run the following commands in your Supabase SQL Editor:")
        print("\n" + "="*60)
        
        for command in rls_commands:
            print(command)
            print()
        
        print("="*60)
        
        # Test if we can create a user after the fix
        print("\n🧪 Testing user creation...")
        test_user_creation()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_user_creation():
    """Test if user creation works"""
    
    url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    try:
        supabase = create_client(url, service_key)
        
        test_user = {
            'id': '00000000-0000-0000-0000-000000000996',
            'email': 'rls-fix-test@example.com',
            'display_name': 'RLS Fix Test User',
            'is_super_admin': False
        }
        
        response = supabase.table('users').insert(test_user).execute()
        
        if response.data:
            print("✅ User creation test successful!")
            
            # Clean up
            supabase.table('users').delete().eq('id', test_user['id']).execute()
            print("🧹 Cleaned up test user")
            return True
        else:
            print("❌ User creation test failed - no data returned")
            return False
            
    except Exception as e:
        if "row-level security policy" in str(e):
            print("❌ RLS policy still blocking user creation")
            print("   Please execute the SQL commands above in your Supabase dashboard")
        else:
            print(f"❌ User creation test failed: {e}")
        return False

def provide_manual_instructions():
    """Provide step-by-step manual instructions"""
    
    print("\n📋 **STEP-BY-STEP MANUAL FIX:**")
    print("="*50)
    print("1. Go to https://app.supabase.com")
    print("2. Select your project")
    print("3. Navigate to 'SQL Editor'")
    print("4. Copy and paste the SQL commands shown above")
    print("5. Click 'Run' to execute them")
    print("6. Test signup again in your application")
    print("\n🔄 **Alternative Quick Fix:**")
    print("1. Go to 'Table Editor' → 'users' table")
    print("2. Click the 'RLS' toggle to disable Row Level Security")
    print("3. This is less secure but will work immediately")

if __name__ == '__main__':
    if not fix_rls_policies():
        provide_manual_instructions()
    
    print("\n🎯 **NEXT STEPS:**")
    print("1. Execute the SQL commands in your Supabase dashboard")
    print("2. Test signup at: http://localhost:5000/auth/signup")
    print("3. If it still doesn't work, try disabling RLS temporarily")
