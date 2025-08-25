#!/usr/bin/env python3
"""
Database Setup Script for AgentSDR
This script helps you set up your database connection and create necessary tables.
"""

import os
import sys
from dotenv import load_dotenv

def check_env_file():
    """Check if .env file exists and has required variables"""
    print("🔍 Checking environment setup...")
    
    if not os.path.exists('.env'):
        print("❌ No .env file found!")
        print("\n📝 Please create a .env file with the following content:")
        print("""
# Flask Configuration
FLASK_ENV=development
FLASK_SECRET_KEY=your-super-secret-key-change-in-production

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Email Configuration (for invitations)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
SMTP_USE_TLS=true

# Application Settings
BASE_URL=http://localhost:5000
INVITATION_EXPIRY_HOURS=72
MAX_ORGS_PER_USER=10
MAX_MEMBERS_PER_ORG=100

# Rate Limiting
RATELIMIT_DEFAULT=200 per day;50 per hour
RATELIMIT_STORAGE_URL=memory://
        """)
        return False
    
    load_dotenv()
    
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY', 
        'SUPABASE_SERVICE_ROLE_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please update your .env file with the correct Supabase credentials.")
        return False
    
    print("✅ Environment variables look good!")
    return True

def test_supabase_connection():
    """Test the Supabase connection"""
    print("\n🔗 Testing Supabase connection...")
    
    try:
        from agentsdr import create_app
        from agentsdr.core.supabase_client import get_service_supabase
        
        # Create Flask app context
        app = create_app()
        with app.app_context():
            supabase = get_service_supabase()
            
            # Try to query the users table
            response = supabase.table('users').select('count').execute()
            print("✅ Successfully connected to Supabase!")
            return True
        
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Make sure your Supabase URL is correct")
        print("2. Check that your API keys are valid")
        print("3. Ensure your Supabase project is active")
        return False

def check_database_tables():
    """Check if required database tables exist"""
    print("\n📊 Checking database tables...")
    
    try:
        from agentsdr import create_app
        from agentsdr.core.supabase_client import get_service_supabase
        
        # Create Flask app context
        app = create_app()
        with app.app_context():
            supabase = get_service_supabase()
            
            required_tables = ['users', 'organizations', 'organization_members', 'invitations', 'records', 'agents']
            
            for table in required_tables:
                try:
                    response = supabase.table(table).select('count').limit(1).execute()
                    print(f"✅ Table '{table}' exists")
                except Exception as e:
                    print(f"❌ Table '{table}' missing or inaccessible: {e}")
                    return False
            
            print("✅ All required tables exist!")
            return True
        
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return False

def create_database_schema():
    """Create the database schema if it doesn't exist"""
    print("\n🏗️ Creating database schema...")
    
    try:
        with open('supabase/schema.sql', 'r') as f:
            schema_sql = f.read()
        
        print("📄 Schema file found. You need to run this SQL in your Supabase dashboard:")
        print("\n1. Go to your Supabase project dashboard")
        print("2. Click on 'SQL Editor' in the left sidebar")
        print("3. Copy and paste the contents of supabase/schema.sql")
        print("4. Click 'Run' to execute the SQL")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading schema file: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 AgentSDR Database Setup")
    print("=" * 40)
    
    # Step 1: Check environment
    if not check_env_file():
        return
    
    # Step 2: Test connection
    if not test_supabase_connection():
        return
    
    # Step 3: Check tables
    if not check_database_tables():
        print("\n📋 You need to create the database tables.")
        create_database_schema()
        return
    
    print("\n🎉 Setup complete! Your database is ready to use.")
    print("\n📝 Next steps:")
    print("1. Run: python app.py")
    print("2. Open: http://localhost:5000")
    print("3. Create your first account!")

if __name__ == '__main__':
    main()
