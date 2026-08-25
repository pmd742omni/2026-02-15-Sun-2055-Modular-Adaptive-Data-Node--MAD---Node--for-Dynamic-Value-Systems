"""
Automated Test Suite for Customer Digital Banking, Wallet Ledgers & Receipt Vault.
"""

import os
import sys
import uuid
import time
import pytest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

from database import (
    init_db, get_db,
    create_business, add_inventory_item,
    create_wallet_for_user, get_wallet_by_username,
    topup_wallet, execute_wallet_transfer,
    deposit_voucher_to_wallet, get_wallet_ledger,
    archive_customer_receipt, get_customer_receipts,
    mint_offline_voucher, execute_checkout_transaction,
    get_all_currencies, add_currency, update_currency, delete_currency,
    search_global_currency_catalog, get_global_currency_by_code, validate_currency_code_collision, sync_global_currencies_from_data_node
)

def create_test_user(username: str, role: str = "customer"):
    """Helper to insert user account for foreign key integrity."""
    now = int(time.time())
    db = get_db()
    try:
        db.execute("""
            INSERT OR IGNORE INTO users (username, password_hash, salt, role, status, created_at, updated_at, pin)
            VALUES (?, 'testhash', 'testsalt', ?, 'active', ?, ?, '1234')
        """, (username, role, now, now))
        db.commit()
    finally:
        db.close()

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Initialize database and seed initial test state."""
    init_db()
    create_test_user("merchant", "merchant")


def test_customer_wallet_creation_and_balances():
    """Verify wallet auto-provisioning and default balances."""
    user = f"cust_{uuid.uuid4().hex[:6]}"
    create_test_user(user)

    wallet = create_wallet_for_user(user)

    assert wallet["username"] == user
    assert wallet["account_number"].startswith("ACC-2026-")
    assert wallet["balance_usd"] == 0.0
    assert wallet["balance_zar"] == 0.0
    assert wallet["balance_zwg"] == 0.0


def test_wallet_topup_and_ledger_hmac():
    """Verify wallet deposits, ledger balance math, and HMAC signature integrity."""
    user = f"cust_{uuid.uuid4().hex[:6]}"
    create_test_user(user)

    wallet = get_wallet_by_username(user)

    # 1. Topup USD
    res_usd = topup_wallet(user, "USD", 100.00, notes="Cash Deposit", performed_by="merchant")
    assert res_usd["new_balance"] == 100.00

    # 2. Topup ZAR
    res_zar = topup_wallet(user, "ZAR", 500.00, notes="ZAR Topup", performed_by="merchant")
    assert res_zar["new_balance"] == 500.00

    # 3. Check wallet balances
    updated = get_wallet_by_username(user)
    assert updated["balance_usd"] == 100.00
    assert updated["balance_zar"] == 500.00

    # 4. Check ledger history
    ledger = get_wallet_ledger(user)
    assert len(ledger) >= 2
    assert any(e["currency"] == "USD" and e["amount"] == 100.00 for e in ledger)
    assert any(e["currency"] == "ZAR" and e["amount"] == 500.00 for e in ledger)


def test_wallet_p2p_transfer():
    """Verify atomic P2P fund transfer between customer accounts."""
    sender = f"snd_{uuid.uuid4().hex[:6]}"
    receiver = f"rcv_{uuid.uuid4().hex[:6]}"
    create_test_user(sender)
    create_test_user(receiver)

    topup_wallet(sender, "USD", 50.00)
    topup_wallet(receiver, "USD", 10.00)

    # Transfer $25 USD from sender to receiver
    res = execute_wallet_transfer(sender, receiver, "USD", 25.00, notes="Split bill")
    assert res["status"] == "success"
    assert res["sender_new_balance"] == 25.00

    # Check updated balances
    s_w = get_wallet_by_username(sender)
    r_w = get_wallet_by_username(receiver)
    assert s_w["balance_usd"] == 25.00
    assert r_w["balance_usd"] == 35.00


def test_voucher_to_wallet_deposit():
    """Verify offline QR bearer voucher converted directly into liquid customer bank balance."""
    user = f"cust_{uuid.uuid4().hex[:6]}"
    create_test_user(user)
    topup_wallet(user, "ZWG", 10.00)

    # Mint a change voucher
    biz = create_business(f"Banking Store {uuid.uuid4().hex[:6]}", "Retail", owner_username="merchant")
    voucher = mint_offline_voucher(
        business_id=biz["id"],
        value_amount=150.00,
        currency="ZWG",
        issued_by_node_id="node-vault-01"
    )

    # Deposit voucher into customer wallet
    res = deposit_voucher_to_wallet(user, voucher["vid"])
    assert res["success"] is True
    assert res["amount_credited"] == 150.00
    assert res["new_balance"] == 160.00

    # Verify voucher is marked redeemed
    with get_db() as db:
        v_row = db.execute("SELECT status FROM vouchers WHERE vid = ?", (voucher["vid"],)).fetchone()
        assert v_row["status"] == "redeemed"


def test_pos_checkout_via_wallet_payment():
    """Verify direct POS checkout debited against customer bank account balance."""
    customer = f"cust_{uuid.uuid4().hex[:6]}"
    create_test_user(customer)
    topup_wallet(customer, "USD", 40.00)

    # Add unique item
    u_suffix = uuid.uuid4().hex[:4]
    item_id = add_inventory_item(f"Organic Avocados {u_suffix}", f"SKU-AVO-{u_suffix}", 50.0, "kg", 2.50, 5.0, "merchant")
    biz = create_business(f"POS Farm {uuid.uuid4().hex[:6]}", "Horticulture", owner_username="merchant")

    # Checkout paying via customer wallet
    res = execute_checkout_transaction(
        operator_username="merchant",
        total_due=10.00,
        client_req_id=f"req-pos-{uuid.uuid4().hex[:6]}",
        tenders=[{"currency": "USD", "amount_tendered": 10.00, "exchange_rate": 1.0, "amount_usd_equiv": 10.00}],
        items=[{"inventory_id": item_id, "quantity": 4.0, "price_usd_at_sale": 2.50}],
        business_id=biz["id"],
        customer_username=customer,
        payment_method="wallet"
    )

    assert res["status"] == "success"
    assert res["customer_username"] == customer
    assert res["payment_method"] == "wallet"

    # Verify customer wallet balance decremented
    w = get_wallet_by_username(customer)
    assert w["balance_usd"] == 30.00


def test_customer_receipt_vault_storage_and_lookup():
    """Verify permanent digital receipt archiving and keyword lookup in customer vault."""
    customer = f"cust_{uuid.uuid4().hex[:6]}"
    create_test_user(customer)
    topup_wallet(customer, "USD", 50.00)

    # Make purchase
    u_suffix = uuid.uuid4().hex[:4]
    crop_name = f"Sweet Potatoes {u_suffix}"
    item_id = add_inventory_item(crop_name, f"SKU-POT-{u_suffix}", 100.0, "kg", 1.50, 10.0, "merchant")
    biz = create_business(f"Vault Farm {uuid.uuid4().hex[:6]}", "Horticulture", owner_username="merchant")

    res = execute_checkout_transaction(
        operator_username="merchant",
        total_due=4.50,
        client_req_id=f"req-pos-{uuid.uuid4().hex[:6]}",
        tenders=[{"currency": "USD", "amount_tendered": 5.00, "exchange_rate": 1.0, "amount_usd_equiv": 5.00}],
        items=[{"inventory_id": item_id, "quantity": 3.0, "price_usd_at_sale": 1.50}],
        business_id=biz["id"],
        issue_voucher_change=True,
        voucher_change_amount=13.25,
        voucher_change_currency="ZWG",
        customer_username=customer,
        payment_method="cash"
    )

    # Retrieve receipts from customer's vault
    receipts = get_customer_receipts(customer)
    assert len(receipts) >= 1
    rcv = receipts[0]
    assert rcv["customer_username"] == customer
    assert rcv["total_due_usd"] == 4.50
    assert crop_name in rcv["receipt_json"]
    assert "vouch-" in rcv["receipt_json"]


def test_dynamic_currencies_and_virtual_tokens():
    """Verify registration, exchange rate updating, and top-up/transfer in custom virtual tokens."""
    # 1. Check default currencies include ZiG (ZWG)
    currs = get_all_currencies()
    codes = [c["code"] for c in currs]
    assert "USD" in codes
    assert "ZAR" in codes
    assert "ZWG" in codes

    zwg_info = next(c for c in currs if c["code"] == "ZWG")
    assert zwg_info["name"] == "Zimbabwe Gold (ZiG)"
    assert zwg_info["symbol"] == "ZiG"
    assert zwg_info["currency_type"] == "gold_backed"

    # 2. Register custom virtual token
    token_code = f"ECO_{uuid.uuid4().hex[:4].upper()}"
    new_curr = add_currency(
        code=token_code,
        name="Eco Community Point",
        symbol="🌱",
        exchange_rate_to_usd=10.0,
        currency_type="virtual_token",
        performed_by="admin"
    )
    assert new_curr["code"] == token_code
    assert new_curr["exchange_rate_to_usd"] == 10.0

    # 3. Create users and test wallet operations with the new token
    user1 = f"eco_user1_{uuid.uuid4().hex[:4]}"
    user2 = f"eco_user2_{uuid.uuid4().hex[:4]}"
    create_test_user(user1)
    create_test_user(user2)

    # Topup ECO tokens
    topup_res = topup_wallet(user1, token_code, 500.0, notes="Community award", performed_by="admin")
    assert topup_res["amount_deposited"] == 500.0
    assert topup_res["new_balance"] == 500.0

    w1 = get_wallet_by_username(user1)
    assert w1["balances"][token_code] == 500.0

    # P2P transfer in ECO tokens
    xfer_res = execute_wallet_transfer(user1, user2, token_code, 150.0, notes="Farm labor exchange")
    assert xfer_res["status"] == "success"
    assert xfer_res["sender_new_balance"] == 350.0

    w1_after = get_wallet_by_username(user1)
    w2_after = get_wallet_by_username(user2)
    assert w1_after["balances"][token_code] == 350.0
    assert w2_after["balances"][token_code] == 150.0

    # 4. Update exchange rate
    upd_res = update_currency(token_code, exchange_rate_to_usd=12.5, performed_by="admin")
    assert upd_res["exchange_rate_to_usd"] == 12.5


def test_world_currency_catalog_and_collision_prevention():
    """Verify ISO 4217 world fiat, cryptocurrency catalog search, and multi-tier collision detection."""
    # 1. Verify global catalog seeded
    catalog = search_global_currency_catalog(limit=150)
    assert len(catalog) >= 50
    codes = [c["code"] for c in catalog]
    assert "EUR" in codes
    assert "GBP" in codes
    assert "BTC" in codes
    assert "ETH" in codes
    assert "BWP" in codes

    # 2. Search catalog by keyword
    pula_results = search_global_currency_catalog("Botswana")
    assert len(pula_results) >= 1
    assert pula_results[0]["code"] == "BWP"

    crypto_results = search_global_currency_catalog(category="crypto")
    assert any(c["code"] == "BTC" for c in crypto_results)

    # 3. Collision Validation: Active Local Currency
    val_usd = validate_currency_code_collision("USD")
    assert val_usd["collision"] is True
    assert val_usd["collision_type"] == "EXISTING_ACTIVE_CURRENCY"

    # 4. Collision Validation: Official Sovereign ISO 4217 Fiat (EUR)
    val_eur = validate_currency_code_collision("EUR")
    assert val_eur["collision"] is True
    assert val_eur["collision_type"] == "OFFICIAL_ISO_FIAT"
    assert val_eur["can_adopt"] is True
    assert val_eur["suggested_name"] == "Euro"
    assert val_eur["suggested_symbol"] == "€"

    # 5. Collision Validation: Major Cryptocurrency (BTC)
    val_btc = validate_currency_code_collision("BTC")
    assert val_btc["collision"] is True
    assert val_btc["collision_type"] == "MAJOR_CRYPTO"
    assert val_btc["can_adopt"] is True
    assert val_btc["suggested_name"] == "Bitcoin"
    assert val_btc["suggested_symbol"] == "₿"

    # 6. Collision Validation: Unique Custom Community Token
    unique_tok = f"LABOR_{uuid.uuid4().hex[:4].upper()}"
    val_unique = validate_currency_code_collision(unique_tok)
    assert val_unique["collision"] is False
    assert val_unique["collision_type"] == "UNIQUE_AVAILABLE"


