"""
Modular Adaptive Data Node (MAD-Node) - Standalone Data Node Service
Can run in any directory, on any computer or VM on the local subnet.
Broadcasts discovery beacons over UDP Multicast (224.0.0.251:8001) and serves
localized ACID data requests over FastAPI HTTP.
"""

import os
import sys

# Ensure UTF-8 formatting on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import time
import json
import uuid
import logging
import datetime
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from beacon import BeaconBroadcaster
from storage import DataNodeStorage
from currency_collector import get_complete_global_catalog, fetch_online_fiat_updates

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("madn.data_node")

# Configuration
NODE_ID = os.getenv("MADN_DATA_NODE_ID", f"data-node-{uuid.uuid4().hex[:8]}")
NODE_PORT = int(os.getenv("MADN_DATA_NODE_PORT", "8002"))
DATA_DIR = os.getenv("MADN_DATA_DIR", "./data_store")
IS_ACTIVE = True

storage = DataNodeStorage(data_dir=DATA_DIR)
broadcaster = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global broadcaster, IS_ACTIVE
    stats = storage.get_storage_stats()
    
    print("\n" + "=" * 70)
    print(f"   MADN STANDALONE DATA NODE [{NODE_PORT}] • LIVE ACTIVITY TRACKER")
    print("   Modular Adaptive Data Node Ecosystem — High-Performance Storage")
    print("=" * 70)
    print(f"  [*] Node Identifier:   {NODE_ID}")
    print(f"  [*] Local Binding Port: {NODE_PORT}")
    print(f"  [*] Storage Engine:    SQLite WAL (Encrypted at Rest AES-256-GCM)")
    print(f"  [*] Storage Database:  {stats['db_path']}")
    print(f"  [*] Free Disk Space:   {stats['free_mb']} MB available")
    print(f"  [*] UDP Multicast:     224.0.0.251:8001 (Heartbeat: 5.0s)")
    print(f"  [*] Currency Registry: 170+ ISO Fiats & Cryptos Active")
    print("=" * 70)
    print("[LIVE ACTIVITY STREAM — REAL-TIME DISCOVERY & STORAGE TELEMETRY]\n")
    sys.stdout.flush()

    broadcaster = BeaconBroadcaster(
        node_id=NODE_ID,
        node_type="data_node",
        port=NODE_PORT,
        interval=5.0,
        metadata={
            "storage_engine": "sqlite_wal",
            "free_mb": stats["free_mb"],
            "db_path": stats["db_path"],
            "is_active": IS_ACTIVE
        }
    )
    if IS_ACTIVE:
        broadcaster.start()
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 📡 BeaconBroadcaster active on 224.0.0.251:8001 (Interval: 5.0s)")
    yield
    if broadcaster:
        broadcaster.stop()
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🛑 Data Node {NODE_ID} gracefully stopped.")


app = FastAPI(title=f"MAD-Node Data Node - {NODE_ID}", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def telemetry_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    latency_ms = (time.perf_counter() - start_time) * 1000
    now_str = datetime.datetime.now().strftime("%H:%M:%S")
    
    path = request.url.path
    query_str = f"?{request.url.query}" if request.url.query else ""
    client_ip = request.client.host if request.client else "127.0.0.1"
    status_icon = "🟢" if response.status_code < 400 else "🔴"

    print(f"[{now_str}] {status_icon} {request.method:<4} {path + query_str:<38} -> {response.status_code} ({latency_ms:5.2f}ms) [{client_ip}]")
    sys.stdout.flush()
    return response


class PutRecordRequest(BaseModel):
    collection: str
    key: str
    data: str


@app.get("/health")
def health():
    stats = storage.get_storage_stats()
    return {
        "status": "healthy" if IS_ACTIVE else "deactivated",
        "node_id": NODE_ID,
        "node_type": "data_node",
        "port": NODE_PORT,
        "is_active": IS_ACTIVE,
        "storage": stats
    }


@app.get("/api/node/status")
def get_node_status():
    stats = storage.get_storage_stats()
    return {
        "node_id": NODE_ID,
        "node_type": "data_node",
        "port": NODE_PORT,
        "is_active": IS_ACTIVE,
        "storage": stats
    }


@app.post("/api/node/activate")
def activate_node():
    global IS_ACTIVE, broadcaster
    IS_ACTIVE = True
    if broadcaster and not broadcaster.running:
        broadcaster.start()
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🟢 Node Activated: {NODE_ID}")
    return {"status": "success", "message": f"Data Node {NODE_ID} is now ACTIVE", "is_active": True}


@app.post("/api/node/deactivate")
def deactivate_node():
    global IS_ACTIVE, broadcaster
    IS_ACTIVE = False
    if broadcaster and broadcaster.running:
        broadcaster.stop()
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ⏸️ Node Deactivated (Standby Mode): {NODE_ID}")
    return {"status": "success", "message": f"Data Node {NODE_ID} is now DEACTIVATED (Standby)", "is_active": False}


@app.get("/api/storage/stats")
def get_stats():
    return storage.get_storage_stats()


@app.post("/api/storage/put")
def put_record(req: PutRecordRequest):
    if not IS_ACTIVE:
        raise HTTPException(status_code=503, detail="Data Node is currently DEACTIVATED (Standby Mode).")
    storage.put_record(req.collection, req.key, req.data)
    return {"status": "success", "collection": req.collection, "key": req.key}


@app.get("/api/storage/get")
def get_record(collection: str = Query(...), key: str = Query(...)):
    data = storage.get_record(collection, key)
    if data is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"status": "success", "collection": collection, "key": key, "data": data}


@app.get("/api/storage/list")
def list_records(collection: str = Query(...)):
    records = storage.list_records(collection)
    return {"status": "success", "collection": collection, "records": records}


@app.get("/api/reference/currencies")
def get_reference_currencies():
    """Returns authoritative ISO 4217 world currencies and top cryptocurrencies."""
    catalog = get_complete_global_catalog()
    return {"status": "success", "count": len(catalog), "currencies": catalog}


@app.post("/api/reference/currencies/collect")
def collect_live_currencies():
    """Attempts live online sync with open currency APIs and stores new records."""
    live_updates = fetch_online_fiat_updates()
    stored_count = 0
    if live_updates:
        for item in live_updates:
            storage.put_record("global_currency_catalog", item["code"], json.dumps(item))
            stored_count += 1
    return {
        "status": "success",
        "live_fetched": len(live_updates),
        "persisted_to_storage": stored_count,
        "mode": "online_updated" if live_updates else "air_gapped_fallback"
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="MADN Standalone Data Node")
    parser.add_argument("port", nargs="?", type=int, default=NODE_PORT, help="Port to bind data node service")
    parser.add_argument("--ssl-keyfile", type=str, default=os.getenv("MADN_SSL_KEYFILE"), help="Path to TLS private key")
    parser.add_argument("--ssl-certfile", type=str, default=os.getenv("MADN_SSL_CERTFILE"), help="Path to TLS certificate")
    args, unknown = parser.parse_known_args()

    ssl_kwargs = {}
    if args.ssl_keyfile and args.ssl_certfile and os.path.exists(args.ssl_keyfile) and os.path.exists(args.ssl_certfile):
        ssl_kwargs["ssl_keyfile"] = args.ssl_keyfile
        ssl_kwargs["ssl_certfile"] = args.ssl_certfile

    uvicorn.run("data_node:app", host="0.0.0.0", port=args.port, reload=False, **ssl_kwargs)
