# Step-by-Step Instructions: Link autoaisale.com to Your Project

Follow these steps **in order** to get your domain working with your AutoAISale application.

---

## ⏱️ **Total Time Required**
- **Setup Time**: 30-60 minutes
- **DNS Propagation**: 24-48 hours
- **SSL Certificate**: Automatic (after DNS propagates)

---

## 📋 **STEP 1: Choose Your Hosting Platform**

You need to pick where you'll host your application. Choose **ONE** option:

### **Option A: Render.com** ⭐ **RECOMMENDED** ⭐

**Why?**
- Free tier available
- Automatic SSL certificates
- Easy deployment
- Good for Python/Flask apps

### **Option B: Railway.app**

**Why?**
- Modern interface
- $5 credit free
- Very fast deployments

### **Option C: Vercel**

**Why?**
- Great for static sites
- Free tier
- Global CDN

**👉 For this guide, I'll use Render.com (most popular for Flask apps)**

---

## 🚀 **STEP 2: Deploy Your App to Render.com**

### **2.1: Create Render Account**

1. Go to: https://render.com/
2. Click **"Get Started"** (top right)
3. Sign up with:
   - GitHub account (RECOMMENDED) ✅
   - OR email/password
4. Verify your email

---

### **2.2: Connect Your GitHub Repository**

1. In Render dashboard, click **"New +"** (top right)
2. Select **"Web Service"**
3. Click **"Connect GitHub"**
4. Authorize Render to access your repos
5. Find and select: **"AgentSDR_Main"** repository
6. Click **"Connect"**

---

### **2.3: Configure Your Web Service**

Fill in these settings:

| Field | Value |
|-------|-------|
| **Name** | `autoaisale` |
| **Region** | Oregon (US West) or closest to you |
| **Branch** | `main` |
| **Root Directory** | `.` (leave blank) |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 4` |
| **Plan** | `Free` (to start) |

**Click "Advanced"** and add these environment variables:

---

### **2.4: Add Environment Variables** ⚠️ **CRITICAL**

Click **"Add Environment Variable"** for each one:

#### **Required Variables:**

```
FLASK_ENV=production
FLASK_SECRET_KEY=your-super-secret-random-key-here-change-this
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
```

#### **How to generate FLASK_SECRET_KEY:**

**On Mac/Linux:**
```bash
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

**On Windows:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and use it as your `FLASK_SECRET_KEY`.

#### **Optional but Recommended:**

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
SMTP_USE_TLS=true

