#!/usr/bin/env python3
"""
Build script for Adventure in Sicily website
Generates static pages from YouTube data
"""

import json
import re
import os
from pathlib import Path

# Resolve paths relative to this script's location so the build works
# regardless of the current working directory (repo root or adventure-website/).
_BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = _BASE_DIR / "src"
PUBLIC_DIR = _BASE_DIR / "public"

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
    """Generate JavaScript data file with sorted arrays"""
    videos = data['videos']

    # Sort by date (newest first)
    videos_by_date = sorted(videos, key=lambda x: x.get('published', ''), reverse=True)

    # Sort by views (most popular first)
    videos_by_popularity = sorted(videos, key=lambda x: x.get('views', 0), reverse=True)

    js_content = f"""// Auto-generated video data
window.CHANNEL = {json.dumps(data['channel'])};
window.VIDEOS_BY_DATE = {json.dumps(videos_by_date)};
window.VIDEOS_BY_POPULARITY = {json.dumps(videos_by_popularity)};
"""
    with open(PUBLIC_DIR / "data.js", "w") as f:
        f.write(js_content)
    print(f"Generated data.js with {len(videos)} videos (sorted by date and popularity)")

def generate_episode_pages(data):
    """Generate individual episode pages"""
    episodes_dir = PUBLIC_DIR / "episodes"
    episodes_dir.mkdir(exist_ok=True)

    template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Adventure in Sicily | Sicily Expat Vlog</title>
    <meta name="description" content="{description}">
    <meta name="keywords" content="Sicily, Italy, {title}, expat life, Italian vlog, Sicilian adventure">
    <link rel="canonical" href="https://adventureinsicily.com/episodes/{slug}/">

    <!-- Geo Meta -->
    <meta name="geo.region" content="IT-82">
    <meta name="geo.placename" content="Sicily, Italy">

    <!-- Open Graph Video -->
    <meta property="og:type" content="video.other">
    <meta property="og:url" content="https://adventureinsicily.com/episodes/{slug}/">
    <meta property="og:title" content="{title_escaped}">
    <meta property="og:description" content="{description_escaped}">
    <meta property="og:image" content="{thumbnail}">
    <meta property="og:video" content="https://www.youtube.com/embed/{video_id}">
    <meta property="og:video:type" content="text/html">
    <meta property="og:video:width" content="1280">
    <meta property="og:video:height" content="720">
    <meta property="og:site_name" content="Adventure in Sicily">

    <!-- Twitter Card -->
    <meta name="twitter:card" content="player">
    <meta name="twitter:title" content="{title_escaped}">
    <meta name="twitter:description" content="{description_escaped}">
    <meta name="twitter:image" content="{thumbnail}">
    <meta name="twitter:player" content="https://www.youtube.com/embed/{video_id}">
    <meta name="twitter:player:width" content="1280">
    <meta name="twitter:player:height" content="720">

    <meta name="robots" content="index, follow, max-image-preview:large, max-video-preview:-1">

    <!-- Video Schema -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "VideoObject",
        "name": "{title_escaped}",
        "description": "{description_escaped}",
        "thumbnailUrl": "{thumbnail}",
        "uploadDate": "{published}",
        "duration": "PT10M",
        "embedUrl": "https://www.youtube.com/embed/{video_id}",
        "contentUrl": "https://www.youtube.com/watch?v={video_id}",
        "interactionStatistic": {{
            "@type": "InteractionCounter",
            "interactionType": "https://schema.org/WatchAction",
            "userInteractionCount": {views}
        }},
        "publisher": {{
            "@type": "Organization",
            "name": "We Bought an Adventure in Sicily",
            "url": "https://adventureinsicily.com",
            "logo": "https://adventureinsicily.com/logo.jpg"
        }},
        "author": {{
            "@type": "Person",
            "name": "Andreas Kviby"
        }}
    }}
    </script>

    <!-- BreadcrumbList Schema -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://adventureinsicily.com/"}},
            {{"@type": "ListItem", "position": 2, "name": "Episodes", "item": "https://adventureinsicily.com/episodes/"}},
            {{"@type": "ListItem", "position": 3, "name": "{title_escaped}"}}
        ]
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
            description=video['description'][:160] if video['description'] else video['title'],
            description_escaped=description_escaped,
            description_html=description_html,
            slug=slug,
            video_id=video['id'],
            thumbnail=video['thumbnail'],
            published=video['published'],
            published_formatted=published_formatted,
            views=video.get('views', 0)
        )

        with open(episode_dir / "index.html", "w") as f:
            f.write(html)

    print(f"Generated {len(data['videos'])} episode pages")

