# 🚀 Enhanced Email Scheduler Setup Guide

## 🎯 **New Features Added**

Your email scheduler now supports:

### **📧 Email Criteria Options:**
- **Last 24 Hours** - Get emails from past day
- **Last 7 Days** - Get emails from past week  
- **Custom Hours Back** - Set any number of hours (1-168)
- **Latest N Emails** - Get most recent X emails (1-100)
- **Oldest N Emails** - Get oldest X emails (1-100)

### **🕐 Schedule Frequencies:**
- **Daily** - Runs every day at specified time
- **Weekly** - Runs once per week on chosen day
- **Monthly** - Runs once per month on chosen date

### **⚡ Smart Features:**
- **Next Run Calculation** - Shows when next email will be sent
- **Immediate Execution** - Schedules run within 5 minutes of being set
- **Duplicate Prevention** - Won't send multiple emails in same hour
- **Error Recovery** - Graceful handling of failures

---

## 🛠️ **Setup Instructions**

### **Step 1: Update Database Schema**
Run the schema update to add new columns:

```bash
# In your Supabase SQL editor, run:
D:\Hope Projects\AgentSDR_Main\update_schedules_schema.sql
```

### **Step 2: Configure SMTP (Required)**
Update your `.env` file with email settings:

```bash
# SMTP Configuration for sending emails
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-gmail-app-password  # Generate in Google Account Settings
SMTP_USE_TLS=true
```

### **Step 3: Start Enhanced Scheduler**
Use the new enhanced scheduler:

```bash
# Start the enhanced scheduler
python enhanced_scheduler.py

# Or run in background (Linux/Mac)
nohup python enhanced_scheduler.py > scheduler.log 2>&1 &

# Windows background
start /B python enhanced_scheduler.py
```

---

## 🎮 **How to Use**

### **1. Creating Schedules**

1. **Go to your Email Summarizer agent**
2. **Scroll to "Automated Daily Summaries" section**
3. **Configure Email Criteria:**
   - Choose: Last 24 Hours, Last 7 Days, Custom Hours, Latest N, or Oldest N
   - For Custom Hours: Enter 1-168 hours
   - For Latest/Oldest N: Enter 1-100 email count

4. **Configure Schedule Frequency:**
   - **Daily**: Runs every day at specified time
   - **Weekly**: Choose day of week (Monday-Sunday) 
   - **Monthly**: Choose day of month (1-31)

5. **Set Delivery:**
   - Enter recipient email address
   - View calculated "Next Run" time

6. **Save Schedule** - System calculates next execution time

### **2. Managing Schedules**

- ✅ **Pause/Resume**: Toggle schedule on/off
- 📊 **Monitor Status**: See last run time and next scheduled run
- ✏️ **Edit Anytime**: Change frequency, criteria, or email
- 🗑️ **Auto-cleanup**: Failed schedules won't spam

---

## 📋 **Examples**

### **Daily Morning Summary**
- **Frequency**: Daily at 09:00
- **Criteria**: Last 24 Hours  
- **Result**: Every morning at 9 AM, get yesterday's emails

### **Weekly Team Report**
- **Frequency**: Weekly on Monday at 08:00
- **Criteria**: Last 7 Days
- **Result**: Every Monday morning, get full week's emails

### **Monthly Top Emails**
- **Frequency**: Monthly on 1st at 10:00
- **Criteria**: Latest 50 Emails
- **Result**: First of each month, get 50 most recent emails

### **Custom Timeframe**
- **Frequency**: Daily at 17:00  
- **Criteria**: Custom 8 Hours Back
- **Result**: Every evening, get emails from work day (8 hours)

---

## 🔧 **Technical Details**

### **Database Schema**
New columns added to `agent_schedules`:
```sql
- frequency_type: 'daily', 'weekly', 'monthly'
- email_count: Number for latest_n/oldest_n
- email_hours: Number for custom_hours  
- day_of_week: 1-7 for weekly (1=Monday)
- day_of_month: 1-31 for monthly
```

### **Enhanced Scheduler Features**
- ✅ **2-minute check interval** (faster than original 5 minutes)
- ✅ **5-minute execution window** (won't miss schedules)
- ✅ **1-hour duplicate prevention** (no spam)
- ✅ **Auto next-run calculation** (smart scheduling)
- ✅ **Robust error handling** (keeps running)

### **Email Content**
Email summaries now include:
- 📊 **Dynamic statistics** based on criteria
- 🎯 **Personalized subject** with agent name
- 📧 **Beautiful HTML formatting**
- 🕐 **Timestamp and criteria info**

---

## 🚨 **Troubleshooting**

### **Common Issues:**

**"Schedule not saving"**
- Check database schema was updated
- Verify all required fields filled

**"Emails not being sent"**  
- Verify SMTP configuration in `.env`
- Check Gmail app password is correct
- Ensure enhanced_scheduler.py is running

**"No emails found"**
- Check Gmail connection in agent
- Verify criteria matches available emails
- Test with broader criteria (e.g., "Last 7 Days")

**"Wrong schedule time"**
- All times are in UTC
- Check timezone considerations
- Next run shows calculated UTC time

### **Monitoring Commands:**
```bash
# Check if scheduler is running
ps aux | grep enhanced_scheduler

# View scheduler logs  
tail -f scheduler.log

# Test database connection
# Run in Python:
# from agentsdr.core.supabase_client import get_service_supabase
# supabase = get_service_supabase()
# print(supabase.table('agent_schedules').select('*').execute())
```

---

## 🎉 **You're All Set!**

Your enhanced email scheduler now supports:

- ✅ **Flexible Email Criteria** (hours, counts, timeframes)
- ✅ **Multiple Frequencies** (daily, weekly, monthly)  
- ✅ **Smart Scheduling** (immediate execution, next-run calculation)
- ✅ **Reliable Delivery** (duplicate prevention, error recovery)
- ✅ **User-Friendly Interface** (intuitive controls, status display)

Users can create powerful automated email workflows:
- 📧 **Daily work summaries** at start/end of day
- 📊 **Weekly team reports** every Monday
- 📈 **Monthly analytics** on first of month
- 🎯 **Custom schedules** for any need

**The system runs 24/7 and handles everything automatically!** 🚀