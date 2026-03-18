import os
import requests
import gzip
from flask import Flask, render_template_string, request, make_response
from urllib.parse import urlparse, quote

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kimstress</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f0f2f5;
            height: 100vh;
            overflow: hidden;
        }
        .container {
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
        }
        .toolbar {
            background: #1a1a1a;
            padding: 8px 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .dots {
            display: flex;
            gap: 6px;
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
            color: #aaa;
            padding: 6px 15px;
            border-radius: 20px;
            font-size: 13px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .lock {
            color: #4caf50;
            font-size: 14px;
        }
        .url {
            color: #fff;
            flex: 1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .reload {
            background: transparent;
            border: none;
            color: #aaa;
            cursor: pointer;
            font-size: 16px;
            padding: 0 5px;
        }
        .reload:hover { color: #fff; }
        .iframe-container {
            flex: 1;
            background: white;
            position: relative;
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
            background: rgba(255,255,255,0.98);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 1000;
            gap: 15px;
            display: none;
        }
        .loading.show { display: flex; }
        .spinner {
            width: 45px;
            height: 45px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .loading-text {
            color: #666;
            font-size: 14px;
        }
        .error {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 30px 40px;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            text-align: center;
            display: none;
            z-index: 1001;
            min-width: 300px;
        }
        .error.show { display: block; }
        .error-icon {
            font-size: 48px;
            margin-bottom: 15px;
        }
        .error-title {
            font-size: 18px;
            font-weight: 600;
            color: #e74c3c;
            margin-bottom: 10px;
        }
        .error-message {
            color: #666;
            font-size: 14px;
            margin-bottom: 20px;
        }
        .error button {
            background: #3498db;
            color: white;
            border: none;
            padding: 10px 30px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
        }
        .error button:hover { background: #2980b9; }
    </style>
</head>
<body>
    <div class="container">
        <div class="toolbar">
            <div class="dots">
                <div class="dot red"></div>
                <div class="dot yellow"></div>
                <div class="dot green"></div>
            </div>
            <div class="address-bar">
                <span class="lock">🔒</span>
                <span class="url" id="urlDisplay">kimstress.st/login</span>
                <button class="reload" onclick="reloadPage()">↻</button>
            </div>
        </div>
        
        <div class="iframe-container">
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <div class="loading-text">Loading secure content...</div>
            </div>
            
            <div class="error" id="error">
                <div class="error-icon">⚠️</div>
                <div class="error-title">Connection Error</div>
                <div class="error-message" id="errorMessage">Unable to load website</div>
                <button onclick="retry()">Try Again</button>
            </div>
            
            <iframe 
                id="main-frame"
                src="/proxy/{{ encoded_url }}"
                sandbox="allow-same-origin allow-scripts allow-popups allow-forms allow-modals allow-top-navigation allow-downloads allow-popups-to-escape-sandbox"
                referrerpolicy="no-referrer"
                style="width: 100%; height: 100%;">
            </iframe>
        </div>
    </div>

    <script>
        const iframe = document.getElementById('main-frame');
        const loading = document.getElementById('loading');
        const error = document.getElementById('error');
        const errorMessage = document.getElementById('errorMessage');
        const urlDisplay = document.getElementById('urlDisplay');
        
        let retryCount = 0;
        const maxRetries = 3;
        
        function reloadPage() {
            loading.classList.add('show');
            error.classList.remove('show');
            iframe.src = iframe.src;
        }
        
        function retry() {
            error.classList.remove('show');
            loading.classList.add('show');
            iframe.src = iframe.src;
        }
        
        iframe.onload = function() {
            loading.classList.remove('show');
            error.classList.remove('show');
            retryCount = 0;
            
            try {
                // Try to update URL display
                const iframeUrl = iframe.contentWindow.location.href;
                if (iframeUrl && iframeUrl !== 'about:blank') {
                    const url = new URL(iframeUrl);
                    urlDisplay.textContent = url.hostname + url.pathname;
                }
            } catch(e) {
                // Cross-origin, ignore
            }
        };
        
        iframe.onerror = function() {
            if (retryCount < maxRetries) {
                retryCount++;
                loading.classList.add('show');
                setTimeout(() => {
                    iframe.src = iframe.src.split('?')[0] + '?retry=' + retryCount;
                }, 2000 * retryCount);
            } else {
                loading.classList.remove('show');
                error.classList.add('show');
                errorMessage.textContent = 'Failed to load after ' + maxRetries + ' attempts';
            }
        };
        
        // Set timeout
        setTimeout(() => {
            try {
                if (iframe.contentWindow && iframe.contentWindow.location.href === 'about:blank') {
                    iframe.onerror();
                }
            } catch(e) {
                // Cross-origin, ignore
            }
        }, 15000);
        
        // Handle visibility change
        document.addEventListener('visibilitychange', function() {
            if (!document.hidden && !loading.classList.contains('show') && !error.classList.contains('show')) {
                try {
                    if (iframe.contentWindow && iframe.contentWindow.location.href === 'about:blank') {
                        iframe.src = iframe.src;
                    }
                } catch(e) {}
            }
        });
    </script>
</body>
</html>
'''

# Target URL (fixed)
TARGET_URL = "https://kimstress.st/login?redirect=%2Fdashboard&__cf_chl_rt_tk=HEBIpVLdsWpuMFNkqAnQTkVE.2QpsO7WH.MNaDn.K40-1773855114-1.0.1.1-uKYdfqVSH3YdlJNDJ8InInyUeAqj5jDM8qk3zXSkJfk"

@app.route('/')
def index():
    from urllib.parse import quote
    encoded_url = quote(TARGET_URL, safe='')
    return render_template_string(HTML_TEMPLATE, encoded_url=encoded_url)

@app.route('/proxy/<path:encoded_url>')
def proxy(encoded_url):
    try:
        # Decode URL
        from urllib.parse import unquote
        target_url = unquote(encoded_url)
        
        # Remove retry parameter if present
        if '?retry=' in target_url:
            target_url = target_url.split('?retry=')[0]
        
        # Headers to mimic real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
            'Pragma': 'no-cookie',
            'Referer': 'https://www.google.com/'
        }
        
        # Add cookies from URL if present
        cookies = {}
        if '__cf_chl_rt_tk' in target_url:
            from urllib.parse import parse_qs, urlparse
            parsed = urlparse(target_url)
            params = parse_qs(parsed.query)
            if '__cf_chl_rt_tk' in params:
                cookies['__cf_chl_rt_tk'] = params['__cf_chl_rt_tk'][0]
        
        # Make request
        session = requests.Session()
        response = session.get(target_url, headers=headers, cookies=cookies, timeout=30, allow_redirects=True)
        
        # Get content
        content = response.content
        
        # Handle compression
        if response.headers.get('Content-Encoding') == 'gzip':
            try:
                content = gzip.decompress(content)
            except:
                pass
        elif response.headers.get('Content-Encoding') == 'br':
            try:
                import brotli
                content = brotli.decompress(content)
            except:
                pass
        
        # Decode content
        if isinstance(content, bytes):
            try:
                content = content.decode('utf-8', errors='ignore')
            except:
                try:
                    content = content.decode('latin-1', errors='ignore')
                except:
                    content = str(content)
        
        # Fix URLs
        base_url = "https://kimstress.st"
        
        # Replace all relative URLs
        replacements = [
            ('src="/', f'src="{base_url}/'),
            ("src='/", f"src='{base_url}/"),
            ('href="/', f'href="{base_url}/'),
            ("href='/", f"href='{base_url}/"),
            ('url("/', f'url("{base_url}/'),
            ("url('/", f"url('{base_url}/"),
            ('@import "/', f'@import "{base_url}/'),
            ("@import '/", f"@import '{base_url}/"),
            ('action="/', f'action="{base_url}/'),
            ("action='/", f"action='{base_url}/"),
        ]
        
        for old, new in replacements:
            content = content.replace(old, new)
        
        # Add base tag
        if '<head>' in content:
            content = content.replace('<head>', f'<head><base href="{base_url}/">')
        else:
            content = f'<base href="{base_url}/">' + content
        
        # Convert back to bytes
        content = content.encode('utf-8')
        
        # Create response
        proxy_response = make_response(content)
        
        # Copy all cookies
        for cookie in response.cookies:
            proxy_response.set_cookie(
                cookie.name, 
                cookie.value,
                domain=None,
                path='/',
                secure=False,
                httponly=False
            )
        
        # Set headers
        content_type = response.headers.get('Content-Type', 'text/html; charset=utf-8')
        if 'text/html' in content_type:
            proxy_response.headers['Content-Type'] = 'text/html; charset=utf-8'
        else:
            proxy_response.headers['Content-Type'] = content_type
        
        proxy_response.headers['Access-Control-Allow-Origin'] = '*'
        proxy_response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        proxy_response.headers['Access-Control-Allow-Headers'] = '*'
        proxy_response.headers['X-Frame-Options'] = 'ALLOWALL'
        
        # Remove encoding headers
        proxy_response.headers.pop('Content-Encoding', None)
        proxy_response.headers.pop('Content-Length', None)
        
        return proxy_response
        
    except requests.exceptions.Timeout:
        return "Connection timeout. Please refresh.", 504
    except requests.exceptions.ConnectionError:
        return "Connection error. Website may be down.", 502
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/health')
def health():
    return {'status': 'healthy', 'url': TARGET_URL[:50] + '...'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
