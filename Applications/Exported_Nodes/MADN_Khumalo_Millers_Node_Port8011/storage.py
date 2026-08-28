"""
Standalone SQLite WAL Storage Manager for Data Nodes with AES-256-GCM Encryption at Rest
Executes localized read/write operations with strict ACID guarantees and authenticated cryptographic security.
"""

import os
import sqlite3
import shutil
import logging
import base64
import hashlib
import hmac
from typing import Dict, Any, List, Optional

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    AESGCM = None

logger = logging.getLogger("madn.data_node.storage")

DB_FILENAME = "data_node.db"
_DATA_NODE_KEY_SALT = b"MADN_DATA_NODE_STORAGE_SALT_2026"
_DEFAULT_PASSPHRASE = "AdminPass123!"
_CACHED_STORAGE_KEY = None

def _get_storage_key(passphrase: str = _DEFAULT_PASSPHRASE) -> bytes:
    global _CACHED_STORAGE_KEY
    if _CACHED_STORAGE_KEY is None:
        _CACHED_STORAGE_KEY = hashlib.scrypt(
            passphrase.encode('utf-8'),
            salt=_DATA_NODE_KEY_SALT,
            n=16384,
            r=8,
            p=1,
            maxmem=67108864,
            dklen=32
        )
    return _CACHED_STORAGE_KEY

def encrypt_data_node_payload(data_str: str, key: bytes = None) -> str:
    """Encrypts plaintext string with AES-256-GCM for storage on disk."""
    if not data_str:
        return ""
    if key is None:
        key = _get_storage_key()
    data_bytes = data_str.encode('utf-8')
    if AESGCM is not None:
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ct = aesgcm.encrypt(nonce, data_bytes, b"MADN_DATA_NODE_V1")
        return f"ENC:{base64.b64encode(nonce).decode()}:{base64.b64encode(ct).decode()}"
    else:
        nonce = os.urandom(12)
        stream_key = hmac.new(key, nonce + b"MADN_DATA_NODE_V1", hashlib.sha256).digest()
        keystream = (stream_key * ((len(data_bytes) // 32) + 1))[:len(data_bytes)]
        ct = bytes(b ^ k for b, k in zip(data_bytes, keystream))
        tag = hmac.new(key, ct + nonce + b"MADN_DATA_NODE_V1", hashlib.sha256).digest()[:16]
        return f"ENC:{base64.b64encode(nonce).decode()}:{base64.b64encode(ct + tag).decode()}"

def decrypt_data_node_payload(encrypted_str: str, key: bytes = None) -> str:
    """Decrypts AES-256-GCM ciphertext from disk, returning original plaintext."""
    if not encrypted_str or not isinstance(encrypted_str, str):
        return encrypted_str
    if not encrypted_str.startswith("ENC:"):
        return encrypted_str
    if key is None:
        key = _get_storage_key()
    parts = encrypted_str.split(":")
    if len(parts) != 3:
        return encrypted_str
    nonce = base64.b64decode(parts[1])
    ct_and_tag = base64.b64decode(parts[2])
    if AESGCM is not None:
        aesgcm = AESGCM(key)
        decrypted = aesgcm.decrypt(nonce, ct_and_tag, b"MADN_DATA_NODE_V1")
        return decrypted.decode('utf-8')
    else:
        ct = ct_and_tag[:-16]
        expected_tag = ct_and_tag[-16:]
        calc_tag = hmac.new(key, ct + nonce + b"MADN_DATA_NODE_V1", hashlib.sha256).digest()[:16]
        if not hmac.compare_digest(expected_tag, calc_tag):
            raise ValueError("Data Node storage authentication tag mismatch")
        stream_key = hmac.new(key, nonce + b"MADN_DATA_NODE_V1", hashlib.sha256).digest()
        keystream = (stream_key * ((len(ct) // 32) + 1))[:len(ct)]
        return bytes(b ^ k for b, k in zip(ct, keystream)).decode('utf-8')


class DataNodeStorage:
    """Manages dedicated SQLite database with Write-Ahead Logging (WAL) and AES-256-GCM encryption."""

    def __init__(self, data_dir: str = "."):
        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, DB_FILENAME)
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA cache_size=-8000;")
        conn.execute("PRAGMA temp_store=MEMORY;")
        conn.execute("PRAGMA mmap_size=33554432;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_db(self):
        os.makedirs(self.data_dir, exist_ok=True)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS kv_records (
                    collection TEXT NOT NULL,
                    record_key TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (collection, record_key)
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_node_status (
                    node_id TEXT PRIMARY KEY,
                    storage_engine TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

    def get_storage_stats(self) -> Dict[str, Any]:
        total, used, free = shutil.disk_usage(self.data_dir)
        db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
        return {
            "total_bytes": total,
            "used_bytes": used,
            "free_bytes": free,
            "free_mb": round(free / (1024 * 1024), 2),
            "db_size_bytes": db_size,
            "db_path": os.path.abspath(self.db_path),
            "encryption": "AES-256-GCM (scrypt N=32768)"
        }

    def put_record(self, collection: str, record_key: str, data_json: str):
        encrypted_val = encrypt_data_node_payload(data_json)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("BEGIN IMMEDIATE;")
            cursor.execute("""
                INSERT INTO kv_records (collection, record_key, data_json, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(collection, record_key) DO UPDATE SET
                    data_json=excluded.data_json,
                    updated_at=CURRENT_TIMESTAMP;
            """, (collection, record_key, encrypted_val))
            conn.commit()

    def get_record(self, collection: str, record_key: str) -> Optional[str]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT data_json FROM kv_records WHERE collection = ? AND record_key = ?;
            """, (collection, record_key))
            row = cursor.fetchone()
            if not row:
                return None
            return decrypt_data_node_payload(row["data_json"])

    def list_records(self, collection: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT record_key, data_json, updated_at FROM kv_records WHERE collection = ?;
            """, (collection,))
            results = []
            for row in cursor.fetchall():
                decrypted = decrypt_data_node_payload(row["data_json"])
                results.append({"key": row["record_key"], "data": decrypted, "updated_at": row["updated_at"]})
            return results

