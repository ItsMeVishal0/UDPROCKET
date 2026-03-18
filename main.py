import os
import time
import json
import gzip
import hashlib
import random
import string
import requests
import threading
import execjs
import re
from flask import Flask, render_template_string, request, make_response, jsonify
from flask_cors import CORS
from urllib.parse import urlparse, urljoin, quote, unquote, parse_qs
from bs4 import BeautifulSoup
from datetime import datetime
from collections import defaultdict
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app, supports_credentials=True)

# Configuration
TARGET_URL = "https://kimstress.st/login"
TARGET_DOMAIN = "kimstress.st"
BASE_URL = f"https://{TARGET_DOMAIN}"

# Real browser user agents
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

# Session storage
session_db = defaultdict(lambda: {
    'cookies': {},
    'headers': {},
    'created': datetime.now(),
    'last_used': datetime.now(),
    'user_agent': random.choice(USER_AGENTS),
    'cf_clearance': None
})

# Cloudflare challenge solver
class CloudflareSolver:
    def __init__(self):
        self.session = requests.Session()
        self.setup_session()
    
    def setup_session(self):
        retry = Retry(total=3, backoff_factor=1)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def solve_challenge(self, url, headers, cookies):
        try:
            # First request to get challenge page
            response = self.session.get(url, headers=headers, cookies=cookies, timeout=30)
            
            # Check if it's Cloudflare
            if 'cf-challenge' in response.text or 'cloudflare' in response.text:
                logger.info("Cloudflare challenge detected")
                
                # Parse challenge
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find challenge form
                form = soup.find('form', {'id': 'challenge-form'})
                if not form:
                    form = soup.find('form', {'action': re.compile(r'challenge')})
                
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
                    challenge_response = self.session.post(
                        action, 
                        data=form_data, 
                        headers=headers,
                        cookies=cookies,
                        timeout=30,
                        allow_redirects=True
                    )
                    
                    # Get cf_clearance cookie
                    for cookie in self.session.cookies:
                        if cookie.name == 'cf_clearance':
                            return {
                                'success': True,
                                'cf_clearance': cookie.value,
                                'cookies': dict(self.session.cookies)
                            }
                    
                    return {'success': True, 'cookies': dict(self.session.cookies)}
            
            return {'success': True, 'cookies': dict(response.cookies)}
            
        except Exception as e:
            logger.error(f"Cloudflare solver error: {e}")
            return {'success': False, 'error': str(e)}

