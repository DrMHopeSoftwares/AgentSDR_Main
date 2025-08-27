-- Add is_active column to agents table for pause/resume functionality
ALTER TABLE public.agents ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- Create index on is_active for better performance
CREATE INDEX IF NOT EXISTS idx_agents_is_active ON public.agents(is_active);

-- Update existing agents to be active by default
UPDATE public.agents SET is_active = TRUE WHERE is_active IS NULL;