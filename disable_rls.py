#!/usr/bin/env python3
"""
Disable RLS on users table to fix signup issues
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def disable_rls_via_api():
    """Disable RLS using Supabase REST API"""
    
    url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not service_key:
        print("❌ Missing Supabase credentials")
        return False
    
    print("🔧 Attempting to disable RLS on users table...")
    
    # Try using Supabase REST API to execute SQL
    api_url = f"{url}/rest/v1/rpc/exec_sql"
    
    headers = {
        'apikey': service_key,
        'Authorization': f'Bearer {service_key}',
        'Content-Type': 'application/json'
    }
    
    # SQL to disable RLS
    sql_command = "ALTER TABLE public.users DISABLE ROW LEVEL SECURITY;"
    
    payload = {
        'sql': sql_command
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            print("✅ RLS disabled successfully!")
            return True
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error making API request: {e}")
        return False

def provide_manual_instructions():
    """Provide manual instructions to disable RLS"""
    
    print("\n📋 **MANUAL INSTRUCTIONS TO DISABLE RLS:**")
    print("="*50)
    print("Since the API approach didn't work, please follow these steps:")
    print()
    print("**Method 1: Via Supabase Dashboard (Easiest)**")
    print("1. Go to https://app.supabase.com")
    print("2. Select your project")
    print("3. Navigate to 'Table Editor'")
    print("4. Click on the 'users' table")
    print("5. Look for the 'RLS' toggle button (usually at the top)")
    print("6. Click it to disable Row Level Security")
    print("7. Save/confirm the change")
    print()
    print("**Method 2: Via SQL Editor**")
    print("1. Go to https://app.supabase.com")
    print("2. Select your project")
    print("3. Navigate to 'SQL Editor'")
    print("4. Paste this command:")
    print("   ALTER TABLE public.users DISABLE ROW LEVEL SECURITY;")
    print("5. Click 'Run'")
    print()
    print("**Method 3: Enable Proper Policies (More Secure)**")
    print("1. Go to 'SQL Editor'")
    print("2. Run the commands from the fix_rls_policies.sql file")
    print()
    print("🎯 **After making the change:**")
    print("1. Test signup at: http://localhost:5000/auth/signup")
    print("2. Try creating an account with any email/password")

def test_signup_after_fix():
    """Test if signup works after RLS fix"""
    
    print("\n🧪 Testing signup after RLS fix...")
    
    try:
        from agentsdr import create_app
        
        app = create_app()
        
        with app.test_client() as client:
            with app.app_context():
                # Get signup page
                response = client.get('/auth/signup')
                
                if response.status_code != 200:
                    print("❌ Can't access signup page")
                    return False
                
                # Extract CSRF token
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.data, 'html.parser')
                csrf_input = soup.find('input', {'name': 'csrf_token'})
                csrf_token = csrf_input.get('value') if csrf_input else None
                
                if not csrf_token:
                    print("❌ No CSRF token found")
                    return False
                
                # Test signup
                import time
                unique_email = f'rlstest{int(time.time())}@example.com'
                
                signup_data = {
                    'email': unique_email,
                    'display_name': 'RLS Test User',
                    'password': 'testpassword123',
                    'confirm_password': 'testpassword123',
                    'submit': 'Sign Up',
                    'csrf_token': csrf_token
                }
                
                response = client.post('/auth/signup', data=signup_data, follow_redirects=False)
                
                if response.status_code == 302:
                    location = response.headers.get('Location', '')
                    if 'dashboard' in location:
                        print("✅ Signup test successful! Redirected to dashboard")
                        return True
                    else:
                        print(f"⚠️  Signup redirected to: {location}")
                        return False
                else:
                    print(f"❌ Signup test failed. Status: {response.status_code}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error testing signup: {e}")
        return False

if __name__ == '__main__':
    print("🚀 AgentSDR RLS Fix Tool")
    print("="*30)
    
    # Try to disable RLS via API
    if disable_rls_via_api():
        print("\n🎉 RLS disabled successfully!")
        
        # Test signup
        if test_signup_after_fix():
            print("\n✅ **SUCCESS!** Your signup should now work!")
            print("🌐 Try it at: http://localhost:5000/auth/signup")
        else:
            print("\n⚠️  RLS was disabled but signup still has issues.")
            print("Please check the Flask app logs for more details.")
    else:
        print("\n⚠️  Automatic RLS disable failed.")
        provide_manual_instructions()
    
    print("\n📝 **Remember:**")
    print("- Disabling RLS is a quick fix but less secure")
    print("- For production, consider implementing proper RLS policies")
    print("- You can re-enable RLS later and add proper policies")
