"""
Trend Detector Skill - Identify trending topics and viral patterns

Analyzes content performance to detect emerging trends and viral patterns.
"""

from __future__ import annotations

from typing import Dict, Any, List, TYPE_CHECKING
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import Counter
import re

from .base import BaseSkill

if TYPE_CHECKING:
    from ..core import ChannelData


class TrendDetectorSkill(BaseSkill):
    """
    Trending topics and viral pattern detection

    Identifies which content is trending, detects viral patterns,
    and provides recommendations for capitalizing on trends.
    """

    name = "trend_detector"
    description = "Trending topics and viral pattern detection"

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

        # === VIRAL VIDEO DETECTION ===
        viral_analysis = self._detect_viral_videos(df)
        metrics.update(viral_analysis['metrics'])
        insights.extend(viral_analysis['insights'])

        # === RECENT PERFORMANCE TRENDS ===
        recent_trends = self._analyze_recent_trends(df)
        metrics.update(recent_trends['metrics'])
        insights.extend(recent_trends['insights'])

        # === BREAKOUT CONTENT ===
        breakout = self._identify_breakout_content(df)
        metrics.update(breakout['metrics'])
        insights.extend(breakout['insights'])

        # === VIRAL PATTERNS ===
        patterns = self._analyze_viral_patterns(df)
        metrics.update(patterns['metrics'])
        insights.extend(patterns['insights'])

        # === MOMENTUM ANALYSIS ===
        momentum = self._analyze_momentum(df)
        metrics.update(momentum['metrics'])

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

    def _detect_viral_videos(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect videos that went viral"""
        insights = []

        if 'views' not in df.columns:
            return {"metrics": {}, "insights": []}

        views = df['views'].dropna()
        mean_views = views.mean()
        std_views = views.std()

        # Viral threshold: 3+ standard deviations above mean
        viral_threshold = mean_views + (3 * std_views)
        viral_videos = df[df['views'] > viral_threshold]

        # Breakout threshold: 1-3 standard deviations
        breakout_threshold = mean_views + std_views
        breakout_videos = df[(df['views'] > breakout_threshold) & (df['views'] <= viral_threshold)]

        if len(viral_videos) > 0:
            insights.append(f"You have {len(viral_videos)} viral videos (3+ std dev above mean)")

        # Analyze viral video characteristics
        viral_characteristics = {}
        if len(viral_videos) > 0:
            if 'content_type' in viral_videos.columns:
                type_dist = viral_videos['content_type'].value_counts()
                viral_characteristics['content_type_distribution'] = type_dist.to_dict()

            if 'duration_seconds' in viral_videos.columns:
                viral_characteristics['avg_duration'] = round(viral_videos['duration_seconds'].mean(), 0)

        metrics = {
            "viral_threshold": int(viral_threshold),
            "breakout_threshold": int(breakout_threshold),
            "viral_video_count": len(viral_videos),
            "breakout_video_count": len(breakout_videos),
            "viral_videos": viral_videos[['video_id', 'title', 'views', 'content_type']].to_dict('records') if 'content_type' in viral_videos.columns else [],
            "viral_characteristics": viral_characteristics,
        }

        return {"metrics": metrics, "insights": insights}

    def _analyze_recent_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze recent performance trends"""
        insights = []

        if 'published_at' not in df.columns or 'views' not in df.columns:
            return {"metrics": {}, "insights": []}

        df_dated = df[df['published_at'].notna()].copy()
        df_dated = df_dated.sort_values('published_at')

        if len(df_dated) < 10:
            return {"metrics": {}, "insights": []}

        # Compare last 10 videos to previous 10
        last_10 = df_dated.tail(10)
        previous_10 = df_dated.iloc[-20:-10] if len(df_dated) >= 20 else df_dated.head(10)

        last_avg = last_10['views'].mean()
        previous_avg = previous_10['views'].mean()

        trend_change = ((last_avg - previous_avg) / previous_avg * 100) if previous_avg > 0 else 0

        if trend_change > 50:
            trend_status = "HOT"
            insights.append(f"🔥 Channel is HOT! Recent videos up {trend_change:.0f}% vs previous")
        elif trend_change > 20:
            trend_status = "TRENDING_UP"
            insights.append(f"📈 Positive momentum: +{trend_change:.0f}% vs previous videos")
        elif trend_change > -20:
            trend_status = "STABLE"
        else:
            trend_status = "COOLING"
            insights.append(f"📉 Recent videos down {abs(trend_change):.0f}% vs previous")

        # Find the recent standout
        if len(last_10) > 0:
            best_recent = last_10.loc[last_10['views'].idxmax()]
            if best_recent['views'] > last_avg * 2:
                insights.append(f"Recent standout: '{best_recent['title'][:30]}...' ({best_recent['views']:,} views)")

        metrics = {
            "trend_status": trend_status,
            "recent_vs_previous_pct": round(trend_change, 1),
            "last_10_avg_views": round(last_avg, 0),
            "previous_10_avg_views": round(previous_avg, 0),
            "best_recent_video": {
                "title": best_recent['title'] if len(last_10) > 0 else None,
                "views": int(best_recent['views']) if len(last_10) > 0 else 0,
            },
        }

        return {"metrics": metrics, "insights": insights}

    def _identify_breakout_content(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identify content that broke out relative to channel average"""
        insights = []

        if 'views' not in df.columns:
            return {"metrics": {}, "insights": []}

        # Calculate view ratio vs median
        median_views = df['views'].median()
        df = df.copy()
        df['view_ratio'] = df['views'] / median_views

        # Breakout = 5x+ median views
        breakouts = df[df['view_ratio'] >= 5].nlargest(10, 'views')

        if len(breakouts) > 0:
            # Analyze what breakouts have in common
            common_elements = []

            if 'content_type' in breakouts.columns:
                dominant_type = breakouts['content_type'].mode()
                if len(dominant_type) > 0:
                    common_elements.append(f"mostly {dominant_type.iloc[0]}")

            if 'title' in breakouts.columns:
                # Check for common words
                all_words = []
                for title in breakouts['title'].dropna():
                    words = str(title).lower().split()
                    all_words.extend(words)

                word_freq = Counter(all_words)
                common_words = [w for w, c in word_freq.most_common(10) if len(w) > 3 and c >= 2]
                if common_words:
                    common_elements.append(f"common words: {', '.join(common_words[:3])}")

            if common_elements:
                insights.append(f"Breakout videos are {', '.join(common_elements)}")

        metrics = {
            "breakout_videos": breakouts[['video_id', 'title', 'views', 'view_ratio']].to_dict('records') if 'view_ratio' in breakouts.columns else [],
            "breakout_count": len(breakouts),
            "median_views": int(median_views),
        }

        return {"metrics": metrics, "insights": insights}

    def _analyze_viral_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze patterns in viral/high-performing content"""
        insights = []

        if 'views' not in df.columns or 'title' not in df.columns:
            return {"metrics": {}, "insights": []}

        # Get top 20% performers
        top_threshold = df['views'].quantile(0.8)
        top_videos = df[df['views'] >= top_threshold]

        patterns = {}

        # Title length pattern
        if len(top_videos) > 5:
            top_videos = top_videos.copy()
            top_videos['title_length'] = top_videos['title'].str.len()
            avg_top_length = top_videos['title_length'].mean()

            rest = df[df['views'] < top_threshold].copy()
            rest['title_length'] = rest['title'].str.len()
            avg_rest_length = rest['title_length'].mean()

            if avg_top_length < avg_rest_length * 0.8:
                patterns['title_length'] = "shorter"
                insights.append("Viral content tends to have shorter titles")
            elif avg_top_length > avg_rest_length * 1.2:
                patterns['title_length'] = "longer"
                insights.append("Viral content tends to have longer, more descriptive titles")

        # Emoji pattern
        top_emoji_pct = sum(1 for t in top_videos['title'] if re.search(r'[\U0001F300-\U0001F9FF]', str(t))) / len(top_videos) * 100 if len(top_videos) > 0 else 0
        patterns['emoji_usage_pct'] = round(top_emoji_pct, 0)

        # Caps pattern
        top_caps_pct = sum(1 for t in top_videos['title'] if re.search(r'[A-Z]{3,}', str(t))) / len(top_videos) * 100 if len(top_videos) > 0 else 0
        patterns['caps_usage_pct'] = round(top_caps_pct, 0)

        # Content type pattern
        if 'content_type' in top_videos.columns:
            type_dist = top_videos['content_type'].value_counts(normalize=True) * 100
            patterns['content_type_distribution'] = type_dist.round(0).to_dict()

        metrics = {
            "viral_patterns": patterns,
        }

        return {"metrics": metrics, "insights": insights}

    def _analyze_momentum(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze channel momentum over time"""

        if 'published_at' not in df.columns or 'views' not in df.columns:
            return {"metrics": {}}

        df_dated = df[df['published_at'].notna()].copy()
        df_dated = df_dated.sort_values('published_at')

        if len(df_dated) < 5:
            return {"metrics": {}}

        # Calculate rolling average
        df_dated['rolling_views'] = df_dated['views'].rolling(5, min_periods=1).mean()

        # Calculate momentum (rate of change)
        if len(df_dated) >= 10:
            first_half_avg = df_dated.iloc[:len(df_dated)//2]['rolling_views'].mean()
            second_half_avg = df_dated.iloc[len(df_dated)//2:]['rolling_views'].mean()

            momentum = (second_half_avg - first_half_avg) / first_half_avg * 100 if first_half_avg > 0 else 0
        else:
            momentum = 0

        # Recent momentum (last 5 vs previous 5)
        if len(df_dated) >= 10:
            recent_5 = df_dated.tail(5)['views'].mean()
            previous_5 = df_dated.iloc[-10:-5]['views'].mean()
            recent_momentum = (recent_5 - previous_5) / previous_5 * 100 if previous_5 > 0 else 0
        else:
            recent_momentum = 0

        metrics = {
            "overall_momentum_pct": round(momentum, 1),
            "recent_momentum_pct": round(recent_momentum, 1),
            "momentum_status": "ACCELERATING" if recent_momentum > 20 else ("STEADY" if recent_momentum > -20 else "SLOWING"),
        }

        return {"metrics": metrics}

    def _build_recommendations(self, metrics: Dict, insights: List) -> List[Dict[str, str]]:
        """Build trend-based recommendations"""
        recommendations = []

        trend_status = metrics.get('trend_status', 'UNKNOWN')
        momentum_status = metrics.get('momentum_status', 'UNKNOWN')

        if trend_status == "HOT":
            recommendations.append({
                "priority": "HIGH",
                "action": "Capitalize on momentum - increase upload frequency",
                "details": "The algorithm is favoring your content. Upload more while the momentum lasts.",
            })

        if trend_status == "COOLING":
            recommendations.append({
                "priority": "HIGH",
                "action": "Analyze what changed in recent content",
                "details": "Recent videos are underperforming. Compare to your viral hits and identify differences.",
            })

        # Viral pattern recommendations
        patterns = metrics.get('viral_patterns', {})
        if patterns.get('emoji_usage_pct', 0) > 70:
            recommendations.append({
                "priority": "MEDIUM",
                "action": "Continue using emojis in titles",
                "details": f"{patterns['emoji_usage_pct']:.0f}% of your top performers use emojis.",
            })

        # Breakout recommendations
        breakout_count = metrics.get('breakout_count', 0)
        if breakout_count >= 3:
            recommendations.append({
                "priority": "MEDIUM",
                "action": "Study your breakout videos",
                "details": f"You have {breakout_count} videos that significantly outperformed. Replicate their elements.",
            })

        return recommendations

    def _calculate_severity(self, metrics: Dict) -> str:
        """Calculate severity"""
        trend_status = metrics.get('trend_status', 'STABLE')

        if trend_status == "HOT":
            return "OK"  # Good status
        elif trend_status == "COOLING":
            return "WARNING"
        return "OK"

    def _generate_digest(self, metrics: Dict, insights: List,
                        recommendations: List, severity: str) -> str:
        """Generate human-readable summary"""
        lines = [
            "=" * 60,
            "TREND DETECTION REPORT",
            "=" * 60,
            "",
            f"Channel Status: {metrics.get('trend_status', 'UNKNOWN')}",
            f"Momentum: {metrics.get('momentum_status', 'UNKNOWN')}",
            "",
        ]

        # Recent trends
        lines.extend([
            "📈 RECENT PERFORMANCE",
            f"  Last 10 videos avg: {metrics.get('last_10_avg_views', 0):,.0f} views",
            f"  vs Previous 10: {metrics.get('recent_vs_previous_pct', 0):+.0f}%",
            "",
        ])

        # Viral videos
        viral_count = metrics.get('viral_video_count', 0)
        if viral_count > 0:
            lines.append(f"🚀 VIRAL VIDEOS: {viral_count}")
            for v in metrics.get('viral_videos', [])[:3]:
                lines.append(f"  {v.get('views', 0):,} - {v.get('title', '')[:35]}...")
            lines.append("")

        # Breakout videos
        breakout_count = metrics.get('breakout_count', 0)
        if breakout_count > 0:
            lines.extend([
                f"⚡ BREAKOUT VIDEOS: {breakout_count}",
                f"  (Videos with 5x+ median views)",
                "",
            ])

        # Viral patterns
        patterns = metrics.get('viral_patterns', {})
        if patterns:
            lines.append("🎯 VIRAL PATTERNS IN TOP PERFORMERS")
            if 'emoji_usage_pct' in patterns:
                lines.append(f"  Emoji usage: {patterns['emoji_usage_pct']:.0f}%")
            if 'caps_usage_pct' in patterns:
                lines.append(f"  CAPS usage: {patterns['caps_usage_pct']:.0f}%")
            if 'content_type_distribution' in patterns:
                for ctype, pct in patterns['content_type_distribution'].items():
                    lines.append(f"  {ctype}: {pct:.0f}%")
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
