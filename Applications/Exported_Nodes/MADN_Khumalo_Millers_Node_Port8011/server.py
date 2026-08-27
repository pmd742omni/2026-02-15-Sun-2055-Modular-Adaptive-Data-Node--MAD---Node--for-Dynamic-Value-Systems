"""
MADN Portable Node Server (Khumalo_Millers_Node - data-node-khumalo_millers_node-21fe71)
Role: DATA_NODE | Port: 8011
"""

import os
import sys
import json
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Local storage and discovery modules
from storage import DataNodeStorage
from beacon import BeaconBroadcaster

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("madn.khumalo_millers_node")

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "node_config.json")

def load_node_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"node_id": "data-node-khumalo_millers_node-21fe71", "node_name": "Khumalo_Millers_Node", "node_type": "data_node", "port": 8011, "is_active": True}

def save_node_config(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

cfg = load_node_config()
NODE_ID = cfg.get("node_id", "data-node-khumalo_millers_node-21fe71")
NODE_NAME = cfg.get("node_name", "Khumalo_Millers_Node")
NODE_TYPE = cfg.get("node_type", "data_node")
NODE_PORT = int(cfg.get("port", 8011))
IS_ACTIVE = cfg.get("is_active", True)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_store")
storage = DataNodeStorage(data_dir=DATA_DIR)
broadcaster = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global broadcaster, IS_ACTIVE
    logger.info(f"Starting Portable Node '{NODE_NAME}' ({NODE_ID}) on port {NODE_PORT}")
    stats = storage.get_storage_stats()
    broadcaster = BeaconBroadcaster(
        node_id=NODE_ID,
        node_type=NODE_TYPE,
        port=NODE_PORT,
        metadata={
            "node_name": NODE_NAME,
            "storage_engine": "sqlite_wal",
            "free_mb": stats.get("free_mb", 0),
            "is_active": IS_ACTIVE
        }
    )
    if IS_ACTIVE:
        broadcaster.start()
        logger.info("[+] Discovery beacon broadcasting active.")
    else:
        logger.info("[*] Node initialized in DEACTIVATED / STANDBY mode.")
    yield
    if broadcaster:
        broadcaster.stop()
    logger.info(f"Node {NODE_ID} halted cleanly.")

app = FastAPI(title=f"MADN Portable Node - {NODE_NAME}", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PutRecordRequest(BaseModel):
    collection: str
    key: str
    data: str

class NodeReconfigureRequest(BaseModel):
    node_name: Optional[str] = None
    parent_vault_url: Optional[str] = None

@app.get("/api/node/status")
def node_status():
    global IS_ACTIVE
    stats = storage.get_storage_stats()
    return {
        "node_id": NODE_ID,
        "node_name": NODE_NAME,
        "node_type": NODE_TYPE,
        "port": NODE_PORT,
        "is_active": IS_ACTIVE,
        "storage": stats
    }

@app.post("/api/node/activate")
def activate_node():
    global IS_ACTIVE, broadcaster
    IS_ACTIVE = True
    cfg = load_node_config()
    cfg["is_active"] = True
    save_node_config(cfg)
    if broadcaster and not broadcaster.running:
        broadcaster.start()
    return {"status": "success", "message": f"Node '{NODE_NAME}' is now ACTIVE", "is_active": True}

@app.post("/api/node/deactivate")
def deactivate_node():
    global IS_ACTIVE, broadcaster
    IS_ACTIVE = False
    cfg = load_node_config()
    cfg["is_active"] = False
    save_node_config(cfg)
    if broadcaster and broadcaster.running:
        broadcaster.stop()
    return {"status": "success", "message": f"Node '{NODE_NAME}' is now DEACTIVATED (Standby)", "is_active": False}

@app.post("/api/node/reconfigure")
def reconfigure_node(req: NodeReconfigureRequest):
    global NODE_NAME
    cfg = load_node_config()
    if req.node_name:
        NODE_NAME = req.node_name
        cfg["node_name"] = req.node_name
    if req.parent_vault_url:
        cfg["parent_vault_url"] = req.parent_vault_url
    save_node_config(cfg)
    return {"status": "success", "config": cfg}

# KV Storage Endpoints
@app.get("/api/storage/stats")
def get_stats():
    return storage.get_storage_stats()

@app.post("/api/storage/put")
def put_record(req: PutRecordRequest):
    if not IS_ACTIVE:
        raise HTTPException(status_code=503, detail="Node is currently DEACTIVATED (Standby Mode). Cannot accept writes.")
    storage.put_record(req.collection, req.key, req.data)
    return {"status": "success", "collection": req.collection, "key": req.key}

@app.get("/api/storage/get")
def get_record(collection: str = Query(...), key: str = Query(...)):
    data = storage.get_record(collection, key)
    if data is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"status": "success", "collection": collection, "key": key, "data": data}

@app.get("/api/storage/list")
def list_records(collection: str = Query(None), limit: int = 50):
    return {"status": "success", "records": storage.list_records(collection, limit)}

# Static Web UI serving
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def serve_index():
    idx_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(idx_path):
        return FileResponse(idx_path)
    return {
        "message": f"MADN Portable Node '{NODE_NAME}' Online",
        "node_id": NODE_ID,
        "role": NODE_TYPE,
        "status": "active" if IS_ACTIVE else "deactivated"
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="MADN Portable Node Server")
    parser.add_argument("port", nargs="?", type=int, default=NODE_PORT, help="Port to bind")
    parser.add_argument("--ssl-keyfile", type=str, default=None, help="Path to TLS private key")
    parser.add_argument("--ssl-certfile", type=str, default=None, help="Path to TLS certificate")
    args, _ = parser.parse_known_args()

    ssl_kwargs = {}
    if args.ssl_keyfile and args.ssl_certfile and os.path.exists(args.ssl_keyfile) and os.path.exists(args.ssl_certfile):
        ssl_kwargs["ssl_keyfile"] = args.ssl_keyfile
        ssl_kwargs["ssl_certfile"] = args.ssl_certfile

    uvicorn.run(app, host="0.0.0.0", port=args.port, **ssl_kwargs)
