#!/usr/bin/env python3
"""
Start the Automated Email Summarization Scheduler

This script starts the scheduler in the background and handles logging.
"""

import os
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Start the scheduler"""
    try:
        logger.info("Starting Automated Email Summarization Scheduler...")
        
        # Check if required environment variables are set
        required_vars = [
            'SUPABASE_URL',
            'SUPABASE_SERVICE_ROLE_KEY',
            'SMTP_HOST',
            'SMTP_USER',
            'SMTP_PASS'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            logger.error("Please check your .env file")
            return 1
        
        # Import and run scheduler
        from scheduler import run_scheduler
        run_scheduler()
        
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Scheduler failed to start: {e}")
        return 1

if __name__ == '__main__':
    exit(main())
