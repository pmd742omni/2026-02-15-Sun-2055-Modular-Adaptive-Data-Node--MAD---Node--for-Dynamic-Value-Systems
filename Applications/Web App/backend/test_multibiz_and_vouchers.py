"""
Automated Test Suite for Multi-Business (Multi-Tenant) Support,
Offline Cryptographic QR Vouchers, and Automatic Multi-Format PDF Receipt Generation.
"""

import os
import sys
import time
import json
import uuid
import pytest
from fastapi.testclient import TestClient

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

from main import app
from database import (
    init_db, get_db,
    create_business, get_all_businesses, get_business_by_id,
    mint_offline_voucher, verify_and_redeem_voucher, get_voucher_by_id,
    compute_voucher_hmac, generate_receipt_data, execute_checkout_transaction
)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Initialize database and seed initial test state."""
    init_db()


def test_multi_business_creation_and_scoping():
    """Verify registration, listing, and isolation of multiple businesses."""
    unique_name = f"Sunrise Poultry & Eggs {uuid.uuid4().hex[:6]}"
    biz = create_business(
        name=unique_name,
        category="Livestock & Poultry",
        contact_phone="+263 77 987 6543",
        location_address="Stand 44, Kensington Peri-Urban, Bulawayo",
        tax_id="ZW-POULT-5541",
        receipt_header="Sunrise Poultry - Fresh Eggs & Broilers",
        receipt_footer_note="High-protein, free-range local poultry!",
        currency_preference="USD",
        owner_username="merchant"
    )

    assert biz is not None
    assert biz["id"].startswith("biz-")
    assert biz["name"] == unique_name
    assert biz["category"] == "Livestock & Poultry"

    # Fetch list
    all_biz = get_all_businesses()
    assert any(b["id"] == biz["id"] for b in all_biz)

    # Fetch by ID
    fetched = get_business_by_id(biz["id"])
    assert fetched["name"] == unique_name


def test_offline_qr_voucher_minting_and_cryptographic_verification():
    """Verify offline bearer voucher minting with HMAC-SHA256 signature."""
    biz_id = "biz-green-valley"
    val = 75.50
    curr = "ZWG"

    # 1. Mint voucher
    voucher = mint_offline_voucher(
        business_id=biz_id,
        value_amount=val,
        currency=curr,
        issued_by_node_id="node-vault-bulawayo-01",
        validity_days=90
    )

    assert voucher["vid"].startswith("vouch-")
    assert voucher["value_amount"] == val
    assert voucher["currency"] == "ZWG"
    assert voucher["equivalent_usd"] == round(75.50 / 26.50, 2)
    assert voucher["status"] == "active"
    assert len(voucher["signature_hmac"]) == 64  # SHA256 hex string

    # 2. Verify signature correctness
    computed_sig = compute_voucher_hmac(
        voucher["vid"],
        biz_id,
        val,
        curr,
        voucher["expires_at_utc"]
    )
    assert voucher["signature_hmac"] == computed_sig

    # 3. Redeem voucher offline
    redeem_res = verify_and_redeem_voucher(voucher["vid"], business_id=biz_id)
    assert redeem_res["success"] is True
    assert redeem_res["status"] == "redeemed"


def test_voucher_double_spend_and_tamper_prevention():
    """Verify double-spend rejection and tamper detection."""
    biz_id = "biz-khumalo-millers"
    v = mint_offline_voucher(business_id=biz_id, value_amount=100.0, currency="ZWG")

    # First redemption succeeds
    r1 = verify_and_redeem_voucher(v["vid"], business_id=biz_id)
    assert r1["success"] is True

    # Second redemption fails (double spend prevention)
    r2 = verify_and_redeem_voucher(v["vid"], business_id=biz_id)
    assert r2["success"] is False
    assert "already redeemed" in r2["detail"]

    # Tampered voucher simulation
    with get_db() as db:
        tampered_vid = f"vouch-tamper-{uuid.uuid4().hex[:6]}"
        db.execute("""
            INSERT INTO vouchers (vid, business_id, value_amount, currency, equivalent_usd, issued_at_utc, expires_at_utc, issued_by_node_id, signature_hmac, status)
            VALUES (?, ?, 500.0, 'USD', 500.0, '2026-08-01T00:00:00Z', '2026-12-31T00:00:00Z', 'node-vault-01', 'fakehash1234567890abcdef', 'active')
        """, (tampered_vid, biz_id))

    r_tamper = verify_and_redeem_voucher(tampered_vid, business_id=biz_id)
    assert r_tamper["success"] is False
    assert "Cryptographic signature verification failed" in r_tamper["detail"]


def test_full_pos_checkout_with_voucher_change_and_receipt():
    """Verify end-to-end POS checkout with business scoping, voucher change, and receipt generation."""
    # 1. Create unique inventory item
    inv_id = str(uuid.uuid4())
    item_name = f"Grade-A Maize Meal {uuid.uuid4().hex[:4]}"
    unique_sku = f"MAIZE-BAG-{uuid.uuid4().hex[:6].upper()}"
    with get_db() as db:
        db.execute("""
            INSERT INTO inventory (id, name, sku, quantity, unit, price_usd, cost_price_usd, low_stock_threshold, business_id)
            VALUES (?, ?, ?, 50.0, 'bags', 4.50, 2.50, 5.0, 'biz-khumalo-millers')
        """, (inv_id, item_name, unique_sku))

    # 2. Perform checkout with $5 USD paid for a $4.50 item, requesting change as a 13.25 ZWG Voucher ($0.50 equiv)
    client_req_id = f"test-req-{uuid.uuid4().hex[:8]}"
    tenders = [{"currency": "USD", "amount_tendered": 4.50, "exchange_rate": 1.0, "amount_usd_equiv": 4.50}]
    items = [{"inventory_id": inv_id, "quantity": 1.0, "price_usd_at_sale": 4.50}]

    tx_res = execute_checkout_transaction(
        operator_username="merchant",
        total_due=4.50,
        client_req_id=client_req_id,
        tenders=tenders,
        items=items,
        business_id="biz-khumalo-millers",
        issue_voucher_change=True,
        voucher_change_amount=13.25,
        voucher_change_currency="ZWG"
    )

    assert tx_res["status"] == "success"
    assert tx_res["business_id"] == "biz-khumalo-millers"
    assert tx_res["voucher_issued"] is not None
    assert tx_res["voucher_issued"]["value_amount"] == 13.25
    assert tx_res["voucher_issued"]["currency"] == "ZWG"

    # 3. Generate receipt
    receipt = generate_receipt_data(tx_res["transaction_id"])
    assert receipt is not None
    assert receipt["business"]["id"] == "biz-khumalo-millers"
    assert receipt["business"]["name"] == "Khumalo Milling & Grains Co."
    assert len(receipt["items"]) == 1
    assert receipt["items"][0]["item_name"] == item_name
    assert receipt["voucher_issued"]["vid"] == tx_res["voucher_issued"]["vid"]
    assert len(receipt["audit_hash"]) == 64
