import os
import re
import time
import json
import gzip
import brotli
import base64
import hashlib
import random
import string
import requests
import threading
from flask import Flask, render_template_string, request, make_response, session as flask_session, g
from flask_cors import CORS
from urllib.parse import urlparse, urljoin, quote, unquote, parse_qs
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from collections import defaultdict
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app, supports_credentials=True)

# Target configuration
TARGET_URL = "https://kimstress.st/login"
TARGET_DOMAIN = "kimstress.st"
BASE_URL = f"https://{TARGET_DOMAIN}"

# User agents pool
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:109.0) Gecko/20100101 Firefox/121.0'
]

# Session with retry strategy
def create_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        read=3,
        connect=3,
        backoff_factor=0.3,
        status_forcelist=(500, 502, 504)
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# Session storage
session_storage = defaultdict(dict)
app_start_time = datetime.now()

# Cloudflare cookies storage
cf_cookies = {}

# HTML Template with Cloudflare handling
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kimstress • Secure Gateway</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .container {
            width: 95%;
            max-width: 1200px;
            height: 95vh;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        
        .browser-header {
            background: #1a1a1a;
            padding: 10px 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .window-dots {
            display: flex;
            gap: 8px;
        }
        
        .dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }
        
        .red { background: #ff5f56; }
        .yellow { background: #ffbd2e; }
        .green { background: #27c93f; }
        
        .address-bar {
            flex: 1;
            background: #333;
            padding: 8px 15px;
            border-radius: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
            color: white;
        }
        
        .lock-icon {
            color: #4caf50;
        }
        
        .url {
            flex: 1;
            font-size: 14px;
        }
        
        .content {
            flex: 1;
            position: relative;
            background: white;
        }
        
        #main-frame {
            width: 100%;
            height: 100%;
            border: none;
            background: white;
        }
        
        .loading {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(255,255,255,0.95);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 1000;
            transition: opacity 0.3s;
        }
        
        .loading.hidden {
            opacity: 0;
            pointer-events: none;
        }
        
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .loading-text {
            color: #333;
            font-size: 16px;
            margin-bottom: 10px;
        }
        
        .loading-subtext {
            color: #666;
            font-size: 14px;
        }
        
        .error {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            text-align: center;
            min-width: 300px;
            display: none;
            z-index: 1001;
        }
        
        .error.show {
            display: block;
        }
        
        .error-icon {
            font-size: 48px;
            margin-bottom: 15px;
        }
        
        .error-title {
            font-size: 20px;
            font-weight: 600;
            color: #e74c3c;
            margin-bottom: 10px;
        }
        
        .error-message {
            color: #666;
            margin-bottom: 20px;
        }
        
        .error-btn {
            background: #3498db;
            color: white;
            border: none;
            padding: 10px 30px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }
        
        .error-btn:hover {
            background: #2980b9;
        }
        
        .cf-challenge {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
            max-width: 500px;
            width: 90%;
            display: none;
            z-index: 2000;
        }
        
        .cf-challenge.show {
            display: block;
        }
        
        .cf-logo {
            font-size: 60px;
            margin-bottom: 20px;
        }
        
        .cf-title {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 10px;
            color: #333;
        }
        
        .cf-text {
            color: #666;
            margin-bottom: 30px;
            line-height: 1.6;
        }
        
        .cf-checkbox {
            width: 30px;
            height: 30px;
            border: 2px solid #ddd;
            border-radius: 5px;
            margin: 0 auto 20px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .cf-checkbox.checked {
            background: #4caf50;
            border-color: #4caf50;
            position: relative;
        }
        
        .cf-checkbox.checked::after {
            content: '✓';
            color: white;
            font-size: 20px;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }
        
        .cf-footer {
            font-size: 12px;
            color: #999;
            margin-top: 20px;
        }
        
        .status-bar {
            background: #1a1a1a;
            padding: 5px 15px;
            color: #aaa;
            font-size: 12px;
            display: flex;
            justify-content: space-between;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="browser-header">
            <div class="window-dots">
                <div class="dot red"></div>
                <div class="dot yellow"></div>
                <div class="dot green"></div>
            </div>
            <div class="address-bar">
                <span class="lock-icon">🔒</span>
                <span class="url" id="urlDisplay">kimstress.st/login</span>
            </div>
        </div>
        
        <div class="content">
            <!-- Loading -->
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <div class="loading-text">Loading secure content...</div>
                <div class="loading-subtext" id="loadingStatus">Connecting to server</div>
            </div>
            
            <!-- Error -->
            <div class="error" id="error">
                <div class="error-icon">⚠️</div>
                <div class="error-title">Connection Error</div>
                <div class="error-message" id="errorMessage">Failed to load website</div>
                <button class="error-btn" onclick="retry()">Try Again</button>
            </div>
            
            <!-- Cloudflare Challenge -->
            <div class="cf-challenge" id="cfChallenge">
                <div class="cf-logo">🛡️</div>
                <div class="cf-title">Verify you are human</div>
                <div class="cf-text">Complete the security check to access kimstress.st</div>
                <div class="cf-checkbox" id="cfCheckbox" onclick="verifyHuman()"></div>
                <div class="cf-text" style="font-size: 14px;">Click to verify</div>
                <div class="cf-footer">Protected by Cloudflare</div>
            </div>
            
            <!-- Iframe -->
            <iframe 
                id="main-frame"
                src="/proxy/{{ encoded_url }}"
                sandbox="allow-same-origin allow-scripts allow-popups allow-forms allow-modals allow-top-navigation allow-downloads"
                referrerpolicy="no-referrer"
                style="width: 100%; height: 100%;">
            </iframe>
        </div>
        
        <div class="status-bar">
            <span id="statusText">Secure Connection</span>
            <span id="timestamp">{{ timestamp }}</span>
        </div>
    </div>

    <script>
        const iframe = document.getElementById('main-frame');
        const loading = document.getElementById('loading');
        const error = document.getElementById('error');
        const cfChallenge = document.getElementById('cfChallenge');
        const cfCheckbox = document.getElementById('cfCheckbox');
        const statusText = document.getElementById('statusText');
        const loadingStatus = document.getElementById('loadingStatus');
        const urlDisplay = document.getElementById('urlDisplay');
        
        let retryCount = 0;
        const maxRetries = 3;
        let verified = false;
        
        // Anti-detection
        Object.defineProperties(navigator, {
            webdriver: { get: () => undefined },
            plugins: { get: () => [1, 2, 3, 4, 5] },
            languages: { get: () => ['en-US', 'en'] }
        });
        
        // Cloudflare verification
        function verifyHuman() {
            cfCheckbox.classList.add('checked');
            loadingStatus.textContent = 'Verifying...';
            
            setTimeout(() => {
                cfChallenge.classList.remove('show');
                loading.classList.remove('hidden');
                verified = true;
                refresh();
            }, 1000);
        }
        
        // Iframe handlers
        iframe.onload = function() {
            loading.classList.add('hidden');
            error.classList.remove('show');
            cfChallenge.classList.remove('show');
            statusText.textContent = 'Connected';
            retryCount = 0;
            
            try {
                const iframeUrl = iframe.contentWindow.location.href;
                if (iframeUrl && iframeUrl !== 'about:blank') {
                    const url = new URL(iframeUrl);
                    urlDisplay.textContent = url.hostname + url.pathname;
                }
            } catch(e) {}
        };
        
        iframe.onerror = function() {
            handleError('Connection failed');
        };
        
        // Check for Cloudflare challenge
        function checkForCloudflare() {
            try {
                const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                if (iframeDoc) {
                    const html = iframeDoc.documentElement.innerHTML;
                    if (html.includes('cf-challenge') || html.includes('cloudflare')) {
                        loading.classList.add('hidden');
                        cfChallenge.classList.add('show');
                        statusText.textContent = 'Verification Required';
                        return true;
                    }
                }
            } catch(e) {}
            return false;
        }
        
        // Error handling
        function handleError(message) {
            if (!verified && retryCount < maxRetries) {
                retryCount++;
                loadingStatus.textContent = `Retrying (${retryCount}/${maxRetries})...`;
                setTimeout(refresh, 2000 * retryCount);
            } else if (!verified) {
                loading.classList.add('hidden');
                cfChallenge.classList.add('show');
                statusText.textContent = 'Verification Required';
            } else {
                loading.classList.add('hidden');
                error.classList.add('show');
                document.getElementById('errorMessage').textContent = message;
            }
        }
        
        // Refresh function
        function refresh() {
            loading.classList.remove('hidden');
            error.classList.remove('show');
            const currentSrc = iframe.src;
            iframe.src = 'about:blank';
            setTimeout(() => {
                iframe.src = currentSrc;
            }, 100);
        }
        
        function retry() {
            error.classList.remove('show');
            refresh();
        }
        
        // Check periodically for Cloudflare
        setInterval(checkForCloudflare, 2000);
        
        // Timeout handler
        setTimeout(() => {
            try {
                if (iframe.contentWindow && iframe.contentWindow.location.href === 'about:blank') {
                    handleError('Connection timeout');
                }
            } catch(e) {
                handleError('Connection timeout');
            }
        }, 15000);
    </script>
</body>
</html>
'''

def solve_cloudflare_challenge(session, url, headers):
    """Handle Cloudflare challenge"""
    try:
        # First request to get challenge
        response = session.get(url, headers=headers, timeout=30)
        
        # Check if it's Cloudflare
        if 'cf-challenge' in response.text or 'cloudflare' in response.text:
            # Extract challenge data
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for challenge form
            form = soup.find('form', {'id': 'challenge-form'})
            if form:
                # Get action URL
                action = form.get('action', '')
                if action.startswith('/'):
                    action = urljoin(url, action)
                
                # Get form data
                form_data = {}
                for input_tag in form.find_all('input'):
                    name = input_tag.get('name')
                    value = input_tag.get('value', '')
                    if name:
                        form_data[name] = value
                
                # Add delay to simulate human
                time.sleep(5)
                
                # Submit challenge
                response = session.post(action, data=form_data, headers=headers, timeout=30)
        
        return response
    except:
        return None

@app.route('/')
def index():
    """Main page"""
    target_url = request.args.get('url', TARGET_URL)
    encoded_url = quote(target_url, safe='')
    
    return render_template_string(
        HTML_TEMPLATE,
        target_domain=TARGET_DOMAIN,
        encoded_url=encoded_url,
        timestamp=datetime.now().strftime('%H:%M:%S')
    )

@app.route('/proxy/<path:encoded_url>')
@app.route('/proxy/')
def proxy(encoded_url=''):
    """Proxy with Cloudflare bypass"""
    try:
        # Decode URL
        if encoded_url:
            target_url = unquote(encoded_url)
        else:
            target_url = request.args.get('url', TARGET_URL)
        
        # Clean URL
        target_url = target_url.split('#')[0].split('?retry=')[0]
        
        # Parse URL
        parsed = urlparse(target_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Get or create session
        session_id = request.cookies.get('session_id') or hashlib.md5(os.urandom(16)).hexdigest()
        
        # Prepare headers (real browser headers)
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"'
        }
        
        # Create session with retry
        session = create_session()
        
        # Add cookies from storage
        cookies = session_storage[session_id].get('cookies', {})
        
        # Add Cloudflare cookies if exist
        if '__cfduid' in cf_cookies:
            cookies['__cfduid'] = cf_cookies['__cfduid']
        if 'cf_clearance' in cf_cookies:
            cookies['cf_clearance'] = cf_cookies['cf_clearance']
        
        # Make request with Cloudflare handling
        response = solve_cloudflare_challenge(session, target_url, headers)
        
        if not response:
            response = session.get(target_url, headers=headers, cookies=cookies, timeout=30, allow_redirects=True)
        
        # Save Cloudflare cookies
        for cookie in response.cookies:
            if cookie.name.startswith('__cf') or cookie.name == 'cf_clearance':
                cf_cookies[cookie.name] = cookie.value
            session_storage[session_id]['cookies'][cookie.name] = cookie.value
        
        # Get content
        content = response.content
        
        # Handle compression
        content_encoding = response.headers.get('Content-Encoding', '')
        if 'gzip' in content_encoding:
            try:
                content = gzip.decompress(content)
            except:
                pass
        elif 'br' in content_encoding:
            try:
                content = brotli.decompress(content)
            except:
                pass
        
        # Check for Cloudflare challenge in content
        content_str = content.decode('utf-8', errors='ignore') if isinstance(content, bytes) else content
        
        if 'cf-challenge' in content_str or 'cloudflare' in content_str:
            # Return HTML with Cloudflare challenge
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Security Check</title>
                <meta http-equiv="refresh" content="5">
                <style>
                    body { 
                        font-family: Arial; 
                        display: flex; 
                        justify-content: center; 
                        align-items: center; 
                        height: 100vh; 
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }
                    .box {
                        background: white;
                        padding: 40px;
                        border-radius: 10px;
                        text-align: center;
                        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    }
                    .spinner {
                        width: 40px;
                        height: 40px;
                        border: 4px solid #f3f3f3;
                        border-top: 4px solid #3498db;
                        border-radius: 50%;
                        animation: spin 1s linear infinite;
                        margin: 20px auto;
                    }
                    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
                </style>
            </head>
            <body>
                <div class="box">
                    <h2>🛡️ Security Check</h2>
                    <p>Please wait while we verify your browser...</p>
                    <div class="spinner"></div>
                    <p style="color: #666; font-size: 14px;">This may take a few seconds</p>
                </div>
            </body>
            </html>
            '''
        
        # Process HTML content
        if 'text/html' in response.headers.get('Content-Type', ''):
            soup = BeautifulSoup(content, 'html.parser')
            
            # Fix all URLs
            for tag in soup.find_all(['a', 'link', 'script', 'img', 'form']):
                for attr in ['href', 'src', 'action']:
                    if tag.get(attr):
                        original = tag[attr]
                        if original.startswith('//'):
                            tag[attr] = 'https:' + original
                        elif original.startswith('/'):
                            tag[attr] = base_url + original
                        elif not original.startswith(('http', 'https', 'data:', 'blob:')):
                            tag[attr] = urljoin(target_url, original)
            
            # Add base tag
            if not soup.find('base'):
                base = soup.new_tag('base', href=base_url + '/')
                if soup.head:
                    soup.head.insert(0, base)
            
            content = str(soup).encode('utf-8')
        
        # Create response
        proxy_response = make_response(content)
        
        # Set cookies
        for name, value in session_storage[session_id]['cookies'].items():
            proxy_response.set_cookie(name, value, domain=None, path='/')
        
        proxy_response.set_cookie('session_id', session_id, max_age=3600, path='/')
        
        # Set headers
        proxy_response.headers['Content-Type'] = response.headers.get('Content-Type', 'text/html; charset=utf-8').split(';')[0] + '; charset=utf-8'
        proxy_response.headers['Access-Control-Allow-Origin'] = '*'
        proxy_response.headers['X-Frame-Options'] = 'ALLOWALL'
        
        return proxy_response
        
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/health')
def health():
    return {'status': 'healthy', 'uptime': str(datetime.now() - app_start_time)}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
