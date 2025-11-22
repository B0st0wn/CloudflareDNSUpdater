import asyncio
import httpx
import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class CloudflareClient:
    BASE = "https://api.cloudflare.com/client/v4"

    def __init__(self, token: str, timeout: float = 10.0):
        self.token = token
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=self.timeout)

    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.BASE}{path}"
        headers = kwargs.pop("headers", {})
        headers.update({"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"})
        backoff = 1.0
        logger.debug(f"CF API Request: {method} {path}")
        for attempt in range(5):
            try:
                resp = await self._client.request(method, url, headers=headers, **kwargs)
                logger.debug(f"CF API Response: {resp.status_code}")
                if resp.status_code == 429:
                    # rate-limited
                    retry = int(resp.headers.get("Retry-After", backoff))
                    logger.warning(f"Rate limited, retrying after {retry}s")
                    await asyncio.sleep(retry)
                    backoff = min(backoff * 2, 60)
                    continue
                resp.raise_for_status()
                data = resp.json()
                logger.debug(f"CF API Response JSON: {data}")
                if not data.get("success", True):
                    logger.error(f"Cloudflare API error: {data.get('errors', [])}")
                return data
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP Error {e.response.status_code}: {e.response.text}")
                if 500 <= e.response.status_code < 600:
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, 60)
                    continue
                # For 4xx errors, print full response for debugging
                logger.error(f"Response body: {e.response.json()}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Request error: {e}")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)
                continue
        raise RuntimeError("Cloudflare request failed after retries")

    async def list_zones(self) -> List[Dict[str, Any]]:
        data = await self._request("GET", "/zones")
        return data.get("result", [])

    async def list_records(self, zone_id: str, record_type: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {}
        if record_type:
            params["type"] = record_type
        data = await self._request("GET", f"/zones/{zone_id}/dns_records", params=params)
        return data.get("result", [])

    async def update_record(self, zone_id: str, record_id: str, content: str, name: Optional[str] = None, record_type: Optional[str] = None) -> Dict[str, Any]:
        payload = {"content": content}
        if name:
            payload["name"] = name
        if record_type:
            payload["type"] = record_type
        data = await self._request("PUT", f"/zones/{zone_id}/dns_records/{record_id}", json=payload)
        return data.get("result", {})

    async def get_record(self, zone_id: str, record_id: str) -> Dict[str, Any]:
        logger.info(f"Fetching record {record_id} from zone {zone_id}")
        data = await self._request("GET", f"/zones/{zone_id}/dns_records/{record_id}")
        return data.get("result", {})

    async def update_record_proxy(self, zone_id: str, record_id: str, proxied: bool) -> Dict[str, Any]:
        # Fetch current record to get all required fields for update
        current_record = await self.get_record(zone_id, record_id)
        # Send ALL required fields according to Cloudflare API documentation
        payload = {
            "type": current_record.get("type"),
            "name": current_record.get("name"),
            "content": current_record.get("content"),
            "ttl": current_record.get("ttl", 3600),
            "proxied": proxied
        }
        logger.info(f"Updating proxy for record {record_id} ({current_record.get('name')}): proxied={proxied}")
        data = await self._request("PUT", f"/zones/{zone_id}/dns_records/{record_id}", json=payload)
        return data.get("result", {})

    async def close(self):
        await self._client.aclose()
