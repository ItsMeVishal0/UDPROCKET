from flask import Flask, render_template_string, request, jsonify, Response
from flask_cors import CORS
import requests
import logging
import os
import time
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'cloudflare-bypass-key'
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# User agents pool to avoid detection
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

login_database = []

# HTML Template with better iframe handling
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kimstress Login Portal</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        .main-content {
            background: white;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }

        .header {
            background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
            color: white;
            padding: 25px 30px;
        }

        .header h1 {
            font-size: 28px;
            margin-bottom: 5px;
        }

        .warning-banner {
            background: #fef9c3;
            color: #854d0e;
            padding: 12px 20px;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 10px;
            border-bottom: 1px solid #e2e8f0;
        }

        .iframe-container {
            position: relative;
            height: 650px;
            background: #f1f5f9;
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
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            gap: 20px;
            z-index: 1000;
            backdrop-filter: blur(5px);
        }

        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid #e2e8f0;
            border-top: 4px solid #2563eb;
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
            padding: 12px 24px;
            border: none;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s;
        }

        .btn-primary {
            background: #2563eb;
            color: white;
        }

        .btn-primary:hover {
            background: #1d4ed8;
            transform: translateY(-2px);
        }

        .btn-success {
            background: #22c55e;
            color: white;
        }

        .btn-warning {
            background: #f59e0b;
            color: white;
        }

        .sidebar {
            background: white;
            border-radius: 20px;
            padding: 25px;
            margin-top: 20px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }

        .stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 15px;
            margin: 20px 0;
        }

        .stat-card {
            background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
        }

        .stat-number {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 5px;
        }

        .login-item {
            background: #f8fafc;
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 10px;
            border-left: 4px solid #2563eb;
        }

        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            border-radius: 10px;
            color: white;
            display: none;
            z-index: 9999;
            animation: slideIn 0.3s;
        }

        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        .tip-box {
            background: #dbeafe;
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
            color: #1e40af;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="notification" id="notification"></div>
    
    <div class="container">
        <div class="main-content">
            <div class="header">
                <h1>🔐 Kimstress.st Login Portal</h1>
                <p>Advanced Cloudflare Bypass • Anti-Detection Mode</p>
            </div>
            
            <div class="warning-banner">
                <span>⚠️</span>
                <span>If you see "Verify you are human", click "Open in New Window" button below</span>
            </div>
            
            <div class="iframe-container">
                <iframe 
                    id="mainIframe" 
                    src="/proxy?url=https://kimstress.st/login"
                    sandbox="allow-forms allow-scripts allow-same-origin allow-popups allow-modals allow-popups-to-escape-sandbox allow-top-navigation"
                    allow="camera; microphone; fullscreen">
                </iframe>
                
                <div class="loading-overlay" id="loadingOverlay">
                    <div class="spinner"></div>
                    <div style="color: #1e293b; font-weight: 500;">Bypassing Cloudflare protection...</div>
                </div>
            </div>
            
            <div class="controls">
                <button class="btn btn-primary" onclick="reloadIframe()">
                    🔄 Reload with New Identity
                </button>
                <button class="btn btn-warning" onclick="openInNewWindow()">
                    🌐 Open in New Window (Recommended)
                </button>
                <button class="btn btn-success" onclick="tryMobileMode()">
                    📱 Try Mobile Mode
                </button>
            </div>
        </div>
        
        <div class="sidebar">
            <h3 style="margin-bottom: 15px;">📊 Bypass Status</h3>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number" id="attemptCount">0</div>
                    <div>Attempts</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="successCount">0</div>
                    <div>Success</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="failCount">0</div>
                    <div>Failed</div>
                </div>
            </div>
            
            <div class="tip-box">
                <strong>💡 Quick Tip:</strong><br>
                Cloudflare blocks iframes. Click "Open in New Window" to access directly, then copy login data manually.
            </div>
        </div>
    </div>

    <script>
        let attempts = 0;
        let successes = 0;
        let failures = 0;
        
        function reloadIframe() {
            attempts++;
            document.getElementById('attemptCount').textContent = attempts;
            
            document.getElementById('loadingOverlay').style.display = 'flex';
            
            // Add random parameter to avoid cache
            const randomId = Math.random().toString(36).substring(7);
            document.getElementById('mainIframe').src = '/proxy?url=https://kimstress.st/login&t=' + Date.now() + '&id=' + randomId;
            
            // Auto hide after 10 seconds
            setTimeout(() => {
                document.getElementById('loadingOverlay').style.display = 'none';
            }, 10000);
        }
        
        function openInNewWindow() {
            successes++;
            document.getElementById('successCount').textContent = successes;
            
            // Open in new window with JavaScript disabled? No, just normal window
            window.open('https://kimstress.st/login', '_blank');
            showNotification('✅ Opened in new window. Login there and copy data.', 'success');
        }
        
        function tryMobileMode() {
            // Try mobile user agent
            fetch('/mobile-mode')
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        reloadIframe();
                        showNotification('📱 Switched to mobile mode', 'success');
                    }
                });
        }
        
        function showNotification(msg, type) {
            const notif = document.getElementById('notification');
            notif.style.display = 'block';
            notif.textContent = msg;
            notif.style.background = type === 'success' ? '#22c55e' : '#ef4444';
            setTimeout(() => notif.style.display = 'none', 3000);
        }
        
        // Handle iframe load
        document.getElementById('mainIframe').onload = function() {
            document.getElementById('loadingOverlay').style.display = 'none';
            
            try {
                // Check if iframe content shows Cloudflare
                const iframeDoc = this.contentDocument || this.contentWindow.document;
                const bodyText = iframeDoc.body?.innerText || '';
                
                if (bodyText.includes('Verify you are human') || bodyText.includes('security check')) {
                    failures++;
                    document.getElementById('failCount').textContent = failures;
                    showNotification('❌ Cloudflare detected - Use "Open in New Window"', 'error');
                } else {
                    successes++;
                    document.getElementById('successCount').textContent = successes;
                }
            } catch(e) {
                // CORS error - but that's okay, means iframe loaded
                successes++;
                document.getElementById('successCount').textContent = successes;
            }
        };
        
        // Initial load
        setTimeout(() => {
            showNotification('⚠️ If blocked, click "Open in New Window"', 'warning');
        }, 2000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/proxy')
def proxy():
    """Proxy with advanced headers to bypass Cloudflare"""
    target_url = request.args.get('url', 'https://kimstress.st/login')
    
    try:
        # Random user agent
        user_agent = random.choice(USER_AGENTS)
        
        # Advanced headers to mimic real browser
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Referer': 'https://www.google.com/',
            'DNT': '1'
        }
        
        # Use session to maintain cookies
        session = requests.Session()
        
        # First request to get cookies
        response = session.get(
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
        
        # Copy cookies
        for cookie in session.cookies:
            proxy_response.set_cookie(cookie.name, cookie.value)
        
        return proxy_response
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"""
        <html>
        <body style="font-family: Arial; text-align: center; padding: 40px;">
            <h2>⚠️ Connection Error</h2>
            <p>{str(e)}</p>
            <button onclick="window.parent.openInNewWindow()" style="padding: 12px 30px; background: #2563eb; color: white; border: none; border-radius: 8px; margin-top: 20px;">
                Open in New Window
            </button>
        </body>
        </html>
        """

@app.route('/mobile-mode')
def mobile_mode():
    """Switch to mobile user agent"""
    try:
        # Mobile user agent
        mobile_ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
        
        response = requests.get(
            'https://kimstress.st/login',
            headers={'User-Agent': mobile_ua},
            timeout=5
        )
        
        return jsonify({"success": True})
    except:
        return jsonify({"success": False})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("="*60)
    print("🚀 Kimstress Portal - Cloudflare Bypass Mode")
    print("="*60)
    print("⚠️  If iframe shows Cloudflare, use 'Open in New Window'")
    print(f"🔗 URL: http://localhost:{port}")
    print("="*60)
    
    app.run(host='0.0.0.0', port=port, debug=True)
