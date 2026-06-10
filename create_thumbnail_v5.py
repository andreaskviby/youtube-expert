#!/usr/bin/env python3
"""
THUMBNAIL CREATOR V5 - No AI Background Stylization
Uses raw background frames to guarantee scene preservation.
Only applies color grading, not AI transformation.

💰 KOSTNAD: 0 kr - Använder BARA lokala verktyg (PIL, rembg)
   - Ingen OpenAI API
   - Ingen bildgenerering
   - Helt gratis att köra
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from rembg import remove
from io import BytesIO
import numpy as np

WIDTH = 1280
HEIGHT = 720
OUTPUT_DIR = Path("thumbnails_master")


def load_and_enhance_background(background_path: str) -> Image.Image:
    """Load background and apply STRONG painterly stylization (NO AI - uses PIL filters)"""

    print("   Step 1: Loading background with STRONG painterly effect...")

    bg = Image.open(background_path).convert("RGB")
    bg = bg.resize((WIDTH, HEIGHT), Image.LANCZOS)

    # Apply warm color grading
    r, g, b = bg.split()
    r = r.point(lambda x: min(255, int(x * 1.2)))  # Strong warm red
    g = g.point(lambda x: min(255, int(x * 1.05)))
    b = b.point(lambda x: int(x * 0.75))  # Strong blue reduction
    bg = Image.merge("RGB", (r, g, b))

    # POSTERIZE for painterly color blocks (fewer colors = more illustrated)
    from PIL import ImageOps
    bg = ImageOps.posterize(bg, 5)  # Reduce to 32 colors per channel

    # Increase saturation for vibrant colors
    bg = ImageEnhance.Color(bg).enhance(1.6)
    bg = ImageEnhance.Contrast(bg).enhance(1.2)

    # MEDIAN FILTER for oil painting effect (smooths while preserving edges)
    bg = bg.filter(ImageFilter.MedianFilter(size=5))

    # Multiple passes of smoothing + edge enhance
    for _ in range(3):
        bg = bg.filter(ImageFilter.GaussianBlur(radius=2))
        bg = bg.filter(ImageFilter.EDGE_ENHANCE_MORE)

    # Final smoothing
    bg = bg.filter(ImageFilter.GaussianBlur(radius=1.2))

    # Boost colors after filtering
    bg = ImageEnhance.Color(bg).enhance(1.3)

    # DARKEN background so subjects POP more
    bg = ImageEnhance.Brightness(bg).enhance(0.85)

    # Add vignette effect (darker edges, lighter center-left where subjects are)
    import numpy as np
    bg_array = np.array(bg, dtype=np.float32)

    # Create vignette mask - lighter on left, darker on right
    rows, cols = bg_array.shape[:2]
    X, Y = np.meshgrid(np.linspace(0, 1, cols), np.linspace(0, 1, rows))

    # Center the vignette slightly to the left where faces are
    center_x, center_y = 0.35, 0.5
    vignette = 1 - 0.4 * np.sqrt((X - center_x)**2 + (Y - center_y)**2)
    vignette = np.clip(vignette, 0.6, 1.0)

    # Apply vignette
    for i in range(3):
        bg_array[:, :, i] = bg_array[:, :, i] * vignette

    bg = Image.fromarray(np.clip(bg_array, 0, 255).astype(np.uint8))

    print("   ✅ Background with painterly effect + darkening applied")
    return bg


def extract_subjects(photo_path: str) -> Image.Image:
    """Extract subjects from photo"""

    print("   Step 2: Extracting subjects...")

    with open(photo_path, "rb") as f:
        subject_data = remove(f.read())

    subject = Image.open(BytesIO(subject_data)).convert("RGBA")

    print("   ✅ Subjects extracted")
    return subject


def composite_subjects(background: Image.Image, subjects: Image.Image) -> Image.Image:
    """Composite subjects onto background"""

    print("   Step 3: Compositing...")

    # Scale subjects
    target_width = int(WIDTH * 0.5)
    aspect = subjects.width / subjects.height
    target_height = int(target_width / aspect)

    if target_height > HEIGHT:
        target_height = HEIGHT
        target_width = int(target_height * aspect)

    subjects = subjects.resize((target_width, target_height), Image.LANCZOS)

    # Warm color grading on subjects
    subjects_rgb = subjects.convert("RGB")
    r, g, b = subjects_rgb.split()
    r = r.point(lambda x: min(255, int(x * 1.05)))
    b = b.point(lambda x: int(x * 0.92))
    subjects_rgb = Image.merge("RGB", (r, g, b))
    subjects_rgb = ImageEnhance.Color(subjects_rgb).enhance(1.1)

    # Get alpha and blur edges slightly
    alpha = subjects.split()[3]
    alpha = alpha.filter(ImageFilter.GaussianBlur(radius=2))

    # Gradient fade on right edge
    gradient = np.ones((target_height, target_width), dtype=np.float32) * 255
    fade_start = int(target_width * 0.75)
    for x in range(fade_start, target_width):
        progress = (x - fade_start) / (target_width - fade_start)
        gradient[:, x] = 255 * (1 - progress ** 2)

    alpha_array = np.array(alpha, dtype=np.float32)
    combined = (alpha_array * gradient / 255).astype(np.uint8)
    alpha_final = Image.fromarray(combined, mode="L")

    # Recombine
    subjects_rgba = subjects_rgb.convert("RGBA")
    subjects_rgba.putalpha(alpha_final)

    # Position
    x = -10
    y = HEIGHT - target_height

    # Composite
    composite = background.convert("RGBA")
    composite.paste(subjects_rgba, (x, y), subjects_rgba)

    print("   ✅ Composited")
    return composite.convert("RGB")


def add_text_overlay(image: Image.Image, title: str, episode: int) -> Image.Image:
    """Add text overlay"""

    print("   Step 4: Adding text...")

    draw = ImageDraw.Draw(image)

    font_size_title = 100
    font_size_badge = 48

    font_paths = [
        "/System/Library/Fonts/Supplemental/Impact.ttf",
        "/Library/Fonts/Impact.ttf",
    ]

    title_font = badge_font = None
    for fp in font_paths:
        if os.path.exists(fp):
            title_font = ImageFont.truetype(fp, font_size_title)
            badge_font = ImageFont.truetype(fp, font_size_badge)
            break

    if not title_font:
        title_font = ImageFont.load_default()
        badge_font = ImageFont.load_default()

    def draw_outlined_text(x, y, text, font, outline_width=8):
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if abs(dx) + abs(dy) <= outline_width + 2:
                    draw.text((x + dx, y + dy), text, font=font, fill="black")
        draw.text((x, y), text, font=font, fill="white")

    # Title
    title_text = title.upper()
    bbox = draw.textbbox((0, 0), title_text, font=title_font)
    w = bbox[2] - bbox[0]
    x = (WIDTH - w) // 2 - 40
    draw_outlined_text(x, 20, title_text, title_font)

    # Badge
    badge_x = WIDTH - 90
    badge_y = 60
    badge_radius = 45

    draw.ellipse(
        [badge_x - badge_radius + 3, badge_y - badge_radius + 3,
         badge_x + badge_radius + 3, badge_y + badge_radius + 3],
        fill="#00000066"
    )
    draw.ellipse(
        [badge_x - badge_radius, badge_y - badge_radius,
         badge_x + badge_radius, badge_y + badge_radius],
        fill="#D32F2F"
    )

    badge_text = f"#{episode}"
    bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
    bw = bbox[2] - bbox[0]
    bh = bbox[3] - bbox[1]
    draw.text((badge_x - bw // 2, badge_y - bh // 2 - 3), badge_text, font=badge_font, fill="white")

    print("   ✅ Text added")
    return image


def create_thumbnail_v5(episode: int, title: str, subject_photo: str, background: str) -> Path:
    """Create thumbnail WITHOUT AI background stylization"""

    print(f"\n{'='*60}")
    print(f"THUMBNAIL V5 - No AI Background")
    print(f"Episode #{episode}: {title}")
    print(f"{'='*60}\n")

    OUTPUT_DIR.mkdir(exist_ok=True)

    subject_path = Path("SOURCES") / subject_photo
    if not subject_path.exists():
        subject_path = Path("SOURCES_compressed") / subject_photo.replace(".png", ".jpg")

    # Load background (no AI)
    bg = load_and_enhance_background(background)

    # Extract subjects
    subjects = extract_subjects(str(subject_path))

    # Composite
    composite = composite_subjects(bg, subjects)

    # Add text
    final = add_text_overlay(composite, title, episode)

    # Save
    safe_title = title.lower().replace(' ', '_').replace('?', '').replace('!', '')
    output_path = OUTPUT_DIR / f"ep{episode}_{safe_title}.png"
    final.save(output_path, "PNG")

    print(f"\n{'='*60}")
    print(f"✅ DONE: {output_path}")
    print(f"{'='*60}")

    return output_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode", "-e", type=int, required=True)
    parser.add_argument("--title", "-t", type=str, required=True)
    parser.add_argument("--photo", "-p", type=str, required=True)
    parser.add_argument("--background", "-b", type=str, required=True)
    args = parser.parse_args()

    create_thumbnail_v5(args.episode, args.title, args.photo, args.background)
