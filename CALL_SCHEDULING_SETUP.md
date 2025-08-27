# Call Scheduling System Setup Guide

This guide explains how to set up and use the enhanced call scheduling system in AgentSDR, which integrates with HubSpot CRM data and Bolna AI for automated call management.

## 🎯 **Overview**

The call scheduling system provides:

- **Manual Call Scheduling**: Schedule calls for specific dates and times
- **Automatic Call Triggering**: Automatically trigger calls based on check-up date thresholds
- **HubSpot Integration**: Fetch contact data and check-up dates from CRM
- **Bolna AI Integration**: Execute calls through the Bolna telephony API
- **Smart Scheduling**: Intelligent scheduling based on business rules
- **Real-time Monitoring**: Track call status and execution

## 🚀 **Features**

### **Core Functionality**
- ✅ Schedule calls manually with date/time picker
- ✅ Automatic call triggering when check-up threshold is exceeded (default: 5 days)
- ✅ Integration with HubSpot CRM for contact data
- ✅ Bolna AI API integration for call execution
- ✅ Call status tracking (scheduled, in_progress, completed, failed, cancelled)
- ✅ Organization-based access control
- ✅ Comprehensive logging and monitoring

### **Smart Automation**
- ✅ Check-up date monitoring from HubSpot
- ✅ Configurable threshold days for follow-up
- ✅ Automatic call execution when conditions are met
- ✅ Batch processing for multiple organizations
- ✅ Error handling and retry mechanisms

## 📋 **Prerequisites**

1. **HubSpot CRM Access**: API key with contact read/write permissions
2. **Bolna AI Account**: API key and agent configuration
3. **Supabase Database**: For storing call schedules and metadata
4. **Python Environment**: Python 3.8+ with required dependencies

## 🔧 **Installation & Setup**

### **Step 1: Database Setup**

Run the call scheduling database migration:

```bash
# Connect to your Supabase database and run:
psql -h your-supabase-host -U postgres -d postgres -f supabase/call_scheduling.sql
```

This creates the necessary tables:
- `call_schedules`: Stores call schedule information
- `call_schedule_rules`: Stores business rules for automatic scheduling

### **Step 2: Environment Configuration**

Add these variables to your `.env` file:

```bash
# HubSpot Configuration
HUBSPOT_API_KEY=your_hubspot_api_key
HUBSPOT_API_URL=https://api.hubapi.com

# Bolna AI Configuration
BOLNA_API_KEY=your_bolna_api_key
BOLNA_API_URL=https://api.bolna.ai
BOLNA_AGENT_ID=your_bolna_agent_id
BOLNA_FROM_NUMBER=+1234567890
BOLNA_CALLS_PATH=/a/your-agent-id/api/v1/voice/calls

# Call Scheduling Configuration
CALL_SCHEDULER_ENABLED=true
CALL_SCHEDULER_INTERVAL=3600  # 1 hour in seconds
CHECKUP_THRESHOLD_DAYS=5      # Default threshold for auto-triggering
```

### **Step 3: Service Registration**

The call scheduling routes are automatically registered when you start the Flask app. Verify in `agentsdr/__init__.py`:

```python
# Register call scheduling routes
try:
    from agentsdr.orgs.call_scheduling_routes import call_scheduling_bp
    app.register_blueprint(call_scheduling_bp, url_prefix='/call-scheduling')
except Exception as e:
    print(f"Warning: Could not register call scheduling routes: {e}")
```

## 📱 **API Endpoints**

### **Call Schedule Management**

#### **Get All Call Schedules**
```http
GET /call-scheduling/<org_slug>/call-schedules
Authorization: Bearer <token>
```

#### **Create Call Schedule**
```http
POST /call-scheduling/<org_slug>/call-schedules
Content-Type: application/json
Authorization: Bearer <token>

{
    "agent_id": "uuid",
    "contact_id": "hubspot_contact_id",
    "contact_name": "John Doe",
    "contact_phone": "+1234567890",
    "scheduled_at": "2024-01-15T10:00:00Z",
    "call_topic": "follow_up",
    "call_language": "en-IN",
    "auto_trigger_enabled": true,
    "checkup_threshold_days": 5
}
```

#### **Update Call Schedule**
```http
PUT /call-scheduling/<org_slug>/call-schedules/<schedule_id>
Content-Type: application/json
Authorization: Bearer <token>

{
    "scheduled_at": "2024-01-16T14:00:00Z",
    "call_topic": "appointment_reminder"
}
```

#### **Delete Call Schedule**
```http
DELETE /call-scheduling/<org_slug>/call-schedules/<schedule_id>
Authorization: Bearer <token>
```

#### **Execute Call Schedule Immediately**
```http
POST /call-scheduling/<org_slug>/call-schedules/<schedule_id>/execute
Authorization: Bearer <token>
```

### **Monitoring & Analytics**

#### **Get Call Scheduling Statistics**
```http
GET /call-scheduling/<org_slug>/call-schedules/statistics
Authorization: Bearer <token>
```

#### **Get Due Call Schedules**
```http
GET /call-scheduling/<org_slug>/call-schedules/due
Authorization: Bearer <token>
```

#### **Trigger Overdue Calls Manually**
```http
POST /call-scheduling/<org_slug>/call-schedules/trigger-overdue
Authorization: Bearer <token>
```

## 🤖 **Automated Call Scheduler**

### **Running the Scheduler**

The automated call scheduler can be run in two modes:

#### **One-time Execution**
```bash
python call_scheduler.py --once
```

#### **Continuous Loop (Recommended for Production)**
```bash
python call_scheduler.py
```

### **Scheduler Configuration**

The scheduler runs every hour by default and:

