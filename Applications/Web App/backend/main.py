import os
import sys
import secrets
import time
import uuid
import json
import datetime
from fastapi import FastAPI, Request, Response, Depends, HTTPException, status, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

try:
    from .database import (
        get_db, init_db, write_audit_log, FORENSIC_MODE,
        get_calculator_config, get_all_calculator_configs, update_calculator_config,
        add_inventory_item, adjust_inventory_qty, log_wastage,
        execute_checkout_transaction, write_shift_handover, verify_shift_handover_chain,
        get_nodes_telemetry, update_node_position_lww, evaluate_agricultural_rules, calculate_pos_catalog_prices,
        track_device_activity, is_device_blocked, block_device, unblock_device, get_tracked_devices,
        compute_production_cost_and_base_price, calculate_continuous_decay_price, calculate_mixed_tender_change,
        create_planting, list_plantings, log_production_costs, get_production_costs,
        log_harvest_and_sync_inventory, list_harvests, list_dispositions,
        checkin_visitor, checkout_visitor, list_visitors, get_active_visitors,
        create_social_post, list_social_posts, add_social_comment, get_social_comments, tip_social_post,
        create_business, get_all_businesses, get_business_by_id,
        mint_offline_voucher, verify_and_redeem_voucher, get_voucher_by_id, generate_receipt_data,
        assign_business_operator, get_business_operators, get_operator_permissions, revoke_business_operator, has_business_permission,
        get_all_currencies, get_currency_by_code, add_currency, update_currency, delete_currency, sync_all_collections_to_data_nodes,
        search_global_currency_catalog, get_global_currency_by_code, validate_currency_code_collision, sync_global_currencies_from_data_node,
        create_wallet_for_user, get_wallet_by_username, topup_wallet, execute_wallet_transfer, deposit_voucher_to_wallet, get_wallet_ledger, archive_customer_receipt, get_customer_receipts,
        get_user_profile, update_user_profile, register_or_rotate_node_key, list_node_communication_keys, get_node_communication_key
    )
    from .node_discovery import discovery_manager
    from .auth_utils import (
        verify_password,
        hash_password,
        verify_totp,
        generate_session_token,
        hash_session_token,
        generate_totp_secret
    )
except ImportError:
    from database import (
        get_db, init_db, write_audit_log, FORENSIC_MODE,
        get_calculator_config, get_all_calculator_configs, update_calculator_config,
        add_inventory_item, adjust_inventory_qty, log_wastage,
        execute_checkout_transaction, write_shift_handover, verify_shift_handover_chain,
        get_nodes_telemetry, update_node_position_lww, evaluate_agricultural_rules, calculate_pos_catalog_prices,
        track_device_activity, is_device_blocked, block_device, unblock_device, get_tracked_devices,
        compute_production_cost_and_base_price, calculate_continuous_decay_price, calculate_mixed_tender_change,
        create_planting, list_plantings, log_production_costs, get_production_costs,
        log_harvest_and_sync_inventory, list_harvests, list_dispositions,
        checkin_visitor, checkout_visitor, list_visitors, get_active_visitors,
        create_social_post, list_social_posts, add_social_comment, get_social_comments, tip_social_post,
        create_business, get_all_businesses, get_business_by_id,
        mint_offline_voucher, verify_and_redeem_voucher, get_voucher_by_id, generate_receipt_data,
        assign_business_operator, get_business_operators, get_operator_permissions, revoke_business_operator, has_business_permission,
        get_all_currencies, get_currency_by_code, add_currency, update_currency, delete_currency, sync_all_collections_to_data_nodes,
        search_global_currency_catalog, get_global_currency_by_code, validate_currency_code_collision, sync_global_currencies_from_data_node,
        create_wallet_for_user, get_wallet_by_username, topup_wallet, execute_wallet_transfer, deposit_voucher_to_wallet, get_wallet_ledger, archive_customer_receipt, get_customer_receipts,
        get_user_profile, update_user_profile, register_or_rotate_node_key, list_node_communication_keys, get_node_communication_key
    )
    from node_discovery import discovery_manager
    from auth_utils import (
        verify_password,
        hash_password,
        verify_totp,
        generate_session_token,
        hash_session_token,
        generate_totp_secret
    )

# Add Applications root directory for node generator engine
APPS_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if APPS_ROOT_DIR not in sys.path:
    sys.path.append(APPS_ROOT_DIR)

try:
    from node_generator import generate_portable_node, list_exported_nodes
except ImportError:
    generate_portable_node = None
    list_exported_nodes = None

# Weak password list (common breached passwords checking)
WEAK_PASSWORDS = {
    "password", "password123", "adminpassword", "admin123456", "12345678", 
    "123456789", "qwertyuiop", "security123", "letmein123", "password1234"
}

# Timing attack dummy credential variables
DUMMY_SALT = "00000000000000000000000000000000"
DUMMY_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

app = FastAPI(
    title="MADN Offline Hub API",
    description="Offline-first API running locally on the Raspberry Pi 4 Vault hub.",
    version="1.1.0"
)

# Startup & Shutdown Initializations
@app.on_event("startup")
def startup_event():
    init_db()
    discovery_manager.start()

@app.on_event("shutdown")
def shutdown_event():
    discovery_manager.stop()

# Security Headers, Device Tracking & Content-Security-Policy (CSP) Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    client_ip = request.client.host if request.client else ""
    user_agent = request.headers.get("User-Agent", "")
    
    # 1. Device IP Blocking & Activity Tracking for API endpoints only (avoids serializing static asset delivery)
    if request.url.path.startswith("/api"):
        if client_ip and is_device_blocked(client_ip):
            return Response(
                content='{"detail": "Device access blocked by system administrator."}',
                status_code=403,
                media_type="application/json"
            )
            
        if client_ip:
            track_device_activity(client_ip, user_agent)

        # 2. If forensic mode is active, block all api requests except health checks
        if FORENSIC_MODE and request.url.path != "/api/health":
            return Response(
                content='{"detail": "Security System Integrity Compromised. Forensic Mode Active."}',
                status_code=500,
                media_type="application/json"
            )
        
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "frame-ancestors 'none';"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# CSRF Protection Validation on POST/PUT/DELETE
@app.middleware("http")
async def csrf_validation(request: Request, call_next):
    if request.method in ["POST", "PUT", "DELETE"] and request.url.path.startswith("/api"):
        # Bypass login/register/logout check if no cookie was issued yet or during session termination
        if request.url.path not in ["/api/auth/login", "/api/auth/register", "/api/auth/logout"]:
            cookie_csrf = request.cookies.get("csrf_token")
            header_csrf = request.headers.get("X-CSRF-Token")
            
            if not cookie_csrf or not header_csrf or not secrets.compare_digest(cookie_csrf, header_csrf):
                return Response(
                    content='{"detail": "CSRF Validation Failed. Missing or Mismatched Token."}',
                    status_code=403,
                    media_type="application/json"
                )
    return await call_next(request)

# Helper: Get current authenticated user
async def get_current_user(request: Request):
    session_token = request.cookies.get("madn_session")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    token_hash = hash_session_token(session_token)
    db = get_db()
    
    # Query session details
    cursor = db.execute("""
        SELECT s.token_hash, s.user_id, s.user_agent, s.ip_subnet, s.stepped_up_until,
               u.username, u.role, u.status, u.must_change_password
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.token_hash = ?
    """, (token_hash,))
    session = cursor.fetchone()
    
    if not session:
        db.close()
        raise HTTPException(status_code=401, detail="Session invalid or expired")
        
    # Check session timeout/expiry
    # (Optional: check last_seen_at for idle session timeouts - e.g. 15 minutes)
    
    # Session Fingerprint Validation (UA and /24 Subnet check)
    ua = request.headers.get("User-Agent", "")
    ip = request.client.host if request.client else "127.0.0.1"
    subnet = ".".join(ip.split(".")[:3])  # Coarse /24 IPv4
    
    if session["user_agent"] != ua or session["ip_subnet"] != subnet:
        # User fingerprint mismatch: invalidate session to prevent hijacking
        db.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
        db.commit()
        db.close()
        write_audit_log(session["username"], "HIJACK_ALERT", f"Fingerprint mismatch: UA '{ua}' / Subnet '{subnet}' vs Session '{session['user_agent']}' / '{session['ip_subnet']}'. Session terminated.")
        raise HTTPException(status_code=401, detail="Session fingerprint mismatch. Please log in again.")
        
    # Check status
    if session["status"] != "active":
        db.close()
        raise HTTPException(status_code=403, detail="Account is disabled or pending approval")
        
    db.close()
    return session

# Health Check Endpoint
@app.get("/api/health")
async def get_health():
    """Local node health check endpoint."""
    return {
        "status": "healthy" if not FORENSIC_MODE else "forensics_active",
        "mode": "offline-first",
        "database": "sqlite_connected"
    }

# --- AUTHENTICATION ENDPOINTS ---

class RegisterPayload(BaseModel):
    username: str
    password: str

class LoginPayload(BaseModel):
    username: str
    password: str
    mfa_token: Optional[str] = None
    totp_token: Optional[str] = None

