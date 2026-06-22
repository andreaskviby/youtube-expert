# Adventure in Sicily - Deployment Setup

## Automatic Deployment (GitHub Actions)

When you push to the `main` branch, the website automatically builds and deploys.

### Setup Steps (One-time)

#### 1. Get Cloudflare API Token

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/profile/api-tokens)
2. Click **Create Token**
3. Use template: **Edit Cloudflare Workers**
4. Or create custom token with these permissions:
   - Account > Cloudflare Pages > Edit
   - Account > Account Settings > Read
5. Copy the token (you'll only see it once!)

#### 2. Add GitHub Secrets

Go to your GitHub repo: `https://github.com/andreaskviby/youtube-expert/settings/secrets/actions`

Add these secrets:

| Secret Name | Value |
|-------------|-------|
| `CLOUDFLARE_API_TOKEN` | Your API token from step 1 |
| `CLOUDFLARE_ACCOUNT_ID` | `913425d85efd8768ce56892d2029234c` |

#### 3. Push to GitHub

```bash
git add .
git commit -m "Add GitHub Actions deployment"
git push origin main
```

The workflow will automatically run!

---

## Manual Deployment (Local)

### Option 1: Deploy Script

```bash
cd /Users/andreaskviby/Herd/youtube-expert/adventure-website
./deploy.sh
```

### Option 2: Step by Step

```bash
# 1. Build
cd /Users/andreaskviby/Herd/youtube-expert
python3 adventure-website/build.py

# 2. Deploy
cd adventure-website
npx wrangler pages deploy public --project-name=adventure-in-sicily
```

---

## Workflow Triggers

The GitHub Action runs when:
- Push to `main` branch AND files in `adventure-website/` changed
- Manual trigger via GitHub Actions UI

---

## Cloudflare Pages Info

| Setting | Value |
|---------|-------|
| Project | `adventure-in-sicily` |
| Account ID | `913425d85efd8768ce56892d2029234c` |
| Production URL | https://adventureinsicily.com |
| Preview URL | https://*.adventure-in-sicily.pages.dev |

---

## Troubleshooting

### "Authentication failed"
- Check CLOUDFLARE_API_TOKEN is correct
- Token needs Pages edit permission

### "Project not found"
- Check CLOUDFLARE_ACCOUNT_ID is correct
- Project name must be `adventure-in-sicily`

### Build fails
- Check Python 3.11+ is available
- Check `src/channel_data.json` exists
