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
VAULT_SECRET_KEY = b"madn-offline-vault-key-secret-2026"

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

    # Stage 1 Core Tables: Agriculture, Security Gatekeeper, and Social Media
    db.execute("""
    CREATE TABLE IF NOT EXISTS agri_plantings (
        id TEXT PRIMARY KEY,
        crop_variety TEXT NOT NULL,
        plot_bed_id TEXT NOT NULL,
        planting_date_utc TEXT NOT NULL,
        seeding_density REAL DEFAULT 0.0,
        target_maturity_date_utc TEXT,
        initial_soil_hydration_pct REAL DEFAULT 0.0,
        status TEXT NOT NULL DEFAULT 'growing',
        created_by TEXT NOT NULL,
        created_at_utc TEXT NOT NULL,
        notes TEXT
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS agri_production_costs (
        id TEXT PRIMARY KEY,
        planting_id TEXT NOT NULL,
        cost_seeds_usd REAL DEFAULT 0.0,
        cost_fertilizer_usd REAL DEFAULT 0.0,
        cost_water_usd REAL DEFAULT 0.0,
        cost_labor_usd REAL DEFAULT 0.0,
        cost_pest_usd REAL DEFAULT 0.0,
        cost_packaging_usd REAL DEFAULT 0.0,
        cost_logistics_usd REAL DEFAULT 0.0,
        cost_overhead_usd REAL DEFAULT 0.0,
        total_cost_usd REAL DEFAULT 0.0,
        logged_by TEXT NOT NULL,
        logged_at_utc TEXT NOT NULL,
        FOREIGN KEY(planting_id) REFERENCES agri_plantings(id)
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS agri_harvests (
        id TEXT PRIMARY KEY,
        planting_id TEXT NOT NULL,
        crop_name TEXT NOT NULL,
        harvest_date_utc TEXT NOT NULL,
        mass_harvest_kg REAL NOT NULL,
        quality_grade TEXT NOT NULL DEFAULT 'Grade A',
        storage_location TEXT NOT NULL,
        mass_self_kg REAL NOT NULL DEFAULT 0.0,
        mass_comm_kg REAL NOT NULL DEFAULT 0.0,
        wholesale_cost_floor_usd REAL NOT NULL DEFAULT 0.0,
        base_price_usd REAL NOT NULL DEFAULT 0.0,
        shelf_life_half_life_days REAL NOT NULL DEFAULT 2.0,
        logged_by TEXT NOT NULL,
        logged_at_utc TEXT NOT NULL,
        inventory_item_id TEXT,
        FOREIGN KEY(planting_id) REFERENCES agri_plantings(id)
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS agri_dispositions (
        id TEXT PRIMARY KEY,
        harvest_id TEXT NOT NULL,
        disposition_type TEXT NOT NULL,
        quantity_kg REAL NOT NULL,
        destination TEXT,
        timestamp_utc TEXT NOT NULL,
        logged_by TEXT NOT NULL,
        FOREIGN KEY(harvest_id) REFERENCES agri_harvests(id)
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS security_visitor_logs (
        id TEXT PRIMARY KEY,
        national_id TEXT NOT NULL,
        full_name TEXT NOT NULL,
        time_in_utc TEXT NOT NULL,
        time_out_utc TEXT,
        destination_env TEXT NOT NULL,
        purpose TEXT NOT NULL,
        escort_officer TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Active',
        notes TEXT,
        logged_by TEXT NOT NULL
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS social_posts (
        id TEXT PRIMARY KEY,
        post_type TEXT NOT NULL,
        author TEXT NOT NULL,
        content_text TEXT,
        media_urls_json TEXT,
        tags_json TEXT,
        views_count INTEGER DEFAULT 0,
        tips_usd REAL DEFAULT 0.0,
        tips_zar REAL DEFAULT 0.0,
        tips_zwg REAL DEFAULT 0.0,
        expires_at_utc TEXT,
        created_at_utc TEXT NOT NULL
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS social_comments (
        id TEXT PRIMARY KEY,
        post_id TEXT NOT NULL,
        author TEXT NOT NULL,
        comment_text TEXT NOT NULL,
        created_at_utc TEXT NOT NULL,
        FOREIGN KEY(post_id) REFERENCES social_posts(id)
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS social_tips (
        id TEXT PRIMARY KEY,
        post_id TEXT NOT NULL,
        sender TEXT NOT NULL,
        currency TEXT NOT NULL,
        amount REAL NOT NULL,
        timestamp_utc TEXT NOT NULL,
        FOREIGN KEY(post_id) REFERENCES social_posts(id)
    );
    """)

    # Multi-Business Tenancy & Offline QR Vouchers
    db.execute("""
    CREATE TABLE IF NOT EXISTS businesses (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        category TEXT NOT NULL,
        contact_phone TEXT,
        location_address TEXT,
        tax_id TEXT,
        receipt_header TEXT,
        receipt_footer_note TEXT,
        currency_preference TEXT DEFAULT 'USD',
        owner_username TEXT,
        created_at_utc TEXT NOT NULL,
        is_active INTEGER DEFAULT 1
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS vouchers (
        vid TEXT PRIMARY KEY,
        business_id TEXT NOT NULL,
        value_amount REAL NOT NULL,
        currency TEXT NOT NULL,
        equivalent_usd REAL NOT NULL,
        issued_at_utc TEXT NOT NULL,
        expires_at_utc TEXT NOT NULL,
        issued_by_node_id TEXT NOT NULL,
        issued_for_tx_id TEXT,
        signature_hmac TEXT NOT NULL,
        status TEXT DEFAULT 'active',
        redeemed_at_utc TEXT,
        redeemed_by_tx_id TEXT,
        FOREIGN KEY (business_id) REFERENCES businesses(id)
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS business_operators (
        id TEXT PRIMARY KEY,
        business_id TEXT NOT NULL,
        username TEXT NOT NULL,
        role_in_business TEXT NOT NULL,
        permissions_json TEXT NOT NULL,
        granted_by TEXT NOT NULL,
        created_at_utc TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (business_id) REFERENCES businesses(id),
        FOREIGN KEY (username) REFERENCES users(username),
        UNIQUE(business_id, username)
    );
    """)

    # Customer Digital Bank Accounts & Multi-Currency Ledger
    db.execute("""
    CREATE TABLE IF NOT EXISTS wallets (
        account_number TEXT PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        balance_usd REAL DEFAULT 0.0,
        balance_zar REAL DEFAULT 0.0,
        balance_zwg REAL DEFAULT 0.0,
        created_at_utc TEXT NOT NULL,
        status TEXT DEFAULT 'active',
        FOREIGN KEY (username) REFERENCES users(username)
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS wallet_ledger (
        id TEXT PRIMARY KEY,
        account_number TEXT NOT NULL,
        transaction_type TEXT NOT NULL,
        currency TEXT NOT NULL,
        amount REAL NOT NULL,
        balance_after REAL NOT NULL,
        counterparty TEXT,
        reference_id TEXT,
        notes TEXT,
        timestamp_utc TEXT NOT NULL,
        signature_hmac TEXT NOT NULL,
        FOREIGN KEY (account_number) REFERENCES wallets(account_number)
    );
    """)

    # Customer Digital Receipt Vault
    db.execute("""
    CREATE TABLE IF NOT EXISTS customer_receipts (
        id TEXT PRIMARY KEY,
        transaction_id TEXT NOT NULL,
        customer_username TEXT NOT NULL,
        business_id TEXT NOT NULL,
        invoice_number TEXT NOT NULL,
        total_due_usd REAL NOT NULL,
        receipt_json TEXT NOT NULL,
        created_at_utc TEXT NOT NULL,
        audit_hash TEXT NOT NULL,
        FOREIGN KEY (transaction_id) REFERENCES transactions(id),
        FOREIGN KEY (customer_username) REFERENCES users(username),
        FOREIGN KEY (business_id) REFERENCES businesses(id)
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

    # PRAGMA Migrations: add business_id column across tenant-scoped tables
    for t_name in ["inventory", "agri_plantings", "agri_harvests", "transactions", "social_posts"]:
        try:
            cursor = db.execute(f"PRAGMA table_info({t_name})")
            cols = [row["name"] for row in cursor.fetchall()]
            if "business_id" not in cols:
                db.execute(f"ALTER TABLE {t_name} ADD COLUMN business_id TEXT DEFAULT 'biz-green-valley';")
                db.commit()
        except sqlite3.OperationalError:
            pass

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
    db.close()
    
    # Seed demo users for all 6 roles and sample records
    seed_stage1_demo_data()

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
    try:
        item_id = str(uuid.uuid4())
        db.execute("""
            INSERT INTO inventory (id, name, sku, quantity, unit, price_usd, low_stock_threshold)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (item_id, name, sku, quantity, unit, price_usd, threshold))
        db.commit()
        write_audit_log(actor, "ADD_INVENTORY", f"Added item '{name}' (SKU: {sku}) with initial quantity {quantity} {unit}")
        return item_id
    finally:
        db.close()

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

