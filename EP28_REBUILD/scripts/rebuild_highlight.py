#!/usr/bin/env python3
"""
EP28 REBUILD SCRIPT - Creates 2-3 minute highlight version
Target: Improve retention from 1.8% to 25%+

Strategy: Start with action, show problem immediately, quick solution, success
"""

import os
import subprocess
from pathlib import Path

# Paths
SOURCE = Path("EP28_REBUILD/source/ep28_full.mp4")
CLIPS_DIR = Path("EP28_REBUILD/clips")
OUTPUT_DIR = Path("EP28_REBUILD/output")

CLIPS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Key moments from transcript analysis (start, end, description)
CLIPS = [
    # HOOK - Start with the wet floor / problem immediately
    ("00:00:15", "00:00:23", "hook_wet", "THE PROBLEM"),

    # Problem explanation - water flooding
    ("00:00:34", "00:01:17", "problem_explanation", "FLOODING TERRACE"),

    # Solution intro - copper pipes
    ("00:01:17", "00:01:33", "solution_intro", "THE SOLUTION"),

    # Work montage - quick cuts
    ("00:02:00", "00:02:10", "work_1", None),
    ("00:03:00", "00:03:05", "work_2", None),
    ("00:04:30", "00:04:40", "work_3", None),

    # Kitchen explanation - how it works
    ("00:05:34", "00:06:13", "kitchen_explanation", "HOW IT WORKS"),

    # More work - time lapse feel
    ("00:08:00", "00:08:15", "work_4", None),
    ("00:09:40", "00:09:55", "work_5", None),
    ("00:10:00", "00:10:15", "work_6", None),

    # SUCCESS - project done!
    ("00:11:00", "00:11:46", "success", "SUCCESS!"),

    # CTA
    ("00:16:46", "00:16:59", "cta", None),
]


def extract_clip(start: str, end: str, name: str) -> Path:
    """Extract a clip from source video"""
    output = CLIPS_DIR / f"{name}.mp4"

    cmd = [
        "ffmpeg", "-y",
        "-ss", start,
        "-to", end,
        "-i", str(SOURCE),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-preset", "fast",
        str(output)
    ]

    print(f"   Extracting {name}: {start} -> {end}")
    subprocess.run(cmd, capture_output=True)
    return output


def speed_up_clip(input_path: Path, speed: float = 2.0) -> Path:
    """Speed up a clip for time-lapse effect"""
    output = input_path.parent / f"{input_path.stem}_fast.mp4"

    # Video speedup with setpts, audio speedup with atempo
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-filter_complex", f"[0:v]setpts={1/speed}*PTS[v];[0:a]atempo={speed}[a]",
        "-map", "[v]",
        "-map", "[a]",
        "-preset", "fast",
        str(output)
    ]

    subprocess.run(cmd, capture_output=True)
    return output


def add_text_overlay(input_path: Path, text: str, position: str = "top") -> Path:
    """Add text overlay to clip"""
    output = input_path.parent / f"{input_path.stem}_text.mp4"

    y_pos = "h*0.1" if position == "top" else "h*0.85"

    # Bold white text with black outline
    drawtext = (
        f"drawtext=text='{text}':"
        f"fontfile=/System/Library/Fonts/Supplemental/Impact.ttf:"
        f"fontsize=72:fontcolor=white:"
        f"borderw=4:bordercolor=black:"
        f"x=(w-text_w)/2:y={y_pos}"
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


def concatenate_clips(clip_paths: list, output_name: str) -> Path:
    """Concatenate all clips into final video"""
    # Create concat file
    concat_file = CLIPS_DIR / "concat_list.txt"
    with open(concat_file, "w") as f:
        for clip in clip_paths:
            f.write(f"file '{clip.absolute()}'\n")

    output = OUTPUT_DIR / output_name

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-preset", "medium",
        "-crf", "23",
        str(output)
    ]

    print(f"\n   Concatenating {len(clip_paths)} clips...")
    subprocess.run(cmd, capture_output=True)

    return output


def main():
    print("=" * 60)
    print("EP28 REBUILD - Creating Highlight Version")
    print("=" * 60)

    print("\n1. EXTRACTING CLIPS...")
    processed_clips = []

    for start, end, name, text_overlay in CLIPS:
        # Extract clip
        clip = extract_clip(start, end, name)

        # Speed up work clips for time-lapse effect
        if "work_" in name:
            clip = speed_up_clip(clip, speed=3.0)

        # Add text overlay if specified
        if text_overlay:
            clip = add_text_overlay(clip, text_overlay)

        processed_clips.append(clip)

    print(f"\n   Extracted {len(processed_clips)} clips")

    print("\n2. ASSEMBLING HIGHLIGHT...")
    final = concatenate_clips(processed_clips, "ep28_highlight_v1.mp4")

    # Get duration
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(final)],
        capture_output=True, text=True
    )
    duration = float(result.stdout.strip())

    print("\n" + "=" * 60)
    print(f"DONE!")
    print(f"Output: {final}")
    print(f"Duration: {int(duration // 60)}:{int(duration % 60):02d}")
    print("=" * 60)

    return final


if __name__ == "__main__":
    main()
