"""
Shorts Strategy Skill - Optimize Shorts vs Long-form balance

Analyzes the relationship between Shorts and long-form content,
identifies the optimal mix for your channel, and provides
strategies to convert Shorts viewers to long-form watchers.
"""

from __future__ import annotations

from typing import Dict, Any, List, TYPE_CHECKING
import pandas as pd
import numpy as np

from .base import BaseSkill

if TYPE_CHECKING:
    from ..core import ChannelData


class ShortsStrategySkill(BaseSkill):
    """
    Shorts vs Long-form optimization strategy

    Analyzes how Shorts and long-form content perform on your
    channel, identifies audience crossover opportunities, and
    provides strategies to maximize both viral reach and watch time.
    """

    name = "shorts_strategy"
    description = "Shorts vs long-form content optimization"

    # Benchmarks based on successful hybrid channels
    IDEAL_SHORTS_RATIO = 0.4  # 40% Shorts, 60% long-form
    SHORTS_TO_LONGFORM_CONVERSION = 0.05  # 5% is good crossover

    def analyze(self, data: ChannelData, **kwargs) -> Dict[str, Any]:
        if data.videos_df is None:
            return {"error": "No video data available"}

        df = data.videos_df.copy()

        # Filter out total/summary rows
        if 'video_id' in df.columns:
            df = df[df['video_id'].notna() & (df['video_id'] != 'Totalt')]

        if 'is_short' not in df.columns:
            return {"error": "Cannot determine content types"}

        shorts = df[df['is_short'] == True]
        longform = df[df['is_short'] == False]

        metrics = {}
        insights = []
        recommendations = []

        # === CONTENT MIX ANALYSIS ===
        mix_analysis = self._analyze_content_mix(df, shorts, longform)
        metrics.update(mix_analysis['metrics'])
        insights.extend(mix_analysis['insights'])

        # === VIRAL POTENTIAL COMPARISON ===
        viral_analysis = self._analyze_viral_potential(shorts, longform)
        metrics.update(viral_analysis['metrics'])
        insights.extend(viral_analysis['insights'])

        # === SUBSCRIBER CONTRIBUTION ===
        sub_analysis = self._analyze_subscriber_contribution(shorts, longform)
        metrics.update(sub_analysis['metrics'])
        insights.extend(sub_analysis['insights'])

        # === WATCH TIME EFFICIENCY ===
        efficiency_analysis = self._analyze_efficiency(shorts, longform)
        metrics.update(efficiency_analysis['metrics'])
        insights.extend(efficiency_analysis['insights'])

        # === TOPIC CROSSOVER ANALYSIS ===
        crossover_analysis = self._analyze_topic_crossover(df)
        metrics.update(crossover_analysis['metrics'])

        # === BUILD STRATEGY RECOMMENDATIONS ===
        recommendations = self._build_strategy(metrics, insights)

        severity = self._calculate_severity(metrics)
        digest = self._generate_digest(metrics, insights, recommendations, severity)

        return {
            "metrics": metrics,
            "insights": insights,
            "recommendations": recommendations,
            "severity": severity,
            "digest": digest,
        }

    def _analyze_content_mix(self, df: pd.DataFrame, shorts: pd.DataFrame,
                             longform: pd.DataFrame) -> Dict[str, Any]:
        """Analyze the mix of Shorts vs long-form content"""
        insights = []

        total_count = len(df)
        shorts_count = len(shorts)
        longform_count = len(longform)

        shorts_ratio = shorts_count / total_count if total_count > 0 else 0
        longform_ratio = longform_count / total_count if total_count > 0 else 0

        # Classify strategy type
        if shorts_ratio > 0.8:
            strategy_type = "SHORTS_DOMINANT"
            insights.append("Channel is Shorts-dominant (>80%). Great for reach, but limits monetization potential.")
        elif longform_ratio > 0.8:
            strategy_type = "LONGFORM_DOMINANT"
            insights.append("Channel is long-form dominant (>80%). Good for watch time, but missing viral Shorts opportunity.")
        elif 0.3 <= shorts_ratio <= 0.5:
            strategy_type = "BALANCED"
            insights.append("Channel has balanced content mix. This is ideal for hybrid growth.")
        else:
            strategy_type = "UNBALANCED"
            insights.append(f"Content mix ({shorts_ratio:.0%} Shorts) could be optimized.")

        # Calculate upload frequency
        if 'published_at' in df.columns:
            df_dated = df[df['published_at'].notna()].sort_values('published_at')
            if len(df_dated) > 1:
                date_range = (df_dated['published_at'].max() - df_dated['published_at'].min()).days
                if date_range > 0:
                    shorts_per_week = (len(shorts) / date_range) * 7
                    longform_per_week = (len(longform) / date_range) * 7
                else:
                    shorts_per_week = longform_per_week = 0
            else:
                shorts_per_week = longform_per_week = 0
        else:
            shorts_per_week = longform_per_week = 0

        metrics = {
            "shorts_count": shorts_count,
            "longform_count": longform_count,
            "shorts_ratio": round(shorts_ratio * 100, 1),
            "longform_ratio": round(longform_ratio * 100, 1),
            "strategy_type": strategy_type,
            "shorts_per_week": round(shorts_per_week, 1),
            "longform_per_week": round(longform_per_week, 1),
            "ideal_shorts_ratio": self.IDEAL_SHORTS_RATIO * 100,
        }

        return {"metrics": metrics, "insights": insights}

    def _analyze_viral_potential(self, shorts: pd.DataFrame,
                                  longform: pd.DataFrame) -> Dict[str, Any]:
        """Compare viral potential between content types"""
        insights = []

        if 'views' not in shorts.columns:
            return {"metrics": {}, "insights": []}

        # Calculate view distributions
        shorts_views = shorts['views'].tolist() if len(shorts) > 0 else []
        longform_views = longform['views'].tolist() if len(longform) > 0 else []

        shorts_max = max(shorts_views) if shorts_views else 0
        longform_max = max(longform_views) if longform_views else 0

        shorts_median = np.median(shorts_views) if shorts_views else 0
        longform_median = np.median(longform_views) if longform_views else 0

        shorts_mean = np.mean(shorts_views) if shorts_views else 0
        longform_mean = np.mean(longform_views) if longform_views else 0

        # Virality coefficient (max / median - high means viral spikes)
        shorts_virality = shorts_max / shorts_median if shorts_median > 0 else 0
        longform_virality = longform_max / longform_median if longform_median > 0 else 0

        # Count "hits" (videos above 90th percentile)
        if shorts_views:
            shorts_90th = np.percentile(shorts_views, 90)
            shorts_hits = sum(1 for v in shorts_views if v >= shorts_90th)
        else:
            shorts_90th = shorts_hits = 0

        if longform_views:
            longform_90th = np.percentile(longform_views, 90)
            longform_hits = sum(1 for v in longform_views if v >= longform_90th)
        else:
            longform_90th = longform_hits = 0

        if shorts_max > longform_max * 3:
            insights.append(f"Shorts have much higher viral ceiling ({shorts_max:,} vs {longform_max:,} peak views)")
        elif longform_max > shorts_max:
            insights.append(f"Long-form content reaches higher peaks than Shorts ({longform_max:,} vs {shorts_max:,})")

        if shorts_virality > 10:
            insights.append("Shorts show strong viral spikes - algorithm is favoring some content")

        metrics = {
            "shorts_max_views": int(shorts_max),
            "longform_max_views": int(longform_max),
            "shorts_median_views": int(shorts_median),
            "longform_median_views": int(longform_median),
            "shorts_mean_views": round(shorts_mean, 0),
            "longform_mean_views": round(longform_mean, 0),
            "shorts_virality_coefficient": round(shorts_virality, 1),
            "longform_virality_coefficient": round(longform_virality, 1),
            "shorts_hits_count": shorts_hits,
            "longform_hits_count": longform_hits,
        }

        return {"metrics": metrics, "insights": insights}

    def _analyze_subscriber_contribution(self, shorts: pd.DataFrame,
                                          longform: pd.DataFrame) -> Dict[str, Any]:
        """Analyze subscriber contribution by content type"""
        insights = []

        if 'subscribers_gained' not in shorts.columns:
            return {"metrics": {}, "insights": []}

        shorts_subs = shorts['subscribers_gained'].sum() if len(shorts) > 0 else 0
        longform_subs = longform['subscribers_gained'].sum() if len(longform) > 0 else 0
        total_subs = shorts_subs + longform_subs or 1

        shorts_subs_ratio = shorts_subs / total_subs
        longform_subs_ratio = longform_subs / total_subs

        # Subs per video
        shorts_subs_per_video = shorts_subs / len(shorts) if len(shorts) > 0 else 0
        longform_subs_per_video = longform_subs / len(longform) if len(longform) > 0 else 0

        # Subs per 1K views
        shorts_views = shorts['views'].sum() if 'views' in shorts.columns and len(shorts) > 0 else 1
        longform_views = longform['views'].sum() if 'views' in longform.columns and len(longform) > 0 else 1

        shorts_subs_per_1k = (shorts_subs / shorts_views) * 1000 if shorts_views > 0 else 0
        longform_subs_per_1k = (longform_subs / longform_views) * 1000 if longform_views > 0 else 0

        if shorts_subs_ratio > 0.7:
            insights.append(f"⚠️ {shorts_subs_ratio:.0%} of subscribers came from Shorts. These viewers often don't watch long-form.")
        elif longform_subs_ratio > 0.7:
            insights.append(f"Strong long-form subscriber base ({longform_subs_ratio:.0%}). These are more engaged viewers.")

        if shorts_subs_per_1k > longform_subs_per_1k * 2:
            insights.append(f"Shorts convert viewers to subs more efficiently ({shorts_subs_per_1k:.1f} vs {longform_subs_per_1k:.1f} per 1K views)")

        metrics = {
            "shorts_subscribers_gained": int(shorts_subs),
            "longform_subscribers_gained": int(longform_subs),
            "shorts_sub_ratio": round(shorts_subs_ratio * 100, 1),
            "longform_sub_ratio": round(longform_subs_ratio * 100, 1),
            "shorts_subs_per_video": round(shorts_subs_per_video, 1),
            "longform_subs_per_video": round(longform_subs_per_video, 1),
            "shorts_subs_per_1k_views": round(shorts_subs_per_1k, 2),
            "longform_subs_per_1k_views": round(longform_subs_per_1k, 2),
        }

        return {"metrics": metrics, "insights": insights}

    def _analyze_efficiency(self, shorts: pd.DataFrame,
                            longform: pd.DataFrame) -> Dict[str, Any]:
        """Analyze watch time efficiency by content type"""
        insights = []

        if 'watch_hours' not in shorts.columns:
            return {"metrics": {}, "insights": []}

        shorts_hours = shorts['watch_hours'].sum() if len(shorts) > 0 else 0
        longform_hours = longform['watch_hours'].sum() if len(longform) > 0 else 0
        total_hours = shorts_hours + longform_hours or 1

        # Hours per video
        shorts_hours_per_video = shorts_hours / len(shorts) if len(shorts) > 0 else 0
        longform_hours_per_video = longform_hours / len(longform) if len(longform) > 0 else 0

        # Content creation efficiency (watch hours generated per content minute created)
        if 'duration_seconds' in shorts.columns:
            shorts_content_minutes = shorts['duration_seconds'].sum() / 60
            longform_content_minutes = longform['duration_seconds'].sum() / 60

            shorts_efficiency = (shorts_hours * 60) / shorts_content_minutes if shorts_content_minutes > 0 else 0
            longform_efficiency = (longform_hours * 60) / longform_content_minutes if longform_content_minutes > 0 else 0
        else:
            shorts_efficiency = longform_efficiency = 0

        if longform_hours > shorts_hours:
            insights.append(f"Long-form drives {longform_hours / total_hours:.0%} of total watch time - good for monetization")
        else:
            insights.append(f"Shorts drive {shorts_hours / total_hours:.0%} of watch time - these hours don't count toward 4000h goal")

        metrics = {
            "shorts_watch_hours": round(shorts_hours, 1),
            "longform_watch_hours": round(longform_hours, 1),
            "shorts_hours_ratio": round((shorts_hours / total_hours) * 100, 1),
            "longform_hours_ratio": round((longform_hours / total_hours) * 100, 1),
            "shorts_hours_per_video": round(shorts_hours_per_video, 2),
            "longform_hours_per_video": round(longform_hours_per_video, 2),
            "shorts_efficiency_ratio": round(shorts_efficiency, 1),
            "longform_efficiency_ratio": round(longform_efficiency, 1),
        }

        return {"metrics": metrics, "insights": insights}

    def _analyze_topic_crossover(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze topic overlap between Shorts and long-form"""
        # This would be enhanced with NLP analysis of titles/descriptions
        # For now, basic keyword analysis

        if 'title' not in df.columns:
            return {"metrics": {}}

        shorts = df[df['is_short'] == True]
        longform = df[df['is_short'] == False]

        # Extract keywords (simple word frequency)
        def extract_keywords(titles):
            words = []
            for title in titles.dropna():
                # Clean and split
                clean = str(title).lower()
                for char in '#📊🎯💡🏆📈📉⚠️🔥💰📱🎬':
                    clean = clean.replace(char, '')
                words.extend(clean.split())
            return set(words)

        shorts_keywords = extract_keywords(shorts['title']) if len(shorts) > 0 else set()
        longform_keywords = extract_keywords(longform['title']) if len(longform) > 0 else set()

        # Find overlap
        common_keywords = shorts_keywords.intersection(longform_keywords)
        overlap_ratio = len(common_keywords) / len(shorts_keywords.union(longform_keywords)) if shorts_keywords or longform_keywords else 0

        metrics = {
            "keyword_overlap_ratio": round(overlap_ratio * 100, 1),
            "common_themes_count": len(common_keywords),
        }

        return {"metrics": metrics}

    def _build_strategy(self, metrics: Dict, insights: List) -> List[Dict[str, str]]:
        """Build strategic recommendations based on analysis"""
        recommendations = []
        strategy_type = metrics.get('strategy_type', 'UNKNOWN')

        if strategy_type == "SHORTS_DOMINANT":
            recommendations.extend([
                {
                    "priority": "HIGH",
                    "action": "Increase long-form content production",
                    "details": "Aim for 1-2 long-form videos per week. Your Shorts audience is established; "
                              "now build watch time for monetization.",
                },
                {
                    "priority": "HIGH",
                    "action": "Create Shorts that tease long-form content",
                    "details": "End Shorts with hooks like 'Full story in our latest video' with pinned comment "
                              "linking to the long-form version.",
                },
                {
                    "priority": "MEDIUM",
                    "action": "Launch a 'best of' compilation series",
                    "details": "Combine your top Shorts into 10-15 minute compilations. This converts Shorts "
                              "views into long-form watch time.",
                },
            ])

        elif strategy_type == "LONGFORM_DOMINANT":
            recommendations.extend([
                {
                    "priority": "HIGH",
                    "action": "Start consistent Shorts production",
                    "details": "Aim for 3-5 Shorts per week. Extract best moments from long-form videos as "
                              "Shorts to cross-promote.",
                },
                {
                    "priority": "MEDIUM",
                    "action": "Repurpose existing content",
                    "details": "Your long-form archive is a goldmine. Extract vertical clips of the most engaging "
                              "30-60 second moments.",
                },
            ])

        elif strategy_type == "BALANCED":
            recommendations.extend([
                {
                    "priority": "MEDIUM",
                    "action": "Optimize the funnel between content types",
                    "details": "Create clear pathways from Shorts to long-form. Use end screens, pinned comments, "
                              "and verbal CTAs.",
                },
                {
                    "priority": "MEDIUM",
                    "action": "Test topic resonance across formats",
                    "details": "Topics that work in Shorts often work as long-form (and vice versa). "
                              "Use Shorts to test ideas before full production.",
                },
            ])

        # Add recommendations based on subscriber dynamics
        if metrics.get('shorts_sub_ratio', 0) > 70:
            recommendations.append({
                "priority": "HIGH",
                "action": "Re-engage Shorts subscribers with long-form",
                "details": "Create a 'For Our Shorts Fans' playlist. Make the first 30 seconds of long-form "
                          "videos feel like extended Shorts to ease the transition.",
            })

        return recommendations

    def _calculate_severity(self, metrics: Dict) -> str:
        """Calculate severity based on strategy health"""
        strategy_type = metrics.get('strategy_type', 'UNKNOWN')
        shorts_sub_ratio = metrics.get('shorts_sub_ratio', 0)

        if strategy_type == "SHORTS_DOMINANT" and shorts_sub_ratio > 80:
            return "WARNING"  # Heavy Shorts dependency
        elif strategy_type == "BALANCED":
            return "OK"
        else:
            return "WATCH"

    def _generate_digest(self, metrics: Dict, insights: List,
                        recommendations: List, severity: str) -> str:
        """Generate human-readable summary"""
        lines = [
            "=" * 60,
            "SHORTS STRATEGY ANALYSIS",
            "=" * 60,
            "",
            f"Strategy Type: {metrics.get('strategy_type', 'UNKNOWN')}",
            f"Status: {severity}",
            "",
            "📊 CONTENT MIX",
            f"  Shorts: {metrics.get('shorts_count', 0)} ({metrics.get('shorts_ratio', 0):.0f}%)",
            f"  Long-form: {metrics.get('longform_count', 0)} ({metrics.get('longform_ratio', 0):.0f}%)",
            f"  Ideal Shorts ratio: {metrics.get('ideal_shorts_ratio', 40):.0f}%",
            "",
            "👥 SUBSCRIBER CONTRIBUTION",
            f"  From Shorts: {metrics.get('shorts_subscribers_gained', 0):,} ({metrics.get('shorts_sub_ratio', 0):.0f}%)",
            f"  From Long-form: {metrics.get('longform_subscribers_gained', 0):,} ({metrics.get('longform_sub_ratio', 0):.0f}%)",
            "",
            "⏱️ WATCH TIME",
            f"  Shorts: {metrics.get('shorts_watch_hours', 0):,.0f} hours ({metrics.get('shorts_hours_ratio', 0):.0f}%)",
            f"  Long-form: {metrics.get('longform_watch_hours', 0):,.0f} hours ({metrics.get('longform_hours_ratio', 0):.0f}%)",
            "",
            "🎯 VIRAL POTENTIAL",
            f"  Shorts peak: {metrics.get('shorts_max_views', 0):,} views",
            f"  Long-form peak: {metrics.get('longform_max_views', 0):,} views",
            "",
        ]

        if insights:
            lines.append("💡 KEY INSIGHTS")
            for insight in insights:
                lines.append(f"  • {insight}")
            lines.append("")

        if recommendations:
            lines.append("📝 STRATEGY RECOMMENDATIONS")
            for rec in recommendations[:4]:
                lines.append(f"  [{rec['priority']}] {rec['action']}")
                lines.append(f"       {rec['details'][:80]}...")
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)
