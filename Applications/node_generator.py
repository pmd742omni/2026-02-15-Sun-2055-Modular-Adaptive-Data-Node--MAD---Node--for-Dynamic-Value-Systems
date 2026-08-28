#!/usr/bin/env python3
"""
MADN Portable Node Generator Engine
===================================
Generates fully self-contained, self-bootstrapping, and portable node folders
(Data Nodes, Peer Vault Nodes, or Hybrid Nodes) that can be copied to any computer
or server, executed via `python start.py`, and managed remotely by other Vault Nodes.
"""

import os
import sys
import json
import uuid
import shutil
import stat
import datetime
from typing import Dict, Any, Optional

APPLICATIONS_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORTED_NODES_DIR = os.path.join(APPLICATIONS_DIR, "Exported_Nodes")
DATA_NODE_SRC = os.path.join(APPLICATIONS_DIR, "Data_Node")


def safe_write_file(filepath: str, content: str, encoding: str = "utf-8"):
    """Safely write to a file, removing existing file if present to avoid Windows lock/permissions."""
    if os.path.exists(filepath):
        try:
            os.chmod(filepath, stat.S_IWRITE | stat.S_IREAD)
            os.remove(filepath)
        except Exception:
            pass
    with open(filepath, "w", encoding=encoding) as f:
        f.write(content)


def safe_copy(src: str, dst: str):
    """Safely copy a file, removing existing file if present to avoid Windows lock/permissions."""
    if os.path.exists(dst):
        try:
            os.chmod(dst, stat.S_IWRITE | stat.S_IREAD)
            os.remove(dst)
        except Exception:
            pass
    shutil.copy2(src, dst)


def generate_portable_node(
    name: str,
    node_type: str = "data_node",
    port: int = 8005,
    storage_quota_mb: int = 2048,
    parent_vault_url: str = "http://127.0.0.1:8000",
    target_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates a self-contained portable node bundle.
    """
    clean_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in name.strip())
    node_id = f"{node_type.replace('_', '-')}-{clean_name.lower()}-{uuid.uuid4().hex[:6]}"
    
    if not target_dir:
        os.makedirs(EXPORTED_NODES_DIR, exist_ok=True)
        bundle_dir = os.path.join(EXPORTED_NODES_DIR, f"MADN_{clean_name}_Port{port}")
    else:
        bundle_dir = os.path.abspath(target_dir)

    os.makedirs(bundle_dir, exist_ok=True)
    frontend_dir = os.path.join(bundle_dir, "frontend")
    os.makedirs(frontend_dir, exist_ok=True)
    data_store_dir = os.path.join(bundle_dir, "data_store")
    os.makedirs(data_store_dir, exist_ok=True)

    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # 1. Write node_config.json
    config_data = {
        "node_id": node_id,
        "node_name": name,
        "node_type": node_type,
        "port": port,
        "host": "0.0.0.0",
        "is_active": True,
        "storage_engine": "sqlite_wal",
        "storage_quota_mb": storage_quota_mb,
        "parent_vault_url": parent_vault_url,
        "created_at_utc": now_utc,
        "version": "1.19.55"
    }
    safe_write_file(os.path.join(bundle_dir, "node_config.json"), json.dumps(config_data, indent=2))

    # 2. Copy or synthesize storage.py, beacon.py & tls_manager.py
    safe_copy(os.path.join(DATA_NODE_SRC, "storage.py"), os.path.join(bundle_dir, "storage.py"))
    safe_copy(os.path.join(DATA_NODE_SRC, "beacon.py"), os.path.join(bundle_dir, "beacon.py"))
    tls_src = os.path.join(APPLICATIONS_DIR, "tls_manager.py")
    if os.path.exists(tls_src):
        safe_copy(tls_src, os.path.join(bundle_dir, "tls_manager.py"))

    # 3. Write server.py (FastAPI Backend with Lifecycle Endpoints & Web UI Serving)
    server_py_content = f'''"""
MADN Portable Node Server ({name} - {node_id})
Role: {node_type.upper()} | Port: {port}
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
logger = logging.getLogger("madn.{clean_name.lower()}")

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "node_config.json")

