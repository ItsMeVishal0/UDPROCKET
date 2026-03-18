import os
import random
import string
import requests
from flask import Flask, render_template_string, make_response
from datetime import datetime

app = Flask(__name__)

# HTML Template with proxy approach
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Secure Gateway</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            overflow: hidden;
        }
        .container {
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
        }
        .browser-mock {
            background: #1a1a1a;
            padding: 8px 15px;
            display: flex;
            align-items: center;
            gap: 10px;
            border-bottom: 1px solid #333;
        }
        .browser-dots { display: flex; gap: 8px; }
        .dot { width: 12px; height: 12px; border-radius: 50%; }
        .dot.red { background: #ff5f56; }
        .dot.yellow { background: #ffbd2e; }
        .dot.green { background: #27c93f; }
        .browser-address {
            flex: 1;
            background: #333;
            color: #fff;
            padding: 6px 15px;
            border-radius: 20px;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .lock-icon { color: #4caf50; font-size: 16px; }
        .url-text { color: #aaa; margin-left: auto; font-size: 12px; }
        .iframe-container {
            flex: 1;
            background: white;
            position: relative;
            overflow: hidden;
        }
        #main-frame {
            width: 100%;
            height: 100%;
            border: none;
            background: white;
            display: block;
        }
        .loading-screen {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: white;
            z-index: 10;
            transition: opacity 0.3s ease;
        }
        .loading-screen.hidden { opacity: 0; pointer-events: none; }
        .loading-spinner {
            width: 60px;
            height: 60px;
            border: 5px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 20px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .loading-text { font-size: 18px; margin-bottom: 10px; }
        .loading-subtext { font-size: 14px; opacity: 0.8; }
        .error-message {
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
            z-index: 20;
        }
        .error-message.show { display: block; }
        .error-title { color: #ff4757; font-size: 20px; margin-bottom: 10px; }
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 30px;
            border-radius: 5px;
            margin-top: 20px;
            cursor: pointer;
            font-weight: 600;
        }
        .refresh-btn:hover { background: #5a67d8; }
    </style>
</head>
<body>
    <div class="container">
        <div class="browser-mock">
            <div class="browser-dots">
                <div class="dot red"></div>
                <div class="dot yellow"></div>
                <div class="dot green"></div>
            </div>
            <div class="browser-address">
                <span class="lock-icon">🔒</span>
                <span>kimstress.st/login</span>
                <span class="url-text">secure connection</span>
            </div>
        </div>
        
        <div class="iframe-container">
            <div class="loading-screen" id="loadingScreen">
                <div class="loading-spinner"></div>
                <div class="loading-text">Loading secure content...</div>
                <div class="loading-subtext">Please wait while we establish connection</div>
            </div>
            
            <div class="error-message" id="errorMessage">
                <div class="error-title">⚠️ Connection Error</div>
                <div id="errorText">Failed to load content</div>
                <button class="refresh-btn" onclick="location.reload()">Try Again</button>
            </div>
            
            <iframe 
                id="main-frame"
                src="/proxy"
                sandbox="allow-same-origin allow-scripts allow-popups allow-forms allow-modals allow-top-navigation allow-downloads allow-popups-to-escape-sandbox allow-storage-access-by-user-activation"
                referrerpolicy="no-referrer"
                importance="high"
                loading="eager">
            </iframe>
        </div>
    </div>

    <script>
        (function() {
            // Anti-detection
            Object.defineProperties(navigator, {
                webdriver: { get: () => undefined },
                plugins: { get: () => [1, 2, 3, 4, 5] },
                languages: { get: () => ['en-US', 'en', 'hi'] }
            });
            
            if (!window.chrome) {
                window.chrome = { runtime: {} };
            }

            const iframe = document.getElementById('main-frame');
            const loadingScreen = document.getElementById('loadingScreen');
            const errorMessage = document.getElementById('errorMessage');
            
            let retryCount = 0;
            const maxRetries = 3;

            function showError(msg) {
                document.getElementById('errorText').textContent = msg;
                errorMessage.classList.add('show');
                loadingScreen.classList.add('hidden');
            }

            // Handle iframe load
            iframe.onload = function() {
                console.log('Iframe loaded successfully');
                loadingScreen.classList.add('hidden');
                errorMessage.classList.remove('show');
                
                // Try to modify iframe content
                try {
                    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                    if (iframeDoc) {
                        // Add meta tags for better rendering
                        const meta = iframeDoc.createElement('meta');
                        meta.name = 'viewport';
                        meta.content = 'width=device-width, initial-scale=1.0';
                        iframeDoc.head.appendChild(meta);
                    }
                } catch(e) {
                    // Cross-origin - ignore
                }
            };

            // Handle iframe error
            iframe.onerror = function() {
                if (retryCount < maxRetries) {
                    retryCount++;
                    console.log(`Retry ${retryCount}/${maxRetries}`);
                    setTimeout(() => {
                        iframe.src = '/proxy?retry=' + retryCount;
                    }, 2000 * retryCount);
                } else {
                    showError('Failed to load content. Please refresh.');
                }
            };

            // Timeout handler
            setTimeout(() => {
                try {
                    if (iframe.contentWindow && iframe.contentWindow.location.href === 'about:blank') {
                        showError('Loading timeout. Please refresh.');
                    }
                } catch(e) {
                    showError('Connection error. Please refresh.');
                }
            }, 10000);

            // Handle visibility change
            document.addEventListener('visibilitychange', function() {
                if (!document.hidden) {
                    try {
                        if (iframe.contentWindow && iframe.contentWindow.location.href === 'about:blank') {
                            iframe.src = '/proxy';
                        }
                    } catch(e) {}
                }
            });

        })();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Main page"""
    response = make_response(render_template_string(HTML_TEMPLATE))
    
    # Headers for Render
    response.headers['X-Frame-Options'] = 'ALLOWALL'
    response.headers['Content-Security-Policy'] = "frame-ancestors *; default-src * 'unsafe-inline' 'unsafe-eval' data: blob:; script-src * 'unsafe-inline' 'unsafe-eval'; connect-src *; img-src * data:; style-src * 'unsafe-inline';"
    response.headers['Access-Control-Allow-Origin'] = '*'
    
    return response

@app.route('/proxy')
@app.route('/proxy/<path:path>')
def proxy(path=''):
    """Proxy endpoint to load the target website"""
    try:
        # Target URL
        target_url = 'https://kimstress.st/login'
        
        # Random parameters to bypass cache
        random_param = f'?r={random.randint(1000, 9999)}&t={datetime.now().timestamp()}'
        
        # Headers to mimic real browser
        headers = {
            'User-Agent': random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Referer': 'https://www.google.com/'
        }
        
        # Make request
        session = requests.Session()
        response = session.get(target_url + random_param, headers=headers, timeout=15, allow_redirects=True)
        
        # Get content
        content = response.content
        
        # Replace URLs
        content = content.replace(b'src="/', b'src="https://kimstress.st/')
        content = content.replace(b"src='/", b"src='https://kimstress.st/")
        content = content.replace(b'href="/', b'href="https://kimstress.st/')
        content = content.replace(b"href='/", b"href='https://kimstress.st/")
        content = content.replace(b'url("/', b'url("https://kimstress.st/')
        content = content.replace(b"url('/", b"url('https://kimstress.st/")
        content = content.replace(b'@import "/', b'@import "https://kimstress.st/')
        content = content.replace(b"@import '/", b"@import 'https://kimstress.st/")
        
        # Add base tag
        if b'<head>' in content.lower():
            base_tag = b'<base href="https://kimstress.st/">'
            content = content.replace(b'<head>', b'<head>' + base_tag)
        
        # Create response
        proxy_response = make_response(content)
        
        # Copy cookies
        for cookie in response.cookies:
            proxy_response.set_cookie(cookie.name, cookie.value, domain=None, path='/')
        
        # Set headers
        proxy_response.headers['Content-Type'] = response.headers.get('Content-Type', 'text/html; charset=utf-8')
        proxy_response.headers['Access-Control-Allow-Origin'] = '*'
        proxy_response.headers['X-Frame-Options'] = 'ALLOWALL'
        
        return proxy_response
        
    except requests.exceptions.Timeout:
        return "Connection timeout. Please refresh.", 504
    except requests.exceptions.ConnectionError:
        return "Connection error. Please check your internet.", 502
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}

@app.after_request
def add_headers(response):
    """Add headers to all responses"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = '*'
    return response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
