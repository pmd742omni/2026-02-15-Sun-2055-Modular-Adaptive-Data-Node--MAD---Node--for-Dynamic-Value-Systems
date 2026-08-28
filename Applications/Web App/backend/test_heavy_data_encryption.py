import os
import sys
import pytest
import sqlite3
import json
import base64
import uuid
import tempfile
import time
from fastapi.testclient import TestClient

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

data_node_dir = os.path.abspath(os.path.join(backend_dir, "..", "..", "Data_Node"))
if data_node_dir not in sys.path:
    sys.path.insert(0, data_node_dir)

from auth_utils import (
    derive_vault_key_from_password,
    encrypt_vault_payload,
    decrypt_vault_payload,
    is_payload_encrypted,
    get_global_vault_key
)
from storage import DataNodeStorage, encrypt_data_node_payload, decrypt_data_node_payload
from database import (
    init_db,
    get_db,
    archive_customer_receipt,
    get_customer_receipts,
    create_business,
    get_business_by_id,
    get_all_businesses,
    add_inventory_item,
    checkin_visitor,
    list_visitors,
    update_user_profile,
    get_user_profile
)
from main import app

@pytest.fixture(scope="module")
def auth_session():
    client = TestClient(app)
    # Perform standard operator login
    login_res = client.post("/api/auth/login", json={"username": "admin", "password": "Password123!"})
    assert login_res.status_code == 200
    csrf = login_res.cookies.get("csrf_token", "")
    headers = {"X-CSRF-Token": csrf}
    return client, headers

def test_01_scrypt_master_key_derivation():
    """Verify scrypt 256-bit vault key derivation parameters."""
    pwd = "OperatorSecretPassphrase2026!"
    salt = b"test_salt_123456"
    key1, salt1 = derive_vault_key_from_password(pwd, salt)
    assert len(key1) == 32  # 256-bit AES key
    assert salt1 == salt
    
    # Determinism
    key2, _ = derive_vault_key_from_password(pwd, salt)
    assert key1 == key2

def test_02_aes_256_gcm_authenticated_payload_encryption():
    """Verify AES-256-GCM encryption, decryption, and tamper detection."""
    test_dict = {
        "account": "ACC-2026-9999",
        "secret_balance": 5420.50,
        "customer": "Sarah Sibanda",
        "sensitive_notes": "VIP Gold Account"
    }
    
    encrypted = encrypt_vault_payload(test_dict)
    assert is_payload_encrypted(encrypted)
    assert encrypted.startswith("ENC:")
    
    # Ensure plaintext is not exposed in ciphertext
    assert "Sarah Sibanda" not in encrypted
    assert "5420.50" not in encrypted
    
    # Decrypt and verify exact match
    decrypted = decrypt_vault_payload(encrypted, return_json=True)
    assert isinstance(decrypted, dict)
    assert decrypted["customer"] == "Sarah Sibanda"
    assert decrypted["secret_balance"] == 5420.50
    
    # Tamper detection test
    parts = encrypted.split(":")
    tampered_ct = parts[2][:-4] + "AAAA"  # Corrupt last 4 bytes (tag)
    tampered_str = f"ENC:{parts[1]}:{tampered_ct}"
    
    with pytest.raises(Exception):
        decrypt_vault_payload(tampered_str)

