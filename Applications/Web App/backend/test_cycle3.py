import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://127.0.0.1:8000"

def test_cycle3_endpoints():
    print("--- STARTING CYCLE 3 INTEGRATION TESTS ---")
    session = requests.Session()
    
    # 1. Log in with admin / adminpassword
    print("\n[Step 1] Logging in with bootstrap credentials...")
    res = session.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": "admin", "password": "adminpassword"}
    )
    import re
    if res.status_code != 200:
        sleep_time = 3.5
        match = re.search(r"Try again in (\d+) seconds", res.text)
        if match:
            sleep_time = float(match.group(1)) + 1.0
        print(f"[Note] Initial login with 'adminpassword' failed. Sleeping {sleep_time} seconds to bypass lockout protection...")
        time.sleep(sleep_time)
        print("Attempting login with changed password 'SuperStrongPassword123!'...")
        res = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "admin", "password": "SuperStrongPassword123!"}
        )
        if res.status_code != 200:
            match = re.search(r"Try again in (\d+) seconds", res.text)
            if match:
                sleep_time2 = float(match.group(1)) + 1.0
                print(f"[Note] Locked out again. Sleeping {sleep_time2} seconds to bypass secondary lockout protection...")
                time.sleep(sleep_time2)
                res = session.post(
                    f"{BASE_URL}/api/auth/login",
                    json={"username": "admin", "password": "SuperStrongPassword123!"}
                )
    
    assert res.status_code == 200, f"Login failed: {res.text}"
    
    # Extract CSRF token from cookies
    csrf_token = session.cookies.get("csrf_token")
    headers = {
        "X-CSRF-Token": csrf_token,
        "Content-Type": "application/json"
    }
    print("[OK] Login successful.")
    
    # Check if must_change_password is True, and change it if so!
    login_data = res.json()
    if login_data.get("must_change_password"):
        print("Changing required initial password to 'SuperStrongPassword123!'...")
        change_res = session.post(
            f"{BASE_URL}/api/auth/change-password",
            headers=headers,
            json={"current_password": "adminpassword", "new_password": "SuperStrongPassword123!"}
        )
        assert change_res.status_code == 200, f"Forced password change failed: {change_res.text}"
        # Update CSRF token in case
        csrf_token = session.cookies.get("csrf_token")
        headers["X-CSRF-Token"] = csrf_token
        print("[OK] Password changed from default.")
    
    # 2. Test Agricultural Estimators Calculation Model
    print("\n[Step 2] Testing Agricultural Scenario Estimator calculation...")
    res = session.post(
        f"{BASE_URL}/api/agriculture/estimator/calculate",
        headers=headers,
        json={
            "type": "crop_yield",
            "inputs": {
                "plot_square_footage": 2500,
                "soil_class": "clay_loam",
                "rainfall_anomaly": 0.15
            }
        }
    )
    print(f"Crop Yield Response: {res.text}")
    assert res.status_code == 200
    crop_data = res.json()
    assert "estimated_yield_kg" in crop_data["outputs"]
    assert crop_data["outputs"]["estimated_yield_kg"] > 0
    
    # Test Feed Intake
    res = session.post(
        f"{BASE_URL}/api/agriculture/estimator/calculate",
        headers=headers,
        json={
            "type": "herd_feed",
            "inputs": {
                "animal_count": 45,
                "average_weight": 420.0,
                "stage": "lactating_dairy"
            }
        }
    )
    print(f"Herd Feed Response: {res.text}")
    assert res.status_code == 200
    feed_data = res.json()
    assert "daily_feed_kg" in feed_data["outputs"]
    assert feed_data["outputs"]["daily_feed_kg"] > 0
    
    # Test Estimator History
    res = session.get(f"{BASE_URL}/api/agriculture/estimator/history")
    history = res.json()
    print(f"History list count: {len(history)}")
    assert len(history) >= 2
    print("[OK] Agricultural estimators calc and history checked.")
    
    # 3. Test POS Inventory endpoint
    print("\n[Step 3] Fetching current stock items...")
    res = session.get(f"{BASE_URL}/api/inventory")
    inventory = res.json()
    print(f"Items: {json.dumps(inventory, indent=2)}")
    assert len(inventory) > 0
    
    # Let's target the first inventory item
    target_item = inventory[0]
    target_id = target_item["id"]
    initial_qty = target_item["quantity"]
    print(f"Target Item ID: {target_id} | Initial stock: {initial_qty} {target_item['unit']}")
    
    # 4. Test POS Checkout transaction & Idempotency
    print("\n[Step 4] Testing checkout transactions and X-Client-Request-Id idempotency...")
    req_id = f"test_req_{int(time.time() * 1000)}"
    checkout_headers = {
        "X-CSRF-Token": csrf_token,
        "X-Client-Request-Id": req_id,
        "Content-Type": "application/json"
    }
    
    payload = {
        "total_due_usd": target_item["price_usd"],
        "tenders": [
            {
                "currency": "USD",
                "amount_tendered": target_item["price_usd"],
                "exchange_rate": 1.0,
                "amount_usd_equiv": target_item["price_usd"]
            }
        ],
        "items": [
            {
                "inventory_id": target_id,
                "quantity": 1.0,
                "price_usd_at_sale": target_item["price_usd"]
            }
        ]
    }
    
    # First checkout
    res1 = session.post(f"{BASE_URL}/api/pos/checkout", headers=checkout_headers, json=payload)
    print(f"First checkout: {res1.text}")
    assert res1.status_code == 200
    
    # Verify stock decremented by 1
    res = session.get(f"{BASE_URL}/api/inventory")
    new_qty = [item["quantity"] for item in res.json() if item["id"] == target_id][0]
    print(f"Stock after first checkout: {new_qty}")
    assert new_qty == initial_qty - 1.0
    
    # Retry with same idempotency header (should return cached response and NOT decrement stock again)
    res2 = session.post(f"{BASE_URL}/api/pos/checkout", headers=checkout_headers, json=payload)
    print(f"Idempotency retry: {res2.text}")
    assert res2.status_code == 200
    assert res2.json()["transaction_id"] == res1.json()["transaction_id"]
    
    # Verify stock has NOT changed again
    res = session.get(f"{BASE_URL}/api/inventory")
    final_qty = [item["quantity"] for item in res.json() if item["id"] == target_id][0]
    print(f"Stock after idempotency retry: {final_qty}")
    assert final_qty == new_qty
    print("[OK] Idempotency check verified successfully.")
    
    # 5. Test Wastage logging & stock adjustment
    print("\n[Step 5] Logging spoilage loss...")
    res = session.post(
        f"{BASE_URL}/api/inventory/{target_id}/wastage",
        headers=headers,
        json={"quantity": 1.0, "reason": "spoiled"}
    )
    print(f"Wastage Log Response: {res.text}")
    assert res.status_code == 200
    
    res = session.get(f"{BASE_URL}/api/inventory")
    qty_after_wastage = [item["quantity"] for item in res.json() if item["id"] == target_id][0]
    print(f"Stock after wastage log: {qty_after_wastage}")
    assert qty_after_wastage == final_qty - 1.0
    print("[OK] Spoilage logging confirmed.")
    
    # 6. Test Guard Shift Handover
    print("\n[Step 6] Testing Security Shift Handover logs...")
    
    # Register and activate a different guard for handover
    print("Registering and activating incoming guard 'operator_guard'...")
    session.post(
        f"{BASE_URL}/api/auth/register",
        json={"username": "operator_guard", "password": "OperatorSecret123!"}
    )
    # Step-Up admin session to perform admin actions
    stepup_res = session.post(
        f"{BASE_URL}/api/auth/step-up",
        headers=headers,
        json={"password": "SuperStrongPassword123!"}
    )
    assert stepup_res.status_code == 200, f"Step-up failed: {stepup_res.text}"
    
    # Get user list to find id
    users_res = session.get(f"{BASE_URL}/api/admin/users")
    users = users_res.json()
    op_user = [u for u in users if u["username"] == "operator_guard"][0]
    
    # Activate status
    act_res = session.put(
        f"{BASE_URL}/api/admin/users/{op_user['id']}/status",
        headers=headers,
        json={"status": "active"}
    )
    assert act_res.status_code == 200
    print("[OK] 'operator_guard' registered and active.")

    # First: wrong PIN (should fail with 401)
    res = session.post(
        f"{BASE_URL}/api/security/handover",
        headers=headers,
        json={
            "incoming_guard": "operator_guard",
            "incoming_pin": "9999", # wrong pin (default pin is '1234')
            "shift_type": "night",
            "severity": "green_routine",
            "events_summary": "Handover test entry - wrong pin",
            "cash_expected": {"usd": 0.0, "zar": 0.0, "zwg": 0.0},
            "cash_counted": {"usd": 0.0, "zar": 0.0, "zwg": 0.0}
        }
    )
    print(f"Wrong PIN response (expected 401 error): {res.text}")
    assert res.status_code == 401
    
    # Success Handover
    res = session.post(
        f"{BASE_URL}/api/security/handover",
        headers=headers,
        json={
            "incoming_guard": "operator_guard",
            "incoming_pin": "1234",
            "shift_type": "day",
            "severity": "amber_minor",
            "events_summary": "All systems operating normally, keys passed.",
            "cash_expected": {"usd": 10.0, "zar": 0.0, "zwg": 0.0},
            "cash_counted": {"usd": 10.0, "zar": 0.0, "zwg": 0.0}
        }
    )
    print(f"Success handover response: {res.text}")
    assert res.status_code == 200
    assert "handover_id" in res.json()
    
    # Get Handovers list
    res = session.get(f"{BASE_URL}/api/security/handover/history")
    history_ho = res.json()
    print(f"Shift handovers count: {len(history_ho)}")
    assert len(history_ho) >= 1
    print("[OK] Guard Shift handover checks succeeded.")
    
    # 7. Concurrency Test
    print("\n[Step 7] Running Concurrency Test with multiple threads checkout...")
    res = session.get(f"{BASE_URL}/api/inventory")
    fresh_inventory = res.json()
    target_item_fresh = [item for item in fresh_inventory if item["id"] == target_id][0]
    stock_before_concurrency = target_item_fresh["quantity"]
    price_usd = target_item_fresh["price_usd"]
    print(f"Available stock before concurrent requests: {stock_before_concurrency}")
    
    # Let's fire 5 checkouts concurrently using ThreadPoolExecutor.
    # Each thread will try to checkout 1 item.
    # We will submit unique idempotency keys so each represents a distinct transaction.
    def execute_single_checkout(thread_idx):
        # Create a new requests session per thread or reuse the main cookies
        th_session = requests.Session()
        # copy cookies
        for cookie in session.cookies:
            th_session.cookies.set(cookie.name, cookie.value, domain=cookie.domain, path=cookie.path)
            
        thread_req_id = f"concur_req_{thread_idx}_{int(time.time() * 1000)}"
        th_headers = {
            "X-CSRF-Token": csrf_token,
            "X-Client-Request-Id": thread_req_id,
            "Content-Type": "application/json"
        }
        th_payload = {
            "total_due_usd": price_usd,
            "tenders": [
                {
                    "currency": "USD",
                    "amount_tendered": price_usd,
                    "exchange_rate": 1.0,
                    "amount_usd_equiv": price_usd
                }
            ],
            "items": [
                {
                    "inventory_id": target_id,
                    "quantity": 1.0,
                    "price_usd_at_sale": price_usd
                }
            ]
        }
        
        try:
            th_res = th_session.post(f"{BASE_URL}/api/pos/checkout", headers=th_headers, json=th_payload)
            return th_res.status_code, th_res.text
        except Exception as e:
            return 500, str(e)
            
    num_threads = 5
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(execute_single_checkout, i) for i in range(num_threads)]
        results = [f.result() for f in futures]
        
    print("\nConcurrent Checkout Results:")
    success_count = 0
    failure_count = 0
    for idx, (status, body) in enumerate(results):
        print(f"Thread #{idx}: Status {status} | Body: {body}")
        if status == 200:
            success_count += 1
        else:
            failure_count += 1
            
    print(f"\nSuccessful checkouts: {success_count} | Failed checkouts: {failure_count}")
    
    # Verify final stock count
    res = session.get(f"{BASE_URL}/api/inventory")
    stock_after_concurrency = [item["quantity"] for item in res.json() if item["id"] == target_id][0]
    print(f"Stock after concurrency: {stock_after_concurrency}")
    
    # The stock must have decreased EXACTLY by the number of successful checkouts
    assert stock_after_concurrency == stock_before_concurrency - success_count
    # And it must not have gone below 0
    assert stock_after_concurrency >= 0
    
    print("[OK] Concurrency transaction safety check passed.")
    print("\n--- ALL CYCLE 3 BACKEND API TESTS PASSED SUCCESSFULLY! ---")

if __name__ == "__main__":
    test_cycle3_endpoints()
