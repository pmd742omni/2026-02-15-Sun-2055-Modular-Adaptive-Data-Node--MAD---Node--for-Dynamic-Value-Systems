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
import re
from typing import Optional, List, Dict, Any, Tuple
try:
    from .auth_utils import hash_password, encrypt_vault_payload, decrypt_vault_payload, is_payload_encrypted
except ImportError:
    from auth_utils import hash_password, encrypt_vault_payload, decrypt_vault_payload, is_payload_encrypted

DB_PATH = os.environ.get("MADN_DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db"))
LOG_PATH = os.environ.get("MADN_LOG_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "audit_logs.log"))

FORENSIC_MODE = False
VAULT_SECRET_KEY = b"madn-offline-vault-key-secret-2026"

def get_db():
    """Get SQLite database connection with WAL mode, busy_timeout, RAM cache, and Foreign Keys active."""
    conn = sqlite3.connect(DB_PATH, timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA cache_size=-64000;")  # 64MB memory page cache
    conn.execute("PRAGMA temp_store=MEMORY;")  # Temp tables in RAM
    conn.execute("PRAGMA mmap_size=268435456;") # 256MB Memory-Mapped I/O
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


# =====================================================================
# GLOBAL WORLD CURRENCIES & CRYPTOCURRENCY REGISTRY (ISO 4217 & CRYPTOS)
# =====================================================================

GLOBAL_AUTHORITATIVE_CATALOG = [
    # Top Sovereign World Fiat Currencies (ISO 4217)
    {"code": "USD", "name": "United States Dollar", "symbol": "$", "category": "fiat", "country_or_issuer": "United States", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 1.0},
    {"code": "ZAR", "name": "South African Rand", "symbol": "R", "category": "fiat", "country_or_issuer": "South Africa (CMA)", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 18.50},
    {"code": "ZWG", "name": "Zimbabwe Gold (ZiG)", "symbol": "ZiG", "category": "gold_backed", "country_or_issuer": "Zimbabwe (RBZ)", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 26.50},
    {"code": "EUR", "name": "Euro", "symbol": "€", "category": "fiat", "country_or_issuer": "Eurozone", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 0.92},
    {"code": "GBP", "name": "British Pound Sterling", "symbol": "£", "category": "fiat", "country_or_issuer": "United Kingdom", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 0.79},
    {"code": "BWP", "name": "Botswana Pula", "symbol": "P", "category": "fiat", "country_or_issuer": "Botswana", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 13.60},
    {"code": "JPY", "name": "Japanese Yen", "symbol": "¥", "category": "fiat", "country_or_issuer": "Japan", "is_iso4217": 1, "default_decimals": 0, "rate_to_usd": 155.0},
    {"code": "CNY", "name": "Chinese Yuan Renminbi", "symbol": "¥", "category": "fiat", "country_or_issuer": "China", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 7.25},
    {"code": "INR", "name": "Indian Rupee", "symbol": "₹", "category": "fiat", "country_or_issuer": "India", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 83.50},
    {"code": "CAD", "name": "Canadian Dollar", "symbol": "CA$", "category": "fiat", "country_or_issuer": "Canada", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 1.36},
    {"code": "AUD", "name": "Australian Dollar", "symbol": "A$", "category": "fiat", "country_or_issuer": "Australia", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 1.52},
    {"code": "CHF", "name": "Swiss Franc", "symbol": "CHF", "category": "fiat", "country_or_issuer": "Switzerland", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 0.90},
    {"code": "NGN", "name": "Nigerian Naira", "symbol": "₦", "category": "fiat", "country_or_issuer": "Nigeria", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 1500.0},
    {"code": "KES", "name": "Kenyan Shilling", "symbol": "KSh", "category": "fiat", "country_or_issuer": "Kenya", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 130.0},
    {"code": "GHS", "name": "Ghanaian Cedi", "symbol": "GH₵", "category": "fiat", "country_or_issuer": "Ghana", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 14.50},
    {"code": "ZMW", "name": "Zambian Kwacha", "symbol": "ZK", "category": "fiat", "country_or_issuer": "Zambia", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 26.0},
    {"code": "MZN", "name": "Mozambican Metical", "symbol": "MT", "category": "fiat", "country_or_issuer": "Mozambique", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 63.8},
    {"code": "NAD", "name": "Namibian Dollar", "symbol": "N$", "category": "fiat", "country_or_issuer": "Namibia", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 18.5},
    {"code": "SZL", "name": "Eswatini Lilangeni", "symbol": "E", "category": "fiat", "country_or_issuer": "Eswatini", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 18.5},
    {"code": "LSL", "name": "Lesotho Loti", "symbol": "L", "category": "fiat", "country_or_issuer": "Lesotho", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 18.5},
    {"code": "MWK", "name": "Malawian Kwacha", "symbol": "MK", "category": "fiat", "country_or_issuer": "Malawi", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 1735.0},
    {"code": "TZS", "name": "Tanzanian Shilling", "symbol": "TSh", "category": "fiat", "country_or_issuer": "Tanzania", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 2600.0},
    {"code": "UGX", "name": "Ugandan Shilling", "symbol": "USh", "category": "fiat", "country_or_issuer": "Uganda", "is_iso4217": 1, "default_decimals": 0, "rate_to_usd": 3750.0},
    {"code": "RWF", "name": "Rwandan Franc", "symbol": "FRw", "category": "fiat", "country_or_issuer": "Rwanda", "is_iso4217": 1, "default_decimals": 0, "rate_to_usd": 1300.0},
    {"code": "AED", "name": "United Arab Emirates Dirham", "symbol": "د.إ", "category": "fiat", "country_or_issuer": "United Arab Emirates", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 3.67},
    {"code": "SAR", "name": "Saudi Riyal", "symbol": "﷼", "category": "fiat", "country_or_issuer": "Saudi Arabia", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 3.75},
    {"code": "BRL", "name": "Brazilian Real", "symbol": "R$", "category": "fiat", "country_or_issuer": "Brazil", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 5.40},
    {"code": "RUB", "name": "Russian Ruble", "symbol": "₽", "category": "fiat", "country_or_issuer": "Russia", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 90.0},
    {"code": "SGD", "name": "Singapore Dollar", "symbol": "S$", "category": "fiat", "country_or_issuer": "Singapore", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 1.35},
    {"code": "HKD", "name": "Hong Kong Dollar", "symbol": "HK$", "category": "fiat", "country_or_issuer": "Hong Kong", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 7.80},
    {"code": "NZD", "name": "New Zealand Dollar", "symbol": "NZ$", "category": "fiat", "country_or_issuer": "New Zealand", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 1.63},
    {"code": "SEK", "name": "Swedish Krona", "symbol": "kr", "category": "fiat", "country_or_issuer": "Sweden", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 10.40},
    {"code": "NOK", "name": "Norwegian Krone", "symbol": "kr", "category": "fiat", "country_or_issuer": "Norway", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 10.60},
    {"code": "DKK", "name": "Danish Krone", "symbol": "kr", "category": "fiat", "country_or_issuer": "Denmark", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 6.85},
    {"code": "PLN", "name": "Polish Zloty", "symbol": "zł", "category": "fiat", "country_or_issuer": "Poland", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 3.95},
    {"code": "TRY", "name": "Turkish Lira", "symbol": "₺", "category": "fiat", "country_or_issuer": "Turkey", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 33.0},
    {"code": "KRW", "name": "South Korean Won", "symbol": "₩", "category": "fiat", "country_or_issuer": "South Korea", "is_iso4217": 1, "default_decimals": 0, "rate_to_usd": 1360.0},
    {"code": "IDR", "name": "Indonesian Rupiah", "symbol": "Rp", "category": "fiat", "country_or_issuer": "Indonesia", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 16000.0},
    {"code": "MYR", "name": "Malaysian Ringgit", "symbol": "RM", "category": "fiat", "country_or_issuer": "Malaysia", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 4.65},
    {"code": "THB", "name": "Thai Baht", "symbol": "฿", "category": "fiat", "country_or_issuer": "Thailand", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 36.0},
    {"code": "PHP", "name": "Philippine Peso", "symbol": "₱", "category": "fiat", "country_or_issuer": "Philippines", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 58.0},
    {"code": "VND", "name": "Vietnamese Dong", "symbol": "₫", "category": "fiat", "country_or_issuer": "Vietnam", "is_iso4217": 1, "default_decimals": 0, "rate_to_usd": 25000.0},
    {"code": "ILS", "name": "Israeli New Shekel", "symbol": "₪", "category": "fiat", "country_or_issuer": "Israel", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 3.70},
    {"code": "CLP", "name": "Chilean Peso", "symbol": "CLP$", "category": "fiat", "country_or_issuer": "Chile", "is_iso4217": 1, "default_decimals": 0, "rate_to_usd": 920.0},
    {"code": "COP", "name": "Colombian Peso", "symbol": "COL$", "category": "fiat", "country_or_issuer": "Colombia", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 4100.0},
    {"code": "PEN", "name": "Peruvian Sol", "symbol": "S/.", "category": "fiat", "country_or_issuer": "Peru", "is_iso4217": 1, "default_decimals": 2, "rate_to_usd": 3.75},
    {"code": "XAU", "name": "Gold Troy Ounce", "symbol": "Au", "category": "commodity", "country_or_issuer": "International Precious Metals", "is_iso4217": 1, "default_decimals": 4, "rate_to_usd": 0.00041},
    {"code": "XAG", "name": "Silver Troy Ounce", "symbol": "Ag", "category": "commodity", "country_or_issuer": "International Precious Metals", "is_iso4217": 1, "default_decimals": 4, "rate_to_usd": 0.033},
    # Top Cryptocurrencies & Digital Reserve Assets
    {"code": "BTC", "name": "Bitcoin", "symbol": "₿", "category": "crypto", "country_or_issuer": "Bitcoin Network", "is_iso4217": 0, "default_decimals": 8, "rate_to_usd": 0.000015},
    {"code": "ETH", "name": "Ethereum", "symbol": "Ξ", "category": "crypto", "country_or_issuer": "Ethereum Foundation", "is_iso4217": 0, "default_decimals": 18, "rate_to_usd": 0.00038},
    {"code": "SOL", "name": "Solana", "symbol": "◎", "category": "crypto", "country_or_issuer": "Solana Network", "is_iso4217": 0, "default_decimals": 9, "rate_to_usd": 0.0068},
    {"code": "USDT", "name": "Tether USD", "symbol": "₮", "category": "stablecoin", "country_or_issuer": "Tether Operations", "is_iso4217": 0, "default_decimals": 6, "rate_to_usd": 1.00},
    {"code": "USDC", "name": "USD Coin", "symbol": "USDC", "category": "stablecoin", "country_or_issuer": "Circle / Centre", "is_iso4217": 0, "default_decimals": 6, "rate_to_usd": 1.00},
    {"code": "BNB", "name": "BNB Chain Token", "symbol": "BNB", "category": "crypto", "country_or_issuer": "BNB Chain", "is_iso4217": 0, "default_decimals": 18, "rate_to_usd": 0.0017},
    {"code": "XRP", "name": "XRP Ledger", "symbol": "XRP", "category": "crypto", "country_or_issuer": "Ripple Labs", "is_iso4217": 0, "default_decimals": 6, "rate_to_usd": 1.70},
    {"code": "ADA", "name": "Cardano", "symbol": "₳", "category": "crypto", "country_or_issuer": "Cardano Foundation", "is_iso4217": 0, "default_decimals": 6, "rate_to_usd": 2.20},
    {"code": "DOGE", "name": "Dogecoin", "symbol": "Ð", "category": "crypto", "country_or_issuer": "Dogecoin Open Source", "is_iso4217": 0, "default_decimals": 8, "rate_to_usd": 8.0},
    {"code": "TRX", "name": "TRON", "symbol": "TRX", "category": "crypto", "country_or_issuer": "TRON DAO", "is_iso4217": 0, "default_decimals": 6, "rate_to_usd": 7.5},
    {"code": "AVAX", "name": "Avalanche", "symbol": "AVAX", "category": "crypto", "country_or_issuer": "Ava Labs", "is_iso4217": 0, "default_decimals": 18, "rate_to_usd": 0.035},
    {"code": "DOT", "name": "Polkadot", "symbol": "DOT", "category": "crypto", "country_or_issuer": "Web3 Foundation", "is_iso4217": 0, "default_decimals": 10, "rate_to_usd": 0.16},
    {"code": "MATIC", "name": "Polygon (POL)", "symbol": "POL", "category": "crypto", "country_or_issuer": "Polygon Labs", "is_iso4217": 0, "default_decimals": 18, "rate_to_usd": 2.0},
    {"code": "LINK", "name": "Chainlink", "symbol": "LINK", "category": "crypto", "country_or_issuer": "Chainlink Labs", "is_iso4217": 0, "default_decimals": 18, "rate_to_usd": 0.08},
    {"code": "DAI", "name": "Dai Stablecoin", "symbol": "DAI", "category": "stablecoin", "country_or_issuer": "MakerDAO / Sky", "is_iso4217": 0, "default_decimals": 18, "rate_to_usd": 1.00},
    {"code": "LTC", "name": "Litecoin", "symbol": "Ł", "category": "crypto", "country_or_issuer": "Litecoin Foundation", "is_iso4217": 0, "default_decimals": 8, "rate_to_usd": 0.013},
    {"code": "TON", "name": "The Open Network", "symbol": "TON", "category": "crypto", "country_or_issuer": "TON Foundation", "is_iso4217": 0, "default_decimals": 9, "rate_to_usd": 0.18}
]

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
        full_name TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        email TEXT DEFAULT '',
        avatar_url TEXT DEFAULT '',
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
    
    try:
        db.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT DEFAULT '';")
    except Exception:
        pass
    
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
        cost_price_usd REAL NOT NULL DEFAULT 0.0,
        low_stock_threshold REAL NOT NULL DEFAULT 5.0,
        barcode TEXT DEFAULT '',
        category TEXT DEFAULT '',
        subcategory TEXT DEFAULT '',
        brand TEXT DEFAULT '',
        description TEXT DEFAULT '',
        specifications TEXT DEFAULT '{}',
        image_url TEXT DEFAULT '',
        wholesale_price_usd REAL DEFAULT 0.0,
        wholesale_min_qty REAL DEFAULT 0.0,
        extra_attributes TEXT DEFAULT '{}',
        business_id TEXT DEFAULT 'biz-green-valley'
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
    CREATE TABLE IF NOT EXISTS agri_fields (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        code TEXT,
        area_size REAL DEFAULT 1.0,
        area_unit TEXT DEFAULT 'hectares',
        soil_type TEXT DEFAULT 'Loamy',
        irrigation_type TEXT DEFAULT 'Drip Irrigation',
        status TEXT DEFAULT 'active',
        notes TEXT,
        created_by TEXT NOT NULL,
        created_at_utc TEXT NOT NULL
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS agri_plantings (
        id TEXT PRIMARY KEY,
        crop_variety TEXT NOT NULL,
        plot_bed_id TEXT NOT NULL,
        field_id TEXT DEFAULT '',
        field_name TEXT DEFAULT '',
        area_utilized REAL DEFAULT 1.0,
        area_unit TEXT DEFAULT 'hectares',
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
        tagline TEXT DEFAULT '',
        description TEXT DEFAULT '',
        logo_url TEXT DEFAULT '',
        banner_url TEXT DEFAULT '',
        contact_phone TEXT DEFAULT '',
        contact_email TEXT DEFAULT '',
        location_address TEXT DEFAULT '',
        tax_id TEXT DEFAULT '',
        website_url TEXT DEFAULT '',
        operating_hours TEXT DEFAULT '',
        return_policy TEXT DEFAULT '',
        bank_account_number TEXT DEFAULT '',
        receipt_header TEXT DEFAULT '',
        receipt_footer_note TEXT DEFAULT '',
        currency_preference TEXT DEFAULT 'USD',
        owner_username TEXT,
        extra_attributes TEXT DEFAULT '{}',
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

    # Customer & Business Digital Bank Accounts & Multi-Currency Ledger
    db.execute("""
    CREATE TABLE IF NOT EXISTS wallets (
        account_number TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        balance_usd REAL DEFAULT 0.0,
        balance_zar REAL DEFAULT 0.0,
        balance_zwg REAL DEFAULT 0.0,
        created_at_utc TEXT NOT NULL,
        status TEXT DEFAULT 'active',
        account_type TEXT DEFAULT 'personal',
        business_id TEXT DEFAULT '',
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

    # Vault Node Inter-Cluster Communication Key Registry
    db.execute("""
    CREATE TABLE IF NOT EXISTS node_communication_keys (
        node_id TEXT PRIMARY KEY,
        node_type TEXT NOT NULL,
        ip_address TEXT NOT NULL,
        port INTEGER NOT NULL,
        hmac_secret_key TEXT NOT NULL,
        public_key TEXT,
        status TEXT DEFAULT 'active',
        created_at_utc TEXT NOT NULL,
        last_rotated_utc TEXT NOT NULL,
        notes TEXT
    );
    """)

    # Dynamic Extensible Currencies & Virtual Tokens Registry
    db.execute("""
    CREATE TABLE IF NOT EXISTS currencies (
        code TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        symbol TEXT NOT NULL,
        exchange_rate_to_usd REAL NOT NULL,
        currency_type TEXT DEFAULT 'fiat',
        is_default INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at_utc TEXT NOT NULL,
        updated_at_utc TEXT NOT NULL
    );
    """)

    # Global World Currency & Cryptocurrency Catalog (ISO 4217 & Major Cryptos)
    db.execute("""
    CREATE TABLE IF NOT EXISTS global_currency_catalog (
        code TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        symbol TEXT NOT NULL,
        category TEXT NOT NULL,
        country_or_issuer TEXT,
        is_iso4217 INTEGER DEFAULT 0,
        default_decimals INTEGER DEFAULT 2,
        rate_to_usd REAL DEFAULT 1.0,
        last_updated_utc TEXT NOT NULL
    );
    """)

    # Dynamic Multi-Currency Wallet Balances
    db.execute("""
    CREATE TABLE IF NOT EXISTS wallet_balances (
        account_number TEXT NOT NULL,
        currency TEXT NOT NULL,
        balance REAL DEFAULT 0.0,
        updated_at_utc TEXT NOT NULL,
        PRIMARY KEY (account_number, currency),
        FOREIGN KEY (account_number) REFERENCES wallets(account_number),
        FOREIGN KEY (currency) REFERENCES currencies(code)
    );
    """)

    # 2. Performance-Critical B-Tree Indexes for Instant Sub-Millisecond Lookups
    db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token_hash ON sessions(token_hash);")
    db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);")
    db.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")
    db.execute("CREATE INDEX IF NOT EXISTS idx_inventory_biz_sku ON inventory(business_id, sku);")
    db.execute("CREATE INDEX IF NOT EXISTS idx_transactions_time_op ON transactions(timestamp, operator_username);")
    db.execute("CREATE INDEX IF NOT EXISTS idx_transaction_items_tx ON transaction_items(transaction_id);")
    db.execute("CREATE INDEX IF NOT EXISTS idx_transaction_tenders_tx ON transaction_tenders(transaction_id);")
    db.execute("CREATE INDEX IF NOT EXISTS idx_wallets_user ON wallets(username);")
    db.execute("CREATE INDEX IF NOT EXISTS idx_wallets_biz ON wallets(business_id);")
    db.execute("CREATE INDEX IF NOT EXISTS idx_wallet_ledger_acc_time ON wallet_ledger(account_number, timestamp_utc);")
    db.execute("CREATE INDEX IF NOT EXISTS idx_customer_receipts_user ON customer_receipts(customer_username, created_at_utc);")
    db.execute("CREATE INDEX IF NOT EXISTS idx_wallet_balances_acc ON wallet_balances(account_number);")
    db.execute("CREATE INDEX IF NOT EXISTS idx_vouchers_biz_status ON vouchers(business_id, status);")
    db.execute("CREATE INDEX IF NOT EXISTS idx_fields_op ON agri_fields(created_by);")
    db.execute("CREATE INDEX IF NOT EXISTS idx_plantings_field ON agri_plantings(field_id);")
    db.execute("CREATE INDEX IF NOT EXISTS idx_harvests_planting ON agri_harvests(planting_id);")
    db.execute("CREATE INDEX IF NOT EXISTS idx_visitors_status ON security_visitor_logs(status);")
    db.execute("CREATE INDEX IF NOT EXISTS idx_tracked_devices_ip ON tracked_devices(ip_address);")
    db.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);")
    db.execute("CREATE INDEX IF NOT EXISTS idx_currencies_code ON currencies(code);")

    db.commit()

    # Seed Default Currencies if not present
    now_utc_init = datetime.datetime.now(datetime.timezone.utc).isoformat()
    default_currs = [
        ("USD", "United States Dollar", "$", 1.00, "fiat", 1),
        ("ZAR", "South African Rand", "R", 18.50, "fiat", 0),
        ("ZWG", "Zimbabwe Gold (ZiG)", "ZiG", 26.50, "gold_backed", 0)
    ]
    for c_code, c_name, c_sym, c_rate, c_type, c_def in default_currs:
        db.execute("""
            INSERT OR IGNORE INTO currencies (code, name, symbol, exchange_rate_to_usd, currency_type, is_default, is_active, created_at_utc, updated_at_utc)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
        """, (c_code, c_name, c_sym, c_rate, c_type, c_def, now_utc_init, now_utc_init))
    
    # Ensure correct name and symbol for ZWG if already in database
    db.execute("""
        UPDATE currencies 
        SET name = 'Zimbabwe Gold (ZiG)', symbol = 'ZiG', currency_type = 'gold_backed' 
        WHERE code = 'ZWG'
    """)
    db.commit()


    # Seed Authoritative Global Currencies & Cryptos Catalog
    for item in GLOBAL_AUTHORITATIVE_CATALOG:
        db.execute("""
            INSERT OR IGNORE INTO global_currency_catalog (code, name, symbol, category, country_or_issuer, is_iso4217, default_decimals, rate_to_usd, last_updated_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (item["code"], item["name"], item["symbol"], item["category"], item.get("country_or_issuer", ""), item.get("is_iso4217", 0), item.get("default_decimals", 2), item.get("rate_to_usd", 1.0), now_utc_init))

    # Schema Migrations: add profile columns to users if they don't exist
    cursor = db.execute("PRAGMA table_info(users)")
    user_cols = [row["name"] for row in cursor.fetchall()]
    for col, col_type in [("full_name", "TEXT DEFAULT ''"), ("phone", "TEXT DEFAULT ''"), ("email", "TEXT DEFAULT ''"), ("pin", "TEXT DEFAULT '1234'")]:
        if col not in user_cols:
            try:
                db.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type};")
                db.commit()
            except sqlite3.OperationalError:
                pass

    # PRAGMA Migration: add modular product columns to inventory
    cursor = db.execute("PRAGMA table_info(inventory)")
    cols = [row["name"] for row in cursor.fetchall()]
    for col_name, col_def in [
        ("cost_price_usd", "REAL DEFAULT 0.0"),
        ("barcode", "TEXT DEFAULT ''"),
        ("category", "TEXT DEFAULT ''"),
        ("subcategory", "TEXT DEFAULT ''"),
        ("brand", "TEXT DEFAULT ''"),
        ("description", "TEXT DEFAULT ''"),
        ("specifications", "TEXT DEFAULT '{}'"),
        ("image_url", "TEXT DEFAULT ''"),
        ("wholesale_price_usd", "REAL DEFAULT 0.0"),
        ("wholesale_min_qty", "REAL DEFAULT 0.0"),
        ("extra_attributes", "TEXT DEFAULT '{}'"),
        ("business_id", "TEXT DEFAULT 'biz-green-valley'")
    ]:
        if col_name not in cols:
            try:
                db.execute(f"ALTER TABLE inventory ADD COLUMN {col_name} {col_def};")
                db.commit()
            except sqlite3.OperationalError:
                pass

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

    # PRAGMA Migrations: modular columns for businesses
    cursor = db.execute("PRAGMA table_info(businesses)")
    biz_cols = [row["name"] for row in cursor.fetchall()]
    for col_name, col_def in [
        ("tagline", "TEXT DEFAULT ''"),
        ("description", "TEXT DEFAULT ''"),
        ("logo_url", "TEXT DEFAULT ''"),
        ("banner_url", "TEXT DEFAULT ''"),
        ("contact_email", "TEXT DEFAULT ''"),
        ("website_url", "TEXT DEFAULT ''"),
        ("operating_hours", "TEXT DEFAULT ''"),
        ("return_policy", "TEXT DEFAULT ''"),
        ("bank_account_number", "TEXT DEFAULT ''"),
        ("extra_attributes", "TEXT DEFAULT '{}'")
    ]:
        if col_name not in biz_cols:
            try:
                db.execute(f"ALTER TABLE businesses ADD COLUMN {col_name} {col_def};")
                db.commit()
            except sqlite3.OperationalError:
                pass

    # PRAGMA Migrations: account_type and business_id for wallets
    cursor = db.execute("PRAGMA table_info(wallets)")
    wallet_cols = [row["name"] for row in cursor.fetchall()]
    for col_name, col_def in [
        ("account_type", "TEXT DEFAULT 'personal'"),
        ("business_id", "TEXT DEFAULT ''")
    ]:
        if col_name not in wallet_cols:
            try:
                db.execute(f"ALTER TABLE wallets ADD COLUMN {col_name} {col_def};")
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

    # Zero-seed inventory initialization: Real items are added by operators or synced from harvests
    # No artificial dummy products seeded into store

    # Zero-seed policy: All map obstacles, security nodes, rules, and store products
    # are strictly operator-managed and created dynamically without artificial dummy entries.
    
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
            # Standard genesis default password
            admin_pw = "Password123!"
            password_method = "default genesis standard"
        
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

def generate_system_sku(name: str, category: str = "") -> str:
    """Systematically automatically assigns an internal tracking SKU."""
    clean_name = re.sub(r'[^A-Za-z0-9]', '', name).upper()
    prefix = clean_name[:4] if len(clean_name) >= 4 else (clean_name + "PROD")[:4]
    cat_tag = ""
    if category:
        clean_cat = re.sub(r'[^A-Za-z0-9]', '', category).upper()
        if clean_cat:
            cat_tag = f"-{clean_cat[:3]}"
    rand_suffix = uuid.uuid4().hex[:4].upper()
    return f"{prefix}{cat_tag}-{rand_suffix}"

def add_inventory_item(
    name: str, 
    sku: str, 
    quantity: float, 
    unit: str, 
    price_usd: float, 
    threshold: float, 
    actor: str, 
    cost_price_usd: float = 0.0, 
    business_id: str = "biz-default",
    barcode: str = "",
    category: str = "",
    subcategory: str = "",
    brand: str = "",
    description: str = "",
    specifications: any = None,
    image_url: str = "",
    wholesale_price_usd: float = 0.0,
    wholesale_min_qty: float = 0.0,
    extra_attributes: any = None
) -> str:
    db = get_db()
    try:
        item_id = str(uuid.uuid4())
        cost_price = float(cost_price_usd or (price_usd * 0.6))
        
        # Resolve and validate business association
        target_biz_id = str(business_id or '').strip()
        if target_biz_id and target_biz_id != "biz-default":
            cursor_biz = db.execute("SELECT id FROM businesses WHERE id = ? AND is_active = 1", (target_biz_id,))
            if not cursor_biz.fetchone():
                raise ValueError(f"Specified business '{target_biz_id}' does not exist.")
        else:
            cursor_any = db.execute("SELECT id FROM businesses WHERE is_active = 1 ORDER BY created_at_utc ASC LIMIT 1")
            first_biz = cursor_any.fetchone()
            if not first_biz:
                raise ValueError("Store setup required: No active business/store found. Please register a business before adding inventory.")
            target_biz_id = first_biz["id"]
        business_id = target_biz_id

        # Systematically auto-assign SKU if not provided
        if not sku or not sku.strip():
            sku = generate_system_sku(name, category)
        else:
            sku = sku.strip()

        specs_str = json.dumps(specifications) if isinstance(specifications, (dict, list)) else str(specifications or "{}")
        extras_str = json.dumps(extra_attributes) if isinstance(extra_attributes, (dict, list)) else str(extra_attributes or "{}")

        db.execute("""
            INSERT INTO inventory (
                id, name, sku, quantity, unit, price_usd, cost_price_usd, low_stock_threshold,
                barcode, category, subcategory, brand, description, specifications, image_url,
                wholesale_price_usd, wholesale_min_qty, extra_attributes, business_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item_id, name, sku, float(quantity), str(unit or 'pcs'), float(price_usd), float(cost_price), float(threshold or 5.0),
            str(barcode or ''), str(category or ''), str(subcategory or ''), str(brand or ''), str(description or ''),
            specs_str, str(image_url or ''), float(wholesale_price_usd or 0.0), float(wholesale_min_qty or 0.0),
            extras_str, str(business_id)
        ))
        db.commit()
        write_audit_log(actor, "ADD_INVENTORY", f"Added item '{name}' (SKU: {sku}) with initial quantity {quantity} {unit}")
        
        # Sync immediately with connected Data Node
        sync_record_to_data_nodes("inventory", item_id, {
            "id": item_id,
            "name": name,
            "sku": sku,
            "quantity": float(quantity),
            "unit": str(unit or 'pcs'),
            "price_usd": float(price_usd),
            "cost_price_usd": float(cost_price),
            "low_stock_threshold": float(threshold or 5.0),
            "barcode": str(barcode or ''),
            "category": str(category or ''),
            "subcategory": str(subcategory or ''),
            "brand": str(brand or ''),
            "description": str(description or ''),
            "specifications": specifications if isinstance(specifications, dict) else {},
            "image_url": str(image_url or ''),
            "wholesale_price_usd": float(wholesale_price_usd or 0.0),
            "wholesale_min_qty": float(wholesale_min_qty or 0.0),
            "business_id": str(business_id or 'biz-default'),
            "added_by": actor
        })
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
            
            acc_num = w_row["account_number"]
            # Check dynamic wallet balance
            bal_cursor = db.execute("SELECT balance FROM wallet_balances WHERE account_number = ? AND currency = 'USD'", (acc_num,))
            bal_row = bal_cursor.fetchone()
            current_bal = bal_row["balance"] if bal_row else w_row["balance_usd"]

            if current_bal < total_due:
                db.rollback()
                db.close()
                raise ValueError(f"Insufficient wallet balance. Available: ${current_bal:.2f} USD, Required: ${total_due:.2f} USD")
            
            new_bal = current_bal - total_due
            now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()

            db.execute("UPDATE wallets SET balance_usd = ? WHERE account_number = ?", (new_bal, acc_num))
            db.execute("""
                INSERT INTO wallet_balances (account_number, currency, balance, updated_at_utc)
                VALUES (?, 'USD', ?, ?)
                ON CONFLICT(account_number, currency) DO UPDATE SET balance = ?, updated_at_utc = ?
            """, (acc_num, new_bal, now_utc, new_bal, now_utc))
            
            # Record wallet ledger debit
            wtx_id = f"wtx-pos-{uuid.uuid4().hex[:8]}"
            sig = hmac.new(VAULT_SECRET_KEY, f"{wtx_id}|{acc_num}|pos_payment|{total_due:.2f}|{new_bal:.2f}".encode("utf-8"), hashlib.sha256).hexdigest()
            db.execute("""
                INSERT INTO wallet_ledger (id, account_number, transaction_type, currency, amount, balance_after, counterparty, reference_id, notes, timestamp_utc, signature_hmac)
                VALUES (?, ?, 'pos_payment', 'USD', ?, ?, ?, ?, 'POS Checkout Payment', ?, ?)
            """, (wtx_id, acc_num, -total_due, new_bal, business_id, client_req_id, now_utc, sig))
                
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

        # 5b. Route sales revenue to respective business banking accounts
        biz_rev_map = {}
        for item in items:
            inv_id = item["inventory_id"]
            qty = float(item["quantity"])
            price_at_sale = float(item["price_usd_at_sale"])
            item_rev = qty * price_at_sale

            cursor_b = db.execute("SELECT business_id FROM inventory WHERE id = ?", (inv_id,))
            b_row = cursor_b.fetchone()
            item_biz_id = b_row["business_id"] if b_row and b_row["business_id"] else business_id
            biz_rev_map[item_biz_id] = biz_rev_map.get(item_biz_id, 0.0) + item_rev

        for b_id, b_rev in biz_rev_map.items():
            cursor_acc = db.execute("SELECT account_number FROM wallets WHERE business_id = ? AND account_type = 'business'", (b_id,))
            acc_row = cursor_acc.fetchone()
            if acc_row:
                b_acc = acc_row["account_number"]
                bal_cur = db.execute("SELECT balance FROM wallet_balances WHERE account_number = ? AND currency = 'USD'", (b_acc,))
                b_bal_row = bal_cur.fetchone()
                b_curr_bal = b_bal_row["balance"] if b_bal_row else 0.0
                b_new_bal = b_curr_bal + b_rev

                db.execute("UPDATE wallets SET balance_usd = ? WHERE account_number = ?", (b_new_bal, b_acc))
                db.execute("""
                    INSERT INTO wallet_balances (account_number, currency, balance, updated_at_utc)
                    VALUES (?, 'USD', ?, ?)
                    ON CONFLICT(account_number, currency) DO UPDATE SET balance = ?, updated_at_utc = ?
                """, (b_acc, b_new_bal, now_utc, b_new_bal, now_utc))

                wtx_id = f"wtx-pos-{uuid.uuid4().hex[:8]}"
                sig = hmac.new(VAULT_SECRET_KEY, f"{wtx_id}|{b_acc}|pos_sale|{b_rev:.2f}|{b_new_bal:.2f}".encode("utf-8"), hashlib.sha256).hexdigest()
                db.execute("""
                    INSERT INTO wallet_ledger (id, account_number, transaction_type, currency, amount, balance_after, counterparty, reference_id, notes, timestamp_utc, signature_hmac)
                    VALUES (?, ?, 'pos_sale', 'USD', ?, ?, ?, ?, 'POS Checkout Revenue', ?, ?)
                """, (wtx_id, b_acc, b_rev, b_new_bal, operator_username, tx_id, now_utc, sig))

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
            
            # If Advisory & Spoilage warning, spawn Harvest Work Order + Cross-Subsystem Spoilage Flash Sale
            if rule["action_type"] == "advisory":
                c = db.execute("SELECT id FROM harvest_orders WHERE rule_id = ? AND status != 'pos_listed'", (rule["id"],))
                if not c.fetchone():
                    h_id = str(uuid.uuid4())
                    spoilage_cutoff = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)).isoformat()
                    db.execute("""
                        INSERT INTO harvest_orders (id, rule_id, crop_type, status, pos_sku, spoilage_deadline_utc, last_modified_utc)
                        VALUES (?, ?, ?, 'triggered', 'CABBAGE-CASE', ?, ?)
                    """, (h_id, rule["id"], rule["crop_type"], spoilage_cutoff, now_utc))
                    
                    # Auto-spawn Cross-Subsystem Spoilage Flash Sale multiplier in POS!
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


# --- IN-MEMORY SECURITY & DEVICE CACHE ---
_BLOCKED_IPS_CACHE = set()
_BLOCKED_IPS_LAST_FETCH = 0.0
_DEVICE_TRACK_CACHE = {}  # ip -> last_updated_ts


def track_device_activity(ip_address, user_agent, username="anonymous"):
    if not ip_address:
        return
    global _DEVICE_TRACK_CACHE
    now_ts = int(time.time())
    last_tracked = _DEVICE_TRACK_CACHE.get(ip_address, 0)
    
    # Throttle DB updates to once per 60 seconds per IP
    if now_ts - last_tracked < 60:
        return
        
    _DEVICE_TRACK_CACHE[ip_address] = now_ts
    device_type = classify_user_agent(user_agent)
    
    try:
        db = get_db()
        cursor = db.execute("SELECT first_seen FROM tracked_devices WHERE ip_address = ?", (ip_address,))
        row = cursor.fetchone()
        
        if row:
            db.execute("""
                UPDATE tracked_devices 
                SET user_agent = ?, device_type = ?, last_seen = ?, last_username = ? 
                WHERE ip_address = ?
            """, (user_agent, device_type, now_ts, username, ip_address))
        else:
            db.execute("""
                INSERT INTO tracked_devices (ip_address, user_agent, device_type, first_seen, last_seen, last_username)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (ip_address, user_agent, device_type, now_ts, now_ts, username))
        db.commit()
        db.close()
    except Exception as e:
        print(f"[DEVICE TRACKING WARNING] Non-blocking device track warning: {e}")


def is_device_blocked(ip_address):
    if not ip_address:
        return False
    global _BLOCKED_IPS_CACHE, _BLOCKED_IPS_LAST_FETCH
    now = time.time()
    if now - _BLOCKED_IPS_LAST_FETCH > 15.0:
        try:
            db = get_db()
            cursor = db.execute("SELECT ip_address FROM blocked_devices")
            _BLOCKED_IPS_CACHE = {r["ip_address"] for r in cursor.fetchall()}
            _BLOCKED_IPS_LAST_FETCH = now
            db.close()
        except Exception:
            pass
    return ip_address in _BLOCKED_IPS_CACHE


def block_device(ip_address, admin_user, reason="Blocked by System Administrator"):
    global _BLOCKED_IPS_LAST_FETCH
    db = get_db()
    now = int(time.time())
    db.execute("""
        INSERT OR REPLACE INTO blocked_devices (ip_address, blocked_by, blocked_at, reason)
        VALUES (?, ?, ?, ?)
    """, (ip_address, admin_user, now, reason))
    
    db.execute("DELETE FROM sessions WHERE ip_subnet = ?", (ip_address,))
    db.commit()
    db.close()
    _BLOCKED_IPS_LAST_FETCH = 0.0  # Invalidate cache
    write_audit_log(admin_user, "BLOCK_DEVICE", f"Blocked device IP '{ip_address}'. Reason: {reason}")


def unblock_device(ip_address, admin_user):
    global _BLOCKED_IPS_LAST_FETCH
    db = get_db()
    db.execute("DELETE FROM blocked_devices WHERE ip_address = ?", (ip_address,))
    db.commit()
    db.close()
    _BLOCKED_IPS_LAST_FETCH = 0.0  # Invalidate cache
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
# STAGE 1 CORE: AGRICULTURE CRUD & FIELD MANAGEMENT
# =====================================================================

def create_field(name: str, code: str = "", area_size: float = 1.0, area_unit: str = "hectares", soil_type: str = "Loamy", irrigation_type: str = "Drip Irrigation", notes: str = "", created_by: str = "operator") -> dict:
    field_id = f"fld-{uuid.uuid4().hex[:8]}"
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    clean_code = code.strip() if code and code.strip() else f"FLD-{field_id[4:8].upper()}"
    with get_db() as db:
        db.execute("""
            INSERT INTO agri_fields (id, name, code, area_size, area_unit, soil_type, irrigation_type, status, notes, created_by, created_at_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
        """, (field_id, name, clean_code, float(area_size or 1.0), area_unit or "hectares", soil_type or "Loamy", irrigation_type or "Drip Irrigation", notes or "", created_by, now_utc))
        db.commit()
    
    field_data = {
        "id": field_id,
        "name": name,
        "code": clean_code,
        "area_size": float(area_size or 1.0),
        "area_unit": area_unit or "hectares",
        "soil_type": soil_type or "Loamy",
        "irrigation_type": irrigation_type or "Drip Irrigation",
        "status": "active",
        "notes": notes or "",
        "created_by": created_by,
        "created_at_utc": now_utc
    }
    sync_record_to_data_nodes("agri_fields", field_id, field_data)
    return field_data


def list_fields() -> list:
    with get_db() as db:
        cursor = db.execute("SELECT * FROM agri_fields ORDER BY created_at_utc DESC")
        rows = [dict(r) for r in cursor.fetchall()]
    return rows


def delete_field(field_id: str) -> bool:
    with get_db() as db:
        cursor = db.execute("DELETE FROM agri_fields WHERE id = ?", (field_id,))
        db.commit()
        return cursor.rowcount > 0


def create_planting(crop_variety: str, plot_bed_id: str = "", planting_date_utc: str = "", seeding_density: float = 0.0, target_maturity_date_utc: str = "", initial_soil_hydration_pct: float = 0.0, created_by: str = "operator", notes: str = "", field_id: str = "", field_name: str = "", area_utilized: float = 1.0, area_unit: str = "hectares") -> dict:
    planting_id = f"plant-{uuid.uuid4().hex[:8]}"
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if not planting_date_utc:
        planting_date_utc = now_utc

    # Resolve field name if field_id is provided
    resolved_field_name = field_name or plot_bed_id
    if field_id and not field_name:
        with get_db() as db:
            cursor = db.execute("SELECT name FROM agri_fields WHERE id = ?", (field_id,))
            row = cursor.fetchone()
            if row:
                resolved_field_name = row["name"]

    resolved_plot_bed_id = plot_bed_id or resolved_field_name or "Field-Plot"

    with get_db() as db:
        db.execute("""
            INSERT INTO agri_plantings (id, crop_variety, plot_bed_id, field_id, field_name, area_utilized, area_unit, planting_date_utc, seeding_density, target_maturity_date_utc, initial_soil_hydration_pct, status, created_by, created_at_utc, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'growing', ?, ?, ?)
        """, (planting_id, crop_variety, resolved_plot_bed_id, field_id or "", resolved_field_name, float(area_utilized or 1.0), area_unit or "hectares", planting_date_utc, float(seeding_density or 0.0), target_maturity_date_utc or "", float(initial_soil_hydration_pct or 0.0), created_by, now_utc, notes or ""))
        db.commit()
    
    planting_data = {
        "id": planting_id,
        "crop_variety": crop_variety,
        "plot_bed_id": resolved_plot_bed_id,
        "field_id": field_id,
        "field_name": resolved_field_name,
        "area_utilized": float(area_utilized or 1.0),
        "area_unit": area_unit or "hectares",
        "planting_date_utc": planting_date_utc,
        "seeding_density": float(seeding_density or 0.0),
        "target_maturity_date_utc": target_maturity_date_utc,
        "initial_soil_hydration_pct": float(initial_soil_hydration_pct or 0.0),
        "status": "growing",
        "created_by": created_by,
        "created_at_utc": now_utc,
        "notes": notes or ""
    }
    sync_record_to_data_nodes("agri_plantings", planting_id, planting_data)
    return planting_data


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
    
    cost_data = {
        "id": cost_id,
        "planting_id": planting_id,
        "costs": costs,
        "total_cost_usd": total,
        "logged_by": logged_by,
        "logged_at_utc": now_utc
    }
    sync_record_to_data_nodes("agri_production_costs", cost_id, cost_data)
    return {"id": cost_id, "planting_id": planting_id, "total_cost_usd": total}


def get_production_costs(planting_id: str) -> list:
    with get_db() as db:
        cursor = db.execute("SELECT * FROM agri_production_costs WHERE planting_id = ? ORDER BY logged_at_utc DESC", (planting_id,))
        rows = [dict(r) for r in cursor.fetchall()]
    return rows


def log_harvest_and_sync_inventory(planting_id: str, crop_name: str, harvest_date_utc: str, mass_harvest_kg: float, quality_grade: str, storage_location: str, mass_self_kg: float, target_markup_pct: float, shelf_life_half_life_days: float, logged_by: str) -> dict:
    """
    Logs harvest, aggregates planting costs, automatically derives P_cost & P_base,
    and inserts commercial batch into POS inventory, replicating to Data Nodes.
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
            cursor_b = db.execute("SELECT id FROM businesses WHERE is_active = 1 LIMIT 1")
            b_row = cursor_b.fetchone()
            biz_id = b_row["id"] if b_row else "biz-green-valley"

            inv_id = str(uuid.uuid4())
            sku = f"{crop_name.upper().replace(' ', '-')[:8]}-{uuid.uuid4().hex[:4].upper()}"
            db.execute("""
                INSERT INTO inventory (id, name, sku, quantity, unit, price_usd, cost_price_usd, low_stock_threshold, business_id)
                VALUES (?, ?, ?, ?, 'kg', ?, ?, 5.0, ?)
            """, (inv_id, item_name, sku, mass_comm, base_price, cost_floor, biz_id))

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

    harvest_data = {
        "harvest_id": harvest_id,
        "planting_id": planting_id,
        "crop_name": crop_name,
        "mass_harvest_kg": mass_harvest_kg,
        "mass_self_kg": mass_self_kg,
        "mass_comm_kg": mass_comm,
        "wholesale_cost_floor_usd": cost_floor,
        "base_price_usd": base_price,
        "inventory_item_id": inv_id,
        "harvest_date_utc": harvest_date_utc
    }
    sync_record_to_data_nodes("agri_harvests", harvest_id, harvest_data)
    sync_record_to_data_nodes("inventory", inv_id, {
        "id": inv_id,
        "name": item_name,
        "quantity": mass_comm,
        "unit": "kg",
        "price_usd": base_price,
        "cost_price_usd": cost_floor
    })

    return harvest_data


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
    query = """
        SELECT p.*, u.full_name as author_full_name, u.avatar_url as author_avatar
        FROM social_posts p
        LEFT JOIN users u ON p.author = u.username
        WHERE 1=1
    """
    params = []
    if post_type:
        query += " AND p.post_type = ?"
        params.append(post_type)
    if not include_expired:
        query += " AND (p.expires_at_utc IS NULL OR p.expires_at_utc > ?)"
        params.append(now_utc)
    query += " ORDER BY p.created_at_utc DESC"
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
        cursor = db.execute("""
            SELECT c.*, u.full_name as author_full_name, u.avatar_url as author_avatar
            FROM social_comments c
            LEFT JOIN users u ON c.author = u.username
            WHERE c.post_id = ?
            ORDER BY c.created_at_utc ASC
        """, (post_id,))
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


def create_business(
    name: str, 
    category: str = "General", 
    tagline: str = "",
    description: str = "",
    logo_url: str = "",
    banner_url: str = "",
    contact_phone: str = "", 
    contact_email: str = "",
    location_address: str = "", 
    tax_id: str = "", 
    website_url: str = "",
    operating_hours: str = "",
    return_policy: str = "",
    receipt_header: str = "", 
    receipt_footer_note: str = "", 
    currency_preference: str = "USD", 
    owner_username: str = "admin",
    extra_attributes: any = None
) -> dict:
    """Creates a new business entity for multi-tenant enterprise operations and provisions dedicated banking accounts."""
    biz_id = f"biz-{uuid.uuid4().hex[:8]}"
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    bank_account_number = f"BIZ-ACC-{biz_id[4:].upper()}"
    if not receipt_header:
        receipt_header = f"{name} Store"
    if not receipt_footer_note:
        receipt_footer_note = "Thank you for supporting our business!"
    
    extras_str = json.dumps(extra_attributes) if isinstance(extra_attributes, (dict, list)) else str(extra_attributes or "{}")

    with get_db() as db:
        db.execute("""
            INSERT INTO businesses (
                id, name, category, tagline, description, logo_url, banner_url,
                contact_phone, contact_email, location_address, tax_id, website_url,
                operating_hours, return_policy, bank_account_number, receipt_header,
                receipt_footer_note, currency_preference, owner_username, extra_attributes,
                created_at_utc, is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            biz_id, name, category or "General", tagline or "", description or "", logo_url or "", banner_url or "",
            contact_phone or "", contact_email or "", location_address or "", tax_id or "", website_url or "",
            operating_hours or "", return_policy or "", bank_account_number, receipt_header,
            receipt_footer_note, currency_preference or "USD", owner_username, extras_str,
            now_utc
        ))

        # Provision dedicated business wallet / banking account
        db.execute("""
            INSERT OR IGNORE INTO wallets (account_number, username, balance_usd, balance_zar, balance_zwg, created_at_utc, status, account_type, business_id)
            VALUES (?, ?, 0.0, 0.0, 0.0, ?, 'active', 'business', ?)
        """, (bank_account_number, owner_username, now_utc, biz_id))

        # Initialize wallet_balances for all active currencies
        curr_cursor = db.execute("SELECT code FROM currencies WHERE is_active = 1")
        active_codes = [r["code"] for r in curr_cursor.fetchall()] or ["USD", "ZAR", "ZWG"]
        for c_code in active_codes:
            db.execute("""
                INSERT OR IGNORE INTO wallet_balances (account_number, currency, balance, updated_at_utc)
                VALUES (?, ?, 0.0, ?)
            """, (bank_account_number, c_code, now_utc))

        # Automatically assign owner as business administrator if user exists
        cursor = db.execute("SELECT id FROM users WHERE username = ?", (owner_username,))
        if cursor.fetchone():
            all_perms = json.dumps(["admin", "pos", "inventory", "agriculture", "security", "social", "vouchers", "reports"])
            db.execute("""
                INSERT OR IGNORE INTO business_operators (id, business_id, username, role_in_business, permissions_json, granted_by, created_at_utc, is_active)
                VALUES (?, ?, ?, 'admin', ?, ?, ?, 1)
            """, (f"op-{uuid.uuid4().hex[:8]}", biz_id, owner_username, all_perms, owner_username, now_utc))

    biz_record = get_business_by_id(biz_id)

    # Sync to local Data Node storage if active
    try:
        data_node_url = os.environ.get("MADN_DATA_NODE_URL", "http://127.0.0.1:8002")
        import urllib.request
        req_data = json.dumps({
            "collection": "businesses",
            "key": biz_id,
            "data": json.dumps(biz_record)
        }).encode('utf-8')
        req = urllib.request.Request(f"{data_node_url}/api/storage/put", data=req_data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=1.0)
    except Exception:
        pass

    return biz_record


def get_all_businesses() -> list:
    """Retrieves list of all active businesses."""
    with get_db() as db:
        cursor = db.execute("SELECT * FROM businesses WHERE is_active = 1 ORDER BY created_at_utc ASC")
        return [dict(row) for row in cursor.fetchall()]


def get_business_by_id(biz_id: str) -> dict:
    """Retrieves business profile by ID."""
    with get_db() as db:
        cursor = db.execute("SELECT * FROM businesses WHERE id = ?", (biz_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_business_banking_accounts(owner_username: str = None) -> list:
    """Retrieves all business banking settlement accounts with real-time multi-currency balances."""
    with get_db() as db:
        if owner_username and owner_username != "admin":
            cursor = db.execute("""
                SELECT w.*, b.name as business_name, b.category as business_category, b.logo_url as business_logo, b.currency_preference
                FROM wallets w
                JOIN businesses b ON w.business_id = b.id
                JOIN business_operators bo ON b.id = bo.business_id
                WHERE w.account_type = 'business' AND bo.username = ? AND b.is_active = 1
                ORDER BY b.name ASC
            """, (owner_username,))
        else:
            cursor = db.execute("""
                SELECT w.*, b.name as business_name, b.category as business_category, b.logo_url as business_logo, b.currency_preference
                FROM wallets w
                JOIN businesses b ON w.business_id = b.id
                WHERE w.account_type = 'business' AND b.is_active = 1
                ORDER BY b.name ASC
            """)
        accounts = []
        for row in cursor.fetchall():
            acc = dict(row)
            acc_num = acc["account_number"]
            bal_cursor = db.execute("SELECT currency, balance FROM wallet_balances WHERE account_number = ?", (acc_num,))
            balances = {r["currency"]: r["balance"] for r in bal_cursor.fetchall()}
            if "USD" not in balances: balances["USD"] = acc.get("balance_usd", 0.0)
            if "ZAR" not in balances: balances["ZAR"] = acc.get("balance_zar", 0.0)
            if "ZWG" not in balances: balances["ZWG"] = acc.get("balance_zwg", 0.0)
            acc["balances"] = balances
            accounts.append(acc)
        return accounts


def get_business_sales_analytics(business_id: str = None, time_range: str = "24h") -> dict:
    """
    Computes sales revenue, COGS, gross margins, transaction count, units sold,
    and hourly velocity for a single business or aggregated across all businesses.
    """
    with get_db() as db:
        where_clause = "WHERE t.type = 'SALE'"
        params = []
        if business_id and business_id != "all":
            where_clause += " AND (inv.business_id = ? OR (inv.business_id IS NULL AND t.business_id = ?))"
            params.extend([business_id, business_id])

        # Gross revenue & units
        cursor_summary = db.execute(f"""
            SELECT 
                COUNT(DISTINCT t.id) as tx_count,
                COALESCE(SUM(ti.quantity * ti.price_usd_at_sale), 0.0) as gross_revenue,
                COALESCE(SUM(ti.quantity), 0.0) as total_units_sold,
                COALESCE(SUM(ti.quantity * COALESCE(inv.cost_price_usd, ti.price_usd_at_sale * 0.6)), 0.0) as total_cogs
            FROM transactions t
            JOIN transaction_items ti ON t.id = ti.transaction_id
            LEFT JOIN inventory inv ON ti.inventory_id = inv.id
            {where_clause}
        """, params)
        summary = cursor_summary.fetchone()
        
        gross_rev = float(summary["gross_revenue"] or 0.0)
        cogs = float(summary["total_cogs"] or 0.0)
        gross_profit = gross_rev - cogs
        margin_pct = ((gross_profit / gross_rev) * 100.0) if gross_rev > 0 else 0.0

        # Top items
        cursor_top = db.execute(f"""
            SELECT 
                COALESCE(inv.name, 'Item') as item_name,
                COALESCE(inv.sku, 'N/A') as sku,
                COALESCE(inv.brand, '') as brand,
                COALESCE(inv.image_url, '') as image_url,
                SUM(ti.quantity) as units_sold,
                SUM(ti.quantity * ti.price_usd_at_sale) as total_revenue
            FROM transactions t
            JOIN transaction_items ti ON t.id = ti.transaction_id
            LEFT JOIN inventory inv ON ti.inventory_id = inv.id
            {where_clause}
            GROUP BY ti.inventory_id
            ORDER BY total_revenue DESC
            LIMIT 5
        """, params)
        top_items = [dict(r) for r in cursor_top.fetchall()]

        # Per business breakdown
        cursor_breakdown = db.execute("""
            SELECT 
                COALESCE(b.id, 'biz-unknown') as business_id,
                COALESCE(b.name, 'Default Store') as business_name,
                COALESCE(b.logo_url, '') as logo_url,
                COUNT(DISTINCT t.id) as tx_count,
                SUM(ti.quantity * ti.price_usd_at_sale) as revenue,
                SUM(ti.quantity) as units
            FROM transactions t
            JOIN transaction_items ti ON t.id = ti.transaction_id
            LEFT JOIN inventory inv ON ti.inventory_id = inv.id
            LEFT JOIN businesses b ON inv.business_id = b.id
            WHERE t.type = 'SALE'
            GROUP BY b.id
            ORDER BY revenue DESC
        """)
        breakdown = [dict(r) for r in cursor_breakdown.fetchall()]

        # Hourly velocity (last 24 hours)
        now_ts = int(time.time())
        day_ago = now_ts - 86400
        cursor_hourly = db.execute(f"""
            SELECT 
                (t.timestamp / 3600) * 3600 as hour_bucket,
                SUM(ti.quantity * ti.price_usd_at_sale) as hourly_rev
            FROM transactions t
            JOIN transaction_items ti ON t.id = ti.transaction_id
            LEFT JOIN inventory inv ON ti.inventory_id = inv.id
            {where_clause} AND t.timestamp >= {day_ago}
            GROUP BY hour_bucket
            ORDER BY hour_bucket ASC
        """, params)
        hourly_map = {str(r["hour_bucket"]): float(r["hourly_rev"]) for r in cursor_hourly.fetchall()}

        return {
            "business_id": business_id or "all",
            "gross_revenue_usd": round(gross_rev, 2),
            "cogs_usd": round(cogs, 2),
            "total_cogs_usd": round(cogs, 2),
            "gross_profit_usd": round(gross_profit, 2),
            "gross_margin_pct": round(margin_pct, 1),
            "total_transactions": int(summary["tx_count"] or 0),
            "transactions_count": int(summary["tx_count"] or 0),
            "total_units_sold": float(summary["total_units_sold"] or 0.0),
            "units_sold_total": float(summary["total_units_sold"] or 0.0),
            "top_selling_items": top_items,
            "business_breakdown": breakdown,
            "hourly_velocity": hourly_map
        }



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
# DYNAMIC MULTI-CURRENCY & VIRTUAL TOKEN ENGINE
# =====================================================================

def get_all_currencies(include_inactive: bool = False) -> list:
    """Returns list of configured currencies and exchange rates."""
    with get_db() as db:
        query = "SELECT * FROM currencies"
        if not include_inactive:
            query += " WHERE is_active = 1"
        query += " ORDER BY is_default DESC, code ASC"
        cursor = db.execute(query)
        return [dict(row) for row in cursor.fetchall()]


def get_currency_by_code(code: str) -> Optional[dict]:
    """Retrieves single currency configuration by code."""
    with get_db() as db:
        cursor = db.execute("SELECT * FROM currencies WHERE code = ?", (code.upper().strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None


def add_currency(code: str, name: str, symbol: str, exchange_rate_to_usd: float, currency_type: str = "fiat", is_default: int = 0, performed_by: str = "system") -> dict:
    """Registers a new fiat currency, gold-backed token, or virtual community currency."""
    code = code.upper().strip()
    if not code or len(code) > 12:
        raise ValueError("Currency code must be 1-12 alphanumeric characters.")
    if exchange_rate_to_usd <= 0:
        raise ValueError("Exchange rate to USD must be positive.")
    
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with get_db() as db:
        cursor = db.execute("SELECT code FROM currencies WHERE code = ?", (code,))
        if cursor.fetchone():
            raise ValueError(f"Currency with code '{code}' already exists.")
        
        db.execute("""
            INSERT INTO currencies (code, name, symbol, exchange_rate_to_usd, currency_type, is_default, is_active, created_at_utc, updated_at_utc)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
        """, (code, name.strip(), symbol.strip(), exchange_rate_to_usd, currency_type, is_default, now_utc, now_utc))
        db.commit()

    write_audit_log(performed_by, "CURRENCY_CREATE", f"Added currency {code} ({name}) with rate {exchange_rate_to_usd} USD/rate")
    
    # Sync to Data Node storage
    sync_record_to_data_nodes("currencies", code, {
        "code": code, "name": name.strip(), "symbol": symbol.strip(),
        "exchange_rate_to_usd": exchange_rate_to_usd, "currency_type": currency_type
    })
    return get_currency_by_code(code)


def update_currency(code: str, name: str = None, symbol: str = None, exchange_rate_to_usd: float = None, is_active: int = None, performed_by: str = "system") -> dict:
    """Updates currency properties or exchange rate."""
    code = code.upper().strip()
    curr = get_currency_by_code(code)
    if not curr:
        raise ValueError(f"Currency '{code}' not found.")
    
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with get_db() as db:
        if name is not None:
            db.execute("UPDATE currencies SET name = ? WHERE code = ?", (name.strip(), code))
        if symbol is not None:
            db.execute("UPDATE currencies SET symbol = ? WHERE code = ?", (symbol.strip(), code))
        if exchange_rate_to_usd is not None:
            if exchange_rate_to_usd <= 0:
                raise ValueError("Exchange rate to USD must be positive.")
            db.execute("UPDATE currencies SET exchange_rate_to_usd = ? WHERE code = ?", (exchange_rate_to_usd, code))
        if is_active is not None:
            db.execute("UPDATE currencies SET is_active = ? WHERE code = ?", (1 if is_active else 0, code))
        db.execute("UPDATE currencies SET updated_at_utc = ? WHERE code = ?", (now_utc, code))
        db.commit()

    write_audit_log(performed_by, "CURRENCY_UPDATE", f"Updated currency {code}")
    updated = get_currency_by_code(code)
    sync_record_to_data_nodes("currencies", code, updated)
    return updated


def delete_currency(code: str, performed_by: str = "system") -> dict:
    """Deactivates/removes a currency."""
    code = code.upper().strip()
    if code in ["USD"]:
        raise ValueError("Primary settlement currency (USD) cannot be deactivated.")
    return update_currency(code, is_active=0, performed_by=performed_by)


# =====================================================================
# CUSTOMER DIGITAL BANKING, MULTI-CURRENCY LEDGER & RECEIPT VAULT
# =====================================================================

def create_wallet_for_user(username: str) -> dict:
    """Provisions a new multi-currency wallet account for a registered user with authentic 0.00 balances."""
    acc_num = f"ACC-2026-{uuid.uuid4().hex[:6].upper()}"
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with get_db() as db:
        cursor = db.execute("SELECT * FROM wallets WHERE username = ? AND (account_type = 'personal' OR account_type IS NULL OR account_type = '')", (username,))
        existing = cursor.fetchone()
        if existing:
            return get_wallet_by_username(username, auto_create=False)
        db.execute("""
            INSERT INTO wallets (account_number, username, balance_usd, balance_zar, balance_zwg, created_at_utc, status, account_type)
            VALUES (?, ?, 0.0, 0.0, 0.0, ?, 'active', 'personal')
        """, (acc_num, username, now_utc))
        
        # Provision 0.0 balance for all active currencies
        active_currs = db.execute("SELECT code FROM currencies WHERE is_active = 1").fetchall()
        for c in active_currs:
            db.execute("""
                INSERT OR IGNORE INTO wallet_balances (account_number, currency, balance, updated_at_utc)
                VALUES (?, ?, 0.0, ?)
            """, (acc_num, c["code"], now_utc))
        db.commit()

    # Sync to Data Node
    sync_record_to_data_nodes("wallets", acc_num, {
        "account_number": acc_num, "username": username, "status": "active"
    })
    return get_wallet_by_username(username, auto_create=False)


def get_wallet_by_username(username: str, auto_create: bool = True) -> Optional[dict]:
    """Returns the multi-currency wallet details for a user with dynamic balances."""
    with get_db() as db:
        cursor = db.execute("SELECT * FROM wallets WHERE username = ? AND (account_type = 'personal' OR account_type IS NULL OR account_type = '')", (username,))
        row = cursor.fetchone()
        if not row:
            if auto_create:
                return create_wallet_for_user(username)
            return None
        
        wallet = dict(row)
        acc_num = wallet["account_number"]
        
        # Fetch dynamic balances from wallet_balances table
        bal_cursor = db.execute("SELECT currency, balance FROM wallet_balances WHERE account_number = ?", (acc_num,))
        balances = {b["currency"]: b["balance"] for b in bal_cursor.fetchall()}
        
        # Ensure all active currencies are present in balances
        active_currs = db.execute("SELECT code FROM currencies WHERE is_active = 1").fetchall()
        now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        for c in active_currs:
            code = c["code"]
            if code not in balances:
                legacy_val = 0.0
                if code == "USD": legacy_val = wallet.get("balance_usd", 0.0)
                elif code == "ZAR": legacy_val = wallet.get("balance_zar", 0.0)
                elif code == "ZWG": legacy_val = wallet.get("balance_zwg", 0.0)
                db.execute("INSERT OR REPLACE INTO wallet_balances (account_number, currency, balance, updated_at_utc) VALUES (?, ?, ?, ?)", (acc_num, code, legacy_val, now_utc))
                balances[code] = legacy_val
        db.commit()
        
        wallet["balances"] = balances
        wallet["balance_usd"] = balances.get("USD", wallet.get("balance_usd", 0.0))
        wallet["balance_zar"] = balances.get("ZAR", wallet.get("balance_zar", 0.0))
        wallet["balance_zwg"] = balances.get("ZWG", wallet.get("balance_zwg", 0.0))
        return wallet


def topup_wallet(username: str, currency: str, amount: float, notes: str = "Deposit", performed_by: str = "system") -> dict:
    """Deposits funds into a user's wallet and creates an audit ledger entry for any supported currency."""
    curr = currency.upper().strip()
    active_currs = [c["code"] for c in get_all_currencies(include_inactive=False)]
    if curr not in active_currs:
        raise ValueError(f"Unsupported or inactive currency: {currency}")
    if amount <= 0:
        raise ValueError("Top-up amount must be positive.")

    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    wallet = get_wallet_by_username(username)
    acc_num = wallet["account_number"]

    with get_db() as db:
        # Update dynamic wallet_balances
        db.execute("""
            INSERT INTO wallet_balances (account_number, currency, balance, updated_at_utc)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(account_number, currency) DO UPDATE SET balance = balance + ?, updated_at_utc = ?
        """, (acc_num, curr, amount, now_utc, amount, now_utc))

        cursor = db.execute("SELECT balance FROM wallet_balances WHERE account_number = ? AND currency = ?", (acc_num, curr))
        new_bal = cursor.fetchone()["balance"]

        # Sync legacy columns if applicable
        if curr in ["USD", "ZAR", "ZWG"]:
            db.execute(f"UPDATE wallets SET balance_{curr.lower()} = ? WHERE account_number = ?", (new_bal, acc_num))

        # Signature payload
        tx_id = f"wtx-{uuid.uuid4().hex[:8]}"
        payload = f"{tx_id}|{acc_num}|deposit|{curr}|{amount:.2f}|{new_bal:.2f}|{now_utc}"
        sig = hmac.new(VAULT_SECRET_KEY, payload.encode("utf-8"), hashlib.sha256).hexdigest()

        db.execute("""
            INSERT INTO wallet_ledger (id, account_number, transaction_type, currency, amount, balance_after, counterparty, reference_id, notes, timestamp_utc, signature_hmac)
            VALUES (?, ?, 'deposit', ?, ?, ?, ?, ?, ?, ?, ?)
        """, (tx_id, acc_num, curr, amount, new_bal, performed_by, tx_id, notes, now_utc, sig))
        db.commit()

    write_audit_log(performed_by, "WALLET_TOPUP", f"Deposited {amount} {curr} to {username} ({acc_num}). New balance: {new_bal} {curr}")
    
    # Sync wallet update to Data Node
    sync_record_to_data_nodes("wallets", acc_num, {
        "account_number": acc_num, "username": username, "currency": curr, "new_balance": new_bal
    })
    
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
    """Atomically transfers funds from one user's wallet to another user's wallet across any active currency."""
    curr = currency.upper().strip()
    active_currs = [c["code"] for c in get_all_currencies(include_inactive=False)]
    if curr not in active_currs:
        raise ValueError(f"Unsupported or inactive currency: {currency}")
    if amount <= 0:
        raise ValueError("Transfer amount must be positive.")

    from_wallet = get_wallet_by_username(from_user)
    to_wallet = get_wallet_by_username(to_user)
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    wtx_id = f"wtx-{uuid.uuid4().hex[:8]}"

    with get_db() as db:
        cursor = db.execute("SELECT balance FROM wallet_balances WHERE account_number = ? AND currency = ?", (from_wallet["account_number"], curr))
        row = cursor.fetchone()
        sender_bal = row["balance"] if row else 0.0
        if sender_bal < amount:
            raise ValueError(f"Insufficient funds in {curr}. Available: {sender_bal:.2f}, Required: {amount:.2f}")

        # Debit sender
        new_sender_bal = sender_bal - amount
        db.execute("UPDATE wallet_balances SET balance = ?, updated_at_utc = ? WHERE account_number = ? AND currency = ?", (new_sender_bal, now_utc, from_wallet["account_number"], curr))
        if curr in ["USD", "ZAR", "ZWG"]:
            db.execute(f"UPDATE wallets SET balance_{curr.lower()} = ? WHERE account_number = ?", (new_sender_bal, from_wallet["account_number"]))

        # Credit receiver
        db.execute("""
            INSERT INTO wallet_balances (account_number, currency, balance, updated_at_utc)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(account_number, currency) DO UPDATE SET balance = balance + ?, updated_at_utc = ?
        """, (to_wallet["account_number"], curr, amount, now_utc, amount, now_utc))
        
        cursor = db.execute("SELECT balance FROM wallet_balances WHERE account_number = ? AND currency = ?", (to_wallet["account_number"], curr))
        new_recv_bal = cursor.fetchone()["balance"]
        if curr in ["USD", "ZAR", "ZWG"]:
            db.execute(f"UPDATE wallets SET balance_{curr.lower()} = ? WHERE account_number = ?", (new_recv_bal, to_wallet["account_number"]))

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
        db.commit()

    write_audit_log(from_user, "WALLET_TRANSFER", f"Transferred {amount} {curr} from @{from_user} to @{to_user}")
    
    # Sync to Data Node
    sync_record_to_data_nodes("wallets", from_wallet["account_number"], {"account_number": from_wallet["account_number"], "currency": curr, "new_balance": new_sender_bal})
    sync_record_to_data_nodes("wallets", to_wallet["account_number"], {"account_number": to_wallet["account_number"], "currency": curr, "new_balance": new_recv_bal})

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
    """Redeems an offline QR voucher and converts it directly into liquid wallet balance for any currency."""
    wallet = get_wallet_by_username(username)
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()

    redemption = verify_and_redeem_voucher(vid, redeemed_by_tx_id=f"WALLET-DEP-{wallet['account_number']}")
    if not redemption.get("success"):
        return redemption

    curr = redemption["currency"].upper().strip()
    amt = redemption["value_amount"]
    wtx_id = f"wtx-vdep-{uuid.uuid4().hex[:8]}"

    with get_db() as db:
        db.execute("""
            INSERT INTO wallet_balances (account_number, currency, balance, updated_at_utc)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(account_number, currency) DO UPDATE SET balance = balance + ?, updated_at_utc = ?
        """, (wallet["account_number"], curr, amt, now_utc, amt, now_utc))

        cursor = db.execute("SELECT balance FROM wallet_balances WHERE account_number = ? AND currency = ?", (wallet["account_number"], curr))
        new_bal = cursor.fetchone()["balance"]

        if curr in ["USD", "ZAR", "ZWG"]:
            db.execute(f"UPDATE wallets SET balance_{curr.lower()} = ? WHERE account_number = ?", (new_bal, wallet["account_number"]))

        sig = hmac.new(VAULT_SECRET_KEY, f"{wtx_id}|{wallet['account_number']}|voucher_deposit|{amt:.2f}|{new_bal:.2f}".encode("utf-8"), hashlib.sha256).hexdigest()
        db.execute("""
            INSERT INTO wallet_ledger (id, account_number, transaction_type, currency, amount, balance_after, counterparty, reference_id, notes, timestamp_utc, signature_hmac)
            VALUES (?, ?, 'voucher_deposit', ?, ?, ?, ?, ?, ?, ?, ?)
        """, (wtx_id, wallet["account_number"], curr, amt, new_bal, redemption["business_id"], vid, f"Voucher {vid} converted to wallet balance", now_utc, sig))
        db.commit()

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

    # Heavy data-at-rest encryption (AES-256-GCM)
    encrypted_receipt_json = encrypt_vault_payload(receipt_json)

    with get_db() as db:
        db.execute("""
            INSERT OR REPLACE INTO customer_receipts (id, transaction_id, customer_username, business_id, invoice_number, total_due_usd, receipt_json, created_at_utc, audit_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (rcv_id, tx_id, customer_username, business_id, inv_num, total_due, encrypted_receipt_json, now_utc, audit_hash))

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
                WHERE cr.customer_username = ? AND (cr.invoice_number LIKE ? OR b.name LIKE ?)
                ORDER BY cr.created_at_utc DESC
            """, (customer_username, q, q))
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
            raw_encrypted = d.get("receipt_json") or "{}"
            decrypted_json_str = decrypt_vault_payload(raw_encrypted)
            d["receipt_json"] = decrypted_json_str
            try:
                d["receipt_data"] = json.loads(decrypted_json_str)
            except Exception:
                d["receipt_data"] = {}
            if query and query.lower() not in decrypted_json_str.lower() and query.lower() not in (d.get("invoice_number") or "").lower() and query.lower() not in (d.get("business_name") or "").lower():
                continue
            result.append(d)
        return result


# =====================================================================
# STAGE 1 CORE: SEED DEMO DATA & ROLES
# =====================================================================

def seed_stage1_demo_data():
    """Seeds only the initial primary administrator account and its wallet. All other accounts register dynamically."""
    now = int(time.time())
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()

    with get_db() as db:
        # Seed only the primary admin user if not exists
        cursor = db.execute("SELECT id FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            salt_hex, hash_hex = hash_password("Password123!")
            db.execute("""
                INSERT OR IGNORE INTO users (username, password_hash, salt, role, status, created_at, updated_at, must_change_password, pin)
                VALUES ('admin', ?, ?, 'admin', 'active', ?, ?, 0, '1234')
            """, (hash_hex, salt_hex, now, now))

        # Seed admin wallet with authentic 0.00 balances
        cursor = db.execute("SELECT account_number FROM wallets WHERE username = 'admin'")
        if not cursor.fetchone():
            acc = f"ACC-2026-{uuid.uuid4().hex[:6].upper()}"
            db.execute("""
                INSERT OR IGNORE INTO wallets (account_number, username, balance_usd, balance_zar, balance_zwg, created_at_utc, status)
                VALUES (?, 'admin', 0.0, 0.0, 0.0, ?, 'active')
            """, (acc, now_utc))
            
            # Initialize wallet_balances for all active currencies
            active_currs = db.execute("SELECT code FROM currencies WHERE is_active = 1").fetchall()
            for c in active_currs:
                db.execute("""
                    INSERT OR IGNORE INTO wallet_balances (account_number, currency, balance, updated_at_utc)
                    VALUES (?, ?, 0.0, ?)
                """, (acc, c["code"], now_utc))

        db.commit()

    # Purge any remaining mock records in existing database instance
    purge_mock_data()


def purge_mock_data():
    """Purges hardcoded sample/mock demonstration records from the active database."""
    with get_db() as db:
        db.execute("DELETE FROM agri_production_costs WHERE id = 'cost-demo-1';")
        db.execute("DELETE FROM agri_plantings WHERE id = 'plant-demo-1';")
        db.execute("DELETE FROM security_visitor_logs WHERE id = 'vis-demo-1';")
        db.execute("DELETE FROM social_posts WHERE id IN ('post-x-1', 'post-ig-1', 'post-snap-1', 'post-tik-1');")
        db.execute("DELETE FROM vouchers WHERE vid = 'vouch-demo-1';")
        db.execute("DELETE FROM businesses WHERE id IN ('biz-green-valley', 'biz-khumalo-millers', 'biz-matopos-dairy');")
        db.execute("DELETE FROM business_operators WHERE business_id IN ('biz-green-valley', 'biz-khumalo-millers', 'biz-matopos-dairy');")
        db.commit()


# =====================================================================
# OPERATOR PROFILE & INTER-CLUSTER NODE SECURITY KEYS
# =====================================================================

def get_user_profile(user_id_or_username) -> Optional[dict]:
    """Retrieves full operator profile including contact details and multi-currency digital accounts."""
    with get_db() as db:
        if isinstance(user_id_or_username, int) or (isinstance(user_id_or_username, str) and user_id_or_username.isdigit()):
            cursor = db.execute("SELECT * FROM users WHERE id = ?", (int(user_id_or_username),))
        else:
            cursor = db.execute("SELECT * FROM users WHERE username = ?", (str(user_id_or_username),))
        user = cursor.fetchone()
        if not user:
            return None
        
        user_dict = dict(user)
        username = user_dict["username"]
        
        # Query wallet balances
        w_cursor = db.execute("SELECT * FROM wallets WHERE username = ?", (username,))
        wallet = w_cursor.fetchone()
        wallet_dict = dict(wallet) if wallet else {
            "account_number": "UNASSIGNED",
            "balance_usd": 0.0,
            "balance_zar": 0.0,
            "balance_zwg": 0.0,
            "status": "inactive"
        }
        
        return {
            "id": user_dict["id"],
            "username": user_dict["username"],
            "full_name": user_dict.get("full_name") or "",
            "phone": user_dict.get("phone") or "",
            "email": user_dict.get("email") or "",
            "avatar_url": user_dict.get("avatar_url") or "",
            "role": user_dict["role"],
            "status": user_dict["status"],
            "created_at": user_dict["created_at"],
            "updated_at": user_dict["updated_at"],
            "must_change_password": user_dict["must_change_password"],
            "pin_set": bool(user_dict.get("pin")),
            "mfa_enrolled": bool(user_dict.get("mfa_secret")),
            "account_number": wallet_dict.get("account_number", "UNASSIGNED"),
            "wallet": {
                "balance_usd": wallet_dict.get("balance_usd", 0.0),
                "balance_zar": wallet_dict.get("balance_zar", 0.0),
                "balance_zwg": wallet_dict.get("balance_zwg", 0.0),
                "status": wallet_dict.get("status", "active")
            }
        }


def update_user_profile(user_id: int, full_name: str = None, phone: str = None, email: str = None, new_username: str = None, pin: str = None, avatar_url: str = None) -> dict:
    """Updates operator profile fields, profile picture, and safely cascades username modifications."""
    now = int(time.time())
    db = get_db()
    try:
        cursor = db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        current_user = cursor.fetchone()
        if not current_user:
            raise ValueError("User not found")
        
        old_username = current_user["username"]
        target_username = old_username

        if new_username and new_username.strip() and new_username.strip() != old_username:
            clean_user = new_username.strip()
            if len(clean_user) < 3 or not clean_user.replace("_", "").isalnum():
                raise ValueError("Username must be at least 3 alphanumeric characters")
            
            chk = db.execute("SELECT id FROM users WHERE username = ? AND id != ?", (clean_user, user_id)).fetchone()
            if chk:
                raise ValueError(f"Username '{clean_user}' is already taken")
            
            target_username = clean_user
            
            # Temporarily disable foreign keys during cascading username update to prevent constraint failure
            db.execute("PRAGMA foreign_keys = OFF;")
            db.execute("UPDATE users SET username = ? WHERE id = ?", (target_username, user_id))
            db.execute("UPDATE wallets SET username = ? WHERE username = ?", (target_username, old_username))
            db.execute("UPDATE business_operators SET username = ? WHERE username = ?", (target_username, old_username))
            db.execute("UPDATE business_operators SET granted_by = ? WHERE granted_by = ?", (target_username, old_username))
            db.execute("UPDATE customer_receipts SET customer_username = ? WHERE customer_username = ?", (target_username, old_username))
            db.execute("UPDATE businesses SET owner_username = ? WHERE owner_username = ?", (target_username, old_username))
            db.execute("PRAGMA foreign_keys = ON;")

        updates = []
        params = []
        if full_name is not None:
            updates.append("full_name = ?")
            params.append(full_name.strip())
        if phone is not None:
            updates.append("phone = ?")
            params.append(phone.strip())
        if email is not None:
            updates.append("email = ?")
            params.append(email.strip())
        if avatar_url is not None:
            updates.append("avatar_url = ?")
            params.append(avatar_url.strip())
        if pin is not None:
            clean_pin = pin.strip()
            if clean_pin and (len(clean_pin) != 4 or not clean_pin.isdigit()):
                raise ValueError("Security PIN must be exactly 4 digits")
            if clean_pin:
                updates.append("pin = ?")
                params.append(clean_pin)

        updates.append("updated_at = ?")
        params.append(now)
        params.append(user_id)

        if updates:
            db.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", tuple(params))
        
        db.commit()
    finally:
        db.close()

    write_audit_log(target_username, "PROFILE_UPDATE", f"Operator profile updated for user ID #{user_id} (username: {target_username})")
    return get_user_profile(user_id)


def register_or_rotate_node_key(node_id: str, node_type: str = "data_node", ip_address: str = "127.0.0.1", port: int = 8002, secret_key: str = None, notes: str = "") -> dict:
    """Registers or rotates a 256-bit cryptographic HMAC communication key for a cluster node in the Vault DB."""
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if not secret_key:
        secret_key = secrets.token_hex(32)  # 256-bit HMAC key
    
    with get_db() as db:
        cursor = db.execute("SELECT node_id FROM node_communication_keys WHERE node_id = ?", (node_id,))
        if cursor.fetchone():
            db.execute("""
                UPDATE node_communication_keys
                SET node_type = ?, ip_address = ?, port = ?, hmac_secret_key = ?, last_rotated_utc = ?, notes = ?, status = 'active'
                WHERE node_id = ?
            """, (node_type, ip_address, port, secret_key, now_utc, notes, node_id))
        else:
            db.execute("""
                INSERT INTO node_communication_keys (node_id, node_type, ip_address, port, hmac_secret_key, status, created_at_utc, last_rotated_utc, notes)
                VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?)
            """, (node_id, node_type, ip_address, port, secret_key, now_utc, now_utc, notes))
        db.commit()
    
    write_audit_log("SYSTEM", "NODE_KEY_ROTATED", f"Communication key for node '{node_id}' ({node_type} at {ip_address}:{port}) registered/rotated in Vault DB")
    return {
        "node_id": node_id,
        "node_type": node_type,
        "ip_address": ip_address,
        "port": port,
        "hmac_secret_key": secret_key,
        "status": "active",
        "last_rotated_utc": now_utc
    }


def list_node_communication_keys() -> list:
    """Lists all cluster node communication keys registered in the Vault DB."""
    with get_db() as db:
        cursor = db.execute("SELECT node_id, node_type, ip_address, port, status, created_at_utc, last_rotated_utc, notes FROM node_communication_keys ORDER BY created_at_utc ASC")
        rows = [dict(r) for r in cursor.fetchall()]
    return rows


def get_node_communication_key(node_id: str) -> Optional[dict]:
    """Retrieves full communication key record for signature verification."""
    with get_db() as db:
        cursor = db.execute("SELECT * FROM node_communication_keys WHERE node_id = ?", (node_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


# =====================================================================
# DATA NODE REPLICATION & COLLECTION SYNCHRONIZATION
# =====================================================================

def sync_record_to_data_nodes(collection: str, key: str, data: Any) -> bool:
    """Replicates a key-value record to connected Standalone Data Node storage (:8002)."""
    try:
        data_node_url = os.environ.get("MADN_DATA_NODE_URL", "http://127.0.0.1:8002")
        import urllib.request
        payload = json.dumps({
            "collection": collection,
            "key": key,
            "data": json.dumps(data) if not isinstance(data, str) else data
        }).encode('utf-8')
        req = urllib.request.Request(f"{data_node_url}/api/storage/put", data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            return resp.status == 200
    except Exception:
        return False


def fetch_records_from_data_nodes(collection: str) -> list:
    """Fetches collection records from the connected Data Node (:8002)."""
    try:
        data_node_url = os.environ.get("MADN_DATA_NODE_URL", "http://127.0.0.1:8002")
        import urllib.request
        import urllib.parse
        req = urllib.request.Request(f"{data_node_url}/api/storage/list?collection={urllib.parse.quote(collection)}")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            if resp.status == 200:
                res_data = json.loads(resp.read().decode('utf-8'))
                return res_data.get("records", [])
    except Exception:
        pass
    return []


def sync_all_collections_to_data_nodes() -> dict:
    """Collects and replicates core operational state with connected Data Nodes."""
    results = {"synced_collections": [], "errors": 0}
    try:
        # 1. Sync currencies
        currs = get_all_currencies(include_inactive=True)
        for c in currs:
            sync_record_to_data_nodes("currencies", c["code"], c)
        results["synced_collections"].append("currencies")

        # 2. Sync businesses
        bizs = get_all_businesses()
        for b in bizs:
            sync_record_to_data_nodes("businesses", b["id"], b)
        results["synced_collections"].append("businesses")

        # 3. Sync inventory
        inv = get_inventory()
        for i in inv:
            sync_record_to_data_nodes("inventory", str(i["id"]), dict(i))
        results["synced_collections"].append("inventory")

        # 4. Sync node communication keys
        keys = list_node_communication_keys()
        for k in keys:
            sync_record_to_data_nodes("communication_keys", k["node_id"], k)
        results["synced_collections"].append("communication_keys")

        # 5. Sync agricultural fields
        fields = list_fields()
        for f in fields:
            sync_record_to_data_nodes("agri_fields", f["id"], f)
        results["synced_collections"].append("agri_fields")

        # 6. Sync agricultural plantings
        plantings = list_plantings()
        for p in plantings:
            sync_record_to_data_nodes("agri_plantings", p["id"], p)
        results["synced_collections"].append("agri_plantings")

        # 7. Sync agricultural harvests
        harvests = list_harvests()
        for h in harvests:
            sync_record_to_data_nodes("agri_harvests", h["id"], h)
        results["synced_collections"].append("agri_harvests")
        
        results["status"] = "success"
    except Exception as e:
        results["status"] = "partial"
        results["error"] = str(e)
    return results








def search_global_currency_catalog(query: str = "", category: str = None, limit: int = 50) -> list:
    """Searches the global catalog of ISO 4217 fiat and cryptocurrencies."""
    with get_db() as db:
        sql = "SELECT * FROM global_currency_catalog"
        params = []
        conditions = []
        if query:
            q_term = f"%{query.strip()}%"
            conditions.append("(code LIKE ? OR name LIKE ? OR country_or_issuer LIKE ?)")
            params.extend([q_term, q_term, q_term])
        if category:
            conditions.append("category = ?")
            params.append(category)
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY is_iso4217 DESC, code ASC LIMIT ?"
        params.append(limit)
        
        cursor = db.execute(sql, tuple(params))
        return [dict(row) for row in cursor.fetchall()]

def get_global_currency_by_code(code: str) -> Optional[dict]:
    """Retrieves a single global currency specification by code."""
    with get_db() as db:
        cursor = db.execute("SELECT * FROM global_currency_catalog WHERE code = ?", (code.upper().strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None

def validate_currency_code_collision(code: str, name: str = "") -> dict:
    """
    Evaluates proposed currency code for namespace collision against:
    1. Currently active local currencies in Vault node.
    2. Official ISO 4217 sovereign fiat currencies.
    3. Major global cryptocurrencies and digital reserve assets.
    """
    code = code.upper().strip()
    if not code:
        return {"code": "", "collision": False, "collision_type": "EMPTY", "message": "Please enter a currency code."}

    # 1. Check local active node currencies
    with get_db() as db:
        local_curr = db.execute("SELECT * FROM currencies WHERE code = ?", (code,)).fetchone()
        if local_curr:
            curr_dict = dict(local_curr)
            is_act = curr_dict.get("is_active", 1) == 1
            return {
                "code": code,
                "collision": True,
                "collision_type": "EXISTING_ACTIVE_CURRENCY" if is_act else "EXISTING_INACTIVE_CURRENCY",
                "matched_currency": curr_dict,
                "message": f"Currency code '{code}' already exists in your local node ({'Active' if is_act else 'Inactive'}).",
                "can_adopt": False,
                "can_reactivate": not is_act
            }

    # 2. Check global catalog
    matched = get_global_currency_by_code(code)
    if matched:
        cat = matched.get("category", "fiat")
        if cat in ["fiat", "gold_backed"]:
            return {
                "code": code,
                "collision": True,
                "collision_type": "OFFICIAL_ISO_FIAT",
                "matched_currency": matched,
                "message": f"Code '{code}' matches official ISO 4217 sovereign fiat '{matched['name']}' ({matched.get('country_or_issuer', '')}).",
                "can_adopt": True,
                "suggested_name": matched["name"],
                "suggested_symbol": matched["symbol"],
                "suggested_type": matched["category"],
                "suggested_rate": matched.get("rate_to_usd", 1.0)
            }
        elif cat in ["crypto", "stablecoin"]:
            return {
                "code": code,
                "collision": True,
                "collision_type": "MAJOR_CRYPTO",
                "matched_currency": matched,
                "message": f"Code '{code}' matches cryptocurrency asset '{matched['name']}' ({matched.get('country_or_issuer', '')}).",
                "can_adopt": True,
                "suggested_name": matched["name"],
                "suggested_symbol": matched["symbol"],
                "suggested_type": "virtual_token",
                "suggested_rate": matched.get("rate_to_usd", 1.0)
            }
        elif cat == "commodity":
            return {
                "code": code,
                "collision": True,
                "collision_type": "COMMODITY_ASSET",
                "matched_currency": matched,
                "message": f"Code '{code}' matches precious metal commodity standard '{matched['name']}'.",
                "can_adopt": True,
                "suggested_name": matched["name"],
                "suggested_symbol": matched["symbol"],
                "suggested_type": "gold_backed",
                "suggested_rate": matched.get("rate_to_usd", 1.0)
            }

    # 3. No collision - safe unique custom token
    return {
        "code": code,
        "collision": False,
        "collision_type": "UNIQUE_AVAILABLE",
        "matched_currency": None,
        "message": f"Code '{code}' is unique and available for your personalized virtual token.",
        "can_adopt": False
    }

def sync_global_currencies_from_data_node(data_node_url: str = None) -> dict:
    """Synchronizes global ISO 4217 and crypto reference catalog from connected Data Node."""
    if not data_node_url:
        data_node_url = os.getenv("MADN_DATA_NODE_URL", "http://127.0.0.1:8002")
    
    url = f"{data_node_url.rstrip('/')}/api/reference/currencies"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MADN-Vault/1.0"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                currencies = data.get("currencies", [])
                now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
                with get_db() as db:
                    for c in currencies:
                        db.execute("""
                            INSERT INTO global_currency_catalog (code, name, symbol, category, country_or_issuer, is_iso4217, default_decimals, rate_to_usd, last_updated_utc)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(code) DO UPDATE SET
                                name = excluded.name,
                                symbol = excluded.symbol,
                                category = excluded.category,
                                country_or_issuer = excluded.country_or_issuer,
                                last_updated_utc = excluded.last_updated_utc
                        """, (c["code"], c["name"], c["symbol"], c["category"], c.get("country_or_issuer", ""), c.get("is_iso4217", 0), c.get("default_decimals", 2), c.get("rate_to_usd", 1.0), now_utc))
                    db.commit()
                return {"status": "success", "synced_count": len(currencies), "source": url}
    except Exception as e:
        pass
    return {"status": "fallback", "synced_count": len(GLOBAL_AUTHORITATIVE_CATALOG), "note": "Using built-in authoritative seed"}
