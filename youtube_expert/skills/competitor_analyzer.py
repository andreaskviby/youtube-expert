"""
Competitor Analyzer Skill - Competitive landscape analysis

Provides framework for analyzing competitor channels.
Note: Direct competitor data requires API access to their channels.
"""

from __future__ import annotations

from typing import Dict, Any, List, TYPE_CHECKING
import pandas as pd
import numpy as np

from .base import BaseSkill

if TYPE_CHECKING:
    from ..core import ChannelData


class CompetitorAnalyzerSkill(BaseSkill):
    """
    Competitive landscape analysis

    Analyzes your channel's positioning and provides
    framework for competitor benchmarking.
    """

    name = "competitor_analyzer"
    description = "Competitive landscape and benchmarking analysis"

    # Industry benchmarks for travel/lifestyle niche
    NICHE_BENCHMARKS = {
        "travel_lifestyle": {
            "avg_ctr": 4.5,
            "avg_retention": 40,
            "subs_per_1k_views": 0.8,
            "views_per_video": 15000,
            "watch_hours_per_video": 300,
        }
    }

    def analyze(self, data: ChannelData, competitors: List[Dict] = None, **kwargs) -> Dict[str, Any]:
        if data.videos_df is None:
            return {"error": "No video data available"}

        df = data.videos_df.copy()

        # Filter out total/summary rows
        if 'video_id' in df.columns:
            df = df[df['video_id'].notna() & (df['video_id'] != 'Totalt')]

        metrics = {}
        insights = []
        recommendations = []

        # === BENCHMARK COMPARISON ===
        benchmark_analysis = self._compare_to_benchmarks(df)
        metrics.update(benchmark_analysis['metrics'])
        insights.extend(benchmark_analysis['insights'])

        # === NICHE POSITIONING ===
        positioning = self._analyze_positioning(df)
        metrics.update(positioning['metrics'])
        insights.extend(positioning['insights'])

        # === CONTENT GAP ANALYSIS ===
        gaps = self._analyze_content_gaps(df)
        metrics.update(gaps['metrics'])

        # === COMPETITIVE ADVANTAGES ===
        advantages = self._identify_advantages(df, metrics)
        metrics.update(advantages['metrics'])
        insights.extend(advantages['insights'])

        # === BUILD RECOMMENDATIONS ===
        recommendations = self._build_recommendations(metrics)

        severity = "OK"
        digest = self._generate_digest(metrics, insights, recommendations, severity)

        return {
            "metrics": metrics,
            "insights": insights,
            "recommendations": recommendations,
            "severity": severity,
            "digest": digest,
        }

    def _compare_to_benchmarks(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compare channel metrics to industry benchmarks"""
        insights = []

        benchmarks = self.NICHE_BENCHMARKS["travel_lifestyle"]

        # Calculate your metrics
        your_metrics = {}

        if 'ctr_percent' in df.columns:
            your_ctr = df[df['ctr_percent'].notna()]['ctr_percent'].mean()
            your_metrics['ctr'] = round(your_ctr, 2)
            ctr_diff = your_ctr - benchmarks['avg_ctr']
            if ctr_diff > 1:
                insights.append(f"CTR ({your_ctr:.1f}%) is above niche average ({benchmarks['avg_ctr']}%)")
            elif ctr_diff < -1:
                insights.append(f"CTR ({your_ctr:.1f}%) is below niche average ({benchmarks['avg_ctr']}%)")

        if 'retention_estimate' in df.columns:
            your_retention = df['retention_estimate'].mean()
            your_metrics['retention'] = round(your_retention, 1)

        if 'views' in df.columns:
            your_avg_views = df['views'].mean()
            your_metrics['avg_views_per_video'] = round(your_avg_views, 0)
            views_diff = (your_avg_views - benchmarks['views_per_video']) / benchmarks['views_per_video'] * 100
            if views_diff > 50:
                insights.append(f"Your avg views ({your_avg_views:,.0f}) significantly exceed niche average")
            elif views_diff < -50:
                insights.append(f"Your avg views ({your_avg_views:,.0f}) are below niche average ({benchmarks['views_per_video']:,})")

        if 'subscribers_gained' in df.columns and 'views' in df.columns:
            total_subs = df['subscribers_gained'].sum()
            total_views = df['views'].sum()
            your_sub_rate = (total_subs / total_views * 1000) if total_views > 0 else 0
            your_metrics['subs_per_1k_views'] = round(your_sub_rate, 2)

        benchmark_comparison = {
            "your_metrics": your_metrics,
            "niche_benchmarks": benchmarks,
            "performance_vs_benchmark": {},
        }

        # Calculate performance percentages
        if 'ctr' in your_metrics:
            benchmark_comparison['performance_vs_benchmark']['ctr'] = round(
                (your_metrics['ctr'] / benchmarks['avg_ctr']) * 100, 0
            )

        if 'avg_views_per_video' in your_metrics:
            benchmark_comparison['performance_vs_benchmark']['views'] = round(
                (your_metrics['avg_views_per_video'] / benchmarks['views_per_video']) * 100, 0
            )

        metrics = {
            "benchmark_comparison": benchmark_comparison,
        }

        return {"metrics": metrics, "insights": insights}

    def _analyze_positioning(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze channel positioning in the niche"""
        insights = []

        # Content type distribution
        if 'content_type' in df.columns:
            type_dist = df['content_type'].value_counts(normalize=True) * 100
            positioning = {
                "content_mix": type_dist.to_dict(),
            }

            shorts_pct = type_dist.get('SHORT', 0)
            if shorts_pct > 70:
                positioning['strategy'] = "SHORTS_FOCUSED"
                insights.append("Channel is Shorts-focused - good for reach, challenging for monetization")
            elif shorts_pct < 30:
                positioning['strategy'] = "LONGFORM_FOCUSED"
                insights.append("Channel is long-form focused - good for monetization and deeper engagement")
            else:
                positioning['strategy'] = "HYBRID"
                insights.append("Hybrid content strategy - balanced approach")
        else:
            positioning = {"strategy": "UNKNOWN"}

        # Posting frequency tier
        if 'published_at' in df.columns:
            df_dated = df[df['published_at'].notna()]
            if len(df_dated) > 1:
                date_range = (df_dated['published_at'].max() - df_dated['published_at'].min()).days
                videos_per_week = len(df_dated) / (date_range / 7) if date_range > 0 else 0

                if videos_per_week >= 5:
                    positioning['frequency_tier'] = "HIGH_VOLUME"
                elif videos_per_week >= 2:
                    positioning['frequency_tier'] = "CONSISTENT"
                else:
                    positioning['frequency_tier'] = "LOW_VOLUME"

                positioning['videos_per_week'] = round(videos_per_week, 1)

        metrics = {
            "positioning": positioning,
        }

        return {"metrics": metrics, "insights": insights}

    def _analyze_content_gaps(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identify content gaps and opportunities"""

        # Analyze what's working vs what's underutilized
        if 'views' not in df.columns or 'content_type' not in df.columns:
            return {"metrics": {}}

        gaps = []

        # Check if long-form is underrepresented
        longform = df[df['content_type'] == 'LONGFORM']
        shorts = df[df['content_type'] == 'SHORT']

        if len(longform) > 0 and len(shorts) > 0:
            longform_avg = longform['views'].mean()
            shorts_avg = shorts['views'].mean()

            # If long-form performs well but is underproduced
            if longform_avg > shorts_avg * 0.5 and len(longform) < len(shorts) * 0.3:
                gaps.append({
                    "type": "LONGFORM_UNDERPRODUCED",
                    "description": "Long-form content performs well but is underrepresented",
                    "opportunity": "Increase long-form production - your audience engages with it",
                })

            # If Shorts dominate but long-form is neglected
            if len(shorts) > len(longform) * 5:
                gaps.append({
                    "type": "MONETIZATION_GAP",
                    "description": "Heavy Shorts focus limits revenue potential",
                    "opportunity": "Add 1-2 long-form videos per week for monetization",
                })

        metrics = {
            "content_gaps": gaps,
            "gap_count": len(gaps),
        }

        return {"metrics": metrics}

    def _identify_advantages(self, df: pd.DataFrame, current_metrics: Dict) -> Dict[str, Any]:
        """Identify competitive advantages"""
        insights = []

        advantages = []
        weaknesses = []

        benchmarks = self.NICHE_BENCHMARKS["travel_lifestyle"]

        # Check CTR advantage
        benchmark_comp = current_metrics.get('benchmark_comparison', {})
        perf = benchmark_comp.get('performance_vs_benchmark', {})

        if perf.get('ctr', 100) > 120:
            advantages.append("Strong thumbnail/title strategy (CTR above benchmark)")

        if perf.get('views', 100) > 150:
            advantages.append("High viewership per video (algorithm favoring your content)")

        # Check for viral hits
        if 'views' in df.columns:
            median_views = df['views'].median()
            max_views = df['views'].max()
            if max_views > median_views * 10:
                advantages.append("Proven viral potential (significant view spikes)")

        # Check subscriber conversion
        your_metrics = benchmark_comp.get('your_metrics', {})
        if your_metrics.get('subs_per_1k_views', 0) > benchmarks['subs_per_1k_views']:
            advantages.append("Strong subscriber conversion")
        elif your_metrics.get('subs_per_1k_views', 0) < benchmarks['subs_per_1k_views'] * 0.5:
            weaknesses.append("Below-average subscriber conversion")

        if perf.get('ctr', 100) < 80:
            weaknesses.append("CTR below benchmark - thumbnails/titles need optimization")

        if advantages:
            insights.append(f"Key advantages: {', '.join(advantages[:2])}")

        metrics = {
            "competitive_advantages": advantages,
            "competitive_weaknesses": weaknesses,
        }

        return {"metrics": metrics, "insights": insights}

    def _build_recommendations(self, metrics: Dict) -> List[Dict[str, str]]:
        """Build competitive recommendations"""
        recommendations = []

        weaknesses = metrics.get('competitive_weaknesses', [])
        gaps = metrics.get('content_gaps', [])

        for weakness in weaknesses:
            if 'CTR' in weakness:
                recommendations.append({
                    "priority": "HIGH",
                    "action": "Optimize thumbnails and titles",
                    "details": "Study top-performing competitors' thumbnails for inspiration.",
                })
            if 'subscriber' in weakness.lower():
                recommendations.append({
                    "priority": "MEDIUM",
                    "action": "Strengthen subscribe CTAs",
                    "details": "Add compelling reasons to subscribe at key moments.",
                })

        for gap in gaps:
            if gap.get('type') == 'LONGFORM_UNDERPRODUCED':
                recommendations.append({
                    "priority": "MEDIUM",
                    "action": "Increase long-form content",
                    "details": gap.get('opportunity', ''),
                })

        recommendations.append({
            "priority": "LOW",
            "action": "Monitor 3-5 competitor channels",
            "details": "Track their content strategy, posting frequency, and viral hits for inspiration.",
        })

        return recommendations

    def _generate_digest(self, metrics: Dict, insights: List,
                        recommendations: List, severity: str) -> str:
        """Generate human-readable summary"""
        lines = [
            "=" * 60,
            "COMPETITIVE ANALYSIS REPORT",
            "=" * 60,
            "",
        ]

        # Positioning
        positioning = metrics.get('positioning', {})
        if positioning:
            lines.extend([
                "📊 YOUR POSITIONING",
                f"  Strategy: {positioning.get('strategy', 'UNKNOWN')}",
                f"  Frequency: {positioning.get('frequency_tier', 'UNKNOWN')}",
                f"  Videos/week: {positioning.get('videos_per_week', 0):.1f}",
                "",
            ])

        # Benchmark comparison
        benchmark = metrics.get('benchmark_comparison', {})
        if benchmark.get('performance_vs_benchmark'):
            perf = benchmark['performance_vs_benchmark']
            lines.extend([
                "📈 VS NICHE BENCHMARKS",
            ])
            if 'ctr' in perf:
                lines.append(f"  CTR: {perf['ctr']:.0f}% of benchmark")
            if 'views' in perf:
                lines.append(f"  Views/video: {perf['views']:.0f}% of benchmark")
            lines.append("")

        # Advantages
        advantages = metrics.get('competitive_advantages', [])
        weaknesses = metrics.get('competitive_weaknesses', [])

        if advantages:
            lines.append("✅ COMPETITIVE ADVANTAGES")
            for adv in advantages:
                lines.append(f"  • {adv}")
            lines.append("")

        if weaknesses:
            lines.append("⚠️ AREAS TO IMPROVE")
            for weak in weaknesses:
                lines.append(f"  • {weak}")
            lines.append("")

        # Content gaps
        gaps = metrics.get('content_gaps', [])
        if gaps:
            lines.append("🎯 CONTENT OPPORTUNITIES")
            for gap in gaps:
                lines.append(f"  • {gap.get('description', '')}")
            lines.append("")

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
