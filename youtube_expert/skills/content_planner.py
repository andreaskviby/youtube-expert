"""
Content Planner Skill - Content calendar and strategy recommendations

Analyzes historical performance to recommend content topics, formats,
and publishing strategy.
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


class ContentPlannerSkill(BaseSkill):
    """
    Content calendar and strategy planning

    Analyzes what content works best and recommends topics,
    formats, and publishing cadence for future content.
    """

    name = "content_planner"
    description = "Content calendar and topic recommendations"

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

        # === TOP PERFORMING CONTENT ANALYSIS ===
        top_content = self._analyze_top_content(df)
        metrics.update(top_content['metrics'])
        insights.extend(top_content['insights'])

        # === TOPIC CLUSTERS ===
        topics = self._identify_topic_clusters(df)
        metrics.update(topics['metrics'])
        insights.extend(topics['insights'])

        # === FORMAT ANALYSIS ===
        formats = self._analyze_formats(df)
        metrics.update(formats['metrics'])

        # === CONTENT MIX RECOMMENDATIONS ===
        content_mix = self._recommend_content_mix(df, metrics)
        metrics.update(content_mix['metrics'])

        # === CONTENT CALENDAR ===
        calendar = self._generate_content_calendar(metrics)
        metrics.update(calendar['metrics'])

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

    def _analyze_top_content(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze what makes top content successful"""
        insights = []

        if 'views' not in df.columns:
            return {"metrics": {}, "insights": []}

        # Get top 10% performers
        top_threshold = df['views'].quantile(0.9)
        top_performers = df[df['views'] >= top_threshold]

        # Analyze characteristics
        characteristics = {}

        # Content type distribution in top performers
        if 'content_type' in top_performers.columns:
            type_dist = top_performers['content_type'].value_counts()
            characteristics['top_content_types'] = type_dist.to_dict()

            dominant_type = type_dist.idxmax()
            insights.append(f"Top performers are mostly {dominant_type} content ({type_dist[dominant_type]}/{len(top_performers)})")

        # Duration analysis
        if 'duration_seconds' in top_performers.columns:
            avg_duration = top_performers['duration_seconds'].mean()
            characteristics['avg_top_duration_seconds'] = round(avg_duration, 0)

        # Title patterns in top performers
        if 'title' in top_performers.columns:
            titles = top_performers['title'].tolist()

            # Check for common elements
            emoji_count = sum(1 for t in titles if re.search(r'[\U0001F300-\U0001F9FF]', str(t)))
            caps_count = sum(1 for t in titles if re.search(r'[A-Z]{3,}', str(t)))
            question_count = sum(1 for t in titles if '?' in str(t))

            characteristics['top_title_patterns'] = {
                'pct_with_emoji': round(emoji_count / len(titles) * 100, 0),
                'pct_with_caps': round(caps_count / len(titles) * 100, 0),
                'pct_with_question': round(question_count / len(titles) * 100, 0),
            }

        # Top performer list
        top_list = top_performers.nlargest(5, 'views')[['video_id', 'title', 'views', 'content_type']].to_dict('records')

        metrics = {
            "top_performer_characteristics": characteristics,
            "top_5_videos": top_list,
            "top_threshold_views": int(top_threshold),
        }

        return {"metrics": metrics, "insights": insights}

    def _identify_topic_clusters(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identify topic clusters from title analysis"""
        insights = []

        if 'title' not in df.columns:
            return {"metrics": {}, "insights": []}

        # Extract keywords
        all_words = []
        for title in df['title'].dropna():
            clean = str(title).lower()
            clean = re.sub(r'[^\w\s#]', ' ', clean)
            words = [w for w in clean.split() if len(w) > 3]
            all_words.extend(words)

        # Remove common words
        stopwords = {
            'the', 'and', 'for', 'you', 'with', 'this', 'that', 'have', 'from',
            'your', 'how', 'what', 'when', 'shorts', 'video', 'vlog', 'part',
        }
        filtered = [w for w in all_words if w not in stopwords]

        # Get top keywords/topics
        word_freq = Counter(filtered)
        top_topics = dict(word_freq.most_common(15))

        # Identify topic performance
        topic_performance = {}
        if 'views' in df.columns:
            for topic in list(top_topics.keys())[:10]:
                topic_videos = df[df['title'].str.lower().str.contains(topic, na=False)]
                if len(topic_videos) >= 2:
                    topic_performance[topic] = {
                        'video_count': len(topic_videos),
                        'avg_views': round(topic_videos['views'].mean(), 0),
                        'total_views': int(topic_videos['views'].sum()),
                    }

        # Find best performing topics
        if topic_performance:
            best_topic = max(topic_performance.items(), key=lambda x: x[1]['avg_views'])
            insights.append(f"Best performing topic: '{best_topic[0]}' ({best_topic[1]['avg_views']:,.0f} avg views)")

        metrics = {
            "top_keywords": top_topics,
            "topic_performance": topic_performance,
        }

        return {"metrics": metrics, "insights": insights}

    def _analyze_formats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze content format performance"""

        if 'content_type' not in df.columns or 'views' not in df.columns:
            return {"metrics": {}}

        format_stats = df.groupby('content_type').agg({
            'views': ['mean', 'sum', 'count'],
            'watch_hours': 'sum' if 'watch_hours' in df.columns else 'count',
        }).round(0)

        format_stats.columns = ['avg_views', 'total_views', 'count', 'total_hours']

        # Duration buckets for long-form
        if 'duration_seconds' in df.columns:
            longform = df[df['content_type'] == 'LONGFORM'].copy()
            if len(longform) > 5:
                longform['duration_bucket'] = pd.cut(
                    longform['duration_seconds'] / 60,
                    bins=[0, 10, 20, 30, float('inf')],
                    labels=['<10min', '10-20min', '20-30min', '30min+']
                )
                duration_perf = longform.groupby('duration_bucket')['views'].mean().round(0).to_dict()
            else:
                duration_perf = {}
        else:
            duration_perf = {}

        metrics = {
            "format_performance": format_stats.to_dict(),
            "duration_performance": duration_perf,
        }

        return {"metrics": metrics}

    def _recommend_content_mix(self, df: pd.DataFrame, current_metrics: Dict) -> Dict[str, Any]:
        """Recommend optimal content mix"""

        topic_perf = current_metrics.get('topic_performance', {})
        format_perf = current_metrics.get('format_performance', {})

        # Recommend top 5 topics to focus on
        recommended_topics = []
        if topic_perf:
            sorted_topics = sorted(topic_perf.items(), key=lambda x: x[1]['avg_views'], reverse=True)
            recommended_topics = [
                {"topic": t[0], "avg_views": t[1]['avg_views'], "frequency": t[1]['video_count']}
                for t in sorted_topics[:5]
            ]

        # Recommend content ratio
        if 'content_type' in df.columns:
            current_shorts = len(df[df['content_type'] == 'SHORT'])
            current_longform = len(df[df['content_type'] == 'LONGFORM'])
            current_ratio = current_shorts / (current_longform or 1)

            # Optimal ratio for hybrid growth: 2-3 Shorts per 1 long-form
            if current_ratio > 5:
                recommended_ratio = "Increase long-form: aim for 3:1 Shorts to long-form"
            elif current_ratio < 1:
                recommended_ratio = "Increase Shorts: aim for 2:1 Shorts to long-form"
            else:
                recommended_ratio = "Current mix is balanced"
        else:
            recommended_ratio = "Unable to determine"

        metrics = {
            "recommended_topics": recommended_topics,
            "recommended_content_ratio": recommended_ratio,
        }

        return {"metrics": metrics}

    def _generate_content_calendar(self, current_metrics: Dict) -> Dict[str, Any]:
        """Generate a weekly content calendar template"""

        recommended_topics = current_metrics.get('recommended_topics', [])
        top_topics = [t['topic'] for t in recommended_topics[:3]] if recommended_topics else ['topic1', 'topic2', 'topic3']

        # Weekly content plan
        weekly_plan = {
            "monday": {
                "content_type": "SHORT",
                "focus": "Quick tip or teaser",
                "topic_suggestion": top_topics[0] if top_topics else "trending topic",
            },
            "tuesday": {
                "content_type": "SHORT",
                "focus": "Behind the scenes",
                "topic_suggestion": "lifestyle/personal",
            },
            "wednesday": {
                "content_type": "LONGFORM",
                "focus": "Main content piece",
                "topic_suggestion": top_topics[0] if top_topics else "flagship content",
                "target_duration": "10-15 minutes",
            },
            "thursday": {
                "content_type": "SHORT",
                "focus": "Clip from Wednesday's video",
                "topic_suggestion": "repurpose",
            },
            "friday": {
                "content_type": "SHORT",
                "focus": "Fun/engaging content",
                "topic_suggestion": top_topics[1] if len(top_topics) > 1 else "entertainment",
            },
            "saturday": {
                "content_type": "OPTIONAL",
                "focus": "Bonus content or rest",
                "topic_suggestion": top_topics[2] if len(top_topics) > 2 else "community engagement",
            },
            "sunday": {
                "content_type": "LONGFORM",
                "focus": "Weekend deep-dive",
                "topic_suggestion": top_topics[1] if len(top_topics) > 1 else "exploration",
                "target_duration": "15-20 minutes",
            },
        }

        metrics = {
            "weekly_content_plan": weekly_plan,
            "recommended_uploads_per_week": {
                "shorts": 4,
                "longform": 2,
            },
        }

        return {"metrics": metrics}

    def _build_recommendations(self, metrics: Dict, insights: List) -> List[Dict[str, str]]:
        """Build content planning recommendations"""
        recommendations = []

        # Topic recommendations
        top_topics = metrics.get('recommended_topics', [])
        if top_topics:
            topic_names = [t['topic'] for t in top_topics[:3]]
            recommendations.append({
                "priority": "HIGH",
                "action": f"Focus on proven topics: {', '.join(topic_names)}",
                "details": "These topics have the highest avg views. Create more content around them.",
            })

        # Format recommendations
        characteristics = metrics.get('top_performer_characteristics', {})
        title_patterns = characteristics.get('top_title_patterns', {})

        if title_patterns.get('pct_with_emoji', 0) > 60:
            recommendations.append({
                "priority": "MEDIUM",
                "action": "Use emojis consistently in titles",
                "details": f"{title_patterns['pct_with_emoji']:.0f}% of top performers use emojis.",
            })

        # Content mix
        ratio_rec = metrics.get('recommended_content_ratio', '')
        if 'Increase' in ratio_rec:
            recommendations.append({
                "priority": "MEDIUM",
                "action": ratio_rec,
                "details": "Rebalancing your content mix can improve reach and monetization.",
            })

        # Calendar recommendation
        recommendations.append({
            "priority": "MEDIUM",
            "action": "Follow the weekly content calendar",
            "details": "Consistency is key. Plan content in advance and batch record when possible.",
        })

        return recommendations

    def _generate_digest(self, metrics: Dict, insights: List,
                        recommendations: List, severity: str) -> str:
        """Generate human-readable summary"""
        lines = [
            "=" * 60,
            "CONTENT PLANNER REPORT",
            "=" * 60,
            "",
        ]

        # Top performing content
        top_5 = metrics.get('top_5_videos', [])
        if top_5:
            lines.append("🏆 TOP PERFORMING CONTENT")
            for v in top_5[:3]:
                lines.append(f"  {v.get('views', 0):,} views - {v.get('title', '')[:40]}...")
            lines.append("")

        # Recommended topics
        topics = metrics.get('recommended_topics', [])
        if topics:
            lines.append("🎯 RECOMMENDED TOPICS (by performance)")
            for t in topics[:5]:
                lines.append(f"  '{t['topic']}' - {t['avg_views']:,.0f} avg views ({t['frequency']} videos)")
            lines.append("")

        # Content calendar
        plan = metrics.get('weekly_content_plan', {})
        if plan:
            lines.append("📅 WEEKLY CONTENT CALENDAR")
            for day, content in list(plan.items())[:5]:
                lines.append(f"  {day.capitalize()}: {content['content_type']} - {content['focus']}")
            lines.append("")

        # Upload targets
        targets = metrics.get('recommended_uploads_per_week', {})
        if targets:
            lines.extend([
                "🎬 WEEKLY UPLOAD TARGETS",
                f"  Shorts: {targets.get('shorts', 0)}/week",
                f"  Long-form: {targets.get('longform', 0)}/week",
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
