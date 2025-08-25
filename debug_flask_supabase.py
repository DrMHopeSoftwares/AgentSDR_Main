#!/usr/bin/env python3
"""
Debug Supabase configuration in Flask context
"""
import os
from dotenv import load_dotenv

load_dotenv()

def debug_flask_supabase():
    """Debug Supabase configuration in Flask context"""
    
    from agentsdr import create_app
    
    app = create_app()
    
    with app.app_context():
        print("🔍 Debugging Supabase configuration in Flask context")
        print("=" * 60)
        
        # Check environment variables
        print("📋 Environment Variables:")
        print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL')}")
        print(f"SUPABASE_ANON_KEY: {os.getenv('SUPABASE_ANON_KEY')[:20]}..." if os.getenv('SUPABASE_ANON_KEY') else "None")
        print(f"SUPABASE_SERVICE_ROLE_KEY: {os.getenv('SUPABASE_SERVICE_ROLE_KEY')[:20]}..." if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else "None")
        
        # Check Flask app config
        print("\n📋 Flask App Config:")
        print(f"SUPABASE_URL: {app.config.get('SUPABASE_URL')}")
        print(f"SUPABASE_ANON_KEY: {app.config.get('SUPABASE_ANON_KEY')[:20]}..." if app.config.get('SUPABASE_ANON_KEY') else "None")
        print(f"SUPABASE_SERVICE_ROLE_KEY: {app.config.get('SUPABASE_SERVICE_ROLE_KEY')[:20]}..." if app.config.get('SUPABASE_SERVICE_ROLE_KEY') else "None")
        
        # Test Supabase clients
        print("\n🔧 Testing Supabase Clients:")
        
        try:
            from agentsdr.core.supabase_client import get_supabase, get_service_supabase
            
            # Test anon client
            print("📝 Testing anon client...")
            anon_client = get_supabase()
            print(f"✅ Anon client created: {type(anon_client)}")
            
            # Test service client
            print("📝 Testing service client...")
            service_client = get_service_supabase()
            print(f"✅ Service client created: {type(service_client)}")
            
            # Test user creation with service client
            print("📝 Testing user creation with service client...")
            
            test_user = {
                'id': '00000000-0000-0000-0000-000000000997',
                'email': 'flask-debug@example.com',
                'display_name': 'Flask Debug User',
                'is_super_admin': False
            }
            
            response = service_client.table('users').insert(test_user).execute()
            
            if response.data:
                print("✅ User creation successful with service client!")
                
                # Clean up
                service_client.table('users').delete().eq('id', test_user['id']).execute()
                print("🧹 Cleaned up test user")
            else:
                print("❌ User creation failed - no data returned")
                
        except Exception as e:
            print(f"❌ Error testing Supabase clients: {e}")
            import traceback
            traceback.print_exc()
        
        # Test User.create_user method
        print("\n📝 Testing User.create_user method...")
        try:
            from agentsdr.auth.models import User
            
            user = User.create_user(
                email='flask-user-test@example.com',
                display_name='Flask User Test'
            )
            
            if user:
                print(f"✅ User.create_user successful: {user.id}")
            else:
                print("❌ User.create_user failed")
                
        except Exception as e:
            print(f"❌ Error in User.create_user: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    debug_flask_supabase()
