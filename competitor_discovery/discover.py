#!/usr/bin/env python3
"""
YouTube Competitor Discovery Tool
Finds channels in your niche that you're not subscribed to
Sends daily digest via email or Telegram
"""

import os
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Set

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Configuration
SEARCH_QUERIES = [
    "life in Sicily",
    "moving to Sicily",
    "buy house Sicily",
    "living in Sicily expat",
    "Sicily renovation",
    "house hunting Sicily Italy",
    "relocating to Sicily",
    "Sicily property",
    "expat Sicily",
    "retire in Sicily",
    "Sicily vlog",
    "Sicily home tour",
]

MAX_RESULTS_PER_QUERY = 10
DATA_DIR = Path(__file__).parent / "data"
SEEN_CHANNELS_FILE = DATA_DIR / "seen_channels.json"
API_DIR = Path(__file__).parent.parent / "youtube_api"


class CompetitorDiscovery:
    def __init__(self):
        DATA_DIR.mkdir(exist_ok=True)
        self.credentials = self._load_credentials()
        self.youtube = build('youtube', 'v3', credentials=self.credentials)
        self.my_channel_id = self._get_my_channel_id()
        self.subscriptions = self._get_my_subscriptions()
        self.seen_channels = self._load_seen_channels()

    def _load_credentials(self) -> Credentials:
        """Load OAuth credentials"""
        token_file = API_DIR / "token.pickle"
        if not token_file.exists():
            raise FileNotFoundError("No YouTube credentials found. Run youtube_api auth first.")

        with open(token_file, 'rb') as f:
            return pickle.load(f)

    def _get_my_channel_id(self) -> str:
        """Get authenticated user's channel ID"""
        response = self.youtube.channels().list(part='id', mine=True).execute()
        return response['items'][0]['id']

    def _get_my_subscriptions(self) -> Set[str]:
        """Get all channels I'm subscribed to"""
        subscriptions = set()
        page_token = None

        while True:
            response = self.youtube.subscriptions().list(
                part='snippet',
                mine=True,
                maxResults=50,
                pageToken=page_token
            ).execute()

            for item in response.get('items', []):
                channel_id = item['snippet']['resourceId']['channelId']
                subscriptions.add(channel_id)

            page_token = response.get('nextPageToken')
            if not page_token:
                break

        return subscriptions

    def _load_seen_channels(self) -> Dict:
        """Load previously seen channels"""
        if SEEN_CHANNELS_FILE.exists():
            with open(SEEN_CHANNELS_FILE) as f:
                return json.load(f)
        return {}

    def _save_seen_channels(self):
        """Save seen channels"""
        with open(SEEN_CHANNELS_FILE, 'w') as f:
            json.dump(self.seen_channels, f, indent=2)

    def search_competitors(self) -> List[Dict]:
        """Search for competitor channels"""
        discovered = {}

        for query in SEARCH_QUERIES:
            print(f"Searching: {query}")

            try:
                response = self.youtube.search().list(
                    part='snippet',
                    q=query,
                    type='video',
                    maxResults=MAX_RESULTS_PER_QUERY,
                    order='date',  # Recent videos
                    publishedAfter=(datetime.utcnow() - timedelta(days=30)).isoformat() + 'Z'
                ).execute()

                for item in response.get('items', []):
                    channel_id = item['snippet']['channelId']

                    # Skip if it's my channel
                    if channel_id == self.my_channel_id:
                        continue

                    # Skip if already subscribed
                    if channel_id in self.subscriptions:
                        continue

                    # Skip if already in results
                    if channel_id in discovered:
                        continue

                    discovered[channel_id] = {
                        'channel_id': channel_id,
                        'channel_title': item['snippet']['channelTitle'],
                        'video_id': item['id']['videoId'],
                        'video_title': item['snippet']['title'],
                        'video_description': item['snippet']['description'][:200],
                        'published': item['snippet']['publishedAt'],
                        'found_via_query': query,
                        'thumbnail': item['snippet']['thumbnails'].get('high', {}).get('url', '')
                    }

            except Exception as e:
                print(f"  Error: {e}")

        return list(discovered.values())

    def get_channel_stats(self, channel_ids: List[str]) -> Dict[str, Dict]:
        """Get subscriber counts for channels"""
        stats = {}

        for i in range(0, len(channel_ids), 50):
            batch = channel_ids[i:i+50]
            response = self.youtube.channels().list(
                part='statistics,snippet',
                id=','.join(batch)
            ).execute()

            for item in response.get('items', []):
                stats[item['id']] = {
                    'subscribers': int(item['statistics'].get('subscriberCount', 0)),
                    'total_views': int(item['statistics'].get('viewCount', 0)),
                    'video_count': int(item['statistics'].get('videoCount', 0)),
                    'description': item['snippet'].get('description', '')[:200]
                }

        return stats

    def filter_new_channels(self, channels: List[Dict]) -> List[Dict]:
        """Filter to only channels we haven't seen before"""
        new_channels = []

        for channel in channels:
            channel_id = channel['channel_id']

            if channel_id not in self.seen_channels:
                new_channels.append(channel)
                self.seen_channels[channel_id] = {
                    'first_seen': datetime.now().isoformat(),
                    'channel_title': channel['channel_title']
                }

        self._save_seen_channels()
        return new_channels

    def generate_report(self, include_seen: bool = False) -> str:
        """Generate discovery report"""
        print("\n" + "="*60)
        print("COMPETITOR DISCOVERY REPORT")
        print("="*60)

        # Search for competitors
        all_channels = self.search_competitors()
        print(f"\nFound {len(all_channels)} channels (not subscribed)")

        # Filter to new only
        if include_seen:
            channels = all_channels
        else:
            channels = self.filter_new_channels(all_channels)
            print(f"New channels (not seen before): {len(channels)}")

        if not channels:
            return "No new channels found today."

        # Get stats
        channel_ids = [c['channel_id'] for c in channels]
        stats = self.get_channel_stats(channel_ids)

        # Enrich with stats
        for channel in channels:
            cid = channel['channel_id']
            if cid in stats:
                channel.update(stats[cid])

        # Sort by subscribers
        channels.sort(key=lambda x: x.get('subscribers', 0), reverse=True)

        # Generate report
        report = []
        report.append(f"🔍 SICILY NICHE DISCOVERY - {datetime.now().strftime('%Y-%m-%d')}")
        report.append(f"Found {len(channels)} new channels to check out:\n")
        report.append("="*50)

        for i, ch in enumerate(channels[:20], 1):  # Top 20
            subs = ch.get('subscribers', 0)
            if subs >= 1000000:
                sub_str = f"{subs/1000000:.1f}M"
            elif subs >= 1000:
                sub_str = f"{subs/1000:.0f}K"
            else:
                sub_str = str(subs)

            report.append(f"\n{i}. {ch['channel_title']} ({sub_str} subs)")
            report.append(f"   📺 Latest: {ch['video_title'][:60]}")
            report.append(f"   🔗 https://youtube.com/watch?v={ch['video_id']}")
            report.append(f"   📢 Channel: https://youtube.com/channel/{ch['channel_id']}")
            report.append(f"   🔎 Found via: \"{ch['found_via_query']}\"")

        report.append("\n" + "="*50)
        report.append(f"Your subscriptions: {len(self.subscriptions)} channels")
        report.append(f"Channels seen before: {len(self.seen_channels)}")

        return "\n".join(report)


def main():
    """Run discovery and print report"""
    discovery = CompetitorDiscovery()
    report = discovery.generate_report(include_seen=False)
    print(report)

    # Save report
    report_file = DATA_DIR / f"report_{datetime.now().strftime('%Y%m%d')}.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    print(f"\nReport saved to: {report_file}")


if __name__ == "__main__":
    main()
