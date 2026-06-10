#!/usr/bin/env python3
"""
EP36 COOKING CLASS - REMASTERED V2
With subtitles and muted time-lapse sections (no Donald Duck!)
"""

import subprocess
import json
from pathlib import Path

SOURCE = Path("EP36_REBUILD/source/ep36_cooking_class.mp4")
SUBTITLES = Path("EP36_REBUILD/source/ep36_subtitles.srt")
CLIPS_DIR = Path("EP36_REBUILD/clips_v2")
OUTPUT_DIR = Path("EP36_REBUILD/output")

CLIPS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Clip structure: (start, end, name, text_overlay, speed)
CLIPS = [
    # HOOK - Opening (garlic prep)
    ("00:00:00", "00:00:50", "01_intro_garlic", "COOKING CLASS", 1.0),

    # Prep work - TIME LAPSE (muted)
    ("00:00:50", "00:02:27", "02_prep_work", None, 3.0),

    # Sicilian spice moment (personality)
    ("00:02:27", "00:03:10", "03_sicilian_spice", "SICILIAN SPICES", 1.0),

    # More prep - TIME LAPSE (muted)
    ("00:03:10", "00:04:47", "04_more_prep", None, 2.5),

    # Wine story (great personality moment)
    ("00:04:47", "00:06:00", "05_wine_story", None, 1.0),

    # Adding meat to pan
    ("00:06:00", "00:06:45", "06_adding_meat", "THE COOKING", 1.0),

    # Fresh olive oil story (local knowledge)
    ("00:07:25", "00:08:10", "07_olive_oil", "FRESH OLIVE OIL", 1.0),

    # Choosing pasta - TIME LAPSE (muted)
    ("00:08:56", "00:10:30", "08_choosing_pasta", None, 3.0),

    # Wine from local vineyard
    ("00:11:27", "00:12:00", "09_local_wine", None, 1.0),

    # THE SECRET - Sicilian tomato sauce
    ("00:12:00", "00:13:10", "10_secret_sauce", "THE SECRET", 1.0),

    # Chili pepper secret
    ("00:14:48", "00:15:35", "11_chili_secret", None, 1.0),

    # Mid-video intro (great hook for retention)
    ("00:15:35", "00:16:28", "12_cooking_class_intro", None, 1.0),

    # Adding cream to sauce
    ("00:16:28", "00:17:10", "13_adding_cream", None, 1.0),

    # Italian lesson (fun personality)
    ("00:18:04", "00:19:00", "14_italian_words", "ITALIAN LESSON", 1.0),

    # Testing pasta - TIME LAPSE (muted)
    ("00:19:10", "00:22:20", "15_testing_pasta", None, 3.5),

    # Al dente wisdom
    ("00:22:22", "00:23:00", "16_al_dente", None, 1.0),

    # Final cooking - TIME LAPSE (muted)
    ("00:23:00", "00:24:20", "17_final_cooking", None, 2.5),

    # The mixing - satisfying moment (slight speedup, keep audio)
    ("00:24:20", "00:25:30", "18_mixing", "MIXING TIME", 1.0),

    # More mixing - TIME LAPSE (muted)
    ("00:25:30", "00:27:26", "19_more_mixing", None, 2.0),

    # Plating - TIME LAPSE (muted)
    ("00:27:26", "00:29:30", "20_plating", None, 3.0),

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
    """Extract clip - mute audio if speed > 1.0"""
    output = CLIPS_DIR / f"{name}.mp4"

    if speed == 1.0:
        # Normal speed - keep audio
        cmd = [
            "ffmpeg", "-y",
            "-ss", start, "-to", end,
            "-i", str(SOURCE),
            "-c:v", "libx264", "-c:a", "aac",
            "-preset", "fast",
            str(output)
        ]
    else:
        # Time-lapse - MUTE audio (no Donald Duck!)
        cmd = [
            "ffmpeg", "-y",
            "-ss", start, "-to", end,
            "-i", str(SOURCE),
            "-filter_complex", f"[0:v]setpts={1/speed}*PTS[v]",
            "-map", "[v]",
            "-an",  # No audio!
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

    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        # If no audio stream, handle differently
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-vf", drawtext,
            "-preset", "fast",
            str(output)
        ]
        subprocess.run(cmd, capture_output=True)

    return output


def create_adjusted_subtitles() -> Path:
    """Create subtitle file adjusted for the remastered timing"""

    # Load original subtitles
    with open("EP36_REBUILD/transcripts/ep36_full.json", "r") as f:
        data = json.load(f)

    segments = data["segments"]
    adjusted_subs = []

    # Calculate timing offsets based on clip structure
    current_output_time = 0.0

    for start_str, end_str, name, text, speed in CLIPS:
        clip_start = time_to_seconds(start_str)
        clip_end = time_to_seconds(end_str)
        clip_duration = clip_end - clip_start
        output_duration = clip_duration / speed

        # Find subtitles that fall within this clip
        for seg in segments:
            seg_start = seg["start"]
            seg_end = seg["end"]

            # Check if segment overlaps with this clip
            if seg_end > clip_start and seg_start < clip_end:
                # Adjust timing relative to clip start
                relative_start = max(0, seg_start - clip_start)
                relative_end = min(clip_duration, seg_end - clip_start)

                # Apply speed adjustment
                adjusted_start = current_output_time + (relative_start / speed)
                adjusted_end = current_output_time + (relative_end / speed)

                adjusted_subs.append({
                    "start": adjusted_start,
                    "end": adjusted_end,
                    "text": seg["text"].strip()
                })

        current_output_time += output_duration

    # Write adjusted SRT
    def format_time(seconds):
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{hours:02d}:{mins:02d}:{secs:02d},{ms:03d}"

    srt_path = CLIPS_DIR / "adjusted_subtitles.srt"
    with open(srt_path, "w") as f:
        for i, sub in enumerate(adjusted_subs, 1):
            f.write(f"{i}\n")
            f.write(f"{format_time(sub['start'])} --> {format_time(sub['end'])}\n")
            f.write(f"{sub['text']}\n\n")

    print(f"   Created {len(adjusted_subs)} adjusted subtitles")
    return srt_path


def concatenate_clips(clips: list, output_name: str) -> Path:
    """Join all clips into intermediate video (no subtitles yet)"""
    concat_file = CLIPS_DIR / "concat_list.txt"

    # Need to ensure all clips have same format
    # Add silent audio to clips without audio
    normalized_clips = []
    for clip in clips:
        # Check if clip has audio
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a",
             "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(clip)],
            capture_output=True, text=True
        )

        if "audio" not in result.stdout:
            # Add silent audio track
            normalized = clip.parent / f"{clip.stem}_norm.mp4"
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                "-i", str(clip),
                "-c:v", "copy", "-c:a", "aac", "-shortest",
                str(normalized)
            ]
            subprocess.run(cmd, capture_output=True)
            normalized_clips.append(normalized)
        else:
            normalized_clips.append(clip)

    with open(concat_file, "w") as f:
        for clip in normalized_clips:
            f.write(f"file '{clip.absolute()}'\n")

    output = CLIPS_DIR / output_name

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-c:a", "aac",
        "-preset", "fast",
        str(output)
    ]

    subprocess.run(cmd, capture_output=True)
    return output