OPENAI_API_KEY=your-openai-key
HUBSPOT_TOKEN=your-hubspot-token
BOLNA_API_KEY=your-bolna-key
```

---

### **2.5: Deploy!**

1. Scroll to bottom
2. Click **"Create Web Service"**
3. Wait 3-5 minutes for deployment
4. You'll see build logs
5. When complete, you'll see: **"Your service is live at https://autoaisale.onrender.com"**

---

## 🌐 **STEP 3: Add Custom Domain in Render**

### **3.1: Open Domain Settings**

1. In Render dashboard, click on your **"autoaisale"** service
2. Click **"Settings"** tab (left sidebar)
3. Scroll down to **"Custom Domains"** section
4. Click **"Add Custom Domain"**

---

### **3.2: Add Your Domains**

**Add BOTH of these (separately):**

1. First domain:
   - Enter: `autoaisale.com`
   - Click **"Save"**

2. Second domain:
   - Click **"Add Custom Domain"** again
   - Enter: `www.autoaisale.com`
   - Click **"Save"**

---

### **3.3: Get DNS Configuration from Render**

After adding each domain, Render will show you DNS records. **Write these down:**

**For autoaisale.com:**
```
Type: A
Name: @
Value: 216.24.57.1  (example - use the IP Render gives you)
```

**For www.autoaisale.com:**
```
Type: CNAME
Name: www
Value: autoaisale.onrender.com  (use your actual Render URL)
```

⚠️ **Don't close this page yet! You need these values for the next step.**

---

## 🔧 **STEP 4: Configure DNS at Your Domain Registrar**

### **4.1: Find Where You Bought autoaisale.com**

**Where did you purchase the domain?**

- [ ] GoDaddy
- [ ] Namecheap
- [ ] Google Domains
- [ ] Domain.com
- [ ] Other: __________

**👇 Follow the instructions for YOUR registrar below:**

---

### **4.2a: If You Used GoDaddy**

1. Go to: https://dcc.godaddy.com/
2. Sign in with your GoDaddy account
3. Find **"My Products"** > **"Domains"**
4. Find `autoaisale.com` in the list
5. Click the **⋯** (three dots) menu
6. Click **"Manage DNS"**

**Add A Record:**
1. Click **"Add"** button
2. Select **"A"** from the Type dropdown
3. In **"Name"** field: enter `@`
4. In **"Value"** field: enter the IP from Render (e.g., `216.24.57.1`)
5. Set **"TTL"** to `600` (10 minutes)
6. Click **"Save"**

**Add CNAME Record:**
1. Click **"Add"** button again
2. Select **"CNAME"** from the Type dropdown
3. In **"Name"** field: enter `www`
4. In **"Value"** field: enter your Render URL (e.g., `autoaisale.onrender.com`)
5. Set **"TTL"** to `600`
6. Click **"Save"**

✅ **Done with GoDaddy!**

---

### **4.2b: If You Used Namecheap**

1. Go to: https://www.namecheap.com/
2. Sign in to your account
3. Click **"Domain List"** (left sidebar)
4. Find `autoaisale.com`
5. Click **"Manage"** button next to it
6. Click the **"Advanced DNS"** tab

**Add A Record:**
1. Click **"Add New Record"**
2. Type: Select **"A Record"**
3. Host: enter `@`
4. Value: enter the IP from Render (e.g., `216.24.57.1`)
5. TTL: Select **"Automatic"** or **"1 min"**
6. Click the **green checkmark** ✅

**Add CNAME Record:**
1. Click **"Add New Record"** again
2. Type: Select **"CNAME Record"**
3. Host: enter `www`
4. Value: enter your Render URL (e.g., `autoaisale.onrender.com`)
5. TTL: Select **"Automatic"** or **"1 min"**
6. Click the **green checkmark** ✅

✅ **Done with Namecheap!**

---

### **4.2c: If You Used Google Domains**

1. Go to: https://domains.google.com/
2. Sign in with your Google account
3. Find `autoaisale.com` in your domain list
4. Click on it
5. Click **"DNS"** in the left sidebar
6. Scroll to **"Custom records"** section

**Add A Record:**
1. Click **"Create new record"**
2. Host name: leave blank or enter `@`
3. Type: Select **"A"**
4. TTL: enter `600` (10 minutes)
5. Data: enter the IP from Render (e.g., `216.24.57.1`)
6. Click **"Add"**

**Add CNAME Record:**
1. Click **"Create new record"** again
2. Host name: enter `www`
3. Type: Select **"CNAME"**
4. TTL: enter `600`
5. Data: enter your Render URL (e.g., `autoaisale.onrender.com`)
6. Click **"Add"**

✅ **Done with Google Domains!**

---

### **4.2d: If You Used Another Registrar**

**General Steps (works for most registrars):**

1. Log in to your domain registrar's website
2. Find "DNS Settings", "DNS Management", or "Nameservers"
3. Look for "Add Record" or "Custom Records"
4. Add these two records:

**Record 1:**
```
Type: A
Name/Host: @ (or leave blank)
Value/Points to: [IP from Render]
TTL: 600 or Auto
```

**Record 2:**
```
Type: CNAME
Name/Host: www
Value/Points to: [your-app].onrender.com
TTL: 600 or Auto
```

5. Save changes

---

## ⏳ **STEP 5: Wait for DNS Propagation**

### **What is DNS Propagation?**

DNS propagation is the time it takes for your domain settings to update across the internet.

**Timeline:**
- ⚡ **First check**: 15-30 minutes (sometimes works quickly!)
- 🕐 **Usually works**: 2-6 hours
- ⏰ **Maximum**: 24-48 hours (rare)

---

### **5.1: Check If DNS Has Propagated**

**Method 1: Command Line** (Mac/Linux)
```bash
# Check main domain
dig autoaisale.com

