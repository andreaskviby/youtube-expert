# Adventure in Sicily - Cloudflare Setup Guide

## Step 1: Deploy the Website

```bash
cd adventure-website
chmod +x deploy.sh
./deploy.sh
```

Or manually:
```bash
npm install -g wrangler
wrangler login
wrangler pages deploy public --project-name=adventure-in-sicily
```

## Step 2: Connect Primary Domain (adventureinsicily.com)

1. Go to **Cloudflare Dashboard** → **Pages** → **adventure-in-sicily**
2. Click **Custom domains** → **Set up a custom domain**
3. Add: `adventureinsicily.com`
4. Add: `www.adventureinsicily.com`
5. Cloudflare will automatically configure DNS

## Step 3: Set Up Redirects for Other Domains

### For weboughtanadventureinsicily.com:

1. Go to **Cloudflare Dashboard** → Select **weboughtanadventureinsicily.com**
2. Go to **Rules** → **Redirect Rules**
3. Create a new rule:
   - **Rule name:** Redirect to primary domain
   - **When incoming requests match:** All incoming requests
   - **Then:** Dynamic Redirect
   - **Expression:** `(http.host eq "weboughtanadventureinsicily.com") or (http.host eq "www.weboughtanadventureinsicily.com")`
   - **URL:** `concat("https://adventureinsicily.com", http.request.uri.path)`
   - **Status code:** 301 (Permanent)
4. Deploy

### For oursicilianadventure.com:

1. Go to **Cloudflare Dashboard** → Select **oursicilianadventure.com**
2. Go to **Rules** → **Redirect Rules**
3. Create a new rule:
   - **Rule name:** Redirect to primary domain
   - **When incoming requests match:** All incoming requests
   - **Then:** Dynamic Redirect
   - **Expression:** `(http.host eq "oursicilianadventure.com") or (http.host eq "www.oursicilianadventure.com")`
   - **URL:** `concat("https://adventureinsicily.com", http.request.uri.path)`
   - **Status code:** 301 (Permanent)
4. Deploy

## Step 4: Enable SSL

SSL should be automatic with Cloudflare. Verify:
1. Go to each domain → **SSL/TLS**
2. Set to **Full (strict)**

## Step 5: Verify Setup

Test all domains redirect correctly:
```bash
curl -I https://weboughtanadventureinsicily.com
# Should show: HTTP/2 301, Location: https://adventureinsicily.com/

curl -I https://oursicilianadventure.com
# Should show: HTTP/2 301, Location: https://adventureinsicily.com/
```

## Updating the Website

When you have new YouTube videos, run:
```bash
cd adventure-website
python3 build.py
./deploy.sh
```

This will:
1. Fetch latest videos from YouTube
2. Generate new episode pages
3. Update sitemap
4. Deploy to Cloudflare

## File Structure

```
adventure-website/
├── public/              # Static site files (deployed)
│   ├── index.html       # Homepage
│   ├── styles.css       # Styling
│   ├── app.js           # JavaScript
│   ├── data.js          # Video data (generated)
│   ├── sitemap.xml      # SEO sitemap (generated)
│   ├── robots.txt       # Crawler rules
│   ├── episodes/        # Episode pages (generated)
│   ├── about/           # About page
│   └── sicily-guide/    # Sicily guide page
├── src/
│   └── channel_data.json # YouTube data
├── build.py             # Build script
├── deploy.sh            # Deploy script
└── wrangler.toml        # Cloudflare config
```

## SEO Benefits

This setup provides:
- **Video Schema markup** on every episode page (Google shows video results)
- **Sitemap** submitted to Google
- **Canonical URLs** preventing duplicate content
- **301 redirects** passing SEO juice from all domains to primary
- **Fast loading** via Cloudflare's CDN
- **Mobile responsive** design
