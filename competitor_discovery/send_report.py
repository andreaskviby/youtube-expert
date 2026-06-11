#!/usr/bin/env python3
"""
Send competitor discovery report via Email or Telegram
"""

import os
import requests
from datetime import datetime
from pathlib import Path

# Email config (Mailgun)
MAILGUN_API_KEY = os.environ.get('MAILGUN_API_KEY', '')
MAILGUN_DOMAIN = os.environ.get('MAILGUN_DOMAIN', 'mg.adventureinsicily.com')
EMAIL_TO = os.environ.get('EMAIL_TO', 'andreas@kviby.com')
EMAIL_FROM = f"Sicily Discovery <discovery@{MAILGUN_DOMAIN}>"

# Telegram config
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')


def send_email(subject: str, body: str) -> bool:
    """Send report via Mailgun"""
    if not MAILGUN_API_KEY:
        print("⚠️  MAILGUN_API_KEY not set")
        return False

    response = requests.post(
        f"https://api.eu.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": EMAIL_FROM,
            "to": EMAIL_TO,
            "subject": subject,
            "text": body
        }
    )

    if response.status_code == 200:
        print(f"✅ Email sent to {EMAIL_TO}")
        return True
    else:
        print(f"❌ Email failed: {response.text}")
        return False


def send_telegram(message: str) -> bool:
    """Send report via Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")
        return False

    # Telegram has 4096 char limit, split if needed
    chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]

    for chunk in chunks:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": chunk,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
        )

        if response.status_code != 200:
            print(f"❌ Telegram failed: {response.text}")
            return False

    print(f"✅ Telegram message sent")
    return True


def send_report(report: str, method: str = "email"):
    """Send the discovery report"""
    date_str = datetime.now().strftime('%Y-%m-%d')
    subject = f"🔍 Sicily Niche Discovery - {date_str}"

    if method == "email":
        return send_email(subject, report)
    elif method == "telegram":
        return send_telegram(report)
    elif method == "both":
        email_ok = send_email(subject, report)
        telegram_ok = send_telegram(report)
        return email_ok or telegram_ok
    else:
        print(f"Unknown method: {method}")
        return False


if __name__ == "__main__":
    # Test with sample report
    test_report = """🔍 SICILY NICHE DISCOVERY - Test

Found 3 new channels:

1. Test Channel (10K subs)
   📺 Latest: Test Video Title
   🔗 https://youtube.com/watch?v=test123
"""

    import sys
    method = sys.argv[1] if len(sys.argv) > 1 else "email"
    send_report(test_report, method)
