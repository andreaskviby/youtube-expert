"""
Audience Analyzer Skill - Viewer retention and engagement analysis

Analyzes viewer behavior patterns, retention estimates, and engagement.
"""

from __future__ import annotations

from typing import Dict, Any, List, TYPE_CHECKING
import pandas as pd
import numpy as np

from .base import BaseSkill

if TYPE_CHECKING:
    from ..core import ChannelData


class AudienceAnalyzerSkill(BaseSkill):
    """
    Audience behavior analysis

    Analyzes viewer retention patterns, engagement metrics,
    and audience preferences to optimize content strategy.
    """

    name = "audience_analyzer"
    description = "Viewer retention and engagement analysis"

    def analyze(self, data: ChannelData, **kwargs) -> Dict[str, Any]:
        if data.videos_df is None:
            return {"error": "No video data available"}

        df = data.videos_df.copy()

        # Filter out total/summary rows
        if 'video_id' in df.columns:
            df = df[df['video_id'].notna() & (df['video_id'] != 'Totalt')]

        metrics = {}
        insights = []
        recommendations = []

        # === RETENTION ANALYSIS ===
        retention_analysis = self._analyze_retention(df)
        metrics.update(retention_analysis['metrics'])
        insights.extend(retention_analysis['insights'])

        # === ENGAGEMENT EFFICIENCY ===
        engagement_analysis = self._analyze_engagement_efficiency(df)
        metrics.update(engagement_analysis['metrics'])
        insights.extend(engagement_analysis['insights'])

        # === SUBSCRIBER CONVERSION ===
        sub_analysis = self._analyze_subscriber_conversion(df)
        metrics.update(sub_analysis['metrics'])
        insights.extend(sub_analysis['insights'])

        # === CONTENT PREFERENCES ===
        preferences = self._analyze_content_preferences(df)
        metrics.update(preferences['metrics'])

        # === BUILD RECOMMENDATIONS ===
        recommendations = self._build_recommendations(metrics, insights)

        severity = self._calculate_severity(metrics)
        digest = self._generate_digest(metrics, insights, recommendations, severity)

        return {
            "metrics": metrics,
            "insights": insights,
            "recommendations": recommendations,
            "severity": severity,
            "digest": digest,
        }

    def _analyze_retention(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze viewer retention patterns"""
        insights = []

        if 'retention_estimate' not in df.columns:
            if 'views' in df.columns and 'watch_hours' in df.columns and 'duration_seconds' in df.columns:
                # Calculate retention estimate
                df['avg_view_duration'] = (df['watch_hours'] * 60) / df['views'].replace(0, 1)
                df['retention_estimate'] = (df['avg_view_duration'] * 60) / df['duration_seconds'].replace(0, 1) * 100
                df['retention_estimate'] = df['retention_estimate'].clip(0, 100)
            else:
                return {"metrics": {}, "insights": []}

        # Separate by content type
        if 'is_short' in df.columns:
            shorts = df[df['is_short'] == True]
            longform = df[df['is_short'] == False]

            shorts_retention = shorts['retention_estimate'].mean() if len(shorts) > 0 else 0
            longform_retention = longform['retention_estimate'].mean() if len(longform) > 0 else 0

            # Retention by duration buckets (for long-form)
            if len(longform) > 10:
                longform = longform.copy()
                longform['duration_bucket'] = pd.cut(
                    longform['duration_seconds'] / 60,
                    bins=[0, 5, 10, 20, 30, float('inf')],
                    labels=['0-5min', '5-10min', '10-20min', '20-30min', '30min+']
                )
                retention_by_duration = longform.groupby('duration_bucket')['retention_estimate'].mean().to_dict()
            else:
                retention_by_duration = {}
        else:
            shorts_retention = longform_retention = 0
            retention_by_duration = {}

        avg_retention = df['retention_estimate'].mean()
        median_retention = df['retention_estimate'].median()

        # Find best and worst retention videos
        best_retention = df.nlargest(5, 'retention_estimate')[['video_id', 'title', 'retention_estimate', 'views']]
        worst_retention = df[df['views'] > 100].nsmallest(5, 'retention_estimate')[['video_id', 'title', 'retention_estimate', 'views']]

        if avg_retention < 30:
            insights.append(f"⚠️ Average retention ({avg_retention:.0f}%) is low. Viewers are leaving early.")
        elif avg_retention > 50:
            insights.append(f"Strong retention ({avg_retention:.0f}%). Content is keeping viewers engaged.")

        if longform_retention > 0 and longform_retention < 25:
            insights.append("Long-form retention is weak. Consider shorter videos or better pacing.")

        metrics = {
            "avg_retention": round(avg_retention, 1),
            "median_retention": round(median_retention, 1),
            "shorts_avg_retention": round(shorts_retention, 1),
            "longform_avg_retention": round(longform_retention, 1),
            "retention_by_duration": {k: round(v, 1) for k, v in retention_by_duration.items()},
            "best_retention_videos": best_retention.to_dict('records'),
            "worst_retention_videos": worst_retention.to_dict('records'),
        }

        return {"metrics": metrics, "insights": insights}

    def _analyze_engagement_efficiency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze how efficiently content generates engagement"""
        insights = []

        if 'views' not in df.columns or 'watch_hours' not in df.columns:
            return {"metrics": {}, "insights": []}

        # Minutes watched per view
        df['minutes_per_view'] = (df['watch_hours'] * 60) / df['views'].replace(0, 1)

        avg_minutes_per_view = df['minutes_per_view'].mean()

        # By content type
        if 'is_short' in df.columns:
            shorts_mpv = df[df['is_short'] == True]['minutes_per_view'].mean()
            longform_mpv = df[df['is_short'] == False]['minutes_per_view'].mean()
        else:
            shorts_mpv = longform_mpv = 0

        # Views to watch hours efficiency
        total_views = df['views'].sum()
        total_hours = df['watch_hours'].sum()
        overall_efficiency = (total_hours * 60) / total_views if total_views > 0 else 0

        metrics = {
            "avg_minutes_per_view": round(avg_minutes_per_view, 2),
            "shorts_minutes_per_view": round(shorts_mpv, 2) if pd.notna(shorts_mpv) else 0,
            "longform_minutes_per_view": round(longform_mpv, 2) if pd.notna(longform_mpv) else 0,
            "overall_efficiency_minutes": round(overall_efficiency, 2),
        }

        return {"metrics": metrics, "insights": insights}

    def _analyze_subscriber_conversion(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze how effectively videos convert viewers to subscribers"""
        insights = []

        if 'subscribers_gained' not in df.columns or 'views' not in df.columns:
            return {"metrics": {}, "insights": []}

        # Subs per 1K views
        df['subs_per_1k'] = (df['subscribers_gained'] / df['views'].replace(0, 1)) * 1000

        avg_subs_per_1k = df['subs_per_1k'].mean()
        median_subs_per_1k = df['subs_per_1k'].median()

        # Top converters
        top_converters = df[df['views'] > 1000].nlargest(5, 'subs_per_1k')[['video_id', 'title', 'subs_per_1k', 'views']]

        # By content type
        if 'is_short' in df.columns:
            shorts_conversion = df[df['is_short'] == True]['subs_per_1k'].mean()
            longform_conversion = df[df['is_short'] == False]['subs_per_1k'].mean()

            if shorts_conversion > longform_conversion * 2:
                insights.append(f"Shorts convert {shorts_conversion / longform_conversion:.1f}x better than long-form")
        else:
            shorts_conversion = longform_conversion = 0

        if avg_subs_per_1k > 1:
            insights.append(f"Good subscriber conversion rate ({avg_subs_per_1k:.1f} subs/1K views)")
        elif avg_subs_per_1k < 0.3:
            insights.append("Low subscriber conversion. Add stronger subscribe CTAs.")

        metrics = {
            "avg_subs_per_1k_views": round(avg_subs_per_1k, 2),
            "median_subs_per_1k_views": round(median_subs_per_1k, 2),
            "shorts_subs_per_1k": round(shorts_conversion, 2) if pd.notna(shorts_conversion) else 0,
            "longform_subs_per_1k": round(longform_conversion, 2) if pd.notna(longform_conversion) else 0,
            "top_converting_videos": top_converters.to_dict('records'),
        }

        return {"metrics": metrics, "insights": insights}

    def _analyze_content_preferences(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze what content resonates most with the audience"""

        if 'views' not in df.columns or 'title' not in df.columns:
            return {"metrics": {}}

        # Ideal video length (by performance)
        if 'duration_seconds' in df.columns and 'is_short' in df.columns:
            longform = df[df['is_short'] == False].copy()

            if len(longform) > 5:
                # Find optimal length range
                longform['duration_minutes'] = longform['duration_seconds'] / 60

                # Weight by views
                total_views = longform['views'].sum()
                longform['view_weight'] = longform['views'] / total_views

                weighted_avg_duration = (longform['duration_minutes'] * longform['view_weight']).sum()

                # Duration buckets performance
                longform['duration_bucket'] = pd.cut(
                    longform['duration_minutes'],
                    bins=[0, 5, 10, 15, 20, 30, float('inf')],
                    labels=['<5min', '5-10min', '10-15min', '15-20min', '20-30min', '>30min']
                )

                duration_performance = longform.groupby('duration_bucket').agg({
                    'views': 'mean',
                    'watch_hours': 'mean',
                }).round(0).to_dict()

                optimal_duration = longform.groupby('duration_bucket')['views'].mean().idxmax()
            else:
                weighted_avg_duration = 0
                duration_performance = {}
                optimal_duration = "N/A"
        else:
            weighted_avg_duration = 0
            duration_performance = {}
            optimal_duration = "N/A"

        metrics = {
            "weighted_avg_duration_minutes": round(weighted_avg_duration, 1),
            "duration_bucket_performance": duration_performance,
            "optimal_duration_bucket": str(optimal_duration),
        }

        return {"metrics": metrics}

    def _build_recommendations(self, metrics: Dict, insights: List) -> List[Dict[str, str]]:
        """Build recommendations based on audience analysis"""
        recommendations = []

        # Retention recommendations
        avg_retention = metrics.get('avg_retention', 50)
        if avg_retention < 30:
            recommendations.append({
                "priority": "HIGH",
                "action": "Improve video hooks in first 30 seconds",
                "details": "Low retention indicates viewers leave early. Start with the payoff, then explain.",
            })

        longform_retention = metrics.get('longform_avg_retention', 50)
        if longform_retention < 25:
            recommendations.append({
                "priority": "HIGH",
                "action": "Add pattern interrupts to long-form videos",
                "details": "Use visual changes, B-roll, and graphics every 2-3 minutes to reset attention.",
            })

        # Subscriber conversion
        subs_per_1k = metrics.get('avg_subs_per_1k_views', 1)
        if subs_per_1k < 0.5:
            recommendations.append({
                "priority": "MEDIUM",
                "action": "Strengthen subscribe calls-to-action",
                "details": "Add verbal CTAs at high-engagement moments, not just at the end.",
            })

        # Duration optimization
        optimal = metrics.get('optimal_duration_bucket', 'N/A')
        if optimal != 'N/A':
            recommendations.append({
                "priority": "MEDIUM",
                "action": f"Target {optimal} for long-form videos",
                "details": "This duration range performs best with your audience.",
            })

        return recommendations

    def _calculate_severity(self, metrics: Dict) -> str:
        """Calculate severity"""
        avg_retention = metrics.get('avg_retention', 50)

        if avg_retention < 20:
            return "WARNING"
        elif avg_retention < 35:
            return "WATCH"
        return "OK"

    def _generate_digest(self, metrics: Dict, insights: List,
                        recommendations: List, severity: str) -> str:
        """Generate human-readable summary"""
        lines = [
            "=" * 60,
            "AUDIENCE ANALYSIS REPORT",
            "=" * 60,
            "",
            f"Status: {severity}",
            "",
            "📺 VIEWER RETENTION",
            f"  Average: {metrics.get('avg_retention', 0):.0f}%",
            f"  Shorts: {metrics.get('shorts_avg_retention', 0):.0f}%",
            f"  Long-form: {metrics.get('longform_avg_retention', 0):.0f}%",
            "",
            "👥 SUBSCRIBER CONVERSION",
            f"  Avg subs per 1K views: {metrics.get('avg_subs_per_1k_views', 0):.2f}",
            f"  Shorts: {metrics.get('shorts_subs_per_1k', 0):.2f}",
            f"  Long-form: {metrics.get('longform_subs_per_1k', 0):.2f}",
            "",
            "⏱️ ENGAGEMENT",
            f"  Avg minutes per view: {metrics.get('avg_minutes_per_view', 0):.1f}",
            "",
        ]

        optimal = metrics.get('optimal_duration_bucket', 'N/A')
        if optimal != 'N/A':
            lines.extend([
                "🎯 OPTIMAL CONTENT",
                f"  Best performing duration: {optimal}",
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
