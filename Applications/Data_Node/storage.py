"""
Standalone SQLite WAL Storage Manager for Data Nodes
Executes localized read/write operations with strict ACID guarantees.
"""

import os
import sqlite3
import shutil
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("madn.data_node.storage")

DB_FILENAME = "data_node.db"


class DataNodeStorage:
    """Manages dedicated SQLite database with Write-Ahead Logging (WAL)."""

    def __init__(self, data_dir: str = "."):
        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, DB_FILENAME)
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
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
            "db_path": os.path.abspath(self.db_path)
        }

    def put_record(self, collection: str, record_key: str, data_json: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("BEGIN IMMEDIATE;")
            cursor.execute("""
                INSERT INTO kv_records (collection, record_key, data_json, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(collection, record_key) DO UPDATE SET
                    data_json=excluded.data_json,
                    updated_at=CURRENT_TIMESTAMP;
            """, (collection, record_key, data_json))
            conn.commit()

    def get_record(self, collection: str, record_key: str) -> Optional[str]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT data_json FROM kv_records WHERE collection = ? AND record_key = ?;
            """, (collection, record_key))
            row = cursor.fetchone()
            return row["data_json"] if row else None

    def list_records(self, collection: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT record_key, data_json, updated_at FROM kv_records WHERE collection = ?;
            """, (collection,))
            return [{"key": row["record_key"], "data": row["data_json"], "updated_at": row["updated_at"]} for row in cursor.fetchall()]
