"""
Upload Scheduler Skill - Optimize posting times

Analyzes historical performance to identify optimal upload times,
posting frequency, and consistency patterns.
"""

from __future__ import annotations

from typing import Dict, Any, List, TYPE_CHECKING
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from .base import BaseSkill

if TYPE_CHECKING:
    from ..core import ChannelData


class UploadSchedulerSkill(BaseSkill):
    """
    Upload schedule optimization

    Analyzes when your videos perform best and recommends
    optimal posting times, frequency, and content cadence.
    """

    name = "upload_scheduler"
    description = "Optimal upload timing and frequency analysis"

    def analyze(self, data: ChannelData, **kwargs) -> Dict[str, Any]:
        if data.videos_df is None:
            return {"error": "No video data available"}

        df = data.videos_df.copy()

        # Filter out total/summary rows
        if 'video_id' in df.columns:
            df = df[df['video_id'].notna() & (df['video_id'] != 'Totalt')]

        if 'published_at' not in df.columns:
            return {"error": "No publish date data available"}

        df = df[df['published_at'].notna()].copy()

        if len(df) < 10:
            return {"error": "Insufficient data for schedule analysis"}

        metrics = {}
        insights = []
        recommendations = []

        # === POSTING FREQUENCY ===
        freq_analysis = self._analyze_posting_frequency(df)
        metrics.update(freq_analysis['metrics'])
        insights.extend(freq_analysis['insights'])

        # === DAY OF WEEK PERFORMANCE ===
        dow_analysis = self._analyze_day_of_week(df)
        metrics.update(dow_analysis['metrics'])
        insights.extend(dow_analysis['insights'])

        # === CONSISTENCY ANALYSIS ===
        consistency_analysis = self._analyze_consistency(df)
        metrics.update(consistency_analysis['metrics'])
        insights.extend(consistency_analysis['insights'])

        # === CONTENT TYPE CADENCE ===
        cadence_analysis = self._analyze_content_cadence(df)
        metrics.update(cadence_analysis['metrics'])

        # === BUILD RECOMMENDATIONS ===
        recommendations = self._build_recommendations(metrics)

        severity = self._calculate_severity(metrics)
        digest = self._generate_digest(metrics, insights, recommendations, severity)

        return {
            "metrics": metrics,
            "insights": insights,
            "recommendations": recommendations,
            "severity": severity,
            "digest": digest,
        }

    def _analyze_posting_frequency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze overall posting frequency"""
        insights = []

        df_sorted = df.sort_values('published_at')
        date_range = (df_sorted['published_at'].max() - df_sorted['published_at'].min()).days

        if date_range <= 0:
            return {"metrics": {}, "insights": []}

        total_videos = len(df)
        weeks = date_range / 7
        months = date_range / 30

        videos_per_week = total_videos / weeks if weeks > 0 else 0
        videos_per_month = total_videos / months if months > 0 else 0

        # Calculate gaps between uploads
        df_sorted['days_since_last'] = df_sorted['published_at'].diff().dt.days

        avg_gap = df_sorted['days_since_last'].mean()
        max_gap = df_sorted['days_since_last'].max()
        min_gap = df_sorted['days_since_last'].min()

        # Consistency score (lower variance = more consistent)
        gap_std = df_sorted['days_since_last'].std()
        consistency_score = max(0, 100 - (gap_std * 10))

        if videos_per_week < 1:
            insights.append(f"Low posting frequency: {videos_per_week:.1f} videos/week. Consider increasing to 2-3/week.")
        elif videos_per_week > 7:
            insights.append(f"High posting frequency: {videos_per_week:.1f} videos/week. Quality may suffer; monitor retention.")

        if max_gap > 14:
            insights.append(f"⚠️ Longest gap: {max_gap:.0f} days. Extended breaks hurt algorithm momentum.")

        metrics = {
            "date_range_days": date_range,
            "total_videos": total_videos,
            "videos_per_week": round(videos_per_week, 2),
            "videos_per_month": round(videos_per_month, 1),
            "avg_days_between_uploads": round(avg_gap, 1),
            "max_gap_days": int(max_gap) if pd.notna(max_gap) else None,
            "min_gap_days": int(min_gap) if pd.notna(min_gap) else None,
            "consistency_score": round(consistency_score, 0),
        }

        return {"metrics": metrics, "insights": insights}

    def _analyze_day_of_week(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze performance by day of week"""
        insights = []

        df['day_of_week'] = df['published_at'].dt.day_name()
        df['day_num'] = df['published_at'].dt.dayofweek

        # Group by day
        if 'views' in df.columns:
            day_stats = df.groupby(['day_of_week', 'day_num']).agg({
                'views': ['mean', 'sum', 'count'],
                'watch_hours': 'mean' if 'watch_hours' in df.columns else 'count',
            }).reset_index()

            day_stats.columns = ['day', 'day_num', 'avg_views', 'total_views', 'count', 'avg_watch_hours']
            day_stats = day_stats.sort_values('day_num')

            best_day = day_stats.loc[day_stats['avg_views'].idxmax()]
            worst_day = day_stats.loc[day_stats['avg_views'].idxmin()]

            if best_day['avg_views'] > worst_day['avg_views'] * 1.5:
                insights.append(f"Best posting day: {best_day['day']} ({best_day['avg_views']:,.0f} avg views)")
                insights.append(f"Weakest day: {worst_day['day']} ({worst_day['avg_views']:,.0f} avg views)")

            metrics = {
                "performance_by_day": day_stats[['day', 'avg_views', 'count']].to_dict('records'),
                "best_day": best_day['day'],
                "best_day_avg_views": round(best_day['avg_views'], 0),
                "worst_day": worst_day['day'],
                "worst_day_avg_views": round(worst_day['avg_views'], 0),
            }
        else:
            # Just count uploads
            day_counts = df['day_of_week'].value_counts()
            metrics = {
                "uploads_by_day": day_counts.to_dict(),
            }

        return {"metrics": metrics, "insights": insights}

    def _analyze_consistency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze upload consistency over time"""
        insights = []

        # Weekly upload counts
        df['week'] = df['published_at'].dt.isocalendar().week
        df['year'] = df['published_at'].dt.year
        df['year_week'] = df['year'].astype(str) + '-W' + df['week'].astype(str).str.zfill(2)

        weekly_counts = df.groupby('year_week').size()

        avg_weekly = weekly_counts.mean()
        std_weekly = weekly_counts.std()
        weeks_with_zero = 0  # Would need full date range to calculate

        # Trend: are we posting more or less over time?
        if len(weekly_counts) >= 4:
            first_half = weekly_counts.iloc[:len(weekly_counts)//2].mean()
            second_half = weekly_counts.iloc[len(weekly_counts)//2:].mean()

            if second_half > first_half * 1.2:
                insights.append("Posting frequency is increasing - good momentum!")
            elif second_half < first_half * 0.8:
                insights.append("⚠️ Posting frequency is declining")

        # Calculate upload streaks
        df_sorted = df.sort_values('published_at')
        df_sorted['week_key'] = df_sorted['year'].astype(str) + df_sorted['week'].astype(str)

        metrics = {
            "avg_videos_per_week": round(avg_weekly, 1),
            "std_videos_per_week": round(std_weekly, 1),
            "total_weeks_analyzed": len(weekly_counts),
            "most_active_week": weekly_counts.idxmax(),
            "most_active_week_count": int(weekly_counts.max()),
        }

        return {"metrics": metrics, "insights": insights}

    def _analyze_content_cadence(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze cadence by content type"""

        if 'content_type' not in df.columns:
            return {"metrics": {}}

        # Calculate frequency by type
        df_sorted = df.sort_values('published_at')
        date_range = (df_sorted['published_at'].max() - df_sorted['published_at'].min()).days
        weeks = date_range / 7 if date_range > 0 else 1

        type_counts = df.groupby('content_type').size()
        type_freq = (type_counts / weeks).round(2)

        metrics = {
            "shorts_per_week": type_freq.get('SHORT', 0),
            "longform_per_week": type_freq.get('LONGFORM', 0),
            "content_type_counts": type_counts.to_dict(),
        }

        return {"metrics": metrics}

    def _build_recommendations(self, metrics: Dict) -> List[Dict[str, str]]:
        """Build scheduling recommendations"""
        recommendations = []

        # Frequency recommendations
        vpw = metrics.get('videos_per_week', 0)
        if vpw < 1:
            recommendations.append({
                "priority": "HIGH",
                "action": "Increase posting frequency",
                "details": "Post at least 1-2 long-form videos and 3-5 Shorts per week to maintain algorithm momentum.",
            })
        elif vpw < 3:
            recommendations.append({
                "priority": "MEDIUM",
                "action": "Consider increasing Shorts frequency",
                "details": "Add 2-3 Shorts per week to supplement your long-form content and increase reach.",
            })

        # Consistency recommendations
        consistency = metrics.get('consistency_score', 100)
        if consistency < 50:
            recommendations.append({
                "priority": "HIGH",
                "action": "Create a consistent upload schedule",
                "details": "Inconsistent posting hurts algorithm performance. Set specific days/times and stick to them.",
            })

        # Day optimization
        best_day = metrics.get('best_day')
        worst_day = metrics.get('worst_day')
        if best_day and worst_day:
            recommendations.append({
                "priority": "MEDIUM",
                "action": f"Prioritize {best_day} for key content",
                "details": f"Your videos perform best on {best_day}. Save important releases for this day.",
            })

        # Gap management
        max_gap = metrics.get('max_gap_days', 0) or 0
        if max_gap > 7:
            recommendations.append({
                "priority": "MEDIUM",
                "action": "Build a content buffer",
                "details": "Maintain 2-3 ready-to-publish videos to avoid gaps during busy periods.",
            })

        return recommendations

    def _calculate_severity(self, metrics: Dict) -> str:
        """Calculate severity"""
        consistency = metrics.get('consistency_score', 100)
        vpw = metrics.get('videos_per_week', 2)

        if consistency < 40 or vpw < 0.5:
            return "WARNING"
        elif consistency < 60 or vpw < 1:
            return "WATCH"
        return "OK"

    def _generate_digest(self, metrics: Dict, insights: List,
                        recommendations: List, severity: str) -> str:
        """Generate human-readable summary"""
        lines = [
            "=" * 60,
            "UPLOAD SCHEDULE ANALYSIS",
            "=" * 60,
            "",
            f"Status: {severity}",
            "",
            "📅 POSTING FREQUENCY",
            f"  Videos per week: {metrics.get('videos_per_week', 0):.1f}",
            f"  Avg days between uploads: {metrics.get('avg_days_between_uploads', 0):.1f}",
            f"  Longest gap: {metrics.get('max_gap_days', 0)} days",
            f"  Consistency score: {metrics.get('consistency_score', 0):.0f}/100",
            "",
        ]

        if metrics.get('best_day'):
            lines.extend([
                "📊 BEST DAYS TO POST",
                f"  Best: {metrics.get('best_day')} ({metrics.get('best_day_avg_views', 0):,.0f} avg views)",
                f"  Worst: {metrics.get('worst_day')} ({metrics.get('worst_day_avg_views', 0):,.0f} avg views)",
                "",
            ])

        if metrics.get('shorts_per_week') is not None:
            lines.extend([
                "🎬 CONTENT CADENCE",
                f"  Shorts: {metrics.get('shorts_per_week', 0):.1f}/week",
                f"  Long-form: {metrics.get('longform_per_week', 0):.1f}/week",
                "",
            ])

        if insights:
            lines.append("💡 INSIGHTS")
            for insight in insights:
                lines.append(f"  • {insight}")
            lines.append("")

        if recommendations:
            lines.append("📝 RECOMMENDATIONS")
            for rec in recommendations[:4]:
                lines.append(f"  [{rec['priority']}] {rec['action']}")
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)