@app.post("/api/auth/register")
async def register(payload: RegisterPayload, request: Request):
    username = payload.username.strip()
    password = payload.password
    
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password are required")
        
    if len(username) < 3 or not username.replace("_", "").isalnum():
        raise HTTPException(status_code=400, detail="Username must be at least 3 alphanumeric characters")

    if len(password) < 12:
        raise HTTPException(status_code=400, detail="Password must be at least 12 characters")
        
    if len(password) > 128:
        raise HTTPException(status_code=400, detail="Password exceeds maximum length (128 characters)")
        
    if password.lower() in WEAK_PASSWORDS:
        raise HTTPException(status_code=400, detail="Selected password is on the breached common list")
        
    db = get_db()
    cursor = db.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        db.close()
        raise HTTPException(status_code=400, detail="Username is already taken")
        
    salt_hex, hash_hex = hash_password(password)
    now = int(time.time())
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    db.execute("""
        INSERT INTO users (username, password_hash, salt, role, status, created_at, updated_at, must_change_password, pin)
        VALUES (?, ?, ?, 'customer', 'active', ?, ?, 0, '1234')
    """, (username, hash_hex, salt_hex, now, now))

    # Provision user multi-currency wallet
    acc = f"ACC-2026-{uuid.uuid4().hex[:6].upper()}"
    db.execute("""
        INSERT OR IGNORE INTO wallets (account_number, username, balance_usd, balance_zar, balance_zwg, created_at_utc, status)
        VALUES (?, ?, 0.00, 0.00, 0.00, ?, 'active')
    """, (acc, username, now_utc))

    db.commit()
    db.close()
    
    write_audit_log("SYSTEM", "REGISTER", f"Account '{username}' registered with active customer role and digital wallet provisioned.")
    return {"status": "success", "message": f"Account '{username}' registered successfully! You may now sign in.", "username": username}

