#!/bin/bash
# Deploy Adventure in Sicily website to Cloudflare Pages

echo "=========================================="
echo "Deploying Adventure in Sicily"
echo "=========================================="

# Check if wrangler is installed
if ! command -v wrangler &> /dev/null; then
    echo "Installing Wrangler CLI..."
    npm install -g wrangler
fi

# Build the site first
echo "Building site..."
cd "$(dirname "$0")"
python3 ../build.py 2>/dev/null || python build.py

# Deploy to Cloudflare Pages
echo "Deploying to Cloudflare Pages..."
wrangler pages deploy public --project-name=adventure-in-sicily

echo ""
echo "=========================================="
echo "Deployment complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Go to Cloudflare Dashboard > Pages > adventure-in-sicily"
echo "2. Add custom domains:"
echo "   - adventureinsicily.com"
echo "   - www.adventureinsicily.com"
echo "3. Set up redirects for other domains (see SETUP.md)"
echo ""
