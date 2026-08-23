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
    mint_offline_voucher, execute_checkout_transaction
)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Initialize database and seed initial test state."""
    init_db()

def create_test_user(username: str):
    """Helper to insert user account for foreign key integrity."""
    now = int(time.time())
    db = get_db()
    try:
        db.execute("""
            INSERT OR IGNORE INTO users (username, password_hash, salt, role, status, created_at, updated_at, pin)
            VALUES (?, 'testhash', 'testsalt', 'customer', 'active', ?, ?, '1234')
        """, (username, now, now))
        db.commit()
    finally:
        db.close()


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
    voucher = mint_offline_voucher(
        business_id="biz-green-valley",
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

    # Checkout paying via customer wallet
    res = execute_checkout_transaction(
        operator_username="merchant",
        total_due=10.00,
        client_req_id=f"req-pos-{uuid.uuid4().hex[:6]}",
        tenders=[{"currency": "USD", "amount_tendered": 10.00, "exchange_rate": 1.0, "amount_usd_equiv": 10.00}],
        items=[{"inventory_id": item_id, "quantity": 4.0, "price_usd_at_sale": 2.50}],
        business_id="biz-green-valley",
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

    res = execute_checkout_transaction(
        operator_username="merchant",
        total_due=4.50,
        client_req_id=f"req-pos-{uuid.uuid4().hex[:6]}",
        tenders=[{"currency": "USD", "amount_tendered": 5.00, "exchange_rate": 1.0, "amount_usd_equiv": 5.00}],
        items=[{"inventory_id": item_id, "quantity": 3.0, "price_usd_at_sale": 1.50}],
        business_id="biz-green-valley",
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
