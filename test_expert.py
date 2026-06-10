#!/usr/bin/env python3
"""
Test script for YouTube Expert

Run with: python test_expert.py
"""

import sys
from pathlib import Path

# Add the project to path
sys.path.insert(0, str(Path(__file__).parent))

from youtube_expert import YouTubeExpert
from youtube_expert.agent_runner import (
    run_skill,
    get_channel_status,
    get_critical_issues,
    get_recommendations,
    generate_action_plan,
    list_available_skills,
)


def main():
    data_path = Path(__file__).parent

    print("=" * 70)
    print("YOUTUBE EXPERT TEST")
    print("=" * 70)

    # Check for CSV files
    csv_files = list(data_path.glob("*.csv"))
    if not csv_files:
        print("No CSV files found in current directory")
        return

    print(f"\nFound {len(csv_files)} CSV files:")
    for f in csv_files:
        print(f"  - {f.name}")

    # List available skills
    print("\n" + "=" * 70)
    print("AVAILABLE SKILLS")
    print("=" * 70)
    skills = list_available_skills()
    for skill in skills:
        print(f"  {skill['name']}: {skill['description'][:50]}...")

    # Get channel status
    print("\n" + "=" * 70)
    print("CHANNEL STATUS")
    print("=" * 70)
    try:
        status = get_channel_status(data_path)
        print(f"  Video count: {status['video_count']}")
        print(f"  Shorts: {status['shorts_count']}")
        print(f"  Long-form: {status['longform_count']}")
        print(f"  Total views: {status['total_views']:,}")
        print(f"  Watch hours: {status['total_watch_hours']:,.1f}")
    except Exception as e:
        print(f"  Error: {e}")

    # Run diagnostics
    print("\n" + "=" * 70)
    print("RUNNING DIAGNOSTICS SKILL")
    print("=" * 70)
    try:
        result = run_skill("diagnostics", data_path)
        if "digest" in result:
            print(result["digest"])
        print(f"\nSeverity: {result.get('severity', 'N/A')}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    # Run shorts strategy
    print("\n" + "=" * 70)
    print("RUNNING SHORTS STRATEGY SKILL")
    print("=" * 70)
    try:
        result = run_skill("shorts_strategy", data_path)
        if "digest" in result:
            print(result["digest"])
    except Exception as e:
        print(f"Error: {e}")

    # Get recommendations
    print("\n" + "=" * 70)
    print("HIGH PRIORITY RECOMMENDATIONS")
    print("=" * 70)
    try:
        recs = get_recommendations(data_path, priority="HIGH")
        for rec in recs[:5]:
            print(f"  [{rec['skill']}] {rec['action']}")
    except Exception as e:
        print(f"Error: {e}")

    # Generate action plan
    print("\n" + "=" * 70)
    print("ACTION PLAN")
    print("=" * 70)
    try:
        plan = generate_action_plan(data_path)
        print(plan)
    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
