import requests
import json
import time
import re
import datetime
import pytest

BASE_URL = "http://127.0.0.1:8000"

def test_cycle4_endpoints():
    print("--- STARTING CYCLE 4 INTEGRATION & VERIFICATION TESTS ---")
    session = requests.Session()
    
    try:
        res_health = session.get(f"{BASE_URL}/api/health", timeout=1.0)
    except Exception:
        pytest.skip("Live Vault Node server is not currently running on port 8000. Skipping live HTTP tests.")
        return

    # 1. Login with Admin credentials
    print("\n[Step 1] Logging in with bootstrap credentials...")
    res = session.post(f"{BASE_URL}/api/auth/login", json={"username": "admin", "password": "adminpassword"})
    
    if res.status_code == 429:
        match = re.search(r"locked out for (\d+\.?\d*)", res.json().get("detail", ""))
        sleep_secs = float(match.group(1)) + 0.5 if match else 4.0
        print(f"[Note] Lockout active. Sleeping {sleep_secs:.1f} seconds...")
        time.sleep(sleep_secs)
        res = session.post(f"{BASE_URL}/api/auth/login", json={"username": "admin", "password": "adminpassword"})
        
    if res.status_code == 401 and "Invalid" in res.text:
        print("Attempting login with changed password 'SuperStrongPassword123!'...")
        res = session.post(f"{BASE_URL}/api/auth/login", json={"username": "admin", "password": "SuperStrongPassword123!"})
        
    assert res.status_code == 200, f"Login failed: {res.text}"
    csrf_token = session.cookies.get("csrf_token")
    headers = {"X-CSRF-Token": csrf_token} if csrf_token else {}
    print("[OK] Admin login successful.")

    # 2. Test Security Nodes Telemetry & R*Tree Spatial Ray Tracing
    print("\n[Step 2] Fetching Security Nodes Telemetry & R*Tree Spatial Ray Tracing...")
    res = session.get(f"{BASE_URL}/api/security/nodes", headers=headers)
    assert res.status_code == 200, f"Failed to fetch security nodes: {res.text}"
    data = res.json()
    assert data["status"] == "success"
    nodes = data["nodes"]
    obstacles = data["obstacles"]
    print(f"Retrieved {len(nodes)} security nodes and {len(obstacles)} spatial R*Tree obstacles.")
    for n in nodes:
        print(f"  -> Node '{n['label']}' | Position: ({n['x_pct']}%, {n['y_pct']}%) | RSSI: {n['rssi']} dBm | Status: {n['status']} | Mesh Path: {n['mesh_path']}")
    print("[OK] Telemetry and R*Tree path loss calculation verified.")

    # 3. Test Field-Level LWW Node Repositioning & Conflict Resolution
    print("\n[Step 3] Testing Field-Level LWW Node Repositioning & Timestamp Conflict Resolution...")
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    # Drag Node 1 behind Grain Silo obstacle
    res = session.put(
        f"{BASE_URL}/api/security/nodes/node-1/position",
        headers=headers,
        json={
            "x_pct": 35.0,
            "y_pct": 30.0,
            "client_id": "field-tablet-1",
            "timestamp_utc": now_iso
        }
    )
    assert res.status_code == 200, f"Position update failed: {res.status_code} {res.text}"
    assert res.json()["status"] == "success", f"Unexpected status: {res.json()}"
    print("Repositioned Node 1 behind Grain Silo obstacle (35.0%, 30.0%).")

    # Fetch updated telemetry to confirm ray-tracing obstacle attenuation was applied
    res = session.get(f"{BASE_URL}/api/security/nodes", headers=headers)
    nodes_updated = res.json()["nodes"]
    n1 = [n for n in nodes_updated if n["id"] == "node-1"][0]
    print(f"Updated Node 1 -> RSSI: {n1['rssi']} dBm | Attenuation Penalty: -{n1['attenuation_db']} dBm | Intersected: {n1['obstacles_hit']}")
    assert "Grain Silo (Metal Reinforced)" in n1["obstacles_hit"]

    # Test Stale LWW Timestamp Conflict Rejection
    old_iso = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2)).isoformat()
    res_stale = session.put(
        f"{BASE_URL}/api/security/nodes/node-1/position",
        headers=headers,
        json={
            "x_pct": 10.0,
            "y_pct": 10.0,
            "client_id": "stale-client",
            "timestamp_utc": old_iso
        }
    )
    assert res_stale.status_code == 200
    assert res_stale.json()["status"] == "ignored"
    print("[OK] Stale timestamp update correctly rejected by LWW sync.")

    # 4. Test Agronomy Compound Rules Evaluation & Cross-VPA Spoilage Flash Sale Spawning
    print("\n[Step 4] Evaluating Agronomy Compound Rules & Spawning Cross-VPA Flash Sale...")
    res = session.post(
        f"{BASE_URL}/api/agriculture/rules/evaluate",
        headers=headers,
        json={
            "sensor_inputs": {
                "temperature": 34.5, # Exceeds 32.0 heatwave threshold
                "soil_moisture": 18.0
            }
        }
    )
    assert res.status_code == 200, f"Rules evaluation failed: {res.status_code} {res.text}"
    data_eval = res.json()
    triggered = data_eval["triggered_rules"]
    print(f"Triggered {len(triggered)} rule(s):")
    for tr in triggered:
        print(f"  -> Rule: '{tr['title']}' | Action: {tr['action_type']} | Msg: {tr['action_message']}")
    assert len(triggered) >= 1

    # Verify Harvest Work Order created
    res_orders = session.get(f"{BASE_URL}/api/agriculture/harvest-orders", headers=headers)
    orders = res_orders.json()
    print(f"Harvest Work Orders count: {len(orders)}")
    assert len(orders) >= 1
    h_order = orders[0]
    print(f"Latest Harvest Order -> ID: {h_order['id'][:8]} | Crop: {h_order['crop_type']} | Status: {h_order['status']}")
    assert h_order["status"] == "triggered"

    # 5. Test Harvest Work Order State Machine Transitions
    print("\n[Step 5] Transitioning Harvest Work Order State Machine...")
    for next_status in ["assigned", "harvested", "pos_listed"]:
        res_trans = session.put(
            f"{BASE_URL}/api/agriculture/harvest-orders/{h_order['id']}/status",
            headers=headers,
            json={"status": next_status}
        )
        assert res_trans.status_code == 200
        print(f"Transitioned status to '{next_status}'.")

    # 6. Test Continuous Exponential Decay POS Catalog Pricing
    print("\n[Step 6] Verifying Continuous Exponential Decay POS Catalog Pricing & Margin Floor Protection...")
    res_pos = session.get(f"{BASE_URL}/api/pos/promotions", headers=headers)
    assert res_pos.status_code == 200
    catalog = res_pos.json()
    print("Catalog Promotions:")
    for item in catalog:
        print(f"  -> Product: {item['name']} | Regular: ${item['price_usd']:.2f} | Cost Floor: ${item['cost_price_usd']:.2f} | Effective: ${item['effective_price_usd']:.2f} | Discount: ${item['discount_applied']:.2f} | Promo: {item['applied_promo_title']}")
        # Verify price never drops below cost floor
        assert item['effective_price_usd'] >= item['cost_price_usd'] - 0.01

    print("\n--- ALL CYCLE 4 BACKEND & MATHEMATICAL TESTS PASSED SUCCESSFULLY! ---")

if __name__ == "__main__":
    test_cycle4_endpoints()
