#!/usr/bin/env python3
"""
Professional YouTube Thumbnail Workflow
Creates thumbnails using real photos + actual episode frames as backgrounds
Following the THUMBNAIL_STYLE_GUIDE.md rules
"""

import os
import subprocess
import base64
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from io import BytesIO
import requests

# Configuration
THUMBNAIL_WIDTH = 1280
THUMBNAIL_HEIGHT = 720
SAFE_MARGIN_H = 102  # 8% horizontal margin
SAFE_MARGIN_V = 72   # 10% vertical margin

# Episode badge settings
BADGE_SIZE = 90
BADGE_MARGIN = 25
BADGE_COLOR = (220, 53, 69)  # Red
BADGE_TEXT_COLOR = (255, 255, 255)

# Text settings
TEXT_COLORS = {
    "drama": ((255, 0, 0), (0, 0, 0)),        # Red with black outline
    "celebration": ((255, 215, 0), (0, 0, 0)), # Gold with black outline
    "adventure": ((255, 255, 255), (0, 100, 200)), # White with blue shadow
    "cooking": ((255, 215, 0), (0, 0, 0)),    # Gold with black outline
    "nature": ((255, 255, 255), (34, 139, 34)), # White with green shadow
    "default": ((255, 255, 255), (0, 0, 0))   # White with black outline
}


class ThumbnailCreator:
    def __init__(self, output_dir: str = "thumbnails_pro"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.sources_dir = Path("SOURCES")
        self.frames_dir = Path("episode_frames")
        self.frames_dir.mkdir(exist_ok=True)

    def extract_frame_from_video(self, video_path: str, timestamp: str, output_name: str) -> Path:
        """Extract a frame from a video file at specified timestamp"""
        output_path = self.frames_dir / f"{output_name}.png"

        cmd = [
            "ffmpeg", "-y",
            "-ss", timestamp,
            "-i", video_path,
            "-frames:v", "1",
            "-q:v", "1",
            str(output_path)
        ]

        subprocess.run(cmd, capture_output=True)
        print(f"   Extracted frame: {output_path}")
        return output_path

    def download_youtube_frame(self, video_url: str, timestamp: str, output_name: str) -> Path:
        """Download a YouTube video and extract a frame"""
        output_path = self.frames_dir / f"{output_name}.png"

        # First download the video
        temp_video = self.frames_dir / "temp_video.mp4"

        print(f"   Downloading video segment...")
        cmd = [
            "yt-dlp",
            "-f", "best[height<=720]",
            "--download-sections", f"*{timestamp}-{timestamp}",
            "-o", str(temp_video),
            video_url
        ]

        try:
            subprocess.run(cmd, capture_output=True, timeout=60)

            # Extract frame
            if temp_video.exists():
                self.extract_frame_from_video(str(temp_video), "00:00:01", output_name)
                temp_video.unlink()  # Clean up
        except Exception as e:
            print(f"   Warning: Could not download video: {e}")
            return None

        return output_path if output_path.exists() else None

    def remove_background(self, image_path: Path) -> Image.Image:
        """Remove background from image using rembg or return original with instructions"""
        try:
            from rembg import remove
            with open(image_path, "rb") as f:
                input_data = f.read()
            output_data = remove(input_data)
            return Image.open(BytesIO(output_data)).convert("RGBA")
        except ImportError:
            print("   Note: Install rembg for auto background removal: pip install rembg")
            print("   Using original image - manually remove background with remove.bg")
            return Image.open(image_path).convert("RGBA")

    def create_episode_badge(self, episode_num: int, color: tuple = None) -> Image.Image:
        """Create a circular episode number badge"""
        badge = Image.new("RGBA", (BADGE_SIZE, BADGE_SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(badge)

        # Draw circle
        badge_color = color or BADGE_COLOR
        draw.ellipse([0, 0, BADGE_SIZE-1, BADGE_SIZE-1], fill=badge_color)

        # Add text
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
        except:
            font = ImageFont.load_default()

        text = f"#{episode_num}"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (BADGE_SIZE - text_width) // 2
        y = (BADGE_SIZE - text_height) // 2 - 5

        draw.text((x, y), text, font=font, fill=BADGE_TEXT_COLOR)

        return badge

    def add_text_with_outline(self, image: Image.Image, text: str, position: str,
                               text_color: tuple, outline_color: tuple,
                               font_size: int = 72, outline_width: int = 5) -> Image.Image:
        """Add text with outline, respecting safe zones"""
        draw = ImageDraw.Draw(image)

        # Try to load a bold font
        font = None
        font_paths = [
            "/System/Library/Fonts/Supplemental/Impact.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial Bold.ttf",
        ]

        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except:
                continue

        if not font:
            font = ImageFont.load_default()

        # Calculate text size
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Position based on preference (respecting safe zones)
        if position == "top-left":
            x = SAFE_MARGIN_H + 20
            y = SAFE_MARGIN_V + 10
        elif position == "top-center":
            x = (THUMBNAIL_WIDTH - text_width) // 2
            y = SAFE_MARGIN_V + 10
        elif position == "bottom-left":
            x = SAFE_MARGIN_H + 20
            y = THUMBNAIL_HEIGHT - SAFE_MARGIN_V - text_height - 20
        elif position == "center":
            x = (THUMBNAIL_WIDTH - text_width) // 2
            y = (THUMBNAIL_HEIGHT - text_height) // 2
        else:
            x = SAFE_MARGIN_H + 20
            y = SAFE_MARGIN_V + 10

        # Draw outline
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), text, font=font, fill=outline_color)

        # Draw main text
        draw.text((x, y), text, font=font, fill=text_color)

        return image

    def create_thumbnail(
        self,
        subject_photo: str,
        background_image: str,
        title_text: str,
        episode_num: int,
        theme: str = "default",
        text_position: str = "top-left",
        output_name: str = None
    ) -> Path:
        """
        Create a professional thumbnail

        Args:
            subject_photo: Path to photo with people (from SOURCES folder)
            background_image: Path to background image (from episode frame)
            title_text: The title text (max 5 words)
            episode_num: Episode number for badge
            theme: Color theme (drama, celebration, adventure, cooking, nature, default)
            text_position: Where to place text (top-left, top-center, bottom-left, center)
            output_name: Output filename
        """
        print(f"\n{'='*60}")
        print(f"Creating: {output_name or title_text}")
        print(f"{'='*60}")

        # Load background
        print(f"   Loading background: {background_image}")
        if background_image and Path(background_image).exists():
            background = Image.open(background_image).convert("RGB")
            background = background.resize((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.LANCZOS)
            # Slightly darken/blur background to make subjects pop
            enhancer = ImageEnhance.Brightness(background)
            background = enhancer.enhance(0.85)
        else:
            # Create gradient background if no image
            background = Image.new("RGB", (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), (40, 40, 60))

        # Load and process subject photo
        subject_path = self.sources_dir / subject_photo
        if subject_path.exists():
            print(f"   Loading subject: {subject_photo}")
            subject = Image.open(subject_path).convert("RGBA")

            # Scale subject to fit (about 60% of height)
            target_height = int(THUMBNAIL_HEIGHT * 0.75)
            aspect = subject.width / subject.height
            target_width = int(target_height * aspect)
            subject = subject.resize((target_width, target_height), Image.LANCZOS)

            # Position subject on left third
            subject_x = 50
            subject_y = THUMBNAIL_HEIGHT - target_height

            # Composite subject onto background
            background = background.convert("RGBA")
            background.paste(subject, (subject_x, subject_y), subject)
            background = background.convert("RGB")

        # Get colors for theme
        text_color, outline_color = TEXT_COLORS.get(theme, TEXT_COLORS["default"])

        # Add title text
        print(f"   Adding text: {title_text}")
        thumbnail = self.add_text_with_outline(
            background.convert("RGBA"),
            title_text.upper(),
            text_position,
            text_color,
            outline_color,
            font_size=68,
            outline_width=5
        )

        # Add episode badge (top-right, inside safe zone)
        badge = self.create_episode_badge(episode_num)
        badge_x = THUMBNAIL_WIDTH - BADGE_SIZE - BADGE_MARGIN - SAFE_MARGIN_H
        badge_y = SAFE_MARGIN_V + BADGE_MARGIN
        thumbnail.paste(badge, (badge_x, badge_y), badge)

        # Save
        output_name = output_name or f"thumbnail_{episode_num}_{title_text.replace(' ', '_').lower()[:20]}.png"
        output_path = self.output_dir / output_name

        # Convert to RGB for saving
        final = thumbnail.convert("RGB")
        final.save(output_path, "PNG", optimize=True)

        # Check file size
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"   Saved: {output_path} ({size_mb:.1f} MB)")

        if size_mb > 2:
            print(f"   Warning: File exceeds 2MB limit, compressing...")
            final.save(output_path, "JPEG", quality=85, optimize=True)
            size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"   Compressed: {size_mb:.1f} MB")

        return output_path


