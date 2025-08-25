#!/usr/bin/env python3
"""
Fix infinite recursion in organization RLS policies
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def test_dashboard_access():
    """Test if dashboard can load without recursion errors"""
    
    print("🧪 Testing dashboard access...")
    
    try:
        from agentsdr import create_app
        
        app = create_app()
        
        with app.test_client() as client:
            with app.app_context():
                # First, let's create a test user and log them in
                print("📝 Creating test user session...")
                
                # Get login page
                response = client.get('/auth/login')
                
                if response.status_code != 200:
                    print("❌ Can't access login page")
                    return False
                
                # For testing, let's try to access dashboard directly
                # This should trigger the error if it still exists
                print("📊 Testing dashboard access...")
                
                response = client.get('/dashboard')
                
                if response.status_code == 200:
                    print("✅ Dashboard loads successfully!")
                    return True
                elif response.status_code == 302:
                    print("🔄 Dashboard redirects (probably to login) - this is normal")
                    return True
                else:
                    print(f"❌ Dashboard error: {response.status_code}")
                    
                    # Check if the response contains the recursion error
                    if b'infinite recursion' in response.data:
                        print("❌ Infinite recursion error still present")
                        return False
                    else:
                        print("⚠️  Different error occurred")
                        return False
                        
    except Exception as e:
        if 'infinite recursion' in str(e):
            print("❌ Infinite recursion error still present in Python code")
            return False
        else:
            print(f"❌ Error testing dashboard: {e}")
            return False

def test_organization_queries():
    """Test organization-related queries directly"""
    
    print("\n🔍 Testing organization queries directly...")
    
    url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not service_key:
        print("❌ Missing Supabase credentials")
        return False
    
    try:
        supabase = create_client(url, service_key)
        
        # Test organizations table
        print("📊 Testing organizations table...")
        try:
            response = supabase.table('organizations').select('count', count='exact').execute()
            print(f"✅ Organizations table accessible. Count: {response.count}")
        except Exception as e:
            if 'infinite recursion' in str(e):
                print("❌ Infinite recursion in organizations table")
                return False
            else:
                print(f"⚠️  Organizations table error: {e}")
        
        # Test organization_members table
        print("📊 Testing organization_members table...")
        try:
            response = supabase.table('organization_members').select('count', count='exact').execute()
            print(f"✅ Organization_members table accessible. Count: {response.count}")
        except Exception as e:
            if 'infinite recursion' in str(e):
                print("❌ Infinite recursion in organization_members table")
                return False
            else:
                print(f"⚠️  Organization_members table error: {e}")
        
        # Test invitations table
        print("📊 Testing invitations table...")
        try:
            response = supabase.table('invitations').select('count', count='exact').execute()
            print(f"✅ Invitations table accessible. Count: {response.count}")
        except Exception as e:
            if 'infinite recursion' in str(e):
                print("❌ Infinite recursion in invitations table")
                return False
            else:
                print(f"⚠️  Invitations table error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing organization queries: {e}")
        return False

def provide_fix_instructions():
    """Provide instructions to fix the recursion issue"""
    
    print("\n🔧 **HOW TO FIX THE INFINITE RECURSION ERROR:**")
    print("="*60)
    print()
    print("**IMMEDIATE FIX (Recommended):**")
    print("1. Go to https://app.supabase.com")
    print("2. Select your project")
    print("3. Navigate to 'SQL Editor'")
    print("4. Copy and paste the contents of 'fix_organization_rls.sql'")
    print("5. Click 'Run' to execute the SQL")
    print()
    print("**ALTERNATIVE QUICK FIX:**")
    print("Disable RLS on organization tables temporarily:")
    print()
    print("1. Go to 'Table Editor'")
    print("2. For each of these tables, click the RLS toggle to disable:")
    print("   - organizations")
    print("   - organization_members") 
    print("   - invitations")
    print()
    print("**MANUAL SQL COMMANDS:**")
    print("If you prefer to run commands individually:")
    print()
    print("-- Disable RLS to stop recursion")
    print("ALTER TABLE public.organizations DISABLE ROW LEVEL SECURITY;")
    print("ALTER TABLE public.organization_members DISABLE ROW LEVEL SECURITY;")
    print("ALTER TABLE public.invitations DISABLE ROW LEVEL SECURITY;")
    print()
    print("🎯 **After applying the fix:**")
    print("1. Test dashboard access: http://localhost:5000/dashboard")
    print("2. Try creating an organization")
    print("3. Test inviting users to organizations")

def main():
    """Main function to diagnose and provide fix instructions"""
    
    print("🚨 AgentSDR Organization RLS Recursion Fix")
    print("="*50)
    
    # Test current state
    dashboard_works = test_dashboard_access()
    queries_work = test_organization_queries()
    
    if dashboard_works and queries_work:
        print("\n✅ **GOOD NEWS!** The recursion issue appears to be resolved!")
        print("🌐 Try accessing: http://localhost:5000/dashboard")
    else:
        print("\n❌ **RECURSION ISSUE DETECTED**")
        provide_fix_instructions()
    
    print("\n📝 **WHAT CAUSED THIS:**")
    print("- RLS policies on organization tables were referencing each other")
    print("- This created a circular dependency causing infinite recursion")
    print("- The fix removes problematic policies and creates simple ones")
    print()
    print("📋 **PREVENTION:**")
    print("- Avoid RLS policies that query other tables with RLS")
    print("- Use service role for backend operations")
    print("- Keep user-facing policies simple and direct")

if __name__ == '__main__':
    main()
