"""
Revenue Optimizer Skill - Monetization strategy optimization

Analyzes revenue potential and provides monetization recommendations.
"""

from __future__ import annotations

from typing import Dict, Any, List, TYPE_CHECKING
import pandas as pd
import numpy as np

from .base import BaseSkill

if TYPE_CHECKING:
    from ..core import ChannelData


class RevenueOptimizerSkill(BaseSkill):
    """
    Revenue and monetization optimization

    Analyzes watch time, CPM potential, and provides strategies
    to maximize YouTube Partner Program revenue.
    """

    name = "revenue_optimizer"
    description = "Monetization and revenue strategy analysis"

    # YPP thresholds
    YPP_WATCH_HOURS = 4000
    YPP_SUBSCRIBERS = 1000
    YPP_SHORTS_VIEWS = 10_000_000  # For Shorts-based monetization

    # Estimated CPM ranges by content type (USD)
    CPM_ESTIMATES = {
        "travel": {"low": 2.0, "mid": 5.0, "high": 10.0},
        "lifestyle": {"low": 1.5, "mid": 4.0, "high": 8.0},
        "default": {"low": 1.0, "mid": 3.0, "high": 6.0},
    }

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

        # === YPP ELIGIBILITY STATUS ===
        ypp_analysis = self._analyze_ypp_status(df, data)
        metrics.update(ypp_analysis['metrics'])
        insights.extend(ypp_analysis['insights'])

        # === REVENUE POTENTIAL ===
        revenue_analysis = self._analyze_revenue_potential(df)
        metrics.update(revenue_analysis['metrics'])
        insights.extend(revenue_analysis['insights'])

        # === WATCH TIME EFFICIENCY ===
        efficiency_analysis = self._analyze_watch_time_efficiency(df)
        metrics.update(efficiency_analysis['metrics'])

        # === MONETIZATION MIX ===
        mix_analysis = self._analyze_monetization_mix(df)
        metrics.update(mix_analysis['metrics'])
        insights.extend(mix_analysis['insights'])

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

    def _analyze_ypp_status(self, df: pd.DataFrame, data: ChannelData) -> Dict[str, Any]:
        """Analyze YouTube Partner Program eligibility"""
        insights = []

        # Calculate long-form watch hours
        if 'is_short' in df.columns and 'watch_hours' in df.columns:
            longform = df[df['is_short'] == False]
            longform_hours = longform['watch_hours'].sum()
        else:
            longform_hours = df['watch_hours'].sum() if 'watch_hours' in df.columns else 0

        watch_hour_progress = (longform_hours / self.YPP_WATCH_HOURS) * 100
        hours_remaining = max(0, self.YPP_WATCH_HOURS - longform_hours)

        # Shorts views (for alternative monetization path)
        if 'is_short' in df.columns:
            shorts = df[df['is_short'] == True]
            shorts_views = shorts['views'].sum() if 'views' in shorts.columns else 0
        else:
            shorts_views = 0

        shorts_view_progress = (shorts_views / self.YPP_SHORTS_VIEWS) * 100

        # Determine eligibility status
        if longform_hours >= self.YPP_WATCH_HOURS:
            eligibility_status = "ELIGIBLE"
            insights.append("Watch hour requirement met for YPP!")
        elif watch_hour_progress >= 75:
            eligibility_status = "CLOSE"
            insights.append(f"Only {hours_remaining:.0f} hours needed for YPP eligibility")
        elif shorts_view_progress >= 100:
            eligibility_status = "SHORTS_ELIGIBLE"
            insights.append("Eligible for Shorts monetization (10M views)")
        else:
            eligibility_status = "NOT_ELIGIBLE"
            insights.append(f"Need {hours_remaining:.0f} more long-form watch hours for YPP")

        metrics = {
            "longform_watch_hours": round(longform_hours, 1),
            "watch_hour_goal": self.YPP_WATCH_HOURS,
            "watch_hour_progress_pct": round(watch_hour_progress, 1),
            "hours_remaining": round(hours_remaining, 1),
            "shorts_total_views": int(shorts_views),
            "shorts_view_progress_pct": round(shorts_view_progress, 1),
            "eligibility_status": eligibility_status,
        }

        return {"metrics": metrics, "insights": insights}

    def _analyze_revenue_potential(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Estimate potential revenue based on views and CPM"""
        insights = []

        if 'views' not in df.columns:
            return {"metrics": {}, "insights": []}

        # Use travel/lifestyle CPM estimates (based on channel content)
        cpm = self.CPM_ESTIMATES["travel"]

        # Only long-form views are monetizable at full rate
        if 'is_short' in df.columns:
            longform = df[df['is_short'] == False]
            monetizable_views = longform['views'].sum()
            shorts_views = df[df['is_short'] == True]['views'].sum()
        else:
            monetizable_views = df['views'].sum()
            shorts_views = 0

        # Revenue estimates (per 1000 views)
        revenue_low = (monetizable_views / 1000) * cpm['low']
        revenue_mid = (monetizable_views / 1000) * cpm['mid']
        revenue_high = (monetizable_views / 1000) * cpm['high']

        # Shorts have much lower RPM (~$0.05-0.10 per 1K views in Shorts fund)
        shorts_revenue_estimate = (shorts_views / 1000) * 0.05

        # Calculate monthly potential (rough estimate)
        if 'published_at' in df.columns:
            df_dated = df[df['published_at'].notna()]
            if len(df_dated) > 0:
                date_range = (df_dated['published_at'].max() - df_dated['published_at'].min()).days
                months = max(1, date_range / 30)
                monthly_revenue_mid = revenue_mid / months
            else:
                monthly_revenue_mid = 0
        else:
            monthly_revenue_mid = 0

        if revenue_mid > 1000:
            insights.append(f"Estimated lifetime revenue potential: ${revenue_mid:,.0f}")

        metrics = {
            "monetizable_views": int(monetizable_views),
            "shorts_views": int(shorts_views),
            "estimated_revenue_low": round(revenue_low, 2),
            "estimated_revenue_mid": round(revenue_mid, 2),
            "estimated_revenue_high": round(revenue_high, 2),
            "shorts_revenue_estimate": round(shorts_revenue_estimate, 2),
            "monthly_revenue_estimate": round(monthly_revenue_mid, 2),
            "cpm_range": cpm,
        }

        return {"metrics": metrics, "insights": insights}

    def _analyze_watch_time_efficiency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze how efficiently videos generate monetizable watch time"""

        if 'watch_hours' not in df.columns or 'views' not in df.columns:
            return {"metrics": {}}

        # Watch hours per 1K views
        total_views = df['views'].sum()
        total_hours = df['watch_hours'].sum()

        hours_per_1k_views = (total_hours / total_views) * 1000 if total_views > 0 else 0

        # By content type
        if 'is_short' in df.columns:
            longform = df[df['is_short'] == False]
            shorts = df[df['is_short'] == True]

            lf_hours_per_1k = (longform['watch_hours'].sum() / longform['views'].sum()) * 1000 if longform['views'].sum() > 0 else 0
            shorts_hours_per_1k = (shorts['watch_hours'].sum() / shorts['views'].sum()) * 1000 if shorts['views'].sum() > 0 else 0
        else:
            lf_hours_per_1k = hours_per_1k_views
            shorts_hours_per_1k = 0

        # RPM efficiency (revenue per 1K views based on watch time)
        rpm_efficiency = lf_hours_per_1k * 3  # Rough estimate: $3 per watch hour

        metrics = {
            "hours_per_1k_views": round(hours_per_1k_views, 2),
            "longform_hours_per_1k": round(lf_hours_per_1k, 2),
            "shorts_hours_per_1k": round(shorts_hours_per_1k, 4),
            "estimated_rpm": round(rpm_efficiency, 2),
        }

        return {"metrics": metrics}

    def _analyze_monetization_mix(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze the mix of revenue sources"""
        insights = []

        if 'is_short' not in df.columns:
            return {"metrics": {}, "insights": []}

        shorts = df[df['is_short'] == True]
        longform = df[df['is_short'] == False]

        shorts_count = len(shorts)
        longform_count = len(longform)
        total = shorts_count + longform_count

        shorts_ratio = shorts_count / total if total > 0 else 0
        longform_ratio = longform_count / total if total > 0 else 0

        # Revenue contribution estimate
        if 'views' in df.columns:
            shorts_views = shorts['views'].sum()
            longform_views = longform['views'].sum()

            # Long-form contributes ~50x more revenue per view
            shorts_revenue_weight = shorts_views * 0.05  # $0.05 per 1K
            longform_revenue_weight = longform_views * 3.0  # $3 per 1K

            total_weight = shorts_revenue_weight + longform_revenue_weight
            if total_weight > 0:
                longform_revenue_share = (longform_revenue_weight / total_weight) * 100
            else:
                longform_revenue_share = 0
        else:
            longform_revenue_share = longform_ratio * 100

        if shorts_ratio > 0.7:
            insights.append("Heavy Shorts focus limits ad revenue. Long-form has 50x higher RPM.")

        if longform_revenue_share > 80:
            insights.append("Revenue is well-diversified toward long-form content.")

        metrics = {
            "shorts_content_ratio": round(shorts_ratio * 100, 1),
            "longform_content_ratio": round(longform_ratio * 100, 1),
            "longform_revenue_share_estimate": round(longform_revenue_share, 1),
        }

        return {"metrics": metrics, "insights": insights}

    def _build_recommendations(self, metrics: Dict, insights: List) -> List[Dict[str, str]]:
        """Build revenue optimization recommendations"""
        recommendations = []

        eligibility = metrics.get('eligibility_status', 'NOT_ELIGIBLE')

        if eligibility == "NOT_ELIGIBLE":
            hours_remaining = metrics.get('hours_remaining', 4000)
            recommendations.append({
                "priority": "HIGH",
                "action": f"Focus on accumulating {hours_remaining:.0f} more long-form watch hours",
                "details": "Prioritize 10-20 minute videos with strong retention. Shorts don't count toward 4000h.",
            })

        if eligibility == "CLOSE":
            recommendations.append({
                "priority": "HIGH",
                "action": "Sprint to YPP eligibility",
                "details": "You're close! Focus all efforts on long-form content for the next few weeks.",
            })

        # Revenue optimization
        shorts_ratio = metrics.get('shorts_content_ratio', 0)
        if shorts_ratio > 60:
            recommendations.append({
                "priority": "HIGH",
                "action": "Rebalance toward long-form content",
                "details": "Long-form generates 50x more revenue per view. Aim for 50/50 content mix.",
            })

        # Watch time efficiency
        hours_per_1k = metrics.get('longform_hours_per_1k', 0)
        if hours_per_1k < 1:
            recommendations.append({
                "priority": "MEDIUM",
                "action": "Improve video retention",
                "details": "Low watch time per view indicates retention issues. Focus on hooks and pacing.",
            })

        # Diversification
        recommendations.append({
            "priority": "LOW",
            "action": "Explore additional revenue streams",
            "details": "Consider: Channel memberships, Super Thanks, merchandise, sponsorships, affiliate marketing.",
        })

        return recommendations

    def _calculate_severity(self, metrics: Dict) -> str:
        """Calculate severity"""
        eligibility = metrics.get('eligibility_status', 'NOT_ELIGIBLE')

        if eligibility == "NOT_ELIGIBLE" and metrics.get('watch_hour_progress_pct', 0) < 25:
            return "WARNING"
        elif eligibility == "NOT_ELIGIBLE":
            return "WATCH"
        return "OK"

    def _generate_digest(self, metrics: Dict, insights: List,
                        recommendations: List, severity: str) -> str:
        """Generate human-readable summary"""
        lines = [
            "=" * 60,
            "REVENUE OPTIMIZATION REPORT",
            "=" * 60,
            "",
            f"Status: {severity}",
            "",
            "🎯 YPP ELIGIBILITY",
            f"  Status: {metrics.get('eligibility_status', 'UNKNOWN')}",
            f"  Long-form hours: {metrics.get('longform_watch_hours', 0):,.0f} / {metrics.get('watch_hour_goal', 4000)}",
            f"  Progress: {metrics.get('watch_hour_progress_pct', 0):.0f}%",
            f"  Hours remaining: {metrics.get('hours_remaining', 0):,.0f}",
            "",
            "💰 ESTIMATED REVENUE POTENTIAL",
            f"  Monetizable views: {metrics.get('monetizable_views', 0):,}",
            f"  Revenue range: ${metrics.get('estimated_revenue_low', 0):,.0f} - ${metrics.get('estimated_revenue_high', 0):,.0f}",
            f"  Monthly estimate: ${metrics.get('monthly_revenue_estimate', 0):,.0f}",
            "",
            "📊 CONTENT MIX",
            f"  Shorts: {metrics.get('shorts_content_ratio', 0):.0f}%",
            f"  Long-form: {metrics.get('longform_content_ratio', 0):.0f}%",
            f"  Long-form revenue share: {metrics.get('longform_revenue_share_estimate', 0):.0f}%",
            "",
        ]

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
