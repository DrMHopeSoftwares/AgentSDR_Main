# Hubspot OAuth Setup Guide

This guide explains how to set up Hubspot OAuth integration for the AgentSDR application.

## Prerequisites

1. A Hubspot Developer Account
2. A Hubspot App created in your developer account
3. Access to environment variable configuration

## Step 1: Create a Hubspot App

1. Go to [Hubspot Developer Portal](https://developers.hubspot.com/)
2. Sign in with your Hubspot account
3. Click "Create App"
4. Give your app a name (e.g., "AgentSDR Integration")
5. Select "Private App" if this is for internal use
6. Click "Create App"

## Step 2: Configure OAuth Settings

1. In your app dashboard, go to "Auth" → "OAuth"
2. Set the following OAuth scopes:
   - `contacts` - Access to contact information
   - `oauth` - Basic OAuth functionality
3. Set the redirect URI to: `http://localhost:5000/hubspot/callback` (for development)
4. For production, use your actual domain: `https://yourdomain.com/hubspot/callback`
5. Save the configuration

## Step 3: Get OAuth Credentials

1. In your app dashboard, go to "Auth" → "OAuth"
2. Copy the "Client ID" and "Client Secret"
3. These will be used in your environment variables

## Step 4: Configure Environment Variables

Add the following variables to your `.env` file:

```bash
# Hubspot OAuth Configuration
HUBSPOT_CLIENT_ID=your-hubspot-client-id
HUBSPOT_CLIENT_SECRET=your-hubspot-client-secret
```

Replace `your-hubspot-client-id` and `your-hubspot-client-secret` with the actual values from your Hubspot app.

## Step 5: Test the Integration

1. Start your application
2. Create a new "Hubspot Data" agent
3. Click "View Details" on the agent
4. Click "Connect Hubspot Account"
5. Complete the OAuth flow
6. Test the connection using the "Test Connection" button

## Troubleshooting

### Common Issues

1. **"Hubspot OAuth not configured" error**
   - Make sure you've set the `HUBSPOT_CLIENT_ID` environment variable
   - Restart your application after setting environment variables

2. **"Invalid redirect URI" error**
   - Verify the redirect URI in your Hubspot app matches exactly
   - Check that you're using the correct protocol (http vs https)

3. **"Token exchange failed" error**
   - Verify your `HUBSPOT_CLIENT_SECRET` is correct
   - Check that your app has the correct OAuth scopes

4. **"Hubspot API error" when testing connection**
   - Ensure your OAuth scopes include `contacts`
   - Check that your access token hasn't expired

### OAuth Scopes Explained

- `contacts`: Allows access to contact information in your Hubspot CRM
- `oauth`: Basic OAuth functionality for authentication

### Security Notes

- Never commit your `.env` file to version control
- Keep your client secret secure
- Use HTTPS in production
- Regularly rotate your OAuth credentials

## API Endpoints

The following endpoints are available for Hubspot integration:

- `GET /<org_slug>/agents/<agent_id>/hubspot/auth` - Initiate OAuth flow
- `GET /hubspot/callback` - Handle OAuth callback
- `POST /<org_slug>/agents/<agent_id>/hubspot/test` - Test connection

## Next Steps

Once connected, you can:

1. Access contact data from Hubspot
2. Analyze company information
3. Process deal pipeline data
4. Generate reports and insights

Advanced features like automated reporting and AI-powered insights are coming soon!
