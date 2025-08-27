import os
from flask import Flask
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from config import config

# Initialize extensions
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address)
csrf = CSRFProtect()

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    # Make config name lowercase to handle Railway's capitalized env vars
    config_name = config_name.lower()
    
    # Fallback to default if config_name not found
    if config_name not in config:
        print(f"Warning: Config '{config_name}' not found, using 'development'")
        config_name = 'development'
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    login_manager.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Register blueprints
    from agentsdr.auth import auth_bp
    from agentsdr.orgs import orgs_bp
    from agentsdr.records import records_bp
    from agentsdr.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(orgs_bp, url_prefix='/orgs')
    app.register_blueprint(records_bp, url_prefix='/records')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Register main routes
    from agentsdr.main import main_bp
    app.register_blueprint(main_bp)
    
    # Register scheduler webhook for external cron services
    try:
        from agentsdr.orgs.scheduler_webhook import scheduler_webhook_bp
        app.register_blueprint(scheduler_webhook_bp, url_prefix='/api')
    except Exception as e:
        app.logger.warning(f"Could not register scheduler webhook: {e}")

    # Register call routes
    try:
        from agentsdr.orgs.call_routes import call_bp, bolna_bp
        app.register_blueprint(call_bp)
        app.register_blueprint(bolna_bp)
    except Exception as e:
        # Log the error but don't fail the app startup
        print(f"Warning: Could not register call routes: {e}")

    # Exempt JSON API routes from CSRF where appropriate
    try:
        from agentsdr.orgs.routes import summarize_emails
        from agentsdr.orgs.routes import test_hubspot_connection, hubspot_call_contact
        from agentsdr.orgs.routes import manage_schedule, toggle_schedule
        csrf.exempt(summarize_emails)
        csrf.exempt(test_hubspot_connection)
        csrf.exempt(hubspot_call_contact)
        csrf.exempt(manage_schedule)
        csrf.exempt(toggle_schedule)
        
        # Exempt scheduler webhook from CSRF
        from agentsdr.orgs.scheduler_webhook import trigger_schedules
        csrf.exempt(trigger_schedules)
    except Exception:
        # If import fails during certain tooling or tests, skip exemption
        pass

    # User loader for Flask-Login
    from agentsdr.auth.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(user_id)
    
    # Initialize and start the email scheduler service
    try:
        from agentsdr.services.scheduler_service import scheduler_service
        scheduler_service.init_app(app)
        
        # Only start scheduler in production or when explicitly enabled
        if config_name == 'production' or os.environ.get('ENABLE_SCHEDULER', 'false').lower() == 'true':
            scheduler_service.start()
            app.logger.info("🚀 Email Scheduler Service started for Railway deployment")
    except Exception as e:
        app.logger.error(f"Failed to start scheduler service: {e}")

    return app