1. **Checks all organizations** for overdue call schedules
2. **Evaluates check-up date thresholds** from HubSpot
3. **Automatically triggers calls** when conditions are met
4. **Logs all activities** for monitoring and debugging

### **Customizing Scheduler Behavior**

Edit `call_scheduler.py` to modify:

- **Check frequency**: Change `time.sleep(3600)` for different intervals
- **Logging level**: Modify logging configuration
- **Error handling**: Adjust retry intervals and error handling logic

## 🔄 **Workflow Examples**

### **Example 1: Manual Call Scheduling**

1. **Agent identifies** a contact needing follow-up
2. **Schedules call** for specific date/time
3. **System stores** schedule in database
4. **At scheduled time**, call is automatically initiated through Bolna AI
5. **Call status** is tracked and updated

### **Example 2: Automatic Call Triggering**

1. **HubSpot contact** has last check-up date: 2024-01-01
2. **System checks** if 5+ days have passed since check-up
3. **Automatically creates** call schedule
4. **Immediately executes** the call through Bolna AI
5. **Updates HubSpot** with new interaction

### **Example 3: Batch Follow-up Campaign**

1. **System identifies** 50 contacts needing follow-up
2. **Creates schedules** for all contacts
3. **Distributes calls** over time to avoid overwhelming
4. **Tracks execution** and success rates
5. **Generates reports** for management review

## 📊 **Monitoring & Reporting**

### **Call Status Tracking**

Each call schedule has a status that progresses through:

- `scheduled` → `in_progress` → `completed`/`failed`/`cancelled`

### **Key Metrics**

- **Total scheduled calls** per organization
- **Call completion rates**
- **Average response times**
- **Failed call analysis**
- **Check-up date compliance**

### **Logging**

The system provides comprehensive logging:

- **Application logs**: Call scheduling activities
- **Scheduler logs**: Automated execution details
- **Error logs**: Failed operations and debugging info

## 🛠 **Troubleshooting**

### **Common Issues**

#### **HubSpot Connection Failed**
- Verify API key and permissions
- Check network connectivity
- Ensure HubSpot account is active

#### **Bolna AI Call Failed**
- Verify API key and agent configuration
- Check phone number format
- Ensure agent is properly configured

#### **Database Connection Issues**
- Verify Supabase credentials
- Check database permissions
- Ensure tables are properly created

### **Debug Mode**

Enable debug logging by setting:

```python
logging.getLogger().setLevel(logging.DEBUG)
```

### **Manual Testing**

Test individual components:

```bash
# Test HubSpot connection
python -c "from agentsdr.services.hubspot_service import HubSpotService; print(HubSpotService().get_contacts_needing_followup())"

# Test call scheduling
python -c "from agentsdr.services.call_scheduling_service import CallSchedulingService; print(CallSchedulingService().get_due_call_schedules('org_id'))"
```

## 🔒 **Security & Permissions**

### **Access Control**

- **Organization-based isolation**: Users can only access their organization's data
- **Role-based permissions**: Admin users have full access, members have limited access
- **API authentication**: All endpoints require valid authentication tokens

### **Data Privacy**

- **Contact information** is stored securely
- **Phone numbers** are encrypted at rest
- **API keys** are stored in environment variables
- **Audit trails** track all scheduling activities

## 🚀 **Production Deployment**

### **Recommended Setup**

1. **Use process manager** (PM2, Supervisor) for the scheduler
2. **Set up monitoring** (Prometheus, Grafana) for system health
3. **Configure alerts** for failed calls or system issues
4. **Regular backups** of call schedule data
5. **Load balancing** for high-traffic scenarios

### **Performance Optimization**

- **Database indexing** on frequently queried fields
- **Connection pooling** for database connections
- **Caching** for frequently accessed HubSpot data
- **Batch processing** for large contact lists

## 📚 **API Reference**

### **Call Schedule Object**

```json
{
    "id": "uuid",
    "org_id": "uuid",
    "agent_id": "uuid",
    "contact_id": "hubspot_contact_id",
    "contact_name": "string",
    "contact_phone": "string",
    "scheduled_at": "ISO 8601 datetime",
    "call_topic": "string",
    "call_language": "string",
    "is_active": "boolean",
    "call_status": "scheduled|in_progress|completed|failed|cancelled",
    "bolna_call_id": "string",
    "auto_trigger_enabled": "boolean",
    "checkup_threshold_days": "integer",
    "last_checkup_date": "ISO 8601 date",
    "created_at": "ISO 8601 datetime",
    "updated_at": "ISO 8601 datetime"
}
```

### **Error Responses**

```json
{
    "success": false,
    "error": "Error description",
    "details": "Additional error information"
}
```

## 🤝 **Support & Contributing**

### **Getting Help**

- **Documentation**: Check this guide and inline code comments
- **Logs**: Review application and scheduler logs
- **Community**: Join the AgentSDR community forums
- **Issues**: Report bugs through the project issue tracker

### **Contributing**

1. **Fork the repository**
2. **Create feature branch**
3. **Make your changes**
4. **Add tests** for new functionality
5. **Submit pull request**

---

## 🎉 **Quick Start Checklist**

- [ ] Database tables created (`call_scheduling.sql`)
- [ ] Environment variables configured
- [ ] Flask app restarted
- [ ] Test API endpoints
- [ ] Configure HubSpot properties
- [ ] Set up Bolna AI agent
- [ ] Test manual call scheduling
- [ ] Test automatic triggering
- [ ] Set up automated scheduler
- [ ] Monitor system logs

**Congratulations!** You now have a fully functional call scheduling system that integrates with HubSpot CRM and Bolna AI for automated customer follow-up calls. 🚀
