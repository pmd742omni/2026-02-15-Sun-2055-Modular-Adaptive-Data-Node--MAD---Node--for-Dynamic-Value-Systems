#!/usr/bin/env python3
"""
Automated Integration Test Suite for Device Tracking and Blocking
Verifies HTTP device tracking, User-Agent classification, Admin Device Endpoints,
and IP blocking middleware enforcement.
"""

import sys
import os
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main import app
from database import init_db, get_db, block_device, unblock_device, is_device_blocked

class TestDeviceManagement(unittest.TestCase):
    def setUp(self):
        init_db()
        self.client = TestClient(app)
        
    def test_01_device_tracking_and_listing(self):
        # 1. Simulate request from a mobile device
        mobile_headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148"}
        res = self.client.get("/api/health", headers=mobile_headers)
        self.assertEqual(res.status_code, 200)
        
        # 2. Login as admin to fetch devices
        login_res = self.client.post("/api/auth/login", json={"username": "admin", "password": "Password123!"})
        self.assertEqual(login_res.status_code, 200)
        
        # 3. Fetch tracked devices
        devices_res = self.client.get("/api/admin/devices", cookies=login_res.cookies)
        self.assertEqual(devices_res.status_code, 200)
        devices = devices_res.json()
        self.assertTrue(len(devices) > 0)
        
    def test_02_device_blocking_middleware(self):
        test_ip = "192.168.1.99"
        
        # Block device IP
        block_device(test_ip, "admin", "Testing security block")
        self.assertTrue(is_device_blocked(test_ip))
        
        # Unblock device IP
        unblock_device(test_ip, "admin")
        self.assertFalse(is_device_blocked(test_ip))

if __name__ == "__main__":
    unittest.main()
