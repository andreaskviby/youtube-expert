#!/usr/bin/env python3
"""
EP36 COOKING CLASS - REMASTERED VERSION
Target: ~12 minutes (from 30:23 original)
Strategy: Keep personality moments, time-lapse cooking process
"""

import subprocess
from pathlib import Path

SOURCE = Path("EP36_REBUILD/source/ep36_cooking_class.mp4")
CLIPS_DIR = Path("EP36_REBUILD/clips")
OUTPUT_DIR = Path("EP36_REBUILD/output")

CLIPS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Clip structure: (start, end, name, text_overlay, speed)
# Speed 1.0 = normal, 2.0+ = time-lapse
CLIPS = [
    # HOOK - Opening (garlic prep)
    ("00:00:00", "00:00:50", "01_intro_garlic", "COOKING CLASS", 1.0),

    # Prep work - TIME LAPSE
    ("00:00:50", "00:03:30", "02_prep_work", None, 3.0),

    # Sicilian spice moment (personality)
    ("00:02:27", "00:03:10", "03_sicilian_spice", "SICILIAN SPICES", 1.0),

    # More prep - TIME LAPSE
    ("00:03:30", "00:04:30", "04_more_prep", None, 2.5),

    # Wine story (great personality moment)
    ("00:04:47", "00:05:50", "05_wine_story", None, 1.0),

    # Adding meat to pan
    ("00:06:00", "00:06:45", "06_adding_meat", "THE COOKING", 1.0),

    # Fresh olive oil story (local knowledge)
    ("00:07:25", "00:08:10", "07_olive_oil", "FRESH OLIVE OIL", 1.0),

    # Choosing pasta - TIME LAPSE
    ("00:08:56", "00:10:30", "08_choosing_pasta", None, 3.0),

    # Wine from local vineyard
    ("00:11:27", "00:11:55", "09_local_wine", None, 1.0),

    # THE SECRET - Sicilian tomato sauce
    ("00:12:00", "00:13:10", "10_secret_sauce", "THE SECRET", 1.0),

    # Chili pepper secret
    ("00:14:48", "00:15:35", "11_chili_secret", None, 1.0),

    # Mid-video intro (great hook for retention)
    ("00:15:35", "00:16:28", "12_cooking_class_intro", None, 1.0),

    # Adding cream to sauce
    ("00:16:28", "00:16:50", "13_adding_cream", None, 1.0),

    # Italian lesson (fun personality)
    ("00:18:04", "00:18:55", "14_italian_words", "ITALIAN LESSON", 1.0),

    # Testing pasta - TIME LAPSE
    ("00:19:10", "00:22:20", "15_testing_pasta", None, 3.5),

    # Al dente wisdom
    ("00:22:22", "00:22:52", "16_al_dente", None, 1.0),

    # Final cooking - TIME LAPSE
    ("00:22:52", "00:24:20", "17_final_cooking", None, 2.5),

    # The mixing - satisfying moment
    ("00:24:20", "00:25:30", "18_mixing", "MIXING TIME", 1.5),

    # More mixing
    ("00:25:30", "00:27:00", "19_more_mixing", None, 2.0),

    # Plating - TIME LAPSE
    ("00:27:26", "00:29:20", "20_plating", None, 3.0),

    # FINAL REVEAL
    ("00:29:30", "00:29:50", "21_reveal", "THE RESULT!", 1.0),

    # CTA
    ("00:29:45", "00:30:20", "22_cta", None, 1.0),
]


def time_to_seconds(t: str) -> float:
    """Convert HH:MM:SS to seconds"""
    parts = t.split(":")
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])


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
        # Speed up video and audio (atempo max is 2.0, chain for higher)
        atempo_filters = []
        remaining_speed = speed
        while remaining_speed > 2.0:
            atempo_filters.append("atempo=2.0")
            remaining_speed /= 2.0
        atempo_filters.append(f"atempo={remaining_speed}")
        atempo_chain = ",".join(atempo_filters)

        cmd = [
            "ffmpeg", "-y",
            "-ss", start, "-to", end,
            "-i", str(SOURCE),
            "-filter_complex", f"[0:v]setpts={1/speed}*PTS[v];[0:a]{atempo_chain}[a]",
            "-map", "[v]", "-map", "[a]",
            "-preset", "fast",
            str(output)
        ]

    subprocess.run(cmd, capture_output=True)
    return output


def add_text_overlay(input_path: Path, text: str) -> Path:
    """Add text overlay at top of frame"""
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
    """Join all clips into final video"""
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


def estimate_duration():
    """Estimate final duration before processing"""
    total = 0
    for start, end, name, text, speed in CLIPS:
        duration = time_to_seconds(end) - time_to_seconds(start)
        adjusted = duration / speed
        total += adjusted
        print(f"   {name}: {duration:.0f}s @ {speed}x = {adjusted:.0f}s")

    mins = int(total // 60)
    secs = int(total % 60)
    print(f"\n   ESTIMATED TOTAL: {mins}:{secs:02d}")
    return total


def main():
    print("=" * 60)
    print("EP36 COOKING CLASS - REMASTERED")
    print("Original: 30:23 | Target: ~12 minutes")
    print("=" * 60)

    print("\n📊 DURATION ESTIMATE:")
    estimate_duration()

    print("\n🎬 PROCESSING CLIPS:")
    processed = []

    for i, (start, end, name, text, speed) in enumerate(CLIPS):
        speed_label = "TIME-LAPSE" if speed > 1.0 else "NORMAL"
        print(f"   [{i+1}/{len(CLIPS)}] {name} ({speed_label} {speed}x)")

        clip = extract_clip(start, end, name, speed)

        if text:
            clip = add_text_overlay(clip, text)

        processed.append(clip)

    print(f"\n🔗 JOINING {len(processed)} CLIPS...")
    final = concatenate_clips(processed, "ep36_cooking_class_remastered.mp4")

    # Get actual duration
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(final)],
        capture_output=True, text=True
    )
    duration = float(result.stdout.strip())
    mins = int(duration // 60)
    secs = int(duration % 60)

    print("\n" + "=" * 60)
    print(f"✅ REMASTERED VIDEO COMPLETE!")
    print(f"   Output: {final}")
    print(f"   Duration: {mins}:{secs:02d}")
    print(f"   Compression: 30:23 → {mins}:{secs:02d}")
    print("=" * 60)

    return final


if __name__ == "__main__":
    main()
