-- Fix RLS Policies for Organization Tables
-- Run this in your Supabase SQL Editor to fix infinite recursion

-- First, disable RLS on all organization-related tables to stop the recursion
ALTER TABLE public.organizations DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.organization_members DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.invitations DISABLE ROW LEVEL SECURITY;

-- Drop all existing policies that might be causing recursion
DROP POLICY IF EXISTS "Users can view organizations they belong to" ON public.organizations;
DROP POLICY IF EXISTS "Users can view their organization memberships" ON public.organization_members;
DROP POLICY IF EXISTS "Users can view invitations for their organizations" ON public.invitations;
DROP POLICY IF EXISTS "Organization admins can manage members" ON public.organization_members;
DROP POLICY IF EXISTS "Organization owners can manage everything" ON public.organizations;

-- Clear any other policies that might exist
DO $$
DECLARE
    pol RECORD;
BEGIN
    -- Drop all policies on organizations table
    FOR pol IN SELECT policyname FROM pg_policies WHERE tablename = 'organizations' LOOP
        EXECUTE 'DROP POLICY IF EXISTS "' || pol.policyname || '" ON public.organizations';
    END LOOP;
    
    -- Drop all policies on organization_members table
    FOR pol IN SELECT policyname FROM pg_policies WHERE tablename = 'organization_members' LOOP
        EXECUTE 'DROP POLICY IF EXISTS "' || pol.policyname || '" ON public.organization_members';
    END LOOP;
    
    -- Drop all policies on invitations table
    FOR pol IN SELECT policyname FROM pg_policies WHERE tablename = 'invitations' LOOP
        EXECUTE 'DROP POLICY IF EXISTS "' || pol.policyname || '" ON public.invitations';
    END LOOP;
END $$;

-- Re-enable RLS with simple, non-recursive policies
ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.organization_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.invitations ENABLE ROW LEVEL SECURITY;

-- Create simple, non-recursive policies

-- 1. Service role has full access to everything (for backend operations)
CREATE POLICY "Service role full access organizations" ON public.organizations
FOR ALL TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Service role full access organization_members" ON public.organization_members
FOR ALL TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Service role full access invitations" ON public.invitations
FOR ALL TO service_role
USING (true)
WITH CHECK (true);

-- 2. Simple user access policies (no cross-table references to avoid recursion)

-- Users can see organizations where they are the owner
CREATE POLICY "Users can see organizations they own" ON public.organizations
FOR SELECT TO authenticated
USING (owner_user_id = auth.uid()::text);

-- Users can update organizations they own
CREATE POLICY "Users can update organizations they own" ON public.organizations
FOR UPDATE TO authenticated
USING (owner_user_id = auth.uid()::text)
WITH CHECK (owner_user_id = auth.uid()::text);

-- Users can see their own organization memberships
CREATE POLICY "Users can see their own memberships" ON public.organization_members
FOR SELECT TO authenticated
USING (user_id = auth.uid()::text);

-- Users can see invitations sent to their email
CREATE POLICY "Users can see invitations to their email" ON public.invitations
FOR SELECT TO authenticated
USING (email = auth.email());

-- Verify the policies were created correctly
SELECT 
    schemaname, 
    tablename, 
    policyname, 
    permissive, 
    roles, 
    cmd
FROM pg_policies 
WHERE tablename IN ('organizations', 'organization_members', 'invitations')
ORDER BY tablename, policyname;
