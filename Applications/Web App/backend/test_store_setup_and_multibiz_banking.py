import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, get_db
from main import app

@pytest.fixture(scope="module")
def auth_session():
    init_db()
    c = TestClient(app)
    # Authenticate as admin
    login_res = c.post("/api/auth/login", json={"username": "admin", "password": "Password123!"})
    assert login_res.status_code == 200
    csrf = login_res.cookies.get("csrf_token", "")
    headers = {"X-CSRF-Token": csrf}
    return c, headers


def test_01_store_setup_prerequisite_enforcement(auth_session):
    client, headers = auth_session
    
    # Check if any businesses exist; if not, inventory creation must be rejected
    res_biz = client.get("/api/businesses", headers=headers)
    assert res_biz.status_code == 200
    existing_businesses = res_biz.json().get("businesses", [])
    
    if len(existing_businesses) == 0:
        # Attempting to add inventory without any store must fail with HTTP 400
        res_inv = client.post("/api/inventory", json={
            "name": "Organic Tomatoes 1kg",
            "cost_price_usd": 0.80,
            "price_usd": 1.50,
            "quantity": 50,
            "unit": "kg"
        }, headers=headers)
        assert res_inv.status_code == 400
        assert "Store setup required" in res_inv.json()["detail"]


def test_02_modular_store_creation_and_banking_wallet_provisioning(auth_session):
    client, headers = auth_session
    
    # Register a modular store with full branding and contact attributes
    store_payload = {
        "name": "Umguza Valley Fresh Produce",
        "tagline": "Pure Organic Agricultural Produce Direct from Soil",
        "description": "Family-run agro-ecological farm specializing in fresh horticulture.",
        "category": "Horticulture & Fresh Produce",
        "currency_preference": "USD",
        "logo_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        "banner_url": "https://example.com/banner.jpg",
        "contact_phone": "+263 77 123 4567",
        "contact_email": "orders@umguzafarm.co.zw",
        "location_address": "Plot 14, Umguza Valley, Bulawayo",
        "tax_id": "ZW-2026-TAX-01",
        "website_url": "https://umguzafarm.co.zw",
        "operating_hours": "Mon-Sat: 07:30 - 17:30",
        "return_policy": "24-hour freshness replacement guarantee.",
        "receipt_header": "Umguza Farm Fresh Direct",
        "receipt_footer_note": "Siyabonga! Thank you for supporting local farmers!"
    }
    
    res = client.post("/api/businesses", json=store_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    biz = data["business"]
    assert biz["name"] == "Umguza Valley Fresh Produce"
    assert biz["tagline"] == "Pure Organic Agricultural Produce Direct from Soil"
    assert biz["bank_account_number"].startswith("BIZ-ACC-")
    
    # Check dedicated business banking accounts endpoint
    res_bank = client.get("/api/banking/business-accounts", headers=headers)
    assert res_bank.status_code == 200
    bank_data = res_bank.json()
    assert len(bank_data["accounts"]) >= 1
    
    acc = next(a for a in bank_data["accounts"] if a["business_id"] == biz["id"])
    assert acc["business_id"] == biz["id"]
    assert acc["account_number"] == biz["bank_account_number"]
    assert acc["account_type"] == "business"
    assert "USD" in acc["balances"]
    assert acc["balances"]["USD"] == 0.00  # Zero-seed balance rule verified


def test_03_multistore_inventory_pos_checkout_revenue_routing(auth_session):
    client, headers = auth_session
    
    # 1. Create Store A: Umguza Agro
    res_a = client.post("/api/businesses", json={
        "name": "Umguza Agro Hub",
        "tagline": "Organic vegetables and fruits",
        "description": "Vegetable farm",
        "category": "Horticulture & Fresh Produce",
        "currency_preference": "USD"
    }, headers=headers)
    assert res_a.status_code == 200
    biz_a = res_a.json()["business"]
    biz_a_id = biz_a["id"]
    
    # 2. Create Store B: Bulawayo Hardware & Seeds
    res_b = client.post("/api/businesses", json={
        "name": "Bulawayo Hardware & Seeds",
        "tagline": "Farming tools and drip irrigation",
        "description": "Machinery and seeds",
        "category": "Hardware & Farm Machinery",
        "currency_preference": "USD"
    }, headers=headers)
    assert res_b.status_code == 200
    biz_b = res_b.json()["business"]
    biz_b_id = biz_b["id"]
    
    # 3. Add inventory item to Store A
    res_item_a = client.post("/api/inventory", json={
        "business_id": biz_a_id,
        "name": "Organic Spinach Bunch",
        "cost_price_usd": 0.50,
        "price_usd": 1.20,
        "quantity": 100,
        "unit": "bunch",
        "category": "Fresh Vegetables"
    }, headers=headers)
    assert res_item_a.status_code == 200
    item_a_id = res_item_a.json()["item_id"]
    
    # 4. Add inventory item to Store B
    res_item_b = client.post("/api/inventory", json={
        "business_id": biz_b_id,
        "name": "Drip Irrigation Emitter 100-Pack",
        "cost_price_usd": 12.00,
        "price_usd": 20.00,
        "quantity": 30,
        "unit": "pack",
        "category": "Irrigation"
    }, headers=headers)
    assert res_item_b.status_code == 200
    item_b_id = res_item_b.json()["item_id"]
    
    # 5. Execute unified multi-store POS cart checkout
    # Cart contains: 5 bunches of Spinach from Store A ($6.00) + 1 pack of Drip Emitters from Store B ($20.00) = $26.00 total
    checkout_payload = {
        "business_id": biz_a_id, # checkout register node
        "cart_items": [
            {"id": item_a_id, "qty": 5},
            {"id": item_b_id, "qty": 1}
        ],
        "tendered_usd": 30.00,
        "tendered_zar": 0.00,
        "tendered_zwg": 0.00,
        "issue_voucher_change": False,
        "customer_username": "admin",
        "payment_method": "cash"
    }
    
    res_checkout = client.post("/api/pos/checkout", json=checkout_payload, headers=headers)
    assert res_checkout.status_code == 200
    checkout_data = res_checkout.json()
    assert checkout_data["status"] == "success"
    assert checkout_data["total_due_usd"] == 26.00
    
    # 6. Verify revenue routing to respective business bank accounts
    res_bank = client.get("/api/banking/business-accounts", headers=headers)
    assert res_bank.status_code == 200
    accounts_by_id = {acc["business_id"]: acc for acc in res_bank.json()["accounts"]}
    
    # Store A received 5 * $1.20 = $6.00
    assert accounts_by_id[biz_a_id]["balances"]["USD"] == 6.00
    # Store B received 1 * $20.00 = $20.00
    assert accounts_by_id[biz_b_id]["balances"]["USD"] == 20.00
    
    # 7. Check Store A Single Analytics
    res_analytics_a = client.get(f"/api/businesses/analytics?business_id={biz_a_id}&time_range=30d", headers=headers)
    assert res_analytics_a.status_code == 200
    a_a = res_analytics_a.json()["analytics"]
    assert a_a["gross_revenue_usd"] == 6.00
    assert a_a["total_cogs_usd"] == 2.50
    assert 58.0 <= a_a["gross_margin_pct"] <= 58.5
    assert a_a["units_sold_total"] == 5
    
    # 8. Check Store B Single Analytics
    res_analytics_b = client.get(f"/api/businesses/analytics?business_id={biz_b_id}&time_range=30d", headers=headers)
    assert res_analytics_b.status_code == 200
    a_b = res_analytics_b.json()["analytics"]
    assert a_b["gross_revenue_usd"] == 20.00
    assert a_b["total_cogs_usd"] == 12.00
    assert a_b["gross_margin_pct"] == 40.0
    assert a_b["units_sold_total"] == 1
    
    # 9. Check Aggregated Business Analytics (All Stores)
    res_analytics_all = client.get("/api/businesses/analytics?business_id=all&time_range=30d", headers=headers)
    assert res_analytics_all.status_code == 200
    a_all = res_analytics_all.json()["analytics"]
    assert a_all["gross_revenue_usd"] >= 26.00
    assert a_all["total_cogs_usd"] >= 14.50
    assert a_all["units_sold_total"] >= 6
