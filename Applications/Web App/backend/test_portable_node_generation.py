"""
Automated Test Suite for Portable Node Generator & Lifecycle Management
========================================================================
Validates:
1. Portable node package synthesis and file structure.
2. Configuration schema and metadata validity.
3. Standalone Data Node lifecycle endpoints (active/deactive/maintenance mode).
4. Vault Node generation and exported package listing APIs.
5. start.py preflight and compilation integrity.
"""

import os
import sys
import json
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient

# Add project paths
BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
APPS_DIR = os.path.abspath(os.path.join(BACKEND_DIR, "..", ".."))
DATA_NODE_DIR = os.path.join(APPS_DIR, "Data_Node")

if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)
if APPS_DIR not in sys.path:
    sys.path.append(APPS_DIR)
if DATA_NODE_DIR not in sys.path:
    sys.path.append(DATA_NODE_DIR)

from node_generator import generate_portable_node, list_exported_nodes
from data_node import app as data_node_app
from main import app as vault_app
from database import init_db


@pytest.fixture(scope="module", autouse=True)
def setup_environment():
    init_db()
    yield


def test_portable_node_generation_and_file_structure():
    """Validates that generate_portable_node creates a complete, self-contained bundle."""
    temp_dir = tempfile.mkdtemp(prefix="madn_test_node_")
    try:
        res = generate_portable_node(
            name="Alpha_Edge_Sensor",
            node_type="data_node",
            port=8009,
            storage_quota_mb=1024,
            parent_vault_url="http://127.0.0.1:8000",
            target_dir=temp_dir
        )

        assert res["status"] == "created"
        assert res["port"] == 8009
        assert res["node_name"] == "Alpha_Edge_Sensor"

        # Check critical files
        expected_files = [
            "start.py",
            "server.py",
            "storage.py",
            "beacon.py",
            "node_config.json",
            "requirements.txt",
            "README.md",
            os.path.join("frontend", "index.html")
        ]
        for ef in expected_files:
            fpath = os.path.join(temp_dir, ef)
            assert os.path.exists(fpath), f"Missing expected file in bundle: {ef}"

        # Verify config JSON
        with open(os.path.join(temp_dir, "node_config.json"), "r", encoding="utf-8") as f:
            cfg = json.load(f)
            assert cfg["node_name"] == "Alpha_Edge_Sensor"
            assert cfg["node_type"] == "data_node"
            assert cfg["port"] == 8009
            assert cfg["is_active"] is True
            assert cfg["storage_quota_mb"] == 1024
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_data_node_lifecycle_and_maintenance_mode():
    """Validates Data Node remote activation, deactivation, and write gating."""
    client = TestClient(data_node_app)

    # 1. Health & status
    res = client.get("/api/node/status")
    assert res.status_code == 200
    data = res.json()
    assert data["node_type"] == "data_node"
    assert data["is_active"] is True

    # 2. Put record while active
    res = client.post("/api/storage/put", json={"collection": "telemetry", "key": "sensor-1", "data": "24.5C"})
    assert res.status_code == 200

    # 3. Deactivate node
    res = client.post("/api/node/deactivate")
    assert res.status_code == 200
    assert res.json()["is_active"] is False

    # 4. Put record while deactivated (must fail with 503)
    res = client.post("/api/storage/put", json={"collection": "telemetry", "key": "sensor-2", "data": "25.0C"})
    assert res.status_code == 503
    assert "DEACTIVATED" in res.json()["detail"]

    # 5. Reactivate node
    res = client.post("/api/node/activate")
    assert res.status_code == 200
    assert res.json()["is_active"] is True

    # 6. Put record succeeds again
    res = client.post("/api/storage/put", json={"collection": "telemetry", "key": "sensor-2", "data": "25.0C"})
    assert res.status_code == 200


def test_vault_cluster_api_exported_list_and_generation():
    """Validates Vault Node endpoints for portable generation and bundle listing."""
    from main import get_current_user, require_admin

    vault_app.dependency_overrides[get_current_user] = lambda: {"username": "admin", "role": "admin"}
    vault_app.dependency_overrides[require_admin] = lambda: {"username": "admin", "role": "admin"}

    csrf = "test_csrf_token_12345"

    try:
        client = TestClient(vault_app, cookies={"csrf_token": csrf})

        # 1. List exported nodes
        res = client.get("/api/cluster/nodes/exported-list")
        assert res.status_code == 200
        assert "exported_nodes" in res.json()

        # 2. Generate a new node pack via REST API
        gen_res = client.post(
            "/api/cluster/nodes/generate-portable",
            json={
                "name": "Khumalo_Millers_Node",
                "node_type": "data_node",
                "port": 8011,
                "storage_quota_mb": 1024
            },
            headers={"X-CSRF-Token": csrf}
        )
        assert gen_res.status_code == 200
        pkg = gen_res.json()["package"]
        assert pkg["port"] == 8011
        assert os.path.exists(pkg["node_dir"])
    finally:
        vault_app.dependency_overrides.clear()


def test_start_py_syntax_and_compilation():
    """Validates that Applications/start.py compiles cleanly."""
    start_py_path = os.path.join(APPS_DIR, "start.py")
    assert os.path.exists(start_py_path)
    
    with open(start_py_path, "r", encoding="utf-8") as f:
        code = f.read()
    
    # Must compile without SyntaxError
    compiled = compile(code, start_py_path, "exec")
    assert compiled is not None
