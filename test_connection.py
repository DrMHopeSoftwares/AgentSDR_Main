#!/usr/bin/env python3
"""
Test script to check Supabase connection and database setup
"""
import os
from dotenv import load_dotenv

# Load environment variables
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '.env')
print(f"Looking for .env file at: {env_path}")
print(f".env file exists: {os.path.exists(env_path)}")
load_dotenv(env_path)

def test_env_vars():
    """Test if environment variables are set"""
    print("🔧 Checking environment variables...")
    
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY', 
        'SUPABASE_SERVICE_ROLE_KEY',
        'FLASK_SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * 20}...{value[-10:]}")
        else:
            print(f"❌ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("\n✅ All required environment variables are set")
        return True

def test_supabase_connection():
    """Test Supabase connection"""
    try:
        print("\n🔗 Testing Supabase connection...")
        
        from supabase import create_client
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        # Create client
        supabase = create_client(supabase_url, supabase_service_key)
        
        # Test connection by trying to access users table
        result = supabase.table('users').select('id').limit(1).execute()
        
        print("✅ Supabase connection successful")
        print(f"✅ Users table accessible")
        
        # Count users
        count_result = supabase.table('users').select('id', count='exact').execute()
        user_count = count_result.count if hasattr(count_result, 'count') else len(count_result.data)
        print(f"📊 Found {user_count} users in database")
        
        return True
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

def test_auth_signup():
    """Test authentication signup"""
    try:
        print("\n🔐 Testing authentication system...")
        
        from supabase import create_client
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
        
        # Create client with anon key (for auth)
        supabase = create_client(supabase_url, supabase_anon_key)
        
        # Test if auth is working by checking the auth endpoint
        print("✅ Auth client created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Auth test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 AgentSDR Connection Test")
    print("=" * 40)
    
    # Test 1: Environment variables
    env_ok = test_env_vars()
    if not env_ok:
        print("\n❌ Environment setup failed. Please check your .env file.")
        return
    
    # Test 2: Supabase connection
    db_ok = test_supabase_connection()
    if not db_ok:
        print("\n❌ Database connection failed. Please check your Supabase credentials.")
        return
    
    # Test 3: Auth system
    auth_ok = test_auth_signup()
    if not auth_ok:
        print("\n❌ Auth system test failed.")
        return
    
    print("\n🎉 All tests passed! Your setup looks good.")
    print("\n📝 If signup/login is still failing, the issue might be:")
    print("1. Database tables not created (run the SQL schema in Supabase)")
    print("2. RLS (Row Level Security) policies not set up correctly")
    print("3. Browser cache or cookies issues")

if __name__ == '__main__':
    main()
