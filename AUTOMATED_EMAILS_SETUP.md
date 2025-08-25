# 🤖 Automated Email Summarization Setup Guide

This guide will help you set up automated daily email summaries that are sent to users at their chosen time.

## 🎯 **What This Feature Does**

- **Daily Automation:** Runs at user-selected time (e.g., 9:00 AM daily)
- **Email Summaries:** Fetches emails from last 24 hours and summarizes them
- **Email Delivery:** Sends beautiful HTML summaries to user's email
- **User Control:** Users can set time, recipient email, and pause/resume

## 📋 **Prerequisites**

1. ✅ **Gmail API Setup** (already done)
2. ✅ **OpenAI API Key** (already configured)
3. ✅ **Supabase Database** (already configured)
4. 🔧 **SMTP Email Service** (needs setup)

## 🔧 **Step 1: Setup SMTP Email Service**

### Option A: Gmail SMTP (Recommended)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password:**
   - Go to Google Account Settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. **Update your `.env` file:**

```bash
# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-16-character-app-password
SMTP_USE_TLS=true
```

### Option B: Other SMTP Providers

You can use any SMTP provider (SendGrid, Mailgun, etc.):

```bash
# Example for SendGrid
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASS=your-sendgrid-api-key
SMTP_USE_TLS=true
```

## 🗄️ **Step 2: Update Database Schema**

Run the updated schema to create the scheduling table:

```bash
# Apply the new schema to your Supabase database
# The agent_schedules table will be created automatically
```

## 🚀 **Step 3: Start the Scheduler**

### Method 1: Direct Python Script

```bash
# Start the scheduler
python start_scheduler.py
```

### Method 2: Background Process (Linux/Mac)

```bash
# Start in background
nohup python start_scheduler.py > scheduler.log 2>&1 &

# Check if running
ps aux | grep scheduler

# View logs
tail -f scheduler.log
```

### Method 3: Windows Service

```bash
# Create a batch file (start_scheduler.bat)
python start_scheduler.py

# Run as Windows service using Task Scheduler
```

### Method 4: Docker (Recommended for Production)

Add to your `docker-compose.yml`:

```yaml
services:
  scheduler:
    build: .
    command: python start_scheduler.py
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
      - SMTP_HOST=${SMTP_HOST}
      - SMTP_USER=${SMTP_USER}
      - SMTP_PASS=${SMTP_PASS}
    restart: unless-stopped
```

## 🎮 **Step 4: Test the Feature**

1. **Start your main app:**
   ```bash
   python app.py
   ```

2. **Go to your agent page:**
   - Navigate to: `http://localhost:5000/orgs/{org}/agents/{agent_id}`

3. **Set up automated summaries:**
   - Scroll to "Automated Daily Summaries" section
   - Set time (e.g., 09:00)
   - Enter recipient email
   - Click "Save Schedule"

4. **Test immediately:**
   - The scheduler will run every 5 minutes
   - If current time matches your schedule, it will execute

## 📊 **How It Works**

### **Scheduler Logic:**
- ✅ **Checks every 5 minutes** for due schedules
- ✅ **Runs within 5-minute window** of scheduled time
- ✅ **Prevents duplicates** (23-hour cooldown)
- ✅ **Handles errors gracefully**

### **Email Summary Process:**
1. **Fetch emails** from Gmail (last 24 hours)
2. **Summarize with OpenAI** (up to 50 emails)
3. **Create beautiful HTML email**
4. **Send via SMTP**
5. **Update last_run timestamp**

### **Email Template Features:**
- 🎨 **Beautiful HTML design**
- 📊 **Summary statistics**
- 👤 **Sender information**
- 📝 **Email subjects**
- 📅 **Timestamps**
- 📧 **Professional formatting**

## 🔍 **Monitoring & Debugging**

### **Check Scheduler Status:**
```bash
# View scheduler logs
tail -f scheduler.log

# Check if scheduler is running
ps aux | grep scheduler
```

### **Database Queries:**
```sql
-- Check all schedules
SELECT * FROM agent_schedules;

-- Check active schedules
SELECT * FROM agent_schedules WHERE is_active = true;

-- Check recent runs
SELECT agent_id, last_run_at, recipient_email 
FROM agent_schedules 
WHERE last_run_at IS NOT NULL 
ORDER BY last_run_at DESC;
```

### **Common Issues:**

1. **"SMTP configuration incomplete"**
   - Check your `.env` file has all SMTP settings
   - Verify Gmail app password is correct

2. **"No Gmail refresh token found"**
   - Reconnect Gmail in the agent settings
   - Check agent config in database

3. **"No emails found"**
   - Check Gmail connection
   - Verify emails exist in the specified time range

4. **Scheduler not running**
   - Check if `start_scheduler.py` is running
   - Verify environment variables
   - Check logs for errors

## 🎯 **Production Deployment**

### **For Production Servers:**

1. **Use systemd service (Linux):**
   ```bash
   # Create service file
   sudo nano /etc/systemd/system/agentsdr-scheduler.service
   
   [Unit]
   Description=AgentSDR Email Scheduler
   After=network.target
   
   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/path/to/agentsdr
   Environment=PATH=/path/to/venv/bin
   ExecStart=/path/to/venv/bin/python start_scheduler.py
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   
   # Enable and start
   sudo systemctl enable agentsdr-scheduler
   sudo systemctl start agentsdr-scheduler
   ```

2. **Use Docker Compose:**
   ```bash
   # Add scheduler service to docker-compose.yml
   # Run with: docker-compose up -d
   ```

3. **Use Cron Job:**
   ```bash
   # Add to crontab
   */5 * * * * cd /path/to/agentsdr && python start_scheduler.py
   ```

## 🎉 **You're All Set!**

Your automated email summarization system is now ready! Users can:

- ✅ **Set daily schedule time**
- ✅ **Choose recipient email**
- ✅ **Pause/resume automation**
- ✅ **Receive beautiful email summaries**
- ✅ **View schedule status**

The system will automatically:
- 🔄 **Run daily at specified time**
- 📧 **Fetch and summarize emails**
- 📨 **Send beautiful HTML summaries**
- 📊 **Track execution history**

**Happy automating! 🚀**