def generate_sitemap(data):
    """Generate enhanced sitemap.xml with lastmod, changefreq, priority"""
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')

    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    # Main pages with high priority
    main_pages = [
        ('https://adventureinsicily.com/', '1.0', 'daily'),
        ('https://adventureinsicily.com/episodes/', '0.9', 'daily'),
        ('https://adventureinsicily.com/about/', '0.7', 'monthly'),
        ('https://adventureinsicily.com/sicily-guide/', '0.8', 'weekly'),
        ('https://adventureinsicily.com/sicily-guide/restaurants/', '0.7', 'weekly'),
        ('https://adventureinsicily.com/sicily-guide/beaches/', '0.7', 'weekly'),
        ('https://adventureinsicily.com/sicily-guide/hotels/', '0.7', 'weekly'),
        ('https://adventureinsicily.com/sicily-guide/stories/', '0.7', 'weekly'),
    ]

    # Auto-discover individual guide detail pages (each is its own indexable URL)
    for section in ("beaches", "restaurants", "hotels"):
        section_dir = PUBLIC_DIR / "sicily-guide" / section
        if section_dir.is_dir():
            for child in sorted(section_dir.iterdir()):
                if child.is_dir() and (child / "index.html").exists():
                    main_pages.append((
                        f'https://adventureinsicily.com/sicily-guide/{section}/{child.name}/',
                        '0.6', 'monthly'
                    ))

    for url, priority, freq in main_pages:
        sitemap += f'''  <url>
    <loc>{url}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>{freq}</changefreq>
    <priority>{priority}</priority>
  </url>\n'''

    # Episode pages with dates
    for video in data['videos']:
        slug = create_slug(video['title'])
        published = video['published'][:10] if video.get('published') else today
        sitemap += f'''  <url>
    <loc>https://adventureinsicily.com/episodes/{slug}/</loc>
    <lastmod>{published}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>\n'''

    sitemap += '</urlset>'

    with open(PUBLIC_DIR / "sitemap.xml", "w") as f:
        f.write(sitemap)

    print(f"Generated sitemap.xml with {len(main_pages) + len(data['videos'])} URLs")

    # Generate video sitemap for Google
    generate_video_sitemap(data)


def generate_video_sitemap(data):
    """Generate video sitemap for better YouTube/Google indexing"""
    from html import escape
    import re

    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
    sitemap += '        xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">\n'

    for video in data['videos']:
        slug = create_slug(video['title'])

        # Clean and escape title
        title_clean = re.sub(r'[^\w\s\-.,!?\'\"()]', '', video['title'])
        title_escaped = escape(title_clean) if title_clean else "Sicily Adventure Video"

        # Always have a description - use title if empty
        desc_raw = video.get('description', '') or video['title']
        desc_clean = re.sub(r'[^\w\s\-.,!?\'\"()]', ' ', desc_raw[:200])
        desc_escaped = escape(desc_clean.strip()) if desc_clean.strip() else title_escaped

        sitemap += f'''  <url>
    <loc>https://adventureinsicily.com/episodes/{slug}/</loc>
    <video:video>
      <video:thumbnail_loc>{video['thumbnail']}</video:thumbnail_loc>
      <video:title>{title_escaped}</video:title>
      <video:description>{desc_escaped}</video:description>
      <video:player_loc allow_embed="yes">https://www.youtube.com/embed/{video['id']}</video:player_loc>
      <video:publication_date>{video['published']}</video:publication_date>
      <video:family_friendly>yes</video:family_friendly>
    </video:video>
  </url>\n'''

    sitemap += '</urlset>'

    with open(PUBLIC_DIR / "sitemap-videos.xml", "w") as f:
        f.write(sitemap)

    print(f"Generated sitemap-videos.xml with {len(data['videos'])} videos")