def main():
    """Demo: Create thumbnails with proper workflow"""
    creator = ThumbnailCreator()

    print("="*70)
    print("PROFESSIONAL THUMBNAIL CREATOR")
    print("Following THUMBNAIL_STYLE_GUIDE.md")
    print("="*70)

    # Example thumbnails to create
    thumbnails = [
        {
            "subject_photo": "IMG_5750.png",
            "background_image": None,  # Will use subject as both
            "title_text": "HE JUST WALKED IN",
            "episode_num": 33,
            "theme": "drama",
            "text_position": "top-left",
            "output_name": "thumb_33_church.png"
        },
        {
            "subject_photo": "IMG_4614.png",
            "background_image": None,
            "title_text": "I ALMOST GAVE UP",
            "episode_num": 35,
            "theme": "adventure",
            "text_position": "top-left",
            "output_name": "thumb_35_climb.png"
        },
        {
            "subject_photo": "IMG_5857.png",
            "background_image": None,
            "title_text": "25K CELEBRATION",
            "episode_num": 25,
            "theme": "celebration",
            "text_position": "top-center",
            "output_name": "thumb_25k_celebration.png"
        },
    ]

    for thumb in thumbnails:
        creator.create_thumbnail(**thumb)

    print("\n" + "="*70)
    print("DONE!")
    print("="*70)
    print(f"\nThumbnails saved to: {creator.output_dir.absolute()}")


if __name__ == "__main__":
    main()
