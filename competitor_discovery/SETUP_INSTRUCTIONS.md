# Competitor Discovery Tool - Setup Instructions for OpenClaw

## Overview

This tool finds YouTube channels in the Sicily/expat niche that Andreas isn't subscribed to. It runs daily and sends a Telegram message with new channels to check out.

**100% ToS compliant** - only searches and lists, no automated engagement.

---

## Prerequisites

1. Python 3.10+
2. YouTube API OAuth credentials (from Andreas's youtube-expert repo)
3. Telegram Bot Token & Chat ID

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/andreaskviby/youtube-expert.git
cd youtube-expert
```

---

## Step 2: Set Up Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install google-auth google-auth-oauthlib google-api-python-client requests
```

---

## Step 3: Copy YouTube OAuth Credentials

The YouTube API requires OAuth credentials. Copy these files from Andreas's local machine or secure storage:

```
youtube_api/token.pickle        # OAuth token (required)
youtube_api/client_secrets.json # OAuth client (required)
```

These files authenticate as Andreas's YouTube account to:
- Check his subscriptions (to filter them out)
- Search YouTube API

**If token.pickle expires**, run this to re-authenticate:
```bash
python -c "from youtube_api.analytics import YouTubeAnalytics; YouTubeAnalytics()"
```
This opens a browser for OAuth login.

---

## Step 4: Create Telegram Bot

### 4.1 Create the Bot

1. Open Telegram and message **@BotFather**
2. Send: `/newbot`
3. Name: `Sicily Discovery Bot`
4. Username: `sicily_discovery_bot` (or similar unique name)
5. **Save the bot token** (looks like: `7123456789:AAHxxxxxxxxxxxxxxxxxxxxxx`)

### 4.2 Get Your Chat ID

1. Message **@userinfobot** on Telegram
2. It replies with your user info
3. **Save your Chat ID** (a number like: `123456789`)

### 4.3 Start the Bot

1. Open your new bot in Telegram (search for the username you created)
2. Press **Start** or send `/start`
3. This is required before the bot can message you

---

## Step 5: Configure Environment Variables

Create a file `/etc/environment.d/sicily-discovery.conf` or add to `.bashrc`:

```bash
export TELEGRAM_BOT_TOKEN="7123456789:AAHxxxxxxxxxxxxxxxxxxxxxx"
export TELEGRAM_CHAT_ID="123456789"
```

Or create `.env` file in the project:

```bash
cd /path/to/youtube-expert
cat > competitor_discovery/.env << 'EOF'
TELEGRAM_BOT_TOKEN=7123456789:AAHxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=123456789
EOF
```

Then modify `daily_run.py` to load it:
```python
from dotenv import load_dotenv
load_dotenv('competitor_discovery/.env')
```

And install python-dotenv:
```bash
pip install python-dotenv
```

---

## Step 6: Test the Setup

### Test Discovery (no send):
```bash
cd /path/to/youtube-expert
source venv/bin/activate
python competitor_discovery/daily_run.py --send none
```

Should output a list of ~50-60 channels.

### Test Telegram:
```bash
python competitor_discovery/daily_run.py --send telegram
```

Should send a message to your Telegram.

---

## Step 7: Set Up Daily Cron Job

```bash
crontab -e
```

Add this line (runs at 8:00 AM every day):

```cron
0 8 * * * cd /path/to/youtube-expert && source venv/bin/activate && TELEGRAM_BOT_TOKEN="your-token" TELEGRAM_CHAT_ID="your-id" python competitor_discovery/daily_run.py --send telegram >> /var/log/sicily-discovery.log 2>&1
```

Or create a systemd timer for more reliability:

### /etc/systemd/system/sicily-discovery.service
```ini
[Unit]
Description=Sicily YouTube Competitor Discovery
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/path/to/youtube-expert
Environment="TELEGRAM_BOT_TOKEN=your-token"
Environment="TELEGRAM_CHAT_ID=your-id"
ExecStart=/path/to/youtube-expert/venv/bin/python competitor_discovery/daily_run.py --send telegram
User=your-user

[Install]
WantedBy=multi-user.target
```

### /etc/systemd/system/sicily-discovery.timer
```ini
[Unit]
Description=Run Sicily Discovery daily at 8am

[Timer]
OnCalendar=*-*-* 08:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable sicily-discovery.timer
sudo systemctl start sicily-discovery.timer
```

---

## Step 8: Customize Search Queries (Optional)

Edit `competitor_discovery/discover.py` and modify the `SEARCH_QUERIES` list:

```python
SEARCH_QUERIES = [
    "life in Sicily",
    "moving to Sicily",
    "buy house Sicily",
    "living in Sicily expat",
    "Sicily renovation",
    "house hunting Sicily Italy",
    "relocating to Sicily",
    "Sicily property",
    "expat Sicily",
    "retire in Sicily",
    "Sicily vlog",
    "Sicily home tour",
    # Add more queries here
]
```

---

## File Structure

```
youtube-expert/
├── competitor_discovery/
│   ├── discover.py          # Main discovery engine
│   ├── send_report.py       # Telegram/Email sender
│   ├── daily_run.py         # Daily runner (cron target)
│   ├── .env                  # Environment variables (create this)
│   ├── README.md            # Quick reference
│   └── data/
│       ├── seen_channels.json    # Tracks seen channels (auto-created)
│       └── report_YYYYMMDD.txt   # Daily reports (auto-created)
│
├── youtube_api/
│   ├── token.pickle         # OAuth token (REQUIRED - copy from Andreas)
│   └── client_secrets.json  # OAuth client (REQUIRED - copy from Andreas)
│
└── venv/                    # Python virtual environment
```

---

## Troubleshooting

### "No YouTube credentials found"
- Copy `youtube_api/token.pickle` and `youtube_api/client_secrets.json` from Andreas's machine

### "Token expired"
- Run: `python -c "from youtube_api.analytics import YouTubeAnalytics; YouTubeAnalytics()"`
- This opens browser for re-authentication

### "Telegram failed"
- Verify bot token is correct
- Make sure you pressed "Start" on the bot in Telegram
- Check chat ID is your personal ID (not a group)

### "No new channels found"
- This is normal after first run - it tracks seen channels
- Delete `competitor_discovery/data/seen_channels.json` to reset
- Or use `--include-seen` flag to see all results

---

## What Gets Sent Daily

Example Telegram message:

```
🔍 SICILY NICHE DISCOVERY - 2026-06-11
Found 12 new channels to check out:

==================================================

1. Sicily Rose (132K subs)
   📺 Latest: Built this life by myself
   🔗 https://youtube.com/watch?v=Lrs8HlnC2y8
   📢 Channel: https://youtube.com/channel/UCHr05r...
   🔎 Found via: "life in Sicily"

2. Move To Italy Now (7K subs)
   📺 Latest: €40,000 Stone House in Sicily
   🔗 https://youtube.com/watch?v=YdWnmo5wI-Y
   ...

==================================================
Your subscriptions: 38 channels
Channels seen before: 147
```

---

## Security Notes

- `token.pickle` contains OAuth credentials - keep secure
- Never commit `.env` or credentials to git
- The tool only READS from YouTube API, never writes
- No automated engagement = 100% ToS compliant

---

## Contact

Questions? This tool was built for Andreas Kviby's "Adventure in Sicily" YouTube channel.

GitHub: https://github.com/andreaskviby/youtube-expert
