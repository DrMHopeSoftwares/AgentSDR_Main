#!/usr/bin/env python3
"""
Simple script to process a call transcript manually
"""

import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def process_call_transcript():
    """Process a call transcript manually"""
    print("🚀 Call Transcript Processing Tool")
    print("=" * 50)
    
    # Get user input
    org_slug = input("Enter organization slug (e.g., nh3): ").strip()
    call_id = input("Enter Bolna Call ID: ").strip()
    agent_id = input("Enter Agent ID: ").strip()
    
    if not all([org_slug, call_id, agent_id]):
        print("❌ All fields are required!")
        return
    
    try:
        # Create Flask app context
        from agentsdr import create_app
        app = create_app('development')
        
        with app.app_context():
            from agentsdr.services.call_transcript_service import CallTranscriptService
            
            print(f"\n🔄 Processing call transcript for call {call_id}...")
            
            # Initialize service
            call_service = CallTranscriptService()
            
            # Process the transcript
            result = call_service.process_call_transcript(
                call_id=call_id,
                org_id=agent_id,  # This should be org_id, not agent_id
                agent_id=agent_id
            )
            
            if result['success']:
                print("✅ Call transcript processed successfully!")
                print(f"📝 Summary: {result['summary']}")
                print(f"🔗 HubSpot sync: {'✅ Success' if result['hubspot_success'] else '❌ Failed'}")
                print(f"🆔 Call Record ID: {result['call_record_id']}")
                print(f"📄 Transcript ID: {result['transcript_id']}")
                print(f"📋 Summary ID: {result['summary_id']}")
                
                if result.get('hubspot_contact_id'):
                    print(f"👤 HubSpot Contact ID: {result['hubspot_contact_id']}")
            else:
                print(f"❌ Failed to process transcript: {result.get('error', 'Unknown error')}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    process_call_transcript()
