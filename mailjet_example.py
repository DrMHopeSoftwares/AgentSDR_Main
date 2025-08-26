#!/usr/bin/env python3
"""
Example script demonstrating how to use Mailjet integration for sending email summaries.

Before running this script, make sure to set the following environment variables:
- MAILJET_API_KEY: Your Mailjet API key
- MAILJET_API_SECRET: Your Mailjet API secret  
- MAILJET_SENDER_EMAIL: Verified sender email address
- MAILJET_SENDER_NAME: Sender name (optional, defaults to 'AgentSDR')
- USE_MAILJET: Set to 'true' to use Mailjet, 'false' for SMTP fallback
"""

import os
from datetime import datetime
from agentsdr.core.email import send_email_summary, get_mailjet_service

# Example email summaries data
sample_summaries = [
    {
        'id': 'msg1',
        'sender': 'John Doe',
        'subject': 'Project Update',
        'date': '2024-01-15 09:30',
        'summary': 'John provided an update on the Q1 project milestones. The development is on track and testing phase will begin next week.',
        'status': 'success'
    },
    {
        'id': 'msg2', 
        'sender': 'Sarah Johnson',
        'subject': 'Meeting Request',
        'date': '2024-01-15 11:15',
        'summary': 'Sarah is requesting a meeting to discuss the new client requirements. She suggests Wednesday afternoon.',
        'status': 'success'
    },
    {
        'id': 'msg3',
        'sender': 'Marketing Team',
        'subject': 'Campaign Results',
        'date': '2024-01-15 14:20',
        'summary': 'The latest email campaign achieved a 25% open rate and 5% click-through rate, exceeding our targets.',
        'status': 'success'
    }
]

def test_mailjet_integration():
    """Test the Mailjet integration with sample data"""
    
    # Check if Mailjet credentials are configured
    required_vars = ['MAILJET_API_KEY', 'MAILJET_API_SECRET', 'MAILJET_SENDER_EMAIL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please configure these variables before running the test.")
        return False
    
    print("🔧 Testing Mailjet integration...")
    print(f"📧 Sender Email: {os.getenv('MAILJET_SENDER_EMAIL')}")
    print(f"👤 Sender Name: {os.getenv('MAILJET_SENDER_NAME', 'AgentSDR')}")
    print(f"📊 Sample summaries: {len(sample_summaries)} emails")
    
    # Get test recipient email (you can modify this)
    recipient_email = input("Enter recipient email address for test: ").strip()
    if not recipient_email:
        print("❌ No recipient email provided")
        return False
    
    try:
        # Test sending email summary
        print(f"\n📤 Sending test email summary to {recipient_email}...")
        
        success = send_email_summary(
            recipient_email=recipient_email,
            summaries=sample_summaries,
            agent_name="Test Agent",
            criteria_type="last_24_hours"
        )
        
        if success:
            print("✅ Email sent successfully!")
            print("📬 Check your inbox for the email summary.")
        else:
            print("❌ Failed to send email. Check the logs for details.")
            
        return success
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

def test_mailjet_service_directly():
    """Test the MailjetService class directly"""
    
    print("\n🧪 Testing MailjetService directly...")
    
    try:
        mailjet_service = get_mailjet_service()
        
        if not mailjet_service.client:
            print("❌ Mailjet client not initialized. Check your API credentials.")
            return False
            
        recipient_email = input("Enter recipient email address for direct test: ").strip()
        if not recipient_email:
            print("❌ No recipient email provided")
            return False
            
        success = mailjet_service.send_email_summary(
            recipient_email=recipient_email,
            summaries=sample_summaries,
            agent_name="Direct Test Agent",
            criteria_type="custom_test"
        )
        
        if success:
            print("✅ Direct Mailjet test successful!")
        else:
            print("❌ Direct Mailjet test failed.")
            
        return success
        
    except Exception as e:
        print(f"❌ Error during direct test: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Mailjet Integration Test Script")
    print("=" * 50)
    
    # Test the main function
    test_result1 = test_mailjet_integration()
    
    # Test the service directly
    test_result2 = test_mailjet_service_directly()
    
    print("\n" + "=" * 50)
    print("📋 Test Results:")
    print(f"Main function test: {'✅ PASSED' if test_result1 else '❌ FAILED'}")
    print(f"Direct service test: {'✅ PASSED' if test_result2 else '❌ FAILED'}")
    
    if test_result1 and test_result2:
        print("\n🎉 All tests passed! Mailjet integration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check your configuration and logs.")