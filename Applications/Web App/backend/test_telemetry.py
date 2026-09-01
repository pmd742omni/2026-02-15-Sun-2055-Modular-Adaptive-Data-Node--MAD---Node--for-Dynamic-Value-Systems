"""
Automated Test Suite for System Telemetry & Hardware Diagnostics Engine
Verifies psutil host sampling, process working set metrics, API profiling middleware,
and diagnostics log ingestion.
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from telemetry import system_telemetry

client = TestClient(app)


def test_01_system_telemetry_snapshot_metrics():
    """Verify that the telemetry manager captures host hardware and process stats."""
    snapshot = system_telemetry.get_system_snapshot()
    assert "host" in snapshot
    assert "backend" in snapshot
    assert "database" in snapshot

    # Host assertions
    host = snapshot["host"]
    assert "cpu_percent" in host
    assert "cpu_cores" in host
    assert host["cpu_cores"] >= 1
    assert "ram_total_gb" in host
    assert host["ram_total_gb"] > 0
    assert "ram_used_gb" in host
    assert "ram_percent" in host

    # Backend process assertions
    backend = snapshot["backend"]
    assert "process_ram_mb" in backend
    assert backend["process_ram_mb"] > 0
    assert "threads" in backend
    assert backend["threads"] >= 1

    # Database assertions
    db = snapshot["database"]
    assert "db_size_kb" in db
    assert "wal_active" in db


def test_02_system_telemetry_rest_endpoint():
    """Verify GET /api/system/telemetry endpoint."""
    res = client.get("/api/system/telemetry")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "telemetry" in data
    assert "host" in data["telemetry"]
    assert "backend" in data["telemetry"]


def test_03_client_telemetry_log_ingestion():
    """Verify POST /api/system/telemetry/log endpoint ingests client-side performance events."""
    payload = {
        "type": "long_task_freeze",
        "data": {
            "durationMs": 75,
            "name": "self",
            "attribution": "store_setup_render"
        }
    }
    res = client.post("/api/system/telemetry/log", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"

    # Verify log tail retrieval
    log_res = client.get("/api/system/telemetry/diagnostics-log?lines=20")
    assert log_res.status_code == 200
    log_data = log_res.json()
    assert log_data["status"] == "success"
    assert isinstance(log_data["logs"], list)
    assert any("CLIENT_LONG_TASK_FREEZE" in line for line in log_data["logs"])


def test_04_request_profiling_middleware_header():
    """Verify that HTTP responses include the high-resolution X-Process-Time-Ms header."""
    res = client.get("/api/health")
    assert res.status_code == 200
    assert "X-Process-Time-Ms" in res.headers
    process_time = float(res.headers["X-Process-Time-Ms"])
    assert process_time >= 0.0
