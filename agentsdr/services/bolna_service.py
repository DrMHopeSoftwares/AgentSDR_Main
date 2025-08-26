import requests
import json
from typing import Optional, Dict, Any
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class BolnaService:
    def __init__(self):
        self.api_key = current_app.config.get('BOLNA_API_KEY')
        self.api_url = current_app.config.get('BOLNA_API_URL')
        
        if not self.api_key:
            raise ValueError("BOLNA_API_KEY not configured")
    
    def get_call_transcript(self, call_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch call transcript from Bolna API
        
        Args:
            call_id: The unique identifier for the call
            
        Returns:
            Dict containing transcript data or None if failed
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Endpoint to get call transcript
            url = f"{self.api_url}/calls/{call_id}/transcript"
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully fetched transcript for call {call_id}")
                return data
            else:
                logger.error(f"Failed to fetch transcript for call {call_id}. Status: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching transcript for call {call_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching transcript for call {call_id}: {e}")
            return None
    
    def get_call_details(self, call_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch call details including metadata from Bolna API
        
        Args:
            call_id: The unique identifier for the call
            
        Returns:
            Dict containing call details or None if failed
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Endpoint to get call details
            url = f"{self.api_url}/calls/{call_id}"
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully fetched details for call {call_id}")
                return data
            else:
                logger.error(f"Failed to fetch details for call {call_id}. Status: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching details for call {call_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching details for call {call_id}: {e}")
            return None
    
    def list_calls(self, limit: int = 100, offset: int = 0) -> Optional[Dict[str, Any]]:
        """
        List recent calls from Bolna API
        
        Args:
            limit: Maximum number of calls to return
            offset: Number of calls to skip
            
        Returns:
            Dict containing list of calls or None if failed
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            params = {
                'limit': limit,
                'offset': offset
            }
            
            # Endpoint to list calls
            url = f"{self.api_url}/calls"
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully fetched {len(data.get('calls', []))} calls")
                return data
            else:
                logger.error(f"Failed to list calls. Status: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error listing calls: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error listing calls: {e}")
            return None
