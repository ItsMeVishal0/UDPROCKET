from flask import Flask, render_template_string, request, jsonify, Response
from flask_cors import CORS
import requests
from urllib.parse import urlparse
import logging
import os
import time

# Proxy Configuration
PROXY_CONFIG = {
    'server': 'http://change4.owlproxy.com:7778',
    'username': 'IIOL0QVOzN30_custom_zone_SG_st__city_sid_79312845_time_5',
    'password': '2272641'
}
PROXY_ENABLED = True

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kimstress Login - Proxy Viewer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        header {
            background: white;
            padding: 20px 30px;
            border-bottom: 1px solid #e0e0e0;
        }
        header h1 {
            color: #333;
            font-size: 24px;
            margin-bottom: 5px;
        }
        .proxy-badge {
            background: #6f42c1;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            margin-left: 10px;
        }
        .status-bar {
            background: #f8f9fa;
            padding: 10px 30px;
            border-bottom: 1px solid #e0e0e0;
            font-size: 13px;
            color: #666;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .status-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 5px;
        }
        .status-online { background-color: #28a745; }
        .status-offline { background-color: #dc3545; }
        .proxy-info {
            background: #e7f5ff;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
        }
        .iframe-container {
            position: relative;
            width: 100%;
            height: 70vh;
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
            text-align: center;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 10px 30px;
            margin: 0 10px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: transform 0.2s;
        }
        .btn:hover { transform: translateY(-2px); }
        .error-message {
            background: #f8d7da;
            color: #721c24;
            padding: 10px 20px;
            display: none;
        }
        .success-message {
            background: #d4edda;
            color: #155724;
            padding: 10px 20px;
            display: none;
        }
        .loading-overlay {
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(255,255,255,0.8);
            display: none;
            justify-content: center;
            align-items: center;
        }
        .loading-spinner {
            width: 40px;
            height: 40px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin { 100% { transform: rotate(360deg); } }
        @media (max-width: 768px) {
            .btn { display: block; width: 100%; margin: 10px 0; }
            .status-bar { flex-direction: column; gap: 10px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Kimstress.st Login <span class="proxy-badge">🌐 Proxy Active</span></h1>
        </header>
        
        <div class="status-bar">
            <span>
                <span class="status-indicator status-online" id="statusIndicator"></span>
                <span id="statusText">Connecting...</span>
            </span>
            <span class="proxy-info" id="proxyLocation">📍 Singapore Proxy</span>
            <span>🎯 kimstress.st/login</span>
        </div>
        
        <div class="iframe-container">
            <iframe id="mainIframe" src="/proxy?url=https://kimstress.st/login" frameborder="0"></iframe>
            <div class="loading-overlay" id="loadingOverlay">
                <div class="loading-spinner"></div>
            </div>
        </div>
        
        <div id="errorMessage" class="error-message"></div>
        <div id="successMessage" class="success-message"></div>
        
        <div class="controls">
            <button onclick="reloadIframe()" class="btn">⟳ Reload</button>
            <button onclick="openInNewTab()" class="btn">↗ New Tab</button>
            <button onclick="testProxy()" class="btn">🌐 Test Proxy</button>
        </div>
    </div>

    <script>
        const iframe = document.getElementById('mainIframe');
        const loadingOverlay = document.getElementById('loadingOverlay');
        const errorMsg = document.getElementById('errorMessage');
        const successMsg = document.getElementById('successMessage');
        const statusIndicator = document.getElementById('statusIndicator');
        const statusText = document.getElementById('statusText');

        iframe.addEventListener('load', function() {
            loadingOverlay.style.display = 'none';
            statusIndicator.className = 'status-indicator status-online';
            statusText.textContent = 'Connected via Proxy';
            showSuccess('Page loaded successfully');
        });

        iframe.addEventListener('error', function() {
            loadingOverlay.style.display = 'none';
            statusIndicator.className = 'status-indicator status-offline';
            statusText.textContent = 'Connection Failed';
            showError('Failed to load page');
        });

        function reloadIframe() {
            loadingOverlay.style.display = 'flex';
            iframe.src = iframe.src;
        }

        function openInNewTab() {
            window.open('https://kimstress.st/login', '_blank');
        }

        function testProxy() {
            fetch('/test-proxy')
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success') {
                        showSuccess(`Proxy OK! IP: ${data.ip}`);
                        document.getElementById('proxyLocation').textContent = `📍 ${data.location}`;
                    } else {
                        showError('Proxy test failed');
                    }
                })
                .catch(() => showError('Proxy test error'));
        }

        function showError(msg) {
            errorMsg.style.display = 'block';
            errorMsg.textContent = '❌ ' + msg;
            successMsg.style.display = 'none';
            setTimeout(() => errorMsg.style.display = 'none', 5000);
        }

        function showSuccess(msg) {
            successMsg.style.display = 'block';
            successMsg.textContent = '✅ ' + msg;
            errorMsg.style.display = 'none';
            setTimeout(() => successMsg.style.display = 'none', 3000);
        }

        // Auto test proxy on load
        setTimeout(testProxy, 1000);
    </script>
</body>
</html>
"""

def get_proxy_config():
    if not PROXY_ENABLED:
        return None
    parsed = urlparse(PROXY_CONFIG['server'])
    proxy_with_auth = f"{parsed.scheme}://{PROXY_CONFIG['username']}:{PROXY_CONFIG['password']}@{parsed.netloc}"
    return {'http': proxy_with_auth, 'https': proxy_with_auth}

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/proxy')
def proxy():
    target_url = request.args.get('url', 'https://kimstress.st/login')
    
    try:
        proxies = get_proxy_config()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        
        logger.info(f"Fetching {target_url} via proxy")
        
        response = requests.get(
            target_url,
            headers=headers,
            timeout=30,
            proxies=proxies,
            allow_redirects=True
        )
        
        proxy_response = Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type', 'text/html')
        )
        
        proxy_response.headers['Access-Control-Allow-Origin'] = '*'
        
        # Remove X-Frame-Options
        if 'X-Frame-Options' in proxy_response.headers:
            del proxy_response.headers['X-Frame-Options']
            
        return proxy_response
        
    except requests.ProxyError as e:
        logger.error(f"Proxy error: {e}")
        return "Proxy connection error", 502
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"Error: {str(e)}", 500

@app.route('/test-proxy')
def test_proxy():
    try:
        proxies = get_proxy_config()
        if not proxies:
            return jsonify({"status": "error", "message": "Proxy disabled"})
            
        response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            ip = data.get('origin', 'Unknown')
            
            # Get location
            loc_res = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
            if loc_res.status_code == 200:
                loc_data = loc_res.json()
                location = f"{loc_data.get('city', 'Unknown')}, {loc_data.get('country', 'Unknown')}"
            else:
                location = "Singapore"
                
            return jsonify({
                "status": "success",
                "ip": ip,
                "location": location
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "proxy_enabled": PROXY_ENABLED,
        "proxy_server": PROXY_CONFIG['server'],
        "timestamp": time.time()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Server starting on port {port}")
    print(f"🌐 Proxy: {PROXY_CONFIG['server']}")
    print(f"📍 Location: Singapore")
    app.run(host='0.0.0.0', port=port, debug=True)
