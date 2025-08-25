#!/usr/bin/env python3
"""
Simple test to start the Flask application
"""
import os
import sys

# Ensure we're in the right directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variable to avoid conflicts
os.environ['FLASK_ENV'] = 'development'

try:
    print("Starting Flask application...")

    # Import Flask components directly
    from flask import Flask
    from flask_login import LoginManager
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    from flask_wtf.csrf import CSRFProtect
    from config import config

    print("Basic imports successful...")

    # Try to import the create_app function
    from agentsdr import create_app

    print("create_app imported successfully...")

    app = create_app()
    print("Flask app created successfully!")

    print("Starting server on http://localhost:5000")
    print("Visit http://localhost:5000 to access the application")
    app.run(debug=True, host='0.0.0.0', port=5000)

except Exception as e:
    print(f"Error starting Flask app: {e}")
    import traceback
    traceback.print_exc()