def generate_robots_txt():
    """Generate robots.txt with all sitemaps"""
    robots = """# Adventure in Sicily - Robots.txt
User-agent: *
Allow: /

# Sitemaps
Sitemap: https://adventureinsicily.com/sitemap.xml
Sitemap: https://adventureinsicily.com/sitemap-videos.xml

# Block low-value pages from crawling
Disallow: /api/
Disallow: /*.json$

# Crawl delay for respectful crawling
Crawl-delay: 1
"""
    with open(PUBLIC_DIR / "robots.txt", "w") as f:
        f.write(robots)
    print("Generated robots.txt")

def generate_episodes_index(data):
    """Generate episodes index page with pre-rendered video grid for SEO"""
    from datetime import datetime
    from html import escape

    videos_by_date = sorted(data['videos'], key=lambda x: x.get('published', ''), reverse=True)

    # Generate video cards HTML
    video_cards = []
    for video in videos_by_date:
        slug = create_slug(video['title'])
        title_escaped = escape(video['title'])
        views = video.get('views', 0)
        views_formatted = f"{views/1000000:.1f}M" if views >= 1000000 else f"{views//1000}K" if views >= 1000 else str(views)

        try:
            published = datetime.fromisoformat(video['published'].replace('Z', '+00:00'))
            date_formatted = published.strftime('%B %d, %Y')
        except:
            date_formatted = ""

        video_cards.append(f'''<a href="/episodes/{slug}/" class="video-card">
            <div class="video-thumbnail">
                <img src="{video['thumbnail']}" alt="{title_escaped}" loading="lazy">
                <div class="play-overlay"></div>
            </div>
            <div class="video-info">
                <h3>{title_escaped}</h3>
                <div class="video-meta">
                    <span class="views">{views_formatted} views</span>
                    <span class="date">{date_formatted}</span>
                </div>
            </div>
        </a>''')

    videos_html = '\n'.join(video_cards)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>All Episodes - Adventure in Sicily | 260+ Sicily Vlog Episodes</title>
    <meta name="description" content="Watch all {len(data['videos'])} episodes of We Bought an Adventure in Sicily. Home renovation, Italian cooking, expat life, and Sicilian adventures.">
    <meta name="keywords" content="Sicily vlog, Italy vlog, expat life Sicily, home renovation Italy, Sicilian food, travel Sicily">
    <link rel="canonical" href="https://adventureinsicily.com/episodes/">

    <!-- Geo Meta -->
    <meta name="geo.region" content="IT-82">
    <meta name="geo.placename" content="Sicily, Italy">

    <!-- Open Graph -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://adventureinsicily.com/episodes/">
    <meta property="og:title" content="All Episodes - Adventure in Sicily">
    <meta property="og:description" content="Watch all {len(data['videos'])} episodes from Swedish expats living in Sicily">
    <meta property="og:image" content="https://adventureinsicily.com/logo.jpg">

    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="All Episodes - Adventure in Sicily">
    <meta name="twitter:description" content="Watch all {len(data['videos'])} episodes from Swedish expats living in Sicily">

    <meta name="robots" content="index, follow">

    <!-- Schema.org -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "All Episodes - Adventure in Sicily",
        "description": "Complete collection of We Bought an Adventure in Sicily videos",
        "url": "https://adventureinsicily.com/episodes/",
        "numberOfItems": {len(data['videos'])},
        "mainEntity": {{
            "@type": "ItemList",
            "numberOfItems": {len(data['videos'])},
            "itemListElement": [
                {{"@type": "ListItem", "position": 1, "url": "https://adventureinsicily.com/episodes/"}}
            ]
        }}
    }}
    </script>

    <link rel="icon" href="/logo.jpg" type="image/jpeg">
    <link rel="stylesheet" href="/styles.css">
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <a href="/" class="logo">
                <img src="/logo.jpg" alt="We Bought an Adventure in Sicily">
                Adventure in Sicily
            </a>
            <ul class="nav-links">
                <li><a href="/">Home</a></li>
                <li><a href="/episodes/">Episodes</a></li>
                <li><a href="/sicily-guide/">Sicily Guide</a></li>
                <li><a href="/about/">About Us</a></li>
                <li><a href="https://www.youtube.com/@weboughtanadventureinsicily?sub_confirmation=1" class="btn-subscribe" target="_blank">Subscribe</a></li>
            </ul>
        </div>
    </nav>

    <header class="page-header">
        <h1>All Episodes</h1>
        <p>{len(data['videos'])} videos documenting our Sicilian adventure</p>
    </header>

    <section class="episodes-section">
        <div class="container">
            <div class="search-bar">
                <input type="text" id="search-input" placeholder="Search episodes... (try: cooking, beach, renovation)">
            </div>
            <p id="result-count" style="text-align: center; color: #666; margin-bottom: 20px;">Showing {len(data['videos'])} episodes</p>
            <div class="video-grid" id="all-videos">
                {videos_html}
            </div>
        </div>
    </section>

    <footer class="footer">
        <div class="container">
            <div class="footer-bottom">
                <p>&copy; 2026 Adventure in Sicily. All rights reserved.</p>
            </div>
        </div>
    </footer>

    <script src="/data.js"></script>
    <script src="/app.js"></script>
