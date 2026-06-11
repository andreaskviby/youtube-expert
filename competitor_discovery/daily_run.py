#!/usr/bin/env python3
"""
Daily Competitor Discovery Runner
Run this via cron or manually to get your daily digest
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from competitor_discovery.discover import CompetitorDiscovery
from competitor_discovery.send_report import send_report


def run_daily_discovery(send_method: str = "email", include_seen: bool = False):
    """Run discovery and send report"""
    print("="*60)
    print("🔍 DAILY COMPETITOR DISCOVERY")
    print("="*60)

    try:
        # Run discovery
        discovery = CompetitorDiscovery()
        report = discovery.generate_report(include_seen=include_seen)

        # Print to console
        print(report)

        # Send report
        if send_method and send_method != "none":
            print(f"\nSending via {send_method}...")
            send_report(report, send_method)

        return report

    except Exception as e:
        error_msg = f"❌ Discovery failed: {str(e)}"
        print(error_msg)

        # Still try to send error notification
        if send_method and send_method != "none":
            send_report(error_msg, send_method)

        return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run daily competitor discovery")
    parser.add_argument(
        "--send",
        choices=["email", "telegram", "both", "none"],
        default="none",
        help="How to send the report"
    )
    parser.add_argument(
        "--include-seen",
        action="store_true",
        help="Include channels seen before"
    )

    args = parser.parse_args()
    run_daily_discovery(send_method=args.send, include_seen=args.include_seen)
