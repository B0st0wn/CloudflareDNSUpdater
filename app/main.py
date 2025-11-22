import os
import asyncio
import logging
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import httpx

from .config import ConfigManager
from .sync import SyncEngine
from .cloudflare_client import CloudflareClient

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s %(message)s')

class ImportRecordsRequest(BaseModel):
    zone_id: str
    record_ids: list = None

DATA_DIR = os.environ.get("DATA_DIR", "/data")
CONFIG_SECRET = os.environ.get("CONFIG_SECRET")

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

cfg = ConfigManager(secret=CONFIG_SECRET)
sync_engine = SyncEngine(cfg, interval=cfg.load_polling_interval())

@app.on_event("startup")
async def startup_event():
    await sync_engine.start()

@app.on_event("shutdown")
async def shutdown_event():
    await sync_engine.stop()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    token_present = cfg.load_token() is not None
    records = cfg.load_records().get("records", [])
    return templates.TemplateResponse("dashboard.html", {"request": request, "token_present": token_present, "records": records})

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/api/status")
async def api_status():
    token = cfg.load_token()
    records = cfg.load_records().get("records", [])
    polling_interval = cfg.load_polling_interval()
    return {"token_configured": bool(token), "record_count": len(records), "polling_interval": polling_interval}

@app.post("/api/polling-interval")
async def api_set_polling_interval(interval: int = None):
    if interval is None or interval < 60:
        raise HTTPException(status_code=400, detail="Polling interval must be at least 60 seconds")
    cfg.save_polling_interval(interval)
    # Update the running sync engine interval
    sync_engine.interval = interval
    logger.info(f"Polling interval updated to {interval} seconds")
    return {"ok": True, "polling_interval": interval}

@app.get("/api/config")
async def get_config():
    token = cfg.load_token()
    return {"token_configured": bool(token)}

@app.post("/api/config")
async def post_config(token: str = Form(...)):
    # accept token via form
    cfg.save_token(token)
    return RedirectResponse(url='/', status_code=303)

@app.get("/api/zones")
async def api_zones():
    token = cfg.load_token()
    if not token:
        raise HTTPException(status_code=400, detail="No token configured")
    try:
        cf = CloudflareClient(token)
        zones = await cf.list_zones()
        await cf.close()
        logger.info(f"Fetched {len(zones)} zones from Cloudflare")
        return zones
    except Exception as e:
        logger.exception(f"Error fetching zones: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch zones: {str(e)}")

@app.get("/api/zones/{zone_id}/records")
async def api_zone_records(zone_id: str):
    token = cfg.load_token()
    if not token:
        raise HTTPException(status_code=400, detail="No token configured")
    try:
        cf = CloudflareClient(token)
        # Fetch A and AAAA records
        a_records = await cf.list_records(zone_id, record_type="A")
        aaaa_records = await cf.list_records(zone_id, record_type="AAAA")
        await cf.close()
        all_records = a_records + aaaa_records
        logger.info(f"Fetched {len(all_records)} A/AAAA records for zone {zone_id}")
        return {"records": all_records}
    except Exception as e:
        logger.exception(f"Error fetching records for zone {zone_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch records: {str(e)}")

@app.post("/api/import-records")
async def api_import_records(req: ImportRecordsRequest):
    """Import selected records from Cloudflare into local storage."""
    token = cfg.load_token()
    if not token:
        raise HTTPException(status_code=400, detail="No token configured")
    try:
        cf = CloudflareClient(token)
        a_records = await cf.list_records(req.zone_id, record_type="A")
        aaaa_records = await cf.list_records(req.zone_id, record_type="AAAA")
        await cf.close()
        all_records = a_records + aaaa_records
        
        # If record_ids provided, filter; otherwise import all
        if req.record_ids:
            all_records = [r for r in all_records if r.get("id") in req.record_ids]
        
        # Convert to internal format and save
        data = cfg.load_records()
        stored_records = data.get("records", [])
        
        imported_count = 0
        for cf_record in all_records:
            # Check if already imported
            if any(sr.get("record_id") == cf_record.get("id") for sr in stored_records):
                continue
            stored_records.append({
                "zone_id": req.zone_id,
                "record_id": cf_record.get("id"),
                "name": cf_record.get("name"),
                "type": cf_record.get("type"),
                "content": cf_record.get("content"),
                "auto_update": False
            })
            imported_count += 1
        
        cfg.save_records({"records": stored_records})
        logger.info(f"Imported {imported_count} records with auto_update enabled")
        return {"ok": True, "imported": imported_count}
    except Exception as e:
        logger.exception(f"Error importing records: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to import records: {str(e)}")

