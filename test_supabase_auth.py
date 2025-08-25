#!/usr/bin/env python3
"""
Test Supabase authentication directly
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def test_supabase_auth():
    """Test Supabase authentication"""
    
    # Get credentials
    url = os.getenv('SUPABASE_URL')
    anon_key = os.getenv('SUPABASE_ANON_KEY')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    print("🔧 Testing Supabase Authentication")
    print("=" * 50)
    print(f"URL: {url}")
    print(f"Anon Key: {anon_key[:20]}..." if anon_key else "Anon Key: None")
    print(f"Service Key: {service_key[:20]}..." if service_key else "Service Key: None")
    print()
    
    if not url or not anon_key:
        print("❌ Missing Supabase credentials!")
        return
    
    try:
        # Test with anon key (for signup/login)
        print("📝 Testing with anon key (user auth)...")
        supabase = create_client(url, anon_key)
        
        # Test signup
        print("🔐 Testing signup...")
        test_email = "test@example.com"
        test_password = "testpassword123"
        
        try:
            response = supabase.auth.sign_up({
                'email': test_email,
                'password': test_password
            })
            
            if response.user:
                print(f"✅ Signup successful! User ID: {response.user.id}")
                print(f"   Email: {response.user.email}")
                print(f"   Email confirmed: {response.user.email_confirmed_at is not None}")
                
                if not response.user.email_confirmed_at:
                    print("⚠️  Email confirmation required!")
                    print("   Check your Supabase Auth settings")
                
            else:
                print("❌ Signup failed - no user returned")
                
        except Exception as signup_error:
            print(f"❌ Signup error: {signup_error}")
            
            # Check if user already exists
            if "User already registered" in str(signup_error):
                print("ℹ️  User already exists, testing login...")
                
                try:
                    login_response = supabase.auth.sign_in_with_password({
                        'email': test_email,
                        'password': test_password
                    })
                    
                    if login_response.user:
                        print(f"✅ Login successful! User ID: {login_response.user.id}")
                    else:
                        print("❌ Login failed")
                        
                except Exception as login_error:
                    print(f"❌ Login error: {login_error}")
        
        # Test service key connection
        print("\n🔧 Testing with service key (admin access)...")
        if service_key:
            service_supabase = create_client(url, service_key)
            
            # Test database access
            try:
                users_response = service_supabase.table('users').select('count', count='exact').execute()
                print(f"✅ Database access successful! User count: {users_response.count}")
            except Exception as db_error:
                print(f"❌ Database access error: {db_error}")
        else:
            print("❌ No service key provided")
            
    except Exception as e:
        print(f"❌ General error: {e}")

if __name__ == '__main__':
    test_supabase_auth()
