#!/usr/bin/env python3
"""
Direct test of the Flask app to see debug output
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Import Flask app
from agentsdr import create_app

def test_signup_directly():
    """Test signup directly with Flask test client"""
    app = create_app()
    
    with app.test_client() as client:
        with app.app_context():
            print("🧪 Testing signup with Flask test client")
            
            # Get the signup page first
            response = client.get('/auth/signup')
            print(f"GET /auth/signup: {response.status_code}")
            
            # Extract CSRF token
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.data, 'html.parser')
            csrf_input = soup.find('input', {'name': 'csrf_token'})
            csrf_token = csrf_input.get('value') if csrf_input else None
            
            print(f"CSRF token: {csrf_token[:20]}..." if csrf_token else "No CSRF token")
            
            # Test signup with unique email
            import time
            unique_email = f'newuser{int(time.time())}@example.com'

            signup_data = {
                'email': unique_email,
                'display_name': 'New Test User',
                'password': 'testpassword123',
                'confirm_password': 'testpassword123',
                'submit': 'Sign Up'
            }
            
            if csrf_token:
                signup_data['csrf_token'] = csrf_token
            
            print(f"Submitting signup for: {signup_data['email']}")
            
            # Submit signup
            response = client.post('/auth/signup', data=signup_data, follow_redirects=False)
            
            print(f"POST /auth/signup: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 302:
                print(f"Redirected to: {response.headers.get('Location')}")
                print("✅ Signup appears successful!")
            else:
                print("❌ Signup failed or stayed on same page")
                
                # Check for flash messages
                with client.session_transaction() as sess:
                    flashes = sess.get('_flashes', [])
                    if flashes:
                        print("Flash messages:")
                        for category, message in flashes:
                            print(f"  {category}: {message}")

if __name__ == '__main__':
    test_signup_directly()
