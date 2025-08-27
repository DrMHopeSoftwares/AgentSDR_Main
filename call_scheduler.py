#!/usr/bin/env python3
"""
Automated Call Scheduler for AgentSDR
This script runs periodically to check for overdue calls and trigger them automatically
"""

import os
import sys
import time
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('call_scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_call_scheduler():
    """Main function to run the call scheduler"""
    logger.info("🚀 Call Scheduler started")
    
    try:
        from agentsdr import create_app
        from agentsdr.core.supabase_client import get_service_supabase
        from agentsdr.services.call_scheduling_service import CallSchedulingService
        
        # Create Flask app context
        app = create_app()
        
        with app.app_context():
            supabase = get_service_supabase()
            scheduling_service = CallSchedulingService()
            
            # Get all organizations
            orgs_response = supabase.table('organizations').select('id, name, slug').execute()
            
            if not orgs_response.data:
                logger.info("No organizations found")
                return
            
            total_triggered = 0
            
            for org in orgs_response.data:
                org_id = org['id']
                org_name = org['name']
                
                logger.info(f"Checking organization: {org_name} ({org_id})")
                
                try:
                    # Check and trigger overdue calls for this organization
                    triggered_calls = scheduling_service.check_and_trigger_overdue_calls(org_id)
                    
                    if triggered_calls:
                        logger.info(f"Triggered {len(triggered_calls)} overdue calls for {org_name}")
                        total_triggered += len(triggered_calls)
                        
                        for call in triggered_calls:
                            logger.info(f"  - {call['contact_name']} ({call['contact_phone']}): {call['trigger_reason']}")
                    else:
                        logger.info(f"No overdue calls found for {org_name}")
                        
                except Exception as e:
                    logger.error(f"Error processing organization {org_name}: {e}")
                    continue
            
            logger.info(f"Call scheduler completed. Total calls triggered: {total_triggered}")
            
    except Exception as e:
        logger.error(f"Fatal error in call scheduler: {e}")
        import traceback
        traceback.print_exc()

def run_scheduler_loop():
    """Run the scheduler in a continuous loop"""
    logger.info("🔄 Starting call scheduler loop")
    
    while True:
        try:
            run_call_scheduler()
            
            # Wait for 1 hour before next check
            logger.info("⏰ Waiting 1 hour before next check...")
            time.sleep(3600)  # 1 hour = 3600 seconds
            
        except KeyboardInterrupt:
            logger.info("🛑 Call scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}")
            # Wait 15 minutes before retrying on error
            logger.info("⏰ Waiting 15 minutes before retry...")
            time.sleep(900)  # 15 minutes = 900 seconds

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Run once and exit
        run_call_scheduler()
    else:
        # Run in continuous loop
        run_scheduler_loop()
