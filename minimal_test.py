#!/usr/bin/env python3
"""
Minimal Flask app to test basic functionality
"""
from flask import Flask, render_template_string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-secret-key'

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>AgentSDR Test</title>
    </head>
    <body>
        <h1>AgentSDR Test Server</h1>
        <p>If you can see this, Flask is working!</p>
        <p><a href="/test-auth">Test Authentication Pages</a></p>
    </body>
    </html>
    ''')

@app.route('/test-auth')
def test_auth():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Auth Test</title>
    </head>
    <body>
        <h1>Authentication Test</h1>
        <p>This would be where login/signup forms appear.</p>
        <p><a href="/">Back to Home</a></p>
    </body>
    </html>
    ''')

if __name__ == '__main__':
    print("Starting minimal Flask test server...")
    print("Visit http://localhost:5000 to test")
    app.run(debug=True, host='0.0.0.0', port=5000)
