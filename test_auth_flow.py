#!/usr/bin/env python3
"""
Test the complete authentication flow
"""
import requests
import json
from bs4 import BeautifulSoup

def test_signup_flow():
    """Test the complete signup flow"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing AgentSDR Authentication Flow")
    print("=" * 50)
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    try:
        # Step 1: Get the signup page
        print("📄 Step 1: Getting signup page...")
        signup_url = f"{base_url}/auth/signup"
        response = session.get(signup_url)
        
        if response.status_code != 200:
            print(f"❌ Failed to get signup page. Status: {response.status_code}")
            return
        
        print(f"✅ Signup page loaded successfully (Status: {response.status_code})")
        
        # Step 2: Parse the form to get CSRF token
        print("🔍 Step 2: Parsing form for CSRF token...")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the form
        form = soup.find('form')
        if not form:
            print("❌ No form found on signup page")
            return
        
        # Find CSRF token
        csrf_token = None
        csrf_input = soup.find('input', {'name': 'csrf_token'})
        if csrf_input:
            csrf_token = csrf_input.get('value')
            print(f"✅ CSRF token found: {csrf_token[:20]}...")
        else:
            print("⚠️  No CSRF token found")
        
        # Step 3: Submit signup form
        print("📝 Step 3: Submitting signup form...")
        
        # Use a unique email to avoid conflicts
        import time
        unique_email = f'testuser{int(time.time())}@example.com'

        signup_data = {
            'email': unique_email,
            'display_name': 'Test User',
            'password': 'testpassword123',
            'confirm_password': 'testpassword123',
            'submit': 'Sign Up'
        }
        
        if csrf_token:
            signup_data['csrf_token'] = csrf_token
        
        print(f"   Email: {signup_data['email']}")
        print(f"   Display Name: {signup_data['display_name']}")
        print(f"   Password: {'*' * len(signup_data['password'])}")
        
        # Submit the form
        response = session.post(signup_url, data=signup_data, allow_redirects=False)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 302:
            # Redirect - check where
            location = response.headers.get('Location', 'Unknown')
            print(f"🔄 Redirected to: {location}")
            
            if 'dashboard' in location:
                print("✅ Signup successful! Redirected to dashboard")
            elif 'login' in location:
                print("ℹ️  Redirected to login page")
            else:
                print(f"⚠️  Unexpected redirect: {location}")
                
        elif response.status_code == 200:
            # Same page - check for errors
            print("📄 Stayed on same page - checking for errors...")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for error messages
            error_elements = soup.find_all(class_=['alert-danger', 'error', 'text-red'])
            if error_elements:
                print("❌ Error messages found:")
                for error in error_elements:
                    print(f"   - {error.get_text().strip()}")
            else:
                print("⚠️  No obvious error messages found")
                
            # Check if form validation failed
            form_errors = soup.find_all('p', class_='text-red')
            if form_errors:
                print("📝 Form validation errors:")
                for error in form_errors:
                    print(f"   - {error.get_text().strip()}")

            # Look for any error text in the response
            if 'error' in response.text.lower() or 'invalid' in response.text.lower():
                print("⚠️  Found error-related text in response")

            # Check if we can find the form again (means we stayed on signup page)
            new_form = soup.find('form')
            if new_form:
                print("📝 Form still present - signup did not succeed")

                # Check for any flash messages
                flash_messages = soup.find_all(class_=['alert', 'flash', 'message'])
                if flash_messages:
                    print("💬 Flash messages found:")
                    for msg in flash_messages:
                        print(f"   - {msg.get_text().strip()}")

            # Save response for debugging
            with open('debug_signup_response.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("💾 Saved response to debug_signup_response.html for inspection")
        
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response text: {response.text[:500]}...")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask app. Make sure it's running on http://localhost:5000")
    except Exception as e:
        print(f"❌ Error during test: {e}")

def test_login_flow():
    """Test the login flow"""
    base_url = "http://localhost:5000"
    
    print("\n🔐 Testing Login Flow")
    print("=" * 30)
    
    session = requests.Session()
    
    try:
        # Get login page
        login_url = f"{base_url}/auth/login"
        response = session.get(login_url)
        
        if response.status_code != 200:
            print(f"❌ Failed to get login page. Status: {response.status_code}")
            return
        
        print(f"✅ Login page loaded successfully")
        
        # Parse for CSRF token
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = None
        csrf_input = soup.find('input', {'name': 'csrf_token'})
        if csrf_input:
            csrf_token = csrf_input.get('value')
        
        # Try login with test credentials
        login_data = {
            'email': 'testuser@example.com',
            'password': 'testpassword123',
            'submit': 'Sign In'
        }
        
        if csrf_token:
            login_data['csrf_token'] = csrf_token
        
        response = session.post(login_url, data=login_data, allow_redirects=False)
        
        print(f"📊 Login Response Status: {response.status_code}")
        
        if response.status_code == 302:
            location = response.headers.get('Location', 'Unknown')
            print(f"🔄 Redirected to: {location}")
            
            if 'dashboard' in location:
                print("✅ Login successful!")
            else:
                print(f"⚠️  Unexpected redirect: {location}")
        else:
            print("❌ Login failed or stayed on same page")
            
    except Exception as e:
        print(f"❌ Error during login test: {e}")

if __name__ == '__main__':
    test_signup_flow()
    test_login_flow()