# Check www subdomain
dig www.autoaisale.com
```

**Method 2: Online Tools** (Any device)
1. Go to: https://dnschecker.org/
2. Enter: `autoaisale.com`
3. Select: **"A"** record type
4. Click **"Search"**
5. Check if the IP matches what Render gave you

**Method 3: Just Try It!**
1. Open browser (incognito/private mode)
2. Try: https://autoaisale.com
3. If you see your app, it's working! 🎉
4. If you see an error, wait longer

---

## 🔒 **STEP 6: SSL Certificate (Automatic)**

### **What Happens:**

Once DNS is configured, Render **automatically**:
1. Detects your custom domain
2. Requests an SSL certificate from Let's Encrypt
3. Installs the certificate
4. Enables HTTPS

**Timeline:**
- Usually: 5-15 minutes after DNS propagates
- Maximum: 2-4 hours

---

### **6.1: Verify SSL is Working**

1. Go to: https://autoaisale.com (note the **https://**)
2. Look for the **padlock icon** 🔒 in browser address bar
3. Click the padlock
4. Should say: "Connection is secure"

✅ **If you see the padlock, SSL is working!**

---

## ✅ **STEP 7: Verify Everything Works**

### **7.1: Test All URLs**

Try these in your browser:

| URL | Should... |
|-----|-----------|
| https://autoaisale.com | ✅ Load your app |
| https://www.autoaisale.com | ✅ Load your app |
| http://autoaisale.com | ✅ Redirect to https:// |
| http://www.autoaisale.com | ✅ Redirect to https:// |

---

### **7.2: Test Features**

✅ **Homepage loads with AutoAISale branding**
✅ **Sign up form works**
✅ **Login form works**
✅ **All images load (especially hero image)**
✅ **Buttons are visible (not white on white)**
✅ **Footer shows "© 2025 AutoAISale"**

---

## 🎉 **STEP 8: You're Live!**

### **What You Can Do Now:**

✅ Share your website: https://autoaisale.com
✅ Add to business cards
✅ Use in email signatures
✅ Share on social media
✅ Start accepting signups!

---

## 📧 **BONUS: Set Up Email (Optional)**

### **Option 1: Email Forwarding (Free)**

**Set up at your registrar:**

Most registrars offer free email forwarding:

1. Go to your domain registrar
2. Find "Email Forwarding" or "Email Settings"
3. Create forwards:
   - `sales@autoaisale.com` → your-personal-email@gmail.com
   - `support@autoaisale.com` → your-support-email@gmail.com

**Now you can:**
- Receive emails sent to sales@autoaisale.com
- Send emails "as" sales@autoaisale.com (configure in Gmail)

---

### **Option 2: Google Workspace (Professional)**

**Cost**: $6/user/month

**Benefits:**
- Full email accounts: sales@autoaisale.com
- 30GB storage per user
- Google Drive, Docs, Sheets
- Professional appearance

**Setup:**
1. Go to: https://workspace.google.com/
2. Sign up and verify domain
3. Add MX records (Google will provide them)
4. Create email accounts

---

## 🆘 **Troubleshooting**

### **Problem 1: Domain not working after 48 hours**

**Solution:**
```bash
# Check if DNS is correct
dig autoaisale.com

# Should show the IP from Render
# If not, re-check your DNS settings at registrar
```

**Also check:**
- Did you save the DNS records?
- Did you add BOTH @ and www records?
- Try a different browser or incognito mode
- Clear your browser cache

---

### **Problem 2: SSL certificate not showing**

**Solution:**
- Wait longer (can take up to 4 hours)
- Check that DNS is fully propagated first
- Go to Render dashboard > Settings > Custom Domains
- Look for "SSL Status" - should say "Active"

---

### **Problem 3: www not working**

**Solution:**
- Make sure you added the CNAME record for "www"
- Check the CNAME points to: `autoaisale.onrender.com` (not the IP!)
- Wait for DNS propagation

---

### **Problem 4: Shows old AgentSDR branding**

**Solution:**
```bash
# Hard refresh your browser
# Mac: Cmd + Shift + R
# Windows: Ctrl + Shift + R

# Or clear browser cache completely
```

---

## 📊 **DNS Configuration Checklist**

Use this to make sure you did everything:

- [ ] Deployed app to Render
- [ ] App is live at autoaisale.onrender.com
- [ ] Added autoaisale.com in Render custom domains
- [ ] Added www.autoaisale.com in Render custom domains
- [ ] Got DNS records from Render dashboard
- [ ] Logged in to domain registrar
- [ ] Added A record for @ (root domain)
- [ ] Added CNAME record for www
- [ ] Saved DNS changes
- [ ] Waited at least 2-4 hours
- [ ] Tested https://autoaisale.com
- [ ] Tested https://www.autoaisale.com
- [ ] SSL certificate is active (padlock showing)
- [ ] All features work on live site

---

## 📞 **Need Help?**

### **Render Support:**
- Docs: https://render.com/docs
- Community: https://community.render.com/
- Status: https://status.render.com/

### **DNS Tools:**
- DNS Checker: https://dnschecker.org/
- What's My DNS: https://www.whatsmydns.net/
- DNS Propagation: https://dnspropagation.net/

---

## 🎯 **Quick Reference**

### **Important URLs:**

| Purpose | URL |
|---------|-----|
| **Live Site** | https://autoaisale.com |
| **Render Dashboard** | https://dashboard.render.com/ |
| **GitHub Repo** | https://github.com/DrMHopeSoftwares/AgentSDR_Main |
| **Domain Registrar** | [Where you bought domain] |

### **Important Commands:**

```bash
# Check DNS
dig autoaisale.com

# Check DNS propagation globally
nslookup autoaisale.com 8.8.8.8

# Hard refresh browser
# Mac: Cmd + Shift + R
# Windows: Ctrl + Shift + R
```

---

## ✨ **Summary**

You've successfully:
1. ✅ Deployed your app to Render
2. ✅ Configured custom domain
3. ✅ Set up DNS records
4. ✅ Got SSL certificate
5. ✅ Your site is live at https://autoaisale.com!

**Congratulations! Your AutoAISale platform is now live on the internet! 🚀**

---

*Last Updated: November 2025*
*Domain: autoaisale.com*
*Platform: Render.com*
