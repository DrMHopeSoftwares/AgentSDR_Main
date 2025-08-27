-- Call Scheduling tables for AgentSDR
-- This extends the existing call system with scheduling capabilities

-- Call Schedules table - stores scheduled calls
CREATE TABLE IF NOT EXISTS call_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    contact_id VARCHAR(255) NOT NULL, -- HubSpot contact ID
    contact_name VARCHAR(255),
    contact_phone VARCHAR(20) NOT NULL,
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    call_topic VARCHAR(255) DEFAULT 'follow_up',
    call_language VARCHAR(10) DEFAULT 'en-IN',
    is_active BOOLEAN DEFAULT TRUE,
    call_status VARCHAR(50) DEFAULT 'scheduled', -- scheduled, in_progress, completed, failed, cancelled
    bolna_call_id VARCHAR(255), -- Bolna call ID after initiation
    created_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_checkup_date DATE, -- Last check-up date from HubSpot
    auto_trigger_enabled BOOLEAN DEFAULT TRUE, -- Whether to auto-trigger based on check-up date
    checkup_threshold_days INTEGER DEFAULT 5 -- Days after last check-up to auto-trigger
);

-- Call Schedule Rules table - stores rules for automatic call scheduling
CREATE TABLE IF NOT EXISTS call_schedule_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    rule_name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(50) NOT NULL CHECK (rule_type IN ('checkup_threshold', 'periodic', 'custom')),
    is_active BOOLEAN DEFAULT TRUE,
    checkup_threshold_days INTEGER DEFAULT 5,
    periodic_days INTEGER, -- For periodic calls (e.g., every 30 days)
    custom_conditions JSONB, -- For complex custom rules
    created_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_call_schedules_org_id ON call_schedules(org_id);
CREATE INDEX IF NOT EXISTS idx_call_schedules_agent_id ON call_schedules(agent_id);
CREATE INDEX IF NOT EXISTS idx_call_schedules_scheduled_at ON call_schedules(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_call_schedules_status ON call_schedules(call_status);
CREATE INDEX IF NOT EXISTS idx_call_schedules_contact_phone ON call_schedules(contact_phone);
CREATE INDEX IF NOT EXISTS idx_call_schedules_last_checkup ON call_schedules(last_checkup_date);

CREATE INDEX IF NOT EXISTS idx_call_schedule_rules_org_id ON call_schedule_rules(org_id);
CREATE INDEX IF NOT EXISTS idx_call_schedule_rules_agent_id ON call_schedule_rules(agent_id);
CREATE INDEX IF NOT EXISTS idx_call_schedule_rules_active ON call_schedule_rules(is_active);

-- RLS Policies for call_schedules
ALTER TABLE call_schedules ENABLE ROW LEVEL SECURITY;

-- Users can view call schedules for organizations they belong to
CREATE POLICY "Users can view call schedules for their organizations" ON call_schedules
    FOR SELECT USING (
        org_id IN (
            SELECT org_id FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

-- Users can create call schedules for organizations they belong to
CREATE POLICY "Users can create call schedules for their organizations" ON call_schedules
    FOR INSERT WITH CHECK (
        org_id IN (
            SELECT org_id FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

-- Users can update call schedules for organizations they belong to
CREATE POLICY "Users can update call schedules for their organizations" ON call_schedules
    FOR UPDATE USING (
        org_id IN (
            SELECT org_id FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

-- Users can delete call schedules for organizations they belong to
CREATE POLICY "Users can delete call schedules for their organizations" ON call_schedules
    FOR DELETE USING (
        org_id IN (
            SELECT org_id FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

-- RLS Policies for call_schedule_rules
ALTER TABLE call_schedule_rules ENABLE ROW LEVEL SECURITY;

-- Users can view call schedule rules for organizations they belong to
CREATE POLICY "Users can view call schedule rules for their organizations" ON call_schedule_rules
    FOR SELECT USING (
        org_id IN (
            SELECT org_id FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

-- Users can manage call schedule rules for organizations they belong to
CREATE POLICY "Users can manage call schedule rules for their organizations" ON call_schedule_rules
    FOR ALL USING (
        org_id IN (
            SELECT org_id FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_call_schedules_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to automatically update updated_at
CREATE TRIGGER update_call_schedules_updated_at 
    BEFORE UPDATE ON call_schedules 
    FOR EACH ROW EXECUTE FUNCTION update_call_schedules_updated_at();

CREATE TRIGGER update_call_schedule_rules_updated_at 
    BEFORE UPDATE ON call_schedule_rules 
    FOR EACH ROW EXECUTE FUNCTION update_call_schedules_updated_at();

-- Function to get due call schedules
CREATE OR REPLACE FUNCTION get_due_call_schedules(org_uuid UUID)
RETURNS TABLE(
    schedule_id UUID,
    agent_id UUID,
    contact_id VARCHAR,
    contact_name VARCHAR,
    contact_phone VARCHAR,
    scheduled_at TIMESTAMP WITH TIME ZONE,
    call_topic VARCHAR,
    call_language VARCHAR,
    last_checkup_date DATE,
    checkup_threshold_days INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cs.id as schedule_id,
        cs.agent_id,
        cs.contact_id,
        cs.contact_name,
        cs.contact_phone,
        cs.scheduled_at,
        cs.call_topic,
        cs.call_language,
        cs.last_checkup_date,
        cs.checkup_threshold_days
    FROM call_schedules cs
    WHERE cs.org_id = org_uuid 
        AND cs.is_active = TRUE 
        AND cs.call_status = 'scheduled'
        AND (
            -- Check if scheduled time has passed
            cs.scheduled_at <= NOW()
            OR 
            -- Check if check-up threshold has been exceeded
            (cs.auto_trigger_enabled = TRUE 
             AND cs.last_checkup_date IS NOT NULL 
             AND cs.last_checkup_date + INTERVAL '1 day' * cs.checkup_threshold_days <= CURRENT_DATE)
        );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get call scheduling statistics
CREATE OR REPLACE FUNCTION get_call_scheduling_statistics(org_uuid UUID)
RETURNS TABLE(
    total_scheduled BIGINT,
    total_completed BIGINT,
    total_failed BIGINT,
    total_cancelled BIGINT,
    overdue_schedules BIGINT,
    upcoming_schedules BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) FILTER (WHERE call_status = 'scheduled')::BIGINT as total_scheduled,
        COUNT(*) FILTER (WHERE call_status = 'completed')::BIGINT as total_completed,
        COUNT(*) FILTER (WHERE call_status = 'failed')::BIGINT as total_failed,
        COUNT(*) FILTER (WHERE call_status = 'cancelled')::BIGINT as total_cancelled,
        COUNT(*) FILTER (WHERE call_status = 'scheduled' AND scheduled_at < NOW())::BIGINT as overdue_schedules,
        COUNT(*) FILTER (WHERE call_status = 'scheduled' AND scheduled_at > NOW())::BIGINT as upcoming_schedules
    FROM call_schedules 
    WHERE org_id = org_uuid;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant necessary permissions
GRANT ALL ON call_schedules TO authenticated;
GRANT ALL ON call_schedule_rules TO authenticated;
GRANT EXECUTE ON FUNCTION get_due_call_schedules(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION get_call_scheduling_statistics(UUID) TO authenticated;
