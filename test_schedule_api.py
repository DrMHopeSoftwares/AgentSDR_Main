#!/usr/bin/env python3
"""
Test the schedule API directly to simulate website form submission
"""

import os
import sys
from flask import Flask
from dotenv import load_dotenv
import requests
import json

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Test data (simulating what your website form would send)
test_data = {
    "schedule_time": "15:40:00",  # 3:40 PM
    "recipient_email": "bkmurali683@gmail.com",
    "criteria_type": "last_24_hours",
    "frequency_type": "daily"
}

print("Testing schedule API with data:", test_data)

# You'll need to get the actual URL and agent ID from your website
# Let me help you construct this properly

# Create Flask app to get the agent info
app = Flask(__name__)
app.config.from_object('config.Config')

with app.app_context():
    try:
        from agentsdr.core.supabase_client import get_service_supabase
        supabase = get_service_supabase()
        
        # Get your organization and agent info
        orgs = supabase.table('organizations').select('*').execute()
        if orgs.data:
            org = orgs.data[0]
            print(f"Found org: {org['name']} (slug: {org['slug']})")
            
            # Get agents for this org
            agents = supabase.table('agents').select('*').eq('org_id', org['id']).execute()
            if agents.data:
                agent = agents.data[0]
                print(f"Found agent: {agent['name']} (id: {agent['id']})")
                
                # Construct the API URL
                api_url = f"http://localhost:5000/orgs/{org['slug']}/agents/{agent['id']}/schedule"
                print(f"API URL: {api_url}")
                
                # Test if the route exists and what happens when we post to it
                print("\\nTesting schedule save...")
                
                try:
                    # This would normally require authentication/cookies
                    # But let's see what error we get
                    response = requests.post(api_url, json=test_data, timeout=5)
                    print(f"Response status: {response.status_code}")
                    print(f"Response: {response.text}")
                except requests.exceptions.ConnectionError:
                    print("Connection error - is your Flask app running at localhost:5000?")
                    print("You need to start your AgentSDR app with: flask run")
                except Exception as e:
                    print(f"Request error: {e}")
            else:
                print("No agents found")
        else:
            print("No organizations found")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()