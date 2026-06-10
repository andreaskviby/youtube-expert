"""
Thumbnail & Title Optimizer Skill

Identifies videos that need thumbnail/title optimization based on
CTR performance, and provides A/B testing recommendations.
"""

from __future__ import annotations

from typing import Dict, Any, List, TYPE_CHECKING
import pandas as pd
import numpy as np
import re

from .base import BaseSkill

if TYPE_CHECKING:
    from ..core import ChannelData


class ThumbnailOptimizerSkill(BaseSkill):
    """
    Thumbnail and title A/B testing recommendations

    Identifies underperforming thumbnails based on CTR data,
    prioritizes videos for refresh, and provides optimization
    guidelines based on top performers.
    """

    name = "thumbnail_optimizer"
    description = "Thumbnail & title A/B test recommendations"

    # CTR benchmarks
    CTR_EXCELLENT = 6.0
    CTR_GOOD = 4.0
    CTR_AVERAGE = 2.5
    CTR_POOR = 1.5

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

        # === CTR PERFORMANCE TIERS ===
        ctr_analysis = self._analyze_ctr_tiers(df)
        metrics.update(ctr_analysis['metrics'])
        insights.extend(ctr_analysis['insights'])

        # === TITLE ANALYSIS ===
        title_analysis = self._analyze_titles(df)
        metrics.update(title_analysis['metrics'])
        insights.extend(title_analysis['insights'])

        # === PRIORITY CANDIDATES FOR REFRESH ===
        priority_analysis = self._identify_priority_candidates(df)
        metrics.update(priority_analysis['metrics'])

        # === TOP PERFORMER PATTERNS ===
        pattern_analysis = self._analyze_top_performer_patterns(df)
        metrics.update(pattern_analysis['metrics'])
        insights.extend(pattern_analysis['insights'])

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

    def _analyze_ctr_tiers(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Categorize videos by CTR performance"""
        insights = []

        if 'ctr_percent' not in df.columns or 'impressions' not in df.columns:
            return {"metrics": {}, "insights": []}

        # Only analyze videos with meaningful impressions
        df_valid = df[(df['ctr_percent'].notna()) & (df['impressions'] > 500)]

        if len(df_valid) == 0:
            return {"metrics": {}, "insights": []}

        # Categorize by CTR tier
        excellent = df_valid[df_valid['ctr_percent'] >= self.CTR_EXCELLENT]
        good = df_valid[(df_valid['ctr_percent'] >= self.CTR_GOOD) & (df_valid['ctr_percent'] < self.CTR_EXCELLENT)]
        average = df_valid[(df_valid['ctr_percent'] >= self.CTR_AVERAGE) & (df_valid['ctr_percent'] < self.CTR_GOOD)]
        poor = df_valid[(df_valid['ctr_percent'] >= self.CTR_POOR) & (df_valid['ctr_percent'] < self.CTR_AVERAGE)]
        critical = df_valid[df_valid['ctr_percent'] < self.CTR_POOR]

        total = len(df_valid)

        # Calculate distribution
        distribution = {
            "excellent": {"count": len(excellent), "percent": round(len(excellent) / total * 100, 1)},
            "good": {"count": len(good), "percent": round(len(good) / total * 100, 1)},
            "average": {"count": len(average), "percent": round(len(average) / total * 100, 1)},
            "poor": {"count": len(poor), "percent": round(len(poor) / total * 100, 1)},
            "critical": {"count": len(critical), "percent": round(len(critical) / total * 100, 1)},
        }

        avg_ctr = df_valid['ctr_percent'].mean()
        median_ctr = df_valid['ctr_percent'].median()

        if len(critical) > total * 0.3:
            insights.append(f"⚠️ {distribution['critical']['percent']:.0f}% of videos have critical CTR (<{self.CTR_POOR}%)")

        if avg_ctr < self.CTR_AVERAGE:
            insights.append(f"Average CTR ({avg_ctr:.1f}%) is below benchmark ({self.CTR_AVERAGE}%)")

        if len(excellent) > 0:
            insights.append(f"You have {len(excellent)} videos with excellent CTR (≥{self.CTR_EXCELLENT}%) - study their patterns")

        metrics = {
            "ctr_distribution": distribution,
            "average_ctr": round(avg_ctr, 2),
            "median_ctr": round(median_ctr, 2),
            "videos_analyzed": total,
            "excellent_ctr_videos": self._videos_to_list(excellent),
            "critical_ctr_videos": self._videos_to_list(critical),
        }

        return {"metrics": metrics, "insights": insights}

    def _analyze_titles(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze title patterns and their correlation with CTR"""
        insights = []

        if 'title' not in df.columns or 'ctr_percent' not in df.columns:
            return {"metrics": {}, "insights": []}

        df_valid = df[df['ctr_percent'].notna() & df['title'].notna()].copy()

        if len(df_valid) == 0:
            return {"metrics": {}, "insights": []}

        # Title characteristics
        df_valid['title_length'] = df_valid['title'].str.len()
        df_valid['has_emoji'] = df_valid['title'].str.contains(r'[\U0001F300-\U0001F9FF]', regex=True)
        df_valid['has_number'] = df_valid['title'].str.contains(r'\d', regex=True)
        df_valid['has_caps'] = df_valid['title'].str.contains(r'[A-Z]{3,}', regex=True)
        df_valid['has_question'] = df_valid['title'].str.contains(r'\?', regex=True)
        df_valid['word_count'] = df_valid['title'].str.split().str.len()

        # Correlation analysis
        correlations = {}

        # Title length vs CTR
        short_titles = df_valid[df_valid['title_length'] <= 40]
        long_titles = df_valid[df_valid['title_length'] > 40]

        if len(short_titles) > 5 and len(long_titles) > 5:
            short_ctr = short_titles['ctr_percent'].mean()
            long_ctr = long_titles['ctr_percent'].mean()
            correlations['title_length'] = {
                "short_avg_ctr": round(short_ctr, 2),
                "long_avg_ctr": round(long_ctr, 2),
                "better": "short" if short_ctr > long_ctr else "long",
            }
            if abs(short_ctr - long_ctr) > 0.5:
                if short_ctr > long_ctr:
                    insights.append(f"Shorter titles (≤40 chars) have higher CTR ({short_ctr:.1f}% vs {long_ctr:.1f}%)")
                else:
                    insights.append(f"Longer titles perform better for your channel ({long_ctr:.1f}% vs {short_ctr:.1f}%)")

        # Emoji impact
        with_emoji = df_valid[df_valid['has_emoji'] == True]
        without_emoji = df_valid[df_valid['has_emoji'] == False]

        if len(with_emoji) > 5 and len(without_emoji) > 5:
            emoji_ctr = with_emoji['ctr_percent'].mean()
            no_emoji_ctr = without_emoji['ctr_percent'].mean()
            correlations['emoji'] = {
                "with_emoji_ctr": round(emoji_ctr, 2),
                "without_emoji_ctr": round(no_emoji_ctr, 2),
                "better": "with" if emoji_ctr > no_emoji_ctr else "without",
            }
            if abs(emoji_ctr - no_emoji_ctr) > 0.5:
                if emoji_ctr > no_emoji_ctr:
                    insights.append(f"Titles with emojis have higher CTR ({emoji_ctr:.1f}% vs {no_emoji_ctr:.1f}%)")

        # Numbers in title
        with_number = df_valid[df_valid['has_number'] == True]
        without_number = df_valid[df_valid['has_number'] == False]

        if len(with_number) > 5 and len(without_number) > 5:
            number_ctr = with_number['ctr_percent'].mean()
            no_number_ctr = without_number['ctr_percent'].mean()
            correlations['numbers'] = {
                "with_number_ctr": round(number_ctr, 2),
                "without_number_ctr": round(no_number_ctr, 2),
                "better": "with" if number_ctr > no_number_ctr else "without",
            }

        avg_title_length = df_valid['title_length'].mean()
        avg_word_count = df_valid['word_count'].mean()

        metrics = {
            "avg_title_length": round(avg_title_length, 1),
            "avg_word_count": round(avg_word_count, 1),
            "titles_with_emoji_percent": round(len(with_emoji) / len(df_valid) * 100, 1),
            "title_correlations": correlations,
        }

        return {"metrics": metrics, "insights": insights}

    def _identify_priority_candidates(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identify videos that should be prioritized for thumbnail refresh"""

        if 'ctr_percent' not in df.columns or 'impressions' not in df.columns:
            return {"metrics": {}}

        df_valid = df[(df['ctr_percent'].notna()) & (df['impressions'] > 1000)].copy()

        if len(df_valid) == 0:
            return {"metrics": {}}

        # Calculate potential impact
        # Videos with high impressions but low CTR have the most upside
        df_valid['potential_impact'] = df_valid['impressions'] * (self.CTR_GOOD - df_valid['ctr_percent'].clip(upper=self.CTR_GOOD))

        # Priority 1: High impressions + Low CTR (biggest opportunity)
        high_opportunity = df_valid[(df_valid['impressions'] > 5000) & (df_valid['ctr_percent'] < self.CTR_AVERAGE)]
        high_opportunity = high_opportunity.nlargest(10, 'potential_impact')

        # Priority 2: Decent CTR but could be better (optimization opportunities)
        optimization_candidates = df_valid[(df_valid['ctr_percent'] >= self.CTR_AVERAGE) & (df_valid['ctr_percent'] < self.CTR_GOOD)]
        optimization_candidates = optimization_candidates.nlargest(10, 'impressions')

        # Priority 3: New videos with low initial CTR
        if 'published_at' in df_valid.columns:
            recent = df_valid[df_valid['published_at'].notna()].nlargest(20, 'published_at')
            recent_low_ctr = recent[recent['ctr_percent'] < self.CTR_AVERAGE]
        else:
            recent_low_ctr = pd.DataFrame()

        metrics = {
            "high_opportunity_videos": self._videos_to_list(high_opportunity),
            "optimization_candidates": self._videos_to_list(optimization_candidates),
            "recent_low_ctr_videos": self._videos_to_list(recent_low_ctr),
            "total_opportunity_videos": len(high_opportunity) + len(optimization_candidates),
        }

        return {"metrics": metrics}

    def _analyze_top_performer_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze patterns in top-performing thumbnails/titles"""
        insights = []

        if 'ctr_percent' not in df.columns or 'title' not in df.columns:
            return {"metrics": {}, "insights": []}

        # Get top 10% by CTR (with decent impressions)
        df_valid = df[(df['ctr_percent'].notna()) & (df['impressions'] > 1000)]
        if len(df_valid) < 10:
            return {"metrics": {}, "insights": []}

        top_performers = df_valid.nlargest(int(len(df_valid) * 0.1), 'ctr_percent')

        # Analyze title patterns of top performers
        top_titles = top_performers['title'].tolist()

        # Common words in top performers
        all_words = []
        for title in top_titles:
            words = str(title).lower().split()
            all_words.extend(words)

        from collections import Counter
        word_freq = Counter(all_words)

        # Filter out common words
        stopwords = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'is', 'it', 'you', 'i', 'we', '|', '-', '#'}
        common_in_top = {word: count for word, count in word_freq.most_common(20) if word not in stopwords and len(word) > 2}

        # Check for patterns
        patterns_found = []

        emoji_count = sum(1 for t in top_titles if re.search(r'[\U0001F300-\U0001F9FF]', str(t)))
        if emoji_count > len(top_titles) * 0.5:
            patterns_found.append(f"{emoji_count}/{len(top_titles)} use emojis")

        caps_count = sum(1 for t in top_titles if re.search(r'[A-Z]{3,}', str(t)))
        if caps_count > len(top_titles) * 0.3:
            patterns_found.append(f"{caps_count}/{len(top_titles)} use CAPS for emphasis")

        question_count = sum(1 for t in top_titles if '?' in str(t))
        if question_count > len(top_titles) * 0.2:
            patterns_found.append(f"{question_count}/{len(top_titles)} ask questions")

        if patterns_found:
            insights.append("Top performer patterns: " + ", ".join(patterns_found))

        if common_in_top:
            top_words = list(common_in_top.keys())[:5]
            insights.append(f"Common words in top titles: {', '.join(top_words)}")

        metrics = {
            "top_performer_patterns": patterns_found,
            "common_words_in_top": list(common_in_top.items())[:10],
            "top_performer_examples": self._videos_to_list(top_performers.head(5)),
        }

        return {"metrics": metrics, "insights": insights}

    def _videos_to_list(self, df: pd.DataFrame) -> List[Dict]:
        """Convert DataFrame to list of video dicts"""
        if df.empty:
            return []

        cols = ['video_id', 'title', 'views', 'impressions', 'ctr_percent', 'content_type']
        available = [c for c in cols if c in df.columns]

        result = df[available].head(10).to_dict('records')
        for item in result:
            for key, value in item.items():
                if isinstance(value, float) and pd.notna(value):
                    item[key] = round(value, 2)
                elif pd.isna(value):
                    item[key] = None
        return result

    def _build_recommendations(self, metrics: Dict, insights: List) -> List[Dict[str, str]]:
        """Build actionable recommendations"""
        recommendations = []

        # High opportunity videos
        high_opp = metrics.get('high_opportunity_videos', [])
        if len(high_opp) > 3:
            recommendations.append({
                "priority": "HIGH",
                "action": f"A/B test thumbnails on {len(high_opp)} high-opportunity videos",
                "details": "These videos have significant impressions but low CTR. "
                          "New thumbnails could dramatically increase views.",
            })

        # Based on CTR distribution
        dist = metrics.get('ctr_distribution', {})
        critical_pct = dist.get('critical', {}).get('percent', 0)
        if critical_pct > 20:
            recommendations.append({
                "priority": "HIGH",
                "action": "Audit thumbnail/title strategy",
                "details": f"{critical_pct:.0f}% of videos have critical CTR. This indicates a systematic issue. "
                          "Review top performer patterns and apply them consistently.",
            })

        # Title recommendations based on correlations
        correlations = metrics.get('title_correlations', {})
        if correlations.get('emoji', {}).get('better') == 'with':
            emoji_lift = correlations['emoji']['with_emoji_ctr'] - correlations['emoji']['without_emoji_ctr']
            if emoji_lift > 0.5:
                recommendations.append({
                    "priority": "MEDIUM",
                    "action": "Add emojis to underperforming titles",
                    "details": f"Emojis correlate with +{emoji_lift:.1f}% CTR on your channel.",
                })

        if correlations.get('title_length', {}).get('better') == 'short':
            recommendations.append({
                "priority": "MEDIUM",
                "action": "Shorten titles to ≤40 characters",
                "details": "Shorter titles perform better for your audience. Front-load the hook.",
            })

        # Thumbnail design recommendations
        recommendations.append({
            "priority": "MEDIUM",
            "action": "Follow thumbnail best practices",
            "details": "Use contrasting colors, expressive faces (eyes visible), "
                      "3 words or less of large text. Ensure readability on mobile.",
        })

        return recommendations

    def _calculate_severity(self, metrics: Dict) -> str:
        """Calculate severity based on CTR health"""
        avg_ctr = metrics.get('average_ctr', 3)
        dist = metrics.get('ctr_distribution', {})
        critical_pct = dist.get('critical', {}).get('percent', 0)

        if avg_ctr < 2 or critical_pct > 30:
            return "WARNING"
        elif avg_ctr < 3 or critical_pct > 15:
            return "WATCH"
        return "OK"

    def _generate_digest(self, metrics: Dict, insights: List,
                        recommendations: List, severity: str) -> str:
        """Generate human-readable summary"""
        lines = [
            "=" * 60,
            "THUMBNAIL & TITLE OPTIMIZATION REPORT",
            "=" * 60,
            "",
            f"Status: {severity}",
            "",
            "📊 CTR PERFORMANCE",
            f"  Average CTR: {metrics.get('average_ctr', 0):.1f}%",
            f"  Videos analyzed: {metrics.get('videos_analyzed', 0)}",
            "",
        ]

        # CTR distribution
        dist = metrics.get('ctr_distribution', {})
        if dist:
            lines.append("CTR DISTRIBUTION")
            lines.append(f"  Excellent (≥6%): {dist.get('excellent', {}).get('count', 0)} videos")
            lines.append(f"  Good (4-6%): {dist.get('good', {}).get('count', 0)} videos")
            lines.append(f"  Average (2.5-4%): {dist.get('average', {}).get('count', 0)} videos")
            lines.append(f"  Poor (1.5-2.5%): {dist.get('poor', {}).get('count', 0)} videos")
            lines.append(f"  Critical (<1.5%): {dist.get('critical', {}).get('count', 0)} videos")
            lines.append("")

        # High opportunity videos
        high_opp = metrics.get('high_opportunity_videos', [])
        if high_opp:
            lines.append("🎯 PRIORITY: REFRESH THESE THUMBNAILS")
            for v in high_opp[:5]:
                lines.append(f"  {v.get('ctr_percent', 0):.1f}% CTR | {v.get('impressions', 0):,} impr | {v.get('title', '')[:35]}...")
            lines.append("")

        # Insights
        if insights:
            lines.append("💡 INSIGHTS")
            for insight in insights:
                lines.append(f"  • {insight}")
            lines.append("")

        # Recommendations
        if recommendations:
            lines.append("📝 RECOMMENDATIONS")
            for rec in recommendations[:4]:
                lines.append(f"  [{rec['priority']}] {rec['action']}")
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)
