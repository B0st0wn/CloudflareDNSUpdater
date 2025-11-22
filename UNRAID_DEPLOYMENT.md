# Cloudflare DDNS Updater - Unraid Deployment Guide

This guide walks you through deploying the Cloudflare DDNS Updater container on Unraid.

## Prerequisites

- Unraid 6.10+
- Cloudflare account with a domain
- Cloudflare API token with DNS edit permissions
- Docker enabled on Unraid

## Installation Steps

### Step 1: Add Container via Docker Tab

1. Go to **Unraid Dashboard** → **Docker** tab
2. Click **Add Container**
3. Configure as follows:

| Field | Value |
|-------|-------|
| **Name** | `cloudflare-ddns` |
| **Repository** | `ghcr.io/YOUR_GITHUB_USERNAME/cloudflare-ddns-updater:latest` |
| **Network Type** | Bridge |
| **Console Shell** | (leave default) |
| **Console Port** | (leave default) |

### Step 2: Configure Port Mapping

Add a port mapping:

| Type | Container Port | Host Port |
|------|---|---|
| Port | 8080 | 8080 |

### Step 3: Configure Storage

Click **Add Path** and map:

| Container Path | Host Path | Access Mode |
|---|---|---|
| `/data` | `/mnt/user/appdata/cf-ddns/` | Read/Write |

### Step 4: Configure Environment Variables (Optional)

Click **Add Variable** to set:

| Key | Value | Description |
|---|---|---|
| `CONFIG_SECRET` | `your-secret-key` | Optional token obfuscation (leave blank to skip) |

Example secure value: Generate with `openssl rand -hex 16`

### Step 5: Set Health Check (Optional)

Enable healthcheck:
- **Healthcheck Enabled**: Yes
- **Healthcheck Command**: Already configured in container
- **Polling Interval**: 30 seconds

### Step 6: Apply Settings

Click **Apply** to start the container. Unraid will download the image and start the container.

## Accessing the Web UI

1. Open your browser and navigate to:
   ```
   http://UNRAID_IP:8080
   ```

2. You should see the Cloudflare DDNS configuration dashboard

## Initial Configuration

### 1. Add Cloudflare API Token

1. In the dashboard, scroll to the **Configuration** section
2. Paste your Cloudflare API token
3. Click **Save Token**

To get your Cloudflare API token:
- Go to [Cloudflare Dashboard](https://dash.cloudflare.com/)
- Click **My Profile** → **API Tokens**
- Create a new token with these permissions:
  - Zone → DNS → Edit
  - Zones → Read
- Copy and paste into the dashboard

### 2. Load and Import Records

1. Click **Load Zones** to fetch your Cloudflare zones
2. Select your domain zone
3. Click **Load Records** to fetch DNS records
4. Check the A/AAAA records you want to auto-update
5. Optionally check **Auto-Update** for records that should sync automatically
6. Click **Import Selected**

### 3. Configure Polling Interval

1. Go to **Configuration** section
2. Set **Polling Interval** (seconds, minimum 60)
   - Default: 300 seconds (5 minutes)
   - Lower = more frequent checks (more API calls)
   - Higher = less frequent checks (delayed IP updates)
3. Click **Update Interval**

### 4. Manage Records

In the **Configured Records** table:

- **Auto-Update** checkbox: Enable to automatically sync this record when your IP changes
- **Proxy** checkbox: Toggle Cloudflare proxying (orange/gray cloud)
- **Delete** button: Remove record from tracking

## Data Persistence

Container data is stored in `/mnt/user/appdata/cf-ddns/`:

- `config.json` - Cloudflare token and settings
- `records.json` - Imported records and sync status
- `logs/` - Sync operation logs

This directory persists across container restarts and updates.

## Troubleshooting

### Container won't start

**Check logs**: 
- In Unraid Docker tab, right-click container → **Console**
- Look for error messages

**Common issues**:
- Port 8080 already in use: Change host port to something else (e.g., 8081)
- Image not found: Verify image name and that ghcr.io is accessible
- Permissions: Ensure `/mnt/user/appdata/cf-ddns/` exists and is writable

### Records not updating automatically

1. Verify **Auto-Update** is checked for the record
2. Check that your public IP has actually changed
3. View logs: Open container console and check sync status
4. Increase polling interval if seeing rate limit errors

### "Cannot connect to WebUI"

1. Verify container is running: Check Unraid Docker tab
2. Check port mapping: Should be `8080:8080`
3. Try different port if 8080 is in use
4. Check firewall: Allow traffic to port 8080

### API token not saving

1. Ensure token is valid (can be tested at [Cloudflare API Docs](https://developers.cloudflare.com/))
2. Check that token has DNS edit permissions
3. Verify `/mnt/user/appdata/cf-ddns/` directory is writable
4. Check container logs for error messages

## Updates

### Updating to Latest Version

1. In Unraid Docker tab, right-click container → **Force Update**
2. This will pull the latest image and restart the container
3. Your configuration in `/data` will be preserved

### Manual Update

1. Remove the container (don't delete image)
2. Delete the image: `ghcr.io/YOUR_GITHUB_USERNAME/cloudflare-ddns-updater`
3. Re-add container - it will pull the latest image

## Uninstallation

1. In Unraid Docker tab, right-click container → **Remove**
2. (Optional) Delete image to free space
3. (Optional) Remove appdata directory at `/mnt/user/appdata/cf-ddns/`

## Performance Considerations

- Polling interval default is 300 seconds (5 minutes)
- Each IP check makes 1 API call; update only if IP changed
- Unraid has plenty of resources for this lightweight container
- Logs are available in `/mnt/user/appdata/cf-ddns/logs/`

## Support & Troubleshooting

For issues or feature requests, visit the GitHub repository:
- GitHub: `https://github.com/YOUR_USERNAME/CloudflareDNSUpdater`
- Issues: Report bugs in GitHub Issues tab
- Wiki: Check for community solutions

## Advanced Configuration

### Using Docker Compose (Alternative)

If you prefer docker-compose, create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  cf-ddns:
    image: ghcr.io/YOUR_GITHUB_USERNAME/cloudflare-ddns-updater:latest
    container_name: cloudflare-ddns
    ports:
      - "8080:8080"
    volumes:
      - /mnt/user/appdata/cf-ddns:/data
    environment:
      - CONFIG_SECRET=your-secret-key
    restart: unless-stopped
```

Then on Unraid terminal:
```bash
docker-compose -f docker-compose.yml up -d
```

### Using Custom Domain

If you have a reverse proxy (nginx, Traefik, etc.), you can expose the container at:
```
https://ddns.yourdomain.com
```

Just route traffic to `localhost:8080` on your Unraid server.

---

Happy DNS updating! 🚀
