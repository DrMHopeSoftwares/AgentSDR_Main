-- Fix for signup/login issues
-- This adds a policy to allow users to create their own accounts during signup

-- Add policy to allow users to insert their own profile during signup
CREATE POLICY "Users can create their own profile during signup" ON public.users
    FOR INSERT WITH CHECK (auth.uid() = id);

-- Also add policy to allow users to update their own profile
CREATE POLICY "Users can update their own profile" ON public.users
    FOR UPDATE USING (auth.uid() = id);
