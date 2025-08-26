import requests
import json
from typing import Optional, Dict, Any
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.api_key = current_app.config.get('OPENAI_API_KEY')
        self.api_url = current_app.config.get('OPENAI_API_URL')
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not configured")
    
    def summarize_transcript(self, transcript_text: str, max_words: int = 20) -> Optional[Dict[str, Any]]:
        """
        Summarize call transcript using OpenAI API
        
        Args:
            transcript_text: The full transcript text to summarize
            max_words: Maximum number of words for the summary
            
        Returns:
            Dict containing summary data or None if failed
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Create a prompt for summarization
            prompt = f"""Please summarize the following call transcript in exactly {max_words} words or less. 
            Focus on the key points, action items, and main outcome of the conversation.
            
            Transcript:
            {transcript_text}
            
            Summary ({max_words} words max):"""
            
            payload = {
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {
                        'role': 'system',
                        'content': f'You are a helpful assistant that summarizes call transcripts in exactly {max_words} words or less. Be concise and focus on key points.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': 100,
                'temperature': 0.3
            }
            
            # Endpoint for chat completions
            url = f"{self.api_url}/chat/completions"
            
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                summary = data['choices'][0]['message']['content'].strip()
                usage = data.get('usage', {})
                
                result = {
                    'summary': summary,
                    'word_count': len(summary.split()),
                    'model_used': data['model'],
                    'tokens_used': usage.get('total_tokens', 0),
                    'prompt_tokens': usage.get('prompt_tokens', 0),
                    'completion_tokens': usage.get('completion_tokens', 0)
                }
                
                logger.info(f"Successfully summarized transcript. Word count: {result['word_count']}")
                return result
            else:
                logger.error(f"Failed to summarize transcript. Status: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error summarizing transcript: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error summarizing transcript: {e}")
            return None
    
    def analyze_sentiment(self, transcript_text: str) -> Optional[Dict[str, Any]]:
        """
        Analyze sentiment of call transcript using OpenAI API
        
        Args:
            transcript_text: The transcript text to analyze
            
        Returns:
            Dict containing sentiment analysis or None if failed
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            prompt = f"""Analyze the sentiment of this call transcript and provide:
            1. Overall sentiment (positive, negative, neutral)
            2. Confidence score (0-100%)
            3. Key emotional indicators
            4. Brief explanation
            
            Transcript:
            {transcript_text}"""
            
            payload = {
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {
                        'role': 'system',
                        'content': 'You are a helpful assistant that analyzes call sentiment. Provide structured analysis in JSON format.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': 200,
                'temperature': 0.1
            }
            
            url = f"{self.api_url}/chat/completions"
            
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content'].strip()
                
                # Try to parse JSON response
                try:
                    sentiment_data = json.loads(content)
                    sentiment_data['model_used'] = data['model']
                    sentiment_data['tokens_used'] = data.get('usage', {}).get('total_tokens', 0)
                    
                    logger.info(f"Successfully analyzed sentiment: {sentiment_data.get('sentiment', 'unknown')}")
                    return sentiment_data
                except json.JSONDecodeError:
                    # Fallback to text parsing
                    logger.warning("Failed to parse JSON response, returning raw content")
                    return {
                        'raw_analysis': content,
                        'model_used': data['model'],
                        'tokens_used': data.get('usage', {}).get('total_tokens', 0)
                    }
            else:
                logger.error(f"Failed to analyze sentiment. Status: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error analyzing sentiment: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error analyzing sentiment: {e}")
            return None
