"""
Gmail API service for fetching and processing emails
"""
import os
import base64
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import openai
from flask import current_app


class GmailService:
    def __init__(self):
        self.client_id = os.getenv('GMAIL_CLIENT_ID')
        self.client_secret = os.getenv('GMAIL_CLIENT_SECRET')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self._service_cache = {}  # Cache Gmail service instances
    
    def get_access_token(self, refresh_token: str) -> str:
        """Get a fresh access token using refresh token"""
        try:
            current_app.logger.info("Refreshing Gmail access token")
            token_data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
            current_app.logger.info(f"Token refresh response status: {response.status_code}")
            
            if response.status_code != 200:
                current_app.logger.error(f"Token refresh failed with status {response.status_code}: {response.text}")
                raise Exception(f"Token refresh failed with status {response.status_code}")
            
            token_json = response.json()
            
            if 'error' in token_json:
                current_app.logger.error(f"Token refresh error: {token_json}")
                raise Exception(f"Token refresh failed: {token_json['error']} - {token_json.get('error_description', '')}")
            
            if 'access_token' not in token_json:
                current_app.logger.error(f"No access token in response: {token_json}")
                raise Exception("No access token received from refresh request")
            
            current_app.logger.info("Access token refreshed successfully")
            return token_json['access_token']
            
        except Exception as e:
            current_app.logger.error(f"Error refreshing access token: {e}")
            raise
    
    def build_gmail_service(self, refresh_token: str):
        """Build Gmail API service with fresh credentials"""
        try:
            current_app.logger.info("Building Gmail service")
            
            # Create credentials with refresh token - let Google API client handle token refresh
            credentials = Credentials(
                token=None,  # Let it refresh automatically
                refresh_token=refresh_token,
                client_id=self.client_id,
                client_secret=self.client_secret,
                token_uri='https://oauth2.googleapis.com/token'
            )
            
            # Refresh the token if needed
            if not credentials.valid:
                current_app.logger.info("Credentials not valid, refreshing...")
                credentials.refresh(Request())
                current_app.logger.info("Credentials refreshed successfully")
            
            service = build('gmail', 'v1', credentials=credentials)
            current_app.logger.info("Gmail service built successfully")
            return service
            
        except Exception as e:
            current_app.logger.error(f"Error building Gmail service: {e}")
            import traceback
            current_app.logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
    def get_query_for_criteria(self, criteria_type: str, count: int = 10) -> str:
        """Build Gmail search query based on criteria"""
        # Use Gmail's search operators to better match the UI semantics
        # Docs: https://support.google.com/mail/answer/7190
        criteria = (criteria_type or '').strip()
        if criteria == 'last_24_hours':
            return 'in:inbox newer_than:1d'
        if criteria == 'last_7_days':
            return 'in:inbox newer_than:7d'
        if criteria == 'latest_n':
            # Use a broader query to get more emails - include all emails, not just inbox
            return ''
        if criteria == 'oldest_n':
            # We will sort ascending later; query stays broad - include all emails
            return ''
        # Default - use broadest query - include all emails
        return ''
    
    def fetch_emails(self, refresh_token: str, criteria_type: str, count: int = 10) -> List[Dict[str, Any]]:
        """Fetch emails from Gmail based on criteria"""
        try:
            # Ensure count is an integer and safe
            try:
                count = int(count)
            except (ValueError, TypeError):
                count = 10
            if count <= 0:
                count = 10
            if count > 100:
                count = 100

            current_app.logger.info(f"Fetching emails: criteria={criteria_type}, count={count} (type: {type(count)})")
            service = self.build_gmail_service(refresh_token)
            query = self.get_query_for_criteria(criteria_type, count)
            current_app.logger.info(f"Using Gmail query: '{query}'")
            current_app.logger.info(f"Requesting maxResults: {count}")
            
            # Get message IDs with retry logic
            max_retries = 3
            retry_count = 0
            results = None
            
            while retry_count < max_retries:
                try:
                    if criteria_type == 'oldest_n':
                        # Fetch a bit more to allow sorting by oldest then slice
                        results = service.users().messages().list(
                            userId='me',
                            q=query,
                            maxResults=min(max(count * 3, count), 100)
                        ).execute()
                    else:
                        # Request more messages than needed to ensure we get enough
                        max_results = min(count * 2, 100)  # Request 2x the count, up to 100
                        current_app.logger.info(f"Requesting maxResults: {max_results} for count: {count}")
                        
                        # Use pagination to get more messages if needed
                        all_messages = []
                        page_token = None
                        
                        while len(all_messages) < count and (page_token is not None or len(all_messages) == 0):
                            request = service.users().messages().list(
                                userId='me',
                                q=query,
                                maxResults=max_results,
                                pageToken=page_token
                            )
                            results = request.execute()
                            
                            messages = results.get('messages', [])
                            all_messages.extend(messages)
                            
                            page_token = results.get('nextPageToken')
                            current_app.logger.info(f"Fetched {len(messages)} messages, total so far: {len(all_messages)}")
                            
                            if not page_token:
                                break
                        
                        # Create a results-like structure with all messages
                        results = {'messages': all_messages}
                    break
                except Exception as list_error:
                    retry_count += 1
                    if retry_count >= max_retries:
                        current_app.logger.error(f"Failed to list messages after {max_retries} retries")
                        raise list_error
                    
                    # Exponential backoff: 2^retry_count seconds
                    wait_time = 2 ** retry_count
                    current_app.logger.warning(f"Gmail API error, waiting {wait_time}s before retry {retry_count}: {list_error}")
                    import time
                    time.sleep(wait_time)
            
            messages = results.get('messages', [])
            current_app.logger.info(f"Gmail API returned {len(messages)} message IDs, requested {count}")
            current_app.logger.info(f"Total messages in results: {len(results.get('messages', []))}")
            current_app.logger.info(f"Results keys: {list(results.keys())}")
            if 'nextPageToken' in results:
                current_app.logger.info(f"More messages available (nextPageToken present)")
            else:
                current_app.logger.info(f"No more messages available")
            if len(messages) == 0:
                current_app.logger.warning(f"No messages returned from Gmail API for query: '{query}'")
            
            if not messages:
                current_app.logger.info("No messages found matching criteria")
                return []
            
            # Fetch full message details
            emails = []
            for i, message in enumerate(messages):
                try:
                    current_app.logger.info(f"Fetching message {i+1}/{len(messages)}: {message['id']}")
                    
                    # Add retry logic for individual message fetching
                    max_retries = 3
                    retry_count = 0
                    msg = None
                    
                    while retry_count < max_retries:
                        try:
                            msg = service.users().messages().get(
                                userId='me',
                                id=message['id'],
                                format='full'
                            ).execute()
                            break
                        except Exception as fetch_error:
                            retry_count += 1
                            if retry_count >= max_retries:
                                raise fetch_error
                            current_app.logger.warning(f"Retry {retry_count} for message {message['id']}: {fetch_error}")
                            import time
                            time.sleep(1)  # Wait 1 second before retry
                    
                    if msg:
                        email_data = self.parse_email(msg)
                        if email_data:
                            emails.append(email_data)
                            current_app.logger.info(f"Successfully parsed email {len(emails)}: {email_data.get('subject', 'No subject')}")
                        else:
                            current_app.logger.warning(f"Failed to parse email {message['id']}")
                    else:
                        current_app.logger.warning(f"Failed to fetch email {message['id']}")
                        
                except Exception as e:
                    current_app.logger.error(f"Error fetching message {message['id']} after retries: {e}")
                    # Don't fail completely, just skip this message
                    continue
            
            # Sort emails based on criteria
            try:
                if criteria_type == 'oldest_n':
                    emails.sort(key=lambda x: x['timestamp'])
                else:
                    emails.sort(key=lambda x: x['timestamp'], reverse=True)
            except TypeError as e:
                current_app.logger.warning(f"Sorting failed due to datetime comparison issue: {e}")
                current_app.logger.info("Proceeding without sorting - emails will be in original order")
                # Continue without sorting if there's a datetime comparison issue
            
            current_app.logger.info(f"=== FINAL SUMMARY ===")
            current_app.logger.info(f"Requested: {count} emails")
            current_app.logger.info(f"Gmail API returned: {len(messages)} message IDs")
            current_app.logger.info(f"Successfully parsed: {len(emails)} emails")
            current_app.logger.info(f"Returning: {len(emails[:count])} emails")
            current_app.logger.info(f"=== END SUMMARY ===")
            return emails[:count]
            
        except Exception as e:
            current_app.logger.error(f"Error fetching emails: {e}")
            raise
    
    def parse_email(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Gmail message into structured data"""
        try:
            current_app.logger.info(f"Parsing email {message.get('id', 'unknown')}")
            headers = message['payload'].get('headers', [])
            
            # Extract headers
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            date_str = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            current_app.logger.info(f"Email headers - From: {sender}, Subject: {subject}")
            
            # Parse date
            timestamp = datetime.now()
            try:
                from email.utils import parsedate_to_datetime
                timestamp = parsedate_to_datetime(date_str)
            except:
                pass
            
            # Extract body
            body = self.extract_body(message['payload'])
            current_app.logger.info(f"Body length: {len(body)} characters")
            
            # Clean sender name (remove email part if present)
            sender_name = sender
            if '<' in sender and '>' in sender:
                sender_name = sender.split('<')[0].strip().strip('"')
            elif '@' in sender:
                sender_name = sender.split('@')[0]
            
            email_data = {
                'id': message['id'],
                'sender': sender_name,
                'sender_email': sender,
                'subject': subject,
                'body': body,
                'timestamp': timestamp,
                'date': timestamp.strftime('%Y-%m-%d %H:%M')
            }
            
            current_app.logger.info(f"Successfully created email data for: {subject}")
            return email_data
            
        except Exception as e:
            current_app.logger.error(f"Error parsing email: {e}")
            return None
    
    def extract_body(self, payload: Dict[str, Any]) -> str:
        """Extract email body from Gmail payload"""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
                        break
                elif part['mimeType'] == 'text/html' and not body:
                    data = part['body'].get('data', '')
                    if data:
                        html_body = base64.urlsafe_b64decode(data).decode('utf-8')
                        body = self.html_to_text(html_body)
        else:
            if payload['mimeType'] == 'text/plain':
                data = payload['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
            elif payload['mimeType'] == 'text/html':
                data = payload['body'].get('data', '')
                if data:
                    html_body = base64.urlsafe_b64decode(data).decode('utf-8')
                    body = self.html_to_text(html_body)
        
        return self.clean_email_body(body)
    
    def html_to_text(self, html: str) -> str:
        """Convert HTML to plain text"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            return soup.get_text()
        except ImportError:
            # Fallback: simple regex-based HTML removal
            clean = re.compile('<.*?>')
            return re.sub(clean, '', html)
    
    def clean_email_body(self, body: str) -> str:
        """Clean email body by removing signatures, footers, etc."""
        if not body:
            return ""
        
        # Remove common signature patterns
        signature_patterns = [
            r'\n--\s*\n.*',  # Standard signature delimiter
            r'\nBest regards.*',
            r'\nSincerely.*',
            r'\nThanks.*\n.*@.*',
            r'\nSent from my.*',
            r'\n\[.*\].*',  # Email client footers
        ]
        
        cleaned = body
        for pattern in signature_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove excessive whitespace
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
        cleaned = cleaned.strip()
        
        # Limit length for summarization
        if len(cleaned) > 2000:
            cleaned = cleaned[:2000] + "..."
        
        return cleaned
    
    def summarize_with_openai(self, emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Summarize emails using OpenAI API"""
        try:
            summaries = []
            successful_count = 0
            failed_count = 0
            
            # Process each email individually to get the requested count
            current_app.logger.info(f"Processing {len(emails)} emails individually")
            
            for email in emails:
                try:
                    # Single email summary
                    summary_text = self.summarize_single_email(email)
                    
                    summaries.append({
                        'id': email['id'],
                        'sender': email['sender'],
                        'subject': email['subject'],
                        'date': email['date'],
                        'summary': summary_text,
                        'email_count': 1,
                        'status': 'success'
                    })
                    successful_count += 1
                    
                except Exception as e:
                    current_app.logger.error(f"Error summarizing email: {e}")
                    failed_count += 1
                    
                    # Add fallback summary with error info
                    summaries.append({
                        'id': email['id'],
                        'sender': email['sender'],
                        'subject': email['subject'],
                        'date': email['date'],
                        'summary': f"Email from {email['sender']} about {email['subject']}",
                        'email_count': 1,
                        'status': 'failed'
                    })
            
            current_app.logger.info(f"Summarization complete: {successful_count} successful, {failed_count} failed")
            current_app.logger.info(f"Created {len(summaries)} individual summaries from {len(emails)} emails")
            return summaries
            
        except Exception as e:
            current_app.logger.error(f"Error in OpenAI summarization: {e}")
            raise
    
    def group_emails_by_topic(self, emails: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Group emails by similar topics/senders"""
        # Simple grouping by sender and subject similarity
        groups = []
        processed = set()
        
        for i, email in enumerate(emails):
            if i in processed:
                continue
            
            group = [email]
            processed.add(i)
            
            # Look for similar emails
            for j, other_email in enumerate(emails[i+1:], i+1):
                if j in processed:
                    continue
                
                # Group by same sender or similar subject
                if (email['sender'] == other_email['sender'] or 
                    self.subjects_similar(email['subject'], other_email['subject'])):
                    group.append(other_email)
                    processed.add(j)
            
            groups.append(group)
        
        return groups
    
    def subjects_similar(self, subject1: str, subject2: str) -> bool:
        """Check if two subjects are similar (simple implementation)"""
        # Remove common prefixes
        clean1 = re.sub(r'^(re:|fwd?:)\s*', '', subject1.lower()).strip()
        clean2 = re.sub(r'^(re:|fwd?:)\s*', '', subject2.lower()).strip()
        
        return clean1 == clean2
    
    def summarize_single_email(self, email: Dict[str, Any]) -> str:
        """Summarize a single email using OpenAI"""
        try:
            current_app.logger.info(f"Summarizing single email from {email['sender']}")
            
            if not self.openai_api_key:
                current_app.logger.error("OpenAI API key not configured")
                return f"Email from {email['sender']} regarding {email['subject']}"
            
            prompt = f"""
            Please summarize this email in 1-3 concise sentences. Focus on the main purpose and any action items.

            From: {email['sender']}
            Subject: {email['subject']}

            Email content:
            {email['body']}

            Summary:
            """

            client = openai.OpenAI(api_key=self.openai_api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes emails concisely and clearly."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.3
            )

            summary = response.choices[0].message.content.strip()
            current_app.logger.info("Single email summarization completed successfully")
            return summary

        except Exception as e:
            current_app.logger.error(f"Error in single email summarization: {e}")
            return f"Email from {email['sender']} regarding {email['subject']}"
    
    def summarize_email_group(self, emails: List[Dict[str, Any]]) -> str:
        """Summarize a group of related emails"""
        try:
            email_contents = []
            for email in emails:
                email_contents.append(f"From: {email['sender']}\nSubject: {email['subject']}\nContent: {email['body'][:500]}...")

            combined_content = "\n\n---\n\n".join(email_contents)

            prompt = f"""
            Please summarize this email thread in 2-4 sentences. Focus on the main topic and key developments.

            Email thread:
            {combined_content}

            Summary:
            """

            client = openai.OpenAI(api_key=self.openai_api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes email threads concisely."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3
            )

            summary = response.choices[0].message.content.strip()
            if len(emails) > 1:
                summary += f" (Thread of {len(emails)} emails)"

            return summary

        except Exception as e:
            current_app.logger.error(f"Error in group email summarization: {e}")
            return f"Email thread with {len(emails)} messages about {emails[0]['subject']}"

    def check_openai_quota(self) -> Dict[str, Any]:
        """Check OpenAI API quota status"""
        try:
            if not self.openai_api_key:
                return {"error": "OpenAI API key not configured"}
            
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            # Try a simple request to check quota
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            
            return {
                "status": "ok",
                "message": "OpenAI API is working correctly"
            }
            
        except openai.RateLimitError:
            return {
                "error": "rate_limit_exceeded",
                "message": "OpenAI API rate limit exceeded. Please wait a moment and try again."
            }
        except openai.InsufficientQuotaError:
            return {
                "error": "insufficient_quota", 
                "message": "OpenAI API quota exceeded. Please add credits to your account."
            }
        except Exception as e:
            return {
                "error": "unknown",
                "message": f"OpenAI API error: {str(e)}"
            }


def fetch_and_summarize_emails(refresh_token: str, criteria_type: str, count: int = 10) -> List[Dict[str, Any]]:
    """Main function to fetch and summarize emails"""
    try:
        current_app.logger.info(f"Starting email fetch and summarization process")
        gmail_service = GmailService()
        
        # Validate inputs
        if not refresh_token:
            raise ValueError("Refresh token is required")
        if not criteria_type:
            raise ValueError("Criteria type is required")
        # Be tolerant to string inputs
        try:
            count = int(count)
        except (ValueError, TypeError):
            count = 10
        if count <= 0:
            count = 10
        if count > 100:
            count = 100
            
        current_app.logger.info(f"Fetching emails with criteria: {criteria_type}, count: {count}")
        
        # Fetch emails
        emails = gmail_service.fetch_emails(refresh_token, criteria_type, count)
        
        if not emails:
            current_app.logger.info("No emails found to summarize")
            return []
        
        current_app.logger.info(f"Found {len(emails)} emails, starting summarization")
        
        # Summarize emails
        summaries = gmail_service.summarize_with_openai(emails)
        
        current_app.logger.info(f"Successfully created {len(summaries)} summaries")
        return summaries
        
    except Exception as e:
        current_app.logger.error(f"Error in fetch_and_summarize_emails: {e}")
        import traceback
        current_app.logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Return empty list instead of raising error to prevent 500
        if "quota" in str(e).lower() or "insufficient" in str(e).lower():
            current_app.logger.error("OpenAI quota exceeded - returning empty summaries")
            return []
        else:
            # For other errors, still return empty list to prevent 500
            current_app.logger.error("Unknown error - returning empty summaries")
            return []
