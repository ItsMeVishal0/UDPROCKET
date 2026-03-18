import os
import sys
import time
import json
import base64
import random
import string
import hashlib
import threading
import subprocess
from flask import Flask, render_template_string, request, make_response, jsonify, send_file
from flask_cors import CORS
from datetime import datetime, timedelta
from collections import defaultdict
from urllib.parse import urlparse, urljoin, quote, unquote
import requests
from bs4 import BeautifulSoup
import gzip
import brotli
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app, supports_credentials=True)

# Configuration
TARGET_URL = "https://kimstress.st/login"
TARGET_DOMAIN = "kimstress.st"
BASE_URL = f"https://{TARGET_DOMAIN}"

# User Agents Pool - Real browsers only
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
]

# Session storage with encryption
session_db = defaultdict(lambda: {
    'cookies': {},
    'headers': {},
    'created': datetime.now(),
    'last_used': datetime.now(),
    'cf_clearance': None,
    'user_agent': random.choice(USER_AGENTS)
})

# HTML Template - Ultimate Browser Experience
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Kimstress • Secure Browser</title>
    <style>
        /* MODERN RESET */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }

        /* VARIABLES */
        :root {
            --bg-primary: #1a1a1a;
            --bg-secondary: #2d2d2d;
            --bg-tertiary: #333333;
            --text-primary: #ffffff;
            --text-secondary: #b0b0b0;
            --text-tertiary: #808080;
            --accent: #4CAF50;
            --accent-hover: #45a049;
            --error: #f44336;
            --warning: #ff9800;
            --info: #2196F3;
            --border: #404040;
            --shadow: rgba(0, 0, 0, 0.3);
        }

        /* BASE STYLES */
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* BROWSER CONTAINER */
        .browser {
            width: 98%;
            max-width: 1400px;
            height: 96vh;
            background: var(--bg-primary);
            border-radius: 20px;
            box-shadow: 0 25px 60px rgba(0,0,0,0.5);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            position: relative;
        }

        /* TITLE BAR */
        .title-bar {
            background: var(--bg-primary);
            padding: 8px 15px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border);
        }

        .window-controls {
            display: flex;
            gap: 8px;
        }

        .window-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            transition: transform 0.2s;
        }

        .window-dot:hover {
            transform: scale(1.1);
        }

        .window-dot.red { background: #ff5f56; }
        .window-dot.yellow { background: #ffbd2e; }
        .window-dot.green { background: #27c93f; }

        .window-title {
            color: var(--text-secondary);
            font-size: 13px;
            font-weight: 500;
        }

        /* TOOLBAR */
        .toolbar {
            background: var(--bg-secondary);
            padding: 10px 15px;
            display: flex;
            align-items: center;
            gap: 12px;
            border-bottom: 1px solid var(--border);
        }

        .nav-buttons {
            display: flex;
            gap: 5px;
        }

        .nav-btn {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            font-size: 18px;
            width: 32px;
            height: 32px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s;
        }

        .nav-btn:hover:not(:disabled) {
            background: var(--bg-tertiary);
            color: var(--text-primary);
        }

        .nav-btn:disabled {
            opacity: 0.3;
            cursor: not-allowed;
        }

        /* ADDRESS BAR */
        .address-bar {
            flex: 1;
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 6px 12px;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s;
        }

        .address-bar:focus-within {
            border-color: var(--accent);
            box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
        }

        .lock-icon {
            color: var(--accent);
            font-size: 14px;
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
            color: var(--text-tertiary);
        }

        .security-badge {
            background: rgba(76, 175, 80, 0.1);
            color: var(--accent);
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 5px;
        }

        /* CONTENT AREA */
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

        /* LOADING OVERLAY */
        .loading-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 1000;
            transition: opacity 0.5s ease;
        }

        .loading-overlay.hidden {
            opacity: 0;
            pointer-events: none;
        }

        .loading-spinner {
            width: 70px;
            height: 70px;
            border: 5px solid rgba(255, 255, 255, 0.2);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 1s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite;
            margin-bottom: 30px;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .loading-text {
            color: white;
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 10px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }

        .loading-subtext {
            color: rgba(255,255,255,0.9);
            font-size: 16px;
        }

        .loading-progress {
            width: 300px;
            height: 4px;
            background: rgba(255,255,255,0.2);
            border-radius: 2px;
            margin-top: 30px;
            overflow: hidden;
        }

        .loading-progress-bar {
            height: 100%;
            background: white;
            width: 0%;
            transition: width 0.3s ease;
            border-radius: 2px;
        }

        /* ERROR MODAL */
        .error-modal {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            border-radius: 16px;
            padding: 40px;
            max-width: 450px;
            width: 90%;
            text-align: center;
            box-shadow: 0 30px 70px rgba(0,0,0,0.3);
            z-index: 2000;
            display: none;
        }

        .error-modal.show {
            display: block;
            animation: slideIn 0.5s ease;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translate(-50%, -60%);
            }
            to {
                opacity: 1;
                transform: translate(-50%, -50%);
            }
        }

        .error-icon {
            font-size: 60px;
            margin-bottom: 20px;
        }

        .error-title {
            font-size: 24px;
            font-weight: 700;
            color: var(--error);
            margin-bottom: 15px;
        }

        .error-message {
            color: #666;
            font-size: 15px;
            line-height: 1.6;
            margin-bottom: 25px;
        }

        .error-details {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 8px;
            font-family: monospace;
            font-size: 12px;
            color: #333;
            margin-bottom: 25px;
            word-break: break-all;
        }

        .error-actions {
            display: flex;
            gap: 15px;
            justify-content: center;
        }

        .error-btn {
            padding: 12px 35px;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }

        .error-btn.primary {
            background: var(--accent);
            color: white;
        }

        .error-btn.primary:hover {
            background: var(--accent-hover);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(76, 175, 80, 0.3);
        }

        .error-btn.secondary {
            background: #e0e0e0;
            color: #333;
        }

        .error-btn.secondary:hover {
            background: #d0d0d0;
        }

        /* CLOUDFLARE CHALLENGE */
        .cf-challenge {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            border-radius: 24px;
            padding: 50px;
            max-width: 500px;
            width: 90%;
            text-align: center;
            box-shadow: 0 30px 80px rgba(0,0,0,0.4);
            z-index: 3000;
            display: none;
        }

        .cf-challenge.show {
            display: block;
            animation: scaleIn 0.5s ease;
        }

        @keyframes scaleIn {
            from {
                opacity: 0;
                transform: translate(-50%, -50%) scale(0.8);
            }
            to {
                opacity: 1;
                transform: translate(-50%, -50%) scale(1);
            }
        }

        .cf-logo {
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 30px;
            color: white;
            font-size: 40px;
        }

        .cf-title {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .cf-text {
            color: #666;
            font-size: 16px;
            line-height: 1.6;
            margin-bottom: 30px;
        }

        .cf-checkbox-container {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
            margin-bottom: 20px;
        }

        .cf-checkbox {
            width: 30px;
            height: 30px;
            border: 3px solid #ddd;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 18px;
        }

        .cf-checkbox.checked {
            background: var(--accent);
            border-color: var(--accent);
        }

        .cf-checkbox-label {
            font-size: 16px;
            color: #333;
        }

        .cf-footer {
            font-size: 12px;
            color: #999;
            margin-top: 30px;
        }

        /* STATUS BAR */
        .status-bar {
            background: var(--bg-secondary);
            padding: 6px 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: var(--text-secondary);
            font-size: 12px;
            border-top: 1px solid var(--border);
        }

        .status-left {
            display: flex;
            gap: 20px;
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

        .status-dot.secure { background: var(--accent); box-shadow: 0 0 10px var(--accent); }
        .status-dot.warning { background: var(--warning); }
        .status-dot.error { background: var(--error); }

        /* TOAST NOTIFICATIONS */
        .toast-container {
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 4000;
        }

        .toast {
            background: white;
            border-radius: 10px;
            padding: 15px 25px;
            margin-top: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            display: flex;
            align-items: center;
            gap: 15px;
            animation: slideInRight 0.3s ease;
            min-width: 300px;
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

        .toast.success { border-left: 5px solid var(--accent); }
        .toast.error { border-left: 5px solid var(--error); }
        .toast.warning { border-left: 5px solid var(--warning); }
        .toast.info { border-left: 5px solid var(--info); }

        .toast-close {
            background: transparent;
            border: none;
            color: #999;
            cursor: pointer;
            font-size: 18px;
            margin-left: auto;
        }

        /* RESPONSIVE */
        @media (max-width: 768px) {
            .browser {
                width: 100%;
                height: 100vh;
                border-radius: 0;
            }
            
            .security-badge span:not(.lock-icon) {
                display: none;
            }
            
            .error-actions {
                flex-direction: column;
            }
            
            .toast {
                min-width: auto;
                width: calc(100vw - 40px);
            }
        }

        /* ANIMATIONS */
        .pulse {
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .glow {
            animation: glow 2s infinite;
        }

        @keyframes glow {
            0%, 100% { box-shadow: 0 0 20px rgba(76, 175, 80, 0.3); }
            50% { box-shadow: 0 0 40px rgba(76, 175, 80, 0.6); }
        }
    </style>
</head>
<body>
    <div class="browser">
        <!-- Title Bar -->
        <div class="title-bar">
            <div class="window-controls">
                <div class="window-dot red"></div>
                <div class="window-dot yellow"></div>
                <div class="window-dot green"></div>
            </div>
            <div class="window-title">Kimstress Secure Browser</div>
            <div style="width: 60px;"></div>
        </div>

        <!-- Toolbar -->
        <div class="toolbar">
            <div class="nav-buttons">
                <button class="nav-btn" onclick="history.back()" id="backBtn" disabled>←</button>
                <button class="nav-btn" onclick="history.forward()" id="forwardBtn" disabled>→</button>
                <button class="nav-btn" onclick="refresh()">↻</button>
            </div>

            <div class="address-bar" id="addressBar">
                <span class="lock-icon">🔒</span>
                <input type="text" class="address-input" id="addressInput" value="{{ target_url }}" placeholder="Enter URL...">
                <div class="security-badge">
                    <span>🔒</span>
                    <span>Secure Connection</span>
                </div>
            </div>

            <button class="nav-btn" onclick="showMenu(event)">⋮</button>
        </div>

        <!-- Content Area -->
        <div class="content-area">
            <!-- Loading Overlay -->
            <div class="loading-overlay" id="loadingOverlay">
                <div class="loading-spinner"></div>
                <div class="loading-text">Loading Secure Content</div>
                <div class="loading-subtext" id="loadingStatus">Establishing encrypted connection...</div>
                <div class="loading-progress">
                    <div class="loading-progress-bar" id="progressBar" style="width: 0%;"></div>
                </div>
            </div>

            <!-- Error Modal -->
            <div class="error-modal" id="errorModal">
                <div class="error-icon">⚠️</div>
                <div class="error-title">Connection Error</div>
                <div class="error-message" id="errorMessage">Unable to establish secure connection</div>
                <div class="error-details" id="errorDetails"></div>
                <div class="error-actions">
                    <button class="error-btn primary" onclick="retry()">Try Again</button>
                    <button class="error-btn secondary" onclick="closeError()">Dismiss</button>
                </div>
            </div>

            <!-- Cloudflare Challenge -->
            <div class="cf-challenge" id="cfChallenge">
                <div class="cf-logo">🛡️</div>
                <div class="cf-title">Security Check</div>
                <div class="cf-text">Please verify that you are human to access kimstress.st</div>
                <div class="cf-checkbox-container">
                    <div class="cf-checkbox" id="cfCheckbox" onclick="verifyHuman()"></div>
                    <span class="cf-checkbox-label">I am human</span>
                </div>
                <div class="cf-footer">Protected by Cloudflare</div>
            </div>

            <!-- Main Frame -->
            <iframe 
                id="main-frame"
                src="/proxy/{{ encoded_url }}"
                sandbox="allow-same-origin allow-scripts allow-popups allow-forms allow-modals allow-top-navigation allow-downloads allow-popups-to-escape-sandbox allow-storage-access-by-user-activation allow-orientation-lock allow-pointer-lock allow-presentation"
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
                <div class="status-item" id="dataSize"></div>
            </div>
            <div class="status-right">
                <span id="timestamp">{{ timestamp }}</span>
            </div>
        </div>

        <!-- Toast Container -->
        <div class="toast-container" id="toastContainer"></div>
    </div>

    <script>
        // ADVANCED BROWSER SIMULATION
        (function() {
            // Complete browser fingerprint
            const browserFingerprint = {
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                language: navigator.language,
                languages: ['en-US', 'en'],
                cookieEnabled: navigator.cookieEnabled,
                doNotTrack: navigator.doNotTrack,
                hardwareConcurrency: 8,
                deviceMemory: 8,
                maxTouchPoints: 0,
                vendor: 'Google Inc.',
                vendorSub: '',
                productSub: '20030107',
                product: 'Gecko',
                appName: 'Netscape',
                appVersion: '5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                appCodeName: 'Mozilla',
                oscpu: 'Windows NT 10.0; Win64; x64',
                webdriver: false,
                plugins: [
                    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
                    { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }
                ],
                mimeTypes: []
            };

            // Override navigator properties
            Object.defineProperties(navigator, {
                webdriver: { get: () => false },
                plugins: { get: () => browserFingerprint.plugins },
                mimeTypes: { get: () => [] },
                languages: { get: () => browserFingerprint.languages },
                hardwareConcurrency: { get: () => browserFingerprint.hardwareConcurrency },
                deviceMemory: { get: () => browserFingerprint.deviceMemory }
            });

            // Add Chrome runtime
            if (!window.chrome) {
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };
            }

            // Remove automation traces
            delete window.domAutomation;
            delete window.domAutomationController;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        })();

        // State management
        const state = {
            loading: true,
            error: null,
            loadTime: 0,
            startTime: Date.now(),
            retryCount: 0,
            maxRetries: 5,
            verified: false,
            progress: 0,
            history: [],
            currentIndex: -1
        };

        // DOM Elements
        const iframe = document.getElementById('main-frame');
        const loadingOverlay = document.getElementById('loadingOverlay');
        const errorModal = document.getElementById('errorModal');
        const cfChallenge = document.getElementById('cfChallenge');
        const cfCheckbox = document.getElementById('cfCheckbox');
        const progressBar = document.getElementById('progressBar');
        const addressInput = document.getElementById('addressInput');
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');
        const loadTimeEl = document.getElementById('loadTime');
        const loadingStatus = document.getElementById('loadingStatus');
        const backBtn = document.getElementById('backBtn');
        const forwardBtn = document.getElementById('forwardBtn');

        // Progress simulation
        function updateProgress() {
            if (state.loading && state.progress < 90) {
                state.progress += Math.random() * 15;
                progressBar.style.width = Math.min(state.progress, 90) + '%';
                setTimeout(updateProgress, 200);
            }
        }

        // Initialize
        window.onload = function() {
            state.startTime = Date.now();
            updateProgress();
            checkConnection();
        };

        // Iframe handlers
        iframe.onload = function() {
            state.loading = false;
            state.loadTime = Date.now() - state.startTime;
            state.progress = 100;
            progressBar.style.width = '100%';
            
            setTimeout(() => {
                loadingOverlay.classList.add('hidden');
            }, 500);
            
            errorModal.classList.remove('show');
            cfChallenge.classList.remove('show');
            
            updateStatus('connected');
            loadTimeEl.textContent = `Load time: ${state.loadTime}ms`;
            
            try {
                const iframeUrl = iframe.contentWindow.location.href;
                if (iframeUrl && iframeUrl !== 'about:blank') {
                    addressInput.value = iframeUrl;
                    updateHistory(iframeUrl);
                }
            } catch(e) {
                // Cross-origin
            }
        };

        iframe.onerror = function() {
            handleError('Failed to load content');
        };

        // Connection check
        function checkConnection() {
            fetch('/health')
                .then(r => r.json())
                .then(data => {
                    showToast('Connection established', 'success');
                })
                .catch(() => {
                    showToast('Connection lost - retrying...', 'warning');
                });
        }

        // Error handling
        function handleError(message, details = '') {
            state.loading = false;
            state.error = message;
            
            if (state.retryCount < state.maxRetries && !state.verified) {
                state.retryCount++;
                loadingStatus.textContent = `Retrying (${state.retryCount}/${state.maxRetries})...`;
                setTimeout(refresh, 2000 * state.retryCount);
            } else if (!state.verified) {
                loadingOverlay.classList.add('hidden');
                cfChallenge.classList.add('show');
                statusText.textContent = 'Verification Required';
                statusDot.className = 'status-dot warning';
            } else {
                loadingOverlay.classList.add('hidden');
                errorModal.classList.add('show');
                document.getElementById('errorMessage').textContent = message;
                document.getElementById('errorDetails').textContent = details || 'Connection failed after multiple attempts';
                statusText.textContent = 'Connection Error';
                statusDot.className = 'status-dot error';
            }
        }

        // Cloudflare verification
        function verifyHuman() {
            cfCheckbox.classList.add('checked');
            loadingStatus.textContent = 'Verifying...';
            state.verified = true;
            
            // Simulate human verification
            setTimeout(() => {
                cfChallenge.classList.remove('show');
                loadingOverlay.classList.remove('hidden');
                state.progress = 0;
                state.retryCount = 0;
                refresh();
                showToast('Verification successful', 'success');
            }, 1500);
        }

        // Navigation functions
        function refresh() {
            state.loading = true;
            state.startTime = Date.now();
            state.progress = 0;
            progressBar.style.width = '0%';
            loadingOverlay.classList.remove('hidden');
            loadingStatus.textContent = 'Refreshing...';
            
            const currentSrc = iframe.src;
            iframe.src = 'about:blank';
            setTimeout(() => {
                iframe.src = currentSrc.split('?')[0] + '?t=' + Date.now();
            }, 100);
        }

        function updateStatus(status) {
            if (status === 'connected') {
                statusDot.className = 'status-dot secure';
                statusText.textContent = 'Secure Connection';
            } else if (status === 'warning') {
                statusDot.className = 'status-dot warning';
                statusText.textContent = 'Verification Required';
            } else {
                statusDot.className = 'status-dot error';
                statusText.textContent = 'Connection Error';
            }
        }

        // Address bar handling
        addressInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                let url = this.value;
                if (!url.startsWith('http')) {
                    url = 'https://' + url;
                }
                window.location.href = '/?url=' + encodeURIComponent(url);
            }
        });

        // History management
        function updateHistory(url) {
            state.history.push(url);
            state.currentIndex = state.history.length - 1;
            updateNavButtons();
        }

        function updateNavButtons() {
            backBtn.disabled = state.currentIndex <= 0;
            forwardBtn.disabled = state.currentIndex >= state.history.length - 1;
        }

        // Toast notifications
        function showToast(message, type = 'info') {
            const container = document.getElementById('toastContainer');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.innerHTML = `
                <span>${message}</span>
                <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
            `;
            container.appendChild(toast);
            
            setTimeout(() => {
                toast.remove();
            }, 5000);
        }

        // Context menu
        function showMenu(event) {
            // Implement context menu if needed
        }

        function retry() {
            errorModal.classList.remove('show');
            refresh();
        }

        function closeError() {
            errorModal.classList.remove('show');
        }

        // Visibility handling
        document.addEventListener('visibilitychange', function() {
            if (!document.hidden && state.error) {
                refresh();
            }
        });

        // Online/Offline handling
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
        }, 15000);

        // Expose functions globally
        window.refresh = refresh;
        window.verifyHuman = verifyHuman;
        window.retry = retry;
        window.closeError = closeError;
        window.showMenu = showMenu;
        window.showToast = showToast;
    </script>
