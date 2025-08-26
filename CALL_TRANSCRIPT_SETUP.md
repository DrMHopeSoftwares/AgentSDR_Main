# Call Transcript Integration Setup Guide

This guide explains how to set up and use the call transcript functionality in AgentSDR, which integrates with Bolna API, OpenAI, and HubSpot.

## Overview

The call transcript system provides:
- **Bolna API Integration**: Fetches call transcripts and metadata
- **OpenAI Summarization**: Generates concise summaries (20 words max)
- **HubSpot Integration**: Automatically updates contact summaries
- **Database Storage**: Stores all call data with proper relationships
- **Web Interface**: Modern UI for managing and reviewing calls

## Prerequisites

1. **Bolna API Access**: You need a Bolna API key and access to their call transcript endpoints
2. **OpenAI API Key**: For transcript summarization
3. **HubSpot API Key**: For contact management
4. **Supabase Database**: For storing call data

## Environment Variables

Add these to your `.env` file:

```bash
# Bolna API Configuration
BOLNA_API_KEY=your_bolna_api_key_here
BOLNA_API_URL=https://api.bolna.ai

# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_URL=https://api.openai.com/v1

# HubSpot API Configuration
HUBSPOT_API_KEY=your_hubspot_api_key_here
HUBSPOT_API_URL=https://api.hubapi.com
```

## Database Setup

1. **Run the migration script**:
   ```bash
   # Connect to your Supabase database and run:
   psql -h your-supabase-host -U postgres -d postgres -f supabase/call_tables.sql
   ```

2. **Verify tables created**:
   - `call_records`: Basic call information
   - `call_transcripts`: Full transcript text
   - `call_summaries`: OpenAI-generated summaries

## API Endpoints

### Process Call Transcript
```http
POST /<org_slug>/calls/process-transcript
Content-Type: application/json

{
    "call_id": "bolna_call_123",
    "agent_id": "agent_user_id"
}
```

### Get Call History
```http
GET /<org_slug>/calls/history?limit=50&offset=0
```

### Get Call Details
```http
GET /<org_slug>/calls/<call_record_id>
```

### Retry HubSpot Sync
```http
POST /<org_slug>/calls/<call_record_id>/retry-hubspot
```

### Get Sync Status
```http
GET /<org_slug>/calls/sync-status
```

## Usage Workflow

### 1. Process a Call Transcript

```python
from agentsdr.services.call_transcript_service import CallTranscriptService

# Initialize the service
call_service = CallTranscriptService()

# Process a call transcript
result = call_service.process_call_transcript(
    call_id="bolna_call_123",
    org_id="your_org_id",
    agent_id="agent_user_id"
)

if result['success']:
    print(f"Summary: {result['summary']}")
    print(f"HubSpot sync: {result['hubspot_success']}")
else:
    print(f"Error: {result['error']}")
```

### 2. Manual Processing via Web Interface

1. Navigate to `/<org_slug>/calls`
2. Click "Process New Transcript"
3. Enter the Bolna Call ID and Agent ID
4. Click "Process"

### 3. View Call History

The web interface shows:
- Call statistics (total calls, sync rate, etc.)
- Filterable call list
- Individual call details
- Transcript and summary viewing
- HubSpot sync status

## Service Architecture

### BolnaService
- Fetches call transcripts and metadata
- Handles API authentication and error handling
- Supports call listing and individual call retrieval

### OpenAIService
- Generates concise summaries (20 words max)
- Uses GPT-3.5-turbo for cost efficiency
- Provides token usage tracking
- Optional sentiment analysis

### HubSpotService
- Finds contacts by phone number
- Creates new contacts if needed
- Updates contact summaries
- Handles custom property creation

### CallTranscriptService
- Orchestrates the entire workflow
- Manages database operations
- Handles error recovery
- Provides comprehensive logging

## Database Schema

### Call Records
```sql
CREATE TABLE call_records (
    id UUID PRIMARY KEY,
    org_id UUID REFERENCES organizations(id),
    call_id VARCHAR(255), -- Bolna call ID
    agent_id UUID REFERENCES auth.users(id),
    contact_phone VARCHAR(20),
    contact_name VARCHAR(255),
    call_duration INTEGER,
    call_status VARCHAR(50),
    transcript_id UUID,
    summary_id UUID,
    hubspot_contact_id VARCHAR(255),
    hubspot_summary_sent BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Call Transcripts
```sql
CREATE TABLE call_transcripts (
    id UUID PRIMARY KEY,
    org_id UUID REFERENCES organizations(id),
    call_id VARCHAR(255),
    agent_id UUID REFERENCES auth.users(id),
    contact_phone VARCHAR(20),
    contact_name VARCHAR(255),
    transcript_text TEXT,
    call_duration INTEGER,
    call_status VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Call Summaries
```sql
CREATE TABLE call_summaries (
    id UUID PRIMARY KEY,
    transcript_id UUID REFERENCES call_transcripts(id),
    org_id UUID REFERENCES organizations(id),
    summary_text TEXT,
    word_count INTEGER,
    openai_model_used VARCHAR(100),
    openai_tokens_used INTEGER,
    created_at TIMESTAMP
);
```

## Security Features

- **Row Level Security (RLS)**: Users can only access their organization's data
- **API Key Management**: Secure storage of external API credentials
- **Input Validation**: Pydantic models ensure data integrity
- **Error Handling**: Comprehensive logging without exposing sensitive data

## Monitoring and Troubleshooting

### Logs
All services provide detailed logging:
- API request/response logging
- Error tracking with context
- Performance metrics
- HubSpot sync status

### Common Issues

1. **Bolna API Errors**:
   - Check API key validity
   - Verify call ID exists
   - Check API rate limits

2. **OpenAI Errors**:
   - Verify API key and quota
   - Check transcript length limits
   - Monitor token usage

3. **HubSpot Errors**:
   - Verify API key permissions
   - Check contact property access
   - Monitor API rate limits

### Health Checks

```python
# Check service health
from agentsdr.services.call_transcript_service import CallTranscriptService

service = CallTranscriptService()

# Test Bolna connection
bolna_status = service.bolna_service.get_call_details("test_call_id")

# Test OpenAI connection
openai_status = service.openai_service.summarize_transcript("Test transcript")

# Test HubSpot connection
hubspot_status = service.hubspot_service.get_contact_properties()
```

## Testing

Run the test script to verify setup:

```bash
python test_call_transcript.py
```

This will test:
- Service initialization
- Model validation
- Configuration loading
- Basic functionality

## Performance Considerations

- **Batch Processing**: Process multiple calls efficiently
- **Caching**: Consider caching frequently accessed data
- **Rate Limiting**: Respect external API limits
- **Database Indexing**: Optimized queries with proper indexes

## Cost Optimization

- **OpenAI Usage**: Monitor token consumption
- **API Calls**: Minimize unnecessary external API calls
- **Storage**: Archive old transcripts if needed
- **Caching**: Reduce duplicate API calls

## Support

For issues or questions:
1. Check the logs for detailed error messages
2. Verify all environment variables are set
3. Test individual services separately
4. Check external API status pages

## Future Enhancements

- **Real-time Processing**: Webhook-based transcript processing
- **Advanced Analytics**: Call quality metrics and insights
- **Multi-language Support**: International transcript handling
- **Custom Summarization**: Organization-specific summary templates
- **Integration APIs**: Webhook endpoints for external systems
