#!/usr/bin/env python3
"""
Test the webhook scheduler endpoint
"""

import requests
import json

def test_webhook_locally():
    """Test webhook on local server"""
    print("=== TESTING WEBHOOK SCHEDULER LOCALLY ===")
    
    # First set up a test schedule for 2 minutes from now
    import subprocess
    result = subprocess.run(['python', 'test_schedule_today.py'], capture_output=True, text=True)
    print("Schedule setup result:", result.stdout)
    
    if result.returncode != 0:
        print("Failed to set up test schedule")
        return
    
    # Test the webhook endpoint locally
    try:
        url = "http://localhost:5000/api/webhook/trigger-schedules"
        headers = {"Content-Type": "application/json"}
        data = {"api_key": "agentsdr-scheduler-2024"}
        
        print(f"Testing webhook at: {url}")
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook test successful!")
        else:
            print("❌ Webhook test failed")
            
    except requests.RequestException as e:
        print(f"❌ Connection error: {e}")
        print("Make sure your Flask app is running locally")

def test_webhook_on_railway():
    """Test webhook on Railway deployment"""
    print("=== TESTING WEBHOOK SCHEDULER ON RAILWAY ===")
    
    # Replace with your actual Railway URL
    railway_url = "https://agentsdrmain-production.up.railway.app"
    
    try:
        url = f"{railway_url}/api/webhook/trigger-schedules"
        headers = {"Content-Type": "application/json"}
        data = {"api_key": "agentsdr-scheduler-2024"}
        
        print(f"Testing webhook at: {url}")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Railway webhook test successful!")
        else:
            print("❌ Railway webhook test failed")
            
    except requests.RequestException as e:
        print(f"❌ Connection error: {e}")
        print("Check your Railway URL")

if __name__ == "__main__":
    print("Choose test option:")
    print("1. Test locally (requires local server running)")
    print("2. Test on Railway")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        test_webhook_locally()
    elif choice == "2":
        test_webhook_on_railway()
    else:
        print("Invalid choice")