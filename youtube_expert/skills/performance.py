"""
Performance Analysis Skill - Deep dive into video performance

Analyzes individual video metrics, identifies patterns, and
provides insights on what's working and what's not.
"""

from __future__ import annotations

from typing import Dict, Any, List, TYPE_CHECKING
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from .base import BaseSkill

if TYPE_CHECKING:
    from ..core import ChannelData


class PerformanceSkill(BaseSkill):
    """
    Deep video performance analysis

    Analyzes views, watch time, CTR, retention, and engagement
    to identify top performers, underperformers, and patterns
    that predict success.
    """

    name = "performance"
    description = "Deep video performance metrics analysis"

    def analyze(self, data: ChannelData, **kwargs) -> Dict[str, Any]:
        if data.videos_df is None:
            return {"error": "No video data available"}

        df = data.videos_df.copy()

        # Filter out total/summary rows
        if 'video_id' in df.columns:
            df = df[df['video_id'].notna() & (df['video_id'] != 'Totalt')]

        # Calculate performance scores
        df = self._calculate_performance_scores(df)

        metrics = {}
        insights = []

        # === TOP PERFORMERS ===
        top_metrics = self._analyze_top_performers(df)
        metrics.update(top_metrics)

        # === UNDERPERFORMERS ===
        under_metrics = self._analyze_underperformers(df)
        metrics.update(under_metrics)

        # === CONTENT TYPE PERFORMANCE ===
        content_metrics = self._analyze_by_content_type(df)
        metrics.update(content_metrics)

        # === EFFICIENCY ANALYSIS ===
        efficiency_metrics = self._analyze_efficiency(df)
        metrics.update(efficiency_metrics)

        # === TREND ANALYSIS ===
        if 'published_at' in df.columns:
            trend_metrics = self._analyze_trends(df)
            metrics.update(trend_metrics)

        # === GENERATE INSIGHTS ===
        insights = self._generate_insights(metrics)

        # Build recommendations
        recommendations = self._build_recommendations(metrics, insights)

        # Generate digest
        digest = self._generate_digest(metrics, insights, recommendations)

        return {
            "metrics": metrics,
            "insights": insights,
            "recommendations": recommendations,
            "severity": self._calculate_severity(metrics),
            "digest": digest,
        }

    def _calculate_performance_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate composite performance scores for each video"""

        # Normalize metrics to 0-100 scale
        numeric_cols = ['views', 'watch_hours', 'ctr_percent', 'impressions']

        for col in numeric_cols:
            if col in df.columns:
                max_val = df[col].max()
                if max_val > 0:
                    df[f'{col}_normalized'] = (df[col] / max_val) * 100

        # Calculate composite score
        score_components = []
        if 'views_normalized' in df.columns:
            score_components.append(df['views_normalized'] * 0.3)
        if 'watch_hours_normalized' in df.columns:
            score_components.append(df['watch_hours_normalized'] * 0.4)
        if 'ctr_percent' in df.columns:
            # CTR is already a percentage, scale appropriately
            score_components.append((df['ctr_percent'] / 10) * 100 * 0.3)

        if score_components:
            df['performance_score'] = sum(score_components) / len(score_components)
        else:
            df['performance_score'] = 50

        return df

    def _analyze_top_performers(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identify and analyze top performing videos"""

        top_by_views = df.nlargest(10, 'views') if 'views' in df.columns else pd.DataFrame()
        top_by_hours = df.nlargest(10, 'watch_hours') if 'watch_hours' in df.columns else pd.DataFrame()
        top_by_ctr = df[df['impressions'] > 1000].nlargest(10, 'ctr_percent') if 'ctr_percent' in df.columns and 'impressions' in df.columns else pd.DataFrame()

        # Views per hour of content (efficiency)
        if 'views' in df.columns and 'watch_hours' in df.columns:
            df_efficiency = df[df['watch_hours'] > 0].copy()
            df_efficiency['views_per_watch_hour'] = df_efficiency['views'] / df_efficiency['watch_hours']
            top_by_efficiency = df_efficiency.nlargest(10, 'views_per_watch_hour')
        else:
            top_by_efficiency = pd.DataFrame()

        return {
            "top_10_by_views": self._videos_to_list(top_by_views),
            "top_10_by_watch_hours": self._videos_to_list(top_by_hours),
            "top_10_by_ctr": self._videos_to_list(top_by_ctr),
            "top_10_by_efficiency": self._videos_to_list(top_by_efficiency),
        }

    def _analyze_underperformers(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identify underperforming videos that need attention"""

        if 'performance_score' not in df.columns:
            return {}

        # Bottom performers
        bottom = df.nsmallest(10, 'performance_score')

        # Videos with potential (high impressions, low CTR)
        if 'impressions' in df.columns and 'ctr_percent' in df.columns:
            high_impression_low_ctr = df[(df['impressions'] > 5000) & (df['ctr_percent'] < 2)].nlargest(10, 'impressions')
        else:
            high_impression_low_ctr = pd.DataFrame()

        # Videos with good CTR but low retention
        if 'ctr_percent' in df.columns and 'retention_estimate' in df.columns:
            good_ctr_low_retention = df[(df['ctr_percent'] > 4) & (df['retention_estimate'] < 30)].nlargest(10, 'views')
        else:
            good_ctr_low_retention = pd.DataFrame()

        return {
            "bottom_10_performers": self._videos_to_list(bottom),
            "needs_thumbnail_refresh": self._videos_to_list(high_impression_low_ctr),
            "needs_content_optimization": self._videos_to_list(good_ctr_low_retention),
        }

    def _analyze_by_content_type(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze performance split by content type"""

        if 'content_type' not in df.columns:
            return {}

        grouped = df.groupby('content_type').agg({
            'views': ['sum', 'mean', 'count'],
            'watch_hours': ['sum', 'mean'] if 'watch_hours' in df.columns else [],
            'ctr_percent': 'mean' if 'ctr_percent' in df.columns else [],
            'subscribers_gained': 'sum' if 'subscribers_gained' in df.columns else [],
        }).round(2)

        # Flatten column names
        grouped.columns = ['_'.join(col).strip() for col in grouped.columns.values]

        return {
            "performance_by_content_type": grouped.to_dict(),
            "shorts_vs_longform_summary": {
                "shorts": {
                    "count": int(df[df['content_type'] == 'SHORT']['views'].count()) if len(df[df['content_type'] == 'SHORT']) > 0 else 0,
                    "total_views": int(df[df['content_type'] == 'SHORT']['views'].sum()) if len(df[df['content_type'] == 'SHORT']) > 0 else 0,
                    "avg_views": round(df[df['content_type'] == 'SHORT']['views'].mean(), 0) if len(df[df['content_type'] == 'SHORT']) > 0 else 0,
                },
                "longform": {
                    "count": int(df[df['content_type'] == 'LONGFORM']['views'].count()) if len(df[df['content_type'] == 'LONGFORM']) > 0 else 0,
                    "total_views": int(df[df['content_type'] == 'LONGFORM']['views'].sum()) if len(df[df['content_type'] == 'LONGFORM']) > 0 else 0,
                    "avg_views": round(df[df['content_type'] == 'LONGFORM']['views'].mean(), 0) if len(df[df['content_type'] == 'LONGFORM']) > 0 else 0,
                },
            },
        }

    def _analyze_efficiency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze content efficiency metrics"""

        if 'views' not in df.columns or 'duration_seconds' not in df.columns:
            return {}

        # Views per minute of content created
        df_with_duration = df[df['duration_seconds'] > 0].copy()
        df_with_duration['views_per_content_minute'] = df_with_duration['views'] / (df_with_duration['duration_seconds'] / 60)

        # Subscriber efficiency (subs gained per 1000 views)
        if 'subscribers_gained' in df.columns:
            df_with_views = df[df['views'] > 0].copy()
            df_with_views['subs_per_1k_views'] = (df_with_views['subscribers_gained'] / df_with_views['views']) * 1000

            avg_sub_efficiency = df_with_views['subs_per_1k_views'].mean()
        else:
            avg_sub_efficiency = 0

        return {
            "avg_views_per_content_minute": round(df_with_duration['views_per_content_minute'].mean(), 1),
            "avg_subs_per_1k_views": round(avg_sub_efficiency, 2),
            "total_content_hours": round(df['duration_seconds'].sum() / 3600, 1),
        }

    def _analyze_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze performance trends over time"""

        df_dated = df[df['published_at'].notna()].copy()

        if len(df_dated) < 5:
            return {}

        df_dated = df_dated.sort_values('published_at')

        # Calculate rolling averages
        df_dated['rolling_views'] = df_dated['views'].rolling(5, min_periods=1).mean()

        # Recent vs older performance
        midpoint = len(df_dated) // 2
        older_half = df_dated.iloc[:midpoint]
        recent_half = df_dated.iloc[midpoint:]

        older_avg_views = older_half['views'].mean()
        recent_avg_views = recent_half['views'].mean()

        trend_direction = "improving" if recent_avg_views > older_avg_views else "declining"
        trend_magnitude = ((recent_avg_views - older_avg_views) / older_avg_views * 100) if older_avg_views > 0 else 0

        return {
            "trend_direction": trend_direction,
            "trend_magnitude_percent": round(trend_magnitude, 1),
            "older_period_avg_views": round(older_avg_views, 0),
            "recent_period_avg_views": round(recent_avg_views, 0),
        }

    def _videos_to_list(self, df: pd.DataFrame, max_items: int = 10) -> List[Dict]:
        """Convert DataFrame to list of video dicts"""
        if df.empty:
            return []

        cols_to_include = ['video_id', 'title', 'views', 'watch_hours', 'ctr_percent', 'content_type', 'duration_seconds']
        available_cols = [c for c in cols_to_include if c in df.columns]

        result = df[available_cols].head(max_items).to_dict('records')

        # Clean up numeric values
        for item in result:
            for key, value in item.items():
                if isinstance(value, float) and pd.notna(value):
                    item[key] = round(value, 2)
                elif pd.isna(value):
                    item[key] = None

        return result

    def _generate_insights(self, metrics: Dict) -> List[str]:
        """Generate human-readable insights from metrics"""
        insights = []

        # Trend insights
        if 'trend_direction' in metrics:
            direction = metrics['trend_direction']
            magnitude = abs(metrics.get('trend_magnitude_percent', 0))

            if direction == "improving":
                insights.append(f"Channel performance is improving - recent videos average {magnitude:.0f}% more views")
            else:
                insights.append(f"Channel performance is declining - recent videos average {magnitude:.0f}% fewer views")

        # Content type insights
        if 'shorts_vs_longform_summary' in metrics:
            summary = metrics['shorts_vs_longform_summary']
            shorts_avg = summary.get('shorts', {}).get('avg_views', 0)
            longform_avg = summary.get('longform', {}).get('avg_views', 0)

            if shorts_avg > longform_avg * 2:
                insights.append(f"Shorts significantly outperform long-form ({shorts_avg:,.0f} vs {longform_avg:,.0f} avg views)")
            elif longform_avg > shorts_avg:
                insights.append(f"Long-form videos outperform Shorts ({longform_avg:,.0f} vs {shorts_avg:,.0f} avg views)")

        # Efficiency insights
        if 'avg_subs_per_1k_views' in metrics:
            sub_rate = metrics['avg_subs_per_1k_views']
            if sub_rate > 2:
                insights.append(f"Strong subscriber conversion: {sub_rate:.1f} subs per 1K views")
            elif sub_rate < 0.5:
                insights.append(f"Low subscriber conversion: only {sub_rate:.1f} subs per 1K views - consider stronger CTAs")

        return insights

    def _build_recommendations(self, metrics: Dict, insights: List) -> List[Dict[str, str]]:
        """Build actionable recommendations"""
        recommendations = []

        # Based on underperformers
        if metrics.get('needs_thumbnail_refresh'):
            count = len(metrics['needs_thumbnail_refresh'])
            recommendations.append({
                "priority": "HIGH",
                "action": "Refresh thumbnails on high-impression videos",
                "details": f"{count} videos are getting impressions but low CTR. New thumbnails could revive them.",
            })

        # Based on trends
        if metrics.get('trend_direction') == "declining":
            recommendations.append({
                "priority": "HIGH",
                "action": "Analyze recent content changes",
                "details": "Recent videos are underperforming. Compare recent content to older top performers to identify what changed.",
            })

        # Based on content type performance
        if 'shorts_vs_longform_summary' in metrics:
            summary = metrics['shorts_vs_longform_summary']
            shorts_count = summary.get('shorts', {}).get('count', 0)
            longform_count = summary.get('longform', {}).get('count', 0)

            if shorts_count > longform_count * 3:
                recommendations.append({
                    "priority": "MEDIUM",
                    "action": "Increase long-form content ratio",
                    "details": "Heavy Shorts focus may limit monetization. Long-form builds deeper audience connection.",
                })

        return recommendations

    def _calculate_severity(self, metrics: Dict) -> str:
        """Calculate overall severity level"""
        if metrics.get('trend_direction') == "declining" and abs(metrics.get('trend_magnitude_percent', 0)) > 30:
            return "WARNING"

        if len(metrics.get('needs_thumbnail_refresh', [])) > 10:
            return "WATCH"

        return "OK"

    def _generate_digest(self, metrics: Dict, insights: List, recommendations: List) -> str:
        """Generate human-readable summary"""
        lines = [
            "=" * 60,
            "VIDEO PERFORMANCE ANALYSIS",
            "=" * 60,
            "",
        ]

        # Summary stats
        if 'shorts_vs_longform_summary' in metrics:
            summary = metrics['shorts_vs_longform_summary']
            lines.extend([
                "📊 CONTENT BREAKDOWN",
                f"  Shorts: {summary.get('shorts', {}).get('count', 0)} videos, "
                f"{summary.get('shorts', {}).get('total_views', 0):,} total views",
                f"  Long-form: {summary.get('longform', {}).get('count', 0)} videos, "
                f"{summary.get('longform', {}).get('total_views', 0):,} total views",
                "",
            ])

        # Trend
        if 'trend_direction' in metrics:
            emoji = "📈" if metrics['trend_direction'] == "improving" else "📉"
            lines.extend([
                f"{emoji} TREND: {metrics['trend_direction'].upper()}",
                f"  Recent avg: {metrics.get('recent_period_avg_views', 0):,.0f} views",
                f"  Change: {metrics.get('trend_magnitude_percent', 0):+.0f}%",
                "",
            ])

        # Top performers
        if metrics.get('top_10_by_views'):
            lines.append("🏆 TOP 5 BY VIEWS")
            for v in metrics['top_10_by_views'][:5]:
                lines.append(f"  {v.get('views', 0):,} - {v.get('title', 'Unknown')[:40]}")
            lines.append("")

        # Insights
        if insights:
            lines.append("💡 KEY INSIGHTS")
            for insight in insights:
                lines.append(f"  • {insight}")
            lines.append("")

        # Recommendations
        if recommendations:
            lines.append("📝 RECOMMENDATIONS")
            for rec in recommendations[:3]:
                lines.append(f"  [{rec['priority']}] {rec['action']}")
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)
