from supabase import create_client, Client
from flask import current_app, session
import os
from typing import Optional, Dict, Any

class SupabaseManager:
    def __init__(self):
        self._client: Optional[Client] = None
        self._service_client: Optional[Client] = None
    
    def get_client(self) -> Client:
        """Get the Supabase client with user authentication"""
        if not self._client:
            try:
                # Create client with minimal parameters to avoid proxy issues
                self._client = create_client(
                    current_app.config['SUPABASE_URL'],
                    current_app.config['SUPABASE_ANON_KEY']
                )
            except Exception as e:
                current_app.logger.error(f"Failed to create Supabase client: {e}")
                # Try alternative approach with environment variable override
                try:
                    # Clear any problematic environment variables
                    old_http_proxy = os.environ.pop('HTTP_PROXY', None)
                    old_https_proxy = os.environ.pop('HTTPS_PROXY', None)
                    old_http_proxy = os.environ.pop('http_proxy', None)
                    old_https_proxy = os.environ.pop('https_proxy', None)
                    
                    self._client = create_client(
                        current_app.config['SUPABASE_URL'],
                        current_app.config['SUPABASE_ANON_KEY']
                    )
                    
                    # Restore environment variables
                    if old_http_proxy:
                        os.environ['HTTP_PROXY'] = old_http_proxy
                    if old_https_proxy:
                        os.environ['HTTPS_PROXY'] = old_https_proxy
                    if old_http_proxy:
                        os.environ['http_proxy'] = old_http_proxy
                    if old_https_proxy:
                        os.environ['https_proxy'] = old_https_proxy
                        
                except Exception as alt_e:
                    current_app.logger.error(f"Alternative client creation also failed: {alt_e}")
                    raise e
        
        # Set auth token if available in session
        try:
            if 'supabase_token' in session:
                self._client.auth.set_session(session['supabase_token'], session.get('supabase_refresh_token'))
        except RuntimeError:
            # No request context, skip session handling
            pass
        
        return self._client
    
    def get_service_client(self) -> Client:
        """Get the Supabase client with service role key (admin access)"""
        if not self._service_client:
            try:
                # Create service client with minimal parameters
                self._service_client = create_client(
                    current_app.config['SUPABASE_URL'],
                    current_app.config['SUPABASE_SERVICE_ROLE_KEY']
                )
            except Exception as e:
                current_app.logger.error(f"Failed to create Supabase service client: {e}")
                # Try alternative approach with environment variable override
                try:
                    # Clear any problematic environment variables
                    old_http_proxy = os.environ.pop('HTTP_PROXY', None)
                    old_https_proxy = os.environ.pop('HTTPS_PROXY', None)
                    old_http_proxy = os.environ.pop('http_proxy', None)
                    old_https_proxy = os.environ.pop('https_proxy', None)
                    
                    self._service_client = create_client(
                        current_app.config['SUPABASE_URL'],
                        current_app.config['SUPABASE_SERVICE_ROLE_KEY']
                    )
                    
                    # Restore environment variables
                    if old_http_proxy:
                        os.environ['HTTP_PROXY'] = old_http_proxy
                    if old_https_proxy:
                        os.environ['HTTPS_PROXY'] = old_https_proxy
                    if old_http_proxy:
                        os.environ['http_proxy'] = old_http_proxy
                    if old_https_proxy:
                        os.environ['https_proxy'] = old_https_proxy
                        
                except Exception as alt_e:
                    current_app.logger.error(f"Alternative service client creation also failed: {alt_e}")
                    raise e
        return self._service_client
    
    def set_session(self, access_token: str, refresh_token: str = None):
        """Set the current session tokens"""
        try:
            session['supabase_token'] = access_token
            if refresh_token:
                session['supabase_refresh_token'] = refresh_token
        except RuntimeError:
            # No request context, skip session handling
            pass
    
    def clear_session(self):
        """Clear the current session tokens"""
        try:
            session.pop('supabase_token', None)
            session.pop('supabase_refresh_token', None)
        except RuntimeError:
            # No request context, skip session handling
            pass
    
    def get_user(self):
        """Get the current authenticated user"""
        client = self.get_client()
        return client.auth.get_user()

# Global instance
supabase = SupabaseManager()

def get_supabase() -> Client:
    """Get the current Supabase client"""
    return supabase.get_client()

def get_service_supabase() -> Client:
    """Get the service role Supabase client"""
    return supabase.get_service_client()
