#!/usr/bin/env python3
"""
Perfect YouTube Thumbnail Creator
- Uses real photos with background removal
- Real episode frames as backgrounds
- Proper safe zones and text placement
- Consistent styling per THUMBNAIL_STYLE_GUIDE.md
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from rembg import remove
from io import BytesIO

# Constants from style guide
THUMBNAIL_WIDTH = 1280
THUMBNAIL_HEIGHT = 720
SAFE_MARGIN_H = 102  # 8% horizontal
SAFE_MARGIN_V = 72   # 10% vertical

# Badge settings (consistent across all thumbnails)
BADGE_SIZE = 80
BADGE_MARGIN = 25
BADGE_BG_COLOR = (220, 53, 69)  # YouTube red

# Text settings
TITLE_FONT_SIZE = 72
TITLE_OUTLINE_WIDTH = 6


def load_font(size: int) -> ImageFont.FreeTypeFont:
    """Load a bold font, with fallbacks"""
    font_paths = [
        "/System/Library/Fonts/Supplemental/Impact.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/SFNSDisplay.ttf",
    ]

    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue

    return ImageFont.load_default()


def remove_background(image_path: Path) -> Image.Image:
    """Remove background from image using rembg"""
    print(f"   Removing background from {image_path.name}...")

    with open(image_path, "rb") as f:
        input_data = f.read()

    output_data = remove(input_data)
    img = Image.open(BytesIO(output_data)).convert("RGBA")

    print(f"   Background removed successfully")
    return img


def create_episode_badge(episode_num: int) -> Image.Image:
    """Create consistent episode number badge"""
    badge = Image.new("RGBA", (BADGE_SIZE, BADGE_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(badge)

    # Draw circle
    draw.ellipse([0, 0, BADGE_SIZE-1, BADGE_SIZE-1], fill=BADGE_BG_COLOR)

    # Add text
    font = load_font(32)
    text = f"#{episode_num}"

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (BADGE_SIZE - text_width) // 2
    y = (BADGE_SIZE - text_height) // 2 - 3

    draw.text((x, y), text, font=font, fill=(255, 255, 255))

    return badge


def draw_text_with_outline(
    draw: ImageDraw.ImageDraw,
    text: str,
    position: tuple,
    font: ImageFont.FreeTypeFont,
    fill_color: tuple,
    outline_color: tuple,
    outline_width: int
):
    """Draw text with outline for visibility"""
    x, y = position

    # Draw outline
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)

    # Draw main text
    draw.text((x, y), text, font=font, fill=fill_color)


def create_thumbnail(
    subject_photo_path: str,
    background_path: str,
    title_text: str,
    episode_num: int,
    output_path: str,
    text_color: tuple = (255, 255, 255),
    outline_color: tuple = (0, 0, 0),
    subject_scale: float = 0.85,
    subject_position: str = "left"  # left, center, right
) -> Path:
    """
    Create a professional YouTube thumbnail

    Args:
        subject_photo_path: Path to photo of you (will have bg removed)
        background_path: Path to episode frame for background
        title_text: The title (max 5 words, will be uppercased)
        episode_num: Episode number for badge
        output_path: Where to save the thumbnail
        text_color: Main text color (RGB)
        outline_color: Text outline color (RGB)
        subject_scale: How much of the height the subjects should take (0.0-1.0)
        subject_position: Where to place subjects (left/center/right)
    """
    print(f"\n{'='*60}")
    print(f"Creating thumbnail: {title_text}")
    print(f"{'='*60}")

    # 1. Load and prepare background
    print(f"   Loading background: {background_path}")
    background = Image.open(background_path).convert("RGB")
    background = background.resize((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.LANCZOS)

    # Darken background slightly so subjects pop
    enhancer = ImageEnhance.Brightness(background)
    background = enhancer.enhance(0.7)

    # Optional: add slight blur to background
    background = background.filter(ImageFilter.GaussianBlur(radius=2))

    # Convert to RGBA for compositing
    thumbnail = background.convert("RGBA")

    # 2. Load subject and remove background
    subject = remove_background(Path(subject_photo_path))

    # Scale subject to fit
    target_height = int(THUMBNAIL_HEIGHT * subject_scale)
    aspect = subject.width / subject.height
    target_width = int(target_height * aspect)

    # Make sure subject doesn't exceed width
    if target_width > THUMBNAIL_WIDTH * 0.7:
        target_width = int(THUMBNAIL_WIDTH * 0.7)
        target_height = int(target_width / aspect)

    subject = subject.resize((target_width, target_height), Image.LANCZOS)

    # Position subject
    if subject_position == "left":
        subject_x = 20
    elif subject_position == "center":
        subject_x = (THUMBNAIL_WIDTH - target_width) // 2
    else:  # right
        subject_x = THUMBNAIL_WIDTH - target_width - 20

    subject_y = THUMBNAIL_HEIGHT - target_height

    # Composite subject onto background
    thumbnail.paste(subject, (subject_x, subject_y), subject)

    # 3. Add title text (top-left, inside safe zone)
    draw = ImageDraw.Draw(thumbnail)
    font = load_font(TITLE_FONT_SIZE)

    title_upper = title_text.upper()

    # Calculate text position (top-left safe zone)
    text_x = SAFE_MARGIN_H + 10
    text_y = SAFE_MARGIN_V + 10

    # Check if text fits, reduce font size if needed
    bbox = draw.textbbox((0, 0), title_upper, font=font)
    text_width = bbox[2] - bbox[0]
    max_text_width = THUMBNAIL_WIDTH - (2 * SAFE_MARGIN_H) - BADGE_SIZE - 50

    while text_width > max_text_width and TITLE_FONT_SIZE > 40:
        font = load_font(int(font.size * 0.9))
        bbox = draw.textbbox((0, 0), title_upper, font=font)
        text_width = bbox[2] - bbox[0]

    draw_text_with_outline(
        draw,
        title_upper,
        (text_x, text_y),
        font,
        text_color,
        outline_color,
        TITLE_OUTLINE_WIDTH
    )

    # 4. Add episode badge (top-right, inside safe zone)
    badge = create_episode_badge(episode_num)
    badge_x = THUMBNAIL_WIDTH - BADGE_SIZE - SAFE_MARGIN_H - BADGE_MARGIN
    badge_y = SAFE_MARGIN_V + BADGE_MARGIN
    thumbnail.paste(badge, (badge_x, badge_y), badge)

    # 5. Save
    output = Path(output_path)
    output.parent.mkdir(exist_ok=True)

    # Convert to RGB for saving
    final = thumbnail.convert("RGB")
    final.save(output, "PNG", optimize=True)

    size_mb = output.stat().st_size / (1024 * 1024)
    print(f"\n   ✅ Saved: {output}")
    print(f"   Size: {size_mb:.2f} MB")

    # Compress if too large
    if size_mb > 2:
        print(f"   Compressing (>2MB)...")
        final.save(output, "JPEG", quality=85, optimize=True)
        size_mb = output.stat().st_size / (1024 * 1024)
        print(f"   New size: {size_mb:.2f} MB")

    return output


def main():
    """Create sample thumbnail for episode #33"""

    print("="*70)
    print("PERFECT THUMBNAIL CREATOR")
    print("="*70)

    # Paths
    subject_photo = "SOURCES/IMG_5857.png"  # The celebration photo
    background = "episode_frames/ep33_background.png"
    output = "thumbnails_perfect/ep33_he_just_walked_in.png"

    # Create thumbnail
    create_thumbnail(
        subject_photo_path=subject_photo,
        background_path=background,
        title_text="He Just Walked In",
        episode_num=33,
        output_path=output,
        text_color=(255, 255, 255),  # White
        outline_color=(0, 0, 0),     # Black outline
        subject_scale=0.80,
        subject_position="left"
    )

    print("\n" + "="*70)
    print("DONE!")
    print("="*70)


if __name__ == "__main__":
    main()
