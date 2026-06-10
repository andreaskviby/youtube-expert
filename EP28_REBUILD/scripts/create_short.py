#!/usr/bin/env python3
"""
Create a YouTube Short from EP59 highlight
Vertical 9:16 format, under 60 seconds
"""

import subprocess
from pathlib import Path

SOURCE = Path("EP28_REBUILD/output/ep28_highlight_v1.mp4")
OUTPUT = Path("EP28_REBUILD/output/ep59_short.mp4")

# Key moments for Short (must be under 60 seconds)
# Structure: Hook → Problem → Solution → Result
CLIPS = [
    # Hook - wet floor reveal
    ("00:00:00", "00:00:08"),
    # Problem - flooding explanation
    ("00:00:08", "00:00:25"),
    # Quick work montage
    ("00:01:07", "00:01:20"),
    # Success reveal
    ("00:02:22", "00:02:40"),
]

def create_short():
    print("=" * 60)
    print("Creating YouTube Short from EP59")
    print("=" * 60)

    # Create temporary clips
    temp_clips = []
    for i, (start, end) in enumerate(CLIPS):
        temp_file = f"/tmp/short_clip_{i}.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-ss", start,
            "-to", end,
            "-i", str(SOURCE),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-preset", "fast",
            temp_file
        ]
        subprocess.run(cmd, capture_output=True)
        temp_clips.append(temp_file)
        print(f"   Extracted clip {i+1}: {start} -> {end}")

    # Create concat file
    concat_file = "/tmp/short_concat.txt"
    with open(concat_file, "w") as f:
        for clip in temp_clips:
            f.write(f"file '{clip}'\n")

    # Concatenate
    temp_concat = "/tmp/short_concat.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-c:v", "libx264",
        "-c:a", "aac",
        temp_concat
    ]
    subprocess.run(cmd, capture_output=True)

    # Convert to vertical 9:16 (1080x1920) with crop and text
    # Crop center of 16:9 to fit 9:16
    cmd = [
        "ffmpeg", "-y",
        "-i", temp_concat,
        "-vf", (
            # Crop to vertical (take center portion)
            "crop=ih*9/16:ih,"
            # Scale to 1080x1920
            "scale=1080:1920,"
            # Add text overlay
            "drawtext=text='RAINWATER DISASTER':"
            "fontfile=/System/Library/Fonts/Supplemental/Impact.ttf:"
            "fontsize=80:fontcolor=white:borderw=4:bordercolor=black:"
            "x=(w-text_w)/2:y=100,"
            # Add CTA at bottom
            "drawtext=text='Full video on channel!':"
            "fontfile=/System/Library/Fonts/Supplemental/Impact.ttf:"
            "fontsize=50:fontcolor=yellow:borderw=3:bordercolor=black:"
            "x=(w-text_w)/2:y=h-150"
        ),
        "-c:a", "aac",
        "-preset", "medium",
        str(OUTPUT)
    ]
    subprocess.run(cmd, capture_output=True)

    # Get duration
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(OUTPUT)],
        capture_output=True, text=True
    )
    duration = float(result.stdout.strip())

    print(f"\n✅ Short created!")
    print(f"   Output: {OUTPUT}")
    print(f"   Duration: {duration:.1f} seconds")
    print(f"   Format: 1080x1920 (9:16 vertical)")

    if duration > 60:
        print(f"\n⚠️ WARNING: Duration is {duration:.1f}s, should be under 60s for Shorts")

    return OUTPUT

if __name__ == "__main__":
    create_short()
