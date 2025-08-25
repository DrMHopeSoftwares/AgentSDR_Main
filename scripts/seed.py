#!/usr/bin/env python3
"""
Seed script for AgentSDR - creates initial data for testing
"""


import os
import sys
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client
from agentsdr.core.email import email_service

def main():
    load_dotenv()
    
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_service_key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
        sys.exit(1)
    
    supabase = create_client(supabase_url, supabase_service_key)
    
    print("🌱 Seeding AgentSDR database...")
    
    # Create super admin user
    super_admin_id = str(uuid.uuid4())
    super_admin_data = {
        'id': super_admin_id,
        'email': 'admin@agentsdr.com',
        'display_name': 'Super Admin',
        'is_super_admin': True,
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    
    try:
        supabase.table('users').insert(super_admin_data).execute()
        print("✅ Created super admin user: admin@agentsdr.com")
    except Exception as e:
        print(f"⚠️  Super admin user might already exist: {e}")
    
    # Create demo users
    demo_users = [
        {
            'id': str(uuid.uuid4()),
            'email': 'john@example.com',
            'display_name': 'John Doe',
            'is_super_admin': False
        },
        {
            'id': str(uuid.uuid4()),
            'email': 'jane@example.com',
            'display_name': 'Jane Smith',
            'is_super_admin': False
        },
        {
            'id': str(uuid.uuid4()),
            'email': 'bob@example.com',
            'display_name': 'Bob Johnson',
            'is_super_admin': False
        }
    ]
    
    for user_data in demo_users:
        user_data.update({
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        })
        try:
            supabase.table('users').insert(user_data).execute()
            print(f"✅ Created user: {user_data['email']}")
        except Exception as e:
            print(f"⚠️  User {user_data['email']} might already exist: {e}")
    
    # Create demo organizations
    org1_id = str(uuid.uuid4())
    org1_data = {
        'id': org1_id,
        'name': 'Acme Corporation',
        'slug': 'acme-corp',
        'owner_user_id': demo_users[0]['id'],
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    
    org2_id = str(uuid.uuid4())
    org2_data = {
        'id': org2_id,
        'name': 'TechStart Inc',
        'slug': 'techstart',
        'owner_user_id': demo_users[1]['id'],
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    
    try:
        supabase.table('organizations').insert([org1_data, org2_data]).execute()
        print("✅ Created demo organizations")
    except Exception as e:
        print(f"⚠️  Organizations might already exist: {e}")
    
    # Create organization members
    members_data = [
        # Acme Corp members
        {
            'org_id': org1_id,
            'user_id': demo_users[0]['id'],
            'role': 'admin',
            'joined_at': datetime.utcnow().isoformat()
        },
        {
            'org_id': org1_id,
            'user_id': demo_users[1]['id'],
            'role': 'member',
            'joined_at': datetime.utcnow().isoformat()
        },
        # TechStart members
        {
            'org_id': org2_id,
            'user_id': demo_users[1]['id'],
            'role': 'admin',
            'joined_at': datetime.utcnow().isoformat()
        },
        {
            'org_id': org2_id,
            'user_id': demo_users[2]['id'],
            'role': 'member',
            'joined_at': datetime.utcnow().isoformat()
        }
    ]
    
    try:
        supabase.table('organization_members').insert(members_data).execute()
        print("✅ Created organization members")
    except Exception as e:
        print(f"⚠️  Members might already exist: {e}")
    
    # Create demo records
    records_data = [
        {
            'id': str(uuid.uuid4()),
            'org_id': org1_id,
            'title': 'Q1 Sales Report',
            'content': 'Sales increased by 15% compared to last quarter. Key highlights include...',
            'created_by': demo_users[0]['id'],
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'org_id': org1_id,
            'title': 'Marketing Strategy',
            'content': 'New marketing campaign focusing on social media and influencer partnerships...',
            'created_by': demo_users[1]['id'],
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'org_id': org2_id,
            'title': 'Product Roadmap',
            'content': 'Q2 product development priorities: 1. Mobile app redesign 2. API improvements...',
            'created_by': demo_users[1]['id'],
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'org_id': org2_id,
            'title': 'Technical Architecture',
            'content': 'Planning migration to microservices architecture. Key considerations...',
            'created_by': demo_users[2]['id'],
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
    ]
    
    try:
        supabase.table('records').insert(records_data).execute()
        print("✅ Created demo records")
    except Exception as e:
        print(f"⚠️  Records might already exist: {e}")
    
    # Create demo invitations
    invitations_data = [
        {
            'id': str(uuid.uuid4()),
            'org_id': org1_id,
            'email': 'alice@example.com',
            'role': 'member',
            'token': 'demo-invite-token-1',
            'expires_at': (datetime.utcnow() + timedelta(hours=72)).isoformat(),
            'invited_by': demo_users[0]['id'],
            'created_at': datetime.utcnow().isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'org_id': org2_id,
            'email': 'charlie@example.com',
            'role': 'admin',
            'token': 'demo-invite-token-2',
            'expires_at': (datetime.utcnow() + timedelta(hours=72)).isoformat(),
            'invited_by': demo_users[1]['id'],
            'created_at': datetime.utcnow().isoformat()
        }
    ]
    
    try:
        supabase.table('invitations').insert(invitations_data).execute()
        print("✅ Created demo invitations")
    except Exception as e:
        print(f"⚠️  Invitations might already exist: {e}")
    
    print("\n🎉 Seeding completed!")
    print("\n📋 Demo Data Summary:")
    print("• Super Admin: admin@agentsdr.com")
    print("• Demo Users: john@example.com, jane@example.com, bob@example.com")
    print("• Organizations: Acme Corporation (acme-corp), TechStart Inc (techstart)")
    print("• Records: 4 demo records across both organizations")
    print("• Invitations: 2 pending invitations")
    print("\n🔑 Login Credentials:")
    print("You'll need to create accounts in Supabase Auth for these users.")
    print("Or use the super admin account to manage the platform.")

if __name__ == '__main__':
    main()
