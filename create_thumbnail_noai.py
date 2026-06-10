#!/usr/bin/env python3
"""
NO-AI THUMBNAIL CREATOR
Uses ONLY PIL - no AI modifications to preserve exact body proportions
Just adds text overlay and slight color enhancement
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

WIDTH = 1280
HEIGHT = 720
OUTPUT_DIR = Path("thumbnails_noai")
OUTPUT_DIR.mkdir(exist_ok=True)


def enhance_image(image: Image.Image) -> Image.Image:
    """Apply subtle enhancements with PIL only - NO AI"""
    img = image.copy()

    # Slight color boost
    img = ImageEnhance.Color(img).enhance(1.15)

    # Slight contrast boost
    img = ImageEnhance.Contrast(img).enhance(1.1)

    # Slight saturation for thumbnail pop
    img = ImageEnhance.Brightness(img).enhance(1.02)

    return img


def add_text_overlay(image: Image.Image, line1: str, line2: str, episode: int) -> Image.Image:
    """Add text with exact control"""

    img = image.copy()
    draw = ImageDraw.Draw(img)

    # Load Impact font
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Impact.ttf", 64)
        badge_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Impact.ttf", 40)
    except:
        title_font = ImageFont.load_default()
        badge_font = ImageFont.load_default()

    margin = 50

    def draw_text_with_outline(text, x, y, font, fill="#FFFDE7", outline="black", width=4):
        for dx in range(-width, width + 1):
            for dy in range(-width, width + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), text, font=font, fill=outline)
        draw.text((x, y), text, font=font, fill=fill)

    # Calculate positions
    bbox1 = draw.textbbox((0, 0), line1.upper(), font=title_font)
    bbox2 = draw.textbbox((0, 0), line2.upper(), font=title_font)

    w1, h1 = bbox1[2] - bbox1[0], bbox1[3] - bbox1[1]
    w2, h2 = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]

    y1 = margin
    y2 = y1 + h1 + 8

    x1 = (WIDTH - w1) // 2
    x2 = (WIDTH - w2) // 2

    draw_text_with_outline(line1.upper(), x1, y1, title_font)
    draw_text_with_outline(line2.upper(), x2, y2, title_font)

    # Episode badge
    badge_r = 40
    badge_x = WIDTH - margin - badge_r
    badge_y = margin + badge_r

    draw.ellipse(
        [badge_x - badge_r, badge_y - badge_r, badge_x + badge_r, badge_y + badge_r],
        fill="#C0392B"
    )

    badge_text = f"#{episode}"
    bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((badge_x - tw//2, badge_y - th//2 - 3), badge_text, font=badge_font, fill="white")

    return img


def create_thumbnail(
    episode: int,
    line1: str,
    line2: str,
    source_thumbnail: str
) -> Path:
    """Create thumbnail without any AI - preserves exact appearance"""

    print(f"\n{'='*60}")
    print(f"NO-AI THUMBNAIL - Episode #{episode}")
    print(f"{'='*60}")

    # Load and resize
    img = Image.open(source_thumbnail).convert("RGB")
    img = img.resize((WIDTH, HEIGHT), Image.LANCZOS)

    # Subtle enhancement (PIL only)
    print("   Enhancing colors (PIL only, no AI)...")
    img = enhance_image(img)

    # Add text
    print("   Adding text overlay...")
    img = add_text_overlay(img, line1, line2, episode)

    # Save
    safe_name = f"ep{episode}_noai.png"
    output_path = OUTPUT_DIR / safe_name
    img.save(output_path, "PNG")

    print(f"   ✅ Saved: {output_path}")
    return output_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 5:
        print("Usage: python create_thumbnail_noai.py <episode> <line1> <line2> <source>")
        sys.exit(1)

    result = create_thumbnail(
        episode=int(sys.argv[1]),
        line1=sys.argv[2],
        line2=sys.argv[3],
        source_thumbnail=sys.argv[4]
    )

    import subprocess
    subprocess.run(["open", str(result)])
