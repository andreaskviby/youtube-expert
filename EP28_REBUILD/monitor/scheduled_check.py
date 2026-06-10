#!/usr/bin/env python3
"""
Scheduled EP59 Monitor - Runs every 2 hours
Checks stats and logs results
"""

import pickle
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from googleapiclient.discovery import build

VIDEO_ID = "pnmTJ0uXvSw"
SHORT_ID = "KDwLINFLH3g"
LOG_FILE = Path("EP28_REBUILD/monitor/scheduled_log.json")
CHECK_INTERVAL = 2 * 60 * 60  # 2 hours

def load_credentials():
    with open('youtube_api/token.pickle', 'rb') as token:
        return pickle.load(token)

def get_stats(youtube, video_id):
    response = youtube.videos().list(
        part="statistics",
        id=video_id
    ).execute()
    
    if response['items']:
        stats = response['items'][0]['statistics']
        return {
            'views': int(stats.get('viewCount', 0)),
            'likes': int(stats.get('likeCount', 0)),
            'comments': int(stats.get('commentCount', 0))
        }
    return None

def get_analytics(credentials):
    try:
        youtube_analytics = build('youtubeAnalytics', 'v2', credentials=credentials)
        today = datetime.now().strftime('%Y-%m-%d')
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        response = youtube_analytics.reports().query(
            ids='channel==MINE',
            startDate=week_ago,
            endDate=today,
            metrics='views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage',
            dimensions='video',
            filters=f'video=={VIDEO_ID}'
        ).execute()
        
        if response.get('rows'):
            row = response['rows'][0]
            return {
                'watch_minutes': row[2],
                'avg_view_duration': row[3],
                'retention_pct': row[4]
            }
    except:
        pass
    return None

def load_log():
    if LOG_FILE.exists():
        with open(LOG_FILE) as f:
            return json.load(f)
    return {'checks': [], 'retention_available': False}

def save_log(log):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'w') as f:
        json.dump(log, f, indent=2)

def check_once():
    credentials = load_credentials()
    youtube = build('youtube', 'v3', credentials=credentials)
    
    now = datetime.now()
    log = load_log()
    
    # Get stats
    main_stats = get_stats(youtube, VIDEO_ID)
    short_stats = get_stats(youtube, SHORT_ID)
    analytics = get_analytics(credentials)
    
    check = {
        'timestamp': now.isoformat(),
        'main': main_stats,
        'short': short_stats,
        'analytics': analytics
    }
    
    log['checks'].append(check)
    
    # Check if retention data is now available
    if analytics and not log.get('retention_available'):
        log['retention_available'] = True
        log['retention_available_at'] = now.isoformat()
    
    save_log(log)
    
    # Print report
    print("=" * 60)
    print(f"EP59 SCHEDULED CHECK - {now.strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    if main_stats:
        print(f"\n📹 MAIN VIDEO:")
        print(f"   Views: {main_stats['views']:,}")
        print(f"   Likes: {main_stats['likes']:,}")
        print(f"   Comments: {main_stats['comments']:,}")
    
    if short_stats:
        print(f"\n📹 SHORT:")
        print(f"   Views: {short_stats['views']:,}")
        print(f"   Likes: {short_stats['likes']:,}")
    
    if analytics:
        print(f"\n📊 RETENTION DATA AVAILABLE!")
        print(f"   Watch Time: {analytics['watch_minutes']:.1f} min")
        print(f"   Avg Duration: {analytics['avg_view_duration']:.0f} sec")
        print(f"   Retention: {analytics['retention_pct']:.1f}%")
        print(f"\n🔔 REMINDER: Retention data is ready for analysis!")
    else:
        print(f"\n📊 Retention: Not yet available")
    
    # Calculate velocity if we have history
    if len(log['checks']) >= 2:
        prev = log['checks'][-2]
        hours_diff = (now - datetime.fromisoformat(prev['timestamp'])).total_seconds() / 3600
        views_diff = main_stats['views'] - prev['main']['views']
        velocity = views_diff / max(hours_diff, 0.1)
        print(f"\n📈 Recent velocity: {velocity:.1f} views/hour")
    
    print("=" * 60)
    
    return analytics is not None

def run_scheduled():
    print("Starting EP59 scheduled monitor...")
    print(f"Checking every {CHECK_INTERVAL // 3600} hours")
    print("Press Ctrl+C to stop\n")
    
    while True:
        retention_ready = check_once()
        
        if retention_ready:
            print("\n" + "!" * 60)
            print("🔔 RETENTION DATA IS NOW AVAILABLE!")
            print("   Run full analysis when ready")
            print("!" * 60 + "\n")
        
        print(f"\nNext check in {CHECK_INTERVAL // 3600} hours...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        check_once()
    else:
        run_scheduled()