def test_03_database_customer_receipts_encryption_at_rest():
    """Verify customer receipts are stored as AES-256-GCM encrypted blobs on disk in SQLite."""
    user = "admin"
    biz = create_business(
        name="Crypto Vault Test Store",
        owner_username=user,
        tagline="Heavily Encrypted Store",
        description="AES-256 Protected"
    )
    biz_id = biz["id"]
    
    receipt_data = {
        "invoice_number": f"INV-{uuid.uuid4().hex[:8].upper()}",
        "total_due_usd": 45.00,
        "items": [
            {"name": "Organic Tomatoes", "qty": 5, "price": 2.00},
            {"name": "Stone-Ground Maize Meal", "qty": 2, "price": 17.50}
        ],
        "confidential_customer_id": "NAT-ID-78-901234-F-56"
    }
    
    tx_id = f"tx-{uuid.uuid4().hex[:8]}"
    with get_db() as db:
        db.execute("""
            INSERT INTO transactions (id, timestamp, operator_username, total_due_usd, type, client_request_id)
            VALUES (?, ?, ?, 45.00, 'sale', ?)
        """, (tx_id, int(time.time()), user, f"req-{uuid.uuid4().hex[:8]}"))
    
    archived = archive_customer_receipt(
        tx_id=tx_id,
        customer_username=user,
        business_id=biz_id,
        receipt_data=receipt_data
    )
    assert archived["id"].startswith("rcv-")
    
    # Directly inspect raw SQLite disk row to ensure it is encrypted
    with get_db() as db:
        cursor = db.execute("SELECT receipt_json FROM customer_receipts WHERE id = ?", (archived["id"],))
        raw_row = cursor.fetchone()
        assert raw_row is not None
        raw_db_value = raw_row["receipt_json"]
        
        # Raw value on disk MUST be encrypted with ENC: prefix
        assert raw_db_value.startswith("ENC:")
        assert "NAT-ID-78-901234-F-56" not in raw_db_value
        assert "Organic Tomatoes" not in raw_db_value
    
    # Decrypt via application API
    receipts = get_customer_receipts(user)
    assert len(receipts) >= 1
    target_rcv = next((r for r in receipts if r["id"] == archived["id"]), None)
    assert target_rcv is not None
    assert target_rcv["receipt_data"]["confidential_customer_id"] == "NAT-ID-78-901234-F-56"
    assert target_rcv["receipt_data"]["total_due_usd"] == 45.00

def test_04_data_node_storage_aes_256_gcm_encryption_at_rest(tmp_path):
    """Verify DataNodeStorage encrypts kv_records with AES-256-GCM on disk."""
    temp_dir = str(tmp_path)
    storage = DataNodeStorage(temp_dir)
    
    test_payload = json.dumps({
        "product_name": "Solar Battery Inverter 5kVA",
        "wholesale_cost": 1250.00,
        "secret_supplier": "Harare Solar Distributors"
    })
    
    storage.put_record("inventory_backup", "item-solar-01", test_payload)
    
    # Inspect raw SQLite database on disk
    db_path = os.path.join(temp_dir, "data_node.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT data_json FROM kv_records WHERE record_key = 'item-solar-01'")
    raw_disk_data = cursor.fetchone()[0]
    conn.close()
    
    # Raw disk data must be encrypted with ENC: prefix
    assert raw_disk_data.startswith("ENC:")
    assert "Harare Solar Distributors" not in raw_disk_data
    assert "1250.00" not in raw_disk_data
    
    # Retrieval must transparently decrypt
    retrieved = storage.get_record("inventory_backup", "item-solar-01")
    assert retrieved is not None
    parsed = json.loads(retrieved)
    assert parsed["secret_supplier"] == "Harare Solar Distributors"
    assert parsed["wholesale_cost"] == 1250.00

