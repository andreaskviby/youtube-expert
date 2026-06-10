#!/usr/bin/env python3
"""
YouTube Expert Agent Runner

This module provides the interface for AI agents to run YouTube Expert skills.
Designed for integration with OpenClaw, Claude Code, and other AI agent systems.

Usage by agents:
    from youtube_expert.agent_runner import run_skill, run_all_skills, get_channel_status

    # Run a specific skill
    result = run_skill("diagnostics", data_path="/path/to/csv/data")

    # Run all skills
    full_report = run_all_skills(data_path="/path/to/csv/data")

    # Get quick status
    status = get_channel_status(data_path="/path/to/csv/data")
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from .core import YouTubeExpert, ChannelData


# Global expert instance for efficient repeated calls
_expert_cache: Dict[str, YouTubeExpert] = {}


def _get_expert(data_path: str | Path) -> YouTubeExpert:
    """Get or create YouTubeExpert instance (cached for efficiency)"""
    path_str = str(Path(data_path).resolve())

    if path_str not in _expert_cache:
        _expert_cache[path_str] = YouTubeExpert(data_path)

    return _expert_cache[path_str]


def run_skill(
    skill_name: str,
    data_path: str | Path,
    **kwargs
) -> Dict[str, Any]:
    """
    Run a specific YouTube Expert skill

    Args:
        skill_name: Name of the skill to run
            Options: diagnostics, performance, shorts_strategy, thumbnail_optimizer,
                    upload_scheduler, seo_optimizer, audience_analyzer, revenue_optimizer,
                    growth_projector, competitor_analyzer, content_planner, trend_detector
        data_path: Path to directory containing CSV files
        **kwargs: Additional arguments to pass to the skill

    Returns:
        Dict containing:
            - metrics: Quantitative measurements
            - insights: Key findings as list of strings
            - recommendations: Actionable suggestions
            - severity: OK | WATCH | WARNING | CRITICAL
            - digest: Human-readable summary string

    Example:
        result = run_skill("diagnostics", "/data/youtube")
        print(result["digest"])  # Print human-readable summary
        if result["severity"] == "CRITICAL":
            # Handle critical issues
    """
    expert = _get_expert(data_path)
    return expert.run_skill(skill_name, **kwargs)


def run_all_skills(data_path: str | Path) -> Dict[str, Any]:
    """
    Run all YouTube Expert skills and get comprehensive report

    Args:
        data_path: Path to directory containing CSV files

    Returns:
        Dict containing:
            - timestamp: When the analysis was run
            - channel_summary: Quick overview of channel metrics
            - skills: Dict of skill_name -> result for each skill

    Example:
        report = run_all_skills("/data/youtube")
        for skill_name, result in report["skills"].items():
            if result.get("severity") == "CRITICAL":
                print(f"CRITICAL issue in {skill_name}: {result['digest']}")
    """
    expert = _get_expert(data_path)
    return expert.run_all_skills()


def get_channel_status(data_path: str | Path) -> Dict[str, Any]:
    """
    Get quick channel status overview

    Args:
        data_path: Path to directory containing CSV files

    Returns:
        Dict containing:
            - video_count: Total number of videos
            - shorts_count: Number of Shorts
            - longform_count: Number of long-form videos
            - total_views: Total views across all videos
            - total_watch_hours: Total watch time in hours
            - summary: Human-readable summary string

    Example:
        status = get_channel_status("/data/youtube")
        print(f"Channel has {status['video_count']} videos")
    """
    expert = _get_expert(data_path)

    return {
        "video_count": expert.data.video_count,
        "shorts_count": expert.data.shorts_count,
        "longform_count": expert.data.longform_count,
        "total_views": expert.data.total_views,
        "total_watch_hours": round(expert.data.total_watch_hours, 1),
        "summary": expert.get_quick_summary(),
    }


def list_available_skills() -> List[Dict[str, str]]:
    """
    List all available skills with descriptions

    Returns:
        List of dicts with 'name' and 'description' keys

    Example:
        skills = list_available_skills()
        for skill in skills:
            print(f"{skill['name']}: {skill['description']}")
    """
    expert = YouTubeExpert()
    return expert.list_skills()


def get_critical_issues(data_path: str | Path) -> List[Dict[str, Any]]:
    """
    Get only critical issues that need immediate attention

    Args:
        data_path: Path to directory containing CSV files

    Returns:
        List of critical issues from all skills

    Example:
        issues = get_critical_issues("/data/youtube")
        if issues:
            for issue in issues:
                print(f"[{issue['skill']}] {issue['message']}")
    """
    expert = _get_expert(data_path)
    full_report = expert.run_all_skills()

    critical_issues = []

    for skill_name, result in full_report["skills"].items():
        if isinstance(result, dict):
            # Check severity
            if result.get("severity") in ["CRITICAL", "WARNING"]:
                critical_issues.append({
                    "skill": skill_name,
                    "severity": result.get("severity"),
                    "message": result.get("digest", "No digest available")[:500],
                    "issues": result.get("issues", []),
                })

    return critical_issues


def get_recommendations(data_path: str | Path, priority: str = None) -> List[Dict[str, Any]]:
    """
    Get all recommendations, optionally filtered by priority

    Args:
        data_path: Path to directory containing CSV files
        priority: Optional filter - "HIGH", "MEDIUM", or "LOW"

    Returns:
        List of recommendations from all skills

    Example:
        high_priority = get_recommendations("/data/youtube", priority="HIGH")
        for rec in high_priority:
            print(f"[{rec['skill']}] {rec['action']}")
    """
    expert = _get_expert(data_path)
    full_report = expert.run_all_skills()

    recommendations = []

    for skill_name, result in full_report["skills"].items():
        if isinstance(result, dict) and "recommendations" in result:
            for rec in result["recommendations"]:
                if priority is None or rec.get("priority") == priority:
                    recommendations.append({
                        "skill": skill_name,
                        **rec,
                    })

    # Sort by priority
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    recommendations.sort(key=lambda x: priority_order.get(x.get("priority", "LOW"), 3))

    return recommendations


def generate_action_plan(data_path: str | Path) -> str:
    """
    Generate a prioritized action plan based on all skills

    Args:
        data_path: Path to directory containing CSV files

    Returns:
        Formatted action plan string

    Example:
        plan = generate_action_plan("/data/youtube")
        print(plan)
    """
    expert = _get_expert(data_path)
    status = get_channel_status(data_path)
    issues = get_critical_issues(data_path)
    high_recs = get_recommendations(data_path, priority="HIGH")

    lines = [
        "=" * 60,
        "YOUTUBE CHANNEL ACTION PLAN",
        "=" * 60,
        "",
        f"Total Videos: {status['video_count']}",
        f"  Shorts: {status['shorts_count']}",
        f"  Long-form: {status['longform_count']}",
        f"Total Views: {status['total_views']:,}",
        f"Watch Hours: {status['total_watch_hours']:,.1f}",
        "",
    ]

    if issues:
        lines.append("🚨 CRITICAL ISSUES TO ADDRESS FIRST:")
        lines.append("-" * 40)
        for issue in issues[:5]:
            lines.append(f"  [{issue['severity']}] {issue['skill']}")
        lines.append("")

    if high_recs:
        lines.append("⚡ HIGH PRIORITY ACTIONS:")
        lines.append("-" * 40)
        for rec in high_recs[:7]:
            lines.append(f"  • {rec['action']}")
            lines.append(f"    ({rec['skill']})")
        lines.append("")

    lines.extend([
        "Next Steps:",
        "  1. Address any critical issues first",
        "  2. Work through high-priority recommendations",
        "  3. Run 'trend_detector' skill weekly to track momentum",
        "  4. Run full analysis monthly to track progress",
        "",
        "=" * 60,
    ])

    return "\n".join(lines)


# For direct execution
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m youtube_expert.agent_runner <data_path> [skill_name]")
        print("\nAvailable skills:")
        for skill in list_available_skills():
            print(f"  {skill['name']}: {skill['description']}")
        sys.exit(0)

    data_path = sys.argv[1]

    if len(sys.argv) > 2:
        skill_name = sys.argv[2]
        result = run_skill(skill_name, data_path)
        if "digest" in result:
            print(result["digest"])
        else:
            print(json.dumps(result, indent=2, default=str))
    else:
        print(generate_action_plan(data_path))