@app.post("/api/auth/login")
async def login(payload: LoginPayload, request: Request, response: Response):
    username = payload.username.strip()
    password = payload.password
    mfa_token = (payload.totp_token or payload.mfa_token or "").strip()
    
    db = get_db()
    cursor = db.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    now = int(time.time())
    
    # 1. Timing-attack prevention: run dummy check if user not found
    if not user:
        verify_password(password, DUMMY_SALT, DUMMY_HASH)
        # Apply honey pot logic if target is 'system_root'
        if username == "system_root":
            client_ip = request.client.host if request.client else "unknown"
            write_audit_log("HONEYPOT", "SECURITY_ALERT", f"Breach attempt: Honey credentials login trigger for system_root from IP {client_ip}.")
        db.close()
        raise HTTPException(status_code=401, detail="Invalid username or password")
        
    # 2. Check lockout state
    if user["locked_until"] > now:
        remaining = user["locked_until"] - now
        db.close()
        raise HTTPException(
            status_code=403, 
            detail=f"Account is temporarily locked. Try again in {remaining} seconds."
        )
        
    # 3. Strict Scrypt Cryptographic Verification
    if not verify_password(password, user["salt"], user["password_hash"]):
        # Login failed: calculate exponential lockout delay
        failed_count = user["failed_login_count"] + 1
        lockout_duration = min(2 ** failed_count, 900)  # capped at 15 minutes
        locked_until = now + lockout_duration
        
        db.execute("""
            UPDATE users 
            SET failed_login_count = ?, locked_until = ? 
            WHERE id = ?
        """, (failed_count, locked_until, user["id"]))
        db.commit()
        db.close()
        
        write_audit_log(username, "LOGIN_FAILED", f"Invalid login attempt. Lockout set for {lockout_duration}s.")
        raise HTTPException(status_code=401, detail="Invalid username or password")
        
    # Check Status
    if user["status"] != "active":
        db.close()
        raise HTTPException(status_code=403, detail="Account status is not active (pending approval or suspended)")
        
    # 4. MFA check (if enabled)
    if user["mfa_secret"]:
        if not mfa_token:
            db.close()
            return {"mfa_required": True, "message": "Multi-Factor Authentication code required"}
            
        is_valid_totp, next_mfa_record = verify_totp(user["mfa_secret"], mfa_token, user["mfa_last_used_code"])
        if not is_valid_totp:
            db.close()
            write_audit_log(username, "MFA_FAILED", "MFA validation check failed.")
            raise HTTPException(status_code=401, detail="Invalid MFA Authenticator Code")
            
        # Persist TOTP token verification code for replay protection
        db.execute("UPDATE users SET mfa_last_used_code = ? WHERE id = ?", (next_mfa_record, user["id"]))
        db.commit()
        
    # Successful login: reset metrics
    db.execute("""
        UPDATE users 
        SET failed_login_count = 0, locked_until = 0, last_login_at = ? 
        WHERE id = ?
    """, (now, user["id"]))
    
    # 5. Create Session
    session_token = generate_session_token()
    token_hash = hash_session_token(session_token)
    
    ua = request.headers.get("User-Agent", "")
    ip = request.client.host if request.client else "127.0.0.1"
    subnet = ".".join(ip.split(".")[:3])
    
    # Session lifespan: 8 hours
    expires_at = now + 8 * 60 * 60
    
    db.execute("""
        INSERT INTO sessions (token_hash, user_id, user_agent, ip_subnet, created_at, last_seen_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (token_hash, user["id"], ua, subnet, now, now))
    db.commit()
    db.close()
    
    # Determine HTTPS security flag
    is_secure = (request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https" or os.environ.get("MADN_HTTPS_ENABLED") == "1")

    # Set secure HttpOnly cookies
    response.set_cookie(
        key="madn_session",
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=is_secure
    )
    
    # Set non-HttpOnly CSRF token cookie
    csrf_token = secrets.token_hex(16)
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        samesite="lax",
        secure=is_secure
    )
    
    write_audit_log(username, "LOGIN", "Successful login session created.")
    return {
        "username": user["username"],
        "role": user["role"],
        "must_change_password": user["must_change_password"],
        "mfa_enrolled": bool(user["mfa_secret"])
    }

@app.post("/api/auth/step-up")
async def step_up(request: Request, current_user = Depends(get_current_user)):
    body = await request.json()
    password = body.get("password", "")
    mfa_token = body.get("mfa_token", "").strip()
    
    db = get_db()
    cursor = db.execute("SELECT * FROM users WHERE id = ?", (current_user["user_id"],))
    user = cursor.fetchone()
    
    if not user or not verify_password(password, user["salt"], user["password_hash"]):
        db.close()
        write_audit_log(current_user["username"], "STEP_UP_FAILED", "Failed step-up auth attempt: invalid password.")
        raise HTTPException(status_code=401, detail="Invalid credential password")
        
    # Check MFA if configured
    if user["mfa_secret"]:
        if not mfa_token:
            db.close()
            raise HTTPException(status_code=400, detail="MFA Code required to elevate privileges")
        is_valid_totp, next_mfa_record = verify_totp(user["mfa_secret"], mfa_token, user["mfa_last_used_code"])
        if not is_valid_totp:
            db.close()
            raise HTTPException(status_code=401, detail="Invalid MFA Authenticator Code")
        db.execute("UPDATE users SET mfa_last_used_code = ? WHERE id = ?", (next_mfa_record, user["id"]))
        db.commit()
        
    # Elevate session for 5 minutes (300 seconds)
    elevated_until = int(time.time()) + 300
    db.execute("UPDATE sessions SET stepped_up_until = ? WHERE token_hash = ?", (elevated_until, current_user["token_hash"]))
    db.commit()
    db.close()
    
    write_audit_log(current_user["username"], "STEP_UP", "Session elevated for destructive operations.")
    return {"message": "Privileges elevated for 5 minutes."}

@app.api_route("/api/auth/logout", methods=["GET", "POST"])
async def logout(request: Request, response: Response):
    raw_token = request.cookies.get("madn_session")
    username = "unknown"
    if raw_token:
        try:
            token_hash = hash_session_token(raw_token)
            db = get_db()
            cursor = db.execute("SELECT u.username FROM sessions s JOIN users u ON s.user_id = u.id WHERE s.token_hash = ?", (token_hash,))
            row = cursor.fetchone()
            if row:
                username = row["username"]
            db.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
            db.commit()
            db.close()
            write_audit_log(username, "LOGOUT", "Session terminated by user.")
        except Exception:
            pass
    
    is_secure = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
    # Delete across both lax and strict samesite, and secure/insecure variants
    response.delete_cookie("madn_session", path="/", samesite="lax", secure=is_secure)
    response.delete_cookie("csrf_token", path="/", samesite="lax", secure=is_secure)
    response.delete_cookie("madn_session", path="/", samesite="lax", secure=False)
    response.delete_cookie("csrf_token", path="/", samesite="lax", secure=False)
    response.delete_cookie("madn_session", path="/", samesite="strict")
    response.delete_cookie("csrf_token", path="/", samesite="strict")
    return {"status": "success", "message": "Logged out successfully."}

@app.get("/api/network/info")
def get_network_info(request: Request):
    """Returns local network adapter IP addresses and reachable LAN URLs with HTTPS support."""
    import socket
    ips = set()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(0.2)
            s.connect(("8.8.8.8", 80))
            primary_ip = s.getsockname()[0]
            if primary_ip and not primary_ip.startswith("127."):
                ips.add(primary_ip)
    except Exception:
        pass

    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if ip and not ip.startswith("127."):
                ips.add(ip)
    except Exception:
        pass

    certs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "certs")
    has_tls = os.path.exists(os.path.join(certs_dir, "cert.pem")) or request.url.scheme == "https" or os.environ.get("MADN_HTTPS_ENABLED") == "1"
    scheme = "https" if has_tls else "http"

    local_ips = sorted(list(ips))
    network_urls = [f"{scheme}://{ip}:8000" for ip in local_ips]
    primary_url = network_urls[0] if network_urls else f"{scheme}://127.0.0.1:8000"

    return {
        "hostname": socket.gethostname(),
        "scheme": scheme,
        "localhost_url": f"{scheme}://127.0.0.1:8000",
        "primary_url": primary_url,
        "local_ips": local_ips,
        "network_urls": network_urls,
        "vault_port": 8000,
        "data_node_port": 8002,
        "beacon_multicast": "224.0.0.251:8001"
    }

@app.post("/api/auth/change-password")
async def change_password(request: Request, current_user = Depends(get_current_user)):
    body = await request.json()
    current_password = body.get("current_password", "")
    new_password = body.get("new_password", "")
    
    if len(new_password) < 12:
        raise HTTPException(status_code=400, detail="New password must be at least 12 characters")
        
    if new_password.lower() in WEAK_PASSWORDS:
        raise HTTPException(status_code=400, detail="Selected password is on the breached common list")
        
    db = get_db()
    cursor = db.execute("SELECT * FROM users WHERE id = ?", (current_user["user_id"],))
    user = cursor.fetchone()
    
    if not user or not verify_password(current_password, user["salt"], user["password_hash"]):
        db.close()
        raise HTTPException(status_code=401, detail="Invalid current password")
        
    # Verify password history (prevent reuse of last 3 passwords)
    cursor = db.execute("SELECT salt, password_hash FROM password_history WHERE user_id = ? ORDER BY created_at DESC LIMIT 3", (user["id"],))
    for hist in cursor.fetchall():
        if verify_password(new_password, hist["salt"], hist["password_hash"]):
            db.close()
            raise HTTPException(status_code=400, detail="Cannot reuse a recently used password")
            
    # Update password
    salt_hex, hash_hex = hash_password(new_password)
    now = int(time.time())
    
    db.execute("""
        UPDATE users 
        SET password_hash = ?, salt = ?, must_change_password = 0, updated_at = ? 
        WHERE id = ?
    """, (hash_hex, salt_hex, now, user["id"]))
    
    # Add to history
    db.execute("""
        INSERT INTO password_history (user_id, salt, password_hash, created_at)
        VALUES (?, ?, ?, ?)
    """, (user["id"], salt_hex, hash_hex, now))
    
    # Invalidate all other sessions for this user except current session
    db.execute("DELETE FROM sessions WHERE user_id = ? AND token_hash != ?", (user["id"], current_user["token_hash"]))
    db.commit()
    db.close()
    
    write_audit_log(current_user["username"], "PASSWORD_CHANGE", "Password successfully changed. Other sessions revoked.")
    return {"message": "Password changed successfully."}

@app.get("/api/auth/session")
async def check_session(current_user = Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "role": current_user["role"],
        "must_change_password": current_user["must_change_password"]
    }

class ProfileUpdatePayload(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    pin: Optional[str] = None

@app.get("/api/user/profile")
async def get_current_user_profile_endpoint(current_user = Depends(get_current_user)):
    """Fetches full profile, contact info, PIN status, and digital accounts for current authenticated operator."""
    profile = get_user_profile(current_user["user_id"])
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    return profile

@app.put("/api/user/profile")
async def update_current_user_profile_endpoint(payload: ProfileUpdatePayload, current_user = Depends(get_current_user)):
    """Updates contact details, PIN, and dynamic username for the authenticated operator."""
    try:
        updated = update_user_profile(
            user_id=current_user["user_id"],
            full_name=payload.full_name,
            phone=payload.phone,
            email=payload.email,
            new_username=payload.username,
            pin=payload.pin
        )
        return {"status": "success", "message": "Profile successfully updated", "profile": updated}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")

@app.put("/api/user/change-password")
async def update_password_alias(request: Request, current_user = Depends(get_current_user)):
    """Alias for PUT /api/user/change-password."""
    return await change_password(request, current_user)

# --- MFA QR/ENROLLMENT ENDPOINTS ---

@app.post("/api/auth/mfa/enroll")
async def enroll_mfa(current_user = Depends(get_current_user)):
    """Start MFA enrollment: generate TOTP secret base32 key."""
    # Enforce step-up validation
    db = get_db()
    cursor = db.execute("SELECT stepped_up_until FROM sessions WHERE token_hash = ?", (current_user["token_hash"],))
    session = cursor.fetchone()
    now = int(time.time())
    
    if not session or session["stepped_up_until"] < now:
        db.close()
        raise HTTPException(status_code=403, detail="Re-authentication required. Please step-up your session first.")
        
    secret = generate_totp_secret()
    db.close()
    return {"secret": secret, "qr_payload": f"otpauth://totp/MADN:{current_user['username']}?secret={secret}&issuer=MADN"}

@app.post("/api/auth/mfa/verify-enroll")
async def verify_enroll_mfa(request: Request, current_user = Depends(get_current_user)):
    """Complete MFA enrollment by verifying first code."""
    body = await request.json()
    secret = body.get("secret", "").strip()
    code = body.get("code", "").strip()
    
    # Enforce step-up
    db = get_db()
    cursor = db.execute("SELECT stepped_up_until FROM sessions WHERE token_hash = ?", (current_user["token_hash"],))
    session = cursor.fetchone()
    now = int(time.time())
    
    if not session or session["stepped_up_until"] < now:
        db.close()
        raise HTTPException(status_code=403, detail="Re-authentication required. Please step-up your session first.")
        
    is_valid, code_record = verify_totp(secret, code)
    if not is_valid:
        db.close()
        raise HTTPException(status_code=400, detail="Invalid verification code")
        
    db.execute("UPDATE users SET mfa_secret = ?, mfa_last_used_code = ? WHERE id = ?", (secret, code_record, current_user["user_id"]))
    db.commit()
    db.close()
    
    write_audit_log(current_user["username"], "MFA_ENROLLED", "MFA successfully configured on account.")
    return {"message": "MFA successfully enrolled."}

# --- ADMIN ENDPOINTS (Requires role = 'admin') ---

def require_admin(current_user = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Administrator permissions required")
    return current_user

def require_elevated_admin(request: Request, admin = Depends(require_admin)):
    """Verifies that the admin's session is currently stepped-up (within 5 min elevation)."""
    now = int(time.time())
    db = get_db()
    cursor = db.execute("SELECT stepped_up_until FROM sessions WHERE token_hash = ?", (admin["token_hash"],))
    session = cursor.fetchone()
    db.close()
    
    if not session or session["stepped_up_until"] < now:
        raise HTTPException(status_code=403, detail="This operation is destructive. Please elevate your session (step-up auth) first.")
    return admin

@app.get("/api/admin/users", dependencies=[Depends(require_admin)])
async def list_users():
    db = get_db()
    cursor = db.execute("SELECT id, username, role, status, created_at, last_login_at FROM users WHERE username != 'system_root'")
    users = [dict(row) for row in cursor.fetchall()]
    db.close()
    return users

@app.put("/api/admin/users/{user_id}/status")
async def update_user_status(user_id: int, request: Request, admin = Depends(require_elevated_admin)):
    body = await request.json()
    new_status = body.get("status", "")
    
    if new_status not in ["active", "disabled"]:
        raise HTTPException(status_code=400, detail="Invalid user status")
        
    # Self lockout protection
    if user_id == admin["user_id"]:
        raise HTTPException(status_code=400, detail="Self-lockout protection: Cannot disable your own account.")
        
    db = get_db()
    
    # Assert we are not disabling the last admin
    cursor = db.execute("SELECT role, username FROM users WHERE id = ?", (user_id,))
    target = cursor.fetchone()
    if not target:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")
        
    if target["role"] == "admin" and new_status == "disabled":
        cursor = db.execute("SELECT COUNT(*) as count FROM users WHERE role = 'admin' AND status = 'active'")
        active_admins = cursor.fetchone()["count"]
        if active_admins <= 1:
            db.close()
            raise HTTPException(status_code=400, detail="Cannot disable the last active administrator.")
            
    now = int(time.time())
    db.execute("UPDATE users SET status = ?, updated_at = ? WHERE id = ?", (new_status, now, user_id))
    
    # If disabling, immediately revoke all active sessions for that user
    if new_status == "disabled":
        db.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        
    db.commit()
    db.close()
    
    write_audit_log(admin["username"], f"USER_STATUS_{new_status.upper()}", f"Updated user ID {user_id} status to {new_status}.")
    return {"message": f"User status updated to {new_status}."}

@app.put("/api/admin/users/{user_id}/role")
async def update_user_role(user_id: int, request: Request, admin = Depends(require_elevated_admin)):
    body = await request.json()
    new_role = body.get("role", "")
    
    if new_role not in ["admin", "operator"]:
        raise HTTPException(status_code=400, detail="Invalid user role")
        
    # Self demotion protection
    if user_id == admin["user_id"]:
        raise HTTPException(status_code=400, detail="Self-lockout protection: Cannot demote yourself.")
        
    db = get_db()
    
    # Assert we are not demoting the last active admin
    cursor = db.execute("SELECT role FROM users WHERE id = ?", (user_id,))
    target = cursor.fetchone()
    if not target:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")
        
    if target["role"] == "admin" and new_role == "operator":
        cursor = db.execute("SELECT COUNT(*) as count FROM users WHERE role = 'admin' AND status = 'active'")
        active_admins = cursor.fetchone()["count"]
        if active_admins <= 1:
            db.close()
            raise HTTPException(status_code=400, detail="Cannot demote the last active administrator.")
            
    now = int(time.time())
    db.execute("UPDATE users SET role = ?, updated_at = ? WHERE id = ?", (new_role, now, user_id))
    db.commit()
    db.close()
    
    write_audit_log(admin["username"], f"USER_ROLE_{new_role.upper()}", f"Demoted/Promoted user ID {user_id} to {new_role}.")
    return {"message": f"User role updated to {new_role}."}

@app.put("/api/admin/users/{user_id}/reset-password")
async def reset_user_password(user_id: int, admin = Depends(require_elevated_admin)):
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    temp_pw = "".join(secrets.choice(alphabet) for _ in range(16))
    
    salt_hex, hash_hex = hash_password(temp_pw)
    now = int(time.time())
    
    db = get_db()
    # Confirm user exists
    cursor = db.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    target = cursor.fetchone()
    if not target:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")
        
    db.execute("""
        UPDATE users 
        SET password_hash = ?, salt = ?, must_change_password = 1, failed_login_count = 0, locked_until = 0, updated_at = ? 
        WHERE id = ?
    """, (hash_hex, salt_hex, now, user_id))
    
    # Invalidate all active sessions for that user
    db.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    db.commit()
    db.close()
    
    write_audit_log(admin["username"], "USER_PASSWORD_RESET", f"Reset password for user '{target['username']}' (ID: {user_id}). Forced change at next login.")
    return {
        "message": "User password reset successfully.",
        "temp_password": temp_pw
    }

@app.delete("/api/admin/users/{user_id}")
async def delete_user(user_id: int, admin = Depends(require_elevated_admin)):
    # Self deletion protection
    if user_id == admin["user_id"]:
        raise HTTPException(status_code=400, detail="Self-lockout protection: Cannot delete your own account.")
        
    db = get_db()
    
    # Confirm user exists
    cursor = db.execute("SELECT role, username FROM users WHERE id = ?", (user_id,))
    target = cursor.fetchone()
    if not target:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")
        
    # Assert we are not deleting the last admin
    if target["role"] == "admin":
        cursor = db.execute("SELECT COUNT(*) as count FROM users WHERE role = 'admin' AND status = 'active'")
        active_admins = cursor.fetchone()["count"]
        if active_admins <= 1:
            db.close()
            raise HTTPException(status_code=400, detail="Cannot delete the last active administrator.")
            
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    db.close()
    
    write_audit_log(admin["username"], "USER_DELETE", f"Permanently deleted user '{target['username']}' (ID: {user_id}).")
    return {"message": f"User '{target['username']}' deleted successfully."}

# --- ADMIN DEVICE MANAGEMENT ENDPOINTS ---

@app.get("/api/admin/devices", dependencies=[Depends(require_admin)])
async def list_tracked_devices():
    """List all tracked network devices and their block status."""
    return get_tracked_devices()

@app.post("/api/admin/devices/block")
async def block_device_endpoint(request: Request, admin = Depends(require_elevated_admin)):
    """Block a network device by IP address."""
    body = await request.json()
    ip_address = body.get("ip_address", "").strip()
    reason = body.get("reason", "Blocked by System Administrator").strip()
    
    if not ip_address:
        raise HTTPException(status_code=400, detail="Device IP address is required")
        
    current_ip = request.client.host if request.client else ""
    if current_ip and secrets.compare_digest(current_ip, ip_address):
        raise HTTPException(status_code=400, detail="Self-lockout protection: Cannot block the IP address of your active session.")
        
    block_device(ip_address, admin["username"], reason)
    return {"message": f"Device IP '{ip_address}' blocked successfully."}

@app.post("/api/admin/devices/unblock")
async def unblock_device_endpoint(request: Request, admin = Depends(require_elevated_admin)):
    """Unblock a network device by IP address."""
    body = await request.json()
    ip_address = body.get("ip_address", "").strip()
    
    if not ip_address:
        raise HTTPException(status_code=400, detail="Device IP address is required")
        
    unblock_device(ip_address, admin["username"])
    return {"message": f"Device IP '{ip_address}' unblocked successfully."}


@app.get("/api/admin/audit", dependencies=[Depends(require_admin)])
async def list_audit_logs():
    db = get_db()
    cursor = db.execute("SELECT id, seq, timestamp, actor, action, details, prev_hash, record_hash FROM audit_logs ORDER BY seq DESC LIMIT 200")
    logs = [dict(row) for row in cursor.fetchall()]
    db.close()
    return logs

# --- CYCLE 3: AGRICULTURE ESTIMATOR & CONFIGS ---

@app.get("/api/agriculture/config", dependencies=[Depends(get_current_user)])
async def list_calculator_configs():
    return get_all_calculator_configs()

@app.put("/api/agriculture/config", dependencies=[Depends(require_admin)])
async def update_config_value(request: Request, admin = Depends(require_admin)):
    body = await request.json()
    key = body.get("key", "").strip()
    value = body.get("value")
    
    if not key or value is None:
        raise HTTPException(status_code=400, detail="Key and value are required")
        
    try:
        val_float = float(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="Value must be a valid float")
        
    success = update_calculator_config(key, val_float, admin["username"])
    if not success:
        raise HTTPException(status_code=404, detail="Configuration key not found")
        
    return {"status": "success", "message": f"Updated key '{key}' to {val_float}"}

@app.post("/api/agriculture/estimator/calculate", dependencies=[Depends(get_current_user)])
async def calculate_estimator(request: Request, current_user = Depends(get_current_user)):
    body = await request.json()
    calc_type = body.get("type", "")
    inputs = body.get("inputs", {})
    
    if calc_type == "herd_feed":
        animal_count = int(inputs.get("animal_count", 0))
        average_weight = float(inputs.get("average_weight", 0))
        stage = inputs.get("stage", "dry_cow")
        
        stage_coeffs = {"lactating_dairy": 1.3, "dry_cow": 1.0, "calf": 0.5}
        coeff = stage_coeffs.get(stage, 1.0)
        
        feed_ratio = get_calculator_config("livestock_feed_ratio") or 0.03
        daily_feed = animal_count * average_weight * feed_ratio * coeff
        
        outputs = {"daily_feed_kg": round(daily_feed, 2)}
        snapshot = {"livestock_feed_ratio": feed_ratio}
        
    elif calc_type == "crop_yield":
        sq_footage = float(inputs.get("plot_square_footage", 0))
        soil = inputs.get("soil_class", "clay_loam")
        rainfall_anomaly = float(inputs.get("rainfall_anomaly", 0.0))
        
        soil_coeffs = {"clay_loam": 1.0, "sandy": 0.8, "silt": 0.9}
        coeff = soil_coeffs.get(soil, 1.0)
        
        yield_ratio = get_calculator_config("crop_yield_ratio") or 0.45
        rainfall_coeff = 1.0 + rainfall_anomaly
        
        estimated_yield = sq_footage * yield_ratio * coeff * rainfall_coeff
        
        outputs = {"estimated_yield_kg": round(estimated_yield, 2)}
        snapshot = {"crop_yield_ratio": yield_ratio}
    else:
        raise HTTPException(status_code=400, detail="Invalid calculation type")
        
    # Save to history
    run_id = str(uuid.uuid4())
    now = int(time.time())
    
    db = get_db()
    db.execute("""
        INSERT INTO estimator_runs (id, timestamp, type, inputs_json, outputs_json, config_snapshot_json)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (run_id, now, calc_type, json.dumps(inputs), json.dumps(outputs), json.dumps(snapshot)))
    db.commit()
    db.close()
    
    return {"status": "success", "id": run_id, "outputs": outputs}

@app.get("/api/agriculture/estimator/history", dependencies=[Depends(get_current_user)])
async def get_estimator_history():
    db = get_db()
    cursor = db.execute("SELECT id, timestamp, type, inputs_json, outputs_json, config_snapshot_json FROM estimator_runs ORDER BY timestamp DESC LIMIT 20")
    rows = cursor.fetchall()
    db.close()
    
    runs = []
    for r in rows:
        runs.append({
            "id": r["id"],
            "timestamp": r["timestamp"],
            "type": r["type"],
            "inputs": json.loads(r["inputs_json"]),
            "outputs": json.loads(r["outputs_json"]),
            "config_snapshot": json.loads(r["config_snapshot_json"])
        })
    return runs

# --- CYCLE 3: SECURITY SHIFT HANDOVER ---

@app.post("/api/security/handover", dependencies=[Depends(get_current_user)])
async def submit_shift_handover(request: Request, current_user = Depends(get_current_user)):
    body = await request.json()
    incoming_guard = body.get("incoming_guard", "").strip()
    incoming_pin = body.get("incoming_pin", "").strip()
    shift_type = body.get("shift_type", "")
    severity = body.get("severity", "green_routine")
    events_summary = body.get("events_summary", "").strip()
    cash_expected = body.get("cash_expected", {})
    cash_counted = body.get("cash_counted", {})
    
    if not incoming_guard or not incoming_pin or not shift_type or not events_summary:
        raise HTTPException(status_code=400, detail="Missing required shift handover parameters")
        
    if severity not in ["green_routine", "amber_minor", "red_critical"]:
        raise HTTPException(status_code=400, detail="Invalid triage severity value")
        
    # Verify incoming guard identity and PIN
    db = get_db()
    cursor = db.execute("SELECT username, pin, status, role FROM users WHERE username = ?", (incoming_guard,))
    guard = cursor.fetchone()
    db.close()
    
    if not guard or guard["status"] != "active":
        raise HTTPException(status_code=401, detail="Incoming guard user account not found or disabled")
        
    # Verify PIN
    if not secrets.compare_digest(guard["pin"], incoming_pin):
        raise HTTPException(status_code=401, detail="Invalid incoming guard authentication PIN")
        
    # Ensure outgoing guard is different from incoming
    if current_user["username"] == incoming_guard:
        raise HTTPException(status_code=400, detail="Incoming guard must be different from the outgoing guard")
        
    # Expected structures
    expected_splits = {
        "usd": float(cash_expected.get("usd", 0)),
        "zar": float(cash_expected.get("zar", 0)),
        "zwg": float(cash_expected.get("zwg", 0))
    }
    counted_splits = {
        "usd": float(cash_counted.get("usd", 0)),
        "zar": float(cash_counted.get("zar", 0)),
        "zwg": float(cash_counted.get("zwg", 0))
    }
    
    handover_id = write_shift_handover(
        outgoing_guard=current_user["username"],
        incoming_guard=incoming_guard,
        shift_type=shift_type,
        severity=severity,
        events_summary=events_summary,
        cash_expected=expected_splits,
        cash_counted=counted_splits
    )
    
    return {"status": "success", "handover_id": handover_id}

@app.get("/api/security/handover/history", dependencies=[Depends(get_current_user)])
async def get_handover_history():
    db = get_db()
    cursor = db.execute("SELECT * FROM shift_handover_logs ORDER BY timestamp DESC LIMIT 30")
    rows = [dict(r) for r in cursor.fetchall()]
    db.close()
    return rows

@app.get("/api/admin/security/verify-chain", dependencies=[Depends(require_admin)])
async def admin_verify_handover_chain():
    is_valid = verify_shift_handover_chain()
    return {"status": "success" if is_valid else "compromised", "valid": is_valid}

# --- CYCLE 3: INVENTORY & POS CHECKOUT ---

@app.get("/api/inventory", dependencies=[Depends(get_current_user)])
async def list_inventory():
    db = get_db()
    cursor = db.execute("SELECT * FROM inventory ORDER BY name ASC")
    items = [dict(row) for row in cursor.fetchall()]
    db.close()
    
    # Calculate low stock status dynamically
    for item in items:
        item["low_stock"] = item["quantity"] <= item["low_stock_threshold"]
    return items

@app.post("/api/inventory", dependencies=[Depends(require_admin)])
async def add_new_stock_item(request: Request, admin = Depends(require_admin)):
    body = await request.json()
    name = body.get("name", "").strip()
    sku = body.get("sku", "").strip()
    qty = float(body.get("quantity", 0.0))
    unit = body.get("unit", "pcs").strip()
    price = float(body.get("price_usd", 0.0))
    threshold = float(body.get("low_stock_threshold", 5.0))
    
    if not name or not sku:
        raise HTTPException(status_code=400, detail="Item name and SKU are required")
        
    db = get_db()
    cursor = db.execute("SELECT id FROM inventory WHERE name = ? OR sku = ?", (name, sku))
    if cursor.fetchone():
        db.close()
        raise HTTPException(status_code=400, detail="Item name or SKU already registered")
    db.close()
    
    item_id = add_inventory_item(name, sku, qty, unit, price, threshold, admin["username"])
    return {"status": "success", "id": item_id}

@app.put("/api/inventory/{item_id}/adjust", dependencies=[Depends(get_current_user)])
async def adjust_stock_manually(item_id: str, request: Request, current_user = Depends(get_current_user)):
    body = await request.json()
    amount = float(body.get("amount", 0.0))
    reason = body.get("reason", "manual adjustment").strip()
    
    if amount == 0:
        raise HTTPException(status_code=400, detail="Adjustment amount cannot be zero")
        
    success = adjust_inventory_qty(item_id, amount, reason, current_user["username"])
    if not success:
        raise HTTPException(status_code=400, detail="Adjustment failed: item not found or insufficient stock")
        
    return {"status": "success"}

@app.post("/api/inventory/{item_id}/wastage", dependencies=[Depends(get_current_user)])
async def adjust_stock_wastage(item_id: str, request: Request, current_user = Depends(get_current_user)):
    body = await request.json()
    qty = float(body.get("quantity", 0.0))
    reason = body.get("reason", "spoiled").strip()
    
    if qty <= 0:
        raise HTTPException(status_code=400, detail="Wastage quantity must be positive")
        
    success = log_wastage(item_id, qty, reason, current_user["username"])
    if not success:
        raise HTTPException(status_code=400, detail="Wastage log failed: insufficient stock or item not found")
        
    return {"status": "success"}

@app.post("/api/pos/checkout", dependencies=[Depends(get_current_user)])
async def pos_checkout(request: Request, current_user = Depends(get_current_user)):
    # 1. Capture Idempotency Key from request headers
    client_req_id = request.headers.get("X-Client-Request-Id") or f"req-{uuid.uuid4().hex[:12]}"
        
    body = await request.json()
    total_due = float(body.get("total_due_usd", 0.0))
    tenders = body.get("tenders", [])
    items = body.get("items", [])
    business_id = body.get("business_id", "biz-green-valley")
    issue_voucher = bool(body.get("issue_voucher_change", False))
    vouch_amount = float(body.get("voucher_change_amount", 0.0) or 0.0)
    vouch_curr = body.get("voucher_change_currency", "ZWG")

    # If simple items format used (e.g. cart_items + tendered_usd)
    cart_items = body.get("cart_items", [])
    if cart_items and not items:
        items = []
        db = get_db()
        for ci in cart_items:
            cursor = db.execute("SELECT id, price_usd FROM inventory WHERE id = ?", (ci["id"],))
            row = cursor.fetchone()
            if row:
                items.append({
                    "inventory_id": row["id"],
                    "quantity": float(ci["qty"]),
                    "price_usd_at_sale": float(row["price_usd"])
                })
        db.close()
        total_due = sum(i["quantity"] * i["price_usd_at_sale"] for i in items)

        # Build tenders from tendered amounts if provided
        t_usd = float(body.get("tendered_usd", 0.0) or 0.0)
        t_zar = float(body.get("tendered_zar", 0.0) or 0.0)
        t_zwg = float(body.get("tendered_zwg", 0.0) or 0.0)
        tenders = []
        if t_usd > 0:
            tenders.append({"currency": "USD", "amount_tendered": t_usd, "exchange_rate": 1.0, "amount_usd_equiv": t_usd})
        if t_zar > 0:
            tenders.append({"currency": "ZAR", "amount_tendered": t_zar, "exchange_rate": 18.5, "amount_usd_equiv": round(t_zar / 18.5, 2)})
        if t_zwg > 0:
            tenders.append({"currency": "ZWG", "amount_tendered": t_zwg, "exchange_rate": 26.5, "amount_usd_equiv": round(t_zwg / 26.5, 2)})
        if not tenders:
            tenders.append({"currency": "USD", "amount_tendered": total_due, "exchange_rate": 1.0, "amount_usd_equiv": total_due})
    
    if not items or not tenders:
        raise HTTPException(status_code=400, detail="Tenders and items lists are required")
        
    customer_user = body.get("customer_username")
    payment_method = body.get("payment_method", "cash")

    try:
        response_data = execute_checkout_transaction(
            operator_username=current_user["username"],
            total_due=total_due,
            client_req_id=client_req_id,
            tenders=tenders,
            items=items,
            business_id=business_id,
            issue_voucher_change=issue_voucher,
            voucher_change_amount=vouch_amount,
            voucher_change_currency=vouch_curr,
            customer_username=customer_user,
            payment_method=payment_method
        )
        # Attach receipt metadata
        tx_id = response_data.get("transaction_id")
        if tx_id:
            response_data["receipt"] = generate_receipt_data(tx_id)
        return response_data
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transaction processing error: {str(e)}")

# --- CYCLE 4: PHYSICS-BASED RF MESH & R*TREE SPATIAL TELEMETRY ---

@app.get("/api/security/nodes", dependencies=[Depends(get_current_user)])
async def list_security_nodes_telemetry():
    nodes, obstacles = get_nodes_telemetry()
    return {"status": "success", "nodes": nodes, "obstacles": obstacles}

@app.put("/api/security/nodes/{node_id}/position", dependencies=[Depends(get_current_user)])
async def update_security_node_position(node_id: str, request: Request, current_user = Depends(get_current_user)):
    body = await request.json()
    x_pct = float(body.get("x_pct", 50.0))
    y_pct = float(body.get("y_pct", 50.0))
    client_id = body.get("client_id", current_user["username"])
    timestamp_utc = body.get("timestamp_utc", datetime.datetime.now(datetime.timezone.utc).isoformat())
    
    updated = update_node_position_lww(node_id, x_pct, y_pct, client_id, timestamp_utc)
    if updated:
        return {"status": "success", "message": "Position updated successfully"}
    else:
        return {"status": "ignored", "message": "Stale update ignored by LWW sync"}

# --- CYCLE 4: COMPOUND AGRONOMY RULES & HARVEST WORK ORDERS ---

@app.get("/api/agriculture/rules", dependencies=[Depends(get_current_user)])
async def list_agricultural_rules():
    db = get_db()
    cursor = db.execute("SELECT * FROM agricultural_rules ORDER BY last_modified_utc DESC")
    rules = [dict(r) for r in cursor.fetchall()]
    db.close()
    return rules

@app.post("/api/agriculture/rules", dependencies=[Depends(get_current_user)])
async def create_agricultural_rule(request: Request, current_user = Depends(get_current_user)):
    body = await request.json()
    title = body.get("title", "").strip()
    crop = body.get("crop_type", "").strip()
    conditions = body.get("conditions", [])
    action_type = body.get("action_type", "advisory")
    action_msg = body.get("action_message", "").strip()
    target = body.get("actuator_target")
    stop_cond = body.get("actuator_stop_condition")
    
    if not title or not crop or not conditions or not action_msg:
        raise HTTPException(status_code=400, detail="Missing required rule fields")
        
    rule_id = str(uuid.uuid4())
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    db = get_db()
    db.execute("""
        INSERT INTO agricultural_rules (id, title, crop_type, conditions_json, action_type, action_message, actuator_target, actuator_stop_condition, is_active, last_modified_utc)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
    """, (rule_id, title, crop, json.dumps(conditions), action_type, action_msg, target, stop_cond, now_utc))
    db.commit()
    db.close()
    
    write_audit_log(current_user["username"], "RULE_CREATED", f"Created rule: {title}")
    return {"status": "success", "id": rule_id}

@app.post("/api/agriculture/rules/evaluate", dependencies=[Depends(get_current_user)])
async def evaluate_rules_endpoint(request: Request):
    body = await request.json()
    sensor_inputs = body.get("sensor_inputs", {})
    triggered = evaluate_agricultural_rules(sensor_inputs)
    return {"status": "success", "triggered_rules": triggered}

@app.get("/api/agriculture/harvest-orders", dependencies=[Depends(get_current_user)])
async def get_harvest_orders():
    db = get_db()
    cursor = db.execute("SELECT * FROM harvest_orders ORDER BY last_modified_utc DESC")
    orders = [dict(r) for r in cursor.fetchall()]
    db.close()
    return orders

@app.put("/api/agriculture/harvest-orders/{order_id}/status", dependencies=[Depends(get_current_user)])
async def update_harvest_order_status(order_id: str, request: Request, current_user = Depends(get_current_user)):
    body = await request.json()
    new_status = body.get("status", "").strip()
    if new_status not in ["triggered", "assigned", "harvested", "pos_listed"]:
        raise HTTPException(status_code=400, detail="Invalid harvest order status")
        
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    db = get_db()
    db.execute("UPDATE harvest_orders SET status = ?, last_modified_utc = ? WHERE id = ?", (new_status, now_utc, order_id))
    db.commit()
    db.close()
    
    write_audit_log(current_user["username"], "HARVEST_ORDER_UPDATED", f"Order {order_id} status changed to {new_status}")
    return {"status": "success"}

# --- CYCLE 4: CONTINUOUS DECAY POS PROMOTIONS ---

@app.get("/api/pos/promotions", dependencies=[Depends(get_current_user)])
async def get_pos_promotions():
    items = calculate_pos_catalog_prices()
    return items


# =====================================================================
# STAGE 1 CORE: CLUSTER NODE DISCOVERY & PORTABLE GENERATION ENDPOINTS
# =====================================================================

@app.get("/api/nodes/discovered")
def get_discovered_nodes():
    """Returns all active Data Nodes, Vault Gateways, and Operator Nodes discovered via UDP Multicast."""
    nodes = discovery_manager.get_cluster_nodes()
    return {"status": "success", "cluster_nodes": nodes, "count": len(nodes)}

@app.post("/api/cluster/nodes/{node_id}/toggle-active", dependencies=[Depends(get_current_user)])
async def toggle_node_active_endpoint(node_id: str, request: Request, current_user = Depends(get_current_user)):
    """Remotely activate or deactivate a discovered Data Node across the local network."""
    body = await request.json()
    target_state = bool(body.get("is_active", True))
    
    # Locate node in discovered registry
    nodes = discovery_manager.get_cluster_nodes(max_age=60.0)
    target_node = next((n for n in nodes if n["node_id"] == node_id), None)
    
    if not target_node:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found in cluster discovery cache.")

    ip = target_node.get("ip", "127.0.0.1")
    port = target_node.get("port", 8002)

    res = discovery_manager.toggle_remote_node_state(ip=ip, port=port, active=target_state)
    write_audit_log(current_user["username"], "NODE_LIFECYCLE_TOGGLE", f"Set node {node_id} ({ip}:{port}) active={target_state}")
    return {"status": "success", "result": res, "node_id": node_id, "is_active": target_state}

@app.post("/api/cluster/nodes/generate-portable", dependencies=[Depends(require_admin)])
async def generate_portable_node_endpoint(request: Request, current_user = Depends(get_current_user)):
    """Generate a self-contained, standalone portable node package with its own web UI & start.py."""
    if not generate_portable_node:
        raise HTTPException(status_code=500, detail="Portable Node Generator engine is unavailable.")

    body = await request.json()
    name = body.get("name", "Edge_Data_Node").strip()
    node_type = body.get("node_type", "data_node").strip().lower()
    port = int(body.get("port", 8005))
    storage_quota_mb = int(body.get("storage_quota_mb", 2048))

    if port in (8000, 8001):
        raise HTTPException(status_code=400, detail="Port 8000 (Vault) and 8001 (Multicast) are reserved.")

    res = generate_portable_node(
        name=name,
        node_type=node_type,
        port=port,
        storage_quota_mb=storage_quota_mb,
        parent_vault_url="http://127.0.0.1:8000"
    )
    write_audit_log(current_user["username"], "PORTABLE_NODE_GENERATED", f"Generated portable {node_type} '{name}' on port {port}")
    return {"status": "success", "package": res}

@app.get("/api/cluster/nodes/exported-list", dependencies=[Depends(get_current_user)])
def get_exported_nodes_endpoint():
    """List all previously generated standalone portable node packages."""
    if not list_exported_nodes:
        return {"status": "success", "exported_nodes": []}
    return {"status": "success", "exported_nodes": list_exported_nodes()}

@app.get("/api/cluster/keys", dependencies=[Depends(require_admin)])
def get_cluster_keys_endpoint():
    """Lists all cluster node communication keys registered in the Vault DB."""
    return {"status": "success", "keys": list_node_communication_keys()}

class NodeKeyRegistrationPayload(BaseModel):
    node_id: str
    node_type: str = "data_node"
    ip_address: str = "127.0.0.1"
    port: int = 8002
    secret_key: Optional[str] = None
    notes: Optional[str] = ""

@app.post("/api/cluster/keys", dependencies=[Depends(require_admin)])
def register_cluster_key_endpoint(payload: NodeKeyRegistrationPayload, current_user = Depends(get_current_user)):
    """Registers or rotates HMAC communication key for a cluster node in the Vault DB."""
    res = register_or_rotate_node_key(
        node_id=payload.node_id,
        node_type=payload.node_type,
        ip_address=payload.ip_address,
        port=payload.port,
        secret_key=payload.secret_key,
        notes=payload.notes or ""
    )
    write_audit_log(current_user["username"], "NODE_KEY_MANAGEMENT", f"Registered/Rotated communication key for node '{payload.node_id}' in Vault DB")
    return {"status": "success", "result": res}



# =====================================================================
# STAGE 1 CORE: AGRICULTURE & PRODUCTION COST ENDPOINTS
# =====================================================================

@app.get("/api/agri/plantings")
def get_plantings():
    return {"status": "success", "plantings": list_plantings()}

@app.post("/api/agri/plantings")
async def add_planting_endpoint(request: Request, current_user = Depends(get_current_user)):
    body = await request.json()
    crop_variety = body.get("crop_variety", "").strip()
    plot_bed_id = body.get("plot_bed_id", "").strip()
    planting_date_utc = body.get("planting_date_utc") or datetime.datetime.now(datetime.timezone.utc).isoformat()
    seeding_density = float(body.get("seeding_density", 0.0) or 0.0)
    target_maturity_date_utc = body.get("target_maturity_date_utc")
    initial_soil_hydration_pct = float(body.get("initial_soil_hydration_pct", 0.0) or 0.0)
    notes = body.get("notes", "")

    if not crop_variety or not plot_bed_id:
        raise HTTPException(status_code=400, detail="Crop variety and Plot ID are required.")

    res = create_planting(crop_variety, plot_bed_id, planting_date_utc, seeding_density, target_maturity_date_utc, initial_soil_hydration_pct, current_user["username"], notes)
    write_audit_log(current_user["username"], "AGRI_PLANTING_CREATED", f"Created planting {crop_variety} in {plot_bed_id}")
    return {"status": "success", "data": res}

@app.get("/api/agri/costs")
def get_costs_endpoint(planting_id: str = None):
    if not planting_id:
        raise HTTPException(status_code=400, detail="planting_id is required")
    costs = get_production_costs(planting_id)
    return {"status": "success", "costs": costs}

@app.post("/api/agri/costs")
async def add_costs_endpoint(request: Request, current_user = Depends(get_current_user)):
    body = await request.json()
    planting_id = body.get("planting_id")
    if not planting_id:
        raise HTTPException(status_code=400, detail="planting_id is required")
    costs = body.get("costs", {})
    res = log_production_costs(planting_id, costs, current_user["username"])
    write_audit_log(current_user["username"], "AGRI_COSTS_LOGGED", f"Logged production costs for {planting_id}")
    return {"status": "success", "data": res}

@app.post("/api/agri/calculate-price")
async def calculate_price_endpoint(request: Request):
    body = await request.json()
    costs = body.get("costs", {})
    mass_harvest_kg = float(body.get("mass_harvest_kg", 0.0) or 0.0)
    mass_self_kg = float(body.get("mass_self_kg", 0.0) or 0.0)
    markup_pct = float(body.get("markup_pct", 1.0) or 1.0)
    res = compute_production_cost_and_base_price(costs, mass_harvest_kg, mass_self_kg, markup_pct)
    return {"status": "success", "calculated": res}

@app.get("/api/agri/harvests")
def get_harvests_endpoint():
    return {"status": "success", "harvests": list_harvests()}

@app.post("/api/agri/harvests")
async def add_harvest_endpoint(request: Request, current_user = Depends(get_current_user)):
    body = await request.json()
    planting_id = body.get("planting_id")
    crop_name = body.get("crop_name", "").strip()
    harvest_date_utc = body.get("harvest_date_utc") or datetime.datetime.now(datetime.timezone.utc).isoformat()
    mass_harvest_kg = float(body.get("mass_harvest_kg", 0.0) or 0.0)
    quality_grade = body.get("quality_grade", "Grade A")
    storage_location = body.get("storage_location", "Farm Cold Room #1")
    mass_self_kg = float(body.get("mass_self_kg", 0.0) or 0.0)
    target_markup_pct = float(body.get("target_markup_pct", 1.0) or 1.0)
    half_life_days = float(body.get("shelf_life_half_life_days", 2.0) or 2.0)

    if not planting_id or not crop_name or mass_harvest_kg <= 0:
        raise HTTPException(status_code=400, detail="Planting ID, crop name, and positive harvest mass are required.")

    res = log_harvest_and_sync_inventory(
        planting_id, crop_name, harvest_date_utc, mass_harvest_kg,
        quality_grade, storage_location, mass_self_kg, target_markup_pct,
        half_life_days, current_user["username"]
    )
    write_audit_log(current_user["username"], "AGRI_HARVEST_LOGGED", f"Logged harvest of {mass_harvest_kg}kg {crop_name}")
    return {"status": "success", "data": res}

@app.get("/api/agri/dispositions")
def get_dispositions_endpoint(harvest_id: str = None):
    return {"status": "success", "dispositions": list_dispositions(harvest_id)}


# =====================================================================
# STAGE 1 CORE: SECURITY VISITOR GATEKEEPER ENDPOINTS
# =====================================================================

@app.get("/api/security/visitors")
def get_visitors_endpoint(search: str = None, destination: str = None, status: str = None):
    return {"status": "success", "visitors": list_visitors(search, destination, status)}

@app.get("/api/security/visitors/active")
def get_active_visitors_endpoint():
    return {"status": "success", "active_visitors": get_active_visitors()}

@app.post("/api/security/visitors/checkin")
async def checkin_visitor_endpoint(request: Request, current_user = Depends(get_current_user)):
    body = await request.json()
    national_id = body.get("national_id", "").strip()
    full_name = body.get("full_name", "").strip()
    destination_env = body.get("destination_env", "Main Office").strip()
    purpose = body.get("purpose", "").strip()
    escort_officer = body.get("escort_officer", "").strip()
    notes = body.get("notes", "")

    if not national_id or not full_name:
        raise HTTPException(status_code=400, detail="National ID and full name are required.")

    res = checkin_visitor(national_id, full_name, destination_env, purpose, escort_officer, current_user["username"], notes)
    write_audit_log(current_user["username"], "VISITOR_CHECKIN", f"Checked in visitor {full_name} ({national_id}) to {destination_env}")
    return {"status": "success", "data": res}

@app.post("/api/security/visitors/checkout")
async def checkout_visitor_endpoint(request: Request, current_user = Depends(get_current_user)):
    body = await request.json()
    visitor_id = body.get("visitor_id")
    if not visitor_id:
        raise HTTPException(status_code=400, detail="visitor_id is required.")
    res = checkout_visitor(visitor_id, current_user["username"])
    write_audit_log(current_user["username"], "VISITOR_CHECKOUT", f"Checked out visitor {visitor_id}")
    return {"status": "success", "data": res}


# =====================================================================
# STAGE 1 CORE: HYBRID SOCIAL MEDIA HUB ENDPOINTS
# =====================================================================

@app.get("/api/social/posts")
def get_social_posts_endpoint(post_type: str = None):
    return {"status": "success", "posts": list_social_posts(post_type)}

@app.get("/api/social/stories")
def get_social_stories_endpoint():
    return {"status": "success", "stories": list_social_posts(post_type="story")}

@app.post("/api/social/posts")
async def add_social_post_endpoint(request: Request, current_user = Depends(get_current_user)):
    body = await request.json()
    post_type = body.get("post_type", "thread")
    content_text = body.get("content_text", "")
    media_urls = body.get("media_urls", [])
    tags = body.get("tags", [])

    if not content_text and not media_urls:
        raise HTTPException(status_code=400, detail="Content or media is required.")

    res = create_social_post(post_type, current_user["username"], content_text, media_urls, tags)
    return {"status": "success", "data": res}

@app.get("/api/social/posts/{post_id}/comments")
def get_comments_endpoint(post_id: str):
    return {"status": "success", "comments": get_social_comments(post_id)}

@app.post("/api/social/posts/{post_id}/comments")
async def add_comment_endpoint(post_id: str, request: Request, current_user = Depends(get_current_user)):
    body = await request.json()
    text = body.get("comment_text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Comment text cannot be empty.")
    res = add_social_comment(post_id, current_user["username"], text)
    return {"status": "success", "data": res}

@app.post("/api/social/posts/{post_id}/tip")
async def tip_post_endpoint(post_id: str, request: Request, current_user = Depends(get_current_user)):
    body = await request.json()
    currency = body.get("currency", "USD").upper()
    amount = float(body.get("amount", 0.0) or 0.0)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Tip amount must be positive.")
    res = tip_social_post(post_id, current_user["username"], currency, amount)
    return {"status": "success", "data": res}


# =====================================================================
# STAGE 1 CORE: POS MIXED-TENDER & MARKETPLACE CATALOG ENDPOINTS
# =====================================================================

@app.get("/api/marketplace/catalog")
def get_marketplace_catalog():
    """Returns marketplace items with dynamic decay pricing and multi-currency rates."""
    db = get_db()
    cursor = db.execute("SELECT * FROM inventory WHERE quantity > 0")
    raw_items = [dict(r) for r in cursor.fetchall()]
    db.close()

    rate_zar = 18.5
    rate_zwg = 26.5

    catalog = []
    for item in raw_items:
        base_p = float(item.get("price_usd") or 0.0)
        cost_p = float(item.get("cost_price_usd") or 0.0)

        decay_info = calculate_continuous_decay_price(
            base_price_usd=base_p,
            cost_floor_usd=cost_p,
            half_life_days=2.0,
            harvest_time_iso=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )
        current_usd = decay_info["current_price_usd"]
        item["current_price_usd"] = current_usd
        item["price_zar"] = round(current_usd * rate_zar, 2)
        item["price_zwg"] = round(current_usd * rate_zwg, 2)
        item["discount_pct"] = decay_info["discount_pct"]
        item["is_floor_active"] = decay_info["is_floor_active"]
        catalog.append(item)

    return {"status": "success", "catalog": catalog, "exchange_rates": {"ZAR": rate_zar, "ZWG": rate_zwg}}

@app.post("/api/pos/calculate-tender")
async def calculate_tender_endpoint(request: Request):
    body = await request.json()
    total_usd = float(body.get("total_usd", 0.0) or 0.0)
    t_usd = float(body.get("tendered_usd", 0.0) or 0.0)
    t_zar = float(body.get("tendered_zar", 0.0) or 0.0)
    t_zwg = float(body.get("tendered_zwg", 0.0) or 0.0)
    r_zar = float(body.get("rate_zar", 18.5) or 18.5)
    r_zwg = float(body.get("rate_zwg", 26.5) or 26.5)

# =====================================================================
# MULTI-BUSINESS, OFFLINE VOUCHERS & RECEIPT ENDPOINTS
# =====================================================================

@app.get("/api/businesses")
def list_businesses_endpoint():
    """List all registered business entities."""
    return {"status": "success", "businesses": get_all_businesses()}

@app.post("/api/businesses", dependencies=[Depends(get_current_user)])
async def create_business_endpoint(request: Request, current_user = Depends(get_current_user)):
    """Register a new business enterprise profile."""
    body = await request.json()
    name = body.get("name", "").strip()
    category = body.get("category", "Horticulture & Fresh Produce").strip()
    phone = body.get("contact_phone", "").strip()
    address = body.get("location_address", "").strip()
    tax_id = body.get("tax_id", "").strip()
    header = body.get("receipt_header", "").strip()
    footer = body.get("receipt_footer_note", "").strip()
    curr = body.get("currency_preference", "USD").strip()

    if not name:
        raise HTTPException(status_code=400, detail="Business name is required.")

    biz = create_business(name, category, phone, address, tax_id, header, footer, curr, current_user["username"])
    return {"status": "success", "business": biz}

@app.get("/api/businesses/{biz_id}")
def get_business_endpoint(biz_id: str):
    biz = get_business_by_id(biz_id)
    if not biz:
        raise HTTPException(status_code=404, detail="Business entity not found.")
    return {"status": "success", "business": biz}

@app.post("/api/vouchers/mint", dependencies=[Depends(get_current_user)])
async def mint_voucher_endpoint(request: Request, current_user = Depends(get_current_user)):
    """Mint an offline cryptographic bearer voucher for change or credit."""
    body = await request.json()
    biz_id = body.get("business_id", "biz-green-valley")
    val = float(body.get("value_amount", 0.0) or 0.0)
    curr = body.get("currency", "ZWG").upper()
    tx_id = body.get("issued_for_tx_id")

    if val <= 0:
        raise HTTPException(status_code=400, detail="Voucher amount must be positive.")

    voucher = mint_offline_voucher(biz_id, val, curr, issued_by_node_id="node-vault-01", issued_for_tx_id=tx_id)
    return {"status": "success", "voucher": voucher}

@app.post("/api/vouchers/redeem", dependencies=[Depends(get_current_user)])
async def redeem_voucher_endpoint(request: Request, current_user = Depends(get_current_user)):
    """Scan and redeem an offline cryptographic bearer voucher."""
    body = await request.json()
    vid = body.get("vid", "").strip()
    biz_id = body.get("business_id")
    tx_id = body.get("redeemed_by_tx_id")

    if not vid:
        raise HTTPException(status_code=400, detail="Voucher ID is required.")

    res = verify_and_redeem_voucher(vid, business_id=biz_id, redeemed_by_tx_id=tx_id)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("detail", "Voucher redemption failed."))

    return {"status": "success", "redemption": res}

@app.get("/api/vouchers/{vid}")
def get_voucher_endpoint(vid: str):
    v = get_voucher_by_id(vid)
    if not v:
        raise HTTPException(status_code=404, detail="Voucher not found.")
    return {"status": "success", "voucher": v}

@app.get("/api/pos/receipt/{tx_id}")
def get_pos_receipt_endpoint(tx_id: str):
    receipt = generate_receipt_data(tx_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Transaction receipt not found.")
    return {"status": "success", "receipt": receipt}

# =====================================================================
# HIERARCHICAL RBAC & BUSINESS OPERATOR DELEGATION ENDPOINTS
# =====================================================================

@app.get("/api/businesses/{biz_id}/operators", dependencies=[Depends(get_current_user)])
async def list_business_operators_endpoint(biz_id: str, current_user = Depends(get_current_user)):
    """List operators assigned to a business (accessible by business admin or super admin)."""
    perms = get_operator_permissions(biz_id, current_user["username"])
    if "admin" not in perms and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only Business Administrators can view operator roster.")
    return {"status": "success", "business_id": biz_id, "operators": get_business_operators(biz_id)}

@app.post("/api/businesses/{biz_id}/operators", dependencies=[Depends(get_current_user)])
async def assign_business_operator_endpoint(biz_id: str, request: Request, current_user = Depends(get_current_user)):
    """Assign or update operator role and subsystem permissions for a business."""
    perms = get_operator_permissions(biz_id, current_user["username"])
    if "admin" not in perms and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only Business Administrators can manage operator permissions.")
    
    body = await request.json()
    username = body.get("username", "").strip()
    role_in_business = body.get("role_in_business", "operator").strip()
    permissions = body.get("permissions", [])

    if not username:
        raise HTTPException(status_code=400, detail="Username is required.")

    # Validate that username exists in users table
    with get_db() as db:
        cursor = db.execute("SELECT id FROM users WHERE username = ?", (username,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"User '{username}' does not exist.")

    op = assign_business_operator(
        business_id=biz_id,
        username=username,
        role_in_business=role_in_business,
        permissions=permissions,
        granted_by=current_user["username"]
    )
    return {"status": "success", "operator": op}

@app.delete("/api/businesses/{biz_id}/operators/{operator_username}", dependencies=[Depends(get_current_user)])
async def revoke_business_operator_endpoint(biz_id: str, operator_username: str, current_user = Depends(get_current_user)):
    """Revoke operator access from a business."""
    perms = get_operator_permissions(biz_id, current_user["username"])
    if "admin" not in perms and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only Business Administrators can revoke operator access.")

    revoke_business_operator(biz_id, operator_username, revoked_by=current_user["username"])
    return {"status": "success", "message": f"Operator '{operator_username}' revoked from business {biz_id}"}

@app.get("/api/businesses/{biz_id}/my-permissions", dependencies=[Depends(get_current_user)])
async def get_my_business_permissions_endpoint(biz_id: str, current_user = Depends(get_current_user)):
    """Return the calling user's granted permissions for the active business."""
    perms = get_operator_permissions(biz_id, current_user["username"])
    return {
        "status": "success",
        "business_id": biz_id,
        "username": current_user["username"],
        "permissions": perms,
        "is_business_admin": "admin" in perms or current_user["role"] == "admin"
    }

# =====================================================================
# DYNAMIC MULTI-CURRENCY & VIRTUAL TOKEN ENDPOINTS
# =====================================================================

class AddCurrencyRequest(BaseModel):
    code: str
    name: str
    symbol: str
    exchange_rate_to_usd: float
    currency_type: Optional[str] = "fiat"
    is_default: Optional[int] = 0

class UpdateCurrencyRequest(BaseModel):
    name: Optional[str] = None
    symbol: Optional[str] = None
    exchange_rate_to_usd: Optional[float] = None
    is_active: Optional[int] = None

@app.get("/api/currencies")
def get_currencies_endpoint(include_inactive: bool = False):
    """Retrieve all active fiat, precious-metal, and personalized virtual currencies."""
    currs = get_all_currencies(include_inactive=include_inactive)
    return {"status": "success", "currencies": currs}

@app.post("/api/admin/currencies", dependencies=[Depends(get_current_user)])
def add_currency_endpoint(req: AddCurrencyRequest, current_user = Depends(get_current_user)):
    """Admin / Operator endpoint to register a new currency or virtual community token."""
    if current_user["role"] not in ["admin", "merchant", "agronomist"]:
        raise HTTPException(status_code=403, detail="Permission denied. Only operators can configure currencies.")
    try:
        res = add_currency(
            code=req.code,
            name=req.name,
            symbol=req.symbol,
            exchange_rate_to_usd=req.exchange_rate_to_usd,
            currency_type=req.currency_type or "fiat",
            is_default=req.is_default or 0,
            performed_by=current_user["username"]
        )
        return {"status": "success", "currency": res}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/admin/currencies/{code}", dependencies=[Depends(get_current_user)])
def update_currency_endpoint(code: str, req: UpdateCurrencyRequest, current_user = Depends(get_current_user)):
    """Admin / Operator endpoint to update currency properties or live exchange rates."""
    if current_user["role"] not in ["admin", "merchant", "agronomist"]:
        raise HTTPException(status_code=403, detail="Permission denied.")
    try:
        res = update_currency(
            code=code,
            name=req.name,
            symbol=req.symbol,
            exchange_rate_to_usd=req.exchange_rate_to_usd,
            is_active=req.is_active,
            performed_by=current_user["username"]
        )
        return {"status": "success", "currency": res}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/admin/currencies/{code}", dependencies=[Depends(get_current_user)])
def delete_currency_endpoint(code: str, current_user = Depends(get_current_user)):
    """Admin / Operator endpoint to deactivate a currency."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only Administrator can deactivate currencies.")
    try:
        res = delete_currency(code=code, performed_by=current_user["username"])
        return {"status": "success", "result": res}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/cluster/sync-data-nodes", dependencies=[Depends(get_current_user)])
def sync_data_nodes_endpoint(current_user = Depends(get_current_user)):
    """Collects and replicates state between Vault Node and active Data Nodes (:8002)."""
    res = sync_all_collections_to_data_nodes()
    return {"status": "success", "sync": res}

@app.get("/api/currencies/catalog")
def get_global_currency_catalog_endpoint(q: Optional[str] = "", category: Optional[str] = None, limit: int = 50):
    """Searches the global catalog of ISO 4217 world currencies and top cryptocurrencies."""
    results = search_global_currency_catalog(query=q or "", category=category, limit=limit)
    return {"status": "success", "count": len(results), "catalog": results}

@app.get("/api/currencies/validate")
def validate_currency_endpoint(code: str = Query(...), name: Optional[str] = ""):
    """Real-time collision validation endpoint for proposed currency codes and custom virtual tokens."""
    validation = validate_currency_code_collision(code=code, name=name or "")
    return {"status": "success", "validation": validation}

@app.post("/api/currencies/catalog/sync", dependencies=[Depends(get_current_user)])
def sync_global_catalog_endpoint(current_user = Depends(get_current_user)):
    """Synchronizes global ISO 4217 & crypto reference catalog from connected Data Node."""
    res = sync_global_currencies_from_data_node()
    return {"status": "success", "result": res}


# =====================================================================
# CUSTOMER DIGITAL BANKING & RECEIPT VAULT ENDPOINTS
# =====================================================================

@app.get("/api/banking/wallet", dependencies=[Depends(get_current_user)])
def get_my_wallet_endpoint(current_user = Depends(get_current_user)):
    """Fetch authenticated user's digital wallet account details and multi-currency balances."""
    wallet = get_wallet_by_username(current_user["username"])
    return {"status": "success", "wallet": wallet}

@app.get("/api/banking/ledger", dependencies=[Depends(get_current_user)])
def get_my_ledger_endpoint(limit: int = 50, current_user = Depends(get_current_user)):
    """Fetch authenticated user's wallet transaction ledger history."""
    entries = get_wallet_ledger(current_user["username"], limit=limit)
    return {"status": "success", "username": current_user["username"], "ledger": entries}

@app.post("/api/banking/topup", dependencies=[Depends(get_current_user)])
async def topup_wallet_endpoint(request: Request, current_user = Depends(get_current_user)):
    """Deposit funds into a user's wallet (or self-deposit)."""
    body = await request.json()
    currency = body.get("currency", "USD").strip().upper()
    amount = float(body.get("amount", 0.0))
    target_username = body.get("username", current_user["username"]).strip()
    notes = body.get("notes", "Cash Top-up at Node Terminal")

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Top-up amount must be greater than zero.")

    res = topup_wallet(
        username=target_username,
        currency=currency,
        amount=amount,
        notes=notes,
        performed_by=current_user["username"]
    )
    return {"status": "success", "result": res}

@app.post("/api/banking/transfer", dependencies=[Depends(get_current_user)])
async def transfer_wallet_endpoint(request: Request, current_user = Depends(get_current_user)):
    """Execute a peer-to-peer (P2P) wallet transfer between users."""
    body = await request.json()
    to_user = body.get("to_user", "").strip()
    currency = body.get("currency", "USD").strip().upper()
    amount = float(body.get("amount", 0.0))
    notes = body.get("notes", "P2P Transfer")

    if not to_user:
        raise HTTPException(status_code=400, detail="Recipient username is required.")
    if to_user == current_user["username"]:
        raise HTTPException(status_code=400, detail="Cannot transfer funds to yourself.")
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Transfer amount must be greater than zero.")

    # Check recipient exists
    with get_db() as db:
        cursor = db.execute("SELECT id FROM users WHERE username = ?", (to_user,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Recipient '@{to_user}' does not exist.")

    try:
        res = execute_wallet_transfer(
            from_user=current_user["username"],
            to_user=to_user,
            currency=currency,
            amount=amount,
            tx_type="p2p_transfer",
            notes=notes
        )
        return {"status": "success", "transfer": res}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/banking/deposit-voucher", dependencies=[Depends(get_current_user)])
async def deposit_voucher_endpoint(request: Request, current_user = Depends(get_current_user)):
    """Convert an offline cryptographic bearer voucher into liquid wallet balance."""
    body = await request.json()
    vid = body.get("vid", "").strip()
    if not vid:
        raise HTTPException(status_code=400, detail="Voucher ID is required.")

    res = deposit_voucher_to_wallet(username=current_user["username"], vid=vid)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("detail", "Voucher deposit failed."))

    return {"status": "success", "deposit": res}

@app.get("/api/banking/receipts", dependencies=[Depends(get_current_user)])
def get_my_receipts_endpoint(query: Optional[str] = None, current_user = Depends(get_current_user)):
    """Fetch customer's archived digital receipts from their personal receipt vault."""
    receipts = get_customer_receipts(current_user["username"], query=query)
    return {"status": "success", "username": current_user["username"], "receipts": receipts}


# Serve static frontend folder (last route matches remaining files)
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