def test_05_database_operator_profiles_and_visitors_encryption_at_rest():
    """Verify operator profile PII and visitor records are encrypted at rest with AES-256-GCM in SQLite."""
    # 1. Update user profile with confidential PII
    update_user_profile(
        user_id=1,
        full_name="Peter Mthokozisi Dube",
        phone="+263 77 987 6543",
        email="peter.dube@sovereign-node.zw",
        avatar_url="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
    )
    
    # Direct raw disk inspection of SQLite users table
    with get_db() as db:
        raw_user = db.execute("SELECT full_name, phone, email, avatar_url FROM users WHERE id = 1").fetchone()
        assert raw_user is not None
        
        # Raw columns in SQLite MUST be ciphertext with ENC: prefix
        assert raw_user["full_name"].startswith("ENC:")
        assert raw_user["phone"].startswith("ENC:")
        assert raw_user["email"].startswith("ENC:")
        assert raw_user["avatar_url"].startswith("ENC:")
        
        # Plaintext must NOT exist in raw SQLite storage
        assert "Peter Mthokozisi Dube" not in raw_user["full_name"]
        assert "+263 77 987 6543" not in raw_user["phone"]
        assert "peter.dube@sovereign-node.zw" not in raw_user["email"]

    # Authenticated retrieval via get_user_profile must transparently decrypt
    profile = get_user_profile(1)
    assert profile["full_name"] == "Peter Mthokozisi Dube"
    assert profile["phone"] == "+263 77 987 6543"
    assert profile["email"] == "peter.dube@sovereign-node.zw"
    
    # 2. Check in a security visitor with confidential national ID and purpose
    vis = checkin_visitor(
        national_id="ZW-63-987123-K-44",
        full_name="Nomathemba Ndlovu",
        destination_env="Data Center Vault Alpha",
        purpose="Hardware Security Key Provisioning",
        escort_officer="Officer Sibanda",
        logged_by="admin",
        notes="Classified security auditor entry"
    )
    vis_id = vis["id"]
    
    # Direct raw disk inspection of security_visitor_logs table
    with get_db() as db:
        raw_vis = db.execute("SELECT national_id, full_name, destination_env, purpose, escort_officer, notes FROM security_visitor_logs WHERE id = ?", (vis_id,)).fetchone()
        assert raw_vis is not None
        
        # Raw values MUST be ciphertext
        assert raw_vis["national_id"].startswith("ENC:")
        assert raw_vis["full_name"].startswith("ENC:")
        assert raw_vis["destination_env"].startswith("ENC:")
        assert raw_vis["purpose"].startswith("ENC:")
        assert raw_vis["notes"].startswith("ENC:")
        
        # Plaintext must NOT appear in raw database file
        assert "ZW-63-987123-K-44" not in raw_vis["national_id"]
        assert "Nomathemba Ndlovu" not in raw_vis["full_name"]
        assert "Classified security auditor entry" not in raw_vis["notes"]
        
    # Authenticated retrieval via list_visitors
    visitors = list_visitors(search="Nomathemba")
    assert len(visitors) >= 1
    found_vis = next(v for v in visitors if v["id"] == vis_id)
    assert found_vis["national_id"] == "ZW-63-987123-K-44"
    assert found_vis["full_name"] == "Nomathemba Ndlovu"
    assert found_vis["destination_env"] == "Data Center Vault Alpha"

def test_06_database_businesses_encryption_at_rest():
    """Verify business store operational and contact details are encrypted at rest in SQLite."""
    biz = create_business(
        name="Umguza Sovereign Agro Hub",
        owner_username="admin",
        tagline="Certified Organic Superfood Node",
        description="Encrypted Agro Farm Data",
        contact_phone="+263 71 234 5678",
        contact_email="vault@umguza.zw",
        location_address="Umguza Plot 24, Matabeleland North",
        tax_id="TAX-SOVEREIGN-2026-99",
        receipt_header="Umguza Certified Sovereign Vault",
        receipt_footer_note="Confidential Node Receipt"
    )
    biz_id = biz["id"]
    
    # Direct raw disk inspection of businesses table
    with get_db() as db:
        raw_biz = db.execute("SELECT tagline, description, contact_phone, contact_email, location_address, tax_id, receipt_header, receipt_footer_note FROM businesses WHERE id = ?", (biz_id,)).fetchone()
        assert raw_biz is not None
        
        # Raw fields in SQLite on disk MUST be ciphertext
        assert raw_biz["tagline"].startswith("ENC:")
        assert raw_biz["description"].startswith("ENC:")
        assert raw_biz["contact_phone"].startswith("ENC:")
        assert raw_biz["contact_email"].startswith("ENC:")
        assert raw_biz["location_address"].startswith("ENC:")
        assert raw_biz["tax_id"].startswith("ENC:")
        assert raw_biz["receipt_header"].startswith("ENC:")
        assert raw_biz["receipt_footer_note"].startswith("ENC:")
        
        # Plaintext must NOT appear in raw database file
        assert "Certified Organic Superfood Node" not in raw_biz["tagline"]
        assert "+263 71 234 5678" not in raw_biz["contact_phone"]
        assert "Umguza Plot 24" not in raw_biz["location_address"]
        assert "TAX-SOVEREIGN-2026-99" not in raw_biz["tax_id"]
        
    # Authenticated retrieval
    retrieved = get_business_by_id(biz_id)
    assert retrieved["tagline"] == "Certified Organic Superfood Node"
    assert retrieved["contact_phone"] == "+263 71 234 5678"
    assert retrieved["location_address"] == "Umguza Plot 24, Matabeleland North"
    assert retrieved["tax_id"] == "TAX-SOVEREIGN-2026-99"

