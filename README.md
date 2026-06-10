# YouTube Expert - Channel Growth & Website System

Complete YouTube channel optimization toolkit with AI-powered analysis and a static SEO website generator. Built for **We Bought an Adventure in Sicily** YouTube channel.

**Live Website:** https://adventureinsicily.com

## Project Overview

This repository contains three main components:

### 1. YouTube Expert (Analysis Engine)
AI-powered YouTube channel analysis with 12 specialized skills for growth optimization.

### 2. Adventure Website (SEO Platform)
Static website for SEO, deployed on Cloudflare Pages, featuring all 261 YouTube episodes with Schema.org markup.

### 3. Video Rebuild Tools
Scripts for remastering videos, creating YouTube Shorts, and generating promotional content.

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/andreaskviby/youtube-expert.git
cd youtube-expert

# Install Python dependencies
pip install -e .

# Run channel diagnostics
python -m youtube_expert.cli --data . --skill diagnostics
```

---

## 1. YouTube Expert - Channel Analysis

### Features
- **12 Specialized Skills** for comprehensive channel analysis
- **Agent-Ready** - Designed for AI agent integration
- **CSV-Based Analysis** - Works with YouTube Studio export data
- **Actionable Insights** - Prioritized recommendations with severity levels

### Available Skills

| Skill | Description |
|-------|-------------|
| `diagnostics` | Channel health check & critical issue detection |
| `performance` | Deep video performance metrics analysis |
| `shorts_strategy` | Shorts vs long-form content optimization |
| `thumbnail_optimizer` | Thumbnail & title A/B test recommendations |
| `upload_scheduler` | Optimal upload timing and frequency analysis |
| `seo_optimizer` | Title, tag, and description SEO analysis |
| `audience_analyzer` | Viewer retention and engagement analysis |
| `revenue_optimizer` | Monetization and revenue strategy analysis |
| `growth_projector` | Growth trend forecasting and projections |
| `competitor_analyzer` | Competitive landscape and benchmarking |
| `content_planner` | Content calendar and topic recommendations |
| `trend_detector` | Trending topics and viral pattern detection |

### Command Line Usage

```bash
# Run channel diagnostics
python -m youtube_expert.cli --data . --skill diagnostics

# Run all skills
python -m youtube_expert.cli --data . --all

# Get quick summary
python -m youtube_expert.cli --data . --summary

# Output as JSON
python -m youtube_expert.cli --data . --skill performance --json

# List available skills
python -m youtube_expert.cli --list-skills
```

### Python API

```python
from youtube_expert import YouTubeExpert

# Initialize with data directory
expert = YouTubeExpert("/path/to/csv/data")

# Run specific skill
result = expert.run_skill("diagnostics")
print(result["digest"])  # Human-readable summary
print(result["severity"])  # OK, WATCH, WARNING, or CRITICAL

# Run all skills
full_report = expert.run_all_skills()
```

### Data Format

Export these CSV files from YouTube Studio Analytics:

- **Table data.csv** (required) - Video-level metrics
- **Totals.csv** (optional) - Daily view totals
- **Chart data.csv** (optional) - Daily per-video metrics

---

## 2. Adventure Website - SEO Platform

A static website promoting the YouTube channel, optimized for search engines.

### Features
- **262 Episode Pages** with embedded YouTube videos
- **Video Schema.org Markup** for Google video results
- **Region-based Sicily Guides** for property search SEO
- **Popularity-sorted Homepage** showing top performing videos
- **Search with Topic Requests** - when no results, suggests requesting new content

### Website Structure

```
adventure-website/
├── public/                    # Static site (deployed to Cloudflare)
│   ├── index.html            # Homepage
│   ├── styles.css            # Styling (Sicilian warm colors)
│   ├── app.js                # JavaScript functionality
│   ├── data.js               # Video data (auto-generated)
│   ├── sitemap.xml           # SEO sitemap (auto-generated)
│   ├── robots.txt            # Crawler rules
│   ├── logo.jpg              # Channel logo
│   ├── episodes/             # 262 episode pages (auto-generated)
│   │   └── {slug}/index.html
│   ├── about/                # About page (true story)
│   │   └── index.html
│   └── sicily-guide/         # Sicily travel guides
│       ├── index.html
│       ├── restaurants/
│       ├── beaches/
│       ├── hotels/
│       ├── stories/
│       └── regions/          # 5 region pages for property SEO
│           ├── catania/
│           ├── palermo/
│           ├── syracuse/
│           ├── taormina/
│           └── agrigento/
├── src/
│   └── channel_data.json     # YouTube data source
├── build.py                  # Build script
├── deploy.sh                 # Deploy to Cloudflare
├── wrangler.toml             # Cloudflare Pages config
└── SETUP.md                  # Domain setup guide
```

### Building the Website

```bash
cd adventure-website

