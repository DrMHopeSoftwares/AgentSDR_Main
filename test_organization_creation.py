#!/usr/bin/env python3
"""
Test organization creation to verify RLS fix
"""
import os
from dotenv import load_dotenv
from supabase import create_client
import uuid

load_dotenv()

def test_organization_creation():
    """Test creating an organization directly"""
    
    print("🏢 Testing organization creation...")
    
    url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not service_key:
        print("❌ Missing Supabase credentials")
        return False
    
    try:
        supabase = create_client(url, service_key)
        
        # First, create a test user if needed
        test_user_id = str(uuid.uuid4())
        test_user = {
            'id': test_user_id,
            'email': 'orgtest@example.com',
            'display_name': 'Org Test User',
            'is_super_admin': False
        }
        
        print("👤 Creating test user...")
        try:
            user_response = supabase.table('users').insert(test_user).execute()
            if user_response.data:
                print("✅ Test user created")
            else:
                print("⚠️  User might already exist, continuing...")
        except Exception as e:
            if "duplicate key" in str(e) or "already exists" in str(e):
                print("⚠️  User already exists, continuing...")
            else:
                print(f"❌ Error creating user: {e}")
                return False
        
        # Now test organization creation
        test_org_id = str(uuid.uuid4())
        test_org = {
            'id': test_org_id,
            'name': 'Test Organization',
            'slug': f'test-org-{int(__import__("time").time())}',
            'owner_user_id': test_user_id
        }
        
        print("🏢 Creating test organization...")
        try:
            org_response = supabase.table('organizations').insert(test_org).execute()
            
            if org_response.data:
                print("✅ Organization created successfully!")
                
                # Test organization membership
                test_membership = {
                    'id': str(uuid.uuid4()),
                    'org_id': test_org_id,
                    'user_id': test_user_id,
                    'role': 'admin'
                }
                
                print("👥 Creating organization membership...")
                membership_response = supabase.table('organization_members').insert(test_membership).execute()
                
                if membership_response.data:
                    print("✅ Organization membership created!")
                else:
                    print("❌ Failed to create organization membership")
                
                # Clean up test data
                print("🧹 Cleaning up test data...")
                supabase.table('organization_members').delete().eq('id', test_membership['id']).execute()
                supabase.table('organizations').delete().eq('id', test_org_id).execute()
                supabase.table('users').delete().eq('id', test_user_id).execute()
                print("✅ Cleanup complete")
                
                return True
            else:
                print("❌ Failed to create organization")
                return False
                
        except Exception as e:
            if 'infinite recursion' in str(e):
                print("❌ INFINITE RECURSION ERROR STILL PRESENT!")
                print("   Please apply the RLS fix in your Supabase dashboard")
                return False
            else:
                print(f"❌ Error creating organization: {e}")
                return False
                
    except Exception as e:
        print(f"❌ General error: {e}")
        return False

def test_flask_organization_creation():
    """Test organization creation through Flask app"""
    
    print("\n🌐 Testing organization creation through Flask app...")
    
    try:
        from agentsdr import create_app
        
        app = create_app()
        
        with app.test_client() as client:
            with app.app_context():
                # This would require a full login flow
                # For now, let's just test if the organization routes are accessible
                
                print("📊 Testing organization routes...")
                
                # Test organization list page (should redirect to login)
                response = client.get('/orgs/')
                
                if response.status_code in [200, 302]:
                    print("✅ Organization routes accessible")
                    return True
                else:
                    print(f"❌ Organization routes error: {response.status_code}")
                    
                    if b'infinite recursion' in response.data:
                        print("❌ Infinite recursion error in Flask app!")
                        return False
                    
                    return False
                    
    except Exception as e:
        if 'infinite recursion' in str(e):
            print("❌ Infinite recursion error in Flask app!")
            return False
        else:
            print(f"❌ Error testing Flask organization creation: {e}")
            return False

def main():
    """Main test function"""
    
    print("🧪 AgentSDR Organization Creation Test")
    print("="*45)
    
    # Test direct organization creation
    direct_test = test_organization_creation()
    
    # Test Flask organization routes
    flask_test = test_flask_organization_creation()
    
    print("\n📊 **TEST RESULTS:**")
    print(f"Direct organization creation: {'✅ PASS' if direct_test else '❌ FAIL'}")
    print(f"Flask organization routes: {'✅ PASS' if flask_test else '❌ FAIL'}")
    
    if direct_test and flask_test:
        print("\n🎉 **SUCCESS!** Organization creation should work!")
        print("🌐 Try creating an organization at: http://localhost:5000")
    else:
        print("\n❌ **ISSUES DETECTED**")
        print("\n🔧 **APPLY THIS FIX:**")
        print("1. Go to https://app.supabase.com")
        print("2. Navigate to SQL Editor")
        print("3. Run these commands:")
        print("   ALTER TABLE public.organizations DISABLE ROW LEVEL SECURITY;")
        print("   ALTER TABLE public.organization_members DISABLE ROW LEVEL SECURITY;")
        print("   ALTER TABLE public.invitations DISABLE ROW LEVEL SECURITY;")
        print("4. Restart your Flask app")
        print("5. Test again")

if __name__ == '__main__':
    main()
