import pytest
from flask import url_for
from agentsdr import create_app
from agentsdr.auth.models import User

@pytest.fixture
def app():
    app = create_app('testing')
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

def test_login_page(client):
    """Test that login page loads correctly"""
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b'Sign in to your account' in response.data

def test_signup_page(client):
    """Test that signup page loads correctly"""
    response = client.get('/auth/signup')
    assert response.status_code == 200
    assert b'Create your account' in response.data

def test_landing_page(client):
    """Test that landing page loads correctly"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'AgentSDR' in response.data

def test_dashboard_requires_auth(client):
    """Test that dashboard requires authentication"""
    response = client.get('/dashboard', follow_redirects=True)
    assert response.status_code == 200
    # Should redirect to login
    assert b'Sign in to your account' in response.data

def test_logout_redirects_to_landing(client):
    """Test that logout redirects to landing page"""
    response = client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'AgentSDR' in response.data