cf_solver = CloudflareSolver()

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
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            width: 100%;
            max-width: 1200px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .browser-header {
            background: #1a1a1a;
            padding: 15px 20px;
        }
        
        .window-controls {
            display: flex;
            gap: 8px;
            margin-bottom: 10px;
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
            background: #333;
            border-radius: 8px;
            padding: 10px 15px;
            display: flex;
            align-items: center;
            gap: 10px;
            color: white;
        }
        
        .lock {
            color: #4caf50;
        }
        
        .url {
            flex: 1;
            font-size: 14px;
        }
        
        .refresh {
            background: transparent;
            border: none;
            color: #aaa;
            cursor: pointer;
            font-size: 16px;
        }
        
        .content {
            min-height: 600px;
            position: relative;
            background: #f5f5f5;
        }
        
        #main-frame {
            width: 100%;
            min-height: 600px;
            border: none;
            background: white;
        }
        
        .loading {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255,255,255,0.95);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        
        .loading.hidden {
            display: none;
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
        
        .cf-box {
            background: white;
            border-radius: 15px;
            padding: 40px;
            text-align: center;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            max-width: 400px;
            margin: 50px auto;
        }
        
        .cf-logo {
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 20px;
            color: white;
            font-size: 40px;
        }
        
        .cf-title {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 15px;
            color: #333;
        }
        
        .cf-text {
            color: #666;
            margin-bottom: 30px;
            line-height: 1.6;
        }
        
        .cf-checkbox {
            width: 60px;
            height: 60px;
            border: 3px solid #ddd;
            border-radius: 50%;
            margin: 0 auto 20px;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 30px;
            color: white;
        }
        
        .cf-checkbox.checked {
            background: #4caf50;
            border-color: #4caf50;
        }
        
        .cf-button {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 40px;
            border-radius: 25px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .cf-button:hover {
            background: #5a67d8;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .cf-footer {
            margin-top: 30px;
            font-size: 12px;
            color: #999;
        }
        
        .error {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            display: none;
        }
        
        .error.show {
            display: block;
        }
        
        .error button {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 30px;
            border-radius: 5px;
            margin-top: 20px;
            cursor: pointer;
        }
        
        .status-bar {
            background: #1a1a1a;
            padding: 8px 20px;
            color: #aaa;
            font-size: 12px;
            display: flex;
            justify-content: space-between;
            border-top: 1px solid #333;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="browser-header">
            <div class="window-controls">
                <div class="dot red"></div>
                <div class="dot yellow"></div>
                <div class="dot green"></div>
            </div>
            <div class="address-bar">
                <span class="lock">🔒</span>
                <span class="url" id="urlDisplay">{{ target_url }}</span>
                <button class="refresh" onclick="refresh()">↻</button>
            </div>
        </div>
        
        <div class="content">
            <!-- Loading -->
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <div class="loading-text">Loading secure content...</div>
                <div id="loadingStatus">Connecting to {{ target_domain }}</div>
            </div>
            
            <!-- Cloudflare Challenge Box -->
            <div class="cf-box" id="cfBox" style="display: none;">
                <div class="cf-logo">🛡️</div>
                <div class="cf-title">Verify You Are Human</div>
                <div class="cf-text">
                    Please complete the security check to access {{ target_domain }}
                </div>
                <div class="cf-checkbox" id="cfCheckbox" onclick="verifyHuman()"></div>
                <button class="cf-button" onclick="verifyHuman()">Click to Verify</button>
                <div class="cf-footer">Protected by Cloudflare</div>
            </div>
            
            <!-- Error -->
            <div class="error" id="error">
                <div style="font-size: 40px; margin-bottom: 20px;">⚠️</div>
                <div style="font-size: 18px; margin-bottom: 10px;">Connection Error</div>
                <div id="errorMessage">Failed to load website</div>
                <button onclick="location.reload()">Reload Page</button>
            </div>
            
            <!-- Main Frame -->
            <iframe 
                id="main-frame"
                src="/proxy/{{ encoded_url }}"
                sandbox="allow-same-origin allow-scripts allow-popups allow-forms allow-modals allow-top-navigation"
                referrerpolicy="no-referrer"
                style="width: 100%; min-height: 600px;">
            </iframe>
        </div>
        
        <div class="status-bar">
            <span id="status">Secure Connection</span>
            <span>{{ timestamp }}</span>
        </div>
    </div>
    
    <script>
        // Anti-detection
        Object.defineProperties(navigator, {
            webdriver: { get: () => undefined },
            plugins: { get: () => [1, 2, 3, 4, 5] }
        });
        
        const iframe = document.getElementById('main-frame');
        const loading = document.getElementById('loading');
        const cfBox = document.getElementById('cfBox');
        const cfCheckbox = document.getElementById('cfCheckbox');
        const error = document.getElementById('error');
        const urlDisplay = document.getElementById('urlDisplay');
        const loadingStatus = document.getElementById('loadingStatus');
        const statusEl = document.getElementById('status');
        
        let retryCount = 0;
        const maxRetries = 3;
        let verified = false;
        
        // Iframe load handler
        iframe.onload = function() {
            loading.style.display = 'none';
            cfBox.style.display = 'none';
            error.classList.remove('show');
            statusEl.textContent = 'Connected • Secure';
            
            try {
                const iframeUrl = iframe.contentWindow.location.href;
                if (iframeUrl && iframeUrl !== 'about:blank') {
                    urlDisplay.textContent = iframeUrl;
                }
                
                // Check for Cloudflare in iframe
                const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                if (iframeDoc) {
                    const html = iframeDoc.documentElement.innerHTML;
                    if (html.includes('cf-challenge') || html.includes('cloudflare')) {
                        showCloudflare();
                    }
                }
            } catch(e) {
                // Cross-origin, ignore
            }
        };
        
        // Iframe error handler
        iframe.onerror = function() {
            if (!verified && retryCount < maxRetries) {
                retryCount++;
                loadingStatus.textContent = `Retrying (${retryCount}/${maxRetries})...`;
                setTimeout(refresh, 2000 * retryCount);
            } else if (!verified) {
                showCloudflare();
            } else {
                loading.style.display = 'none';
                error.classList.add('show');
                document.getElementById('errorMessage').textContent = 'Failed to load website';
            }
        };
        
        // Show Cloudflare challenge
        function showCloudflare() {
            loading.style.display = 'none';
            cfBox.style.display = 'block';
            statusEl.textContent = 'Verification Required';
        }
        
        // Verify human
        function verifyHuman() {
            cfCheckbox.classList.add('checked');
            loading.style.display = 'flex';
            loadingStatus.textContent = 'Verifying...';
            verified = true;
            
            // Simulate verification
            setTimeout(() => {
                cfBox.style.display = 'none';
                refresh();
            }, 2000);
        }
        
        // Refresh function
        function refresh() {
            loading.style.display = 'flex';
            loadingStatus.textContent = 'Refreshing...';
            cfBox.style.display = 'none';
            error.classList.remove('show');
            
            const currentSrc = iframe.src;
            iframe.src = 'about:blank';
            setTimeout(() => {
                iframe.src = currentSrc.split('?')[0] + '?t=' + Date.now();
            }, 100);
        }
        
        // Check for Cloudflare periodically
        setInterval(() => {
            try {
                const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                if (iframeDoc) {
                    const html = iframeDoc.documentElement.innerHTML;
                    if (html.includes('cf-challenge') || html.includes('cloudflare')) {
                        showCloudflare();
                    }
                }
            } catch(e) {}
        }, 2000);
        
        // Timeout check
        setTimeout(() => {
            try {
                if (iframe.contentWindow.location.href === 'about:blank') {
                    iframe.onerror();
                }
            } catch(e) {}
        }, 15000);
        
        window.refresh = refresh;
        window.verifyHuman = verifyHuman;
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Main page"""
    target_url = request.args.get('url', TARGET_URL)
    encoded_url = quote(target_url, safe='')
    
    return render_template_string(
        HTML_TEMPLATE,
        target_url=target_url,
        target_domain=TARGET_DOMAIN,
        encoded_url=encoded_url,
        timestamp=datetime.now().strftime('%H:%M:%S')
    )

@app.route('/proxy/<path:encoded_url>')
@app.route('/proxy/')
def proxy(encoded_url=''):
    """Proxy with Cloudflare handling"""
    try:
        # Decode URL
        if encoded_url:
            target_url = unquote(encoded_url)
        else:
            target_url = request.args.get('url', TARGET_URL)
        
        # Clean URL
        target_url = target_url.split('?t=')[0].split('?retry=')[0]
        
        # Get session ID
        session_id = request.cookies.get('session_id') or hashlib.md5(os.urandom(16)).hexdigest()
        
        # Update session
        session_db[session_id]['last_used'] = datetime.now()
        
        # Headers
        headers = {
            'User-Agent': session_db[session_id]['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Referer': 'https://www.google.com/'
        }
        
        # Get cookies
        cookies = session_db[session_id]['cookies'].copy()
        
        # Add CF clearance if exists
        if session_db[session_id]['cf_clearance']:
            cookies['cf_clearance'] = session_db[session_id]['cf_clearance']
        
        # Try to solve Cloudflare if needed
        result = cf_solver.solve_challenge(target_url, headers, cookies)
        
        if result['success']:
            # Update cookies
            for name, value in result.get('cookies', {}).items():
                session_db[session_id]['cookies'][name] = value
                if name == 'cf_clearance':
                    session_db[session_id]['cf_clearance'] = value
            
            # Get final content
            response = cf_solver.session.get(
                target_url,
                headers=headers,
                cookies=session_db[session_id]['cookies'],
                timeout=30,
                allow_redirects=True,
                verify=False
            )
            
            # Get content
            content = response.content
            
            # Handle compression
            if response.headers.get('Content-Encoding') == 'gzip':
                try:
                    content = gzip.decompress(content)
                except:
                    pass
            
            # Process HTML
            content_type = response.headers.get('Content-Type', 'text/html')
            if 'text/html' in content_type:
                try:
                    # Parse HTML
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Fix URLs
                    parsed = urlparse(target_url)
                    base_url = f"{parsed.scheme}://{parsed.netloc}"
                    
                    for tag in soup.find_all(['a', 'link', 'script', 'img', 'form']):
                        for attr in ['href', 'src', 'action']:
                            if tag.get(attr):
                                original = tag[attr]
                                if original.startswith('/'):
                                    tag[attr] = base_url + original
                                elif original.startswith('//'):
                                    tag[attr] = 'https:' + original
                                elif not original.startswith(('http', 'https', 'data:')):
                                    tag[attr] = urljoin(base_url, original)
                    
                    # Add base tag
                    if not soup.find('base'):
                        base = soup.new_tag('base', href=base_url + '/')
                        if soup.head:
                            soup.head.insert(0, base)
                    
                    content = str(soup).encode('utf-8')
                except Exception as e:
                    logger.error(f"HTML processing error: {e}")
            
            # Create response
            proxy_response = make_response(content)
            
            # Set cookies
            for name, value in session_db[session_id]['cookies'].items():
                proxy_response.set_cookie(name, value, path='/')
            
            proxy_response.set_cookie('session_id', session_id, max_age=3600, path='/')
            
            # Set headers
            proxy_response.headers['Content-Type'] = 'text/html; charset=utf-8'
            proxy_response.headers['Access-Control-Allow-Origin'] = '*'
            proxy_response.headers['X-Frame-Options'] = 'ALLOWALL'
            
            return proxy_response
        else:
            return "Cloudflare challenge failed", 403
            
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        return f"Error: {str(e)}", 500

@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'sessions': len(session_db),
        'timestamp': datetime.now().isoformat()
    })

# Cleanup old sessions
def cleanup_sessions():
    while True:
        try:
            now = datetime.now()
            expired = [sid for sid, data in session_db.items() 
                      if (now - data['last_used']).seconds > 3600]
            for sid in expired:
                del session_db[sid]
            time.sleep(300)
        except:
            time.sleep(60)

# Start cleanup thread
threading.Thread(target=cleanup_sessions, daemon=True).start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
