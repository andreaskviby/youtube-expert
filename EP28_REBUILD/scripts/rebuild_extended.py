#!/usr/bin/env python3
"""
EP28 REBUILD - EXTENDED VERSION (5-7 min)
More content, same strong hook structure
"""

import subprocess
from pathlib import Path

SOURCE = Path("EP28_REBUILD/source/ep28_full.mp4")
CLIPS_DIR = Path("EP28_REBUILD/clips_extended")
OUTPUT_DIR = Path("EP28_REBUILD/output")

CLIPS_DIR.mkdir(exist_ok=True)

# Extended clip list for 5-7 minute version
CLIPS = [
    # HOOK - Problem intro (full version)
    ("00:00:00", "00:01:33", "01_intro_problem", "THE PROBLEM", 1.0),

    # Work begins - show more process
    ("00:01:45", "00:02:30", "02_work_start", None, 1.0),
    ("00:02:30", "00:03:30", "03_work_progress", None, 1.5),  # Slight speedup
    ("00:03:30", "00:04:30", "04_work_cont", None, 1.5),
    ("00:04:30", "00:05:30", "05_work_more", None, 2.0),  # Speed up repetitive

    # Kitchen explanation (full)
    ("00:05:34", "00:06:46", "06_kitchen_explain", "HOW IT WORKS", 1.0),

    # Template and prep work
    ("00:06:46", "00:07:30", "07_template", None, 1.0),

    # Cutting and adjustment
    ("00:07:53", "00:08:48", "08_cutting", "THE BUILD", 1.0),

    # Installation work
    ("00:08:48", "00:09:50", "09_install", None, 1.5),
    ("00:09:50", "00:10:50", "10_crawling", None, 1.5),

    # SUCCESS - full reveal
    ("00:11:00", "00:12:11", "11_success", "SUCCESS!", 1.0),

    # Bonus teaser (optional room preview)
    ("00:12:19", "00:12:35", "12_bonus_teaser", "COMING NEXT...", 1.0),

    # CTA
    ("00:16:46", "00:16:59", "13_cta", None, 1.0),
]


def extract_clip(start: str, end: str, name: str, speed: float = 1.0) -> Path:
    """Extract clip with optional speed adjustment"""
    output = CLIPS_DIR / f"{name}.mp4"

    if speed == 1.0:
        cmd = [
            "ffmpeg", "-y",
            "-ss", start, "-to", end,
            "-i", str(SOURCE),
            "-c:v", "libx264", "-c:a", "aac",
            "-preset", "fast",
            str(output)
        ]
    else:
        # Speed up video and audio
        cmd = [
            "ffmpeg", "-y",
            "-ss", start, "-to", end,
            "-i", str(SOURCE),
            "-filter_complex", f"[0:v]setpts={1/speed}*PTS[v];[0:a]atempo={speed}[a]",
            "-map", "[v]", "-map", "[a]",
            "-preset", "fast",
            str(output)
        ]

    subprocess.run(cmd, capture_output=True)
    return output


def add_text_overlay(input_path: Path, text: str) -> Path:
    """Add text overlay"""
    output = input_path.parent / f"{input_path.stem}_text.mp4"

    drawtext = (
        f"drawtext=text='{text}':"
        f"fontfile=/System/Library/Fonts/Supplemental/Impact.ttf:"
        f"fontsize=72:fontcolor=white:"
        f"borderw=4:bordercolor=black:"
        f"x=(w-text_w)/2:y=h*0.1"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-vf", drawtext,
        "-c:a", "copy",
        "-preset", "fast",
        str(output)
    ]

    subprocess.run(cmd, capture_output=True)
    return output


def concatenate_clips(clips: list, output_name: str) -> Path:
    """Join all clips"""
    concat_file = CLIPS_DIR / "concat_list.txt"
    with open(concat_file, "w") as f:
        for clip in clips:
            f.write(f"file '{clip.absolute()}'\n")

    output = OUTPUT_DIR / output_name

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-c:a", "aac",
        "-preset", "medium", "-crf", "23",
        str(output)
    ]

    subprocess.run(cmd, capture_output=True)
    return output


def main():
    print("=" * 60)
    print("EP28 REBUILD - EXTENDED VERSION")
    print("Target: 5-7 minutes")
    print("=" * 60)

    processed = []

    for start, end, name, text, speed in CLIPS:
        print(f"   Processing: {name} ({start} -> {end}, speed {speed}x)")

        clip = extract_clip(start, end, name, speed)

        if text:
            clip = add_text_overlay(clip, text)

        processed.append(clip)

    print(f"\n   Joining {len(processed)} clips...")

    final = concatenate_clips(processed, "ep28_extended_v1.mp4")

    # Get duration
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(final)],
        capture_output=True, text=True
    )
    duration = float(result.stdout.strip())
    mins = int(duration // 60)
    secs = int(duration % 60)

    print(f"\n" + "=" * 60)
    print(f"✅ DONE!")
    print(f"   Output: {final}")
    print(f"   Duration: {mins}:{secs:02d}")
    print("=" * 60)

    return final


if __name__ == "__main__":
    main()
