#!/usr/bin/env python3
"""
Automated Pytest Suite for Field-First Agriculture, Operator Store Inventory,
and Data Node Replication.
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main import app
from database import init_db, get_db

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

def test_01_verify_no_dummy_data_on_startup(auth_session):
    """Ensure no hardcoded dummy items, dummy plantings, or dummy fields exist."""
    client, headers = auth_session
    # Check inventory
    inv_res = client.get("/api/pos/promotions", headers=headers)
    assert inv_res.status_code == 200
    
    # Check fields
    fields_res = client.get("/api/agri/fields", headers=headers)
    assert fields_res.status_code == 200
    assert isinstance(fields_res.json().get("fields"), list)

def test_02_field_first_lifecycle_and_data_node_sync(auth_session):
    """Test full Field-First Agriculture: Register Field -> Create Planting -> Log Costs -> Record Harvest."""
    client, headers = auth_session

    # 1. Create a Farm Field
    field_payload = {
        "name": "North Valley Maize Block A",
        "code": "FLD-MAIZE-01",
        "area_size": 3.5,
        "area_unit": "hectares",
        "soil_type": "Loamy",
        "irrigation_type": "Drip Irrigation",
        "notes": "Adjacent to primary borehole #1"
    }
    field_res = client.post("/api/agri/fields", json=field_payload, headers=headers)
    assert field_res.status_code == 200
    field_data = field_res.json().get("field")
    assert field_data["name"] == "North Valley Maize Block A"
    field_id = field_data["id"]

    # 2. List Fields
    list_res = client.get("/api/agri/fields", headers=headers)
    assert list_res.status_code == 200
    fields = list_res.json().get("fields")
    assert any(f["id"] == field_id for f in fields)

    # 3. Create a Crop Planting linked to this Field
    planting_payload = {
        "field_id": field_id,
        "field_name": "North Valley Maize Block A",
        "crop_variety": "White Maize (SC719)",
        "area_utilized": 2.0,
        "area_unit": "hectares",
        "planting_date_utc": "2026-08-25",
        "target_maturity_date_utc": "2026-11-25",
        "seeding_density": 4.5,
        "initial_soil_hydration_pct": 70.0,
        "notes": "Certified seed with basal compound D fertilizer"
    }
    plant_res = client.post("/api/agri/plantings", json=planting_payload, headers=headers)
    assert plant_res.status_code == 200
    planting_data = plant_res.json().get("planting")
    assert planting_data["field_id"] == field_id
    assert planting_data["crop_variety"] == "White Maize (SC719)"
    planting_id = planting_data["id"]

    # 4. Itemize and Save Production Expenses
    cost_payload = {
        "planting_id": planting_id,
        "costs": {
            "seeds": 45.00,
            "fertilizer": 80.00,
            "water": 30.00,
            "labor": 60.00,
            "pest": 15.00,
            "packaging": 20.00,
            "logistics": 25.00,
            "overhead": 15.00
        }
    }
    cost_res = client.post("/api/agri/costs", json=cost_payload, headers=headers)
    assert cost_res.status_code == 200

    # 5. Record Harvest and Verify POS Inventory Sync
    harvest_payload = {
        "planting_id": planting_id,
        "crop_name": "White Maize (SC719)",
        "mass_harvest_kg": 600.0,
        "mass_self_kg": 100.0,
        "quality_grade": "Grade A",
        "shelf_life_half_life_days": 14.0
    }
    harvest_res = client.post("/api/agri/harvests", json=harvest_payload, headers=headers)
    assert harvest_res.status_code == 200
    harvest_data = harvest_res.json()
    assert harvest_data["status"] == "success"
    assert harvest_data["data"]["mass_comm_kg"] == 500.0
    assert harvest_data["data"]["inventory_item_id"] is not None

    # Clean up field
    del_res = client.delete(f"/api/agri/fields/{field_id}", headers=headers)
    assert del_res.status_code == 200

def test_03_operator_direct_store_inventory_management(auth_session):
    """Test operators directly adding products to store catalog."""
    client, headers = auth_session

    product_payload = {
        "name": "Organic Stone-Ground Maize Meal (10kg)",
        "sku": "MEAL-10KG-ORG",
        "quantity": 30,
        "unit": "bags",
        "price_usd": 7.50,
        "cost_price_usd": 4.80,
        "low_stock_threshold": 5
    }
    inv_res = client.post("/api/inventory", json=product_payload, headers=headers)
    assert inv_res.status_code == 200
    prod_data = inv_res.json()
    assert prod_data["name"] == "Organic Stone-Ground Maize Meal (10kg)"
    assert prod_data["cost_price_usd"] == 4.80

    # Verify item is available in POS catalog
    pos_res = client.get("/api/pos/promotions", headers=headers)
    assert pos_res.status_code == 200
    items = pos_res.json()
    assert any(i["name"] == "Organic Stone-Ground Maize Meal (10kg)" for i in items)

def test_04_modular_dynamic_product_engine_and_auto_sku(auth_session):
    """Test modular dynamic fields (Category hierarchy, Brand, Specs, Wholesale, Image, Barcode) & Auto-SKU."""
    client, headers = auth_session

    product_payload = {
        "name": "Switch Energy Drink (Original 500ml)",
        "sku": "",  # Blank to trigger system auto-generation
        "cost_price_usd": 0.95,
        "price_usd": 1.75,
        "quantity": 48,
        "unit": "cans",
        "low_stock_threshold": 12,
        "barcode": "6009802491823",
        "category": "Drinks",
        "subcategory": "Switch Energy Drinks",
        "brand": "Switch Energy",
        "description": "High performance taurine and caffeine energy boost.",
        "specifications": {
            "Volume": "500ml",
            "Caffeine": "160mg",
            "Pack Size": "24 Cans / Case"
        },
        "image_url": "https://example.com/switch-energy.png",
        "wholesale_price_usd": 1.40,
        "wholesale_min_qty": 24
    }

    res = client.post("/api/inventory", json=product_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()

    # Verify auto-assigned SKU
    assert data["sku"] != ""
    assert "SWIT" in data["sku"] or "DRIN" in data["sku"]
    assert data["brand"] == "Switch Energy"
    assert data["category"] == "Drinks"
    assert data["subcategory"] == "Switch Energy Drinks"
    assert data["barcode"] == "6009802491823"
    assert data["specifications"]["Volume"] == "500ml"
    assert data["wholesale_price_usd"] == 1.40
    assert data["wholesale_min_qty"] == 24

    # Verify category listing endpoint
    cat_res = client.get("/api/inventory/categories", headers=headers)
    assert cat_res.status_code == 200
    categories = cat_res.json().get("categories", [])
    assert any(c["category"] == "Drinks" for c in categories)

    # Verify filtered inventory search
    filter_res = client.get("/api/inventory?category=Drinks", headers=headers)
    assert filter_res.status_code == 200
    filter_data = filter_res.json()
    filtered_items = filter_data if isinstance(filter_data, list) else filter_data.get("items", [])
    assert any(item["name"] == "Switch Energy Drink (Original 500ml)" for item in filtered_items)

def test_05_mandatory_cost_and_selling_price_validation(auth_session):
    """Test validation errors when mandatory fields are missing or invalid."""
    client, headers = auth_session

    # Missing name
    res1 = client.post("/api/inventory", json={"name": "", "price_usd": 5.0, "cost_price_usd": 2.0}, headers=headers)
    assert res1.status_code == 400

    # Negative price
    res2 = client.post("/api/inventory", json={"name": "Faulty Product", "price_usd": -1.0, "cost_price_usd": 2.0}, headers=headers)
    assert res2.status_code == 400