</body>
</html>'''

    with open(PUBLIC_DIR / "episodes" / "index.html", "w") as f:
        f.write(html)
    print(f"Generated episodes/index.html with {len(data['videos'])} pre-rendered videos")


def generate_homepage(data):
    """Generate homepage with pre-rendered popular videos for SEO"""
    from html import escape

    videos_by_popularity = sorted(data['videos'], key=lambda x: x.get('views', 0), reverse=True)[:6]

    video_cards = []
    for video in videos_by_popularity:
        slug = create_slug(video['title'])
        title_escaped = escape(video['title'])
        views = video.get('views', 0)
        views_formatted = f"{views/1000000:.1f}M" if views >= 1000000 else f"{views//1000}K" if views >= 1000 else str(views)

        video_cards.append(f'''<a href="/episodes/{slug}/" class="video-card">
            <div class="video-thumbnail">
                <img src="{video['thumbnail']}" alt="{title_escaped}" loading="lazy">
                <div class="play-overlay"></div>
            </div>
            <div class="video-info">
                <h3>{title_escaped}</h3>
                <div class="video-meta">
                    <span class="views">{views_formatted} views</span>
                </div>
            </div>
        </a>''')

    # Read existing index.html and update the video grid
    index_path = PUBLIC_DIR / "index.html"
    with open(index_path, 'r') as f:
        html = f.read()

    # Replace the placeholder with pre-rendered content
    videos_html = '\n'.join(video_cards)
    html = html.replace(
        '<div class="video-grid" id="latest-videos">\n                <!-- Videos loaded dynamically -->',
        f'<div class="video-grid" id="latest-videos">\n                {videos_html}'
    )

    # Update stats
    channel = data.get('channel', {})
    subs = channel.get('subscribers', 70300)
    subs_formatted = f"{subs/1000:.1f}K" if subs >= 1000 else str(subs)
    views = channel.get('totalViews', 4600000)
    views_formatted = f"{views/1000000:.1f}M" if views >= 1000000 else f"{views//1000}K"

    html = html.replace('70.3K', subs_formatted)
    html = html.replace('261', str(channel.get('videoCount', len(data['videos']))))
    html = html.replace('4.6M', views_formatted)
    html = html.replace('View All 261 Episodes', f'View All {len(data["videos"])} Episodes')

    with open(index_path, 'w') as f:
        f.write(html)

    print(f"Updated index.html with {len(videos_by_popularity)} pre-rendered popular videos")


def main():
    print("=" * 50)
    print("Building Adventure in Sicily website")
    print("=" * 50)

    data = load_data()
    generate_data_js(data)
    generate_episode_pages(data)
    generate_episodes_index(data)
    generate_homepage(data)
    generate_sitemap(data)
    generate_robots_txt()

    print("\n" + "=" * 50)
    print("Build complete!")
    print(f"Output: {PUBLIC_DIR}")
    print("=" * 50)

if __name__ == "__main__":
    main()
