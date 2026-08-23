"""
Automated Test Suite for MAD-Node Stage 1 Core:
- Decoupled Standalone Data Node & Multicast Discovery
- Agricultural Lifecycle, Itemized Cost Breakdown & Price Derivation
- Continuous Exponential Decay Pricing Math & Margin Floor Protection
- Security Visitor Gatekeeper Registry & Active Visitor Tracking
- Hybrid Social Media Hub (Threads, Carousels, 24h Stories, Reels) & Multi-Currency Tips
- Composable Enterprise Mixed-Tender Checkout & Change Algorithm
"""

import os
import sys
import time
import json
import uuid
import pytest
from fastapi.testclient import TestClient

# Ensure backend directory is in path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

DATA_NODE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "Data_Node"))
if DATA_NODE_DIR not in sys.path:
    sys.path.append(DATA_NODE_DIR)

from main import app
from database import (
    init_db, get_db,
    compute_production_cost_and_base_price,
    calculate_continuous_decay_price,
    calculate_mixed_tender_change,
    create_planting, list_plantings, log_production_costs, get_production_costs,
    log_harvest_and_sync_inventory, list_harvests, list_dispositions,
    checkin_visitor, checkout_visitor, list_visitors, get_active_visitors,
    create_social_post, list_social_posts, add_social_comment, get_social_comments, tip_social_post
)
from storage import DataNodeStorage
from beacon import BeaconBroadcaster, BeaconListener


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    init_db()


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------
# TEST 1: MATHEMATICAL ENGINES & COST DERIVATION
# ---------------------------------------------------------------------

def test_production_cost_and_base_price_math():
    costs = {
        "seeds": 20.0,
        "fertilizer": 35.0,
        "water": 25.0,
        "labor": 50.0,
        "pest": 10.0,
        "packaging": 15.0,
        "logistics": 15.0,
        "overhead": 10.0
    }
    # Total cost = 180.0
    # Harvest mass = 500kg, Self-consumption = 100kg -> Commercial mass = 400kg
    # Target markup = 100% (1.0)
    res = compute_production_cost_and_base_price(costs, mass_harvest_kg=500.0, mass_self_kg=100.0, target_markup_pct=1.0)
    assert res["total_cost_usd"] == 180.0
    assert res["mass_comm_kg"] == 400.0
    assert res["wholesale_cost_floor_usd"] == 0.45  # 180 / 400
    assert res["base_price_usd"] == 0.90  # 0.45 * 2.0


def test_continuous_exponential_decay_pricing_math():
    # Produce item: base_price = $2.00, cost_floor = $0.80, half_life = 2.0 days
    # Day 0 (Fresh)
    p0 = calculate_continuous_decay_price(
        base_price_usd=2.00, cost_floor_usd=0.80, half_life_days=2.0,
        harvest_time_iso=time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(time.time()))
    )
    assert p0["current_price_usd"] == 2.00
    assert p0["discount_pct"] == 0.0
    assert not p0["is_floor_active"]

    # Elapsed 2.0 days (1 half-life): Margin ($1.20) halved to $0.60 -> Price = $1.40
    two_days_ago = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(time.time() - (2 * 86400)))
    p2 = calculate_continuous_decay_price(
        base_price_usd=2.00, cost_floor_usd=0.80, half_life_days=2.0,
        harvest_time_iso=two_days_ago
    )
    assert abs(p2["current_price_usd"] - 1.40) <= 0.02
    assert abs(p2["discount_pct"] - 30.0) <= 1.0

    # Elapsed 30 days (High decay): Price must hit and not drop below cost floor ($0.80 * 1.05 = $0.84)
    old_date = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(time.time() - (30 * 86400)))
    p_old = calculate_continuous_decay_price(
        base_price_usd=2.00, cost_floor_usd=0.80, half_life_days=2.0,
        harvest_time_iso=old_date
    )
    assert p_old["current_price_usd"] >= 0.84
    assert p_old["is_floor_active"] is True


def test_mixed_tender_split_change_math():
    # Item Total: $10.00 USD
    # Tendered: $5.00 USD + 50.00 ZAR (at 18.5 ZAR/USD = $2.7027 USD) + 100.00 ZWG (at 26.5 ZWG/USD = $3.7735 USD)
    # Total paid = 5 + 2.7027 + 3.7735 = $11.4762 USD
    # Excess = $1.48 USD -> Change in ZWG = 1.48 * 26.5 = 39.22 ZWG
    res = calculate_mixed_tender_change(
        total_usd=10.00,
        tendered_usd=5.00,
        tendered_zar=50.00,
        tendered_zwg=100.00,
        rate_zar=18.5,
        rate_zwg=26.5
    )
    assert res["is_fully_paid"] is True
    assert res["total_paid_usd"] >= 11.47
    assert res["deficit_usd"] == 0.0
    assert res["change_usd"] > 1.40
    assert res["change_zwg"] > 35.0


# ---------------------------------------------------------------------
# TEST 2: AGRICULTURE LIFECYCLE & POS INVENTORY SYNC
# ---------------------------------------------------------------------

