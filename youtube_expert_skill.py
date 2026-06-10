#!/usr/bin/env python3
"""
YouTube Expert Skill
Complete YouTube channel analysis, optimization, and management

Features:
- Channel analytics and YPP status
- Video performance analysis
- Watch time breakdown (Shorts vs Long-form)
- Re-launch recommendations
- Thumbnail creation
- Title optimization
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class YouTubeExpertSkill:
    """
    Complete YouTube Expert Skill for AI Agents

    Usage:
        skill = YouTubeExpertSkill()
        status = skill.check_ypp_status()
        recommendations = skill.get_relaunch_recommendations()
    """

    def __init__(self):
        self.data_dir = Path(__file__).parent
        self.has_api = self._check_api_setup()

    def _check_api_setup(self) -> bool:
        """Check if YouTube API is configured"""
        env_file = self.data_dir / '.env'
        return env_file.exists()

    # ========== YPP & MONETIZATION ==========

    def check_ypp_status(self) -> Dict[str, Any]:
        """
        Check YouTube Partner Program eligibility

        Returns:
            dict with subscriber count, watch hours, and eligibility status
        """
        if self.has_api:
            try:
                from youtube_api import YouTubeAnalytics
                analytics = YouTubeAnalytics()
                return analytics.get_ypp_status()
            except Exception as e:
                return {'error': str(e), 'note': 'API not configured'}

        # Fallback to CSV data
        return self._check_ypp_from_csv()

    def _check_ypp_from_csv(self) -> Dict[str, Any]:
        """Check YPP status from exported CSV data"""
        import csv

        csv_file = self.data_dir / 'Table data.csv'
        if not csv_file.exists():
            return {'error': 'No data file found'}

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Get totals from first row
        totals = rows[0] if rows else {}

        total_views = int(totals.get('Visningar', 0))
        total_hours = float(totals.get('Visningstid (timmar)', 0))
        subscribers = int(totals.get('Prenumeranter', 0))

        return {
            'subscribers': subscribers,
            'subscribers_required': 1000,
            'subscribers_met': subscribers >= 1000,

            'total_watch_hours': total_hours,
            'note': 'This is TOTAL hours, not 365-day eligible hours',

            'ypp_requirements': {
                '1000_subscribers': subscribers >= 1000,
                '4000_hours_365d': 'Check YouTube Studio for accurate 365-day count'
            }
        }

    def explain_eligible_hours(self) -> str:
        """
        Explain why eligible hours differ from total hours

        Returns:
            Detailed explanation string
        """
        return """
## Why Eligible Hours ≠ Total Hours

YouTube Partner Program only counts watch hours from:
- **Last 365 days** (rolling window - hours "expire" daily)
- **Long-form videos only** (over 60 seconds)
- **Public videos** (not private/unlisted)
- **Valid traffic** (bot/spam views filtered out)

### What DOESN'T count:
- Shorts (under 60 seconds) → separate Shorts monetization
- Hours from videos older than 12 months
- Deleted videos
- Invalid/suspicious traffic

### To check your REAL eligible hours:
1. YouTube Studio → Analytics
2. Click "See More"
3. Filter: "Visningstid"
4. Set date range: Last 365 days
5. Filter by "Long-form" only

