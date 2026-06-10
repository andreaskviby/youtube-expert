#!/usr/bin/env python3
"""
EP59 Performance Monitor
Tracks video performance and alerts on key metrics
"""

import pickle
import json
from datetime import datetime, timedelta
from pathlib import Path
from googleapiclient.discovery import build

VIDEO_ID = "pnmTJ0uXvSw"
VIDEO_DURATION_SEC = 188  # 3:08
TARGET_RETENTION = 0.25  # 25%
LOG_FILE = Path("EP28_REBUILD/monitor/performance_log.json")

def load_credentials():
    with open('youtube_api/token.pickle', 'rb') as token:
        return pickle.load(token)

def get_video_stats(youtube):
    response = youtube.videos().list(
        part="snippet,statistics",
        id=VIDEO_ID
    ).execute()

    if not response['items']:
        return None

    video = response['items'][0]
    stats = video['statistics']
    snippet = video['snippet']

    published = datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00'))
    age_hours = (datetime.now(published.tzinfo) - published).total_seconds() / 3600

    return {
        'timestamp': datetime.now().isoformat(),
        'age_hours': round(age_hours, 1),
        'views': int(stats.get('viewCount', 0)),
        'likes': int(stats.get('likeCount', 0)),
        'comments': int(stats.get('commentCount', 0)),
    }

def get_analytics(youtube_analytics):
    today = datetime.now().strftime('%Y-%m-%d')
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

    try:
        response = youtube_analytics.reports().query(
            ids='channel==MINE',
            startDate=week_ago,
            endDate=today,
            metrics='views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained',
            dimensions='video',
            filters=f'video=={VIDEO_ID}'
        ).execute()

        if response.get('rows'):
            row = response['rows'][0]
            return {
                'watch_minutes': row[2],
                'avg_view_duration': row[3],
                'avg_view_percentage': row[4],
                'subscribers_gained': row[5]
            }
    except:
        pass

    return None

def load_history():
    if LOG_FILE.exists():
        with open(LOG_FILE) as f:
            return json.load(f)
    return []

def save_history(history):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def analyze_performance(current, history):
    insights = []

    # Calculate velocity
    views_per_hour = current['views'] / max(current['age_hours'], 1)

    # Velocity trend
    if len(history) >= 2:
        prev = history[-1]
        hours_diff = current['age_hours'] - prev['age_hours']
        views_diff = current['views'] - prev['views']
        recent_velocity = views_diff / max(hours_diff, 0.1)

        if recent_velocity > views_per_hour * 1.5:
            insights.append("🚀 ACCELERATING - Views picking up speed!")
        elif recent_velocity < views_per_hour * 0.5:
            insights.append("📉 SLOWING - Views decreasing")

    # Like rate
    if current['views'] > 0:
        like_rate = (current['likes'] / current['views']) * 100
        if like_rate > 10:
            insights.append(f"👍 HIGH ENGAGEMENT - {like_rate:.1f}% like rate")
        elif like_rate < 3:
            insights.append(f"⚠️ LOW ENGAGEMENT - {like_rate:.1f}% like rate")

    # Milestones
    milestones = [100, 500, 1000, 5000, 10000]
    for m in milestones:
        if current['views'] >= m and (not history or history[-1]['views'] < m):
            insights.append(f"🎉 MILESTONE: {m:,} views reached!")

    return insights, views_per_hour

def main():
    credentials = load_credentials()
    youtube = build('youtube', 'v3', credentials=credentials)

    try:
        youtube_analytics = build('youtubeAnalytics', 'v2', credentials=credentials)
    except:
        youtube_analytics = None

    # Get current stats
    current = get_video_stats(youtube)
    if not current:
        print("Error: Could not fetch video stats")
        return

    # Get analytics if available
    analytics = get_analytics(youtube_analytics) if youtube_analytics else None

    # Load history and analyze
    history = load_history()
    insights, velocity = analyze_performance(current, history)

    # Save to history
    history.append(current)
    save_history(history)

    # Print report
    print("=" * 60)
    print(f"EP59 MONITOR - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    print(f"\n⏱️  Age: {current['age_hours']:.1f} hours")
    print(f"👁️  Views: {current['views']:,}")
    print(f"👍 Likes: {current['likes']:,}")
    print(f"💬 Comments: {current['comments']:,}")
    print(f"📈 Velocity: {velocity:.2f} views/hour")

    if analytics:
        print(f"\n📊 RETENTION DATA:")
        print(f"   Avg View: {analytics['avg_view_duration']:.0f} sec")
        print(f"   Retention: {analytics['avg_view_percentage']:.1f}%")
        print(f"   Watch Time: {analytics['watch_minutes']:.1f} min")
        print(f"   Subs Gained: {analytics['subscribers_gained']}")
    else:
        print(f"\n📊 Retention data: Pending (available after 24-48h)")

    if insights:
        print(f"\n💡 INSIGHTS:")
        for insight in insights:
            print(f"   {insight}")

    # Projections
    print(f"\n🔮 PROJECTIONS (at current velocity):")
    for hours in [24, 48, 168]:
        projected = int(velocity * hours)
        print(f"   {hours}h: ~{projected:,} views")

    print("=" * 60)

if __name__ == "__main__":
    main()
