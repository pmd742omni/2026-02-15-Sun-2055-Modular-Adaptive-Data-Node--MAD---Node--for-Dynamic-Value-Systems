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
    add_inventory_item
)
from main import app

@pytest.fixture(scope="module")
def auth_session():
    client = TestClient(app)
    # Perform standard operator login
    login_res = client.post("/api/auth/login", json={"username": "admin", "password": "AdminPass123!"})
    assert login_res.status_code == 200
    token = login_res.json()["session_token"]
    headers = {"Authorization": f"Bearer {token}"}
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
