"""
Growth Projector Skill - Trend forecasting and growth projections

Analyzes historical performance to project future growth.
"""

from __future__ import annotations

from typing import Dict, Any, List, TYPE_CHECKING
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from .base import BaseSkill

if TYPE_CHECKING:
    from ..core import ChannelData


class GrowthProjectorSkill(BaseSkill):
    """
    Growth trend analysis and forecasting

    Analyzes historical performance trends to project future
    subscriber growth, view counts, and watch time accumulation.
    """

    name = "growth_projector"
    description = "Growth trend forecasting and projections"

    def analyze(self, data: ChannelData, **kwargs) -> Dict[str, Any]:
        if data.videos_df is None:
            return {"error": "No video data available"}

        df = data.videos_df.copy()

        # Filter out total/summary rows
        if 'video_id' in df.columns:
            df = df[df['video_id'].notna() & (df['video_id'] != 'Totalt')]

        if 'published_at' not in df.columns:
            return {"error": "No date data available for projections"}

        df = df[df['published_at'].notna()].copy()

        if len(df) < 10:
            return {"error": "Insufficient data for projections (need 10+ videos)"}

        metrics = {}
        insights = []
        recommendations = []

        # === GROWTH TREND ANALYSIS ===
        trend_analysis = self._analyze_growth_trends(df)
        metrics.update(trend_analysis['metrics'])
        insights.extend(trend_analysis['insights'])

        # === PROJECTIONS ===
        projections = self._calculate_projections(df, trend_analysis['metrics'])
        metrics.update(projections['metrics'])
        insights.extend(projections['insights'])

        # === MILESTONE FORECASTS ===
        milestones = self._forecast_milestones(df, metrics)
        metrics.update(milestones['metrics'])
        insights.extend(milestones['insights'])

        # === VELOCITY ANALYSIS ===
        velocity = self._analyze_velocity(df)
        metrics.update(velocity['metrics'])

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

    def _analyze_growth_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze historical growth trends"""
        insights = []

        df_sorted = df.sort_values('published_at')

        # Calculate cumulative metrics over time
        df_sorted['cumulative_views'] = df_sorted['views'].cumsum()
        df_sorted['cumulative_hours'] = df_sorted['watch_hours'].cumsum() if 'watch_hours' in df_sorted.columns else 0
        df_sorted['cumulative_subs'] = df_sorted['subscribers_gained'].cumsum() if 'subscribers_gained' in df_sorted.columns else 0

        # Weekly aggregation
        df_sorted['week'] = df_sorted['published_at'].dt.isocalendar().week
        df_sorted['year'] = df_sorted['published_at'].dt.year
        df_sorted['year_week'] = df_sorted['year'].astype(str) + '-W' + df_sorted['week'].astype(str).str.zfill(2)

        weekly = df_sorted.groupby('year_week').agg({
            'views': 'sum',
            'watch_hours': 'sum' if 'watch_hours' in df_sorted.columns else 'count',
            'subscribers_gained': 'sum' if 'subscribers_gained' in df_sorted.columns else 'count',
            'video_id': 'count',
        }).reset_index()
        weekly.columns = ['week', 'views', 'hours', 'subs', 'uploads']

        if len(weekly) < 4:
            return {"metrics": {}, "insights": ["Insufficient weekly data for trend analysis"]}

        # Calculate trends (comparing first half to second half)
        midpoint = len(weekly) // 2
        first_half = weekly.iloc[:midpoint]
        second_half = weekly.iloc[midpoint:]

        views_trend = ((second_half['views'].mean() - first_half['views'].mean()) / first_half['views'].mean() * 100) if first_half['views'].mean() > 0 else 0
        hours_trend = ((second_half['hours'].mean() - first_half['hours'].mean()) / first_half['hours'].mean() * 100) if first_half['hours'].mean() > 0 else 0
        subs_trend = ((second_half['subs'].mean() - first_half['subs'].mean()) / first_half['subs'].mean() * 100) if first_half['subs'].mean() > 0 else 0

        # Determine trend direction
        if views_trend > 20:
            trend_direction = "STRONG_GROWTH"
            insights.append(f"Strong growth: Views up {views_trend:.0f}% vs earlier period")
        elif views_trend > 0:
            trend_direction = "GROWING"
            insights.append(f"Steady growth: Views up {views_trend:.0f}%")
        elif views_trend > -20:
            trend_direction = "STABLE"
            insights.append("Growth has plateaued - consider new content strategies")
        else:
            trend_direction = "DECLINING"
            insights.append(f"⚠️ Declining: Views down {abs(views_trend):.0f}%")

        # Calculate growth rates
        recent_weekly_views = second_half['views'].mean()
        recent_weekly_hours = second_half['hours'].mean()
        recent_weekly_subs = second_half['subs'].mean()

        metrics = {
            "trend_direction": trend_direction,
            "views_trend_percent": round(views_trend, 1),
            "hours_trend_percent": round(hours_trend, 1),
            "subs_trend_percent": round(subs_trend, 1),
            "recent_weekly_views": round(recent_weekly_views, 0),
            "recent_weekly_hours": round(recent_weekly_hours, 1),
            "recent_weekly_subs": round(recent_weekly_subs, 0),
            "weeks_analyzed": len(weekly),
        }

        return {"metrics": metrics, "insights": insights}

    def _calculate_projections(self, df: pd.DataFrame, trend_metrics: Dict) -> Dict[str, Any]:
        """Calculate future projections based on trends"""
        insights = []

        recent_weekly_views = trend_metrics.get('recent_weekly_views', 0)
        recent_weekly_hours = trend_metrics.get('recent_weekly_hours', 0)
        recent_weekly_subs = trend_metrics.get('recent_weekly_subs', 0)

        # Project forward assuming current rate continues
        # 30 days = ~4.3 weeks
        # 90 days = ~13 weeks
        # 365 days = ~52 weeks

        projections = {
            "30_days": {
                "views": round(recent_weekly_views * 4.3, 0),
                "hours": round(recent_weekly_hours * 4.3, 1),
                "subs": round(recent_weekly_subs * 4.3, 0),
            },
            "90_days": {
                "views": round(recent_weekly_views * 13, 0),
                "hours": round(recent_weekly_hours * 13, 1),
                "subs": round(recent_weekly_subs * 13, 0),
            },
            "365_days": {
                "views": round(recent_weekly_views * 52, 0),
                "hours": round(recent_weekly_hours * 52, 1),
                "subs": round(recent_weekly_subs * 52, 0),
            },
        }

        # With 10% growth scenario
        growth_factor_30 = 1.1 ** (30/365)
        growth_factor_90 = 1.1 ** (90/365)
        growth_factor_365 = 1.1

        projections_optimistic = {
            "30_days": {
                "views": round(projections["30_days"]["views"] * growth_factor_30, 0),
                "hours": round(projections["30_days"]["hours"] * growth_factor_30, 1),
            },
            "90_days": {
                "views": round(projections["90_days"]["views"] * growth_factor_90, 0),
                "hours": round(projections["90_days"]["hours"] * growth_factor_90, 1),
            },
            "365_days": {
                "views": round(projections["365_days"]["views"] * growth_factor_365, 0),
                "hours": round(projections["365_days"]["hours"] * growth_factor_365, 1),
            },
        }

        projected_annual_hours = projections["365_days"]["hours"]
        if projected_annual_hours < 4000:
            insights.append(f"At current rate, you'll accumulate {projected_annual_hours:,.0f} watch hours in a year")
        else:
            insights.append(f"Projected annual watch hours ({projected_annual_hours:,.0f}) exceeds 4000h goal!")

        metrics = {
            "projections_baseline": projections,
            "projections_10pct_growth": projections_optimistic,
        }

        return {"metrics": metrics, "insights": insights}

    def _forecast_milestones(self, df: pd.DataFrame, current_metrics: Dict) -> Dict[str, Any]:
        """Forecast when key milestones will be reached"""
        insights = []

        recent_weekly_hours = current_metrics.get('recent_weekly_hours', 0)
        recent_weekly_subs = current_metrics.get('recent_weekly_subs', 0)
        recent_weekly_views = current_metrics.get('recent_weekly_views', 0)

        # Current totals
        total_hours = df['watch_hours'].sum() if 'watch_hours' in df.columns else 0
        total_subs = df['subscribers_gained'].sum() if 'subscribers_gained' in df.columns else 0
        total_views = df['views'].sum() if 'views' in df.columns else 0

        milestones = {}

        # 4000 watch hours milestone
        if total_hours < 4000 and recent_weekly_hours > 0:
            hours_needed = 4000 - total_hours
            weeks_to_4000h = hours_needed / recent_weekly_hours
            days_to_4000h = weeks_to_4000h * 7

            if days_to_4000h < 365:
                milestone_date = datetime.now() + timedelta(days=days_to_4000h)
                milestones["4000_watch_hours"] = {
                    "days_away": round(days_to_4000h, 0),
                    "estimated_date": milestone_date.strftime("%Y-%m-%d"),
                    "hours_remaining": round(hours_needed, 0),
                }
                insights.append(f"4000h milestone estimated in {days_to_4000h:.0f} days ({milestone_date.strftime('%B %Y')})")
            else:
                milestones["4000_watch_hours"] = {
                    "days_away": round(days_to_4000h, 0),
                    "estimated_date": "More than 1 year away",
                    "hours_remaining": round(hours_needed, 0),
                }
        elif total_hours >= 4000:
            milestones["4000_watch_hours"] = {"status": "ACHIEVED"}

        # View milestones (1M, 5M, 10M)
        view_milestones = [1_000_000, 5_000_000, 10_000_000]
        for milestone in view_milestones:
            if total_views < milestone and recent_weekly_views > 0:
                views_needed = milestone - total_views
                weeks_to_milestone = views_needed / recent_weekly_views
                days_to_milestone = weeks_to_milestone * 7

                if days_to_milestone < 730:  # Within 2 years
                    milestones[f"{milestone//1_000_000}M_views"] = {
                        "days_away": round(days_to_milestone, 0),
                        "views_remaining": int(views_needed),
                    }
            elif total_views >= milestone:
                milestones[f"{milestone//1_000_000}M_views"] = {"status": "ACHIEVED"}

        metrics = {
            "milestones": milestones,
            "current_totals": {
                "views": int(total_views),
                "watch_hours": round(total_hours, 0),
                "subscribers_gained": int(total_subs),
            },
        }

        return {"metrics": metrics, "insights": insights}

    def _analyze_velocity(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze the velocity/acceleration of growth"""

        df_sorted = df.sort_values('published_at')

        # Calculate rolling averages to detect acceleration
        df_sorted['rolling_views'] = df_sorted['views'].rolling(5, min_periods=1).mean()

        if len(df_sorted) >= 10:
            # Compare recent 5 to previous 5
            recent = df_sorted.tail(5)['views'].mean()
            previous = df_sorted.iloc[-10:-5]['views'].mean()

            if previous > 0:
                acceleration = ((recent - previous) / previous) * 100
            else:
                acceleration = 0

            if acceleration > 50:
                velocity_status = "ACCELERATING"
            elif acceleration > 0:
                velocity_status = "STEADY"
            elif acceleration > -20:
                velocity_status = "SLOWING"
            else:
                velocity_status = "DECELERATING"
        else:
            acceleration = 0
            velocity_status = "INSUFFICIENT_DATA"

        metrics = {
            "velocity_status": velocity_status,
            "recent_vs_previous_pct": round(acceleration, 1),
        }

        return {"metrics": metrics}

    def _build_recommendations(self, metrics: Dict) -> List[Dict[str, str]]:
        """Build growth recommendations"""
        recommendations = []

        trend = metrics.get('trend_direction', 'UNKNOWN')
        velocity = metrics.get('velocity_status', 'UNKNOWN')

        if trend in ["DECLINING", "STABLE"]:
            recommendations.append({
                "priority": "HIGH",
                "action": "Experiment with new content formats",
                "details": "Growth has stalled. Try new video styles, topics, or formats to reignite the algorithm.",
            })

        if velocity == "DECELERATING":
            recommendations.append({
                "priority": "HIGH",
                "action": "Analyze recent underperformers",
                "details": "Recent videos are performing worse. Review what changed vs your viral hits.",
            })

        if velocity == "ACCELERATING":
            recommendations.append({
                "priority": "MEDIUM",
                "action": "Double down on what's working",
                "details": "Growth is accelerating! Identify common elements in recent hits and replicate.",
            })

        milestones = metrics.get('milestones', {})
        watch_hour_milestone = milestones.get('4000_watch_hours', {})
        if watch_hour_milestone.get('days_away', 9999) > 180:
            recommendations.append({
                "priority": "HIGH",
                "action": "Increase long-form content output",
                "details": "At current pace, 4000h is far away. Increase upload frequency or video length.",
            })

        return recommendations

    def _calculate_severity(self, metrics: Dict) -> str:
        """Calculate severity"""
        trend = metrics.get('trend_direction', 'UNKNOWN')
        velocity = metrics.get('velocity_status', 'UNKNOWN')

        if trend == "DECLINING" or velocity == "DECELERATING":
            return "WARNING"
        elif trend == "STABLE":
            return "WATCH"
        return "OK"

    def _generate_digest(self, metrics: Dict, insights: List,
                        recommendations: List, severity: str) -> str:
        """Generate human-readable summary"""
        lines = [
            "=" * 60,
            "GROWTH PROJECTION REPORT",
            "=" * 60,
            "",
            f"Status: {severity}",
            f"Trend: {metrics.get('trend_direction', 'UNKNOWN')}",
            f"Velocity: {metrics.get('velocity_status', 'UNKNOWN')}",
            "",
            "📈 CURRENT WEEKLY RATE",
            f"  Views: {metrics.get('recent_weekly_views', 0):,.0f}",
            f"  Watch hours: {metrics.get('recent_weekly_hours', 0):.1f}",
            f"  Subscribers: {metrics.get('recent_weekly_subs', 0):,.0f}",
            "",
        ]

        # Projections
        baseline = metrics.get('projections_baseline', {})
        if baseline.get('90_days'):
            lines.extend([
                "📊 90-DAY PROJECTIONS (Current Rate)",
                f"  Views: {baseline['90_days'].get('views', 0):,}",
                f"  Watch hours: {baseline['90_days'].get('hours', 0):,.0f}",
                f"  Subscribers: +{baseline['90_days'].get('subs', 0):,}",
                "",
            ])

        if baseline.get('365_days'):
            lines.extend([
                "📊 12-MONTH PROJECTIONS",
                f"  Views: {baseline['365_days'].get('views', 0):,}",
                f"  Watch hours: {baseline['365_days'].get('hours', 0):,.0f}",
                f"  Subscribers: +{baseline['365_days'].get('subs', 0):,}",
                "",
            ])

        # Milestones
        milestones = metrics.get('milestones', {})
        if milestones:
            lines.append("🎯 MILESTONE FORECASTS")
            for name, data in milestones.items():
                if data.get('status') == 'ACHIEVED':
                    lines.append(f"  {name}: ✓ ACHIEVED")
                elif data.get('days_away'):
                    lines.append(f"  {name}: {data['days_away']:.0f} days")
            lines.append("")

        if insights:
            lines.append("💡 INSIGHTS")
            for insight in insights:
                lines.append(f"  • {insight}")
            lines.append("")

        if recommendations:
            lines.append("📝 RECOMMENDATIONS")
            for rec in recommendations[:3]:
                lines.append(f"  [{rec['priority']}] {rec['action']}")
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)
