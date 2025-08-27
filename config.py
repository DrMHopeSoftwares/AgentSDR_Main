import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'dev-secret-key-change-in-production'
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY')
    SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    
    # Email settings for invitations
    SMTP_HOST = os.environ.get('SMTP_HOST', 'localhost')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USER = os.environ.get('SMTP_USER')
    SMTP_PASS = os.environ.get('SMTP_PASS')
    SMTP_USE_TLS = os.environ.get('SMTP_USE_TLS', 'true').lower() == 'true'
    
    # Mailjet settings
    MAILJET_API_KEY = os.environ.get('MAILJET_API_KEY')
    MAILJET_API_SECRET = os.environ.get('MAILJET_API_SECRET')
    MAILJET_SENDER_EMAIL = os.environ.get('MAILJET_SENDER_EMAIL')
    MAILJET_SENDER_NAME = os.environ.get('MAILJET_SENDER_NAME', 'AgentSDR')
    USE_MAILJET = os.environ.get('USE_MAILJET', 'true').lower() == 'true'
    
    # Bolna API settings
    BOLNA_API_KEY = os.environ.get('BOLNA_API_KEY')
    BOLNA_API_URL = os.environ.get('BOLNA_API_URL', 'https://api.bolna.ai')
    # Optional explicit settings used by calling services
    BOLNA_AGENT_ID = os.environ.get('BOLNA_AGENT_ID')
    BOLNA_FROM_NUMBER = os.environ.get('BOLNA_FROM_NUMBER')
    # Allow overriding calls path if provider URL differs
    BOLNA_CALLS_PATH = os.environ.get('BOLNA_CALLS_PATH')
    # Optional full calls URL (takes precedence). Matches manual call route behavior
    BOLNA_FULL_CALLS_URL = os.environ.get('BOLNA_FULL_CALLS_URL')
    
    # OpenAI API settings
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_API_URL = os.environ.get('OPENAI_API_URL', 'https://api.openai.com/v1')
    
    # HubSpot API settings
    HUBSPOT_API_KEY = os.environ.get('HUBSPOT_API_KEY')
    HUBSPOT_API_URL = os.environ.get('HUBSPOT_API_URL', 'https://api.hubapi.com')
    
    # Rate limiting
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    RATELIMIT_STORAGE_URL = "memory://"
    
    # Security
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # App settings
    INVITATION_EXPIRY_HOURS = 72
    MAX_ORGS_PER_USER = 10
    MAX_MEMBERS_PER_ORG = 100

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
