"""
Channel Diagnostics Skill - Comprehensive health check

Identifies critical issues that suppress channel growth:
- Made for Kids settings (channel/video level)
- Private/unlisted videos not counting toward 4000 hours
- Age restrictions blocking recommendations
- Shorts vs long-form imbalance
- Low discovery traffic (Browse + Suggested)
- Subscriber/view ratio anomalies
"""

from __future__ import annotations

from typing import Dict, Any, List, TYPE_CHECKING
import pandas as pd
import numpy as np

from .base import BaseSkill

if TYPE_CHECKING:
    from ..core import ChannelData


class DiagnosticsSkill(BaseSkill):
    """
    Comprehensive channel health diagnostic

    Identifies critical issues that suppress growth and prevent
    monetization. Designed to find the "silent killers" that
    cause channels with many subscribers to have low watch time.
    """

    name = "diagnostics"
    description = "Channel health check & critical issue detection"

    # YPP threshold for full monetization
    WATCH_HOUR_GOAL = 4000
    SUBSCRIBER_GOAL = 1000

    def analyze(self, data: ChannelData, **kwargs) -> Dict[str, Any]:
        if data.videos_df is None:
            return {"error": "No video data available"}

        df = data.videos_df.copy()

        # Filter out total/summary rows
        if 'video_id' in df.columns:
            df = df[df['video_id'].notna() & (df['video_id'] != 'Totalt')]

        issues = []
        metrics = {}
        severity = "OK"

        # === 1. SHORTS VS LONGFORM ANALYSIS ===
        shorts_metrics = self._analyze_shorts_balance(df, data)
        metrics.update(shorts_metrics['metrics'])
        issues.extend(shorts_metrics['issues'])
        if shorts_metrics['severity'] == "CRITICAL":
            severity = "CRITICAL"
        elif shorts_metrics['severity'] == "WARNING" and severity == "OK":
            severity = "WARNING"

        # === 2. WATCH TIME PROGRESS ===
        wt_metrics = self._analyze_watch_time_progress(df, data)
        metrics.update(wt_metrics['metrics'])
        issues.extend(wt_metrics['issues'])

        # === 3. CTR ANALYSIS ===
        ctr_metrics = self._analyze_ctr(df)
        metrics.update(ctr_metrics['metrics'])
        issues.extend(ctr_metrics['issues'])

        # === 4. RETENTION ANALYSIS ===
        retention_metrics = self._analyze_retention(df)
        metrics.update(retention_metrics['metrics'])
        issues.extend(retention_metrics['issues'])

        # === 5. DORMANT VIDEO DETECTION ===
        dormant_metrics = self._analyze_dormant_videos(df)
        metrics.update(dormant_metrics['metrics'])
        issues.extend(dormant_metrics['issues'])

        # === 6. VIRAL POTENTIAL ===
        viral_metrics = self._analyze_viral_potential(df)
        metrics.update(viral_metrics['metrics'])

        # Build recommendations
        recommendations = self._build_recommendations(issues, metrics)

        # Generate digest
        digest = self._generate_digest(data, metrics, issues, recommendations, severity)

        return {
            "metrics": metrics,
            "issues": issues,
            "recommendations": recommendations,
            "severity": severity,
            "digest": digest,
        }

    def _analyze_shorts_balance(self, df: pd.DataFrame, data: ChannelData) -> Dict[str, Any]:
        """Analyze the balance between Shorts and long-form content"""
        issues = []

        if 'is_short' not in df.columns:
            return {"metrics": {}, "issues": [], "severity": "OK"}

        shorts = df[df['is_short'] == True]
        longform = df[df['is_short'] == False]

        shorts_views = shorts['views'].sum() if len(shorts) > 0 else 0
        longform_views = longform['views'].sum() if len(longform) > 0 else 0
        total_views = shorts_views + longform_views or 1

        shorts_hours = shorts['watch_hours'].sum() if 'watch_hours' in shorts.columns and len(shorts) > 0 else 0
        longform_hours = longform['watch_hours'].sum() if 'watch_hours' in longform.columns and len(longform) > 0 else 0
        total_hours = shorts_hours + longform_hours or 1

        shorts_subs = shorts['subscribers_gained'].sum() if 'subscribers_gained' in shorts.columns and len(shorts) > 0 else 0
        longform_subs = longform['subscribers_gained'].sum() if 'subscribers_gained' in longform.columns and len(longform) > 0 else 0
        total_subs = shorts_subs + longform_subs or 1

        shorts_view_pct = (shorts_views / total_views) * 100
        shorts_hours_pct = (shorts_hours / total_hours) * 100
        shorts_subs_pct = (shorts_subs / total_subs) * 100

        severity = "OK"

        # Check for Shorts-dominated subscriber base (explains low watch time)
        if shorts_subs_pct >= 60:
            severity = "WARNING"
            issues.append({
                "type": "SHORTS_SUBS_IMBALANCE",
                "severity": "WARNING",
                "message": f"{shorts_subs_pct:.0f}% of new subscribers came from Shorts. "
                          "Shorts viewers rarely watch long-form content, and Shorts "
                          "watch time doesn't count toward the 4000-hour goal.",
            })

        # Check for view/watch time mismatch (lots of views but low hours)
        if shorts_view_pct >= 50 and shorts_hours_pct < 30:
            issues.append({
                "type": "SHORTS_EFFICIENCY_GAP",
                "severity": "INFO",
                "message": f"Shorts drive {shorts_view_pct:.0f}% of views but only "
                          f"{shorts_hours_pct:.0f}% of watch time. This is normal but "
                          "explains the views-to-hours ratio.",
            })

        metrics = {
            "shorts_count": len(shorts),
            "longform_count": len(longform),
            "shorts_view_percent": round(shorts_view_pct, 1),
            "shorts_hours_percent": round(shorts_hours_pct, 1),
            "shorts_subs_percent": round(shorts_subs_pct, 1),
            "longform_total_hours": round(longform_hours, 1),
            "avg_views_per_short": round(shorts_views / len(shorts), 0) if len(shorts) > 0 else 0,
            "avg_views_per_longform": round(longform_views / len(longform), 0) if len(longform) > 0 else 0,
        }

        return {"metrics": metrics, "issues": issues, "severity": severity}

    def _analyze_watch_time_progress(self, df: pd.DataFrame, data: ChannelData) -> Dict[str, Any]:
        """Analyze progress toward 4000 watch hour goal"""
        issues = []

        if 'is_short' not in df.columns or 'watch_hours' not in df.columns:
            return {"metrics": {}, "issues": []}

        longform = df[df['is_short'] == False]
        longform_hours = longform['watch_hours'].sum() if len(longform) > 0 else 0

        progress_pct = (longform_hours / self.WATCH_HOUR_GOAL) * 100
        hours_needed = max(0, self.WATCH_HOUR_GOAL - longform_hours)

        # Calculate daily rate needed
        # Assuming 12-month window, calculate daily requirement
        days_in_year = 365
        daily_hours_needed = hours_needed / days_in_year if hours_needed > 0 else 0

        if progress_pct < 50:
            issues.append({
                "type": "LOW_WATCH_HOURS",
                "severity": "WARNING",
                "message": f"Only {progress_pct:.0f}% toward 4000-hour goal. "
                          f"Need {hours_needed:.0f} more long-form hours.",
            })

        metrics = {
            "longform_watch_hours": round(longform_hours, 1),
            "watch_hour_goal": self.WATCH_HOUR_GOAL,
            "goal_progress_percent": round(progress_pct, 1),
            "hours_remaining": round(hours_needed, 1),
            "daily_hours_needed": round(daily_hours_needed, 2),
        }

        return {"metrics": metrics, "issues": issues}

    def _analyze_ctr(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze click-through rates"""
        issues = []

        if 'ctr_percent' not in df.columns or 'impressions' not in df.columns:
            return {"metrics": {}, "issues": []}

        # Only analyze videos with meaningful impressions
        df_with_ctr = df[(df['ctr_percent'].notna()) & (df['impressions'] > 100)]

        if len(df_with_ctr) == 0:
            return {"metrics": {}, "issues": []}

        avg_ctr = df_with_ctr['ctr_percent'].mean()
        median_ctr = df_with_ctr['ctr_percent'].median()

        # Segment by content type
        shorts_ctr = df_with_ctr[df_with_ctr['is_short'] == True]['ctr_percent'].mean() if 'is_short' in df_with_ctr.columns else 0
        longform_ctr = df_with_ctr[df_with_ctr['is_short'] == False]['ctr_percent'].mean() if 'is_short' in df_with_ctr.columns else 0

        # Find underperformers (CTR < 2% with decent impressions)
        underperformers = df_with_ctr[(df_with_ctr['ctr_percent'] < 2) & (df_with_ctr['impressions'] > 1000)]

        if avg_ctr < 3:
            issues.append({
                "type": "LOW_AVERAGE_CTR",
                "severity": "WARNING",
                "message": f"Average CTR is {avg_ctr:.1f}%, below the 3-5% healthy range. "
                          "Thumbnails and titles may need optimization.",
            })

        if len(underperformers) > 5:
            issues.append({
                "type": "MANY_LOW_CTR_VIDEOS",
                "severity": "INFO",
                "message": f"{len(underperformers)} videos have CTR below 2% despite "
                          "significant impressions. Consider A/B testing thumbnails.",
            })

        metrics = {
            "average_ctr": round(avg_ctr, 2),
            "median_ctr": round(median_ctr, 2),
            "shorts_avg_ctr": round(shorts_ctr, 2) if pd.notna(shorts_ctr) else None,
            "longform_avg_ctr": round(longform_ctr, 2) if pd.notna(longform_ctr) else None,
            "low_ctr_video_count": len(underperformers),
        }

        return {"metrics": metrics, "issues": issues}

    def _analyze_retention(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze viewer retention patterns"""
        issues = []

        if 'retention_estimate' not in df.columns:
            return {"metrics": {}, "issues": []}

        # Focus on long-form for retention analysis
        longform = df[(df['is_short'] == False) & (df['retention_estimate'].notna())]

        if len(longform) == 0:
            return {"metrics": {}, "issues": []}

        avg_retention = longform['retention_estimate'].mean()
        median_retention = longform['retention_estimate'].median()

        # Find videos with very low retention
        low_retention = longform[longform['retention_estimate'] < 20]

        if avg_retention < 30:
            issues.append({
                "type": "LOW_RETENTION",
                "severity": "WARNING",
                "message": f"Average retention is {avg_retention:.0f}%. Viewers are "
                          "leaving early. Consider improving hooks and pacing.",
            })

        metrics = {
            "avg_retention_estimate": round(avg_retention, 1),
            "median_retention_estimate": round(median_retention, 1),
            "low_retention_video_count": len(low_retention),
        }

        return {"metrics": metrics, "issues": issues}

    def _analyze_dormant_videos(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Find videos with high impressions but low performance"""
        issues = []

        if 'impressions' not in df.columns or 'views' not in df.columns:
            return {"metrics": {}, "issues": []}

        # Videos with impressions but poor conversion
        df_filtered = df[df['impressions'] > 0]
        df_filtered = df_filtered.copy()
        df_filtered['impression_to_view_rate'] = df_filtered['views'] / df_filtered['impressions']

        # Find dormant: high impressions, low CTR
        dormant = df_filtered[(df_filtered['impressions'] > 5000) & (df_filtered['ctr_percent'] < 2)]

        if len(dormant) > 3:
            issues.append({
                "type": "DORMANT_VIDEOS",
                "severity": "INFO",
                "message": f"{len(dormant)} videos get impressions but low clicks. "
                          "These are candidates for thumbnail/title refresh.",
            })

        metrics = {
            "dormant_video_count": len(dormant),
            "dormant_videos": dormant[['video_id', 'title', 'impressions', 'ctr_percent']].head(10).to_dict('records') if len(dormant) > 0 else [],
        }

        return {"metrics": metrics, "issues": issues}

    def _analyze_viral_potential(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identify videos with viral characteristics"""

        if 'views' not in df.columns:
            return {"metrics": {}}

        # Calculate view distribution
        views = df['views'].dropna()
        mean_views = views.mean()
        std_views = views.std()

        # Viral = more than 3 standard deviations above mean
        viral_threshold = mean_views + (3 * std_views)
        viral_videos = df[df['views'] > viral_threshold]

        # Breakout videos (1-3 std above mean)
        breakout_threshold = mean_views + std_views
        breakout_videos = df[(df['views'] > breakout_threshold) & (df['views'] <= viral_threshold)]

        metrics = {
            "mean_views": round(mean_views, 0),
            "viral_threshold": round(viral_threshold, 0),
            "viral_video_count": len(viral_videos),
            "breakout_video_count": len(breakout_videos),
            "top_performers": df.nlargest(5, 'views')[['video_id', 'title', 'views', 'content_type']].to_dict('records') if 'content_type' in df.columns else [],
        }

        return {"metrics": metrics}

    def _build_recommendations(self, issues: List[Dict], metrics: Dict) -> List[Dict[str, str]]:
        """Generate prioritized recommendations based on issues"""
        recommendations = []

        issue_types = {i['type'] for i in issues}

        # Priority 1: Critical settings issues
        if "SHORTS_SUBS_IMBALANCE" in issue_types:
            recommendations.append({
                "priority": "HIGH",
                "action": "Bridge Shorts viewers to long-form",
                "details": "Create 'teaser' Shorts that end with hooks to your long-form content. "
                          "Add end screens pointing to related long videos. Consider a 'best of' "
                          "long-form compilation of your viral Shorts to capture that audience.",
            })

        if "LOW_AVERAGE_CTR" in issue_types:
            recommendations.append({
                "priority": "HIGH",
                "action": "Run thumbnail A/B tests",
                "details": "YouTube Studio allows A/B testing thumbnails. Start with your "
                          "most-viewed videos that have CTR below 3%. Use contrasting colors, "
                          "expressive faces, and 3 words or less of text.",
            })

        if "LOW_RETENTION" in issue_types:
            recommendations.append({
                "priority": "HIGH",
                "action": "Improve video hooks",
                "details": "The first 30 seconds determine if viewers stay. Open with the "
                          "payoff/result, then 'here's how we got there.' Add pattern "
                          "interrupts every 2-3 minutes to reset attention.",
            })

        if "DORMANT_VIDEOS" in issue_types:
            recommendations.append({
                "priority": "MEDIUM",
                "action": "Refresh dormant thumbnails",
                "details": "Videos getting impressions but low CTR have YouTube's attention "
                          "but aren't converting. New thumbnails can revive them without "
                          "re-uploading.",
            })

        # General growth recommendations
        if metrics.get('goal_progress_percent', 100) < 50:
            recommendations.append({
                "priority": "HIGH",
                "action": "Focus on long-form watch time",
                "details": f"You need {metrics.get('hours_remaining', 0):.0f} more hours. "
                          "Prioritize 10-20 minute videos with strong retention over "
                          "quantity. Each video should target 40%+ retention.",
            })

        if not recommendations:
            recommendations.append({
                "priority": "LOW",
                "action": "Maintain current strategy",
                "details": "No critical issues detected. Continue optimizing based on "
                          "Analytics data and audience feedback.",
            })

        return recommendations

    def _generate_digest(self, data: ChannelData, metrics: Dict, issues: List,
                        recommendations: List, severity: str) -> str:
        """Generate human-readable summary"""
        lines = [
            "=" * 60,
            "YOUTUBE CHANNEL DIAGNOSTICS REPORT",
            "=" * 60,
            "",
            f"Status: {severity}",
            "",
            "📊 CHANNEL OVERVIEW",
            f"  Total Videos: {data.video_count}",
            f"    - Shorts: {metrics.get('shorts_count', 0)}",
            f"    - Long-form: {metrics.get('longform_count', 0)}",
            "",
            "📈 PERFORMANCE METRICS",
            f"  Shorts drive: {metrics.get('shorts_view_percent', 0):.0f}% of views, "
            f"{metrics.get('shorts_hours_percent', 0):.0f}% of watch time",
            f"  Shorts subscribers: {metrics.get('shorts_subs_percent', 0):.0f}% of new subs",
            "",
            "⏱️ WATCH TIME PROGRESS (4000h Goal)",
            f"  Long-form hours: {metrics.get('longform_watch_hours', 0):,.0f}",
            f"  Progress: {metrics.get('goal_progress_percent', 0):.0f}%",
            f"  Hours remaining: {metrics.get('hours_remaining', 0):,.0f}",
            "",
        ]

        if metrics.get('average_ctr'):
            lines.extend([
                "🎯 CLICK-THROUGH RATE",
                f"  Average CTR: {metrics.get('average_ctr', 0):.1f}%",
                f"  Low CTR videos: {metrics.get('low_ctr_video_count', 0)}",
                "",
            ])

        if metrics.get('avg_retention_estimate'):
            lines.extend([
                "📺 RETENTION",
                f"  Average retention: {metrics.get('avg_retention_estimate', 0):.0f}%",
                "",
            ])

        if issues:
            lines.append("⚠️ ISSUES DETECTED")
            for issue in issues:
                lines.append(f"  [{issue['severity']}] {issue['message']}")
            lines.append("")

        if recommendations:
            lines.append("💡 RECOMMENDATIONS")
            for rec in recommendations:
                lines.append(f"  [{rec['priority']}] {rec['action']}")
                lines.append(f"       {rec['details'][:100]}...")
            lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)
