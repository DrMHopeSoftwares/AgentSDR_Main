#!/usr/bin/env python3
"""
Script to set up call transcript database tables
"""

import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def setup_database():
    """Set up the call transcript database tables"""
    print("🚀 Setting up Call Transcript Database Tables")
    print("=" * 50)
    
    try:
        # Create Flask app context
        from agentsdr import create_app
        app = create_app('development')
        
        with app.app_context():
            from agentsdr.core.supabase_client import get_service_supabase
            
            print("🔄 Connecting to Supabase...")
            supabase = get_service_supabase()
            
            # Read the SQL file
            sql_file_path = os.path.join(os.path.dirname(__file__), 'supabase', 'call_tables.sql')
            
            if not os.path.exists(sql_file_path):
                print(f"❌ SQL file not found: {sql_file_path}")
                return
            
            print("📖 Reading SQL file...")
            with open(sql_file_path, 'r') as f:
                sql_content = f.read()
            
            # Split into individual statements
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            print(f"🔧 Executing {len(statements)} SQL statements...")
            
            for i, statement in enumerate(statements, 1):
                if statement and not statement.startswith('--'):
                    try:
                        print(f"  {i}/{len(statements)}: {statement[:50]}...")
                        supabase.rpc('exec_sql', {'sql': statement}).execute()
                        print(f"    ✅ Success")
                    except Exception as e:
                        print(f"    ⚠️  Warning: {e}")
                        # Continue with other statements
            
            print("\n✅ Database setup completed!")
            print("\n📋 Next steps:")
            print("1. Run the call transcript processing script")
            print("2. Check if tables were created successfully")
            print("3. Test with a sample call transcript")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    setup_database()
