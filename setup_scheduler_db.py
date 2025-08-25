#!/usr/bin/env python3
"""
Setup Database Schema for Automated Email Scheduler

This script creates the necessary database tables for the automated email summarization feature.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agentsdr.core.supabase_client import get_service_supabase

def setup_scheduler_database():
    """Create the agent_schedules table and related schema"""
    try:
        print("🔧 Setting up database schema for automated email scheduler...")
        
        supabase = get_service_supabase()
        
        # Create agent_schedules table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS public.agent_schedules (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            agent_id UUID NOT NULL REFERENCES public.agents(id) ON DELETE CASCADE,
            org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
            is_active BOOLEAN DEFAULT TRUE,
            schedule_time TIME NOT NULL,
            timezone TEXT DEFAULT 'UTC',
            recipient_email TEXT NOT NULL,
            criteria_type TEXT DEFAULT 'last_24_hours',
            created_by UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_run_at TIMESTAMP WITH TIME ZONE,
            next_run_at TIMESTAMP WITH TIME ZONE
        );
        """
        
        # Execute the SQL
        result = supabase.rpc('exec_sql', {'sql': create_table_sql}).execute()
        print("✅ Created agent_schedules table")
        
        # Create indexes
        indexes_sql = """
        CREATE INDEX IF NOT EXISTS idx_agent_schedules_agent_id ON public.agent_schedules(agent_id);
        CREATE INDEX IF NOT EXISTS idx_agent_schedules_org_id ON public.agent_schedules(org_id);
        CREATE INDEX IF NOT EXISTS idx_agent_schedules_next_run ON public.agent_schedules(next_run_at);
        CREATE INDEX IF NOT EXISTS idx_agent_schedules_active ON public.agent_schedules(is_active);
        """
        
        supabase.rpc('exec_sql', {'sql': indexes_sql}).execute()
        print("✅ Created indexes for agent_schedules")
        
        # Enable RLS
        rls_sql = "ALTER TABLE public.agent_schedules ENABLE ROW LEVEL SECURITY;"
        supabase.rpc('exec_sql', {'sql': rls_sql}).execute()
        print("✅ Enabled Row Level Security for agent_schedules")
        
        # Create RLS policies
        policies_sql = """
        CREATE POLICY "Users can view schedules from their organizations" ON public.agent_schedules
            FOR SELECT USING (
                public.is_org_member(org_id) OR public.is_super_admin()
            );

        CREATE POLICY "Users can create schedules in their organizations" ON public.agent_schedules
            FOR INSERT WITH CHECK (
                public.is_org_member(org_id) OR public.is_super_admin()
            );

        CREATE POLICY "Users can update schedules in their organizations" ON public.agent_schedules
            FOR UPDATE USING (
                public.is_org_member(org_id) OR public.is_super_admin()
            );

        CREATE POLICY "Users can delete schedules in their organizations" ON public.agent_schedules
            FOR DELETE USING (
                public.is_org_member(org_id) OR public.is_super_admin()
            );
        """
        
        supabase.rpc('exec_sql', {'sql': policies_sql}).execute()
        print("✅ Created RLS policies for agent_schedules")
        
        print("🎉 Database schema setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up database schema: {e}")
        print("\n🔧 Manual Setup Required:")
        print("1. Go to your Supabase dashboard")
        print("2. Go to SQL Editor")
        print("3. Run the following SQL:")
        print("\n" + "="*50)
        print("""
-- Create agent_schedules table
CREATE TABLE IF NOT EXISTS public.agent_schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES public.agents(id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT TRUE,
    schedule_time TIME NOT NULL,
    timezone TEXT DEFAULT 'UTC',
    recipient_email TEXT NOT NULL,
    criteria_type TEXT DEFAULT 'last_24_hours',
    created_by UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_agent_schedules_agent_id ON public.agent_schedules(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_schedules_org_id ON public.agent_schedules(org_id);
CREATE INDEX IF NOT EXISTS idx_agent_schedules_next_run ON public.agent_schedules(next_run_at);
CREATE INDEX IF NOT EXISTS idx_agent_schedules_active ON public.agent_schedules(is_active);

-- Enable RLS
ALTER TABLE public.agent_schedules ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can view schedules from their organizations" ON public.agent_schedules
    FOR SELECT USING (
        public.is_org_member(org_id) OR public.is_super_admin()
    );

CREATE POLICY "Users can create schedules in their organizations" ON public.agent_schedules
    FOR INSERT WITH CHECK (
        public.is_org_member(org_id) OR public.is_super_admin()
    );

CREATE POLICY "Users can update schedules in their organizations" ON public.agent_schedules
    FOR UPDATE USING (
        public.is_org_member(org_id) OR public.is_super_admin()
    );

CREATE POLICY "Users can delete schedules in their organizations" ON public.agent_schedules
    FOR DELETE USING (
        public.is_org_member(org_id) OR public.is_super_admin()
    );
        """)
        print("="*50)
        return False

if __name__ == '__main__':
    setup_scheduler_database()
