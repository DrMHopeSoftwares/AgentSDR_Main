-- Call-related tables for AgentSDR

-- Call Records table - stores basic call information
CREATE TABLE IF NOT EXISTS call_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    call_id VARCHAR(255) NOT NULL, -- Bolna call ID
    agent_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    contact_phone VARCHAR(20),
    contact_name VARCHAR(255),
    call_duration INTEGER, -- in seconds
    call_status VARCHAR(50) DEFAULT 'completed',
    transcript_id UUID,
    summary_id UUID,
    hubspot_contact_id VARCHAR(255),
    hubspot_summary_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Call Transcripts table - stores the actual transcript text
CREATE TABLE IF NOT EXISTS call_transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    call_id VARCHAR(255) NOT NULL, -- Bolna call ID
    agent_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    contact_phone VARCHAR(20),
    contact_name VARCHAR(255),
    transcript_text TEXT NOT NULL,
    call_duration INTEGER, -- in seconds
    call_status VARCHAR(50) DEFAULT 'completed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Call Summaries table - stores OpenAI-generated summaries
CREATE TABLE IF NOT EXISTS call_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transcript_id UUID NOT NULL REFERENCES call_transcripts(id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    summary_text TEXT NOT NULL,
    word_count INTEGER NOT NULL,
    openai_model_used VARCHAR(100),
    openai_tokens_used INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_call_records_org_id ON call_records(org_id);
CREATE INDEX IF NOT EXISTS idx_call_records_call_id ON call_records(call_id);
CREATE INDEX IF NOT EXISTS idx_call_records_agent_id ON call_records(agent_id);
CREATE INDEX IF NOT EXISTS idx_call_records_contact_phone ON call_records(contact_phone);
CREATE INDEX IF NOT EXISTS idx_call_records_created_at ON call_records(created_at);

CREATE INDEX IF NOT EXISTS idx_call_transcripts_org_id ON call_transcripts(org_id);
CREATE INDEX IF NOT EXISTS idx_call_transcripts_call_id ON call_transcripts(call_id);
CREATE INDEX IF NOT EXISTS idx_call_transcripts_agent_id ON call_transcripts(agent_id);
CREATE INDEX IF NOT EXISTS idx_call_transcripts_contact_phone ON call_transcripts(contact_phone);

CREATE INDEX IF NOT EXISTS idx_call_summaries_org_id ON call_summaries(org_id);
CREATE INDEX IF NOT EXISTS idx_call_summaries_transcript_id ON call_summaries(transcript_id);

-- RLS Policies for call_records
ALTER TABLE call_records ENABLE ROW LEVEL SECURITY;

-- Users can view call records for organizations they belong to
CREATE POLICY "Users can view call records for their organizations" ON call_records
    FOR SELECT USING (
        org_id IN (
            SELECT org_id FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

-- Users can create call records for organizations they belong to
CREATE POLICY "Users can create call records for their organizations" ON call_records
    FOR INSERT WITH CHECK (
        org_id IN (
            SELECT org_id FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

-- Users can update call records for organizations they belong to
CREATE POLICY "Users can update call records for their organizations" ON call_records
    FOR UPDATE USING (
        org_id IN (
            SELECT org_id FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

-- RLS Policies for call_transcripts
ALTER TABLE call_transcripts ENABLE ROW LEVEL SECURITY;

-- Users can view transcripts for organizations they belong to
CREATE POLICY "Users can view transcripts for their organizations" ON call_transcripts
    FOR SELECT USING (
        org_id IN (
            SELECT org_id FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

-- Users can create transcripts for organizations they belong to
CREATE POLICY "Users can create transcripts for their organizations" ON call_transcripts
    FOR INSERT WITH CHECK (
        org_id IN (
            SELECT org_id FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

-- Users can update transcripts for organizations they belong to
CREATE POLICY "Users can update transcripts for their organizations" ON call_transcripts
    FOR UPDATE USING (
        org_id IN (
            SELECT org_id FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

-- RLS Policies for call_summaries
ALTER TABLE call_summaries ENABLE ROW LEVEL SECURITY;

-- Users can view summaries for organizations they belong to
CREATE POLICY "Users can view summaries for their organizations" ON call_summaries
    FOR SELECT USING (
        org_id IN (
            SELECT org_id FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

-- Users can create summaries for organizations they belong to
CREATE POLICY "Users can create summaries for their organizations" ON call_summaries
    FOR INSERT WITH CHECK (
        org_id IN (
            SELECT org_id FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to automatically update updated_at
CREATE TRIGGER update_call_records_updated_at 
    BEFORE UPDATE ON call_records 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_call_transcripts_updated_at 
    BEFORE UPDATE ON call_transcripts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to get call statistics
CREATE OR REPLACE FUNCTION get_call_statistics(org_uuid UUID)
RETURNS TABLE(
    total_calls BIGINT,
    total_duration BIGINT,
    avg_duration NUMERIC,
    calls_today BIGINT,
    calls_this_week BIGINT,
    calls_this_month BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_calls,
        COALESCE(SUM(call_duration), 0)::BIGINT as total_duration,
        COALESCE(AVG(call_duration), 0)::NUMERIC as avg_duration,
        COUNT(*) FILTER (WHERE DATE(created_at) = CURRENT_DATE)::BIGINT as calls_today,
        COUNT(*) FILTER (WHERE created_at >= DATE_TRUNC('week', CURRENT_DATE))::BIGINT as calls_this_week,
        COUNT(*) FILTER (WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE))::BIGINT as calls_this_month
    FROM call_records 
    WHERE org_id = org_uuid;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON call_records TO authenticated;
GRANT ALL ON call_transcripts TO authenticated;
GRANT ALL ON call_summaries TO authenticated;
GRANT EXECUTE ON FUNCTION get_call_statistics(UUID) TO authenticated;