This number is your YPP-eligible watch hours.
"""

    # ========== VIDEO ANALYSIS ==========

    def get_top_videos(self, metric: str = 'watch_hours', limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top performing videos

        Args:
            metric: 'watch_hours', 'views', or 'ctr'
            limit: Number of videos to return
        """
        import csv

        csv_file = self.data_dir / 'Table data.csv'
        if not csv_file.exists():
            return []

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)[1:]  # Skip totals row

        videos = []
        for row in rows:
            try:
                video = {
                    'video_id': row.get('Innehåll', ''),
                    'title': row.get('Videotitel', ''),
                    'views': int(row.get('Visningar', 0)),
                    'watch_hours': float(row.get('Visningstid (timmar)', 0)),
                    'ctr': float(row.get('Klickfrekvens för exponeringar (%)', 0)),
                    'duration_seconds': int(row.get('Längd', 0)),
                    'impressions': int(row.get('Exponeringar', 0))
                }
                videos.append(video)
            except:
                pass

        # Sort by metric
        if metric == 'watch_hours':
            videos.sort(key=lambda x: x['watch_hours'], reverse=True)
        elif metric == 'views':
            videos.sort(key=lambda x: x['views'], reverse=True)
        elif metric == 'ctr':
            videos.sort(key=lambda x: x['ctr'], reverse=True)

        return videos[:limit]

    def get_long_form_videos(self) -> List[Dict[str, Any]]:
        """Get only long-form videos (over 60 seconds)"""
        all_videos = self.get_top_videos(limit=500)
        return [v for v in all_videos if v['duration_seconds'] > 60]

    def get_shorts(self) -> List[Dict[str, Any]]:
        """Get only Shorts (60 seconds or less)"""
        all_videos = self.get_top_videos(limit=500)
        return [v for v in all_videos if v['duration_seconds'] <= 60]

    # ========== RECOMMENDATIONS ==========

    def get_relaunch_recommendations(self) -> Dict[str, Any]:
        """
        Get recommendations for re-launching top videos

        Returns:
            dict with videos to re-launch and strategies
        """
        top_videos = self.get_top_videos(metric='watch_hours', limit=10)
        long_form = [v for v in top_videos if v['duration_seconds'] > 60]

        recommendations = []
        for video in long_form[:5]:
            rec = {
                'video': video,
                'strategies': []
            }

            # Low CTR = thumbnail/title issue
            if video['ctr'] < 3.0:
                rec['strategies'].append({
                    'action': 'NEW_THUMBNAIL',
                    'reason': f"CTR is {video['ctr']:.1f}% (target: 4%+)",
                    'impact': 'High'
                })

            # High impressions but low CTR
            if video['impressions'] > 5000 and video['ctr'] < 2.5:
                rec['strategies'].append({
                    'action': 'A/B_TEST_THUMBNAIL',
                    'reason': 'High impressions but low conversion',
                    'impact': 'High'
                })

            # Create Shorts from long-form
            if video['duration_seconds'] > 300:  # Over 5 minutes
                rec['strategies'].append({
                    'action': 'CREATE_SHORTS',
                    'reason': 'Long video can be clipped into multiple Shorts',
                    'impact': 'Medium'
                })

            # Community post
            rec['strategies'].append({
                'action': 'COMMUNITY_POST',
                'reason': 'Re-share with existing subscribers',
                'impact': 'Low-Medium'
            })

            recommendations.append(rec)

        return {
            'videos_to_relaunch': recommendations,
            'general_strategies': [
                'Update end screens to point to these top videos',
                'Add cards in new videos linking to these',
                'Create playlists grouping related content',
                'Pin comment with CTA on popular Shorts'
            ]
        }

    def get_ctr_improvement_tips(self, video_id: str) -> Dict[str, Any]:
        """
        Get specific CTR improvement tips for a video

        Args:
            video_id: YouTube video ID
        """
        # Find the video
        all_videos = self.get_top_videos(limit=500)
        video = next((v for v in all_videos if v['video_id'] == video_id), None)

        if not video:
            return {'error': 'Video not found'}

        tips = {
            'video': video,
            'current_ctr': video['ctr'],
            'target_ctr': 4.0,
            'thumbnail_tips': [],
            'title_tips': []
        }

        # Thumbnail tips based on research
        tips['thumbnail_tips'] = [
            'Use close-up faces with clear emotions',
            'Add bold, readable text (3-5 words max)',
            'Use contrasting colors (complementary)',
            'Include curiosity elements',
            'Test multiple versions with A/B testing'
        ]

        # Title tips
        tips['title_tips'] = [
            'Start with hook word (SECRET, HIDDEN, BEST)',
            'Include numbers if relevant',
            'Create curiosity gap',
            'Keep under 60 characters',
            'Front-load important words'
        ]

        return tips

    # ========== THUMBNAIL CREATION ==========

    def create_thumbnail(
        self,
        episode: int,
        title: str,
        subject_photo: str,
        background: str = None
    ) -> str:
        """
        Create a thumbnail in the approved style

        Args:
            episode: Episode number
            title: Title text for thumbnail
            subject_photo: Photo filename in SOURCES folder
            background: Background image path (optional)

        Returns:
            Path to created thumbnail
        """
        from create_thumbnail_master import create_thumbnail

        return str(create_thumbnail(
            episode=episode,
            title=title,
            subject_photo=subject_photo,
            background=background
        ))


def main():
    """Test the skill"""
    skill = YouTubeExpertSkill()

    print("="*60)
    print("YOUTUBE EXPERT SKILL TEST")
    print("="*60)

    # Check YPP status
    print("\n📊 YPP Status:")
    status = skill.check_ypp_status()
    for key, value in status.items():
        print(f"   {key}: {value}")

    # Get top videos
    print("\n🎬 Top 5 Videos by Watch Hours:")
    top = skill.get_top_videos(limit=5)
    for i, v in enumerate(top, 1):
        print(f"   {i}. {v['title'][:40]}... ({v['watch_hours']:.0f} hrs)")

    # Get recommendations
    print("\n💡 Re-launch Recommendations:")
    recs = skill.get_relaunch_recommendations()
    for rec in recs['videos_to_relaunch'][:3]:
        print(f"   • {rec['video']['title'][:35]}...")
        for s in rec['strategies'][:2]:
            print(f"     → {s['action']}: {s['reason']}")


if __name__ == "__main__":
    main()
