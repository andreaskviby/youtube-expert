#!/usr/bin/env python3
"""
EP28 REBUILD - EXTENDED VERSION v2 (6-7 min target)
Tighter edit, but more content than 3-min version
"""

import subprocess
from pathlib import Path

SOURCE = Path("EP28_REBUILD/source/ep28_full.mp4")
CLIPS_DIR = Path("EP28_REBUILD/clips_extended_v2")
OUTPUT_DIR = Path("EP28_REBUILD/output")

CLIPS_DIR.mkdir(exist_ok=True)

# Tighter clip list for 6-7 minutes
CLIPS = [
    # HOOK - Problem intro (keep full - this is gold)
    ("00:00:00", "00:01:33", "01_intro_problem", "THE PROBLEM", 1.0),

    # Work montage - faster cuts
    ("00:01:45", "00:02:20", "02_work_start", None, 1.5),
    ("00:02:30", "00:03:20", "03_work_progress", None, 2.0),
    ("00:04:00", "00:05:00", "04_work_cont", None, 2.5),

    # Kitchen explanation (full - important)
    ("00:05:34", "00:06:20", "05_kitchen_explain", "HOW IT WORKS", 1.0),

    # Build section - key moments
    ("00:07:53", "00:08:30", "06_cutting", "THE BUILD", 1.0),
    ("00:08:38", "00:09:30", "07_install", None, 1.5),
    ("00:10:02", "00:10:50", "08_crawling", None, 1.5),

    # SUCCESS - full reveal (emotional payoff)
    ("00:11:00", "00:11:50", "09_success", "SUCCESS!", 1.0),

    # CTA
    ("00:16:46", "00:16:59", "10_cta", None, 1.0),
]


def extract_clip(start: str, end: str, name: str, speed: float = 1.0) -> Path:
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
        cmd = [
            "ffmpeg", "-y",
            "-ss", start, "-to", end,
            "-i", str(SOURCE),
            "-filter_complex", f"[0:v]setpts={1/speed}*PTS[v];[0:a]atempo={min(speed, 2.0)}[a]",
            "-map", "[v]", "-map", "[a]",
            "-preset", "fast",
            str(output)
        ]

    subprocess.run(cmd, capture_output=True)
    return output


def add_text_overlay(input_path: Path, text: str) -> Path:
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
    print("EP28 REBUILD - EXTENDED v2")
    print("Target: 6-7 minutes")
    print("=" * 60)

    processed = []

    for start, end, name, text, speed in CLIPS:
        print(f"   {name}: {start} -> {end} @ {speed}x")
        clip = extract_clip(start, end, name, speed)
        if text:
            clip = add_text_overlay(clip, text)
        processed.append(clip)

    print(f"\n   Joining {len(processed)} clips...")
    final = concatenate_clips(processed, "ep28_extended_v2.mp4")

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
