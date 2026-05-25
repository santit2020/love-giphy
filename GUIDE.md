# Complete Fix Guide — Love Giphy Bot on Render Free Plan

---

## WHY YOUR BOT WAS NOT RESPONDING — All 5 Problems Explained

---

### Problem 1 (MOST IMPORTANT): Wrong Service Type in render.yaml

**What was wrong:**
Your `render.yaml` file said `type: worker`. 

**Why this breaks everything:**
Render's FREE plan does NOT support "Worker" services. Worker services cost money on Render.
When you deployed with `type: worker` on the free plan, Render either rejected it silently
or the service never actually started running. That's why your bot did nothing at all — 
it was never running in the first place!

**The OLD broken line:**
```yaml
- type: worker
```

**The NEW fixed line:**
```yaml
- type: web
```

A "web" service IS available on Render's free plan and it's what your bot needs.

---

### Problem 2: Missing Environment Variables on Render Dashboard

**What was wrong:**
Your code reads secrets like this:
```python
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")
```

These are never stored in your code files (which is correct and safe!).
But if you don't tell Render what these values ARE, your bot starts up,
immediately sees they are missing, prints an error, and shuts down.

**How to fix it (step by step):**
1. Go to https://dashboard.render.com
2. Click on your service "love-giphy-bot"
3. Click "Environment" in the left sidebar
4. Click "Add Environment Variable"
5. Add these two, one at a time:
   - Key: `TELEGRAM_BOT_TOKEN`  →  Value: (paste your bot token from BotFather)
   - Key: `GIPHY_API_KEY`        →  Value: (paste your Giphy API key)
6. Click "Save Changes"
7. Render will automatically redeploy your service

---

### Problem 3: Render Free Web Services "Spin Down" After 15 Minutes

**What was wrong:**
Render's free web services go to "sleep" if nobody visits them for 15 minutes.
When the service is asleep, your Telegram bot stops responding.

**How to fix it:**
You need a FREE external service to "ping" (visit) your bot's URL every 10 minutes
to keep it awake.

**Step by step:**
1. Sign up at https://uptimerobot.com (it's completely free)
2. Click "Add New Monitor"
3. Choose "HTTP(s)" as the monitor type
4. Set the URL to: `https://your-render-url.onrender.com/health`
   (Replace with your actual Render URL, visible in your Render dashboard)
5. Set the check interval to "Every 5 minutes"
6. Click "Create Monitor"

UptimeRobot will now visit your bot URL every 5 minutes, keeping it awake 24/7.

---

### Problem 4: GIF Function Was Freezing the Bot

**What was wrong:**
The original code used `requests.get()` inside an async function:
```python
# OLD BROKEN CODE — blocks the entire bot while fetching GIF
import requests
response = requests.get(url, params=params)
```

`requests` is "synchronous" — it freezes everything while it waits for the internet.
When your bot was fetching a GIF, it could not respond to ANY Telegram messages 
at the same time. This made the bot feel unresponsive.

**The NEW fixed code — uses async httpx:**
```python
# NEW FIXED CODE — fetches GIF without freezing the bot
import httpx
async with httpx.AsyncClient(timeout=15) as client:
    response = await client.get(url, params=params)
```

The `await` keyword means "go fetch this, but let the bot keep doing other things while waiting."
The `requests` package was also removed from requirements.txt since it's no longer needed.

---

### Problem 5: users.json Gets Deleted on Every Redeploy

**What was wrong:**
`users.json` stores everyone's name and schedule. But on Render (and most cloud services),
files you create while the app is running get deleted when the app restarts or redeploys.
So every time you push new code, all your users' settings are wiped.

