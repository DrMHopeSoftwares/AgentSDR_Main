-- Enhanced Agent Schedules Schema Update
-- Run this to add the new flexible scheduling features

-- Add new columns to agent_schedules table
ALTER TABLE public.agent_schedules 
ADD COLUMN IF NOT EXISTS frequency_type TEXT DEFAULT 'daily' CHECK (frequency_type IN ('once', 'daily', 'weekly', 'monthly'));

ALTER TABLE public.agent_schedules 
ADD COLUMN IF NOT EXISTS email_count INTEGER;

ALTER TABLE public.agent_schedules 
ADD COLUMN IF NOT EXISTS email_hours INTEGER;

ALTER TABLE public.agent_schedules 
ADD COLUMN IF NOT EXISTS day_of_week INTEGER CHECK (day_of_week BETWEEN 1 AND 7); -- 1=Monday, 7=Sunday

ALTER TABLE public.agent_schedules 
ADD COLUMN IF NOT EXISTS day_of_month INTEGER CHECK (day_of_month BETWEEN 1 AND 31);

ALTER TABLE public.agent_schedules 
ADD COLUMN IF NOT EXISTS one_time_datetime TIMESTAMP WITH TIME ZONE;

-- Update criteria_type to support new options
ALTER TABLE public.agent_schedules 
DROP CONSTRAINT IF EXISTS agent_schedules_criteria_type_check;

ALTER TABLE public.agent_schedules 
ADD CONSTRAINT agent_schedules_criteria_type_check 
CHECK (criteria_type IN ('last_24_hours', 'last_7_days', 'latest_n', 'oldest_n', 'custom_hours'));

-- Add index for new columns
CREATE INDEX IF NOT EXISTS idx_agent_schedules_frequency_type ON public.agent_schedules(frequency_type);

-- Add comments for documentation
COMMENT ON COLUMN public.agent_schedules.frequency_type IS 'How often to run: once, daily, weekly, monthly';
COMMENT ON COLUMN public.agent_schedules.email_count IS 'Number of emails to fetch when criteria_type is latest_n or oldest_n';
COMMENT ON COLUMN public.agent_schedules.email_hours IS 'Number of hours back to fetch emails when criteria_type is custom_hours';
COMMENT ON COLUMN public.agent_schedules.day_of_week IS 'Day of week for weekly schedules (1=Monday, 7=Sunday)';
COMMENT ON COLUMN public.agent_schedules.day_of_month IS 'Day of month for monthly schedules (1-31)';
COMMENT ON COLUMN public.agent_schedules.one_time_datetime IS 'Specific datetime for one-time schedules';