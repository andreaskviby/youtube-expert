#!/usr/bin/env python3
"""
YouTube Video Upload Script for EP59
Uses YouTube Data API v3 with OAuth2

Requirements:
1. client_secrets.json in youtube_api/ folder
2. First run will open browser for authorization
"""

import os
import json
import pickle
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
CLIENT_SECRETS_FILE = 'youtube_api/client_secrets.json'
TOKEN_FILE = 'youtube_api/token.pickle'

def get_authenticated_service():
    """Get authenticated YouTube service"""
    credentials = None

    # Load existing token
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            credentials = pickle.load(token)

    # Refresh or get new credentials
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRETS_FILE):
                print("ERROR: client_secrets.json not found!")
                print("\nTo set up YouTube upload:")
                print("1. Go to https://console.cloud.google.com/")
                print("2. Create OAuth 2.0 Client ID (Desktop app)")
                print("3. Download JSON as 'client_secrets.json'")
                print("4. Place in youtube_api/ folder")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES
            )
            credentials = flow.run_local_server(port=0)

        # Save token for future use
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(credentials, token)

    return build('youtube', 'v3', credentials=credentials)


def upload_video(metadata_file: str):
    """Upload video with metadata"""

    # Load metadata
    with open(metadata_file) as f:
        meta = json.load(f)

    print("=" * 60)
    print("YOUTUBE VIDEO UPLOAD")
    print("=" * 60)
    print(f"Title: {meta['title']}")
    print(f"Video: {meta['video_file']}")
    print(f"Thumbnail: {meta['thumbnail']}")
    print("=" * 60)

    # Check files exist
    if not os.path.exists(meta['video_file']):
        print(f"ERROR: Video file not found: {meta['video_file']}")
        return None

    # Get authenticated service
    youtube = get_authenticated_service()
    if not youtube:
        return None

    print("\nUploading video...")

    # Upload body
    body = {
        'snippet': {
            'title': meta['title'],
            'description': meta['description'],
            'tags': meta['tags'],
            'categoryId': meta['category'],
            'defaultLanguage': meta.get('language', 'en'),
        },
        'status': {
            'privacyStatus': meta.get('privacy', 'private'),
            'selfDeclaredMadeForKids': meta.get('made_for_kids', False),
        }
    }

    # Media upload
    media = MediaFileUpload(
        meta['video_file'],
        mimetype='video/mp4',
        resumable=True,
        chunksize=10 * 1024 * 1024  # 10MB chunks
    )

    # Execute upload
    request = youtube.videos().insert(
        part='snippet,status',
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"   Upload progress: {int(status.progress() * 100)}%")

    video_id = response['id']
    print(f"\n✅ Video uploaded! ID: {video_id}")
    print(f"   URL: https://youtube.com/watch?v={video_id}")

    # Upload thumbnail
    if os.path.exists(meta['thumbnail']):
        print("\nUploading thumbnail...")
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(meta['thumbnail'])
        ).execute()
        print("✅ Thumbnail uploaded!")

    print("\n" + "=" * 60)
    print("UPLOAD COMPLETE!")
    print(f"https://youtube.com/watch?v={video_id}")
    print("=" * 60)

    return video_id


if __name__ == "__main__":
    upload_video("EP28_REBUILD/upload/metadata.json")
