#!/usr/bin/env python3
"""
Build script for Adventure in Sicily website
Generates static pages from YouTube data
"""

import json
import re
import os
from pathlib import Path

SRC_DIR = Path("adventure-website/src")
PUBLIC_DIR = Path("adventure-website/public")

def create_slug(title):
    """Create URL-friendly slug from title"""
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug[:50]

def load_data():
    """Load channel data"""
    with open(SRC_DIR / "channel_data.json") as f:
        return json.load(f)

def generate_data_js(data):
    """Generate JavaScript data file"""
    js_content = f"""// Auto-generated video data
window.CHANNEL = {json.dumps(data['channel'])};
window.VIDEOS = {json.dumps(data['videos'])};
"""
    with open(PUBLIC_DIR / "data.js", "w") as f:
        f.write(js_content)
    print(f"Generated data.js with {len(data['videos'])} videos")

def generate_episode_pages(data):
    """Generate individual episode pages"""
    episodes_dir = PUBLIC_DIR / "episodes"
    episodes_dir.mkdir(exist_ok=True)

    template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Adventure in Sicily</title>
    <meta name="description" content="{description}">
    <link rel="canonical" href="https://adventureinsicily.com/episodes/{slug}/">

    <!-- Video Schema -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "VideoObject",
        "name": "{title_escaped}",
        "description": "{description_escaped}",
        "thumbnailUrl": "{thumbnail}",
        "uploadDate": "{published}",
        "embedUrl": "https://www.youtube.com/embed/{video_id}",
        "publisher": {{
            "@type": "Organization",
            "name": "We Bought an Adventure in Sicily",
            "url": "https://adventureinsicily.com"
        }}
    }}
    </script>

    <link rel="stylesheet" href="/styles.css">
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <a href="/" class="logo">Adventure in Sicily</a>
            <ul class="nav-links">
                <li><a href="/">Home</a></li>
                <li><a href="/episodes/">Episodes</a></li>
                <li><a href="/about/">About Us</a></li>
                <li><a href="https://www.youtube.com/@weboughtanadventureinsicily?sub_confirmation=1" class="btn-subscribe" target="_blank">Subscribe</a></li>
            </ul>
        </div>
    </nav>

    <section class="episode-page">
        <div class="episode-container">
            <div class="video-embed">
                <iframe
                    src="https://www.youtube.com/embed/{video_id}"
                    title="{title_escaped}"
                    frameborder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowfullscreen>
                </iframe>
            </div>

            <h1 class="episode-title">{title}</h1>

            <div class="episode-meta">
                <span>Published: {published_formatted}</span>
            </div>

            <div class="episode-description">
                <p>{description_html}</p>
            </div>

            <a href="https://www.youtube.com/watch?v={video_id}" class="watch-youtube" target="_blank">
                Watch on YouTube
            </a>
        </div>
    </section>

    <footer class="footer">
        <div class="container">
            <div class="footer-bottom">
                <p>&copy; 2026 Adventure in Sicily. All rights reserved.</p>
            </div>
        </div>
    </footer>
</body>
</html>'''

    for video in data['videos']:
        slug = create_slug(video['title'])
        episode_dir = episodes_dir / slug
        episode_dir.mkdir(exist_ok=True)

        # Format date
        from datetime import datetime
        published = datetime.fromisoformat(video['published'].replace('Z', '+00:00'))
        published_formatted = published.strftime('%B %d, %Y')

        # Escape for JSON and HTML
        title_escaped = video['title'].replace('"', '\\"').replace('<', '&lt;').replace('>', '&gt;')
        description_escaped = video['description'][:200].replace('"', '\\"').replace('\n', ' ')
        description_html = video['description'].replace('\n', '<br>')

        html = template.format(
            title=video['title'],
            title_escaped=title_escaped,
            description=video['description'][:160],
            description_escaped=description_escaped,
            description_html=description_html,
            slug=slug,
            video_id=video['id'],
            thumbnail=video['thumbnail'],
            published=video['published'],
            published_formatted=published_formatted
        )

        with open(episode_dir / "index.html", "w") as f:
            f.write(html)

    print(f"Generated {len(data['videos'])} episode pages")

def generate_sitemap(data):
    """Generate sitemap.xml"""
    urls = [
        'https://adventureinsicily.com/',
        'https://adventureinsicily.com/episodes/',
        'https://adventureinsicily.com/about/',
        'https://adventureinsicily.com/sicily-guide/',
    ]

    for video in data['videos']:
        slug = create_slug(video['title'])
        urls.append(f'https://adventureinsicily.com/episodes/{slug}/')

    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    for url in urls:
        sitemap += f'  <url><loc>{url}</loc></url>\n'

    sitemap += '</urlset>'

    with open(PUBLIC_DIR / "sitemap.xml", "w") as f:
        f.write(sitemap)

    print(f"Generated sitemap.xml with {len(urls)} URLs")

def generate_robots_txt():
    """Generate robots.txt"""
    robots = """User-agent: *
Allow: /

Sitemap: https://adventureinsicily.com/sitemap.xml
"""
    with open(PUBLIC_DIR / "robots.txt", "w") as f:
        f.write(robots)
    print("Generated robots.txt")

def main():
    print("=" * 50)
    print("Building Adventure in Sicily website")
    print("=" * 50)

    data = load_data()
    generate_data_js(data)
    generate_episode_pages(data)
    generate_sitemap(data)
    generate_robots_txt()

    print("\n" + "=" * 50)
    print("Build complete!")
    print(f"Output: {PUBLIC_DIR}")
    print("=" * 50)

if __name__ == "__main__":
    main()
