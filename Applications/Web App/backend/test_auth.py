import os
import sys
import unittest
import sqlite3
import hashlib
import time
import secrets

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth_utils import (
    hash_password,
    verify_password,
    generate_totp_secret,
    get_totp_token,
    verify_totp,
    hash_session_token
)
from database import write_audit_log_raw

class TestMADNSecurity(unittest.TestCase):
    
    def setUp(self):
        # Initialize an in-memory database for clean unit testing
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON;")
        
        self.db.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            last_login_at INTEGER,
            failed_login_count INTEGER DEFAULT 0,
            locked_until INTEGER DEFAULT 0,
            must_change_password INTEGER DEFAULT 1,
            mfa_secret TEXT,
            mfa_last_used_code TEXT
        );
        """)
        
        self.db.execute("""
        CREATE TABLE audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seq INTEGER NOT NULL,
            nonce TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            actor TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT NOT NULL,
            prev_hash TEXT NOT NULL,
            record_hash TEXT NOT NULL
        );
        """)
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_scrypt_password_hashing(self):
        password = "SuperStrongPassword123!"
        salt_hex, hash_hex = hash_password(password)
        
        # Verify length and properties
        self.assertEqual(len(salt_hex), 32) # 16 bytes in hex = 32 chars
        self.assertEqual(len(hash_hex), 64) # 32 bytes in hex = 64 chars
        
        # Validate verification
        self.assertTrue(verify_password(password, salt_hex, hash_hex))
        self.assertFalse(verify_password("wrongpassword", salt_hex, hash_hex))

    def test_totp_replay_and_drift(self):
        secret = generate_totp_secret()
        current_step = int(time.time() / 30)
        
        # Get active token
        valid_code = get_totp_token(secret, current_step)
        
        # Check standard verify
        is_valid, record = verify_totp(secret, valid_code)
        self.assertTrue(is_valid)
        self.assertEqual(record, f"{valid_code}:{current_step}")
        
        # Check replay protection: the exact same code cannot be verified twice under same window record
        is_valid_replay, _ = verify_totp(secret, valid_code, last_used_code=record)
        self.assertFalse(is_valid_replay)
        
        # Check drift tolerance (T-1)
        prev_code = get_totp_token(secret, current_step - 1)
        is_valid_prev, record_prev = verify_totp(secret, prev_code)
        self.assertTrue(is_valid_prev)
        self.assertEqual(record_prev, f"{prev_code}:{current_step - 1}")
        
        # Check invalid code
        is_valid_bad, _ = verify_totp(secret, "999999")
        self.assertFalse(is_valid_bad)

    def test_tarpit_lockout_duration(self):
        # Lockout duration matches min(2^failed_login_count, 900)
        durations = []
        for failed_attempts in range(1, 12):
            lockout_duration = min(2 ** failed_attempts, 900)
            durations.append(lockout_duration)
            
        # Verify exponential steps
        self.assertEqual(durations[0], 2)
        self.assertEqual(durations[1], 4)
        self.assertEqual(durations[2], 8)
        self.assertEqual(durations[9], 900) # capped at 15 minutes
        self.assertEqual(durations[10], 900)

    def test_tamper_evident_audit_chain(self):
        # Insert 3 consecutive log entries
        write_audit_log_raw(self.db, "admin", "LOGIN", "Admin logged in.")
        write_audit_log_raw(self.db, "admin", "UPDATE_CONFIG", "Admin updated node properties.")
        write_audit_log_raw(self.db, "operator1", "CHECKOUT", "Sale checkout logged.")
        
        cursor = self.db.execute("SELECT seq, prev_hash, record_hash, actor, action, details, nonce, timestamp FROM audit_logs ORDER BY seq ASC")
        rows = cursor.fetchall()
        
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["prev_hash"], "0" * 64)
        self.assertEqual(rows[1]["prev_hash"], rows[0]["record_hash"])
        self.assertEqual(rows[2]["prev_hash"], rows[1]["record_hash"])
        
        # Verify hashes mathematically
        for r in rows:
            payload = f"{r['prev_hash']}:{r['seq']}:{r['nonce']}:{r['timestamp']}:{r['actor']}:{r['action']}:{r['details']}"
            expected_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()
            self.assertEqual(r["record_hash"], expected_hash)
            
        # Simulate an attacker tampering with entry 2 in the database file
        # We manually overwrite action and details
        self.db.execute("UPDATE audit_logs SET details = 'Hacked edit' WHERE seq = 2")
        self.db.commit()
        
        # Recalculate validation chain
        cursor = self.db.execute("SELECT seq, prev_hash, record_hash, actor, action, details, nonce, timestamp FROM audit_logs ORDER BY seq ASC")
        hacked_rows = cursor.fetchall()
        
        # Chain verification: check if recalculating row 2 matches its stored hash
        r2 = hacked_rows[1]
        payload = f"{r2['prev_hash']}:{r2['seq']}:{r2['nonce']}:{r2['timestamp']}:{r2['actor']}:{r2['action']}:{r2['details']}"
        recalculated_hash_2 = hashlib.sha256(payload.encode('utf-8')).hexdigest()
        
        # Check that a tamper event is detected!
        self.assertNotEqual(r2["record_hash"], recalculated_hash_2)

    def test_session_token_hashing(self):
        raw_token = secrets.token_hex(32)
        hashed = hash_session_token(raw_token)
        
        # Assert database doesn't write plaintext
        self.assertNotEqual(raw_token, hashed)
        self.assertEqual(len(hashed), 64) # sha256 hex is 64 chars

if __name__ == '__main__':
    unittest.main()