def test_agri_lifecycle_and_inventory_sync():
    # 1. Create planting
    p = create_planting(
        crop_variety="Sugar Cabbage",
        plot_bed_id="Bed 7 - South",
        planting_date_utc="2026-08-01T08:00:00Z",
        seeding_density=3.0,
        target_maturity_date_utc="2026-09-15T08:00:00Z",
        initial_soil_hydration_pct=72.0,
        created_by="agronomist",
        notes="High yield experimental variety"
    )
    assert p["id"].startswith("plant-")

    # 2. Log production costs
    costs = {
        "seeds": 15.0,
        "fertilizer": 25.0,
        "water": 20.0,
        "labor": 40.0,
        "pest": 5.0,
        "packaging": 10.0,
        "logistics": 10.0,
        "overhead": 5.0
    }
    c_res = log_production_costs(p["id"], costs, logged_by="agronomist")
    assert c_res["total_cost_usd"] == 130.0

    # 3. Log harvest and sync to POS inventory
    unique_crop = f"Sugar Cabbage {uuid.uuid4().hex[:6]}"
    h_res = log_harvest_and_sync_inventory(
        planting_id=p["id"],
        crop_name=unique_crop,
        harvest_date_utc="2026-08-20T10:00:00Z",
        mass_harvest_kg=300.0,
        quality_grade="Grade A",
        storage_location="Cold Room 2",
        mass_self_kg=50.0,
        target_markup_pct=0.80,
        shelf_life_half_life_days=3.0,
        logged_by="agronomist"
    )
    assert h_res["mass_comm_kg"] == 250.0
    assert h_res["wholesale_cost_floor_usd"] == 0.52  # 130 / 250
    assert h_res["base_price_usd"] == 0.94  # 0.52 * 1.80
    assert h_res["inventory_item_id"] is not None

    # 4. Verify in inventory
    with get_db() as db:
        cursor = db.execute("SELECT * FROM inventory WHERE id = ?", (h_res["inventory_item_id"],))
        inv = cursor.fetchone()
        assert inv is not None
        assert inv["quantity"] == 250.0
        assert inv["price_usd"] == 0.94
        assert inv["cost_price_usd"] == 0.52


# ---------------------------------------------------------------------
# TEST 3: SECURITY VISITOR GATEKEEPER
# ---------------------------------------------------------------------

def test_security_visitor_gatekeeper():
    # 1. Check in visitor
    v = checkin_visitor(
        national_id="08-987654-K-12",
        full_name="Sipho Ndlovu",
        destination_env="Farm Quadrant B",
        purpose="Soil Sampling Equipment Maintenance",
        escort_officer="Officer Dube",
        logged_by="guard",
        notes="Carrying tool chest"
    )
    assert v["status"] == "Active"
    vis_id = v["id"]

    # 2. Verify active visitor list
    active = get_active_visitors()
    assert any(x["id"] == vis_id for x in active)

    # 3. Check out visitor
    out_res = checkout_visitor(vis_id, logged_by="guard")
    assert out_res["status"] == "Checked-Out"
    assert out_res["time_out_utc"] is not None

    # 4. Verify no longer in active list
    active_after = get_active_visitors()
    assert not any(x["id"] == vis_id for x in active_after)


# ---------------------------------------------------------------------
# TEST 4: HYBRID SOCIAL MEDIA HUB
# ---------------------------------------------------------------------

def test_social_media_hub_crud_and_tipping():
    # 1. Create Thread post (X paradigm)
    post = create_social_post(
        post_type="thread",
        author="agronomist",
        content_text="Maize germination rate in Bed 1 reached 94% after optimal drip cycle!",
        tags=["maize", "irrigation"]
    )
    post_id = post["id"]

    # 2. Add comment
    comm = add_social_comment(post_id, author="merchant", comment_text="Excellent, reserve 50kg for POS.")
    assert comm["id"].startswith("comm-")

    comments = get_social_comments(post_id)
    assert len(comments) >= 1

    # 3. Send Tip
    tip_res = tip_social_post(post_id, sender="customer", currency="USD", amount=2.50)
    assert tip_res["amount"] == 2.50

    # 4. Verify post tips updated
    posts = list_social_posts()
    matching = next(p for p in posts if p["id"] == post_id)
    assert matching["tips_usd"] >= 2.50


# ---------------------------------------------------------------------
# TEST 5: STANDALONE DATA NODE STORAGE
# ---------------------------------------------------------------------

def test_standalone_data_node_storage(tmp_path):
    storage = DataNodeStorage(data_dir=str(tmp_path))
    stats = storage.get_storage_stats()
    assert stats["free_mb"] > 0

    # Write and read KV record
    test_data = json.dumps({"crop": "Tomatoes", "mass_kg": 450.0, "status": "stored"})
    storage.put_record("crops", "batch-101", test_data)

    retrieved = storage.get_record("crops", "batch-101")
    assert retrieved == test_data

    records = storage.list_records("crops")
    assert len(records) == 1
    assert records[0]["key"] == "batch-101"