def burn_subtitles(video_path: Path, srt_path: Path, output_name: str) -> Path:
    """Burn subtitles into final video"""
    output = OUTPUT_DIR / output_name

    # Escape path for ffmpeg filter
    srt_escaped = str(srt_path.absolute()).replace(":", "\\:")

    subtitle_style = (
        "FontName=Impact,"
        "FontSize=24,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "Outline=2,"
        "Shadow=1,"
        "MarginV=50"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vf", f"subtitles='{srt_escaped}':force_style='{subtitle_style}'",
        "-c:a", "copy",
        "-preset", "medium", "-crf", "23",
        str(output)
    ]

    subprocess.run(cmd, capture_output=True)
    return output


def estimate_duration():
    """Estimate final duration"""
    total = 0
    for start, end, name, text, speed in CLIPS:
        duration = time_to_seconds(end) - time_to_seconds(start)
        adjusted = duration / speed
        total += adjusted
        audio_status = "🔇 MUTED" if speed > 1.0 else "🔊 AUDIO"
        print(f"   {name}: {duration:.0f}s @ {speed}x = {adjusted:.0f}s {audio_status}")

    mins = int(total // 60)
    secs = int(total % 60)
    print(f"\n   ESTIMATED TOTAL: {mins}:{secs:02d}")
    return total


def main():
    print("=" * 60)
    print("EP36 COOKING CLASS - REMASTERED V2")
    print("With subtitles + muted time-lapse (no Donald Duck!)")
    print("=" * 60)

    print("\n📊 DURATION ESTIMATE:")
    estimate_duration()

    print("\n📝 CREATING ADJUSTED SUBTITLES...")
    srt_path = create_adjusted_subtitles()

    print("\n🎬 PROCESSING CLIPS:")
    processed = []

    for i, (start, end, name, text, speed) in enumerate(CLIPS):
        audio_status = "🔇 MUTED" if speed > 1.0 else "🔊 AUDIO"
        print(f"   [{i+1}/{len(CLIPS)}] {name} ({speed}x) {audio_status}")

        clip = extract_clip(start, end, name, speed)

        if text:
            clip = add_text_overlay(clip, text)

        processed.append(clip)

    print(f"\n🔗 JOINING {len(processed)} CLIPS...")
    intermediate = concatenate_clips(processed, "intermediate.mp4")

    print("\n📝 BURNING SUBTITLES...")
    final = burn_subtitles(intermediate, srt_path, "ep36_cooking_class_remastered_v2.mp4")

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
    print(f"✅ REMASTERED V2 COMPLETE!")
    print(f"   Output: {final}")
    print(f"   Duration: {mins}:{secs:02d}")
    print(f"   Features: Subtitles + muted time-lapse")
    print("=" * 60)

    return final


if __name__ == "__main__":
    main()
