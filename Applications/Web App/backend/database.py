import os
import sys
import sqlite3
import hashlib
import secrets
import time
import uuid
import json
import hmac
import datetime
import math
try:
    from .auth_utils import hash_password
except ImportError:
    from auth_utils import hash_password

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audit_logs.log")

FORENSIC_MODE = False

def get_db():
    """Get SQLite database connection with WAL mode, busy_timeout, and Foreign Keys active."""
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def init_db():
    """Create database tables, seed bootstrap admin, and verify audit log integrity."""
    global FORENSIC_MODE
    db = get_db()
    
    # 1. Create tables if not exist
    db.execute("""
    CREATE TABLE IF NOT EXISTS users (
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
        mfa_last_used_code TEXT,
        pin TEXT DEFAULT '1234'
    );
    """)
    
    db.execute("""
    CREATE TABLE IF NOT EXISTS password_history (
        user_id INTEGER NOT NULL,
        salt TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        created_at INTEGER NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)
    
    db.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        token_hash TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        user_agent TEXT NOT NULL,
        ip_subnet TEXT NOT NULL,
        created_at INTEGER NOT NULL,
        last_seen_at INTEGER NOT NULL,
        stepped_up_until INTEGER DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)
    
    db.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
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
    
    # Cycle 3 tables
    db.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id TEXT PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        sku TEXT UNIQUE,
        quantity REAL NOT NULL DEFAULT 0.0,
        unit TEXT NOT NULL DEFAULT 'pcs',
        price_usd REAL NOT NULL DEFAULT 0.0,
        low_stock_threshold REAL NOT NULL DEFAULT 5.0
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS inventory_wastage (
        id TEXT PRIMARY KEY,
        inventory_id TEXT NOT NULL,
        quantity REAL NOT NULL,
        reason TEXT NOT NULL,
        timestamp INTEGER NOT NULL,
        FOREIGN KEY(inventory_id) REFERENCES inventory(id) ON DELETE CASCADE
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id TEXT PRIMARY KEY,
        timestamp INTEGER NOT NULL,
        operator_username TEXT NOT NULL,
        total_due_usd REAL NOT NULL,
        type TEXT NOT NULL,
        client_request_id TEXT UNIQUE NOT NULL
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS transaction_tenders (
        id TEXT PRIMARY KEY,
        transaction_id TEXT NOT NULL,
        currency TEXT NOT NULL,
        amount_tendered REAL NOT NULL,
        exchange_rate REAL NOT NULL,
        amount_usd_equiv REAL NOT NULL,
        FOREIGN KEY(transaction_id) REFERENCES transactions(id) ON DELETE CASCADE
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS transaction_items (
        id TEXT PRIMARY KEY,
        transaction_id TEXT NOT NULL,
        inventory_id TEXT NOT NULL,
        quantity REAL NOT NULL,
        price_usd_at_sale REAL NOT NULL,
        FOREIGN KEY(transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
        FOREIGN KEY(inventory_id) REFERENCES inventory(id) ON DELETE CASCADE
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS calculator_config (
        key TEXT PRIMARY KEY,
        value REAL NOT NULL,
        version INTEGER NOT NULL DEFAULT 1,
        valid_from INTEGER NOT NULL,
        valid_to INTEGER
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS estimator_runs (
        id TEXT PRIMARY KEY,
        timestamp INTEGER NOT NULL,
        type TEXT NOT NULL,
        inputs_json TEXT NOT NULL,
        outputs_json TEXT NOT NULL,
        config_snapshot_json TEXT NOT NULL
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS shift_handover_logs (
        id TEXT PRIMARY KEY,
        timestamp INTEGER NOT NULL,
        outgoing_guard TEXT NOT NULL,
        incoming_guard TEXT NOT NULL,
        shift_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        events_summary TEXT NOT NULL,
        cash_usd_expected REAL NOT NULL,
        cash_usd_counted REAL NOT NULL,
        cash_zar_expected REAL NOT NULL,
        cash_zar_counted REAL NOT NULL,
        cash_zwg_expected REAL NOT NULL,
        cash_zwg_counted REAL NOT NULL,
        prev_hash TEXT NOT NULL,
        record_hash TEXT NOT NULL
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS processed_requests (
        client_request_id TEXT PRIMARY KEY,
        timestamp INTEGER NOT NULL,
        response_json TEXT NOT NULL
    );
    """)

    # --- CYCLE 4 TABLES ---
    db.execute("""
    CREATE TABLE IF NOT EXISTS security_nodes (
        id TEXT PRIMARY KEY,
        label TEXT NOT NULL,
        x_pct REAL NOT NULL,
        y_pct REAL NOT NULL,
        online INTEGER NOT NULL DEFAULT 1,
        alarm INTEGER NOT NULL DEFAULT 0,
        battery_pct REAL NOT NULL DEFAULT 100.0,
        position_last_modified_utc TEXT NOT NULL,
        battery_last_modified_utc TEXT NOT NULL,
        client_id TEXT NOT NULL DEFAULT 'server'
    );
    """)

    db.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS map_obstacles_rtree USING rtree(
        id, x_min, x_max, y_min, y_max
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS map_obstacles_meta (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        attenuation_db REAL NOT NULL DEFAULT 12.0
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS harvest_orders (
        id TEXT PRIMARY KEY,
        rule_id TEXT NOT NULL,
        crop_type TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'triggered',
        pos_sku TEXT,
        spoilage_deadline_utc TEXT,
        last_modified_utc TEXT NOT NULL
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS agricultural_rules (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        crop_type TEXT NOT NULL,
        conditions_json TEXT NOT NULL,
        action_type TEXT NOT NULL,
        action_message TEXT NOT NULL,
        actuator_target TEXT,
        actuator_stop_condition TEXT,
        is_active INTEGER NOT NULL DEFAULT 1,
        last_modified_utc TEXT NOT NULL
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS pricing_multipliers (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        target_sku TEXT,
        min_quantity REAL NOT NULL DEFAULT 1.0,
        max_quantity_per_customer REAL,
        max_discount_pct REAL NOT NULL DEFAULT 0.50,
        decay_rate_k REAL NOT NULL DEFAULT 0.05,
        stack_mode TEXT NOT NULL DEFAULT 'best',
        spoilage_deadline_utc TEXT,
        is_active INTEGER NOT NULL DEFAULT 1,
        last_modified_utc TEXT NOT NULL
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS blocked_devices (
        ip_address TEXT PRIMARY KEY,
        blocked_by TEXT NOT NULL,
        blocked_at INTEGER NOT NULL,
        reason TEXT NOT NULL
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS tracked_devices (
        ip_address TEXT PRIMARY KEY,
        user_agent TEXT NOT NULL,
        device_type TEXT NOT NULL,
        first_seen INTEGER NOT NULL,
        last_seen INTEGER NOT NULL,
        last_username TEXT NOT NULL
    );
    """)

    db.commit()

    # Schema Migration: add pin column to users if it doesn't exist
    try:
        db.execute("ALTER TABLE users ADD COLUMN pin TEXT DEFAULT '1234';")
        db.commit()
    except sqlite3.OperationalError:
        pass

    # PRAGMA Migration: add cost_price_usd column to inventory
    cursor = db.execute("PRAGMA table_info(inventory)")
    cols = [row["name"] for row in cursor.fetchall()]
    if "cost_price_usd" not in cols:
        db.execute("ALTER TABLE inventory ADD COLUMN cost_price_usd REAL DEFAULT 0.0;")
        db.commit()

    # Seed default configurations
    cursor = db.execute("SELECT COUNT(*) as count FROM calculator_config")
    if cursor.fetchone()["count"] == 0:
        now = int(time.time())
        db.execute("""
            INSERT INTO calculator_config (key, value, version, valid_from)
            VALUES (?, ?, ?, ?)
        """, ("livestock_feed_ratio", 0.03, 1, now))
        db.execute("""
            INSERT INTO calculator_config (key, value, version, valid_from)
            VALUES (?, ?, ?, ?)
        """, ("crop_yield_ratio", 0.45, 1, now))
        db.commit()

    # Seed sample inventory items
    cursor = db.execute("SELECT COUNT(*) as count FROM inventory")
    if cursor.fetchone()["count"] == 0:
        samples = [
            ("Maize Seed (10kg Bag)", "MAIZE-10KG", 15.0, "bags", 25.00, 15.00, 5.0),
            ("Nitrogen Fertilizer (50kg Bag)", "FERT-NITRO", 8.0, "bags", 45.00, 28.00, 3.0),
            ("Livestock Dip Concentrate (1L)", "DIP-CONC-1L", 4.0, "bottles", 32.50, 20.00, 2.0),
            ("Irrigation Dripper Nozzles (Pack of 50)", "IRRIG-NOZ-50", 12.0, "packs", 15.00, 9.00, 4.0),
            ("Fresh Harvest Cabbage (Case)", "CABBAGE-CASE", 20.0, "cases", 18.00, 8.00, 4.0)
        ]
        for name, sku, qty, unit, price, cost, threshold in samples:
            item_id = str(uuid.uuid4())
            db.execute("""
                INSERT INTO inventory (id, name, sku, quantity, unit, price_usd, cost_price_usd, low_stock_threshold)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (item_id, name, sku, qty, unit, price, cost, threshold))
        db.commit()
    else:
        # Update cost_price_usd if zero
        db.execute("UPDATE inventory SET cost_price_usd = price_usd * 0.6 WHERE cost_price_usd = 0.0;")
        db.commit()

    # Seed Cycle 4 Default R*Tree Map Obstacles
    cursor = db.execute("SELECT COUNT(*) as count FROM map_obstacles_meta")
    if cursor.fetchone()["count"] == 0:
        obstacles = [
            (1, "Grain Silo (Metal Reinforced)", 30.0, 45.0, 25.0, 40.0, 25.0),
            (2, "Wooden Equipment Barn", 60.0, 75.0, 55.0, 70.0, 8.0)
        ]
        for obs_id, name, x_min, x_max, y_min, y_max, atten in obstacles:
            db.execute("INSERT INTO map_obstacles_meta (id, name, attenuation_db) VALUES (?, ?, ?)", (obs_id, name, atten))
            db.execute("INSERT INTO map_obstacles_rtree (id, x_min, x_max, y_min, y_max) VALUES (?, ?, ?, ?, ?)", (obs_id, x_min, x_max, y_min, y_max))
        db.commit()

    # Seed Cycle 4 Default Security Nodes
    cursor = db.execute("SELECT COUNT(*) as count FROM security_nodes")
    if cursor.fetchone()["count"] == 0:
        now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        default_nodes = [
            ("node-1", "North Perimeter Gate", 20.0, 15.0, 1, 0, 95.0, now_utc, now_utc, "server"),
            ("node-2", "South Feed Storage", 80.0, 85.0, 1, 0, 88.0, now_utc, now_utc, "server"),
            ("node-3", "East Solar Array", 85.0, 20.0, 1, 0, 15.0, now_utc, now_utc, "server"),
            ("node-4", "West Water Reservoir", 15.0, 80.0, 1, 0, 90.0, now_utc, now_utc, "server")
        ]
        for nid, lbl, x, y, on, alm, bat, pos_t, bat_t, cid in default_nodes:
            db.execute("""
                INSERT INTO security_nodes (id, label, x_pct, y_pct, online, alarm, battery_pct, position_last_modified_utc, battery_last_modified_utc, client_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (nid, lbl, x, y, on, alm, bat, pos_t, bat_t, cid))
        db.commit()

    # Seed Cycle 4 Default Agricultural Rules
    cursor = db.execute("SELECT COUNT(*) as count FROM agricultural_rules")
    if cursor.fetchone()["count"] == 0:
        now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        rules = [
            (
                "rule-1",
                "Extreme Heatwave Spoilage Warning",
                "Cabbage",
                json.dumps([{"metric": "temperature", "op": ">", "val": 32.0}]),
                "advisory",
                "Severe heatwave detected: Cabbage spoilage risk in 24h. Spawning Harvest Work Order & POS Flash Sale.",
                None,
                None,
                1,
                now_utc
            ),
            (
                "rule-2",
                "Automated Nighttime Irrigation",
                "Maize",
                json.dumps([
                    {"metric": "soil_moisture", "op": "<", "val": 20.0},
                    {"metric": "time", "op": "between", "val": "18:00-06:00"}
                ]),
                "actuator",
                "Nighttime soil dry. Opening Drip Irrigation Valve #1 until moisture > 45%.",
                "irrigation_valve_1",
                "soil_moisture > 45",
                1,
                now_utc
            )
        ]
        for rid, ttl, crop, cond, act_t, msg, target, stop_cond, active, modified in rules:
            db.execute("""
                INSERT INTO agricultural_rules (id, title, crop_type, conditions_json, action_type, action_message, actuator_target, actuator_stop_condition, is_active, last_modified_utc)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (rid, ttl, crop, cond, act_t, msg, target, stop_cond, active, modified))
        db.commit()
    
    # 2. Seed bootstrap admin
    cursor = db.execute("SELECT COUNT(*) as count FROM users")
    if cursor.fetchone()["count"] == 0:
        # Determine password source
        env_pw = os.environ.pop("MADN_BOOTSTRAP_ADMIN_PW", None)
        if env_pw:
            admin_pw = env_pw
            password_method = "environment variable"
        elif sys.stdin.isatty():
            # Prompt operator interactively
            print("\n--- FIRST-RUN MADN BOOTSTRAPPING ---")
            import getpass
            while True:
                p1 = getpass.getpass("Enter password for user 'admin' (min 12 chars): ")
                if len(p1) < 12:
                    print("Error: Password must be at least 12 characters.")
                    continue
                p2 = getpass.getpass("Confirm password: ")
                if p1 == p2:
                    admin_pw = p1
                    password_method = "interactive console prompt"
                    break
                print("Error: Passwords do not match.")
        else:
            # Headless fallback - generate random password
            alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
            admin_pw = "".join(secrets.choice(alphabet) for _ in range(16))
            password_method = "secure random generator"
            
            # Print to stdout ONLY if TTY is active to prevent journald logs capture leaks
            if sys.stdout.isatty():
                print("\n" + "="*60)
                print("MADN BOOTSTRAP: Seeded administrator credentials")
                print("Username: admin")
                print(f"Password: {admin_pw}")
                print("PLEASE CHANGE THIS PASSWORD IMMEDIATELY UPON FIRST LOGIN.")
                print("="*60 + "\n")
            else:
                # If stdout is NOT a TTY, write to owner-read-only temp file as a secure fallback
                temp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "admin_bootstrap_temp.txt")
                try:
                    fd = os.open(temp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                    with open(fd, 'w') as f:
                        f.write(f"admin:{admin_pw}\n")
                    print(f"\n[ALERT] Headless startup: admin credentials written to owner-restricted {temp_path}\n")
                except Exception as e:
                    print(f"\n[ERROR] Failed to output admin password: {str(e)}\n")
        
        # Save admin record to database
        salt_hex, hash_hex = hash_password(admin_pw)
        now = int(time.time())
        db.execute("""
            INSERT INTO users (username, password_hash, salt, role, status, created_at, updated_at, must_change_password)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("admin", hash_hex, salt_hex, "admin", "active", now, now, 0))
        
        # Record password history entry
        db.execute("""
            INSERT INTO password_history (user_id, salt, password_hash, created_at)
            VALUES (1, ?, ?, ?)
        """, (salt_hex, hash_hex, now))
        
        # Seed Honey Pot account 'system_root'
        fake_salt, fake_hash = hash_password(secrets.token_hex(16))
        db.execute("""
            INSERT INTO users (username, password_hash, salt, role, status, created_at, updated_at, must_change_password)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("system_root", fake_hash, fake_salt, "admin", "disabled", now, now, 1))
        
        db.commit()
        
        # Log bootstrap event
        write_audit_log_raw(db, "SYSTEM", "BOOTSTRAP", f"Seeded admin account via {password_method}.")
        
    db.close()
    
    # 3. Verify audit log integrity with external anchor file
    verify_audit_log_integrity()

def write_audit_log_raw(db, actor: str, action: str, details: str):
    """Internal log function to insert records during table initializations."""
    now = int(time.time())
    
    # Retrieve last row hash
    cursor = db.execute("SELECT seq, record_hash FROM audit_logs ORDER BY seq DESC LIMIT 1")
    row = cursor.fetchone()
    if row:
        prev_hash = row["record_hash"]
        seq = row["seq"] + 1
    else:
        prev_hash = "0" * 64
        seq = 1
        
    nonce = secrets.token_hex(16)
    payload = f"{prev_hash}:{seq}:{nonce}:{now}:{actor}:{action}:{details}"
    # Use HMAC-SHA256 for cryptographic signing of the chain
    hmac_key = os.environ.get("MADN_HMAC_SECRET", "default_secret_key_12345!").encode('utf-8')
    record_hash = hmac.new(hmac_key, payload.encode('utf-8'), hashlib.sha256).hexdigest()
    
    db.execute("""
        INSERT INTO audit_logs (seq, nonce, timestamp, actor, action, details, prev_hash, record_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (seq, nonce, now, actor, action, details, prev_hash, record_hash))
    db.commit()
    
    # Write to external log file anchor
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{now}|{actor}|{action}|{details}|{seq}|{nonce}|{prev_hash}|{record_hash}\n")
    except Exception as e:
        print(f"[SECURITY WARNING] Failed to write external audit log anchor: {str(e)}")

def write_audit_log(actor: str, action: str, details: str):
    """Write an audit entry, updates database chain, and appends to flat anchor file."""
    db = get_db()
    write_audit_log_raw(db, actor, action, details)
    db.close()

def verify_database_audit_chain():
    """Verify the entire database audit log chain mathematically using HMAC-SHA256."""
    global FORENSIC_MODE
    db = get_db()
    cursor = db.execute("SELECT seq, prev_hash, record_hash, actor, action, details, nonce, timestamp FROM audit_logs ORDER BY seq ASC")
    rows = cursor.fetchall()
    db.close()
    
    hmac_key = os.environ.get("MADN_HMAC_SECRET", "default_secret_key_12345!").encode('utf-8')
    expected_prev = "0" * 64
    
    for r in rows:
        # Check chain link
        if r["prev_hash"] != expected_prev:
            print(f"[CRITICAL SECURITY BREACH] Chain link broken at Seq #{r['seq']}! Expected prev_hash {expected_prev}, found {r['prev_hash']}.")
            FORENSIC_MODE = True
            return False
            
        # Check hash math
        payload = f"{r['prev_hash']}:{r['seq']}:{r['nonce']}:{r['timestamp']}:{r['actor']}:{r['action']}:{r['details']}"
        expected_hash = hmac.new(hmac_key, payload.encode('utf-8'), hashlib.sha256).hexdigest()
        
        if r["record_hash"] != expected_hash:
            print(f"[CRITICAL SECURITY BREACH] Log math signature mismatch at Seq #{r['seq']}! Tampering detected.")
            FORENSIC_MODE = True
            return False
            
        expected_prev = r["record_hash"]
        
    return True

def verify_audit_log_integrity():
    """Verify that DB audit records match the append-only flat text file log anchor."""
    global FORENSIC_MODE
    
    # 1. Perform full mathematical DB chain validation first
    if not verify_database_audit_chain():
        FORENSIC_MODE = True
        return
        
    db = get_db()
    cursor = db.execute("SELECT seq, record_hash FROM audit_logs ORDER BY seq DESC LIMIT 1")
    db_row = cursor.fetchone()
    db.close()
    
    if not db_row:
        # No audit records exist yet
        return
        
    last_db_hash = db_row["record_hash"]
    
    # Read last line from file anchor
    if not os.path.exists(LOG_PATH):
        print("[CRITICAL SECURITY WARNING] External audit log file is missing!")
        FORENSIC_MODE = True
        return
        
    try:
        with open(LOG_PATH, "rb") as f:
            # Efficiently seek to end of file to read last line
            f.seek(0, os.SEEK_END)
            end_pos = f.tell()
            if end_pos == 0:
                print("[CRITICAL SECURITY WARNING] External audit log file is empty!")
                FORENSIC_MODE = True
                return
                
            buffer_size = 1024
            offset = max(0, end_pos - buffer_size)
            f.seek(offset)
            lines = f.read().decode('utf-8').splitlines()
            
            if not lines:
                print("[CRITICAL SECURITY WARNING] External audit log file structure is invalid!")
                FORENSIC_MODE = True
                return
                
            last_line = lines[-1]
            parts = last_line.split("|")
            last_file_hash = parts[-1]
            
            if last_db_hash != last_file_hash:
                print(f"[CRITICAL SECURITY BREACH] Database audit hash ({last_db_hash}) does not match log file anchor ({last_file_hash})! Forensics triggered.")
                FORENSIC_MODE = True
            else:
                FORENSIC_MODE = False
    except Exception as e:
        print(f"[CRITICAL SECURITY WARNING] Audit log validation failed with error: {str(e)}")
        FORENSIC_MODE = True

def get_calculator_config(key: str) -> float:
    db = get_db()
    cursor = db.execute("SELECT value FROM calculator_config WHERE key = ? ORDER BY version DESC LIMIT 1", (key,))
    row = cursor.fetchone()
    db.close()
    return row["value"] if row else None

def get_all_calculator_configs():
    db = get_db()
    cursor = db.execute("SELECT key, value, version, valid_from FROM calculator_config")
    rows = cursor.fetchall()
    db.close()
    return [dict(r) for r in rows]

def update_calculator_config(key: str, value: float, actor: str) -> bool:
    db = get_db()
    cursor = db.execute("SELECT version FROM calculator_config WHERE key = ? ORDER BY version DESC LIMIT 1", (key,))
    row = cursor.fetchone()
    if not row:
        db.close()
        return False
    
    new_version = row["version"] + 1
    now = int(time.time())
    db.execute("""
        INSERT INTO calculator_config (key, value, version, valid_from)
        VALUES (?, ?, ?, ?)
    """, (key, value, new_version, now))
    db.commit()
    db.close()
    write_audit_log(actor, "UPDATE_CONFIG", f"Updated config key '{key}' to value {value} (v{new_version})")
    return True

def add_inventory_item(name: str, sku: str, quantity: float, unit: str, price_usd: float, threshold: float, actor: str) -> str:
    db = get_db()
    item_id = str(uuid.uuid4())
    db.execute("""
        INSERT INTO inventory (id, name, sku, quantity, unit, price_usd, low_stock_threshold)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (item_id, name, sku, quantity, unit, price_usd, threshold))
    db.commit()
    db.close()
    write_audit_log(actor, "ADD_INVENTORY", f"Added item '{name}' (SKU: {sku}) with initial quantity {quantity} {unit}")
    return item_id

def adjust_inventory_qty(item_id: str, amount: float, reason: str, actor: str) -> bool:
    """Adjust inventory quantity atomically using BEGIN IMMEDIATE lock."""
    db = get_db()
    try:
        db.execute("BEGIN IMMEDIATE")
        cursor = db.execute("SELECT name, quantity FROM inventory WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        if not row:
            db.rollback()
            db.close()
            return False
        
        new_qty = row["quantity"] + amount
        if new_qty < 0:
            db.rollback()
            db.close()
            return False
            
        db.execute("UPDATE inventory SET quantity = ? WHERE id = ?", (new_qty, item_id))
        db.commit()
        db.close()
        write_audit_log(actor, "ADJUST_STOCK", f"Adjusted stock for '{row['name']}' by {amount} ({reason}). New stock: {new_qty}")
        return True
    except sqlite3.OperationalError:
        # Handle lock timeout
        db.rollback()
        db.close()
        return False

def log_wastage(item_id: str, qty: float, reason: str, actor: str) -> bool:
    """Record stock loss as wastage/spoilage."""
    db = get_db()
    try:
        db.execute("BEGIN IMMEDIATE")
        cursor = db.execute("SELECT name, quantity FROM inventory WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        if not row:
            db.rollback()
            db.close()
            return False
        
        if row["quantity"] < qty:
            db.rollback()
            db.close()
            return False
            
        new_qty = row["quantity"] - qty
        wastage_id = str(uuid.uuid4())
        now = int(time.time())
        
        db.execute("UPDATE inventory SET quantity = ? WHERE id = ?", (new_qty, item_id))
        db.execute("""
            INSERT INTO inventory_wastage (id, inventory_id, quantity, reason, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (wastage_id, item_id, qty, reason, now))
        
        db.commit()
        db.close()
        write_audit_log(actor, "WASTAGE", f"Logged {qty} units wastage of '{row['name']}' Reason: {reason}")
        return True
    except sqlite3.OperationalError:
        db.rollback()
        db.close()
        return False

def execute_checkout_transaction(operator_username: str, total_due: float, client_req_id: str, tenders: list, items: list) -> dict:
    """Perform atomic split tender checks and inventory deductions with WAL + BEGIN IMMEDIATE."""
    db = get_db()
    db.execute("PRAGMA busy_timeout=5000;")
    
    try:
        db.execute("BEGIN IMMEDIATE")
        
        # 1. Idempotency Check
        cursor = db.execute("SELECT response_json FROM processed_requests WHERE client_request_id = ?", (client_req_id,))
        row = cursor.fetchone()
        if row:
            db.rollback()
            db.close()
            return json.loads(row["response_json"])
            
        # 2. Check stock levels
        for item in items:
            inv_id = item["inventory_id"]
            qty = item["quantity"]
            cursor = db.execute("SELECT name, quantity FROM inventory WHERE id = ?", (inv_id,))
            inv_row = cursor.fetchone()
            if not inv_row:
                db.rollback()
                db.close()
                raise ValueError(f"Inventory item not found: {inv_id}")
            if inv_row["quantity"] < qty:
                db.rollback()
                db.close()
                raise ValueError(f"Insufficient stock for '{inv_row['name']}': Count = {inv_row['quantity']}, Requested = {qty}")
                
        # 3. Perform atomic deductions
        for item in items:
            inv_id = item["inventory_id"]
            qty = item["quantity"]
            cursor = db.execute("UPDATE inventory SET quantity = quantity - ? WHERE id = ? AND quantity >= ?", (qty, inv_id, qty))
            if cursor.rowcount == 0:
                db.rollback()
                db.close()
                raise ValueError(f"Atomic decrement check failed for inventory ID: {inv_id}")
                
        # 4. Save transaction records
        tx_id = str(uuid.uuid4())
        now = int(time.time())
        db.execute("""
            INSERT INTO transactions (id, timestamp, operator_username, total_due_usd, type, client_request_id)
            VALUES (?, ?, ?, ?, 'SALE', ?)
        """, (tx_id, now, operator_username, total_due, client_req_id))
        
        # Insert tenders
        for t in tenders:
            tender_id = str(uuid.uuid4())
            db.execute("""
                INSERT INTO transaction_tenders (id, transaction_id, currency, amount_tendered, exchange_rate, amount_usd_equiv)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (tender_id, tx_id, t["currency"], t["amount_tendered"], t["exchange_rate"], t["amount_usd_equiv"]))
            
        # Insert sold items
        for item in items:
            sale_item_id = str(uuid.uuid4())
            db.execute("""
                INSERT INTO transaction_items (id, transaction_id, inventory_id, quantity, price_usd_at_sale)
                VALUES (?, ?, ?, ?, ?)
            """, (sale_item_id, tx_id, item["inventory_id"], item["quantity"], item["price_usd_at_sale"]))
            
        # Log processed request
        response_data = {"status": "success", "transaction_id": tx_id, "total_due_usd": total_due}
        db.execute("""
            INSERT INTO processed_requests (client_request_id, timestamp, response_json)
            VALUES (?, ?, ?)
        """, (client_req_id, now, json.dumps(response_data)))
        
        db.commit()
        db.close()
        
        # Log audit log
        write_audit_log(operator_username, "POS_CHECKOUT", f"Sale checkout completed. Transaction ID: {tx_id}. Due: ${total_due}")
        return response_data
        
    except Exception as e:
        db.rollback()
        db.close()
        raise e

def write_shift_handover(outgoing_guard: str, incoming_guard: str, shift_type: str, severity: str, events_summary: str,
                         cash_expected: dict, cash_counted: dict) -> str:
    """Create shift handover logs with cryptographic HMAC-SHA256 linking."""
    db = get_db()
    
    # Retrieve last row hash
    cursor = db.execute("SELECT record_hash FROM shift_handover_logs ORDER BY timestamp DESC, id DESC LIMIT 1")
    row = cursor.fetchone()
    prev_hash = row["record_hash"] if row else ("0" * 64)
    
    handover_id = str(uuid.uuid4())
    now = int(time.time())
    
    # Build payload representation
    payload = (
        f"{prev_hash}:{handover_id}:{now}:{outgoing_guard}:{incoming_guard}:{shift_type}:{severity}:{events_summary}:"
        f"{cash_expected['usd']}:{cash_counted['usd']}:{cash_expected['zar']}:{cash_counted['zar']}:"
        f"{cash_expected['zwg']}:{cash_counted['zwg']}"
    )
    
    # Cryptographic signature
    hmac_key = os.environ.get("MADN_HMAC_SECRET", "default_secret_key_12345!").encode('utf-8')
    record_hash = hmac.new(hmac_key, payload.encode('utf-8'), hashlib.sha256).hexdigest()
    
    db.execute("""
        INSERT INTO shift_handover_logs (
            id, timestamp, outgoing_guard, incoming_guard, shift_type, severity, events_summary,
            cash_usd_expected, cash_usd_counted, cash_zar_expected, cash_zar_counted, cash_zwg_expected, cash_zwg_counted,
            prev_hash, record_hash
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        handover_id, now, outgoing_guard, incoming_guard, shift_type, severity, events_summary,
        cash_expected['usd'], cash_counted['usd'], cash_expected['zar'], cash_counted['zar'], cash_expected['zwg'], cash_counted['zwg'],
        prev_hash, record_hash
    ))
    db.commit()
    db.close()
    
    write_audit_log(outgoing_guard, "SHIFT_HANDOVER", f"Shift handover signed to {incoming_guard} (Severity: {severity})")
    return handover_id

def verify_shift_handover_chain() -> bool:
    """Verify the entire shift handover chain mathematically."""
    db = get_db()
    cursor = db.execute("SELECT * FROM shift_handover_logs ORDER BY timestamp ASC, id ASC")
    rows = cursor.fetchall()
    db.close()
    
    hmac_key = os.environ.get("MADN_HMAC_SECRET", "default_secret_key_12345!").encode('utf-8')
    expected_prev = "0" * 64
    
    for r in rows:
        if r["prev_hash"] != expected_prev:
            print(f"[SECURITY ALERT] Shift chain link broken at handover ID {r['id']}!")
            return False
            
        payload = (
            f"{r['prev_hash']}:{r['id']}:{r['timestamp']}:{r['outgoing_guard']}:{r['incoming_guard']}:{r['shift_type']}:{r['severity']}:{r['events_summary']}:"
            f"{r['cash_usd_expected']}:{r['cash_usd_counted']}:{r['cash_zar_expected']}:{r['cash_zar_counted']}:"
            f"{r['cash_zwg_expected']}:{r['cash_zwg_counted']}"
        )
        
        expected_hash = hmac.new(hmac_key, payload.encode('utf-8'), hashlib.sha256).hexdigest()
        if r["record_hash"] != expected_hash:
            print(f"[SECURITY ALERT] Handover signature math mismatched at ID {r['id']}!")
            return False
            
        expected_prev = r["record_hash"]
        
    return True

# --- CYCLE 4 MATH ENGINES & HELPER FUNCTIONS ---

def ray_intersects_box(x1: float, y1: float, x2: float, y2: float, bx_min: float, by_min: float, bx_max: float, by_max: float) -> bool:
    """Liang-Barsky 2D line segment clipping check against axis-aligned rectangle."""
    dx = x2 - x1
    dy = y2 - y1
    
    p = [-dx, dx, -dy, dy]
    q = [x1 - bx_min, bx_max - x1, y1 - by_min, by_max - y1]
    
    u1 = 0.0
    u2 = 1.0
    
    for i in range(4):
        if p[i] == 0:
            if q[i] < 0:
                return False
        else:
            t = q[i] / p[i]
            if p[i] < 0:
                if t > u2:
                    return False
                if t > u1:
                    u1 = t
            else:
                if t < u1:
                    return False
                if t < u2:
                    u2 = t
    return u1 <= u2

def get_nodes_telemetry():
    """Fetch all security nodes and calculate RF path loss, R*Tree obstacle attenuation, and A* mesh routing."""
    db = get_db()
    cursor = db.execute("SELECT * FROM security_nodes")
    nodes = [dict(row) for row in cursor.fetchall()]
    
    # Fetch map obstacles
    cursor = db.execute("""
        SELECT meta.id, meta.name, meta.attenuation_db, rtree.x_min, rtree.x_max, rtree.y_min, rtree.y_max
        FROM map_obstacles_meta meta
        JOIN map_obstacles_rtree rtree ON meta.id = rtree.id
    """)
    obstacles = [dict(row) for row in cursor.fetchall()]
    db.close()
    
    hub_x, hub_y = 50.0, 50.0 # Central Hub coordinates
    scale_meters = 5.0 # 1% = 5 meters (500m field canvas)
    
    # Helper to calculate RSSI between two points
    def calc_point_rssi(x1, y1, x2, y2):
        dist_pct = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        dist_m = dist_pct * scale_meters
        # Open field path loss (exponent gamma = 2.5)
        rssi_fs = -30.0 - (10.0 * 2.5 * math.log10(max(dist_m, 1.0)))
        
        # Ray-trace obstacles
        atten_sum = 0.0
        intersected = []
        for obs in obstacles:
            if ray_intersects_box(x1, y1, x2, y2, obs["x_min"], obs["y_min"], obs["x_max"], obs["y_max"]):
                atten_sum += obs["attenuation_db"]
                intersected.append(obs["name"])
        return rssi_fs - atten_sum, atten_sum, intersected

    telemetry_results = []
    
    for n in nodes:
        nx, ny = n["x_pct"], n["y_pct"]
        rssi_direct, atten_direct, obstacles_hit = calc_point_rssi(nx, ny, hub_x, hub_y)
        
        node_status = "direct"
        mesh_path = ["Central Hub"]
        final_rssi = rssi_direct
        
        # If direct signal is weak (< -88 dBm), calculate A* / Max-Min multi-hop mesh route
        if rssi_direct < -88.0 and n["online"] == 1:
            best_relay = None
            best_quality = -999.0
            
            for relay in nodes:
                if relay["id"] == n["id"] or relay["online"] == 0:
                    continue
                    
                rx, ry = relay["x_pct"], relay["y_pct"]
                rssi_to_relay, _, _ = calc_point_rssi(nx, ny, rx, ry)
                rssi_relay_to_hub, _, _ = calc_point_rssi(rx, ry, hub_x, hub_y)
                
                # Max-Min Effective Quality
                link_quality = min(rssi_to_relay, rssi_relay_to_hub)
                
                # Penalize low-battery intermediate relay nodes (< 20%)
                if relay["battery_pct"] < 20.0:
                    link_quality -= 20.0
                    
                if link_quality > best_quality:
                    best_quality = link_quality
                    best_relay = relay
                    
            if best_relay and best_quality >= -88.0:
                node_status = "meshed"
                final_rssi = best_quality
                mesh_path = [best_relay["label"], "Central Hub"]
            else:
                node_status = "offline"
                final_rssi = rssi_direct
                
        # Signal quality label
        if final_rssi >= -65.0:
            quality_label = "Excellent"
        elif final_rssi >= -78.0:
            quality_label = "Good"
        elif final_rssi >= -88.0:
            quality_label = "Fair (Mesh Candidate)"
        else:
            quality_label = "Weak / Dead Zone"
            
        n_res = dict(n)
        n_res.update({
            "rssi": round(final_rssi, 1),
            "direct_rssi": round(rssi_direct, 1),
            "attenuation_db": round(atten_direct, 1),
            "obstacles_hit": obstacles_hit,
            "status": node_status,
            "quality_label": quality_label,
            "mesh_path": mesh_path
        })
        telemetry_results.append(n_res)
        
    return telemetry_results, obstacles

def update_node_position_lww(node_id: str, x_pct: float, y_pct: float, client_id: str = "client", timestamp_utc: str = None) -> bool:
    """Field-level LWW node position update."""
    if not timestamp_utc:
        timestamp_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
    db = get_db()
    cursor = db.execute("SELECT position_last_modified_utc FROM security_nodes WHERE id = ?", (node_id,))
    row = cursor.fetchone()
    
    if not row:
        db.close()
        return False
        
    # Check LWW timestamp
    if timestamp_utc >= row["position_last_modified_utc"]:
        db.execute("""
            UPDATE security_nodes
            SET x_pct = ?, y_pct = ?, position_last_modified_utc = ?, client_id = ?
            WHERE id = ?
        """, (x_pct, y_pct, timestamp_utc, client_id, node_id))
        db.commit()
        db.close()
        write_audit_log(client_id, "NODE_DRAGGED", f"Node {node_id} repositioned to ({x_pct:.1f}%, {y_pct:.1f}%)")
        return True
    else:
        db.close()
        return False # Incoming update is older than stored position

def evaluate_agricultural_rules(sensor_inputs: dict):
    """Evaluates active compound rules against weather/soil telemetry, spawning Harvest Work Orders & POS Flash Sales."""
    db = get_db()
    cursor = db.execute("SELECT * FROM agricultural_rules WHERE is_active = 1")
    rules = [dict(r) for r in cursor.fetchall()]
    
    triggered_actions = []
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    now_time_str = datetime.datetime.now().strftime("%H:%M")
    
    def is_time_between(now_str, start_str, end_str):
        if start_str <= end_str:
            return start_str <= now_str <= end_str
        else: # midnight crossing e.g. 18:00 to 06:00
            return now_str >= start_str or now_str <= end_str

    for rule in rules:
        conditions = json.loads(rule["conditions_json"])
        rule_matched = True
        
        for cond in conditions:
            metric = cond.get("metric")
            op = cond.get("op")
            target_val = cond.get("val")
            input_val = sensor_inputs.get(metric)
            
            if metric == "time":
                if op == "between":
                    times = target_val.split("-")
                    if len(times) == 2 and not is_time_between(now_time_str, times[0], times[1]):
                        rule_matched = False
                        break
            else:
                if input_val is None:
                    rule_matched = False
                    break
                if op == ">" and not (input_val > target_val):
                    rule_matched = False; break
                elif op == "<" and not (input_val < target_val):
                    rule_matched = False; break
                elif op == "==" and not (input_val == target_val):
                    rule_matched = False; break
                    
        if rule_matched:
            action_info = {
                "rule_id": rule["id"],
                "title": rule["title"],
                "action_type": rule["action_type"],
                "action_message": rule["action_message"],
                "actuator_target": rule["actuator_target"],
                "actuator_stop_condition": rule["actuator_stop_condition"]
            }
            triggered_actions.append(action_info)
            
            # If Advisory & Spoilage warning, spawn Harvest Work Order + Cross-VPA Spoilage Flash Sale
            if rule["action_type"] == "advisory":
                c = db.execute("SELECT id FROM harvest_orders WHERE rule_id = ? AND status != 'pos_listed'", (rule["id"],))
                if not c.fetchone():
                    h_id = str(uuid.uuid4())
                    spoilage_cutoff = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)).isoformat()
                    db.execute("""
                        INSERT INTO harvest_orders (id, rule_id, crop_type, status, pos_sku, spoilage_deadline_utc, last_modified_utc)
                        VALUES (?, ?, ?, 'triggered', 'CABBAGE-CASE', ?, ?)
                    """, (h_id, rule["id"], rule["crop_type"], spoilage_cutoff, now_utc))
                    
                    # Auto-spawn Cross-VPA Spoilage Flash Sale multiplier in POS!
                    p_id = str(uuid.uuid4())
                    db.execute("""
                        INSERT INTO pricing_multipliers (
                            id, title, target_sku, min_quantity, max_quantity_per_customer, max_discount_pct, decay_rate_k, stack_mode, spoilage_deadline_utc, is_active, last_modified_utc
                        ) VALUES (?, ?, 'CABBAGE-CASE', 1.0, 3.0, 0.60, 0.08, 'best', ?, 1, ?)
                    """, (p_id, f"Smart Spoilage Flash Sale: {rule['crop_type']}", spoilage_cutoff, now_utc))
                    db.commit()
                    
    db.close()
    return triggered_actions

def calculate_pos_catalog_prices():
    """Calculates active catalog prices applying continuous exponential decay markdown and margin floor protections."""
    db = get_db()
    cursor = db.execute("SELECT * FROM inventory")
    items = [dict(r) for r in cursor.fetchall()]
    
    cursor = db.execute("SELECT * FROM pricing_multipliers WHERE is_active = 1")
    promos = [dict(r) for r in cursor.fetchall()]
    db.close()
    
    now_dt = datetime.datetime.now(datetime.timezone.utc)
    
    for item in items:
        sku = item["sku"]
        regular_price = float(item["price_usd"])
        cost_price = float(item.get("cost_price_usd", regular_price * 0.6))
        
        best_price = regular_price
        applied_promo = None
        
        for p in promos:
            if p["target_sku"] and p["target_sku"] != sku:
                continue
                
            discount_pct = float(p.get("max_discount_pct", 0.10))
            
            # Continuous Exponential Decay math if spoilage deadline is set
            if p.get("spoilage_deadline_utc"):
                deadline_dt = datetime.datetime.fromisoformat(p["spoilage_deadline_utc"])
                hours_remaining = max(0.0, (deadline_dt - now_dt).total_seconds() / 3600.0)
                
                # Continuous decay formula: Discount(t) = MaxDiscount * (1 - e^(-k * (24 - t)))
                k = float(p.get("decay_rate_k", 0.08))
                time_elapsed = max(0.0, 24.0 - hours_remaining)
                decay_factor = 1.0 - math.exp(-k * time_elapsed)
                discount_pct = min(discount_pct, discount_pct * max(0.2, decay_factor))
                
            calc_price = regular_price * (1.0 - discount_pct)
            
            # Enforce Margin Floor Protection (Price never drops below Cost Price)
            protected_price = max(calc_price, cost_price)
            
            if protected_price < best_price:
                best_price = protected_price
                applied_promo = p["title"]
                
        item["effective_price_usd"] = round(best_price, 2)
        item["discount_applied"] = round(regular_price - best_price, 2)
        item["applied_promo_title"] = applied_promo
        
    return items


def classify_user_agent(ua_str):
    ua = ua_str.lower() if ua_str else ""
    if any(k in ua for k in ["ipad", "android tablet", "kindle", "playbook", "silk", "nexus 7", "nexus 9", "nexus 10", "sm-t"]):
        return "Tablet"
    elif any(k in ua for k in ["mobile", "iphone", "ipod", "android", "blackberry", "opera mini", "windows phone"]):
        return "Mobile"
    return "Desktop"


def track_device_activity(ip_address, user_agent, username="anonymous"):
    if not ip_address:
        return
    db = get_db()
    device_type = classify_user_agent(user_agent)
    now = int(time.time())
    
    cursor = db.execute("SELECT first_seen FROM tracked_devices WHERE ip_address = ?", (ip_address,))
    row = cursor.fetchone()
    
    if row:
        db.execute("""
            UPDATE tracked_devices 
            SET user_agent = ?, device_type = ?, last_seen = ?, last_username = ? 
            WHERE ip_address = ?
        """, (user_agent, device_type, now, username, ip_address))
    else:
        db.execute("""
            INSERT INTO tracked_devices (ip_address, user_agent, device_type, first_seen, last_seen, last_username)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (ip_address, user_agent, device_type, now, now, username))
    db.commit()
    db.close()


def is_device_blocked(ip_address):
    if not ip_address:
        return False
    db = get_db()
    cursor = db.execute("SELECT ip_address FROM blocked_devices WHERE ip_address = ?", (ip_address,))
    blocked = cursor.fetchone() is not None
    db.close()
    return blocked


def block_device(ip_address, admin_user, reason="Blocked by System Administrator"):
    db = get_db()
    now = int(time.time())
    db.execute("""
        INSERT OR REPLACE INTO blocked_devices (ip_address, blocked_by, blocked_at, reason)
        VALUES (?, ?, ?, ?)
    """, (ip_address, admin_user, now, reason))
    
    db.execute("DELETE FROM sessions WHERE ip_subnet = ?", (ip_address,))
    db.commit()
    db.close()
    write_audit_log(admin_user, "BLOCK_DEVICE", f"Blocked device IP '{ip_address}'. Reason: {reason}")


def unblock_device(ip_address, admin_user):
    db = get_db()
    db.execute("DELETE FROM blocked_devices WHERE ip_address = ?", (ip_address,))
    db.commit()
    db.close()
    write_audit_log(admin_user, "UNBLOCK_DEVICE", f"Unblocked device IP '{ip_address}'.")


def get_tracked_devices():
    db = get_db()
    cursor = db.execute("SELECT * FROM tracked_devices ORDER BY last_seen DESC")
    devices = [dict(r) for r in cursor.fetchall()]
    
    cursor = db.execute("SELECT ip_address FROM blocked_devices")
    blocked_ips = {row["ip_address"] for row in cursor.fetchall()}
    db.close()
    
    for dev in devices:
        dev["status"] = "blocked" if dev["ip_address"] in blocked_ips else "allowed"
        
    return devices


