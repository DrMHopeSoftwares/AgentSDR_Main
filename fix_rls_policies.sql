-- Fix RLS Policies for AgentSDR
-- Run this in your Supabase SQL Editor

-- First, ensure RLS is enabled on the users table
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (to avoid conflicts)
DROP POLICY IF EXISTS "Allow service role full access to users" ON public.users;
DROP POLICY IF EXISTS "Allow authenticated users to read own data" ON public.users;
DROP POLICY IF EXISTS "Allow users to insert themselves" ON public.users;

-- Policy 1: Allow service role (your backend) full access to users table
CREATE POLICY "Allow service role full access to users" ON public.users
FOR ALL TO service_role
USING (true)
WITH CHECK (true);

-- Policy 2: Allow authenticated users to read their own user data
CREATE POLICY "Allow authenticated users to read own data" ON public.users
FOR SELECT TO authenticated
USING (auth.uid()::text = id);

-- Policy 3: Allow authenticated users to update their own data
CREATE POLICY "Allow authenticated users to update own data" ON public.users
FOR UPDATE TO authenticated
USING (auth.uid()::text = id)
WITH CHECK (auth.uid()::text = id);

-- Verify the policies were created
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
FROM pg_policies 
WHERE tablename = 'users';

-- Test that service role can insert (this should work)
-- Note: This is just a test query, don't actually run this insert
-- INSERT INTO public.users (id, email, display_name, is_super_admin) 
-- VALUES ('test-id', 'test@example.com', 'Test User', false);