def load_node_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {{"node_id": "{node_id}", "node_name": "{name}", "node_type": "{node_type}", "port": {port}, "is_active": True}}

def save_node_config(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

cfg = load_node_config()
NODE_ID = cfg.get("node_id", "{node_id}")
NODE_NAME = cfg.get("node_name", "{name}")
NODE_TYPE = cfg.get("node_type", "{node_type}")
NODE_PORT = int(cfg.get("port", {port}))
IS_ACTIVE = cfg.get("is_active", True)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_store")
storage = DataNodeStorage(data_dir=DATA_DIR)
broadcaster = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global broadcaster, IS_ACTIVE
    logger.info(f"Starting Portable Node '{{NODE_NAME}}' ({{NODE_ID}}) on port {{NODE_PORT}}")
    stats = storage.get_storage_stats()
    broadcaster = BeaconBroadcaster(
        node_id=NODE_ID,
        node_type=NODE_TYPE,
        port=NODE_PORT,
        metadata={{
            "node_name": NODE_NAME,
            "storage_engine": "sqlite_wal",
            "free_mb": stats.get("free_mb", 0),
            "is_active": IS_ACTIVE
        }}
    )
    if IS_ACTIVE:
        broadcaster.start()
        logger.info("[+] Discovery beacon broadcasting active.")
    else:
        logger.info("[*] Node initialized in DEACTIVATED / STANDBY mode.")
    yield
    if broadcaster:
        broadcaster.stop()
    logger.info(f"Node {{NODE_ID}} halted cleanly.")

app = FastAPI(title=f"MADN Portable Node - {{NODE_NAME}}", lifespan=lifespan)

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
    return {{
        "node_id": NODE_ID,
        "node_name": NODE_NAME,
        "node_type": NODE_TYPE,
        "port": NODE_PORT,
        "is_active": IS_ACTIVE,
        "storage": stats
    }}

@app.post("/api/node/activate")
def activate_node():
    global IS_ACTIVE, broadcaster
    IS_ACTIVE = True
    cfg = load_node_config()
    cfg["is_active"] = True
    save_node_config(cfg)
    if broadcaster and not broadcaster.running:
        broadcaster.start()
    return {{"status": "success", "message": f"Node '{{NODE_NAME}}' is now ACTIVE", "is_active": True}}

@app.post("/api/node/deactivate")
def deactivate_node():
    global IS_ACTIVE, broadcaster
    IS_ACTIVE = False
    cfg = load_node_config()
    cfg["is_active"] = False
    save_node_config(cfg)
    if broadcaster and broadcaster.running:
        broadcaster.stop()
    return {{"status": "success", "message": f"Node '{{NODE_NAME}}' is now DEACTIVATED (Standby)", "is_active": False}}

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
    return {{"status": "success", "config": cfg}}

# KV Storage Endpoints
@app.get("/api/storage/stats")
def get_stats():
    return storage.get_storage_stats()

@app.post("/api/storage/put")
def put_record(req: PutRecordRequest):
    if not IS_ACTIVE:
        raise HTTPException(status_code=503, detail="Node is currently DEACTIVATED (Standby Mode). Cannot accept writes.")
    storage.put_record(req.collection, req.key, req.data)
    return {{"status": "success", "collection": req.collection, "key": req.key}}

@app.get("/api/storage/get")
def get_record(collection: str = Query(...), key: str = Query(...)):
    data = storage.get_record(collection, key)
    if data is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return {{"status": "success", "collection": collection, "key": key, "data": data}}

@app.get("/api/storage/list")
def list_records(collection: str = Query(None), limit: int = 50):
    return {{"status": "success", "records": storage.list_records(collection, limit)}}

# Static Web UI serving
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def serve_index():
    idx_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(idx_path):
        return FileResponse(idx_path)
    return {{
        "message": f"MADN Portable Node '{{NODE_NAME}}' Online",
        "node_id": NODE_ID,
        "role": NODE_TYPE,
        "status": "active" if IS_ACTIVE else "deactivated"
    }}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="MADN Portable Node Server")
    parser.add_argument("port", nargs="?", type=int, default=NODE_PORT, help="Port to bind")
    parser.add_argument("--ssl-keyfile", type=str, default=None, help="Path to TLS private key")
    parser.add_argument("--ssl-certfile", type=str, default=None, help="Path to TLS certificate")
    args, _ = parser.parse_known_args()

    ssl_kwargs = {{}}
    if args.ssl_keyfile and args.ssl_certfile and os.path.exists(args.ssl_keyfile) and os.path.exists(args.ssl_certfile):
        ssl_kwargs["ssl_keyfile"] = args.ssl_keyfile
        ssl_kwargs["ssl_certfile"] = args.ssl_certfile

    uvicorn.run(app, host="0.0.0.0", port=args.port, **ssl_kwargs)
