import os
import random
import requests
import gzip
from flask import Flask, render_template_string, make_response
from datetime import datetime

app = Flask(__name__)

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
        .header {
            background: #1a1a1a;
            padding: 8px 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .dots {
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
            color: #fff;
            padding: 6px 15px;
            border-radius: 20px;
            font-size: 14px;
        }
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
            background: white;
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 10;
        }
        .loading.hidden {
            display: none;
        }
        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .error {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
            display: none;
            z-index: 20;
        }
        .error.show {
            display: block;
        }
        .error button {
            background: #3498db;
            color: white;
            border: none;
            padding: 8px 20px;
            border-radius: 4px;
            margin-top: 10px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="dots">
                <div class="dot red"></div>
                <div class="dot yellow"></div>
                <div class="dot green"></div>
            </div>
            <div class="address-bar">
                🔒 kimstress.st/login
            </div>
        </div>
        
        <div class="iframe-container">
            <div class="loading" id="loading">
                <div class="spinner"></div>
            </div>
            
            <div class="error" id="error">
                <div style="color: #e74c3c; margin-bottom: 10px;">⚠️ Connection Error</div>
                <div id="errorText">Failed to load website</div>
                <button onclick="location.reload()">Retry</button>
            </div>
            
            <iframe 
                id="main-frame"
                src="/proxy"
                sandbox="allow-same-origin allow-scripts allow-popups allow-forms allow-modals allow-top-navigation"
                referrerpolicy="no-referrer"
                style="width: 100%; height: 100%;">
            </iframe>
        </div>
    </div>

    <script>
        const iframe = document.getElementById('main-frame');
        const loading = document.getElementById('loading');
        const error = document.getElementById('error');
        
        let retryCount = 0;
        const maxRetries = 3;
        
        iframe.onload = function() {
            loading.classList.add('hidden');
            error.classList.remove('show');
            console.log('Iframe loaded successfully');
        };
        
        iframe.onerror = function() {
            if (retryCount < maxRetries) {
                retryCount++;
                console.log('Retrying...', retryCount);
                setTimeout(() => {
                    iframe.src = '/proxy?retry=' + retryCount;
                }, 2000);
            } else {
                loading.classList.add('hidden');
                error.classList.add('show');
                document.getElementById('errorText').innerText = 'Failed after ' + maxRetries + ' attempts';
            }
        };
        
        // Timeout after 10 seconds
        setTimeout(() => {
            try {
                if (iframe.contentWindow && iframe.contentWindow.location.href === 'about:blank') {
                    iframe.onerror();
                }
            } catch(e) {
                // Cross-origin error, ignore
            }
        }, 10000);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    response = make_response(render_template_string(HTML_TEMPLATE))
    response.headers['X-Frame-Options'] = 'ALLOWALL'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Content-Security-Policy'] = "frame-ancestors *; default-src * 'unsafe-inline' 'unsafe-eval'; script-src * 'unsafe-inline' 'unsafe-eval'; connect-src *; img-src * data:; style-src * 'unsafe-inline';"
    return response

@app.route('/proxy')
def proxy():
    try:
        # Target URL
        url = 'https://kimstress.st/login'
        
        # Headers to mimic real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        # Make request
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=15, allow_redirects=True)
        
        # Get content and handle compression
        content = response.content
        
        # Check if content is gzipped
        if response.headers.get('Content-Encoding') == 'gzip':
            try:
                content = gzip.decompress(content)
            except:
                pass
        
        # Decode if it's bytes
        if isinstance(content, bytes):
            try:
                # Try to decode as utf-8
                content = content.decode('utf-8', errors='ignore')
            except:
                # If decode fails, keep as bytes
                pass
        
        # Fix relative URLs
        if isinstance(content, str):
            content = content.replace('src="/', 'src="https://kimstress.st/')
            content = content.replace("src='/", "src='https://kimstress.st/")
            content = content.replace('href="/', 'href="https://kimstress.st/')
            content = content.replace("href='/", "href='https://kimstress.st/")
            content = content.replace('url("/', 'url("https://kimstress.st/')
            content = content.replace("url('/", "url('https://kimstress.st/")
            content = content.replace('@import "/', '@import "https://kimstress.st/')
            content = content.replace("@import '/", "@import 'https://kimstress.st/")
            
            # Add base tag
            if '<head>' in content:
                content = content.replace('<head>', '<head><base href="https://kimstress.st/">')
            
            # Convert back to bytes
            content = content.encode('utf-8')
        
        # Create response
        proxy_response = make_response(content)
        
        # Copy cookies
        for cookie in response.cookies:
            proxy_response.set_cookie(cookie.name, cookie.value, domain=None, path='/')
        
        # Set content type
        proxy_response.headers['Content-Type'] = 'text/html; charset=utf-8'
        proxy_response.headers['Access-Control-Allow-Origin'] = '*'
        proxy_response.headers['X-Frame-Options'] = 'ALLOWALL'
        
        # Remove content encoding to prevent double compression
        proxy_response.headers.pop('Content-Encoding', None)
        
        return proxy_response
        
    except requests.exceptions.Timeout:
        return "Connection timeout. Please refresh.", 504
    except requests.exceptions.ConnectionError:
        return "Connection error. Please check your internet.", 502
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/health')
def health():
    return {'status': 'healthy', 'time': str(datetime.now())}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
