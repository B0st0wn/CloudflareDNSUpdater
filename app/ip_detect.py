import httpx
from typing import Optional

CF_TRACE = "https://cloudflare.com/cdn-cgi/trace"
IPIFY = "https://api.ipify.org"
IFCONFIG = "https://ifconfig.co/ip"

async def detect_wan_ip(client: httpx.AsyncClient) -> Optional[str]:
    # Try Cloudflare trace
    try:
        r = await client.get(CF_TRACE, timeout=5.0)
        if r.status_code == 200:
            text = r.text
            for line in text.splitlines():
                if line.startswith("ip="):
                    return line.split("=", 1)[1].strip()
    except Exception:
        pass

    # Fallback to ipify
    try:
        r = await client.get(IPIFY, timeout=5.0)
        if r.status_code == 200:
            return r.text.strip()
    except Exception:
        pass

    # Fallback to ifconfig.co
    try:
        r = await client.get(IFCONFIG, timeout=5.0, headers={"Accept": "text/plain"})
        if r.status_code == 200:
            return r.text.strip()
    except Exception:
        pass

    return None