'''
    safe_write_file(os.path.join(bundle_dir, "server.py"), server_py_content)

    # 4. Write start.py for the portable bundle
    bundle_start_content = f'''#!/usr/bin/env python3
"""
Portable Launcher for {name} ({node_type.upper()})
=====================================================
Run this file on any computer with Python 3.9+ installed to start this node.
"""

import os
import sys
import time
import subprocess
import threading
import webbrowser

REQUIRED_PACKAGES = ["fastapi", "uvicorn", "pydantic", "jinja2", "cryptography"]

def check_and_install():
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"[*] Installing dependencies for {name}: {{missing}}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
        except Exception as e:
            print(f"[!] Pip warning: {{e}}")

def open_browser():
    time.sleep(1.2)
    url = f"https://127.0.0.1:{port}"
    print(f"[*] Opening browser at {{url}} ...")
    try:
        webbrowser.open(url)
    except Exception:
        pass

if __name__ == "__main__":
    check_and_install()

    # Generate or verify local X.509 TLS Certificates
    cert_file, key_file = None, None
    try:
        if os.path.exists("tls_manager.py"):
            from tls_manager import ensure_ssl_certificates
            cert_file, key_file = ensure_ssl_certificates(certs_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), "certs"))
    except Exception as e:
        print(f"[!] TLS Notice: {{e}}")

    print(f"=======================================================")
    print(f"   STARTING PORTABLE NODE: {name} ({node_type.upper()})")
    print(f"   Port: {port} | ID: {node_id}")
    print(f"   Web UI: https://127.0.0.1:{port}")
    print(f"=======================================================")
    threading.Thread(target=open_browser, daemon=True).start()
    server_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server.py")
    cmd = [sys.executable, server_path, str({port})]
    if cert_file and key_file:
        cmd.extend(["--ssl-keyfile", key_file, "--ssl-certfile", cert_file])
    subprocess.call(cmd)
