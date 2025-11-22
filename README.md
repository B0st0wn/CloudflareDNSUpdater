# Cloudflare DDNS Updater

A lightweight, web-based Cloudflare Dynamic DNS (DDNS) agent designed for Docker, Unraid, and home labs. Automatically detects your public IP and updates Cloudflare DNS records with optional proxy status control.

## Features

- **Automatic IP Detection** - Detects WAN IP via Cloudflare's trace endpoint
- **Selective Record Updates** - Choose which records to auto-update with the new IP
- **Proxy Control** - Toggle Cloudflare proxy (orange cloud) status per record
- **Configurable Polling** - Adjustable sync interval (default 300 seconds, minimum 60 seconds)
- **Web UI** - Simple, responsive FastAPI + HTMX interface (no heavy JS frameworks)
- **Persistent Storage** - Configuration and records stored in `/data` volume
- **Secure** - Optional token obfuscation via `CONFIG_SECRET`
- **Lightweight** - Python 3.12 slim base, minimal dependencies
- **Health Checks** - Built-in Docker healthcheck

## Quick Start

### Docker (Docker-Compose)

```yaml
version: '3.8'
services:
  cf-ddns:
    image: ghcr.io/YOUR_GITHUB_USERNAME/cloudflare-ddns-updater:latest
    container_name: cloudflare-ddns
    ports:
      - "8080:8080"
    volumes:
      - ./data:/data
    environment:
      CONFIG_SECRET: your-secret-key-here
    restart: unless-stopped
```

### Unraid

1. Install the container using the template (coming soon to Unraid Community Apps)
2. Configure volume mapping: `/mnt/user/appdata/cf-ddns/` → `/data`
3. Set environment variables (optional `CONFIG_SECRET`)
4. Access the WebUI at `http://[YOUR_UNRAID_IP]:8080`

### Development (Local)

```powershell
# Clone repo and setup venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Then open `http://localhost:8080` in your browser.

## Setup Instructions

1. **Get Cloudflare API Token**
   - Go to [Cloudflare Dashboard](https://dash.cloudflare.com/)
   - Account Settings → API Tokens
   - Create token with "DNS Edit" permissions for your domain
   - Copy the token

2. **Configure in Web UI**
   - Open the application dashboard
   - Paste your Cloudflare API token in the Configuration section
   - Click "Save Token"

3. **Import Records**
   - Click "Load Zones" to fetch your Cloudflare zones
   - Select a zone and click "Load Records"
   - Check the A/AAAA records you want to monitor
   - Click "Import Selected"

4. **Configure Auto-Update**
   - In "Configured Records" table, check/uncheck "Auto-Update" for each record
   - Records with Auto-Update enabled will sync when your WAN IP changes

5. **Adjust Polling Interval** (Optional)
   - Go to Configuration → Polling Interval
   - Set desired check frequency (seconds)
   - Higher values reduce API calls, lower values detect changes faster

6. **Control Proxy Status** (Optional)
   - Use the "Proxy" checkbox for each record to toggle Cloudflare proxying
   - Checked = orange cloud (proxied through Cloudflare)
   - Unchecked = gray cloud (DNS only)

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CONFIG_SECRET` | Secret for optional token obfuscation | (none) |
| `DATA_DIR` | Directory for config/record files | `/data` |

## API Endpoints

### Records Management
- `GET /api/records` - List all configured records
- `POST /api/records` - Add a new record
- `PATCH /api/records` - Update record auto_update flag
- `DELETE /api/records` - Delete a record

### Cloudflare Integration
- `GET /api/zones` - Fetch zones from Cloudflare
- `GET /api/zones/{zone_id}/records` - Fetch zone records
- `POST /api/import-records` - Import records from Cloudflare

### Proxy Control
- `GET /api/records/{record_id}/proxy` - Get proxy status
- `PATCH /api/records/{record_id}/proxy` - Set proxy status

### Sync Control
- `POST /api/update-now` - Trigger immediate sync
- `GET /api/status` - Get current status
- `POST /api/polling-interval` - Update polling interval

### Health
- `GET /health` - Health check endpoint

## Security Notes

- **API Token** is stored locally and never transmitted to third parties
- `CONFIG_SECRET` environment variable enables optional XOR obfuscation of stored token
- No telemetry or external analytics
- All traffic to Cloudflare is HTTPS
- Token is never logged to console

## Troubleshooting

### "Failed to update proxy status"
- Ensure the record supports proxying (A, AAAA, CNAME only)
- Check that your API token has "DNS Edit" permissions
- Verify the record exists in Cloudflare

### Records not syncing
- Check that "Auto-Update" is enabled for the record
- Verify your public IP is different from the record's current IP
- Check logs: `docker logs cf-ddns` (or your container name)
- Increase polling interval if you see rate limit errors

### Can't connect to container
- Verify port 8080 is mapped: `-p 8080:8080`
- Check container is running: `docker ps`
- View logs: `docker logs <container_id>`

## Data Persistence

The application stores configuration in the `/data` volume:

- `/data/config.json` - API token and settings
- `/data/records.json` - Imported records and their status
- `/data/logs/` - Sync operation logs

## Building from Source

```bash
docker build -t cf-ddns:latest .
docker run -p 8080:8080 -v ./data:/data cf-ddns:latest
```

## Contributing

Contributions welcome! Feel free to submit issues or pull requests.

## License

See LICENSE file in repository.

## Changelog

### v1.0.0
- Initial release
- Auto-update DNS records with public IP
- Web UI for record management
- Configurable polling interval
- Proxy (orange cloud) status control
- Cloudflare API integration
