import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_live_flow():
    print("--- STARTING LIVE API INTEGRATION TEST ---")
    session = requests.Session()
    
    # 1. Test Session check (should be 401 Unauthorized since we are not logged in)
    print("\n[Step 1] Verifying /api/auth/session yields 401...")
    res = session.get(f"{BASE_URL}/api/auth/session")
    print(f"Status Code: {res.status_code}")
    assert res.status_code == 401, "Expected 401"
    print("[OK] Unauthorized check passed.")
    
    # 2. Log in with admin / adminpassword
    print("\n[Step 2] Logging in with bootstrap credentials...")
    res = session.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": "admin", "password": "adminpassword"}
    )
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.text}")
    assert res.status_code == 200, "Login failed"
    
    login_data = res.json()
    assert login_data["username"] == "admin"
    assert login_data["role"] == "admin"
    assert bool(login_data["must_change_password"]) is True, "Bootstrap admin should be forced to change password"
    print("[OK] Login succeeded. must_change_password is True.")
    
    # Extract CSRF token from cookies
    csrf_token = session.cookies.get("csrf_token")
    print(f"Issued CSRF Token: {csrf_token}")
    assert csrf_token is not None, "CSRF cookie not issued"
    
    # 3. Try to change password (must provide CSRF token)
    print("\n[Step 3] Updating password to 'SuperStrongPassword123!'...")
    headers = {
        "X-CSRF-Token": csrf_token,
        "Content-Type": "application/json"
    }
    res = session.post(
        f"{BASE_URL}/api/auth/change-password",
        headers=headers,
        json={"current_password": "adminpassword", "new_password": "SuperStrongPassword123!"}
    )
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.text}")
    assert res.status_code == 200, "Password change failed"
    print("[OK] Password updated successfully.")
    
    # 4. Verify session state updated
    print("\n[Step 4] Checking session status after password update...")
    res = session.get(f"{BASE_URL}/api/auth/session")
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.text}")
    assert res.status_code == 200
    
    session_data = res.json()
    assert bool(session_data["must_change_password"]) is False, "must_change_password should now be False"
    print("[OK] Session is active. must_change_password is now False.")
    
    # 5. Register a new user 'operator1'
    print("\n[Step 5] Registering new operator account...")
    res = session.post(
        f"{BASE_URL}/api/auth/register",
        json={"username": "operator1", "password": "OperatorSecret123!"}
    )
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.text}")
    assert res.status_code == 200, "Registration failed"
    print("[OK] Registration submitted successfully.")
    
    # 6. Admin User Management: List users
    print("\n[Step 6] Listing users from admin account...")
    res = session.get(f"{BASE_URL}/api/admin/users")
    print(f"Status Code: {res.status_code}")
    users = res.json()
    print(f"Users Directory: {users}")
    assert res.status_code == 200
    
    # Find operator1
    operator1_user = None
    for u in users:
        if u["username"] == "operator1":
            operator1_user = u
            break
            
    assert operator1_user is not None, "operator1 not found in list"
    assert operator1_user["status"] == "pending", "operator1 should be pending"
    print("[OK] operator1 found in directory as 'pending'.")
    
    # 7. Elevate Privileges (Step-Up Auth) to modify user status (destructive action)
    print("\n[Step 7] Attempting to activate user without Step-Up (should yield 403 step-up check)...")
    res = session.put(
        f"{BASE_URL}/api/admin/users/{operator1_user['id']}/status",
        headers=headers,
        json={"status": "active"}
    )
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.text}")
    assert res.status_code == 403 and "step-up" in res.json()["detail"], "Expected 403 step-up prompt"
    print("[OK] Step-up protection intercept verified.")
    
    print("\nPerforming Step-Up authentication...")
    res = session.post(
        f"{BASE_URL}/api/auth/step-up",
        headers=headers,
        json={"password": "SuperStrongPassword123!"}
    )
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.text}")
    assert res.status_code == 200, "Step-up failed"
    print("[OK] Session stepped-up successfully.")
    
    print("\nRetrying user activation...")
    res = session.put(
        f"{BASE_URL}/api/admin/users/{operator1_user['id']}/status",
        headers=headers,
        json={"status": "active"}
    )
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.text}")
    assert res.status_code == 200, "Activation failed after step-up"
    print("[OK] User status updated to 'active' successfully.")
    
    # 8. Check Audit log chain
    print("\n[Step 8] Checking audit logs...")
    res = session.get(f"{BASE_URL}/api/admin/audit")
    print(f"Status Code: {res.status_code}")
    logs = res.json()
    assert res.status_code == 200
    
    print("\nAudit Logs received:")
    for log in reversed(logs):
        print(f"Seq: #{log['seq']} | Actor: {log['actor']} | Action: {log['action']} | Hash: {log['record_hash'][:16]}...")
        
    # Verify hash linkage mathematical check
    for idx in range(1, len(logs)):
        # Since logs are returned newest first (seq descending)
        current_log = logs[idx - 1]
        previous_log = logs[idx]
        assert current_log["prev_hash"] == previous_log["record_hash"], f"Audit log link broken at Seq #{current_log['seq']}!"
        
    print("\n[OK] Audit log chain validation passed! All hashes are perfectly connected.")
    
    print("\n--- ALL LIVE SECURITY API TESTS PASSED SUCCESSFULLY! ---")

if __name__ == "__main__":
    test_live_flow()