def execute_checkout_transaction(operator_username: str, total_due: float, client_req_id: str, tenders: list, items: list, business_id: str = "biz-green-valley", issue_voucher_change: bool = False, voucher_change_amount: float = 0.0, voucher_change_currency: str = "ZWG", customer_username: str = None, payment_method: str = "cash") -> dict:
    """Perform atomic split tender checks, inventory deductions, wallet debits, and receipt vaulting with WAL + BEGIN IMMEDIATE."""
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

        # 3. Handle Wallet Payment
        if payment_method == "wallet" and customer_username:
            cursor = db.execute("SELECT account_number, balance_usd FROM wallets WHERE username = ?", (customer_username,))
            w_row = cursor.fetchone()
            if not w_row:
                db.rollback()
                db.close()
                raise ValueError(f"Customer wallet not found for '{customer_username}'")
            if w_row["balance_usd"] < total_due:
                db.rollback()
                db.close()
                raise ValueError(f"Insufficient wallet balance. Available: ${w_row['balance_usd']:.2f} USD, Required: ${total_due:.2f} USD")
            
            new_bal = w_row["balance_usd"] - total_due
            db.execute("UPDATE wallets SET balance_usd = ? WHERE account_number = ?", (new_bal, w_row["account_number"]))
            
            # Record wallet ledger debit
            wtx_id = f"wtx-pos-{uuid.uuid4().hex[:8]}"
            now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
            sig = hmac.new(VAULT_SECRET_KEY, f"{wtx_id}|{w_row['account_number']}|pos_payment|{total_due:.2f}|{new_bal:.2f}".encode("utf-8"), hashlib.sha256).hexdigest()
            db.execute("""
                INSERT INTO wallet_ledger (id, account_number, transaction_type, currency, amount, balance_after, counterparty, reference_id, notes, timestamp_utc, signature_hmac)
                VALUES (?, ?, 'pos_payment', 'USD', ?, ?, ?, ?, 'POS Checkout Payment', ?, ?)
            """, (wtx_id, w_row["account_number"], -total_due, new_bal, business_id, client_req_id, now_utc, sig))
                
        # 4. Perform atomic deductions
        for item in items:
            inv_id = item["inventory_id"]
            qty = item["quantity"]
            cursor = db.execute("UPDATE inventory SET quantity = quantity - ? WHERE id = ? AND quantity >= ?", (qty, inv_id, qty))
            if cursor.rowcount == 0:
                db.rollback()
                db.close()
                raise ValueError(f"Atomic decrement check failed for inventory ID: {inv_id}")
                
        # 5. Save transaction records
        tx_id = str(uuid.uuid4())
        now = int(time.time())
        now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        db.execute("""
            INSERT INTO transactions (id, timestamp, operator_username, total_due_usd, type, client_request_id, business_id)
            VALUES (?, ?, ?, ?, 'SALE', ?, ?)
        """, (tx_id, now, operator_username, total_due, client_req_id, business_id))
        
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

        # 6. Mint voucher change if requested
        voucher_issued = None
        if issue_voucher_change and voucher_change_amount > 0:
            vid = f"vouch-{uuid.uuid4().hex[:8]}"
            now_dt = datetime.datetime.now(datetime.timezone.utc)
            exp_utc = (now_dt + datetime.timedelta(days=90)).isoformat()
            equiv_usd = voucher_change_amount
            if voucher_change_currency.upper() == "ZAR":
                equiv_usd = round(voucher_change_amount / 18.50, 2)
            elif voucher_change_currency.upper() == "ZWG":
                equiv_usd = round(voucher_change_amount / 26.50, 2)

            sig = compute_voucher_hmac(vid, business_id, voucher_change_amount, voucher_change_currency.upper(), exp_utc)
            db.execute("""
                INSERT INTO vouchers (vid, business_id, value_amount, currency, equivalent_usd, issued_at_utc, expires_at_utc, issued_by_node_id, issued_for_tx_id, signature_hmac, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'node-vault-01', ?, ?, 'active')
            """, (vid, business_id, voucher_change_amount, voucher_change_currency.upper(), equiv_usd, now_utc, exp_utc, tx_id, sig))

            voucher_issued = {
                "vid": vid,
                "business_id": business_id,
                "value_amount": voucher_change_amount,
                "currency": voucher_change_currency.upper(),
                "equivalent_usd": equiv_usd,
                "expires_at_utc": exp_utc,
                "signature_hmac": sig,
                "status": "active"
            }

        # 7. Customer Receipt Vault Archival
        if customer_username:
            rcv_id = f"rcv-{uuid.uuid4().hex[:8]}"
            inv_num = f"INV-{datetime.datetime.fromtimestamp(now).strftime('%Y%m%d')}-{tx_id[:6].upper()}"
            
            # Enrich items with inventory item names
            enriched_items = []
            for item in items:
                cursor_name = db.execute("SELECT name, unit FROM inventory WHERE id = ?", (item["inventory_id"],))
                i_row = cursor_name.fetchone()
                item_name = i_row["name"] if i_row else "Produce Item"
                unit = i_row["unit"] if i_row else "unit"
                enriched_items.append({
                    "inventory_id": item["inventory_id"],
                    "name": item_name,
                    "quantity": item["quantity"],
                    "unit": unit,
                    "price_usd_at_sale": item["price_usd_at_sale"],
                    "subtotal_usd": round(item["quantity"] * item["price_usd_at_sale"], 2)
                })

            receipt_payload = {
                "invoice_number": inv_num,
                "transaction_id": tx_id,
                "timestamp": now,
                "timestamp_iso": now_utc,
                "operator": operator_username,
                "customer": customer_username,
                "business_id": business_id,
                "total_due_usd": total_due,
                "items": enriched_items,
                "tenders": tenders,
                "voucher_issued": voucher_issued
            }
            receipt_json = json.dumps(receipt_payload)
            audit_hash = hashlib.sha256(receipt_json.encode("utf-8")).hexdigest()
            db.execute("""
                INSERT OR REPLACE INTO customer_receipts (id, transaction_id, customer_username, business_id, invoice_number, total_due_usd, receipt_json, created_at_utc, audit_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (rcv_id, tx_id, customer_username, business_id, inv_num, total_due, receipt_json, now_utc, audit_hash))
            
        # Log processed request
        response_data = {
            "status": "success",
            "transaction_id": tx_id,
            "business_id": business_id,
            "total_due_usd": total_due,
            "voucher_issued": voucher_issued,
            "customer_username": customer_username,
            "payment_method": payment_method
        }
        db.execute("""
            INSERT INTO processed_requests (client_request_id, timestamp, response_json)
            VALUES (?, ?, ?)
        """, (client_req_id, now, json.dumps(response_data)))
        
        db.commit()
        db.close()
        
        # Log audit log
        write_audit_log(operator_username, "POS_CHECKOUT", f"Sale completed ({business_id}). Transaction ID: {tx_id}. Due: ${total_due}")
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


# =====================================================================
# STAGE 1 CORE: MATHEMATICAL ENGINES & COST DERIVATION
# =====================================================================

def compute_production_cost_and_base_price(costs: dict, mass_harvest_kg: float, mass_self_kg: float = 0.0, target_markup_pct: float = 1.0) -> dict:
    """
    Computes total production expenditures, commercial yield allocation, wholesale cost floor (P_cost),
    and opening fresh retail base price (P_base).
    """
    cost_keys = ["seeds", "fertilizer", "water", "labor", "pest", "packaging", "logistics", "overhead"]
    itemized = {k: float(costs.get(k, 0.0) or 0.0) for k in cost_keys}
    total_cost = sum(itemized.values())
    
    mass_comm = max(0.001, mass_harvest_kg - mass_self_kg)
    cost_floor_per_kg = round(total_cost / mass_comm, 4)
    base_price_per_kg = round(cost_floor_per_kg * (1.0 + target_markup_pct), 4)
    
    return {
        "itemized_costs": itemized,
        "total_cost_usd": round(total_cost, 2),
        "mass_harvest_kg": round(mass_harvest_kg, 2),
        "mass_self_kg": round(mass_self_kg, 2),
        "mass_comm_kg": round(mass_comm, 2),
        "wholesale_cost_floor_usd": cost_floor_per_kg,
        "base_price_usd": base_price_per_kg
    }


def calculate_continuous_decay_price(base_price_usd: float, cost_floor_usd: float, half_life_days: float, harvest_time_iso: str, margin_floor_pct: float = 0.05) -> dict:
    """
    Evaluates real-time exponential decay price P(t) = P_cost + (P_base - P_cost) * e^(-lambda * t)
    safeguarded by a cost margin floor guardrail.
    """
    if half_life_days <= 0:
        half_life_days = 2.0
    decay_k = math.log(2) / half_life_days

    try:
        harvest_dt = datetime.datetime.fromisoformat(harvest_time_iso.replace("Z", "+00:00"))
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        elapsed_days = max(0.0, (now_dt - harvest_dt).total_seconds() / 86400.0)
    except Exception:
        elapsed_days = 0.0

    margin = max(0.0, base_price_usd - cost_floor_usd)
    decay_factor = math.exp(-decay_k * elapsed_days)
    raw_decay_price = cost_floor_usd + (margin * decay_factor)

    cost_floor_guaranteed = cost_floor_usd * (1.0 + margin_floor_pct)
    current_price_usd = round(max(raw_decay_price, cost_floor_guaranteed), 2)
    discount_pct = round(max(0.0, (base_price_usd - current_price_usd) / base_price_usd * 100), 1) if base_price_usd > 0 else 0.0

    return {
        "base_price_usd": round(base_price_usd, 2),
        "cost_floor_usd": round(cost_floor_usd, 2),
        "current_price_usd": current_price_usd,
        "elapsed_days": round(elapsed_days, 2),
        "decay_factor": round(decay_factor, 4),
        "discount_pct": discount_pct,
        "is_floor_active": raw_decay_price <= cost_floor_guaranteed
    }


def calculate_mixed_tender_change(total_usd: float, tendered_usd: float = 0.0, tendered_zar: float = 0.0, tendered_zwg: float = 0.0, rate_zar: float = 18.5, rate_zwg: float = 26.5) -> dict:
    """
    Computes total tendered value converted to USD across multi-currency tri-ledger (USD, ZAR, ZWG)
    and calculates change returned in ZWG and ZAR to preserve hard currency.
    """
    val_usd_from_zar = (tendered_zar / rate_zar) if rate_zar > 0 else 0.0
    val_usd_from_zwg = (tendered_zwg / rate_zwg) if rate_zwg > 0 else 0.0
    total_paid_usd = round(tendered_usd + val_usd_from_zar + val_usd_from_zwg, 4)

    deficit_usd = round(max(0.0, total_usd - total_paid_usd), 2)
    change_usd = round(max(0.0, total_paid_usd - total_usd), 2)
    change_zwg = round(change_usd * rate_zwg, 2)
    change_zar = round(change_usd * rate_zar, 2)

    return {
        "total_due_usd": round(total_usd, 2),
        "total_paid_usd": round(total_paid_usd, 2),
        "is_fully_paid": total_paid_usd >= (total_usd - 0.001),
        "deficit_usd": deficit_usd,
        "change_usd": change_usd,
        "change_zwg": change_zwg,
        "change_zar": change_zar
    }


# =====================================================================
# STAGE 1 CORE: AGRICULTURE CRUD
# =====================================================================

def create_planting(crop_variety: str, plot_bed_id: str, planting_date_utc: str, seeding_density: float, target_maturity_date_utc: str, initial_soil_hydration_pct: float, created_by: str, notes: str = "") -> dict:
    planting_id = f"plant-{uuid.uuid4().hex[:8]}"
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with get_db() as db:
        db.execute("""
            INSERT INTO agri_plantings (id, crop_variety, plot_bed_id, planting_date_utc, seeding_density, target_maturity_date_utc, initial_soil_hydration_pct, status, created_by, created_at_utc, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'growing', ?, ?, ?)
        """, (planting_id, crop_variety, plot_bed_id, planting_date_utc, seeding_density, target_maturity_date_utc, initial_soil_hydration_pct, created_by, now_utc, notes))
        db.commit()
    return {"id": planting_id, "crop_variety": crop_variety, "plot_bed_id": plot_bed_id, "status": "growing"}


def list_plantings() -> list:
    with get_db() as db:
        cursor = db.execute("SELECT * FROM agri_plantings ORDER BY created_at_utc DESC")
        rows = [dict(r) for r in cursor.fetchall()]
    return rows


def log_production_costs(planting_id: str, costs: dict, logged_by: str) -> dict:
    cost_id = f"cost-{uuid.uuid4().hex[:8]}"
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    c_seeds = float(costs.get("seeds", 0.0) or 0.0)
    c_fert = float(costs.get("fertilizer", 0.0) or 0.0)
    c_water = float(costs.get("water", 0.0) or 0.0)
    c_labor = float(costs.get("labor", 0.0) or 0.0)
    c_pest = float(costs.get("pest", 0.0) or 0.0)
    c_pack = float(costs.get("packaging", 0.0) or 0.0)
    c_log = float(costs.get("logistics", 0.0) or 0.0)
    c_over = float(costs.get("overhead", 0.0) or 0.0)
    total = c_seeds + c_fert + c_water + c_labor + c_pest + c_pack + c_log + c_over

    with get_db() as db:
        db.execute("""
            INSERT INTO agri_production_costs (id, planting_id, cost_seeds_usd, cost_fertilizer_usd, cost_water_usd, cost_labor_usd, cost_pest_usd, cost_packaging_usd, cost_logistics_usd, cost_overhead_usd, total_cost_usd, logged_by, logged_at_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (cost_id, planting_id, c_seeds, c_fert, c_water, c_labor, c_pest, c_pack, c_log, c_over, total, logged_by, now_utc))
        db.commit()
    return {"id": cost_id, "planting_id": planting_id, "total_cost_usd": total}


def get_production_costs(planting_id: str) -> list:
    with get_db() as db:
        cursor = db.execute("SELECT * FROM agri_production_costs WHERE planting_id = ? ORDER BY logged_at_utc DESC", (planting_id,))
        rows = [dict(r) for r in cursor.fetchall()]
    return rows


def log_harvest_and_sync_inventory(planting_id: str, crop_name: str, harvest_date_utc: str, mass_harvest_kg: float, quality_grade: str, storage_location: str, mass_self_kg: float, target_markup_pct: float, shelf_life_half_life_days: float, logged_by: str) -> dict:
    """
    Logs harvest, aggregates planting costs, automatically derives P_cost & P_base,
    and inserts commercial batch into POS inventory.
    """
    harvest_id = f"harv-{uuid.uuid4().hex[:8]}"
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()

    with get_db() as db:
        # Aggregate costs for this planting
        cursor = db.execute("SELECT SUM(total_cost_usd) as total FROM agri_production_costs WHERE planting_id = ?", (planting_id,))
        row = cursor.fetchone()
        total_cost = row["total"] if row and row["total"] is not None else 0.0

        mass_comm = max(0.0, mass_harvest_kg - mass_self_kg)
        cost_floor = round(total_cost / max(0.001, mass_comm), 2) if mass_comm > 0 else 0.50
        if cost_floor <= 0.0:
            cost_floor = 0.50
        base_price = round(cost_floor * (1.0 + target_markup_pct), 2)

        # Sync into POS inventory
        item_name = f"Fresh {crop_name} ({quality_grade})"
        cursor_inv = db.execute("SELECT id FROM inventory WHERE name = ?", (item_name,))
        existing_row = cursor_inv.fetchone()
        if existing_row:
            inv_id = existing_row["id"]
            db.execute("""
                UPDATE inventory 
                SET quantity = quantity + ?, price_usd = ?, cost_price_usd = ?
                WHERE id = ?
            """, (mass_comm, base_price, cost_floor, inv_id))
        else:
            inv_id = str(uuid.uuid4())
            sku = f"{crop_name.upper().replace(' ', '-')[:8]}-{uuid.uuid4().hex[:4].upper()}"
            db.execute("""
                INSERT INTO inventory (id, name, sku, quantity, unit, price_usd, cost_price_usd, low_stock_threshold)
                VALUES (?, ?, ?, ?, 'kg', ?, ?, 5.0)
            """, (inv_id, item_name, sku, mass_comm, base_price, cost_floor))

        # Record Harvest
        db.execute("""
            INSERT INTO agri_harvests (id, planting_id, crop_name, harvest_date_utc, mass_harvest_kg, quality_grade, storage_location, mass_self_kg, mass_comm_kg, wholesale_cost_floor_usd, base_price_usd, shelf_life_half_life_days, logged_by, logged_at_utc, inventory_item_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (harvest_id, planting_id, crop_name, harvest_date_utc, mass_harvest_kg, quality_grade, storage_location, mass_self_kg, mass_comm, cost_floor, base_price, shelf_life_half_life_days, logged_by, now_utc, inv_id))

        # Mark planting as harvested
        db.execute("UPDATE agri_plantings SET status = 'harvested' WHERE id = ?", (planting_id,))

        # Log dispositions
        if mass_self_kg > 0:
            db.execute("""
                INSERT INTO agri_dispositions (id, harvest_id, disposition_type, quantity_kg, destination, timestamp_utc, logged_by)
                VALUES (?, ?, 'self_consumption', ?, 'Household / Farm Kitchen', ?, ?)
            """, (f"disp-{uuid.uuid4().hex[:8]}", harvest_id, mass_self_kg, now_utc, logged_by))
        if mass_comm > 0:
            db.execute("""
                INSERT INTO agri_dispositions (id, harvest_id, disposition_type, quantity_kg, destination, timestamp_utc, logged_by)
                VALUES (?, ?, 'pos_commercial_transfer', ?, 'Composable Enterprise POS', ?, ?)
            """, (f"disp-{uuid.uuid4().hex[:8]}", harvest_id, mass_comm, now_utc, logged_by))

        db.commit()

    return {
        "harvest_id": harvest_id,
        "planting_id": planting_id,
        "crop_name": crop_name,
        "mass_harvest_kg": mass_harvest_kg,
        "mass_self_kg": mass_self_kg,
        "mass_comm_kg": mass_comm,
        "wholesale_cost_floor_usd": cost_floor,
        "base_price_usd": base_price,
        "inventory_item_id": inv_id
    }


def list_harvests() -> list:
    with get_db() as db:
        cursor = db.execute("SELECT * FROM agri_harvests ORDER BY harvest_date_utc DESC")
        rows = [dict(r) for r in cursor.fetchall()]
    return rows


def list_dispositions(harvest_id: str = None) -> list:
    with get_db() as db:
        if harvest_id:
            cursor = db.execute("SELECT * FROM agri_dispositions WHERE harvest_id = ? ORDER BY timestamp_utc DESC", (harvest_id,))
        else:
            cursor = db.execute("SELECT * FROM agri_dispositions ORDER BY timestamp_utc DESC")
        rows = [dict(r) for r in cursor.fetchall()]
    return rows


# =====================================================================
# STAGE 1 CORE: SECURITY VISITOR GATEKEEPER CRUD
# =====================================================================

def checkin_visitor(national_id: str, full_name: str, destination_env: str, purpose: str, escort_officer: str, logged_by: str, notes: str = "") -> dict:
    vis_id = f"vis-{uuid.uuid4().hex[:8]}"
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with get_db() as db:
        db.execute("""
            INSERT INTO security_visitor_logs (id, national_id, full_name, time_in_utc, destination_env, purpose, escort_officer, status, notes, logged_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Active', ?, ?)
        """, (vis_id, national_id, full_name, now_utc, destination_env, purpose, escort_officer, notes, logged_by))
        db.commit()
    return {"id": vis_id, "national_id": national_id, "full_name": full_name, "time_in_utc": now_utc, "status": "Active"}


def checkout_visitor(visitor_id: str, logged_by: str) -> dict:
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with get_db() as db:
        db.execute("""
            UPDATE security_visitor_logs
            SET time_out_utc = ?, status = 'Checked-Out'
            WHERE id = ?
        """, (now_utc, visitor_id))
        db.commit()
    return {"id": visitor_id, "time_out_utc": now_utc, "status": "Checked-Out"}


def list_visitors(search: str = None, destination: str = None, status: str = None) -> list:
    query = "SELECT * FROM security_visitor_logs WHERE 1=1"
    params = []
    if search:
        query += " AND (full_name LIKE ? OR national_id LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    if destination:
        query += " AND destination_env = ?"
        params.append(destination)
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY time_in_utc DESC"
    with get_db() as db:
        cursor = db.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
    return rows


def get_active_visitors() -> list:
    return list_visitors(status="Active")


# =====================================================================
# STAGE 1 CORE: HYBRID SOCIAL MEDIA HUB CRUD
# =====================================================================

def create_social_post(post_type: str, author: str, content_text: str, media_urls: list = None, tags: list = None) -> dict:
    post_id = f"post-{uuid.uuid4().hex[:8]}"
    now_dt = datetime.datetime.now(datetime.timezone.utc)
    now_utc = now_dt.isoformat()

    expires_at_utc = None
    if post_type == "story":
        expires_at_utc = (now_dt + datetime.timedelta(hours=24)).isoformat()

    with get_db() as db:
        db.execute("""
            INSERT INTO social_posts (id, post_type, author, content_text, media_urls_json, tags_json, views_count, tips_usd, tips_zar, tips_zwg, expires_at_utc, created_at_utc)
            VALUES (?, ?, ?, ?, ?, ?, 0, 0.0, 0.0, 0.0, ?, ?)
        """, (post_id, post_type, author, content_text, json.dumps(media_urls or []), json.dumps(tags or []), expires_at_utc, now_utc))
        db.commit()
    return {"id": post_id, "post_type": post_type, "author": author, "created_at_utc": now_utc}


def list_social_posts(post_type: str = None, include_expired: bool = False) -> list:
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    query = "SELECT * FROM social_posts WHERE 1=1"
    params = []
    if post_type:
        query += " AND post_type = ?"
        params.append(post_type)
    if not include_expired:
        query += " AND (expires_at_utc IS NULL OR expires_at_utc > ?)"
        params.append(now_utc)
    query += " ORDER BY created_at_utc DESC"
    with get_db() as db:
        cursor = db.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
    for row in rows:
        row["media_urls"] = json.loads(row.get("media_urls_json") or "[]")
        row["tags"] = json.loads(row.get("tags_json") or "[]")
    return rows


def add_social_comment(post_id: str, author: str, comment_text: str) -> dict:
    cid = f"comm-{uuid.uuid4().hex[:8]}"
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with get_db() as db:
        db.execute("""
            INSERT INTO social_comments (id, post_id, author, comment_text, created_at_utc)
            VALUES (?, ?, ?, ?, ?)
        """, (cid, post_id, author, comment_text, now_utc))
        db.commit()
    return {"id": cid, "post_id": post_id, "author": author, "comment_text": comment_text, "created_at_utc": now_utc}


def get_social_comments(post_id: str) -> list:
    with get_db() as db:
        cursor = db.execute("SELECT * FROM social_comments WHERE post_id = ? ORDER BY created_at_utc ASC", (post_id,))
        rows = [dict(r) for r in cursor.fetchall()]
    return rows


def tip_social_post(post_id: str, sender: str, currency: str, amount: float) -> dict:
    tid = f"tip-{uuid.uuid4().hex[:8]}"
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    currency = currency.upper()

    with get_db() as db:
        db.execute("""
            INSERT INTO social_tips (id, post_id, sender, currency, amount, timestamp_utc)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (tid, post_id, sender, currency, amount, now_utc))

        if currency == "USD":
            db.execute("UPDATE social_posts SET tips_usd = tips_usd + ? WHERE id = ?", (amount, post_id))
        elif currency == "ZAR":
            db.execute("UPDATE social_posts SET tips_zar = tips_zar + ? WHERE id = ?", (amount, post_id))
        elif currency == "ZWG":
            db.execute("UPDATE social_posts SET tips_zwg = tips_zwg + ? WHERE id = ?", (amount, post_id))

        db.commit()
    return {"id": tid, "post_id": post_id, "currency": currency, "amount": amount}


# =====================================================================
# MULTI-BUSINESS TENANCY & OFFLINE QR VOUCHER HELPER FUNCTIONS
# =====================================================================

def compute_voucher_hmac(vid: str, business_id: str, value_amount: float, currency: str, expires_at_utc: str) -> str:
    """Computes tamper-proof HMAC-SHA256 signature for offline bearer voucher."""
    secret = os.environ.get("MADN_VAULT_SECRET_KEY", "madn-vault-root-security-master-key-2026")
    msg = f"{vid}|{business_id}|{value_amount:.2f}|{currency}|{expires_at_utc}"
    return hmac.new(secret.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()


def create_business(name: str, category: str, contact_phone: str = "", location_address: str = "", tax_id: str = "", receipt_header: str = "", receipt_footer_note: str = "", currency_preference: str = "USD", owner_username: str = "admin") -> dict:
    """Creates a new business entity for multi-tenant enterprise operations."""
    biz_id = f"biz-{uuid.uuid4().hex[:8]}"
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if not receipt_header:
        receipt_header = f"{name} - Fresh Agricultural Depot"
    if not receipt_footer_note:
        receipt_footer_note = "Thank you for supporting local community agriculture!"

    with get_db() as db:
        db.execute("""
            INSERT INTO businesses (id, name, category, contact_phone, location_address, tax_id, receipt_header, receipt_footer_note, currency_preference, owner_username, created_at_utc, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (biz_id, name, category, contact_phone, location_address, tax_id, receipt_header, receipt_footer_note, currency_preference, owner_username, now_utc))

    return get_business_by_id(biz_id)


def get_all_businesses() -> list:
    """Retrieves list of all active businesses."""
    with get_db() as db:
        cursor = db.execute("SELECT * FROM businesses WHERE is_active = 1 ORDER BY name ASC")
        return [dict(row) for row in cursor.fetchall()]


def get_business_by_id(biz_id: str) -> dict:
    """Retrieves business profile by ID."""
    with get_db() as db:
        cursor = db.execute("SELECT * FROM businesses WHERE id = ?", (biz_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def mint_offline_voucher(business_id: str, value_amount: float, currency: str = "ZWG", issued_by_node_id: str = "node-vault-01", issued_for_tx_id: str = None, validity_days: int = 90) -> dict:
    """
    Mints a cryptographically signed offline bearer voucher (for cash change or credit).
    Calculates equivalent USD and signs with HMAC-SHA256.
    """
    vid = f"vouch-{uuid.uuid4().hex[:8]}"
    now_dt = datetime.datetime.now(datetime.timezone.utc)
    now_utc = now_dt.isoformat()
    exp_utc = (now_dt + datetime.timedelta(days=validity_days)).isoformat()

    # Calculate USD equivalent
    equiv_usd = value_amount
    if currency.upper() == "ZAR":
        equiv_usd = round(value_amount / 18.50, 2)
    elif currency.upper() == "ZWG":
        equiv_usd = round(value_amount / 26.50, 2)

    sig = compute_voucher_hmac(vid, business_id, value_amount, currency.upper(), exp_utc)

    with get_db() as db:
        db.execute("""
            INSERT INTO vouchers (vid, business_id, value_amount, currency, equivalent_usd, issued_at_utc, expires_at_utc, issued_by_node_id, issued_for_tx_id, signature_hmac, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
        """, (vid, business_id, value_amount, currency.upper(), equiv_usd, now_utc, exp_utc, issued_by_node_id, issued_for_tx_id, sig))

    return {
        "vid": vid,
        "business_id": business_id,
        "value_amount": value_amount,
        "currency": currency.upper(),
        "equivalent_usd": equiv_usd,
        "issued_at_utc": now_utc,
        "expires_at_utc": exp_utc,
        "issued_by_node_id": issued_by_node_id,
        "issued_for_tx_id": issued_for_tx_id,
        "signature_hmac": sig,
        "status": "active"
    }


def verify_and_redeem_voucher(vid: str, business_id: str = None, redeemed_by_tx_id: str = None) -> dict:
    """
    Verifies cryptographic signature and redeems voucher balance offline.
    Prevents double-spending by checking status and expiry.
    """
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()

    with get_db() as db:
        cursor = db.execute("SELECT * FROM vouchers WHERE vid = ?", (vid,))
        row = cursor.fetchone()
        if not row:
            return {"success": False, "detail": "Voucher not found."}

        v = dict(row)
        if v["status"] != "active":
            return {"success": False, "detail": f"Voucher is already {v['status']}."}

        # Check expiry
        if v["expires_at_utc"] < now_utc:
            db.execute("UPDATE vouchers SET status = 'expired' WHERE vid = ?", (vid,))
            return {"success": False, "detail": "Voucher has expired."}

        # Verify HMAC cryptographic integrity
        expected_sig = compute_voucher_hmac(v["vid"], v["business_id"], v["value_amount"], v["currency"], v["expires_at_utc"])
        if not hmac.compare_digest(v["signature_hmac"], expected_sig):
            db.execute("UPDATE vouchers SET status = 'voided' WHERE vid = ?", (vid,))
            return {"success": False, "detail": "Cryptographic signature verification failed (Tampered voucher)."}

        # Optional business check
        if business_id and v["business_id"] != business_id:
            # Check if business allows cross-redemption or reject
            pass

        # Mark redeemed
        db.execute("""
            UPDATE vouchers 
            SET status = 'redeemed', redeemed_at_utc = ?, redeemed_by_tx_id = ?
            WHERE vid = ?
        """, (now_utc, redeemed_by_tx_id, vid))

        return {
            "success": True,
            "vid": v["vid"],
            "business_id": v["business_id"],
            "value_amount": v["value_amount"],
            "currency": v["currency"],
            "equivalent_usd": v["equivalent_usd"],
            "status": "redeemed",
            "redeemed_at_utc": now_utc
        }


def get_voucher_by_id(vid: str) -> dict:
    """Retrieves voucher details by ID."""
    with get_db() as db:
        cursor = db.execute("SELECT * FROM vouchers WHERE vid = ?", (vid,))
        row = cursor.fetchone()
        return dict(row) if row else None


def generate_receipt_data(tx_id: str) -> dict:
    """Generates structured receipt metadata for automatic PDF/thermal synthesis."""
    with get_db() as db:
        # Fetch transaction
        cursor_tx = db.execute("SELECT * FROM transactions WHERE id = ?", (tx_id,))
        tx_row = cursor_tx.fetchone()
        if not tx_row:
            return None
        tx = dict(tx_row)

        biz_id = tx.get("business_id", "biz-green-valley")
        biz = get_business_by_id(biz_id)
        if not biz:
            biz = {
                "name": "MADN Agribusiness Hub",
                "category": "Agriculture",
                "contact_phone": "+263 77 123 4567",
                "location_address": "Bulawayo Market Hub",
                "tax_id": "ZW-99281-AGRI",
                "receipt_header": "MADN Agribusiness Hub - Fresh Produce",
                "receipt_footer_note": "Thank you for supporting community smallholders!"
            }

        # Fetch items
        cursor_items = db.execute("""
            SELECT ti.*, inv.name as item_name, inv.unit
            FROM transaction_items ti
            LEFT JOIN inventory inv ON ti.inventory_id = inv.id
            WHERE ti.transaction_id = ?
        """, (tx_id,))
        items = [dict(r) for r in cursor_items.fetchall()]

        # Fetch tenders
        cursor_tenders = db.execute("SELECT * FROM transaction_tenders WHERE transaction_id = ?", (tx_id,))
        tenders = [dict(r) for r in cursor_tenders.fetchall()]

        # Fetch any change voucher
        cursor_vouch = db.execute("SELECT * FROM vouchers WHERE issued_for_tx_id = ?", (tx_id,))
        vouch_row = cursor_vouch.fetchone()
        voucher_issued = dict(vouch_row) if vouch_row else None

        # Build cryptographic verification payload
        audit_payload = f"TX:{tx_id}|BIZ:{biz_id}|TOTAL:{tx['total_due_usd']:.2f}|TIME:{tx['timestamp']}"
        audit_hash = hashlib.sha256(audit_payload.encode("utf-8")).hexdigest()

        return {
            "invoice_number": f"INV-{datetime.datetime.fromtimestamp(tx['timestamp']).strftime('%Y%m%d')}-{tx_id[:6].upper()}",
            "transaction_id": tx_id,
            "timestamp": tx["timestamp"],
            "timestamp_iso": datetime.datetime.fromtimestamp(tx["timestamp"], tz=datetime.timezone.utc).isoformat(),
            "operator": tx["operator_username"],
            "business": biz,
            "items": items,
            "total_due_usd": tx["total_due_usd"],
            "tenders": tenders,
            "voucher_issued": voucher_issued,
            "audit_hash": audit_hash
        }


# =====================================================================
# HIERARCHICAL RBAC & BUSINESS OPERATOR DELEGATION
# =====================================================================

def assign_business_operator(business_id: str, username: str, role_in_business: str, permissions: list, granted_by: str) -> dict:
    """Assigns or updates an operator's role and granular subsystem permissions for a business."""
    op_id = f"op-{uuid.uuid4().hex[:8]}"
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    perm_json = json.dumps(permissions)

    with get_db() as db:
        # Check if user already has an assignment for this business
        cursor = db.execute("SELECT id FROM business_operators WHERE business_id = ? AND username = ?", (business_id, username))
        existing = cursor.fetchone()
        if existing:
            db.execute("""
                UPDATE business_operators
                SET role_in_business = ?, permissions_json = ?, granted_by = ?, is_active = 1
                WHERE id = ?
            """, (role_in_business, perm_json, granted_by, existing["id"]))
            op_id = existing["id"]
        else:
            db.execute("""
                INSERT INTO business_operators (id, business_id, username, role_in_business, permissions_json, granted_by, created_at_utc, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (op_id, business_id, username, role_in_business, perm_json, granted_by, now_utc))

    write_audit_log(granted_by, "ASSIGN_OPERATOR", f"Assigned {username} as '{role_in_business}' in {business_id} with permissions {permissions}")
    return {
        "id": op_id,
        "business_id": business_id,
        "username": username,
        "role_in_business": role_in_business,
        "permissions": permissions,
        "granted_by": granted_by,
        "is_active": 1
    }

def get_business_operators(business_id: str) -> list:
    """Returns all operators and their permissions for a given business."""
    with get_db() as db:
        cursor = db.execute("""
            SELECT bo.*, u.role as global_role
            FROM business_operators bo
            LEFT JOIN users u ON bo.username = u.username
            WHERE bo.business_id = ? AND bo.is_active = 1
            ORDER BY bo.created_at_utc ASC
        """, (business_id,))
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["permissions"] = json.loads(d.get("permissions_json") or "[]")
            except Exception:
                d["permissions"] = []
            result.append(d)
        return result

def get_operator_permissions(business_id: str, username: str) -> list:
    """Returns the list of granted permissions for a user within a business."""
    with get_db() as db:
        # 1. If user is system super admin, grant all permissions
        cursor_u = db.execute("SELECT role FROM users WHERE username = ?", (username,))
        u_row = cursor_u.fetchone()
        if u_row and u_row["role"] == "admin":
            return ["admin", "pos", "inventory", "agriculture", "security", "social", "vouchers", "reports"]

        # 2. If user is the business owner/creator, grant all business permissions
        cursor_b = db.execute("SELECT owner_username FROM businesses WHERE id = ?", (business_id,))
        b_row = cursor_b.fetchone()
        if b_row and b_row["owner_username"] == username:
            return ["admin", "pos", "inventory", "agriculture", "security", "social", "vouchers", "reports"]

        # 3. Check business_operators table
        cursor_op = db.execute("""
            SELECT role_in_business, permissions_json FROM business_operators
            WHERE business_id = ? AND username = ? AND is_active = 1
        """, (business_id, username))
        op_row = cursor_op.fetchone()
        if op_row:
            if op_row["role_in_business"] in ["admin", "manager"]:
                return ["admin", "pos", "inventory", "agriculture", "security", "social", "vouchers", "reports"]
            try:
                return json.loads(op_row["permissions_json"])
            except Exception:
                return []

        return []

def revoke_business_operator(business_id: str, username: str, revoked_by: str = "admin") -> bool:
    """Revokes an operator's access to a business."""
    with get_db() as db:
        db.execute("""
            UPDATE business_operators SET is_active = 0
            WHERE business_id = ? AND username = ?
        """, (business_id, username))
    write_audit_log(revoked_by, "REVOKE_OPERATOR", f"Revoked operator access for {username} in {business_id}")
    return True

def has_business_permission(username: str, business_id: str, required_permission: str) -> bool:
    """Checks whether a user has a specific permission in a business."""
    perms = get_operator_permissions(business_id, username)
    return ("admin" in perms) or (required_permission in perms)


# =====================================================================
# CUSTOMER DIGITAL BANKING, MULTI-CURRENCY LEDGER & RECEIPT VAULT
# =====================================================================

def create_wallet_for_user(username: str) -> dict:
    """Provisions a new multi-currency wallet account for a registered user."""
    acc_num = f"ACC-2026-{uuid.uuid4().hex[:6].upper()}"
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with get_db() as db:
        cursor = db.execute("SELECT * FROM wallets WHERE username = ?", (username,))
        existing = cursor.fetchone()
        if existing:
            return dict(existing)
        db.execute("""
            INSERT INTO wallets (account_number, username, balance_usd, balance_zar, balance_zwg, created_at_utc, status)
            VALUES (?, ?, 0.0, 0.0, 0.0, ?, 'active')
        """, (acc_num, username, now_utc))
        return {
            "account_number": acc_num,
            "username": username,
            "balance_usd": 0.0,
            "balance_zar": 0.0,
            "balance_zwg": 0.0,
            "created_at_utc": now_utc,
            "status": "active"
        }

def get_wallet_by_username(username: str, auto_create: bool = True) -> dict:
    """Returns the multi-currency wallet details for a user."""
    with get_db() as db:
        cursor = db.execute("SELECT * FROM wallets WHERE username = ?", (username,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    if auto_create:
        return create_wallet_for_user(username)
    return None

def topup_wallet(username: str, currency: str, amount: float, notes: str = "Deposit", performed_by: str = "system") -> dict:
    """Deposits funds into a user's wallet and creates an audit ledger entry."""
    curr = currency.upper()
    if curr not in ["USD", "ZAR", "ZWG"]:
        raise ValueError(f"Unsupported currency: {currency}")
    if amount <= 0:
        raise ValueError("Top-up amount must be positive.")

    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    wallet = get_wallet_by_username(username)
    acc_num = wallet["account_number"]
    col_name = f"balance_{curr.lower()}"

    with get_db() as db:
        db.execute(f"UPDATE wallets SET {col_name} = {col_name} + ? WHERE account_number = ?", (amount, acc_num))
        cursor = db.execute(f"SELECT {col_name} FROM wallets WHERE account_number = ?", (acc_num,))
        new_bal = cursor.fetchone()[col_name]

        # Signature payload
        tx_id = f"wtx-{uuid.uuid4().hex[:8]}"
        payload = f"{tx_id}|{acc_num}|deposit|{curr}|{amount:.2f}|{new_bal:.2f}|{now_utc}"
        sig = hmac.new(VAULT_SECRET_KEY, payload.encode("utf-8"), hashlib.sha256).hexdigest()

        db.execute("""
            INSERT INTO wallet_ledger (id, account_number, transaction_type, currency, amount, balance_after, counterparty, reference_id, notes, timestamp_utc, signature_hmac)
            VALUES (?, ?, 'deposit', ?, ?, ?, ?, ?, ?, ?, ?)
        """, (tx_id, acc_num, curr, amount, new_bal, performed_by, tx_id, notes, now_utc, sig))

    write_audit_log(performed_by, "WALLET_TOPUP", f"Deposited {amount} {curr} to {username} ({acc_num}). New balance: {new_bal} {curr}")
    return {
        "status": "success",
        "account_number": acc_num,
        "username": username,
        "currency": curr,
        "amount_deposited": amount,
        "new_balance": round(new_bal, 2),
        "transaction_id": tx_id
    }

def execute_wallet_transfer(from_user: str, to_user: str, currency: str, amount: float, tx_type: str = "p2p_transfer", counterparty: str = None, reference_id: str = None, notes: str = "") -> dict:
    """Atomically transfers funds from one user's wallet to another user's wallet."""
    curr = currency.upper()
    if curr not in ["USD", "ZAR", "ZWG"]:
        raise ValueError(f"Unsupported currency: {currency}")
    if amount <= 0:
        raise ValueError("Transfer amount must be positive.")

    from_wallet = get_wallet_by_username(from_user)
    to_wallet = get_wallet_by_username(to_user)
    col_name = f"balance_{curr.lower()}"

    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    wtx_id = f"wtx-{uuid.uuid4().hex[:8]}"

    with get_db() as db:
        cursor = db.execute(f"SELECT {col_name} FROM wallets WHERE account_number = ?", (from_wallet["account_number"],))
        sender_bal = cursor.fetchone()[col_name]
        if sender_bal < amount:
            raise ValueError(f"Insufficient funds in {curr}. Available: {sender_bal:.2f}, Required: {amount:.2f}")

        # Debit sender
        db.execute(f"UPDATE wallets SET {col_name} = {col_name} - ? WHERE account_number = ?", (amount, from_wallet["account_number"]))
        new_sender_bal = sender_bal - amount

        # Credit receiver
        db.execute(f"UPDATE wallets SET {col_name} = {col_name} + ? WHERE account_number = ?", (amount, to_wallet["account_number"]))
        cursor = db.execute(f"SELECT {col_name} FROM wallets WHERE account_number = ?", (to_wallet["account_number"],))
        new_recv_bal = cursor.fetchone()[col_name]

        # Ledger entries
        sig_debit = hmac.new(VAULT_SECRET_KEY, f"{wtx_id}-deb|{from_wallet['account_number']}|{amount:.2f}|{new_sender_bal:.2f}".encode("utf-8"), hashlib.sha256).hexdigest()
        db.execute("""
            INSERT INTO wallet_ledger (id, account_number, transaction_type, currency, amount, balance_after, counterparty, reference_id, notes, timestamp_utc, signature_hmac)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (f"{wtx_id}-deb", from_wallet["account_number"], tx_type, curr, -amount, new_sender_bal, to_user, reference_id or wtx_id, notes or f"Transfer to @{to_user}", now_utc, sig_debit))

        sig_credit = hmac.new(VAULT_SECRET_KEY, f"{wtx_id}-crd|{to_wallet['account_number']}|{amount:.2f}|{new_recv_bal:.2f}".encode("utf-8"), hashlib.sha256).hexdigest()
        db.execute("""
            INSERT INTO wallet_ledger (id, account_number, transaction_type, currency, amount, balance_after, counterparty, reference_id, notes, timestamp_utc, signature_hmac)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (f"{wtx_id}-crd", to_wallet["account_number"], tx_type, curr, amount, new_recv_bal, from_user, reference_id or wtx_id, notes or f"Received from @{from_user}", now_utc, sig_credit))

    write_audit_log(from_user, "WALLET_TRANSFER", f"Transferred {amount} {curr} from @{from_user} to @{to_user}")
    return {
        "status": "success",
        "transfer_id": wtx_id,
        "from_user": from_user,
        "to_user": to_user,
        "currency": curr,
        "amount": amount,
        "sender_new_balance": round(new_sender_bal, 2)
    }

def deposit_voucher_to_wallet(username: str, vid: str) -> dict:
    """Redeems an offline QR voucher and converts it directly into liquid wallet balance."""
    wallet = get_wallet_by_username(username)
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Verify & redeem the voucher
    redemption = verify_and_redeem_voucher(vid, redeemed_by_tx_id=f"WALLET-DEP-{wallet['account_number']}")
    if not redemption.get("success"):
        return redemption

    curr = redemption["currency"]
    amt = redemption["value_amount"]
    col_name = f"balance_{curr.lower()}"
    wtx_id = f"wtx-vdep-{uuid.uuid4().hex[:8]}"

    with get_db() as db:
        db.execute(f"UPDATE wallets SET {col_name} = {col_name} + ? WHERE account_number = ?", (amt, wallet["account_number"]))
        cursor = db.execute(f"SELECT {col_name} FROM wallets WHERE account_number = ?", (wallet["account_number"],))
        new_bal = cursor.fetchone()[col_name]

        sig = hmac.new(VAULT_SECRET_KEY, f"{wtx_id}|{wallet['account_number']}|voucher_deposit|{amt:.2f}|{new_bal:.2f}".encode("utf-8"), hashlib.sha256).hexdigest()
        db.execute("""
            INSERT INTO wallet_ledger (id, account_number, transaction_type, currency, amount, balance_after, counterparty, reference_id, notes, timestamp_utc, signature_hmac)
            VALUES (?, ?, 'voucher_deposit', ?, ?, ?, ?, ?, ?, ?, ?)
        """, (wtx_id, wallet["account_number"], curr, amt, new_bal, redemption["business_id"], vid, f"Voucher {vid} converted to wallet balance", now_utc, sig))

    write_audit_log(username, "VOUCHER_TO_WALLET", f"Converted voucher {vid} ({amt} {curr}) into wallet balance.")
    return {
        "success": True,
        "vid": vid,
        "currency": curr,
        "amount_credited": amt,
        "new_balance": round(new_bal, 2),
        "account_number": wallet["account_number"]
    }

def get_wallet_ledger(username: str, limit: int = 50) -> list:
    """Returns ledger transactions for a user's wallet account."""
    wallet = get_wallet_by_username(username)
    with get_db() as db:
        cursor = db.execute("""
            SELECT * FROM wallet_ledger
            WHERE account_number = ?
            ORDER BY timestamp_utc DESC
            LIMIT ?
        """, (wallet["account_number"], limit))
        return [dict(r) for r in cursor.fetchall()]

def archive_customer_receipt(tx_id: str, customer_username: str, business_id: str, receipt_data: dict) -> dict:
    """Permanently stores an itemized receipt in the customer's digital receipt vault."""
    rcv_id = f"rcv-{uuid.uuid4().hex[:8]}"
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    receipt_json = json.dumps(receipt_data)
    inv_num = receipt_data.get("invoice_number", f"INV-{tx_id[:8].upper()}")
    total_due = receipt_data.get("total_due_usd", 0.0)
    audit_hash = receipt_data.get("audit_hash", hashlib.sha256(receipt_json.encode("utf-8")).hexdigest())

    with get_db() as db:
        db.execute("""
            INSERT OR REPLACE INTO customer_receipts (id, transaction_id, customer_username, business_id, invoice_number, total_due_usd, receipt_json, created_at_utc, audit_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (rcv_id, tx_id, customer_username, business_id, inv_num, total_due, receipt_json, now_utc, audit_hash))

    return {
        "id": rcv_id,
        "transaction_id": tx_id,
        "customer_username": customer_username,
        "invoice_number": inv_num,
        "created_at_utc": now_utc,
        "audit_hash": audit_hash
    }

def get_customer_receipts(customer_username: str, query: str = None) -> list:
    """Retrieves all archived digital receipts for a customer with optional keyword search."""
    with get_db() as db:
        if query:
            q = f"%{query}%"
            cursor = db.execute("""
                SELECT cr.*, b.name as business_name
                FROM customer_receipts cr
                LEFT JOIN businesses b ON cr.business_id = b.id
                WHERE cr.customer_username = ? AND (cr.invoice_number LIKE ? OR b.name LIKE ? OR cr.receipt_json LIKE ?)
                ORDER BY cr.created_at_utc DESC
            """, (customer_username, q, q, q))
        else:
            cursor = db.execute("""
                SELECT cr.*, b.name as business_name
                FROM customer_receipts cr
                LEFT JOIN businesses b ON cr.business_id = b.id
                WHERE cr.customer_username = ?
                ORDER BY cr.created_at_utc DESC
            """, (customer_username,))

        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["receipt_data"] = json.loads(d.get("receipt_json") or "{}")
            except Exception:
                d["receipt_data"] = {}
            result.append(d)
        return result


# =====================================================================
# STAGE 1 CORE: SEED DEMO DATA & ROLES
# =====================================================================

def seed_stage1_demo_data():
    """Seeds default accounts for all roles, businesses, and initial agricultural/social/security records."""
    now = int(time.time())
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()

    with get_db() as db:
        # Seed Demo Businesses
        businesses_to_seed = [
            ("biz-green-valley", "Green Valley Organic Horticulture", "Horticulture & Fresh Produce", "+263 77 234 5678", "Plot 12, Umguza Valley, Bulawayo", "ZW-8841-HORT", "Green Valley Organic - Farm Fresh Direct", "Sustainably grown with zero synthetic pesticides. Siyabonga!", "USD", "agronomist"),
            ("biz-khumalo-millers", "Khumalo Milling & Grains Co.", "Grain Milling & Animal Feeds", "+263 71 890 1234", "Tsholotsho Grain Silo Depot #2", "ZW-9102-MILL", "Khumalo Millers - Quality Maize & Sorghum", "Fortified roller meal and livestock feeds. Siyabonga kakhulu!", "ZWG", "merchant"),
            ("biz-matopos-dairy", "Matopos Heritage Dairy & Livestock", "Dairy & Livestock Products", "+263 78 555 4321", "Matopos Farm Outpost, Matabeleland South", "ZW-7730-DAIRY", "Matopos Heritage - Pure Artisanal Dairy", "Fresh milk, sour milk (amasi), and cheese. Thank you!", "ZAR", "merchant")
        ]
        for b_id, b_name, b_cat, b_phone, b_addr, b_tax, b_head, b_foot, b_curr, b_owner in businesses_to_seed:
            cursor = db.execute("SELECT id FROM businesses WHERE id = ?", (b_id,))
            if not cursor.fetchone():
                db.execute("""
                    INSERT OR IGNORE INTO businesses (id, name, category, contact_phone, location_address, tax_id, receipt_header, receipt_footer_note, currency_preference, owner_username, created_at_utc, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (b_id, b_name, b_cat, b_phone, b_addr, b_tax, b_head, b_foot, b_curr, b_owner, now_utc))

        # Seed demo users for all 6 roles
        roles = [
            ("admin", "admin"),
            ("agronomist", "agronomist"),
            ("guard", "guard"),
            ("merchant", "merchant"),
            ("customer", "customer"),
            ("guest", "guest")
        ]
        for username, role in roles:
            cursor = db.execute("SELECT id FROM users WHERE username = ?", (username,))
            if not cursor.fetchone():
                salt_hex, hash_hex = hash_password("Password123!")
                db.execute("""
                    INSERT OR IGNORE INTO users (username, password_hash, salt, role, status, created_at, updated_at, must_change_password, pin)
                    VALUES (?, ?, ?, ?, 'active', ?, ?, 0, '1234')
                """, (username, hash_hex, salt_hex, role, now, now))

        # Seed sample planting
        cursor = db.execute("SELECT COUNT(*) as count FROM agri_plantings")
        if cursor.fetchone()["count"] == 0:
            p_id = "plant-demo-1"
            db.execute("""
                INSERT OR IGNORE INTO agri_plantings (id, crop_variety, plot_bed_id, planting_date_utc, seeding_density, target_maturity_date_utc, initial_soil_hydration_pct, status, created_by, created_at_utc, notes, business_id)
                VALUES (?, 'Roma Tomato (Determinate)', 'Bed 4 - North Plot', ?, 4.5, ?, 68.0, 'growing', 'agronomist', ?, 'Drip irrigated with compost top dressing', 'biz-green-valley')
            """, (p_id, now_utc, (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=45)).isoformat(), now_utc))

            # Seed costs for planting
            db.execute("""
                INSERT OR IGNORE INTO agri_production_costs (id, planting_id, cost_seeds_usd, cost_fertilizer_usd, cost_water_usd, cost_labor_usd, cost_pest_usd, cost_packaging_usd, cost_logistics_usd, cost_overhead_usd, total_cost_usd, logged_by, logged_at_utc)
                VALUES ('cost-demo-1', ?, 20.0, 35.0, 25.0, 50.0, 10.0, 15.0, 15.0, 10.0, 180.0, 'agronomist', ?)
            """, (p_id, now_utc))

        # Seed sample visitor
        cursor = db.execute("SELECT COUNT(*) as count FROM security_visitor_logs")
        if cursor.fetchone()["count"] == 0:
            db.execute("""
                INSERT OR IGNORE INTO security_visitor_logs (id, national_id, full_name, time_in_utc, destination_env, purpose, escort_officer, status, notes, logged_by)
                VALUES ('vis-demo-1', '63-198274-B-28', 'Tendai Moyo', ?, 'Crop Silos', 'Bulk Grain Inspection & Quality Assay', 'Officer Sibanda', 'Active', 'Carrying sampling probe', 'guard')
            """, (now_utc,))

        # Seed sample social posts for each of the 4 paradigms
        cursor = db.execute("SELECT COUNT(*) as count FROM social_posts")
        if cursor.fetchone()["count"] == 0:
            # X / Thread
            db.execute("""
                INSERT OR IGNORE INTO social_posts (id, post_type, author, content_text, media_urls_json, tags_json, views_count, tips_usd, tips_zar, tips_zwg, created_at_utc, business_id)
                VALUES ('post-x-1', 'thread', 'agronomist', 'Morning soil hydration at North Bed #4 reached 68% optimal moisture. Tomatoes entering heavy flowering stage!', '[]', '["farming", "tomatoes", "irrigation"]', 42, 1.50, 20.0, 50.0, ?, 'biz-green-valley')
            """, (now_utc,))
            # Instagram / Carousel
            db.execute("""
                INSERT OR IGNORE INTO social_posts (id, post_type, author, content_text, media_urls_json, tags_json, views_count, tips_usd, tips_zar, tips_zwg, created_at_utc, business_id)
                VALUES ('post-ig-1', 'carousel', 'merchant', 'Fresh harvest arriving at the village depot! Roma tomatoes & green cabbages listed with live decay pricing.', '["assets/images/sample_produce_1.png", "assets/images/sample_produce_2.png"]', '["market", "organic", "pos"]', 88, 5.00, 0.0, 100.0, ?, 'biz-green-valley')
            """, (now_utc,))
            # Snapchat / Story
            db.execute("""
                INSERT OR IGNORE INTO social_posts (id, post_type, author, content_text, media_urls_json, tags_json, views_count, tips_usd, tips_zar, tips_zwg, expires_at_utc, created_at_utc, business_id)
                VALUES ('post-snap-1', 'story', 'guard', 'Perimeter Gate inspection clear. Solar backup batteries at 98% charge for nighttime duty.', '[]', '["security", "daily"]', 19, 0.0, 10.0, 0.0, ?, ?, 'biz-green-valley')
            """, ((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)).isoformat(), now_utc))
            # TikTok / Reel
            db.execute("""
                INSERT OR IGNORE INTO social_posts (id, post_type, author, content_text, media_urls_json, tags_json, views_count, tips_usd, tips_zar, tips_zwg, created_at_utc, business_id)
                VALUES ('post-tik-1', 'reel', 'agronomist', 'Quick 30s tutorial on setting up low-pressure gravity drip emitters on sandy loam plots.', '["assets/videos/tutorial_drip.mp4"]', '["tutorial", "microirrigation"]', 145, 10.00, 150.0, 250.0, ?, 'biz-green-valley')
            """, (now_utc,))

        # Seed sample starter voucher
        cursor = db.execute("SELECT COUNT(*) as count FROM vouchers")
        if cursor.fetchone()["count"] == 0:
            vid = "vouch-demo-1"
            exp_utc = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=90)).isoformat()
            sig = compute_voucher_hmac(vid, "biz-green-valley", 50.00, "ZWG", exp_utc)
            db.execute("""
                INSERT OR IGNORE INTO vouchers (vid, business_id, value_amount, currency, equivalent_usd, issued_at_utc, expires_at_utc, issued_by_node_id, signature_hmac, status)
                VALUES (?, 'biz-green-valley', 50.00, 'ZWG', 1.89, ?, ?, 'node-vault-01', ?, 'active')
            """, (vid, now_utc, exp_utc, sig))

        # Seed sample business operator assignments
        operators_to_seed = [
            ("biz-green-valley", "agronomist", "agronomist", ["agriculture", "social", "reports"], "admin"),
            ("biz-green-valley", "merchant", "manager", ["admin", "pos", "inventory", "agriculture", "security", "social", "vouchers", "reports"], "admin"),
            ("biz-green-valley", "guard", "guard", ["security", "social"], "admin"),
            ("biz-khumalo-millers", "merchant", "admin", ["admin", "pos", "inventory", "agriculture", "security", "social", "vouchers", "reports"], "admin"),
            ("biz-matopos-dairy", "merchant", "admin", ["admin", "pos", "inventory", "agriculture", "security", "social", "vouchers", "reports"], "admin")
        ]
        for b_id, u_name, r_name, p_list, g_by in operators_to_seed:
            cursor = db.execute("SELECT id FROM business_operators WHERE business_id = ? AND username = ?", (b_id, u_name))
            if not cursor.fetchone():
                db.execute("""
                    INSERT OR IGNORE INTO business_operators (id, business_id, username, role_in_business, permissions_json, granted_by, created_at_utc, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """, (f"op-{uuid.uuid4().hex[:8]}", b_id, u_name, r_name, json.dumps(p_list), g_by, now_utc))

        # Seed customer and staff wallets with starting multi-currency balances
        wallets_to_seed = [
            ("customer", 50.00, 250.00, 500.00),
            ("merchant", 250.00, 1500.00, 2000.00),
            ("agronomist", 75.00, 400.00, 750.00),
            ("guard", 30.00, 150.00, 300.00),
            ("admin", 500.00, 5000.00, 10000.00),
            ("guest", 10.00, 50.00, 100.00)
        ]
        for u_name, b_usd, b_zar, b_zwg in wallets_to_seed:
            cursor = db.execute("SELECT account_number FROM wallets WHERE username = ?", (u_name,))
            if not cursor.fetchone():
                acc = f"ACC-2026-{uuid.uuid4().hex[:6].upper()}"
                db.execute("""
                    INSERT OR IGNORE INTO wallets (account_number, username, balance_usd, balance_zar, balance_zwg, created_at_utc, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'active')
                """, (acc, u_name, b_usd, b_zar, b_zwg, now_utc))
                
                # Seed initial deposit ledger entry
                sig = hmac.new(VAULT_SECRET_KEY, f"wtx-init-{acc}|{acc}|deposit|{b_usd:.2f}".encode("utf-8"), hashlib.sha256).hexdigest()
                db.execute("""
                    INSERT OR IGNORE INTO wallet_ledger (id, account_number, transaction_type, currency, amount, balance_after, counterparty, reference_id, notes, timestamp_utc, signature_hmac)
                    VALUES (?, ?, 'deposit', 'USD', ?, ?, 'system', 'genesis', 'Initial Account Opening Balance', ?, ?)
                """, (f"wtx-init-{acc}", acc, b_usd, b_usd, now_utc, sig))

        db.commit()




