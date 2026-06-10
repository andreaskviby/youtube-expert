#!/usr/bin/env python3
"""
YouTube Expert CLI - Command-line interface for running skills

Usage:
    python -m youtube_expert.cli --data /path/to/data --skill diagnostics
    python -m youtube_expert.cli --data /path/to/data --all
    python -m youtube_expert.cli --data /path/to/data --skill performance --json

Skills available:
    diagnostics, performance, shorts_strategy, thumbnail_optimizer,
    upload_scheduler, seo_optimizer, audience_analyzer, revenue_optimizer,
    growth_projector, competitor_analyzer, content_planner, trend_detector
"""

import argparse
import json
import sys
from pathlib import Path

from .core import YouTubeExpert


def main():
    parser = argparse.ArgumentParser(
        description="YouTube Expert - AI-powered channel analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run channel diagnostics
    python -m youtube_expert.cli --data ./data --skill diagnostics

    # Run all skills and generate full report
    python -m youtube_expert.cli --data ./data --all

    # Output as JSON for programmatic use
    python -m youtube_expert.cli --data ./data --skill performance --json

    # List available skills
    python -m youtube_expert.cli --list-skills
        """,
    )

    parser.add_argument(
        "--data", "-d",
        type=str,
        help="Path to directory containing YouTube Analytics CSV files",
    )

    parser.add_argument(
        "--skill", "-s",
        type=str,
        help="Name of skill to run",
    )

    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Run all skills",
    )

    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output results as JSON",
    )

    parser.add_argument(
        "--list-skills", "-l",
        action="store_true",
        help="List all available skills",
    )

    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show quick channel summary",
    )

    args = parser.parse_args()

    # List skills
    if args.list_skills:
        expert = YouTubeExpert()
        print("\nAvailable Skills:")
        print("-" * 50)
        for skill_info in expert.list_skills():
            print(f"  {skill_info['name']}")
            print(f"    {skill_info['description'][:60]}")
            print()
        return

    # Require data path for other operations
    if not args.data:
        parser.error("--data is required unless using --list-skills")

    data_path = Path(args.data)
    if not data_path.exists():
        print(f"Error: Data directory not found: {data_path}", file=sys.stderr)
        sys.exit(1)

    # Initialize expert
    try:
        expert = YouTubeExpert(data_path)
    except Exception as e:
        print(f"Error loading data: {e}", file=sys.stderr)
        sys.exit(1)

    # Quick summary
    if args.summary:
        print(expert.get_quick_summary())
        return

    # Run specific skill
    if args.skill:
        try:
            result = expert.run_skill(args.skill)

            if args.json:
                print(json.dumps(result, indent=2, default=str, ensure_ascii=False))
            else:
                if "digest" in result:
                    print(result["digest"])
                else:
                    print(json.dumps(result, indent=2, default=str, ensure_ascii=False))

        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error running skill '{args.skill}': {e}", file=sys.stderr)
            sys.exit(1)
        return

    # Run all skills
    if args.all:
        result = expert.run_all_skills()

        if args.json:
            print(json.dumps(result, indent=2, default=str, ensure_ascii=False))
        else:
            # Print channel summary
            print("=" * 70)
            print("YOUTUBE EXPERT - FULL CHANNEL ANALYSIS")
            print("=" * 70)
            print(f"\nTimestamp: {result['timestamp']}")
            print(f"\nChannel Summary:")
            for key, value in result['channel_summary'].items():
                print(f"  {key}: {value}")
            print()

            # Print each skill's digest
            for skill_name, skill_result in result['skills'].items():
                if isinstance(skill_result, dict):
                    if "error" in skill_result:
                        print(f"\n[{skill_name.upper()}] Error: {skill_result['error']}")
                    elif "digest" in skill_result:
                        print(f"\n{skill_result['digest']}")
                    else:
                        print(f"\n[{skill_name.upper()}] Completed")
                        print(f"  Severity: {skill_result.get('severity', 'N/A')}")
        return

    # Default: show summary
    print(expert.get_quick_summary())


if __name__ == "__main__":
    main()
