"""
SEO Optimizer Skill - Title, tags, and description optimization

Analyzes title and metadata patterns to improve discoverability.
"""

from __future__ import annotations

from typing import Dict, Any, List, TYPE_CHECKING
import pandas as pd
import numpy as np
import re
from collections import Counter

from .base import BaseSkill

if TYPE_CHECKING:
    from ..core import ChannelData


class SEOOptimizerSkill(BaseSkill):
    """
    YouTube SEO optimization

    Analyzes titles, identifies keyword patterns in top performers,
    and provides recommendations for improving discoverability.
    """

    name = "seo_optimizer"
    description = "Title, tag, and description SEO analysis"

    def analyze(self, data: ChannelData, **kwargs) -> Dict[str, Any]:
        if data.videos_df is None:
            return {"error": "No video data available"}

        df = data.videos_df.copy()

        # Filter out total/summary rows
        if 'video_id' in df.columns:
            df = df[df['video_id'].notna() & (df['video_id'] != 'Totalt')]

        if 'title' not in df.columns:
            return {"error": "No title data available"}

        metrics = {}
        insights = []
        recommendations = []

        # === KEYWORD ANALYSIS ===
        keyword_analysis = self._analyze_keywords(df)
        metrics.update(keyword_analysis['metrics'])
        insights.extend(keyword_analysis['insights'])

        # === TITLE STRUCTURE ANALYSIS ===
        structure_analysis = self._analyze_title_structure(df)
        metrics.update(structure_analysis['metrics'])
        insights.extend(structure_analysis['insights'])

        # === HASHTAG ANALYSIS ===
        hashtag_analysis = self._analyze_hashtags(df)
        metrics.update(hashtag_analysis['metrics'])
        insights.extend(hashtag_analysis['insights'])

        # === TOP PERFORMER KEYWORDS ===
        top_keywords = self._extract_top_performer_keywords(df)
        metrics.update(top_keywords['metrics'])

        # === BUILD RECOMMENDATIONS ===
        recommendations = self._build_recommendations(metrics, insights)

        severity = "OK"
        digest = self._generate_digest(metrics, insights, recommendations, severity)

        return {
            "metrics": metrics,
            "insights": insights,
            "recommendations": recommendations,
            "severity": severity,
            "digest": digest,
        }

    def _analyze_keywords(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze keyword frequency and performance correlation"""
        insights = []

        # Extract all words from titles
        all_words = []
        for title in df['title'].dropna():
            clean = str(title).lower()
            # Remove emojis and special chars
            clean = re.sub(r'[^\w\s#]', ' ', clean)
            words = clean.split()
            all_words.extend([w for w in words if len(w) > 2])

        word_freq = Counter(all_words)

        # Remove common stopwords
        stopwords = {
            'the', 'and', 'for', 'you', 'with', 'this', 'that', 'have', 'are',
            'was', 'were', 'from', 'our', 'your', 'how', 'what', 'when', 'why',
            'which', 'who', 'will', 'can', 'has', 'had', 'but', 'not', 'all',
        }
        filtered_freq = {w: c for w, c in word_freq.items() if w not in stopwords}

        top_keywords = dict(Counter(filtered_freq).most_common(20))

        # Identify potential niche keywords
        niche_keywords = [kw for kw, count in filtered_freq.items() if 3 <= count <= 10]

        if top_keywords:
            top_word = list(top_keywords.keys())[0]
            top_count = list(top_keywords.values())[0]
            insights.append(f"Most used keyword: '{top_word}' ({top_count} videos)")

        metrics = {
            "top_20_keywords": top_keywords,
            "unique_keywords": len(filtered_freq),
            "niche_keywords": niche_keywords[:10],
            "total_words_analyzed": len(all_words),
        }

        return {"metrics": metrics, "insights": insights}

    def _analyze_title_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze title structures and patterns"""
        insights = []

        df = df[df['title'].notna()].copy()

        df['title_length'] = df['title'].str.len()
        df['word_count'] = df['title'].str.split().str.len()
        df['has_number'] = df['title'].str.contains(r'\d', regex=True)
        df['has_question'] = df['title'].str.contains(r'\?', regex=True)
        df['has_exclamation'] = df['title'].str.contains(r'!', regex=True)
        df['has_brackets'] = df['title'].str.contains(r'[\[\(\{]', regex=True)
        df['has_pipe'] = df['title'].str.contains(r'\|', regex=True)
        df['has_emoji'] = df['title'].str.contains(r'[\U0001F300-\U0001F9FF]', regex=True)
        df['starts_with_number'] = df['title'].str.match(r'^\d', na=False)

        # Calculate percentages
        patterns = {
            "avg_title_length": round(df['title_length'].mean(), 1),
            "avg_word_count": round(df['word_count'].mean(), 1),
            "pct_with_numbers": round(df['has_number'].mean() * 100, 1),
            "pct_with_questions": round(df['has_question'].mean() * 100, 1),
            "pct_with_exclamations": round(df['has_exclamation'].mean() * 100, 1),
            "pct_with_brackets": round(df['has_brackets'].mean() * 100, 1),
            "pct_with_emoji": round(df['has_emoji'].mean() * 100, 1),
            "pct_starts_with_number": round(df['starts_with_number'].mean() * 100, 1),
        }

        # Insights based on patterns
        if patterns['avg_title_length'] > 60:
            insights.append("Titles average over 60 chars - may get truncated. Consider shorter titles.")
        elif patterns['avg_title_length'] < 30:
            insights.append("Titles are quite short. You may be missing keyword opportunities.")

        if patterns['pct_with_emoji'] > 50:
            insights.append(f"{patterns['pct_with_emoji']:.0f}% of titles use emojis - this is your signature style")

        if patterns['pct_with_numbers'] > 40:
            insights.append("Numbers are frequently used in titles - good for specificity")

        metrics = {
            "title_patterns": patterns,
        }

        return {"metrics": metrics, "insights": insights}

    def _analyze_hashtags(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze hashtag usage"""
        insights = []

        # Extract hashtags from titles
        all_hashtags = []
        for title in df['title'].dropna():
            hashtags = re.findall(r'#\w+', str(title).lower())
            all_hashtags.extend(hashtags)

        hashtag_freq = Counter(all_hashtags)

        if all_hashtags:
            pct_with_hashtags = len(df[df['title'].str.contains('#', na=False)]) / len(df) * 100
            avg_hashtags = len(all_hashtags) / len(df)

            insights.append(f"{pct_with_hashtags:.0f}% of videos use hashtags in titles")

            if pct_with_hashtags < 30:
                insights.append("Consider using more hashtags for Shorts discoverability")

        metrics = {
            "top_hashtags": dict(hashtag_freq.most_common(10)),
            "total_hashtag_usage": len(all_hashtags),
            "unique_hashtags": len(hashtag_freq),
            "pct_videos_with_hashtags": round(pct_with_hashtags, 1) if all_hashtags else 0,
        }

        return {"metrics": metrics, "insights": insights}

    def _extract_top_performer_keywords(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract keywords from top performing videos"""

        if 'views' not in df.columns:
            return {"metrics": {}}

        # Get top 20% by views
        threshold = df['views'].quantile(0.8)
        top_performers = df[df['views'] >= threshold]

        # Extract keywords
        top_words = []
        for title in top_performers['title'].dropna():
            clean = str(title).lower()
            clean = re.sub(r'[^\w\s]', ' ', clean)
            words = [w for w in clean.split() if len(w) > 2]
            top_words.extend(words)

        stopwords = {
            'the', 'and', 'for', 'you', 'with', 'this', 'that', 'have', 'are',
            'was', 'were', 'from', 'our', 'your', 'how', 'what', 'when', 'why',
        }
        filtered = [w for w in top_words if w not in stopwords]
        top_keywords = dict(Counter(filtered).most_common(15))

        # Extract keywords from bottom performers to compare
        bottom_threshold = df['views'].quantile(0.2)
        bottom_performers = df[df['views'] <= bottom_threshold]

        bottom_words = []
        for title in bottom_performers['title'].dropna():
            clean = str(title).lower()
            clean = re.sub(r'[^\w\s]', ' ', clean)
            words = [w for w in clean.split() if len(w) > 2]
            bottom_words.extend(words)

        bottom_keywords = set(Counter([w for w in bottom_words if w not in stopwords]).most_common(15))
        bottom_keywords = {kw for kw, _ in bottom_keywords}

        # Keywords unique to top performers
        winning_keywords = [kw for kw in top_keywords.keys() if kw not in bottom_keywords]

        metrics = {
            "top_performer_keywords": top_keywords,
            "winning_keywords": winning_keywords[:10],
            "top_performer_count": len(top_performers),
        }

        return {"metrics": metrics}

    def _build_recommendations(self, metrics: Dict, insights: List) -> List[Dict[str, str]]:
        """Build SEO recommendations"""
        recommendations = []

        # Keyword recommendations
        winning_keywords = metrics.get('winning_keywords', [])
        if winning_keywords:
            recommendations.append({
                "priority": "HIGH",
                "action": "Use proven keywords in new titles",
                "details": f"These keywords appear in top performers: {', '.join(winning_keywords[:5])}",
            })

        # Title length
        patterns = metrics.get('title_patterns', {})
        avg_length = patterns.get('avg_title_length', 40)
        if avg_length > 60:
            recommendations.append({
                "priority": "MEDIUM",
                "action": "Shorten titles to under 60 characters",
                "details": "Longer titles get truncated in search and recommendations. Front-load key info.",
            })

        # Hashtag usage
        pct_hashtags = metrics.get('pct_videos_with_hashtags', 0)
        if pct_hashtags < 50:
            recommendations.append({
                "priority": "MEDIUM",
                "action": "Add hashtags to Shorts titles",
                "details": "Use 3-5 relevant hashtags. Include #Shorts and your niche hashtags.",
            })

        # General SEO tips
        recommendations.append({
            "priority": "LOW",
            "action": "Optimize first 48 characters",
            "details": "The first 48 chars show in search. Include your primary keyword there.",
        })

        return recommendations

    def _generate_digest(self, metrics: Dict, insights: List,
                        recommendations: List, severity: str) -> str:
        """Generate human-readable summary"""
        lines = [
            "=" * 60,
            "SEO OPTIMIZATION ANALYSIS",
            "=" * 60,
            "",
        ]

        # Keyword analysis
        top_kw = metrics.get('top_20_keywords', {})
        if top_kw:
            lines.append("🔑 TOP KEYWORDS IN YOUR TITLES")
            for i, (kw, count) in enumerate(list(top_kw.items())[:10]):
                lines.append(f"  {i+1}. '{kw}' ({count}x)")
            lines.append("")

        # Winning keywords
        winning = metrics.get('winning_keywords', [])
        if winning:
            lines.append("🏆 WINNING KEYWORDS (in top performers)")
            lines.append(f"  {', '.join(winning[:8])}")
            lines.append("")

        # Title patterns
        patterns = metrics.get('title_patterns', {})
        if patterns:
            lines.extend([
                "📊 TITLE PATTERNS",
                f"  Avg length: {patterns.get('avg_title_length', 0)} chars",
                f"  With emojis: {patterns.get('pct_with_emoji', 0):.0f}%",
                f"  With numbers: {patterns.get('pct_with_numbers', 0):.0f}%",
                f"  With hashtags: {metrics.get('pct_videos_with_hashtags', 0):.0f}%",
                "",
            ])

        # Top hashtags
        top_tags = metrics.get('top_hashtags', {})
        if top_tags:
            lines.append("# TOP HASHTAGS")
            for tag, count in list(top_tags.items())[:5]:
                lines.append(f"  {tag} ({count}x)")
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
