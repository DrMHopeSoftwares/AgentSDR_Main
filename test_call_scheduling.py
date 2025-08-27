#!/usr/bin/env python3
"""
Test script for the call scheduling system
"""

import os
import sys
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def test_call_scheduling_system():
    """Test the call scheduling system components"""
    print("🧪 Testing Call Scheduling System")
    print("=" * 50)
    
    try:
        from agentsdr import create_app
        from agentsdr.services.call_scheduling_service import CallSchedulingService
        from agentsdr.services.hubspot_service import HubSpotService
        from agentsdr.core.supabase_client import get_service_supabase
        
        # Create Flask app context
        app = create_app()
        
        with app.app_context():
            print("✅ Flask app context created successfully")
            
            # Test Supabase connection
            try:
                supabase = get_service_supabase()
                print("✅ Supabase connection successful")
            except Exception as e:
                print(f"❌ Supabase connection failed: {e}")
                return False
            
            # Test HubSpot service
            try:
                hubspot_service = HubSpotService()
                print("✅ HubSpot service initialized successfully")
                
                # Test getting contacts needing follow-up
                contacts = hubspot_service.get_contacts_needing_followup(days_threshold=5)
                print(f"✅ HubSpot service working. Found {len(contacts)} contacts needing follow-up")
                
            except Exception as e:
                print(f"❌ HubSpot service test failed: {e}")
                return False
            
            # Test call scheduling service
            try:
                scheduling_service = CallSchedulingService()
                print("✅ Call scheduling service initialized successfully")
                
                # Test getting call scheduling statistics (this will fail if tables don't exist)
                try:
                    # Get first organization for testing
                    orgs_response = supabase.table('organizations').select('id, name').limit(1).execute()
                    if orgs_response.data:
                        org_id = orgs_response.data[0]['id']
                        org_name = orgs_response.data[0]['name']
                        print(f"✅ Using organization for testing: {org_name}")
                        
                        # Test getting due schedules
                        due_schedules = scheduling_service.get_due_call_schedules(org_id)
                        print(f"✅ Call scheduling service working. Found {len(due_schedules)} due schedules")
                        
                        # Test getting statistics
                        stats = scheduling_service.get_call_scheduling_statistics(org_id)
                        print(f"✅ Statistics retrieved: {stats}")
                        
                    else:
                        print("⚠️  No organizations found for testing")
                        
                except Exception as e:
                    print(f"⚠️  Call scheduling service test incomplete (tables may not exist): {e}")
                    print("   This is expected if you haven't run the database migration yet")
                
            except Exception as e:
                print(f"❌ Call scheduling service test failed: {e}")
                return False
            
            print("\n🎉 All core services are working correctly!")
            return True
            
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_tables():
    """Test if the required database tables exist"""
    print("\n🔍 Testing Database Tables")
    print("=" * 30)
    
    try:
        from agentsdr import create_app
        from agentsdr.core.supabase_client import get_service_supabase
        
        app = create_app()
        
        with app.app_context():
            supabase = get_service_supabase()
            
            # Test call_schedules table
            try:
                response = supabase.table('call_schedules').select('count').execute()
                print("✅ call_schedules table exists")
            except Exception as e:
                print(f"❌ call_schedules table not found: {e}")
                return False
            
            # Test call_schedule_rules table
            try:
                response = supabase.table('call_schedule_rules').select('count').execute()
                print("✅ call_schedule_rules table exists")
            except Exception as e:
                print(f"❌ call_schedule_rules table not found: {e}")
                return False
            
            # Test database functions
            try:
                response = supabase.rpc('get_due_call_schedules', {'org_uuid': '00000000-0000-0000-0000-000000000000'}).execute()
                print("✅ get_due_call_schedules function exists")
            except Exception as e:
                print(f"❌ get_due_call_schedules function not found: {e}")
                return False
            
            try:
                response = supabase.rpc('get_call_scheduling_statistics', {'org_uuid': '00000000-0000-0000-0000-000000000000'}).execute()
                print("✅ get_call_scheduling_statistics function exists")
            except Exception as e:
                print(f"❌ get_call_scheduling_statistics function not found: {e}")
                return False
            
            print("✅ All required database tables and functions exist")
            return True
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 AgentSDR Call Scheduling System Test")
    print("=" * 60)
    
    # Test 1: Core services
    services_ok = test_call_scheduling_system()
    
    # Test 2: Database tables
    tables_ok = test_database_tables()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    if services_ok:
        print("✅ Core Services: PASSED")
    else:
        print("❌ Core Services: FAILED")
    
    if tables_ok:
        print("✅ Database Tables: PASSED")
    else:
        print("❌ Database Tables: FAILED")
    
    if services_ok and tables_ok:
        print("\n🎉 All tests passed! Your call scheduling system is ready to use.")
        print("\n📝 Next steps:")
        print("1. Set up your HubSpot CRM properties for check-up dates")
        print("2. Configure your Bolna AI agent")
        print("3. Start the automated scheduler: python call_scheduler.py")
        print("4. Use the API endpoints to schedule calls")
    else:
        print("\n⚠️  Some tests failed. Please check the setup:")
        if not tables_ok:
            print("- Run the database migration: supabase/call_scheduling.sql")
        if not services_ok:
            print("- Check your environment variables and API keys")
            print("- Verify your HubSpot and Bolna AI configurations")
    
    print("\n📚 For detailed setup instructions, see: CALL_SCHEDULING_SETUP.md")

if __name__ == "__main__":
    main()
