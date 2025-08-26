#!/usr/bin/env python3
"""
Test script for call transcript functionality
"""

import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def test_services():
    """Test the call transcript services"""
    print("Testing Call Transcript Services...")
    
    try:
        # Create a Flask app context for testing services
        from agentsdr import create_app
        app = create_app('development')
        
        with app.app_context():
            # Test Bolna Service
            print("\n1. Testing Bolna Service...")
            from agentsdr.services.bolna_service import BolnaService
            
            try:
                bolna_service = BolnaService()
                print("✓ Bolna Service initialized successfully")
            except ValueError as e:
                print(f"⚠ Bolna Service: {e} (expected if API key not configured)")
            
            # Test OpenAI Service
            print("\n2. Testing OpenAI Service...")
            from agentsdr.services.openai_service import OpenAIService
            
            try:
                openai_service = OpenAIService()
                print("✓ OpenAI Service initialized successfully")
            except ValueError as e:
                print(f"⚠ OpenAI Service: {e} (expected if API key not configured)")
            
            # Test HubSpot Service
            print("\n3. Testing HubSpot Service...")
            from agentsdr.services.hubspot_service import HubSpotService
            
            try:
                hubspot_service = HubSpotService()
                print("✓ HubSpot Service initialized successfully")
            except ValueError as e:
                print(f"⚠ HubSpot Service: {e} (expected if API key not configured)")
            
            # Test Call Transcript Service
            print("\n4. Testing Call Transcript Service...")
            from agentsdr.services.call_transcript_service import CallTranscriptService
            
            try:
                call_service = CallTranscriptService()
                print("✓ Call Transcript Service initialized successfully")
            except Exception as e:
                print(f"✗ Call Transcript Service failed: {e}")
        
        print("\n✅ All service tests completed!")
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Make sure all required packages are installed")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")

def test_models():
    """Test the Pydantic models"""
    print("\nTesting Pydantic Models...")
    
    try:
        from agentsdr.core.models import (
            CallTranscript, CallSummary, CallRecord,
            CreateCallRecordRequest, UpdateCallTranscriptRequest, CreateCallSummaryRequest
        )
        
        # Test CallRecord model
        call_record_data = {
            'id': '123e4567-e89b-12d3-a456-426614174000',
            'org_id': '123e4567-e89b-12d3-a456-426614174001',
            'call_id': 'bolna_call_123',
            'agent_id': '123e4567-e89b-12d3-a456-426614174002',
            'contact_phone': '+1234567890',
            'contact_name': 'John Doe',
            'call_duration': 300,
            'call_status': 'completed',
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z'
        }
        
        call_record = CallRecord(**call_record_data)
        print("✓ CallRecord model works correctly")
        
        # Test CreateCallRecordRequest model
        create_request_data = {
            'call_id': 'bolna_call_123',
            'agent_id': '123e4567-e89b-12d3-a456-426614174002',
            'contact_phone': '+1234567890',
            'contact_name': 'John Doe',
            'call_duration': 300,
            'call_status': 'completed'
        }
        
        create_request = CreateCallRecordRequest(**create_request_data)
        print("✓ CreateCallRecordRequest model works correctly")
        
        print("✅ All model tests completed!")
        
    except Exception as e:
        print(f"✗ Model test failed: {e}")

def test_config():
    """Test configuration loading"""
    print("\nTesting Configuration...")
    
    try:
        from config import config
        from config import Config
        
        # Check if new config variables are available
        config_vars = [
            'BOLNA_API_KEY',
            'BOLNA_API_URL', 
            'OPENAI_API_KEY',
            'OPENAI_API_URL',
            'HUBSPOT_API_KEY',
            'HUBSPOT_API_URL'
        ]
        
        for var in config_vars:
            if hasattr(Config, var):
                print(f"✓ {var} configuration available")
            else:
                print(f"✗ {var} configuration missing")
        
        print("✅ Configuration test completed!")
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")

def main():
    """Main test function"""
    print("🚀 Starting Call Transcript Integration Tests\n")
    
    test_config()
    test_models()
    test_services()
    
    print("\n🎉 All tests completed!")
    print("\nNext steps:")
    print("1. Set up your environment variables:")
    print("   - BOLNA_API_KEY")
    print("   - OPENAI_API_KEY") 
    print("   - HUBSPOT_API_KEY")
    print("2. Run the database migration: supabase/call_tables.sql")
    print("3. Test the API endpoints")
    print("4. Use the web interface at /<org_slug>/calls")

if __name__ == "__main__":
    main()
