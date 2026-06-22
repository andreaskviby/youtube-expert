# Adventure in Sicily - SEO & Google Ads Setup Guide

## Overview

This guide covers:
1. Google Search Console setup (indexing)
2. Google Ads preparation
3. SEO improvements implemented
4. Ranking strategy for "Sicily expat" niche

---

## Step 1: Google Search Console Setup

### 1.1 Add Property

1. Go to [Google Search Console](https://search.google.com/search-console)
2. Click **"Add Property"**
3. Choose **"URL prefix"** method
4. Enter: `https://adventureinsicily.com`

### 1.2 Verify Ownership (DNS Method - Recommended)

1. In Search Console, select **DNS verification**
2. Copy the TXT record (looks like: `google-site-verification=XXXXX`)
3. Add to Cloudflare DNS:
   ```
   Type: TXT
   Name: @
   Content: google-site-verification=XXXXX
   TTL: Auto
   ```
4. Wait 5 minutes, click "Verify" in Search Console

### 1.3 Alternative: HTML Tag Verification

1. Get the verification code from Search Console
2. Edit `/adventure-website/public/index.html`
3. Replace `GOOGLE_VERIFICATION_CODE_HERE` with your code:
   ```html
   <meta name="google-site-verification" content="YOUR_CODE_HERE">
   ```
4. Rebuild and deploy:
   ```bash
   cd adventure-website
   python3 build.py
   npx wrangler pages deploy public --project-name=adventure-in-sicily
   ```
5. Click "Verify" in Search Console

### 1.4 Submit Sitemaps

After verification:

1. Go to **Sitemaps** in Search Console sidebar
2. Submit these sitemaps:
   - `https://adventureinsicily.com/sitemap.xml` (main sitemap)
   - `https://adventureinsicily.com/sitemap-videos.xml` (video sitemap)
3. Click "Submit" for each

### 1.5 Request Indexing

1. Go to **URL Inspection** tool
2. Enter: `https://adventureinsicily.com/`
3. Click **"Request Indexing"**
4. Repeat for key pages:
   - `https://adventureinsicily.com/episodes/`
   - `https://adventureinsicily.com/about/`
   - `https://adventureinsicily.com/sicily-guide/`

---

## Step 2: Google Ads Setup

### 2.1 Create Google Ads Account

1. Go to [ads.google.com](https://ads.google.com)
2. Sign in with your Google account
3. Create a new campaign (skip for now, we'll set up conversion tracking first)

### 2.2 Install Google Ads Tag

1. In Google Ads, go to **Tools & Settings** → **Measurement** → **Conversions**
2. Create a new conversion action:
   - Category: "Subscribe"
   - Conversion name: "YouTube Subscribe Click"
   - Value: $5 (estimated value)
   - Count: One per click
3. Get your Conversion ID and Label (e.g., `AW-123456789/AbCdEfGh`)
4. Edit `/adventure-website/public/index.html`
5. Uncomment and update the Google Ads script:
   ```html
   <script async src="https://www.googletagmanager.com/gtag/js?id=AW-123456789"></script>
   <script>
     window.dataLayer = window.dataLayer || [];
     function gtag(){dataLayer.push(arguments);}
     gtag('js', new Date());
     gtag('config', 'AW-123456789');
   </script>
   ```

### 2.3 Track Subscribe Button Clicks

Add this event tracking to the subscribe buttons:

```html
<a href="https://www.youtube.com/..."
   onclick="gtag('event', 'conversion', {'send_to': 'AW-123456789/AbCdEfGh'});"
   class="btn-subscribe">Subscribe</a>
```

### 2.4 Recommended Campaign Types

| Campaign Type | Budget | Target |
|--------------|--------|--------|
| **YouTube Ads** | $10-20/day | People watching Sicily/Italy travel videos |
| **Search Ads** | $5-10/day | "life in sicily", "move to sicily", "buy house sicily" |
| **Display Ads** | $3-5/day | Travel & Italy interest audiences |

### 2.5 Recommended Keywords for Search Ads

**High Intent (Buy House):**
- buy house in sicily
- sicily property for sale
- cheap houses in sicily
- 1 euro house sicily

**Lifestyle (Expat):**
- moving to sicily
- life in sicily
- expat life sicily
- living in italy as an expat

**Travel (Awareness):**
- sicily travel vlog
- things to do in sicily
- sicily food tour
- best beaches sicily

---

## Step 3: SEO Improvements Implemented

### Technical SEO

| Feature | Status |
|---------|--------|
| Sitemap.xml with lastmod/priority | ✅ |
| Video sitemap (sitemap-videos.xml) | ✅ |
| Robots.txt with all sitemaps | ✅ |
| Canonical URLs | ✅ |
| Pre-rendered content (no JS needed) | ✅ |
| Mobile-responsive | ✅ |
| Fast loading (static site) | ✅ |

### Meta Tags

| Tag | Status |
|-----|--------|
| Title tags (optimized) | ✅ |
| Meta descriptions | ✅ |
| Open Graph tags | ✅ |
| Twitter Cards | ✅ |
| Geo meta tags (Sicily) | ✅ |
| hreflang tags | ✅ |

### Schema.org Structured Data

| Type | Status |
|------|--------|
| WebSite | ✅ |
| Organization | ✅ |
| VideoObject (per episode) | ✅ |
| BreadcrumbList | ✅ |
| Place (Sicily) | ✅ |
| CollectionPage (episodes) | ✅ |
| SearchAction | ✅ |

---

## Step 4: Ranking Strategy

### Target Keywords

**Primary (High Volume):**
1. "life in sicily" - lifestyle content
2. "moving to sicily" - relocation guides
3. "buy house sicily" - property content
4. "sicily vlog" - brand awareness

**Secondary (Long-tail):**
1. "swedish expats in sicily"
2. "renovating house in sicily"
3. "sicilian food tour"
4. "best beaches in sicily"

### Content Strategy

1. **Sicily Guide Section** - Create SEO-optimized guides:
   - `/sicily-guide/buying-property/` - "How to Buy a House in Sicily"
   - `/sicily-guide/cost-of-living/` - "Cost of Living in Sicily 2026"
   - `/sicily-guide/visa-residency/` - "Moving to Sicily from USA/UK"

2. **Episode Categorization** - Tag videos by topic:
   - Food & Restaurants
   - Beaches & Travel
   - Home Renovation
   - Expat Life

3. **Local SEO** - Target specific Sicily regions:
   - Palermo
   - Catania
   - Taormina

### Link Building Ideas

1. **Guest posts** on Italy/expat blogs
2. **Reddit presence** in r/IWantOut, r/expats, r/Italy
3. **YouTube community** collaborations
4. **Travel websites** like Nomad List, Expat.com

---

## Step 5: Monitoring & Maintenance

### Weekly Tasks

1. Check Search Console for:
   - Indexing errors
   - Mobile usability issues
   - Core Web Vitals

2. Review top performing queries
3. Submit new episode pages for indexing

### Monthly Tasks

1. Update sitemap (automatic with build)
2. Review Google Ads performance
3. Check competitor rankings
4. Create new guide content

### Google Analytics 4 (Optional)

Add GA4 for detailed traffic analysis:

```html
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

---

## Quick Commands

```bash
# Rebuild site
cd /Users/andreaskviby/Herd/youtube-expert
python3 adventure-website/build.py

# Deploy to Cloudflare
cd adventure-website
npx wrangler pages deploy public --project-name=adventure-in-sicily

# Test sitemap
curl https://adventureinsicily.com/sitemap.xml | head -50

# Test video sitemap
curl https://adventureinsicily.com/sitemap-videos.xml | head -50
```

---

## Support

- Google Search Console Help: https://support.google.com/webmasters
- Google Ads Help: https://support.google.com/google-ads
- Cloudflare Pages Docs: https://developers.cloudflare.com/pages

---

*Generated: 2026-06-20*
