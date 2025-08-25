#!/usr/bin/env python3
"""
Script to set up the database schema and seed initial data
"""
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

load_dotenv()

from agentsdr.core.supabase_client import get_service_supabase

def setup_database():
    """Set up the database schema"""
    try:
        supabase = get_service_supabase()
        
        print("🔧 Setting up database schema...")
        
        # Read the schema file
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'supabase', 'schema.sql')
        
        if not os.path.exists(schema_path):
            print(f"❌ Schema file not found at {schema_path}")
            return False
        
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        # Split the SQL into individual statements
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        
        print(f"📝 Found {len(statements)} SQL statements to execute...")
        
        # Execute each statement
        for i, statement in enumerate(statements, 1):
            if statement:
                try:
                    print(f"  [{i}/{len(statements)}] Executing statement...")
                    # Note: Supabase doesn't support direct SQL execution via client
                    # This would need to be done via the Supabase dashboard SQL editor
                    print(f"  ⚠️  Please run this SQL in your Supabase SQL editor:")
                    print(f"  {statement}")
                    print()
                except Exception as e:
                    print(f"  ❌ Error executing statement {i}: {e}")
        
        print("✅ Database setup instructions provided!")
        print("\n📋 **Next Steps:**")
        print("1. Go to your Supabase dashboard")
        print("2. Navigate to SQL Editor")
        print("3. Copy and paste the schema.sql content")
        print("4. Execute the SQL")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return False

def check_database_connection():
    """Check if we can connect to the database"""
    try:
        supabase = get_service_supabase()
        
        # Try a simple query
        response = supabase.table('users').select('count', count='exact').limit(1).execute()
        
        print("✅ Database connection successful!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n🔧 **Troubleshooting:**")
        print("1. Check your .env file has correct Supabase credentials")
        print("2. Ensure your Supabase project is active")
        print("3. Verify the database schema is set up")
        return False

def seed_initial_data():
    """Seed initial data for testing"""
    try:
        supabase = get_service_supabase()
        
        print("🌱 Seeding initial data...")
        
        # Check if we already have data
        users_response = supabase.table('users').select('count', count='exact').execute()
        
        if users_response.count > 0:
            print("⚠️  Database already has data. Skipping seed.")
            return True
        
        # Create a test super admin user
        test_user = {
            'id': '00000000-0000-0000-0000-000000000001',
            'email': 'admin@agentsdr.com',
            'display_name': 'System Admin',
            'role': 'super_admin',
            'is_super_admin': True,
            'is_active': True
        }
        
        user_response = supabase.table('users').insert(test_user).execute()
        
        if user_response.data:
            print("✅ Created test super admin user:")
            print(f"   Email: admin@agentsdr.com")
            print(f"   Role: Super Admin")
            print(f"   Password: (use signup flow)")
        
        # Create a test organization
        test_org = {
            'id': '00000000-0000-0000-0000-000000000002',
            'name': 'Demo Organization',
            'slug': 'demo-org',
            'description': 'A demo organization for testing',
            'created_by': test_user['id']
        }
        
        org_response = supabase.table('organizations').insert(test_org).execute()
        
        if org_response.data:
            print("✅ Created test organization:")
            print(f"   Name: Demo Organization")
            print(f"   Slug: demo-org")
        
        return True
        
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        return False

if __name__ == "__main__":
    print("🔧 AgentSDR Database Setup")
    print("=" * 50)
    
    # Check if Supabase credentials are configured
    if not os.getenv('SUPABASE_URL') or os.getenv('SUPABASE_URL') == 'https://your-project.supabase.co':
        print("❌ ERROR: Supabase credentials not configured!")
        print("Please update your .env file with your actual Supabase credentials.")
        sys.exit(1)
    
    while True:
        print("\n📋 **Options:**")
        print("1. Check database connection")
        print("2. Setup database schema (instructions)")
        print("3. Seed initial test data")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            check_database_connection()
            
        elif choice == "2":
            setup_database()
            
        elif choice == "3":
            seed_initial_data()
            
        elif choice == "4":
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please try again.")
