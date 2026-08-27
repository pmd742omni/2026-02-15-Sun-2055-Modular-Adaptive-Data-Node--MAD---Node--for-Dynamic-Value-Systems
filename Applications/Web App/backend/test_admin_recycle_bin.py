import pytest
import sqlite3
import time
from fastapi.testclient import TestClient
from main import app, get_db
from auth_utils import hash_password

client = TestClient(app)

def create_admin_and_operator():
    db = get_db()
    # Ensure test admin
    salt, pwd_hash = hash_password("AdminPass123!")
    cursor = db.execute("SELECT id FROM users WHERE username = 'test_admin_rb'")
    admin_row = cursor.fetchone()
    if not admin_row:
        cursor = db.execute("""
            INSERT INTO users (username, password_hash, salt, role, status, full_name, email, created_at, updated_at, is_deleted)
            VALUES (?, ?, ?, 'admin', 'active', 'Test Admin RB', 'admin_rb@example.com', ?, ?, 0)
        """, ("test_admin_rb", pwd_hash, salt, int(time.time()), int(time.time())))
        admin_id = cursor.lastrowid
    else:
        admin_id = admin_row["id"]

    # Ensure test operator
    cursor = db.execute("SELECT id FROM users WHERE username = 'test_operator_rb'")
    op_row = cursor.fetchone()
    if not op_row:
        cursor = db.execute("""
            INSERT INTO users (username, password_hash, salt, role, status, full_name, email, created_at, updated_at, is_deleted)
            VALUES (?, ?, ?, 'merchant', 'active', 'Test Operator RB', 'operator_rb@example.com', ?, ?, 0)
        """, ("test_operator_rb", pwd_hash, salt, int(time.time()), int(time.time())))
        op_id = cursor.lastrowid
    else:
        op_id = op_row["id"]
        db.execute("UPDATE users SET is_deleted = 0, status = 'active' WHERE id = ?", (op_id,))

    db.commit()
    db.close()
    return admin_id, op_id

def test_recycle_bin_full_lifecycle():
    admin_id, op_id = create_admin_and_operator()

    # 1. Login as Admin
    client.cookies.clear()
    login_res = client.post("/api/auth/login", json={"username": "test_admin_rb", "password": "AdminPass123!"})
    assert login_res.status_code == 200
    client.cookies.update(login_res.cookies)

    csrf_token = login_res.cookies.get("csrf_token", "")
    headers = {"X-CSRF-Token": csrf_token} if csrf_token else {}

    # Step-up elevation for admin
    stepup_res = client.post("/api/auth/step-up", json={"password": "AdminPass123!"}, headers=headers)
    assert stepup_res.status_code == 200

    # 2. List active users (should include test_operator_rb)
    users_res = client.get("/api/admin/users", headers=headers)
    assert users_res.status_code == 200
    usernames = [u["username"] for u in users_res.json()]
    assert "test_operator_rb" in usernames

    # 3. Soft delete test_operator_rb (Move to Recycle Bin)
    del_res = client.delete(f"/api/admin/users/{op_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["deleted"] is True

    # 4. Confirm operator is NOT in active users list
    users_after_del = client.get("/api/admin/users", headers=headers)
    usernames_after = [u["username"] for u in users_after_del.json()]
    assert "test_operator_rb" not in usernames_after

    # 5. Confirm operator cannot log in
    op_login = client.post("/api/auth/login", json={"username": "test_operator_rb", "password": "AdminPass123!"})
    assert op_login.status_code == 403

    # 6. List Recycle Bin (should contain test_operator_rb)
    rb_res = client.get("/api/admin/users/recycle-bin", headers=headers)
    assert rb_res.status_code == 200
    rb_users = [u["username"] for u in rb_res.json()]
    assert "test_operator_rb" in rb_users

    # 7. Restore operator from Recycle Bin
    restore_res = client.post(f"/api/admin/users/{op_id}/restore", headers=headers)
    assert restore_res.status_code == 200
    assert restore_res.json()["restored"] is True

    # 8. Confirm operator is back in active users list
    users_after_restore = client.get("/api/admin/users", headers=headers)
    usernames_restored = [u["username"] for u in users_after_restore.json()]
    assert "test_operator_rb" in usernames_restored

    # 9. Move back to Recycle Bin and test Permanent Purge
    client.delete(f"/api/admin/users/{op_id}", headers=headers)
    perm_res = client.delete(f"/api/admin/users/{op_id}/permanent", headers=headers)
    assert perm_res.status_code == 200
    assert perm_res.json()["permanent_delete"] is True

    # Confirm completely gone from database
    db = get_db()
    row = db.execute("SELECT id FROM users WHERE id = ?", (op_id,)).fetchone()
    db.close()
    assert row is None
