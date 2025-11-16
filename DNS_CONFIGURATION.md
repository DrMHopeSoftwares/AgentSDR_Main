# DNS Configuration Guide for autoaisale.com

This guide will help you configure your domain `autoaisale.com` to point to your AgentSDR deployment.

## Overview

You need to configure DNS records at your domain registrar to point your domain to your hosting platform (Render, Railway, Vercel, or custom server).

---

## Step 1: Choose Your Deployment Platform

### Option A: Render.com (Recommended)

1. **Get your Render app URL**
   - Go to https://dashboard.render.com/
   - Select your web service
   - Copy the Render URL (e.g., `your-app.onrender.com`)

2. **Add Custom Domain in Render**
   - In your Render dashboard, go to your service
   - Navigate to "Settings" > "Custom Domains"
   - Click "Add Custom Domain"
   - Enter: `autoaisale.com`
   - Enter: `www.autoaisale.com`
   - Render will provide DNS records to configure

3. **Configure DNS at your registrar**:
   ```
   Type: A Record
   Name: @
   Value: [IP provided by Render]
   TTL: 3600

   Type: CNAME
   Name: www
   Value: your-app.onrender.com
   TTL: 3600
   ```

### Option B: Railway.app

1. **Get your Railway domain**
   - Go to https://railway.app/dashboard
   - Select your project
   - Click on "Settings" > "Domains"
   - Add custom domain: `autoaisale.com`

2. **Configure DNS**:
   ```
   Type: CNAME
   Name: @
   Value: [Railway provides this]
   TTL: 3600

   Type: CNAME
   Name: www
   Value: [Railway provides this]
   TTL: 3600
   ```

### Option C: Vercel

1. **Add domain in Vercel**
   - Go to https://vercel.com/dashboard
   - Select your project
   - Go to "Settings" > "Domains"
   - Add: `autoaisale.com`

2. **Configure DNS**:
   ```
   Type: A Record
   Name: @
   Value: 76.76.21.21
   TTL: 3600

   Type: CNAME
   Name: www
   Value: cname.vercel-dns.com
   TTL: 3600
   ```

---

## Step 2: Configure DNS at Your Domain Registrar

### Where did you purchase autoaisale.com?

#### If from GoDaddy:

1. Log in to https://dcc.godaddy.com/
2. Find your domain `autoaisale.com`
3. Click "DNS" or "Manage DNS"
4. Add the DNS records from your chosen platform above
5. Save changes

#### If from Namecheap:

1. Log in to https://www.namecheap.com/
2. Go to "Domain List"
3. Click "Manage" next to autoaisale.com
4. Go to "Advanced DNS"
5. Add the DNS records from your chosen platform above
6. Save changes

#### If from Google Domains:

1. Log in to https://domains.google.com/
2. Find autoaisale.com
3. Click "DNS" in the left sidebar
4. Add the DNS records from your chosen platform above
5. Save

#### If from another registrar:

1. Log in to your domain registrar
2. Look for "DNS Settings", "DNS Management", or "Nameservers"
3. Add the records from your chosen platform
4. Save changes

---

## Step 3: SSL/TLS Certificate

Most platforms (Render, Railway, Vercel) automatically provision SSL certificates for your custom domain.

**Wait time**: 24-48 hours for DNS propagation and SSL certificate issuance.

---

## Step 4: Verify Configuration

### Check DNS Propagation:

```bash
# Check A record
dig autoaisale.com

# Check CNAME record
dig www.autoaisale.com

# Or use online tools:
# https://dnschecker.org/
# https://www.whatsmydns.net/
```

### Test Your Domain:

1. Wait 15-30 minutes after DNS configuration
2. Visit: https://autoaisale.com
3. Visit: https://www.autoaisale.com
4. Both should load your application with HTTPS

---

## Common DNS Record Examples

### For Render.com:
```
Type  | Name | Value                    | TTL
------|------|--------------------------|-----
A     | @    | 216.24.57.1             | 3600
CNAME | www  | your-app.onrender.com   | 3600
```

### For Railway.app:
```
Type  | Name | Value                        | TTL
------|------|------------------------------|-----
CNAME | @    | your-app.up.railway.app     | 3600
CNAME | www  | your-app.up.railway.app     | 3600
```

### For Vercel:
```
Type  | Name | Value                    | TTL
------|------|--------------------------|-----
A     | @    | 76.76.21.21             | 3600
CNAME | www  | cname.vercel-dns.com    | 3600
```

---

## Step 5: Update Email Configuration (Optional)

If you want to use custom email addresses like `sales@autoaisale.com`:

### Option A: Google Workspace (Recommended for Business)

1. Sign up at https://workspace.google.com/
2. Verify domain ownership
3. Add MX records provided by Google:
   ```
   Priority | Value
   ---------|------------------------------
   1        | ASPMX.L.GOOGLE.COM
   5        | ALT1.ASPMX.L.GOOGLE.COM
   5        | ALT2.ASPMX.L.GOOGLE.COM
   10       | ALT3.ASPMX.L.GOOGLE.COM
   10       | ALT4.ASPMX.L.GOOGLE.COM
   ```

### Option B: Email Forwarding (Free)

Most registrars offer free email forwarding:

1. Set up email forwarding in your registrar
2. Forward `sales@autoaisale.com` → your personal email
3. Forward `support@autoaisale.com` → your support email

---

## Troubleshooting

### Problem: Domain not working after 24 hours

**Solution**:
```bash
# Check if DNS has propagated
nslookup autoaisale.com

# Check with different DNS servers
nslookup autoaisale.com 8.8.8.8  # Google DNS
nslookup autoaisale.com 1.1.1.1  # Cloudflare DNS
```

### Problem: SSL certificate not provisioned

**Solution**:
- Wait 48 hours for automatic provisioning
- Check platform documentation for manual certificate upload
- Verify DNS records are correct

### Problem: www not working

**Solution**:
- Ensure you added BOTH `@` and `www` records
- Some platforms need separate entries for each

---

## Quick Start Checklist

- [ ] Choose deployment platform (Render/Railway/Vercel)
- [ ] Deploy application to platform
- [ ] Add custom domain in platform dashboard
- [ ] Get DNS configuration from platform
- [ ] Log in to domain registrar
- [ ] Add A and/or CNAME records
- [ ] Wait 24-48 hours for propagation
- [ ] Verify https://autoaisale.com works
- [ ] Verify https://www.autoaisale.com works
- [ ] Set up email (optional)

---

## Need Help?

- **DNS Checker**: https://dnschecker.org/
- **Render Docs**: https://render.com/docs/custom-domains
- **Railway Docs**: https://docs.railway.app/deploy/deployments#custom-domains
- **Vercel Docs**: https://vercel.com/docs/concepts/projects/domains

---

## Current Configuration Status

**Domain**: autoaisale.com
**Application**: AutoAISale (AI-Powered Sales Automation)
**Deployment Platform**: [To be configured]
**DNS Status**: [Pending configuration]
**SSL Status**: [Pending configuration]

---

*Last Updated: November 2025*
