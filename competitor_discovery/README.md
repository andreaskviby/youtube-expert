# Competitor Discovery Tool

Finds YouTube channels in your niche that you're not subscribed to.
Sends daily digest via email or Telegram.

## Quick Start

```bash
# Run discovery (print only)
python competitor_discovery/daily_run.py --send none

# Run and send via email
python competitor_discovery/daily_run.py --send email

# Run and send via Telegram
python competitor_discovery/daily_run.py --send telegram
```

## Setup

### 1. Email (Mailgun)

Set environment variables:
```bash
export MAILGUN_API_KEY="your-api-key"
export MAILGUN_DOMAIN="mg.adventureinsicily.com"
export EMAIL_TO="andreas@kviby.com"
```

### 2. Telegram Bot

1. Create a bot with @BotFather on Telegram
2. Get your chat ID by messaging @userinfobot
3. Set environment variables:
```bash
export TELEGRAM_BOT_TOKEN="123456:ABC..."
export TELEGRAM_CHAT_ID="your-chat-id"
```

### 3. Daily Cron Job

Add to crontab (`crontab -e`):
```cron
# Run at 8am every day
0 8 * * * cd /Users/andreaskviby/Herd/youtube-expert && /Users/andreaskviby/Herd/youtube-expert/venv/bin/python competitor_discovery/daily_run.py --send email
```

## Search Queries

The tool searches for these terms:
- life in Sicily
- moving to Sicily
- buy house Sicily
- living in Sicily expat
- Sicily renovation
- house hunting Sicily Italy
- relocating to Sicily
- Sicily property
- expat Sicily
- retire in Sicily
- Sicily vlog
- Sicily home tour

Edit `discover.py` to add/change search queries.

## Output

Reports are saved to `competitor_discovery/data/report_YYYYMMDD.txt`

Seen channels are tracked in `competitor_discovery/data/seen_channels.json` to avoid showing duplicates.

## Legal & ToS Compliant

This tool ONLY:
- ✅ Searches public YouTube data
- ✅ Lists channels for manual review
- ✅ Tracks what you've seen

It does NOT:
- ❌ Auto-subscribe
- ❌ Auto-comment
- ❌ Auto-like
- ❌ Any automated engagement
