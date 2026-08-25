#!/usr/bin/env python3
"""
Automated Pytest Suite for Operator Profile Management, Profile Picture Persistence,
and Foreign-Key Safe Username Cascading.
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main import app
from database import init_db

@pytest.fixture(scope="module")
def auth_session():
    init_db()
    c = TestClient(app)
    # Authenticate as admin
    login_res = c.post("/api/auth/login", json={"username": "admin", "password": "Password123!"})
    assert login_res.status_code == 200
    csrf = login_res.cookies.get("csrf_token", "")
    headers = {"X-CSRF-Token": csrf}
    return c, headers

def test_01_fetch_operator_profile(auth_session):
    """Ensure operator profile endpoint returns contact details, wallet, and avatar URL."""
    client, headers = auth_session
    res = client.get("/api/user/profile", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "username" in data
    assert "account_number" in data
    assert "wallet" in data
    assert "avatar_url" in data
    assert "pin_set" in data

def test_02_update_profile_and_avatar_picture(auth_session):
    """Ensure updating full name, phone, email, PIN, and avatar picture works with 200 OK."""
    client, headers = auth_session
    sample_avatar = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP..."
    
    update_res = client.put("/api/user/profile", json={
        "full_name": "Peter Mthokozisi Dube",
        "phone": "+263782876567",
        "email": "ignazie742@gmail.com",
        "username": "admin",
        "pin": "5678",
        "avatar_url": sample_avatar
    }, headers=headers)
    
    assert update_res.status_code == 200
    updated = update_res.json().get("profile", {})
    assert updated["full_name"] == "Peter Mthokozisi Dube"
    assert updated["phone"] == "+263782876567"
    assert updated["email"] == "ignazie742@gmail.com"
    assert updated["avatar_url"] == sample_avatar
    assert updated["pin_set"] is True

def test_03_profile_validation_rules(auth_session):
    """Ensure invalid PINs or invalid short usernames return graceful 400 Bad Request."""
    client, headers = auth_session
    
    # Invalid PIN (not 4 digits)
    bad_pin = client.put("/api/user/profile", json={
        "pin": "12"
    }, headers=headers)
    assert bad_pin.status_code == 400
    
    # Invalid short username
    bad_user = client.put("/api/user/profile", json={
        "username": "ab"
    }, headers=headers)
    assert bad_user.status_code == 400