'''
    safe_write_file(os.path.join(bundle_dir, "start.py"), bundle_start_content)

    # 5. Write requirements.txt & README.md
    safe_write_file(os.path.join(bundle_dir, "requirements.txt"), "fastapi>=0.100.0\nuvicorn>=0.22.0\npydantic>=2.0.0\njinja2>=3.1.0\n")

    readme_content = f"""# MADN Portable Node: {name}

**Node ID**: `{node_id}`  
**Role**: `{node_type}`  
**Default Port**: `{port}`  
**Created**: `{now_utc}`  

## Quick Start
1. Ensure Python 3.9+ is installed.
2. Run the portable bootstrapper:
   ```bash
   python start.py
   ```
3. Open your browser to:
   [http://127.0.0.1:{port}](http://127.0.0.1:{port})

## Remote Lifecycle Management
This node can be discovered, activated, deactivated, and managed remotely by any authorized Vault Node on the local subnet via REST API:
- `GET /api/node/status`
- `POST /api/node/activate`
- `POST /api/node/deactivate`
- `POST /api/storage/put`
- `GET /api/storage/get`
"""
    safe_write_file(os.path.join(bundle_dir, "README.md"), readme_content)

    # 6. Write standalone glassmorphic frontend
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MADN Node | {name}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-dark: #0a0e17;
      --card-bg: rgba(20, 27, 45, 0.7);
      --card-border: rgba(255, 255, 255, 0.08);
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --accent-cyan: #38bdf8;
      --accent-emerald: #10b981;
      --accent-rose: #f43f5e;
      --accent-amber: #f59e0b;
      --radius: 16px;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Inter', sans-serif;
      background: radial-gradient(circle at 15% 15%, #1e1b4b 0%, #0a0e17 60%, #030712 100%);
      color: var(--text-main);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 24px;
    }}
    .container {{ width: 100%; max-width: 900px; display: flex; flex-direction: column; gap: 20px; }}
    .header-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--radius);
      padding: 24px;
      backdrop-filter: blur(20px);
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    .node-title {{ display: flex; align-items: center; gap: 12px; }}
    .node-icon {{ font-size: 2rem; }}
    .node-h1 {{ font-size: 1.4rem; font-weight: 700; }}
    .node-sub {{ font-size: 0.8rem; color: var(--text-muted); font-family: 'JetBrains Mono', monospace; }}
    .status-badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 14px;
      border-radius: 9999px;
      font-weight: 600;
      font-size: 0.85rem;
    }}
    .status-active {{ background: rgba(16, 185, 129, 0.15); color: var(--accent-emerald); border: 1px solid rgba(16, 185, 129, 0.3); }}
    .status-deactive {{ background: rgba(244, 63, 94, 0.15); color: var(--accent-rose); border: 1px solid rgba(244, 63, 94, 0.3); }}
    .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }}
    .stat-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--radius);
      padding: 20px;
      backdrop-filter: blur(20px);
    }}
    .stat-label {{ font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); margin-bottom: 6px; }}
    .stat-value {{ font-size: 1.6rem; font-weight: 700; color: #fff; }}
    .controls-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--radius);
      padding: 24px;
      backdrop-filter: blur(20px);
    }}
    .btn {{
      padding: 10px 20px;
      border-radius: 10px;
      border: none;
      font-weight: 600;
      cursor: pointer;
      font-size: 0.9rem;
      transition: all 0.2s;
    }}
    .btn-emerald {{ background: var(--accent-emerald); color: #fff; }}
    .btn-emerald:hover {{ opacity: 0.9; transform: translateY(-1px); }}
    .btn-rose {{ background: var(--accent-rose); color: #fff; }}
    .btn-rose:hover {{ opacity: 0.9; transform: translateY(-1px); }}
    .btn-outline {{ background: transparent; border: 1px solid var(--card-border); color: var(--text-main); }}
    .btn-outline:hover {{ background: rgba(255,255,255,0.05); }}
    .table-container {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--radius);
      padding: 20px;
      backdrop-filter: blur(20px);
      overflow-x: auto;
    }}
    table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 0.85rem; }}
    th, td {{ padding: 12px; border-bottom: 1px solid var(--card-border); }}
    th {{ color: var(--text-muted); font-weight: 600; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header-card">
      <div class="node-title">
        <div class="node-icon">📦</div>
        <div>
          <h1 class="node-h1">{name}</h1>
          <div class="node-sub">ID: {node_id} | Port: {port} | Role: {node_type.upper()}</div>
        </div>
      </div>
      <div id="node-status-badge" class="status-badge status-active">🟢 Active</div>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">Storage Engine</div>
        <div class="stat-value" style="font-size: 1.2rem; color: var(--accent-cyan);">SQLite WAL</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Free Storage</div>
        <div class="stat-value" id="stat-free-mb">-- MB</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">KV Records</div>
        <div class="stat-value" id="stat-records">0</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Mesh Beacon</div>
        <div class="stat-value" style="font-size: 1.2rem; color: var(--accent-amber);">224.0.0.251:8001</div>
      </div>
    </div>

    <div class="controls-card">
      <h3 style="margin-bottom: 14px;">Node Lifecycle Operations</h3>
      <div style="display: flex; gap: 12px; flex-wrap: wrap;">
        <button id="btn-activate" class="btn btn-emerald" onclick="toggleActive(true)">⚡ Activate Node</button>
        <button id="btn-deactivate" class="btn btn-rose" onclick="toggleActive(false)">⏸️ Deactivate Node</button>
        <button class="btn btn-outline" onclick="loadNodeData()">🔄 Refresh</button>
        <a href="{parent_vault_url}" target="_blank" style="text-decoration:none;"><button class="btn btn-outline">🌐 Open Parent Vault</button></a>
      </div>
    </div>

    <div class="table-container">
      <h3 style="margin-bottom: 14px;">Local Storage Key-Value Browser</h3>
      <table>
        <thead>
          <tr>
            <th>Collection</th>
            <th>Key</th>
            <th>Data Preview</th>
            <th>Updated</th>
          </tr>
        </thead>
        <tbody id="kv-tbody">
          <tr><td colspan="4" style="text-align:center; color: var(--text-muted);">Loading storage records...</td></tr>
        </tbody>
      </table>
    </div>
  </div>

  <script>
    async function loadNodeData() {{
      try {{
        const res = await fetch('/api/node/status');
        const data = await res.json();
        const badge = document.getElementById('node-status-badge');
        if (data.is_active) {{
          badge.className = 'status-badge status-active';
          badge.innerText = '🟢 Active';
        }} else {{
          badge.className = 'status-badge status-deactive';
          badge.innerText = '🔴 Deactivated (Standby)';
        }}
        if (data.storage) {{
          document.getElementById('stat-free-mb').innerText = (data.storage.free_mb || 0).toLocaleString() + ' MB';
        }}
        loadRecords();
      }} catch (e) {{
        console.error("Status fetch error:", e);
      }}
    }}

    async function loadRecords() {{
      try {{
        const res = await fetch('/api/storage/list?limit=25');
        const data = await res.json();
        const tbody = document.getElementById('kv-tbody');
        const recs = data.records || [];
        document.getElementById('stat-records').innerText = recs.length;
        if (recs.length === 0) {{
          tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color: var(--text-muted);">No records currently stored.</td></tr>';
          return;
        }}
        tbody.innerHTML = recs.map(r => `
          <tr>
            <td><strong style="color: var(--accent-cyan);">${{r.collection}}</strong></td>
            <td><code style="font-size:0.8rem;">${{r.key}}</code></td>
            <td style="color: var(--text-muted); max-width:300px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${{r.data}}</td>
            <td style="font-size:0.75rem;">${{r.updated_at}}</td>
          </tr>
        `).join('');
      }} catch (e) {{
        console.error("Records fetch error:", e);
      }}
    }}

    async function toggleActive(targetState) {{
      const endpoint = targetState ? '/api/node/activate' : '/api/node/deactivate';
      try {{
        const res = await fetch(endpoint, {{ method: 'POST' }});
        const data = await res.json();
        alert(data.message || 'Updated');
        loadNodeData();
      }} catch (e) {{
        alert('Action failed: ' + e.message);
      }}
    }}

    window.addEventListener('DOMContentLoaded', loadNodeData);
  </script>
</body>
</html>
"""
    safe_write_file(os.path.join(frontend_dir, "index.html"), html_content)

    return {
        "status": "created",
        "node_id": node_id,
        "node_name": name,
        "node_type": node_type,
        "port": port,
        "node_dir": bundle_dir,
        "config": config_data
    }


def list_exported_nodes() -> list:
    """Returns metadata of all exported portable nodes."""
    nodes = []
    if not os.path.exists(EXPORTED_NODES_DIR):
        return nodes

    for item in os.listdir(EXPORTED_NODES_DIR):
        subpath = os.path.join(EXPORTED_NODES_DIR, item)
        if os.path.isdir(subpath):
            cfg_path = os.path.join(subpath, "node_config.json")
            if os.path.exists(cfg_path):
                try:
                    with open(cfg_path, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                        cfg["node_dir"] = subpath
                        nodes.append(cfg)
                except Exception:
                    pass
    return nodes


if __name__ == "__main__":
    if len(sys.argv) >= 4:
        name_arg = sys.argv[1]
        type_arg = sys.argv[2]
        port_arg = int(sys.argv[3])
        out_arg = sys.argv[4] if len(sys.argv) >= 5 else None
        res = generate_portable_node(name_arg, type_arg, port_arg, target_dir=out_arg)
        print(json.dumps(res, indent=2))
    else:
        print("Usage: python node_generator.py <NAME> <TYPE> <PORT> [OUTPUT_DIR]")
        print("Available exported nodes:")
        print(json.dumps(list_exported_nodes(), indent=2))
