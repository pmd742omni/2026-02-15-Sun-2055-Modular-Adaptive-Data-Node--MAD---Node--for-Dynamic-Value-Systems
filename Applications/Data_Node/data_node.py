"""
Modular Adaptive Data Node (MAD-Node) - Standalone Data Node Service
Can run in any directory, on any computer or VM on the local subnet.
Broadcasts discovery beacons over UDP Multicast (224.0.0.251:8001) and serves
localized ACID data requests over FastAPI HTTP.
"""

import os
import sys
import uuid
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Local imports
from beacon import BeaconBroadcaster
from storage import DataNodeStorage

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
    logger.info(f"Starting Standalone Data Node: {NODE_ID} on port {NODE_PORT}")
    stats = storage.get_storage_stats()
    broadcaster = BeaconBroadcaster(
        node_id=NODE_ID,
        node_type="data_node",
        port=NODE_PORT,
        metadata={
            "storage_engine": "sqlite_wal",
            "free_mb": stats["free_mb"],
            "db_path": stats["db_path"],
            "is_active": IS_ACTIVE
        }
    )
    if IS_ACTIVE:
        broadcaster.start()
    yield
    if broadcaster:
        broadcaster.stop()
    logger.info(f"Data Node {NODE_ID} shut down successfully.")


app = FastAPI(title=f"MAD-Node Data Node - {NODE_ID}", lifespan=lifespan)

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
    return {"status": "success", "message": f"Data Node {NODE_ID} is now ACTIVE", "is_active": True}


@app.post("/api/node/deactivate")
def deactivate_node():
    global IS_ACTIVE, broadcaster
    IS_ACTIVE = False
    if broadcaster and broadcaster.running:
        broadcaster.stop()
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


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else NODE_PORT
    uvicorn.run("data_node:app", host="0.0.0.0", port=port, reload=False)