# Fetch latest YouTube data and rebuild
python3 build.py

# Deploy to Cloudflare Pages
./deploy.sh
```

### Design

Colors extracted from YouTube channel logo:
- Primary: `#48372f` (Dark brown)
- Accent: `#C4713B` (Sicilian terracotta)
- Mediterranean: `#2E86AB` (Sea blue)
- Cream: `#F5F0EB` (Background)

---

## 3. Domain Configuration

### Primary Domain
- **adventureinsicily.com** → Cloudflare Pages

### Redirect Domains
- **weboughtanadventureinsicily.com** → 301 redirect to primary
- **oursicilianadventure.com** → 301 redirect to primary

### Cloudflare Setup

All domains are managed via Cloudflare:
1. DNS: CNAME to `adventure-in-sicily.pages.dev`
2. SSL: Automatic via Cloudflare
3. CDN: Global edge caching

See `adventure-website/SETUP.md` for detailed setup instructions.

---

## 4. Video Rebuild Tools

### EP36 Cooking Class Remaster

Located in `EP36_REBUILD/`:

```bash
# Create remastered video with time-lapse and subtitles
python scripts/rebuild_remastered_v2.py

# Create YouTube Shorts
python scripts/create_shorts.py
```

**Output:**
- `output/ep36_remastered.mp4` - 16-minute remastered video
- `shorts/short1_wine_story.mp4` - 58s
- `shorts/short2_secret_sauce.mp4` - 60s
- `shorts/short3_chili.mp4` - 42s
- `shorts/short4_timelapse_reveal.mp4` - 55s

### EP28 Extended Cut

Located in `EP28_REBUILD/`:

```bash
# Create extended version
python scripts/rebuild_extended_v2.py

# Upload to YouTube
python upload/upload_video.py
```

---

## 5. Thumbnail System

### Thumbnail Style Guide
See `THUMBNAIL_STYLE_GUIDE.md` for the complete style system:
- Faces prominent with emotions
- Curiosity gap text
- Location/food elements
- Consistent color scheme

### Creating Thumbnails

```bash
# AI-powered thumbnail creation
python create_thumbnail_v5.py --video_id VIDEO_ID

# Simple thumbnail (no AI)
python create_thumbnail_noai.py --image source.jpg --text "Title"
```

---

## File Structure

```
youtube-expert/
├── README.md                     # This file
├── pyproject.toml                # Python package config
├── requirements.txt              # Python dependencies
│
├── youtube_expert/               # Core analysis engine
│   ├── __init__.py
│   ├── core.py                   # YouTubeExpert class
│   ├── cli.py                    # Command line interface
│   ├── agent_runner.py           # AI agent integration
│   └── skills/                   # 12 analysis skills
│
├── adventure-website/            # SEO website
│   ├── public/                   # Static site files
│   ├── build.py                  # Build script
│   └── SETUP.md                  # Domain setup guide
│
├── EP36_REBUILD/                 # Cooking class remaster
│   ├── scripts/                  # Python scripts
│   ├── shorts/                   # Generated Shorts
│   └── community_posts.md        # YouTube post drafts
│
├── EP28_REBUILD/                 # Extended cut tools
│
├── thumbnails_master/            # Thumbnail assets
├── THUMBNAIL_STYLE_GUIDE.md      # Thumbnail guidelines
├── THUMBNAIL_WORKFLOW.md         # Thumbnail process
│
├── Table data.csv                # YouTube Studio export
├── Totals.csv                    # Daily totals
└── Chart data.csv                # Chart data
```

---

## Environment Variables

Create `.env` file:

```bash
YOUTUBE_API_KEY=your_api_key_here
```

---

## Channel Stats

As of June 2026:
- **70,300** subscribers
- **4.6M** total views
- **261** videos

---

## License

MIT

---

## Contact

- **YouTube:** [@weboughtanadventureinsicily](https://www.youtube.com/@weboughtanadventureinsicily)
- **Website:** https://adventureinsicily.com
