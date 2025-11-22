import asyncio
import logging
import os
import time
from typing import Dict, List
import httpx

from .config import ConfigManager
from .cloudflare_client import CloudflareClient
from .ip_detect import detect_wan_ip

LOG_DIR = os.path.join(os.environ.get("DATA_DIR", "/data"), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
logger = logging.getLogger("cf_ddns")
fh = logging.FileHandler(os.path.join(LOG_DIR, "sync.log"))
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)
logger.setLevel(logging.INFO)

class SyncEngine:
    def __init__(self, cfg: ConfigManager, interval: int = 300):
        self.cfg = cfg
        self.interval = interval
        self._task = None
        self._running = False

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _loop(self):
        while self._running:
            try:
                await self._run_once()
            except Exception as e:
                logger.exception("Sync loop error: %s", e)
            await asyncio.sleep(self.interval)

    async def _run_once(self):
        token = self.cfg.load_token()
        if not token:
            logger.info("No Cloudflare token configured; skipping sync")
            return
        cf = CloudflareClient(token)
        async with httpx.AsyncClient() as client:
            ip = await detect_wan_ip(client)
        if not ip:
            logger.warning("Could not detect WAN IP")
            await cf.close()
            return
        logger.info(f"Detected WAN IP: {ip}")

        data = self.cfg.load_records()
        records = data.get("records", [])
        updated_any = False
        
        for rec in records:
            if not rec.get("auto_update"):
                continue
            zone_id = rec.get("zone_id")
            record_id = rec.get("record_id")
            name = rec.get("name")
            record_type = rec.get("type")
            current = rec.get("content")
            if current == ip:
                logger.info(f"Record {name} already matches {ip}")
                continue
            try:
                updated = await cf.update_record(zone_id, record_id, ip, name=name, record_type=record_type)
                rec["content"] = ip
                updated_any = True
                logger.info(f"Updated {name} -> {ip}")
            except Exception as e:
                logger.exception(f"Failed to update {name}: {e}")
        
        if updated_any:
            self.cfg.save_records(data)
        
        await cf.close()
        self.cfg.save_records({"records": records})
        await cf.close()
