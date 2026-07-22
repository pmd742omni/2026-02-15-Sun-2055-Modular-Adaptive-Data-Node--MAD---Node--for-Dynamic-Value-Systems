import os
import secrets
import time
import uuid
import json
import datetime
from fastapi import FastAPI, Request, Response, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

try:
    from .database import (
        get_db, init_db, write_audit_log, FORENSIC_MODE,
        get_calculator_config, get_all_calculator_configs, update_calculator_config,
        add_inventory_item, adjust_inventory_qty, log_wastage,
        execute_checkout_transaction, write_shift_handover, verify_shift_handover_chain,
        get_nodes_telemetry, update_node_position_lww, evaluate_agricultural_rules, calculate_pos_catalog_prices,
        track_device_activity, is_device_blocked, block_device, unblock_device, get_tracked_devices
    )
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
        track_device_activity, is_device_blocked, block_device, unblock_device, get_tracked_devices
    )
    from auth_utils import (
        verify_password,
        hash_password,
        verify_totp,
        generate_session_token,
        hash_session_token,
        generate_totp_secret
    )

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
    version="1.0.0"
)

# Startup DB initializations
@app.on_event("startup")
def startup_event():
    init_db()

# Security Headers, Device Tracking & Content-Security-Policy (CSP) Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    client_ip = request.client.host if request.client else ""
    user_agent = request.headers.get("User-Agent", "")
    
    # 1. Device IP Blocking Enforcement
    if client_ip and is_device_blocked(client_ip):
        return Response(
            content='{"detail": "Device access blocked by system administrator."}',
            status_code=403,
            media_type="application/json"
        )
        
    # 2. Track connected device activity
    if client_ip:
        track_device_activity(client_ip, user_agent)

    # 3. If forensic mode is active, block all api requests except health checks
    if FORENSIC_MODE and request.url.path.startswith("/api") and request.url.path != "/api/health":
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
        # Bypass login/register check if no cookie was issued yet
        if request.url.path not in ["/api/auth/login", "/api/auth/register"]:
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

@app.post("/api/auth/register")
async def register(request: Request):
    body = await request.json()
    username = body.get("username", "").strip()
    password = body.get("password", "")
    
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password are required")
        
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
    
    db.execute("""
        INSERT INTO users (username, password_hash, salt, role, status, created_at, updated_at, must_change_password)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (username, hash_hex, salt_hex, "operator", "pending", now, now, 0))
    db.commit()
    db.close()
    
    write_audit_log("SYSTEM", "REGISTER", f"Account '{username}' created with status pending approval.")
    return {"message": "Registration successful. Please wait for an administrator to activate your account."}

@app.post("/api/auth/login")
async def login(request: Request, response: Response):
    body = await request.json()
    username = body.get("username", "").strip()
    password = body.get("password", "")
    mfa_token = body.get("mfa_token", "").strip()
    
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
        
    # 3. Verify Password
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
        raise HTTPException(status_code=403, detail="Account status is not active (pending or disabled)")
        
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
    
    # Set secure HttpOnly cookies
    response.set_cookie(
        key="madn_session",
        value=session_token,
        httponly=True,
        samesite="strict",
        secure=False  # Set to True if local host is run with TLS/HTTPS proxy
    )
    
    # Set non-HttpOnly CSRF token cookie
    csrf_token = secrets.token_hex(16)
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        samesite="strict"
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

@app.post("/api/auth/logout")
async def logout(request: Request, response: Response, current_user = Depends(get_current_user)):
    db = get_db()
    db.execute("DELETE FROM sessions WHERE token_hash = ?", (current_user["token_hash"],))
    db.commit()
    db.close()
    
    response.delete_cookie("madn_session")
    response.delete_cookie("csrf_token")
    
    write_audit_log(current_user["username"], "LOGOUT", "Session terminated by user.")
    return {"message": "Logged out successfully."}

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
    client_req_id = request.headers.get("X-Client-Request-Id")
    if not client_req_id:
        raise HTTPException(status_code=400, detail="Missing X-Client-Request-Id header for transaction idempotency")
        
    body = await request.json()
    total_due = float(body.get("total_due_usd", 0.0))
    tenders = body.get("tenders", [])
    items = body.get("items", [])
    
    if not items or not tenders:
        raise HTTPException(status_code=400, detail="Tenders and items lists are required")
        
    # Validate split totals
    tenders_total = sum(float(t["amount_usd_equiv"]) for t in tenders)
    if abs(tenders_total - total_due) > 0.01:
         raise HTTPException(status_code=400, detail=f"Tenders total equivalent (${tenders_total:.2f}) does not match invoice total (${total_due:.2f})")
         
    try:
        response_data = execute_checkout_transaction(
            operator_username=current_user["username"],
            total_due=total_due,
            client_req_id=client_req_id,
            tenders=tenders,
            items=items
        )
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

# Serve static frontend folder (last route matches remaining files)
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
