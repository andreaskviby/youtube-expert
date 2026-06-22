#!/bin/bash
# Adventure in Sicily - Local Deploy Script
# Usage: ./deploy.sh

set -e

echo "=========================================="
echo "Building Adventure in Sicily Website"
echo "=========================================="

cd "$(dirname "$0")/.."

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run build
python3 adventure-website/build.py

echo ""
echo "=========================================="
echo "Deploying to Cloudflare Pages"
echo "=========================================="

cd adventure-website
npx wrangler pages deploy public --project-name=adventure-in-sicily

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo "Live at: https://adventureinsicily.com"
