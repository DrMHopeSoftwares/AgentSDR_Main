import requests
import json
from typing import Optional, Dict, Any, List
from flask import current_app
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class HubSpotService:
    def __init__(self):
        self.api_key = current_app.config.get('HUBSPOT_API_KEY')
        self.api_url = current_app.config.get('HUBSPOT_API_URL')
        self.summary_property = current_app.config.get('HUBSPOT_SUMMARY_PROPERTY', 'call_summary')
        
        if not self.api_key:
            raise ValueError("HUBSPOT_API_KEY not configured")
    
    def find_contact_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """
        Find HubSpot contact by phone number
        
        Args:
            phone_number: The phone number to search for
            
        Returns:
            Dict containing contact data or None if not found
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Search for contact by phone number
            url = f"{self.api_url}/crm/v3/objects/contacts/search"
            
            payload = {
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "phone",
                                "operator": "EQ",
                                "value": phone_number
                            }
                        ]
                    }
                ],
                "properties": ["id", "firstname", "lastname", "email", "phone", "company", "lifecyclestage"],
                "limit": 1
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results') and len(data['results']) > 0:
                    contact = data['results'][0]
                    logger.info(f"Found contact by phone: {contact.get('id')}")
                    return contact
                else:
                    logger.info(f"No contact found for phone number: {phone_number}")
                    return None
            else:
                logger.error(f"Failed to search contact by phone. Status: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error searching contact by phone: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error searching contact by phone: {e}")
            return None
    
    def create_contact(self, contact_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new contact in HubSpot
        
        Args:
            contact_data: Dictionary containing contact information
            
        Returns:
            Dict containing created contact data or None if failed
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            url = f"{self.api_url}/crm/v3/objects/contacts"
            
            # Prepare properties for HubSpot
            properties = {}
            for key, value in contact_data.items():
                if value is not None:
                    properties[key] = value
            
            payload = {
                "properties": properties
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 201:
                data = response.json()
                logger.info(f"Successfully created contact: {data.get('id')}")
                return data
            else:
                logger.error(f"Failed to create contact. Status: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error creating contact: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating contact: {e}")
            return None
    
    def update_contact_summary(self, contact_id: str, summary: str) -> bool:
        """
        Update contact summary in HubSpot
        
        Args:
            contact_id: HubSpot contact ID
            summary: The call summary to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            url = f"{self.api_url}/crm/v3/objects/contacts/{contact_id}"
            
            # Get existing contact to check if summary field exists
            get_response = requests.get(url, headers=headers, timeout=30)
            
            if get_response.status_code != 200:
                logger.error(f"Failed to get contact {contact_id}. Status: {get_response.status_code}")
                return False
            
            existing_contact = get_response.json()
            existing_summary = existing_contact.get('properties', {}).get(self.summary_property, '')
            
            # Append new summary to existing one
            if existing_summary:
                new_summary = f"{existing_summary}\n\n{datetime.now().strftime('%Y-%m-%d %H:%M')}: {summary}"
            else:
                new_summary = f"{datetime.now().strftime('%Y-%m-%d %H:%M')}: {summary}"
            
            # Update contact with new summary
            payload = {
                "properties": {
                    self.summary_property: new_summary
                }
            }
            
            response = requests.patch(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"Successfully updated summary for contact {contact_id}")
                return True
            else:
                logger.error(f"Failed to update contact summary. Status: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error updating contact summary: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating contact summary: {e}")
            return False
    
    def get_contact_properties(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get available contact properties from HubSpot
        
        Returns:
            List of property definitions or None if failed
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            url = f"{self.api_url}/crm/v3/properties/contacts"
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully fetched {len(data.get('results', []))} contact properties")
                return data.get('results', [])
            else:
                logger.error(f"Failed to get contact properties. Status: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error getting contact properties: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting contact properties: {e}")
            return None
    
    def create_custom_property(self, property_name: str, property_label: str, property_type: str = "string") -> bool:
        """
        Create a custom property for call summaries if it doesn't exist
        
        Args:
            property_name: Internal property name (e.g., 'call_summary')
            property_label: Display label (e.g., 'Call Summary')
            property_type: Property type (e.g., 'string', 'textarea')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            url = f"{self.api_url}/crm/v3/properties/contacts"
            
            payload = {
                "name": property_name,
                "label": property_label,
                "type": property_type,
                "groupName": "callinformation",
                "description": "Summary of call conversations with this contact"
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 201:
                logger.info(f"Successfully created custom property: {property_name}")
                return True
            elif response.status_code == 409:
                logger.info(f"Property {property_name} already exists")
                return True
            else:
                logger.error(f"Failed to create custom property. Status: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error creating custom property: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating custom property: {e}")
            return False
    
    def get_contact_checkup_date(self, contact_id: str) -> Optional[datetime]:
        """
        Get the last check-up date for a HubSpot contact
        
        Args:
            contact_id: HubSpot contact ID
            
        Returns:
            Last check-up date as datetime or None if not found
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Try different property names for check-up date
            checkup_properties = [
                'check_up_date',
                'last_checkup_date', 
                'last_check_up_date',
                'checkup_date',
                'last_visit_date',
                'last_appointment_date'
            ]
            
            url = f"{self.api_url}/crm/v3/objects/contacts/{contact_id}"
            params = {
                'properties': ','.join(checkup_properties)
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                properties = data.get('properties', {})
                
                # Find the first available check-up date property
                for prop in checkup_properties:
                    if prop in properties and properties[prop]:
                        try:
                            # Parse the date (HubSpot returns ISO format)
                            checkup_date = datetime.fromisoformat(properties[prop].replace('Z', '+00:00'))
                            logger.info(f"Found check-up date for contact {contact_id}: {checkup_date}")
                            return checkup_date
                        except ValueError:
                            logger.warning(f"Invalid date format for {prop}: {properties[prop]}")
                            continue
                
                logger.info(f"No check-up date found for contact {contact_id}")
                return None
            else:
                logger.error(f"Failed to get contact {contact_id}. Status: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error getting contact check-up date: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting contact check-up date: {e}")
            return None
    
    def update_contact_checkup_date(self, contact_id: str, checkup_date: datetime) -> bool:
        """
        Update the check-up date for a HubSpot contact
        
        Args:
            contact_id: HubSpot contact ID
            checkup_date: New check-up date
            
        Returns:
            True if successful, False otherwise
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            url = f"{self.api_url}/crm/v3/objects/contacts/{contact_id}"
            
            # Try to update the primary check-up date property
            payload = {
                "properties": {
                    "check_up_date": checkup_date.isoformat()
                }
            }
            
            response = requests.patch(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"Updated check-up date for contact {contact_id} to {checkup_date}")
                return True
            else:
                logger.error(f"Failed to update check-up date for contact {contact_id}. Status: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error updating contact check-up date: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating contact check-up date: {e}")
            return False
    
    def get_contacts_needing_followup(self, days_threshold: int = 5) -> List[Dict[str, Any]]:
        """
        Get contacts that need follow-up based on check-up date threshold
        
        Args:
            days_threshold: Number of days after last check-up to trigger follow-up
            
        Returns:
            List of contacts needing follow-up
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Get all contacts with check-up date properties
            url = f"{self.api_url}/crm/v3/objects/contacts"
            params = {
                'properties': 'id,firstname,lastname,email,phone,check_up_date,last_checkup_date',
                'limit': 100  # Adjust based on your needs
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Failed to get contacts. Status: {response.status_code}")
                return []
            
            data = response.json()
            contacts_needing_followup = []
            threshold_date = datetime.now().date()
            
            for contact in data.get('results', []):
                properties = contact.get('properties', {})
                
                # Check for check-up date
                checkup_date_str = properties.get('check_up_date') or properties.get('last_checkup_date')
                
                if checkup_date_str:
                    try:
                        checkup_date = datetime.fromisoformat(checkup_date_str.replace('Z', '+00:00')).date()
                        days_since_checkup = (threshold_date - checkup_date).days
                        
                        if days_since_checkup >= days_threshold:
                            contacts_needing_followup.append({
                                'id': contact['id'],
                                'firstname': properties.get('firstname', ''),
                                'lastname': properties.get('lastname', ''),
                                'email': properties.get('email', ''),
                                'phone': properties.get('phone', ''),
                                'last_checkup_date': checkup_date_str,
                                'days_since_checkup': days_since_checkup
                            })
                    except ValueError:
                        logger.warning(f"Invalid date format for contact {contact['id']}: {checkup_date_str}")
                        continue
            
            logger.info(f"Found {len(contacts_needing_followup)} contacts needing follow-up")
            return contacts_needing_followup
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error getting contacts needing follow-up: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting contacts needing follow-up: {e}")
            return []
