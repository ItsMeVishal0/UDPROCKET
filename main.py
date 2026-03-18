import os
import re
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
from werkzeug.utils import secure_filename
from time import time

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
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
]

# Session storage
session_storage = defaultdict(dict)
app_start_time = datetime.now()

# Cleanup old sessions periodically
def cleanup_sessions():
    """Remove expired sessions"""
    while True:
        try:
            now = datetime.now()
            expired = [sid for sid, data in session_storage.items() 
                      if (now - data.get('last_used', now)).seconds > 3600]
            for sid in expired:
                del session_storage[sid]
            threading.Event().wait(300)  # Run every 5 minutes
        except:
            pass

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_sessions, daemon=True)
cleanup_thread.start()

# HTML Template with advanced features
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Kimstress • Secure Gateway</title>
    <style>
        /* Modern Reset */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }

        /* Variables */
        :root {
            --bg-primary: #1a1a1a;
            --bg-secondary: #2d2d2d;
            --text-primary: #ffffff;
            --text-secondary: #b0b0b0;
            --accent: #4CAF50;
            --accent-hover: #45a049;
            --error: #f44336;
            --success: #4CAF50;
            --warning: #ff9800;
            --border: #404040;
            --shadow: rgba(0, 0, 0, 0.3);
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: var(--bg-primary);
            height: 100vh;
            overflow: hidden;
            color: var(--text-primary);
        }

        /* Main Container */
        .browser {
            display: flex;
            flex-direction: column;
            height: 100vh;
            background: var(--bg-primary);
        }

        /* Browser Chrome */
        .browser-chrome {
            background: var(--bg-primary);
            border-bottom: 1px solid var(--border);
            padding: 8px 12px;
        }

        /* Window Controls */
        .window-controls {
            display: flex;
            gap: 8px;
            margin-bottom: 8px;
        }

        .window-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }

        .window-dot.red { background: #ff5f56; }
        .window-dot.yellow { background: #ffbd2e; }
        .window-dot.green { background: #27c93f; }

        /* Navigation Bar */
        .nav-bar {
            display: flex;
            align-items: center;
            gap: 10px;
            background: var(--bg-secondary);
            padding: 6px 12px;
            border-radius: 8px;
            margin-top: 4px;
        }

        .nav-button {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            font-size: 18px;
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 4px;
            transition: all 0.2s;
        }

        .nav-button:hover {
            background: rgba(255, 255, 255, 0.1);
            color: var(--text-primary);
        }

        .nav-button:disabled {
            opacity: 0.3;
            cursor: not-allowed;
        }

        /* Address Bar */
        .address-bar {
            flex: 1;
            display: flex;
            align-items: center;
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 6px 12px;
            gap: 8px;
        }

        .address-bar.locked .lock-icon {
            color: var(--success);
        }

        .lock-icon {
            font-size: 14px;
            color: var(--text-secondary);
        }

        .address-input {
            flex: 1;
            background: transparent;
            border: none;
            color: var(--text-primary);
            font-size: 14px;
            outline: none;
        }

        .address-input::placeholder {
            color: var(--text-secondary);
        }

        /* Security Badge */
        .security-badge {
            display: flex;
            align-items: center;
            gap: 5px;
            padding: 4px 8px;
            background: rgba(76, 175, 80, 0.1);
            border-radius: 4px;
            color: var(--success);
            font-size: 12px;
        }

        /* Main Content Area */
        .content-area {
            flex: 1;
            position: relative;
            background: white;
            overflow: hidden;
        }

        #main-frame {
            width: 100%;
            height: 100%;
            border: none;
            background: white;
            display: block;
        }

        /* Loading Overlay */
        .loading-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
            transition: opacity 0.3s ease;
            opacity: 1;
            pointer-events: all;
        }

        .loading-overlay.hidden {
            opacity: 0;
            pointer-events: none;
        }

        .loader {
            text-align: center;
            color: white;
        }

        .loader-spinner {
            width: 60px;
            height: 60px;
            border: 4px solid rgba(255, 255, 255, 0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .loader-text {
            font-size: 18px;
            font-weight: 500;
            margin-bottom: 8px;
        }

        .loader-subtext {
            font-size: 14px;
            opacity: 0.8;
        }

        /* Progress Bar */
        .progress-bar {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: rgba(255, 255, 255, 0.2);
            z-index: 1001;
        }

        .progress-fill {
            height: 100%;
            background: var(--accent);
            width: 0%;
            transition: width 0.3s ease;
        }

        /* Error Modal */
        .error-modal {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            border-radius: 12px;
            padding: 30px;
            max-width: 400px;
            width: 90%;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            z-index: 2000;
            display: none;
        }

        .error-modal.show {
            display: block;
        }

        .error-icon {
            font-size: 48px;
            margin-bottom: 15px;
        }

        .error-title {
            font-size: 20px;
            font-weight: 600;
            color: var(--error);
            margin-bottom: 10px;
        }

        .error-message {
            color: #666;
            font-size: 14px;
            margin-bottom: 20px;
            line-height: 1.5;
        }

        .error-details {
            background: #f5f5f5;
            padding: 10px;
            border-radius: 6px;
            font-family: monospace;
            font-size: 12px;
            color: #333;
            margin-bottom: 20px;
            word-break: break-all;
        }

        .error-actions {
            display: flex;
            gap: 10px;
            justify-content: center;
        }

        .error-btn {
            padding: 10px 25px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }

        .error-btn.primary {
            background: var(--accent);
            color: white;
        }

        .error-btn.primary:hover {
            background: var(--accent-hover);
        }

        .error-btn.secondary {
            background: #e0e0e0;
            color: #333;
        }

        .error-btn.secondary:hover {
            background: #d0d0d0;
        }

        /* Status Bar */
        .status-bar {
            background: var(--bg-secondary);
            padding: 4px 12px;
            font-size: 12px;
            color: var(--text-secondary);
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-top: 1px solid var(--border);
        }

        .status-left {
            display: flex;
            gap: 15px;
        }

        .status-item {
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }

        .status-dot.secure { background: var(--success); }
        .status-dot.insecure { background: var(--error); }
        .status-dot.loading { background: var(--warning); }

        /* Context Menu */
        .context-menu {
            position: absolute;
            background: white;
            border-radius: 8px;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.2);
            padding: 5px 0;
            min-width: 150px;
            z-index: 3000;
            display: none;
        }

        .context-menu.show {
            display: block;
        }

        .context-menu-item {
            padding: 8px 15px;
            font-size: 13px;
            color: #333;
            cursor: pointer;
            transition: background 0.2s;
        }

        .context-menu-item:hover {
            background: #f0f0f0;
        }

        .context-menu-divider {
            height: 1px;
            background: #e0e0e0;
            margin: 5px 0;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .security-badge span:not(.lock-icon) {
                display: none;
            }
            
            .address-bar {
                padding: 4px 8px;
            }
            
            .error-actions {
                flex-direction: column;
            }
        }

        /* Animations */
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        .pulse {
            animation: pulse 2s infinite;
        }

        /* Toast Notifications */
        .toast-container {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 4000;
        }

        .toast {
            background: white;
            border-radius: 8px;
            padding: 12px 20px;
            margin-top: 10px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
            display: flex;
            align-items: center;
            gap: 10px;
            animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        .toast.success { border-left: 4px solid var(--success); }
        .toast.error { border-left: 4px solid var(--error); }
        .toast.warning { border-left: 4px solid var(--warning); }
    </style>
</head>
<body>
    <div class="browser">
        <!-- Browser Chrome -->
        <div class="browser-chrome">
            <div class="window-controls">
                <div class="window-dot red"></div>
                <div class="window-dot yellow"></div>
                <div class="window-dot green"></div>
            </div>
            
            <div class="nav-bar">
                <button class="nav-button" onclick="history.back()" id="backBtn" disabled>←</button>
                <button class="nav-button" onclick="history.forward()" id="forwardBtn" disabled>→</button>
                <button class="nav-button" onclick="refresh()">↻</button>
                
                <div class="address-bar locked" id="addressBar">
                    <span class="lock-icon">🔒</span>
                    <input type="text" class="address-input" id="addressInput" value="{{ target_url }}" readonly>
                    <div class="security-badge">
                        <span>🔒</span>
                        <span>Secure</span>
                    </div>
                </div>
                
                <button class="nav-button" onclick="showMenu(event)">⋮</button>
            </div>
        </div>

        <!-- Main Content -->
        <div class="content-area">
            <!-- Progress Bar -->
            <div class="progress-bar" id="progressBar">
                <div class="progress-fill" id="progressFill"></div>
            </div>

            <!-- Loading Overlay -->
            <div class="loading-overlay" id="loadingOverlay">
                <div class="loader">
                    <div class="loader-spinner"></div>
                    <div class="loader-text">Establishing secure connection...</div>
                    <div class="loader-subtext" id="loadingStatus">Connecting to {{ target_domain }}</div>
                </div>
            </div>

            <!-- Error Modal -->
            <div class="error-modal" id="errorModal">
                <div class="error-icon">⚠️</div>
                <div class="error-title" id="errorTitle">Connection Error</div>
                <div class="error-message" id="errorMessage">Unable to load the website</div>
                <div class="error-details" id="errorDetails"></div>
                <div class="error-actions">
                    <button class="error-btn primary" onclick="retry()">Try Again</button>
                    <button class="error-btn secondary" onclick="closeError()">Dismiss</button>
                </div>
            </div>

            <!-- Iframe -->
            <iframe 
                id="main-frame"
                src="/proxy/{{ encoded_url }}"
                sandbox="allow-same-origin allow-scripts allow-popups allow-forms allow-modals allow-top-navigation allow-downloads allow-popups-to-escape-sandbox allow-storage-access-by-user-activation"
                referrerpolicy="no-referrer"
                importance="high"
                loading="eager">
            </iframe>
        </div>

        <!-- Status Bar -->
        <div class="status-bar">
            <div class="status-left">
                <div class="status-item">
                    <span class="status-dot secure" id="statusDot"></span>
                    <span id="statusText">Secure Connection</span>
                </div>
                <div class="status-item" id="loadTime">Load time: 0ms</div>
            </div>
            <div class="status-right">
                <span id="timestamp">{{ timestamp }}</span>
            </div>
        </div>

        <!-- Context Menu -->
        <div class="context-menu" id="contextMenu">
            <div class="context-menu-item" onclick="copyUrl()">Copy URL</div>
            <div class="context-menu-item" onclick="openInNewTab()">Open in new tab</div>
            <div class="context-menu-divider"></div>
            <div class="context-menu-item" onclick="viewSource()">View page source</div>
            <div class="context-menu-item" onclick="inspect()">Inspect element</div>
        </div>

        <!-- Toast Container -->
        <div class="toast-container" id="toastContainer"></div>
    </div>

    <script>
        // State management
        let state = {
            loading: true,
            error: null,
            loadTime: 0,
            history: [],
            currentIndex: -1,
            retryCount: 0,
            maxRetries: 3,
            startTime: Date.now()
        };

        // DOM Elements
        const iframe = document.getElementById('main-frame');
        const loadingOverlay = document.getElementById('loadingOverlay');
        const errorModal = document.getElementById('errorModal');
        const progressFill = document.getElementById('progressFill');
        const addressInput = document.getElementById('addressInput');
        const backBtn = document.getElementById('backBtn');
        const forwardBtn = document.getElementById('forwardBtn');
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');
        const loadTimeEl = document.getElementById('loadTime');
        const loadingStatus = document.getElementById('loadingStatus');

        // Initialize
        window.onload = function() {
            state.startTime = Date.now();
            updateLoadingStatus('Connecting...');
            
            // Anti-detection
            Object.defineProperties(navigator, {
                webdriver: { get: () => undefined },
                plugins: { get: () => [1, 2, 3, 4, 5] },
                languages: { get: () => ['en-US', 'en'] }
            });
            
            if (!window.chrome) {
                window.chrome = { runtime: {} };
            }
        };

        // Iframe event handlers
        iframe.onload = function() {
            state.loading = false;
            state.loadTime = Date.now() - state.startTime;
            state.retryCount = 0;
            
            loadingOverlay.classList.add('hidden');
            errorModal.classList.remove('show');
            
            updateStatus('connected');
            updateLoadTime();
            
            try {
                const iframeUrl = iframe.contentWindow.location.href;
                if (iframeUrl && iframeUrl !== 'about:blank') {
                    addressInput.value = iframeUrl;
                }
            } catch(e) {
                // Cross-origin
            }
        };

        iframe.onerror = function(e) {
            handleError('Failed to load website', e);
        };

        // Progress simulation
        function updateProgress(percent) {
            progressFill.style.width = percent + '%';
        }

        let progress = 0;
        const progressInterval = setInterval(() => {
            if (state.loading && progress < 90) {
                progress += Math.random() * 10;
                updateProgress(Math.min(progress, 90));
            }
        }, 200);

        // Error handling
        function handleError(message, details = null) {
            state.loading = false;
            state.error = message;
            
            if (state.retryCount < state.maxRetries) {
                state.retryCount++;
                updateLoadingStatus(`Retrying (${state.retryCount}/${state.maxRetries})...`);
                setTimeout(() => {
                    refresh();
                }, 2000 * state.retryCount);
            } else {
                loadingOverlay.classList.add('hidden');
                errorModal.classList.add('show');
                document.getElementById('errorTitle').textContent = 'Connection Error';
                document.getElementById('errorMessage').textContent = message;
                document.getElementById('errorDetails').textContent = details || 'Maximum retry attempts reached';
            }
            
            updateStatus('error');
        }

        // Navigation functions
        function refresh() {
            state.loading = true;
            state.startTime = Date.now();
            progress = 0;
            updateProgress(0);
            loadingOverlay.classList.remove('hidden');
            updateLoadingStatus('Refreshing...');
            
            const currentSrc = iframe.src;
            iframe.src = 'about:blank';
            setTimeout(() => {
                iframe.src = currentSrc;
            }, 100);
        }

        function updateLoadingStatus(text) {
            loadingStatus.textContent = text;
        }

        function updateStatus(status) {
            if (status === 'connected') {
                statusDot.className = 'status-dot secure';
                statusText.textContent = 'Secure Connection';
            } else if (status === 'error') {
                statusDot.className = 'status-dot insecure';
                statusText.textContent = 'Connection Error';
            } else {
                statusDot.className = 'status-dot loading';
                statusText.textContent = 'Loading...';
            }
        }

        function updateLoadTime() {
            loadTimeEl.textContent = `Load time: ${state.loadTime}ms`;
        }

        // Address bar functions
        addressInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                let url = this.value;
                if (!url.startsWith('http')) {
                    url = 'https://' + url;
                }
                window.location.href = '/?url=' + encodeURIComponent(url);
            }
        });

        // Context menu
        function showMenu(event) {
            const menu = document.getElementById('contextMenu');
            menu.style.display = 'block';
            menu.style.left = event.pageX + 'px';
            menu.style.top = event.pageY + 'px';
            
            setTimeout(() => {
                document.addEventListener('click', function hideMenu() {
                    menu.style.display = 'none';
                    document.removeEventListener('click', hideMenu);
                });
            }, 100);
        }

        // Toast notifications
        function showToast(message, type = 'info') {
            const container = document.getElementById('toastContainer');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.innerHTML = `
                <span>${message}</span>
                <button onclick="this.parentElement.remove()" style="background:none; border:none; cursor:pointer;">✕</button>
            `;
            container.appendChild(toast);
            
            setTimeout(() => {
                toast.remove();
            }, 5000);
        }

        // Utility functions
        function copyUrl() {
            navigator.clipboard.writeText(addressInput.value);
            showToast('URL copied to clipboard', 'success');
        }

        function openInNewTab() {
            window.open(addressInput.value, '_blank');
        }

        function viewSource() {
            try {
                const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                const source = iframeDoc.documentElement.outerHTML;
                const win = window.open();
                win.document.write('<pre>' + source.replace(/</g, '&lt;') + '</pre>');
            } catch(e) {
                showToast('Cannot view source: Cross-origin restrictions', 'error');
            }
        }

        function inspect() {
            showToast('Inspect element is not available in proxy mode', 'warning');
        }

        function retry() {
            errorModal.classList.remove('show');
            refresh();
        }

        function closeError() {
            errorModal.classList.remove('show');
        }

        // Handle visibility change
        document.addEventListener('visibilitychange', function() {
            if (!document.hidden && state.error) {
                refresh();
            }
        });

        // Handle offline/online
        window.addEventListener('online', function() {
            showToast('Connection restored', 'success');
            refresh();
        });

        window.addEventListener('offline', function() {
            showToast('No internet connection', 'error');
        });

        // Periodic check
        setInterval(() => {
            try {
                if (iframe.contentWindow && iframe.contentWindow.location.href === 'about:blank' && !state.loading) {
                    refresh();
                }
            } catch(e) {}
        }, 30000);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Main page with advanced proxy"""
    target_url = request.args.get('url', TARGET_URL)
    from urllib.parse import quote
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
    """Advanced proxy handler"""
    try:
        # Decode URL
        from urllib.parse import unquote
        if encoded_url:
            target_url = unquote(encoded_url)
        else:
            target_url = request.args.get('url', TARGET_URL)
        
        # Clean URL
        target_url = target_url.split('#')[0].split('?retry=')[0]
        
        # Parse URL
        parsed = urlparse(target_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Generate session ID
        session_id = request.cookies.get('session_id') or hashlib.md5(os.urandom(16)).hexdigest()
        
        # Get or create session
        if session_id not in session_storage:
            session_storage[session_id] = {
                'cookies': {},
                'headers': {},
                'last_used': datetime.now()
            }
        
        # Update session
        session_storage[session_id]['last_used'] = datetime.now()
        
        # Prepare headers
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
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
            'Referer': random.choice(['https://www.google.com/', 'https://www.bing.com/', 'https://duckduckgo.com/']),
            'DNT': '1'
        }
        
        # Add session cookies
        cookies = session_storage[session_id].get('cookies', {})
        
        # Extract cookies from URL
        if '__cf_chl_rt_tk' in target_url:
            params = parse_qs(parsed.query)
            if '__cf_chl_rt_tk' in params:
                cookies['__cf_chl_rt_tk'] = params['__cf_chl_rt_tk'][0]
        
        # Make request
        session = requests.Session()
        response = session.get(
            target_url,
            headers=headers,
            cookies=cookies,
            timeout=30,
            allow_redirects=True,
            verify=False  # For HTTPS issues
        )
        
        # Save cookies
        for cookie in response.cookies:
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
        
        # Detect content type
        content_type = response.headers.get('Content-Type', 'text/html; charset=utf-8')
        
        # Process HTML content
        if 'text/html' in content_type:
            # Parse with BeautifulSoup
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
            
            # Fix CSS links
            for link in soup.find_all('link', rel='stylesheet'):
                if link.get('href'):
                    href = link['href']
                    if not href.startswith(('http', 'https', 'data:')):
                        link['href'] = urljoin(base_url, href)
            
            # Add base tag
            if not soup.find('base'):
                base = soup.new_tag('base', href=base_url + '/')
                if soup.head:
                    soup.head.insert(0, base)
                else:
                    head = soup.new_tag('head')
                    head.append(base)
                    if soup.html:
                        soup.html.insert(0, head)
            
            # Add meta tags
            meta = soup.new_tag('meta')
            meta['http-equiv'] = 'Content-Security-Policy'
            meta['content'] = "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:; script-src * 'unsafe-inline' 'unsafe-eval'; connect-src *; img-src * data: blob:; style-src * 'unsafe-inline'; frame-src *;"
            
            if soup.head:
                soup.head.append(meta)
            
            # Convert back to string
            content = str(soup).encode('utf-8')
        
        # Create response
        proxy_response = make_response(content)
        
        # Set cookies
        for name, value in session_storage[session_id]['cookies'].items():
            proxy_response.set_cookie(
                name,
                value,
                domain=None,
                path='/',
                secure=False,
                httponly=False,
                samesite='Lax'
            )
        
        proxy_response.set_cookie('session_id', session_id, max_age=3600, path='/')
        
        # Set headers
        proxy_response.headers['Content-Type'] = content_type.split(';')[0] + '; charset=utf-8'
        proxy_response.headers['Access-Control-Allow-Origin'] = '*'
        proxy_response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        proxy_response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        proxy_response.headers['Access-Control-Allow-Credentials'] = 'true'
        proxy_response.headers['X-Frame-Options'] = 'ALLOWALL'
        proxy_response.headers['X-Content-Type-Options'] = 'nosniff'
        proxy_response.headers['Referrer-Policy'] = 'no-referrer'
        
        # Remove problematic headers
        proxy_response.headers.pop('Content-Encoding', None)
        proxy_response.headers.pop('Content-Length', None)
        proxy_response.headers.pop('Transfer-Encoding', None)
        
        return proxy_response
        
    except requests.exceptions.Timeout:
        return "Connection timeout. The server is not responding.", 504
    except requests.exceptions.ConnectionError:
        return "Connection error. Unable to reach the server.", 502
    except requests.exceptions.SSLError:
        return "SSL Error. There might be an issue with the website's security certificate.", 525
    except Exception as e:
        return f"Proxy error: {str(e)}", 500

@app.route('/health')
def health():
    """Health check with detailed status"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_sessions': len(session_storage),
        'target': TARGET_DOMAIN,
        'uptime': str(datetime.now() - app_start_time)
    }

@app.teardown_appcontext
def close_connection(exception):
    """Clean up after request"""
    pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
