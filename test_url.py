#!/usr/bin/env python3
"""
Test the Supabase URL for encoding issues
"""
import os
from dotenv import load_dotenv

load_dotenv()

def test_url():
    url = os.getenv('SUPABASE_URL')
    anon_key = os.getenv('SUPABASE_ANON_KEY')
    
    print(f"URL: '{url}'")
    print(f"URL length: {len(url)}")
    print(f"URL bytes: {url.encode('utf-8')}")
    print(f"Anon key length: {len(anon_key)}")
    
    # Test URL encoding
    try:
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        print(f"Parsed URL: {parsed}")
        print(f"Hostname: '{parsed.hostname}'")
        
        # Test IDNA encoding
        hostname_bytes = parsed.hostname.encode('idna')
        print(f"IDNA encoded hostname: {hostname_bytes}")
        
    except Exception as e:
        print(f"URL parsing error: {e}")
    
    # Test Supabase client creation
    try:
        from supabase import create_client
        print("Creating Supabase client...")
        client = create_client(url, anon_key)
        print("✅ Supabase client created successfully")
        
        # Test a simple operation
        print("Testing auth signup...")
        response = client.auth.sign_up({
            'email': 'urltest@example.com',
            'password': 'testpassword123'
        })
        print(f"✅ Auth signup test successful: {response.user.id if response.user else 'No user'}")
        
    except Exception as e:
        print(f"❌ Supabase client error: {e}")
        print(f"Error type: {type(e)}")

if __name__ == '__main__':
    test_url()
