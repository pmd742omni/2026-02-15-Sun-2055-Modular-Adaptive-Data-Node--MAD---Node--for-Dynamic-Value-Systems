"""
Automated Test Suite for Hierarchical Multi-Tenant RBAC & Business Operator Delegation.
"""

import os
import sys
import uuid
import pytest
from fastapi.testclient import TestClient

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

from main import app
from database import (
    init_db, get_db, hash_password,
    create_business, get_all_businesses,
    assign_business_operator, get_business_operators,
    get_operator_permissions, revoke_business_operator,
    has_business_permission
)

def create_test_user(username: str, role: str = "customer"):
    import time
    with get_db() as db:
        cursor = db.execute("SELECT id FROM users WHERE username = ?", (username,))
        if not cursor.fetchone():
            now = int(time.time())
            salt_hex, hash_hex = hash_password("Password123!")
            db.execute("""
                INSERT OR IGNORE INTO users (username, password_hash, salt, role, status, created_at, updated_at, must_change_password, pin)
                VALUES (?, ?, ?, ?, 'active', ?, ?, 0, '1234')
            """, (username, hash_hex, salt_hex, role, now, now))

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Initialize database and seed initial test state."""
    init_db()
    create_test_user("merchant", "merchant")
    create_test_user("customer", "customer")
    create_test_user("agronomist", "agronomist")
    create_test_user("guard", "guard")


def test_assign_and_list_business_operators():
    """Verify business admin assigning custom operator with fine-grained permissions."""
    biz = create_business(
        name=f"Enterprise {uuid.uuid4().hex[:6]}",
        category="Horticulture",
        contact_phone="+263 77 111 2233",
        location_address="Bulawayo North",
        tax_id="ZW-ENT-001",
        receipt_header="Enterprise Test",
        receipt_footer_note="Testing footer",
        currency_preference="USD",
        owner_username="merchant"
    )
    biz_id = biz["id"]

    # 1. Assign 'customer' as Cashier with POS + Voucher permissions
    op = assign_business_operator(
        business_id=biz_id,
        username="customer",
        role_in_business="cashier",
        permissions=["pos", "vouchers"],
        granted_by="merchant"
    )

    assert op["username"] == "customer"
    assert op["role_in_business"] == "cashier"
    assert "pos" in op["permissions"]
    assert "vouchers" in op["permissions"]

    # 2. List operators for business
    ops = get_business_operators(biz_id)
    assert len(ops) >= 1
    found = next((o for o in ops if o["username"] == "customer"), None)
    assert found is not None
    assert found["role_in_business"] == "cashier"
    assert "pos" in found["permissions"]


def test_subsystem_permission_evaluation():
    """Verify granular permission checks: allowed subsystems pass, unassigned subsystems fail."""
    biz = create_business(
        name=f"Enterprise {uuid.uuid4().hex[:6]}",
        category="Grains",
        contact_phone="+263 77 444 5566",
        location_address="Tsholotsho",
        tax_id="ZW-GRAIN-002",
        receipt_header="Grain Test",
        receipt_footer_note="Testing footer",
        currency_preference="ZWG",
        owner_username="merchant"
    )
    biz_id = biz["id"]

    # Assign 'agronomist' with only 'agriculture' and 'social'
    assign_business_operator(
        business_id=biz_id,
        username="agronomist",
        role_in_business="agronomist",
        permissions=["agriculture", "social"],
        granted_by="merchant"
    )

    # 1. Check positive permissions
    assert has_business_permission("agronomist", biz_id, "agriculture") is True
    assert has_business_permission("agronomist", biz_id, "social") is True

    # 2. Check negative (unassigned) permissions
    assert has_business_permission("agronomist", biz_id, "pos") is False
    assert has_business_permission("agronomist", biz_id, "vouchers") is False
    assert has_business_permission("agronomist", biz_id, "security") is False

    # 3. Check Owner & Super Admin bypass
    assert has_business_permission("merchant", biz_id, "pos") is True
    assert has_business_permission("merchant", biz_id, "security") is True
    assert has_business_permission("admin", biz_id, "pos") is True
    assert has_business_permission("admin", biz_id, "vouchers") is True


def test_cross_business_operator_isolation():
    """Verify that operator permissions in Business A do not grant access to Business B."""
    biz_a_obj = create_business(name=f"Farm A {uuid.uuid4().hex[:6]}", category="Horticulture", contact_phone="", location_address="", tax_id="", receipt_header="", receipt_footer_note="", currency_preference="USD", owner_username="merchant")
    biz_b_obj = create_business(name=f"Farm B {uuid.uuid4().hex[:6]}", category="Dairy", contact_phone="", location_address="", tax_id="", receipt_header="", receipt_footer_note="", currency_preference="USD", owner_username="merchant")

    biz_a = biz_a_obj["id"]
    biz_b = biz_b_obj["id"]

    # Grant 'guard' access to Farm A only
    assign_business_operator(biz_a, "guard", "guard", ["security"], "merchant")

    assert has_business_permission("guard", biz_a, "security") is True
    # In Farm B, guard has zero permissions
    assert has_business_permission("guard", biz_b, "security") is False
    assert has_business_permission("guard", biz_b, "pos") is False


def test_revoke_business_operator_access():
    """Verify that revoking operator deactivates access immediately."""
    biz = create_business(name=f"Store Revoke {uuid.uuid4().hex[:6]}", category="Retail", contact_phone="", location_address="", tax_id="", receipt_header="", receipt_footer_note="", currency_preference="USD", owner_username="merchant")
    biz_id = biz["id"]

    assign_business_operator(biz_id, "customer", "cashier", ["pos", "vouchers"], "merchant")
    assert has_business_permission("customer", biz_id, "pos") is True

    # Revoke operator
    res = revoke_business_operator(biz_id, "customer", revoked_by="merchant")
    assert res is True

    # Now permission check must return False
    assert has_business_permission("customer", biz_id, "pos") is False
    assert has_business_permission("customer", biz_id, "vouchers") is False

    # Check active operators list
    ops = get_business_operators(biz_id)
    assert not any(o["username"] == "customer" for o in ops)
