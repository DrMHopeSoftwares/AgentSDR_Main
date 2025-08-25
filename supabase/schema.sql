-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    display_name TEXT,
    is_super_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create organizations table
CREATE TABLE IF NOT EXISTS public.organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    owner_user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create organization_members table
CREATE TABLE IF NOT EXISTS public.organization_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('admin', 'member')),
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(org_id, user_id)
);

-- Create invitations table
CREATE TABLE IF NOT EXISTS public.invitations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'member')),
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    accepted_at TIMESTAMP WITH TIME ZONE,
    invited_by UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create records table (example domain data)
CREATE TABLE IF NOT EXISTS public.records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_by UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create agents table (first-class entity)
CREATE TABLE IF NOT EXISTS public.agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    agent_type TEXT NOT NULL CHECK (agent_type IN ('email_summarizer','hubspot_data','custom')),
    config JSONB DEFAULT '{}'::jsonb,
    created_by UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_agents_org_id ON public.agents(org_id);
CREATE INDEX IF NOT EXISTS idx_agents_created_by ON public.agents(created_by);



-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
ALTER TABLE public.agents ENABLE ROW LEVEL SECURITY;

CREATE INDEX IF NOT EXISTS idx_organizations_slug ON public.organizations(slug);
CREATE INDEX IF NOT EXISTS idx_organizations_owner ON public.organizations(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_organization_members_org_id ON public.organization_members(org_id);
CREATE INDEX IF NOT EXISTS idx_organization_members_user_id ON public.organization_members(user_id);
CREATE INDEX IF NOT EXISTS idx_invitations_token ON public.invitations(token);
CREATE INDEX IF NOT EXISTS idx_invitations_org_id ON public.invitations(org_id);
CREATE INDEX IF NOT EXISTS idx_invitations_email ON public.invitations(email);
CREATE INDEX IF NOT EXISTS idx_records_org_id ON public.records(org_id);
CREATE INDEX IF NOT EXISTS idx_records_created_by ON public.records(created_by);

-- Create agent_schedules table for automated email summarization
CREATE TABLE IF NOT EXISTS public.agent_schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES public.agents(id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT TRUE,
    schedule_time TIME NOT NULL, -- Time of day (e.g., '09:00:00')
    timezone TEXT DEFAULT 'UTC',
    recipient_email TEXT NOT NULL,
    criteria_type TEXT DEFAULT 'last_24_hours',
    created_by UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for agent_schedules
CREATE INDEX IF NOT EXISTS idx_agent_schedules_agent_id ON public.agent_schedules(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_schedules_org_id ON public.agent_schedules(org_id);
CREATE INDEX IF NOT EXISTS idx_agent_schedules_next_run ON public.agent_schedules(next_run_at);
CREATE INDEX IF NOT EXISTS idx_agent_schedules_active ON public.agent_schedules(is_active);

-- Enable RLS for agent_schedules
ALTER TABLE public.agent_schedules ENABLE ROW LEVEL SECURITY;

-- Enable Row Level Security (RLS)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.organization_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.invitations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.records ENABLE ROW LEVEL SECURITY;

-- Create function to check if user is super admin
CREATE OR REPLACE FUNCTION public.is_super_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.users
        WHERE id = auth.uid() AND is_super_admin = TRUE
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to check if user is member of organization
CREATE OR REPLACE FUNCTION public.is_org_member(org_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.organization_members
        WHERE org_id = $1 AND user_id = auth.uid()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to check if user is admin of organization
CREATE OR REPLACE FUNCTION public.is_org_admin(org_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.organization_members
        WHERE org_id = $1 AND user_id = auth.uid() AND role = 'admin'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Users table policies
CREATE POLICY "Users can view their own profile" ON public.users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Super admins can view all users" ON public.users
    FOR SELECT USING (public.is_super_admin());

CREATE POLICY "Super admins can insert users" ON public.users
    FOR INSERT WITH CHECK (public.is_super_admin());

CREATE POLICY "Super admins can update users" ON public.users
    FOR UPDATE USING (public.is_super_admin());

-- Organizations table policies
CREATE POLICY "Users can view organizations they are members of" ON public.organizations
    FOR SELECT USING (
        public.is_org_member(id) OR public.is_super_admin()
    );

CREATE POLICY "Users can create organizations" ON public.organizations
    FOR INSERT WITH CHECK (auth.uid() = owner_user_id);

CREATE POLICY "Org admins can update their organizations" ON public.organizations
    FOR UPDATE USING (
        public.is_org_admin(id) OR public.is_super_admin()
    );

CREATE POLICY "Super admins can delete organizations" ON public.organizations
    FOR DELETE USING (public.is_super_admin());

-- Organization members table policies
CREATE POLICY "Users can view members of organizations they belong to" ON public.organization_members
    FOR SELECT USING (
        public.is_org_member(org_id) OR public.is_super_admin()
    );

CREATE POLICY "Org admins can manage members" ON public.organization_members
    FOR ALL USING (
        public.is_org_admin(org_id) OR public.is_super_admin()
    );

-- Invitations table policies
CREATE POLICY "Users can view invitations for organizations they admin" ON public.invitations
    FOR SELECT USING (
        public.is_org_admin(org_id) OR public.is_super_admin()
    );


-- Agents table policies
CREATE POLICY "Users can view agents from their organizations" ON public.agents
    FOR SELECT USING (
        public.is_org_member(org_id) OR public.is_super_admin()
    );

CREATE POLICY "Users can create agents in their organizations" ON public.agents
    FOR INSERT WITH CHECK (
        public.is_org_admin(org_id) OR public.is_super_admin()
    );

CREATE POLICY "Users can update agents in their organizations" ON public.agents
    FOR UPDATE USING (
        public.is_org_admin(org_id) OR public.is_super_admin()
    );

CREATE POLICY "Users can delete agents in their organizations" ON public.agents
    FOR DELETE USING (
        public.is_org_admin(org_id) OR public.is_super_admin()
    );

        public.is_org_admin(org_id) OR public.is_super_admin()
    );

CREATE POLICY "Org admins can create invitations" ON public.invitations
    FOR INSERT WITH CHECK (
        public.is_org_admin(org_id) OR public.is_super_admin()
    );

CREATE POLICY "Org admins can update invitations" ON public.invitations
    FOR UPDATE USING (
        public.is_org_admin(org_id) OR public.is_super_admin()
    );

CREATE POLICY "Org admins can delete invitations" ON public.invitations
    FOR DELETE USING (
        public.is_org_admin(org_id) OR public.is_super_admin()
    );

-- Records table policies
CREATE POLICY "Users can view records from their organizations" ON public.records
    FOR SELECT USING (
        public.is_org_member(org_id) OR public.is_super_admin()
    );

CREATE POLICY "Users can create records in their organizations" ON public.records
    FOR INSERT WITH CHECK (
        public.is_org_member(org_id) OR public.is_super_admin()
    );

CREATE POLICY "Users can update records in their organizations" ON public.records
    FOR UPDATE USING (
        public.is_org_member(org_id) OR public.is_super_admin()
    );

CREATE POLICY "Users can delete records in their organizations" ON public.records
    FOR DELETE USING (
        public.is_org_member(org_id) OR public.is_super_admin()
    );

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON public.organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_records_updated_at BEFORE UPDATE ON public.records
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