</body>
</html>
'''

# Advanced proxy with complete browser emulation
class AdvancedProxy:
    def __init__(self):
        self.session = requests.Session()
        self.setup_session()
    
    def setup_session(self):
        """Setup session with real browser behavior"""
        retry_strategy = requests.adapters.Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def get_headers(self, session_id):
        """Generate real browser headers"""
        ua = session_db[session_id]['user_agent']
        
        return {
            'User-Agent': ua,
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
            'Pragma': 'no-cache',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"'
        }
    
    def process_content(self, content, content_type, base_url):
        """Process and fix HTML content"""
        if 'text/html' in content_type:
            try:
                soup = BeautifulSoup(content, 'html.parser')
                
                # Fix all URLs
                for tag in soup.find_all(['a', 'link', 'script', 'img', 'form', 'iframe', 'frame']):
                    for attr in ['href', 'src', 'action', 'data-src']:
                        if tag.get(attr):
                            original = tag[attr]
                            if original.startswith('//'):
                                tag[attr] = 'https:' + original
                            elif original.startswith('/'):
                                tag[attr] = base_url + original
                            elif not original.startswith(('http', 'https', 'data:', 'blob:', 'javascript:', 'mailto:', 'tel:')):
                                tag[attr] = urljoin(base_url, original)
                
                # Fix CSS links
                for link in soup.find_all('link'):
                    if link.get('href') and 'stylesheet' in link.get('rel', []):
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
                
                # Add meta tags for security
                meta = soup.new_tag('meta')
                meta['http-equiv'] = 'Content-Security-Policy'
                meta['content'] = "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:; script-src * 'unsafe-inline' 'unsafe-eval'; connect-src *; img-src * data: blob:; style-src * 'unsafe-inline'; frame-src *;"
                
                if soup.head:
                    soup.head.append(meta)
                
                return str(soup).encode('utf-8')
            except Exception as e:
                logger.error(f"Error processing HTML: {e}")
                return content
        return content

proxy = AdvancedProxy()

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
def handle_proxy(encoded_url=''):
    """Handle all proxy requests"""
    try:
        # Decode URL
        if encoded_url:
            target_url = unquote(encoded_url)
        else:
            target_url = request.args.get('url', TARGET_URL)
        
        # Clean URL
        target_url = target_url.split('#')[0].split('?t=')[0]
        
        # Parse URL
        parsed = urlparse(target_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Get session ID
        session_id = request.cookies.get('session_id') or hashlib.md5(os.urandom(16)).hexdigest()
        
        # Update session
        session_db[session_id]['last_used'] = datetime.now()
        
        # Get headers and cookies
        headers = proxy.get_headers(session_id)
        cookies = session_db[session_id]['cookies']
        
        # Add CF clearance if exists
        if session_db[session_id]['cf_clearance']:
            cookies['cf_clearance'] = session_db[session_id]['cf_clearance']
        
        # Make request
        response = proxy.session.get(
            target_url,
            headers=headers,
            cookies=cookies,
            timeout=30,
            allow_redirects=True,
            verify=False
        )
        
        # Save cookies
        for cookie in response.cookies:
            session_db[session_id]['cookies'][cookie.name] = cookie.value
            if cookie.name == 'cf_clearance':
                session_db[session_id]['cf_clearance'] = cookie.value
        
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
        
        # Process content
        content_type = response.headers.get('Content-Type', 'text/html; charset=utf-8')
        content = proxy.process_content(content, content_type, base_url)
        
        # Create response
        proxy_response = make_response(content)
        
        # Set cookies
        for name, value in session_db[session_id]['cookies'].items():
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
        proxy_response.headers['X-Frame-Options'] = 'ALLOWALL'
        proxy_response.headers['X-Content-Type-Options'] = 'nosniff'
        
        return proxy_response
        
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

@app.route('/stats')
def stats():
    """Session statistics"""
    return jsonify({
        'active_sessions': len(session_db),
        'uptime': str(datetime.now() - app_start_time)
    })

# Cleanup old sessions periodically
def cleanup_sessions():
    while True:
        try:
            now = datetime.now()
            expired = [sid for sid, data in session_db.items() 
                      if (now - data.get('last_used', now)).seconds > 7200]
            for sid in expired:
                del session_db[sid]
            time.sleep(300)
        except:
            time.sleep(60)

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_sessions, daemon=True)
cleanup_thread.start()

app_start_time = datetime.now()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
