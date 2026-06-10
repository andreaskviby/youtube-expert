#!/usr/bin/env python3
"""
Create YouTube Shorts from EP36 Cooking Class
Vertical 9:16 format with captions
"""

import subprocess
from pathlib import Path

SOURCE = Path("EP36_REBUILD/source/ep36_cooking_class.mp4")
SHORTS_DIR = Path("EP36_REBUILD/shorts")
SHORTS_DIR.mkdir(exist_ok=True)

# Shorts: (start, end, name, caption_text, has_talking)
SHORTS = [
    # Short 1: Wine Story (personality moment)
    ("00:04:47", "00:05:45", "short1_wine_story",
     "The REAL reason I drink wine while cooking", True),

    # Short 2: Secret Sauce Reveal
    ("00:12:00", "00:13:00", "short2_secret_sauce",
     "The €1 secret to amazing pasta", True),

    # Short 3: Chili Pepper Moment
    ("00:14:48", "00:15:30", "short3_chili",
     "This Sicilian chili will DESTROY any cold", True),

    # Short 4: Final Reveal (time-lapse style)
    ("00:24:20", "00:29:50", "short4_timelapse_reveal",
     "30 minutes of cooking in 60 seconds", False),
]


def create_short(start: str, end: str, name: str, caption: str, has_talking: bool) -> Path:
    """Create vertical short with caption overlay"""
    output = SHORTS_DIR / f"{name}.mp4"

    # Calculate if we need to speed up (for timelapse short)
    # Short 4 is 5:30 -> need to compress to ~50 seconds
    speed = 1.0
    if not has_talking:
        speed = 6.0  # Speed up non-talking sections

    # Build filter for vertical crop (9:16) + caption
    # Crop center of 16:9 to get 9:16
    # Original is likely 1920x1080, we want 1080x1920 (or 608x1080 from center)

    caption_escaped = caption.replace("'", "'\\''")

    if speed == 1.0:
        filter_complex = (
            # Crop to vertical (take center portion)
            "[0:v]crop=ih*9/16:ih:iw/2-ih*9/32:0,"
            # Scale to 1080x1920
            "scale=1080:1920,"
            # Add caption at bottom
            f"drawtext=text='{caption_escaped}':"
            "fontfile=/System/Library/Fonts/Supplemental/Impact.ttf:"
            "fontsize=60:fontcolor=white:"
            "borderw=3:bordercolor=black:"
            "x=(w-text_w)/2:y=h-150[v]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-ss", start, "-to", end,
            "-i", str(SOURCE),
            "-filter_complex", filter_complex,
            "-map", "[v]", "-map", "0:a",
            "-c:v", "libx264", "-c:a", "aac",
            "-preset", "fast",
            "-t", "60",  # Max 60 seconds for shorts
            str(output)
        ]
    else:
        # Time-lapse version (muted, sped up)
        filter_complex = (
            # Crop to vertical
            f"[0:v]crop=ih*9/16:ih:iw/2-ih*9/32:0,"
            # Speed up
            f"setpts={1/speed}*PTS,"
            # Scale to 1080x1920
            "scale=1080:1920,"
            # Add caption at bottom
            f"drawtext=text='{caption_escaped}':"
            "fontfile=/System/Library/Fonts/Supplemental/Impact.ttf:"
            "fontsize=60:fontcolor=white:"
            "borderw=3:bordercolor=black:"
            "x=(w-text_w)/2:y=h-150[v]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-ss", start, "-to", end,
            "-i", str(SOURCE),
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-an",  # No audio for timelapse
            "-c:v", "libx264",
            "-preset", "fast",
            "-t", "60",
            str(output)
        ]

    print(f"   Creating: {name}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"   Error: {result.stderr[:200]}")

    return output


def get_duration(path: Path) -> float:
    """Get video duration in seconds"""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True
    )
    return float(result.stdout.strip()) if result.stdout.strip() else 0


def main():
    print("=" * 60)
    print("CREATING YOUTUBE SHORTS")
    print("From EP36 Cooking Class")
    print("=" * 60)

    created = []

    for start, end, name, caption, has_talking in SHORTS:
        short_path = create_short(start, end, name, caption, has_talking)
        duration = get_duration(short_path)
        created.append((name, duration, caption))

    print("\n" + "=" * 60)
    print("✅ SHORTS CREATED:")
    print("=" * 60)

    for name, duration, caption in created:
        print(f"\n📱 {name}")
        print(f"   Duration: {int(duration)}s")
        print(f"   Caption: \"{caption}\"")
        print(f"   File: EP36_REBUILD/shorts/{name}.mp4")

    print("\n" + "=" * 60)
    print("SUGGESTED HASHTAGS:")
    print("#sicily #italianfood #cooking #pasta #homecooking")
    print("#sicilianfood #cookingclass #foodie #italia")
    print("=" * 60)


if __name__ == "__main__":
    main()