@app.get("/api/records")
async def api_records():
    return cfg.load_records()

@app.post("/api/records")
async def api_add_record(payload: dict):
    data = cfg.load_records()
    recs = data.get("records", [])
    recs.append(payload)
    cfg.save_records({"records": recs})
    return {"ok": True}

@app.patch("/api/records")
async def api_patch_record(record_id: str = None, auto_update: str = None):
    data = cfg.load_records()
    recs = data.get("records", [])
    for r in recs:
        if r.get("record_id") == record_id:
            if auto_update is not None:
                # Handle checkbox string values from HTMX
                r["auto_update"] = auto_update.lower() in ('true', '1', 'on', 'yes')
            cfg.save_records({"records": recs})
            return {"ok": True}
    raise HTTPException(status_code=404, detail="Record not found")

@app.delete("/api/records")
async def api_delete_record(id: str):
    data = cfg.load_records()
    recs = data.get("records", [])
    recs = [r for r in recs if r.get("record_id") != id]
    cfg.save_records({"records": recs})
    return {"ok": True}

@app.get("/api/records/{record_id}/proxy")
async def api_get_record_proxy(record_id: str):
    """Get proxy status for a record."""
    token = cfg.load_token()
    if not token:
        raise HTTPException(status_code=400, detail="No token configured")
    try:
        data = cfg.load_records()
        records = data.get("records", [])
        rec = next((r for r in records if r.get("record_id") == record_id), None)
        if not rec:
            raise HTTPException(status_code=404, detail="Record not found")
        
        zone_id = rec.get("zone_id")
        cf = CloudflareClient(token)
        record = await cf.get_record(zone_id, record_id)
        await cf.close()
        
        proxied = record.get("proxied", False)
        logger.info(f"Retrieved proxy status for {rec.get('name')}: {proxied}")
        return {"proxied": proxied}
    except Exception as e:
        logger.exception(f"Error getting proxy status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get proxy status: {str(e)}")

@app.patch("/api/records/{record_id}/proxy")
async def api_set_record_proxy(record_id: str, proxied: str = None):
    """Set proxy status for a record."""
    token = cfg.load_token()
    if not token:
        raise HTTPException(status_code=400, detail="No token configured")
    try:
        # Convert string to boolean
        if proxied is None:
            raise HTTPException(status_code=400, detail="proxied parameter required")
        proxied_bool = proxied.lower() in ('true', '1', 'on', 'yes')
        
        data = cfg.load_records()
        records = data.get("records", [])
        rec = next((r for r in records if r.get("record_id") == record_id), None)
        if not rec:
            raise HTTPException(status_code=404, detail="Record not found")
        
        zone_id = rec.get("zone_id")
        cf = CloudflareClient(token)
        updated = await cf.update_record_proxy(zone_id, record_id, proxied_bool)
        await cf.close()
        
        logger.info(f"Updated proxy status for {rec.get('name')}: {proxied_bool}")
        return {"ok": True, "proxied": proxied_bool}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error setting proxy status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to set proxy status: {str(e)}")

@app.post("/api/update-now")
async def api_update_now():
    # run one sync loop
    loop = asyncio.get_event_loop()
    await sync_engine._run_once()
    return {"ok": True}
