# Quick Reference - Publishing to GitHub

## Copy-Paste Commands

Replace `YOUR_USERNAME` with your GitHub username:

### 1️⃣ Create Repository on GitHub
1. Go to https://github.com/new
2. Repository name: `CloudflareDNSUpdater`
3. Visibility: **Public**
4. Click "Create repository"

### 2️⃣ Push to GitHub

```powershell
cd c:\My_Projects\CloudflareDNSUpdater

# Configure remote
git remote add origin https://github.com/YOUR_USERNAME/CloudflareDNSUpdater.git
git branch -M main

# Push!
git push -u origin main
```

### 3️⃣ Watch It Build

1. Go to your GitHub repo
2. Click **Actions** tab
3. Wait for "Build and Push Docker Image" workflow to complete (1-3 min)
4. ✅ Done! Image is at `ghcr.io/YOUR_USERNAME/cloudflarednsupdater:latest`

## Verify Image Built Successfully

```powershell
# Test pulling the image (wait 2-3 min after workflow completes)
docker pull ghcr.io/YOUR_USERNAME/cloudflarednsupdater:latest

# Run it
docker run -p 8080:8080 -v ./data:/data ghcr.io/YOUR_USERNAME/cloudflarednsupdater:latest

# Test it (in new terminal)
curl http://localhost:8080/health
```

## Share with Unraid Users

Send them this:

```
Image: ghcr.io/YOUR_USERNAME/cloudflarednsupdater:latest

# In Unraid Docker UI:
- Add Container
- Repository: ghcr.io/YOUR_USERNAME/cloudflarednsupdater:latest
- Port: 8080:8080
- Volume: /mnt/user/appdata/cf-ddns → /data
- Apply

# Then open: http://UNRAID_IP:8080
```

## Git Info

```
Local: ✅ Initialized
Commits: 2 (Initial + Status)
Branch: main
Remote: (Will be added by you in Step 2)
```

## Files Modified/Created for GitHub

- `.github/workflows/docker-publish.yml` ← Automated CI/CD
- `.gitignore` ← Ignore build artifacts
- `README.md` ← Updated with ghcr.io reference
- `STATUS.md` ← Project completion status
- `GITHUB_PUBLISHING.md` ← Full publishing guide
- `UNRAID_DEPLOYMENT.md` ← Unraid step-by-step

## What Gets Published

**Automatic on every push**:
- Docker image to ghcr.io
- Latest tag
- Branch name tags
- Semantic version tags (from git tags like `v1.0.0`)
- Git SHA tags

**Example after tagging v1.0.0**:
```
ghcr.io/YOUR_USERNAME/cloudflarednsupdater:latest       ← always latest
ghcr.io/YOUR_USERNAME/cloudflarednsupdater:1.0.0        ← exact version
ghcr.io/YOUR_USERNAME/cloudflarednsupdater:1.0          ← major.minor
ghcr.io/YOUR_USERNAME/cloudflarednsupdater:1            ← major
ghcr.io/YOUR_USERNAME/cloudflarednsupdater:sha-abc1234  ← git commit
```

## Status: ✅ READY TO PUSH

Everything is configured. Just follow the 3 copy-paste commands above!

---

For detailed troubleshooting, see `GITHUB_PUBLISHING.md`
For Unraid setup, see `UNRAID_DEPLOYMENT.md`
For full project status, see `STATUS.md`