**How to fix it (simple approach for now):**
This is a known limitation of the free tier. For now, users will need to re-run `/start`
after a redeploy. A proper fix would require a database (like Render's free PostgreSQL),
but that's more advanced — the bot still works, users just need to re-register after redeploys.

---

## HOW TO SAFELY STORE AND CHANGE YOUR BOT TOKEN

**Where is the token stored?**
- Your token is stored ONLY in Render's Environment Variables dashboard
- It is NEVER in your code files
- It is NEVER in render.yaml (render.yaml only lists the variable NAME, not the value)
- It is NEVER on GitHub

**To change your bot token in the future:**
1. Go to Telegram → talk to @BotFather
2. Send `/mybots` → select your bot → "API Token" → "Revoke current token"
3. BotFather gives you a new token — copy it
4. Go to https://dashboard.render.com → your service → "Environment"
5. Find `TELEGRAM_BOT_TOKEN` and click the edit (pencil) icon
6. Paste your new token
7. Click "Save Changes" — Render redeploys automatically with the new token
8. Test your bot in Telegram within a minute or two

**What NOT to do (keeping secrets safe):**
- NEVER paste your token directly into any .py file
- NEVER commit a `.env` file that contains your token to GitHub
- The `.gitignore` file already blocks `key.txt` and `.env` — good!
- If you accidentally push a token to GitHub, immediately revoke it in BotFather
  (tokens exposed on GitHub get stolen within minutes by automated bots)

---

## HOW TO REDEPLOY ON RENDER (Step by Step)

### Option A — Automatic (recommended): Push to GitHub
1. Replace your old files with the fixed files from this folder
2. Open a terminal in your project folder
3. Run these commands:
   ```
   git add .
   git commit -m "fix: change worker to web service, fix async gif"
   git push
   ```
4. Go to your Render dashboard — it will automatically redeploy within 1-2 minutes

### Option B — Manual from Render Dashboard
1. Go to https://dashboard.render.com
2. Click on your service "love-giphy-bot"
3. Click the "Manual Deploy" button (top right)
4. Click "Deploy latest commit"
5. Wait ~2 minutes for the build to finish

---

## HOW TO CHECK LOGS ON RENDER

Logs tell you exactly what's happening with your bot.

1. Go to https://dashboard.render.com
2. Click on your service
3. Click "Logs" in the left sidebar
4. You should see lines like:
   ```
   ✅ Environment variables loaded successfully
   🤖 starting love bot...
   💖 bot is alive! Polling for messages...
   ```
5. If you see `❌ TELEGRAM_BOT_TOKEN is missing!` — go add the environment variable (Problem 2 above)
6. If you see `❌ GIPHY_API_KEY is missing!` — go add the Giphy key (Problem 2 above)

---

## HOW TO TEST YOUR BOT AFTER DEPLOYING

1. Wait for the Render deployment to finish (the logs say "💖 bot is alive!")
2. Open Telegram
3. Search for your bot by its username (e.g. @YourBotName)
4. Send `/start`
5. The bot should reply: "💖 hiiii what's your name?"
6. Type your name and press enter
7. The bot should ask for your love frequency (1h, 4h, 12h, 24h buttons)
8. Click a button — you should see "💖 messages every X hour(s)"
9. Test "love u" in a message — bot should reply with "love u more 💖" or similar

---

## HOW TO GET A GIPHY API KEY (if you don't have one)

1. Go to https://developers.giphy.com
2. Click "Create an App"
3. Sign up for a free account
4. Choose "API" (not SDK)
5. Fill in your app name (e.g. "LoveBot") and description
6. Click "Create App"
7. Your API key appears on the dashboard — copy it
8. Add it to Render as `GIPHY_API_KEY` (see Problem 2 above)

---

## SUMMARY OF ALL CHANGES MADE

| File | What Changed | Why |
|------|-------------|-----|
| `render.yaml` | `type: worker` → `type: web` | Free plan only supports web services |
| `render.yaml` | Added `envVars` block | Documents required environment variables |
| `loveboost.py` | `import requests` → `import httpx` + async | Fixes bot freeze during GIF fetch |
| `loveboost.py` | Added `/health` route | For UptimeRobot to ping |
| `loveboost.py` | Added `daemon=True` to Flask thread | Cleaner shutdown behavior |
| `loveboost.py` | Added `drop_pending_updates=True` to polling | Ignores old messages from when bot was offline |
| `requirements.txt` | Removed `requests`, kept `httpx` | `requests` no longer needed after async fix |

---

That's everything! After making these changes, your bot should run 24/7 on Render's free plan.
