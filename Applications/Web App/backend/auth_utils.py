import os
import time
import hmac
import hashlib
import base64
import struct
import secrets

def hash_password(password: str, salt: bytes = None) -> tuple[str, str]:
    """Hash password using hashlib.scrypt (N=16384, r=8, p=1)."""
    if salt is None:
        salt = os.urandom(16)
    # scrypt hashing
    hashed = hashlib.scrypt(
        password.encode('utf-8'),
        salt=salt,
        n=16384,
        r=8,
        p=1,
        dklen=32
    )
    return salt.hex(), hashed.hex()

def verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    """Verify password against salt and hash in constant time."""
    try:
        salt = bytes.fromhex(salt_hex)
        target_hash = bytes.fromhex(hash_hex)
        _, computed_hash = hash_password(password, salt)
        return hmac.compare_digest(bytes.fromhex(computed_hash), target_hash)
    except Exception:
        return False

def generate_totp_secret() -> str:
    """Generate a random Base32 encoded key for TOTP secrets."""
    # 10 bytes = 80 bits, which encodes to 16 Base32 characters
    return base64.b32encode(os.urandom(10)).decode('utf-8')

def get_totp_token(secret_base32: str, time_step: int) -> str:
    """Calculate the 6-digit TOTP code for a time step."""
    # Normalize secret padding
    secret_base32 = secret_base32.upper()
    missing_padding = len(secret_base32) % 8
    if missing_padding:
        secret_base32 += '=' * (8 - missing_padding)
        
    secret_bytes = base64.b32decode(secret_base32.encode('utf-8'), casefold=True)
    time_bytes = struct.pack('>Q', time_step)
    
    # HMAC-SHA1 (RFC 6238 Standard)
    hmac_hash = hmac.new(secret_bytes, time_bytes, hashlib.sha1).digest()
    
    # Dynamic truncation
    offset = hmac_hash[-1] & 0x0f
    code_bytes = hmac_hash[offset:offset+4]
    code_val = struct.unpack('>I', code_bytes)[0] & 0x7fffffff
    
    return str(code_val % 1000000).zfill(6)

def verify_totp(secret_base32: str, code: str, last_used_code: str = None) -> tuple[bool, str]:
    """
    Verify a TOTP token with drift tolerance of +/- 1 window (30s) and replay protection.
    Returns (is_valid, code_to_persist).
    """
    if not code or len(code) != 6 or not code.isdigit():
        return False, None
        
    current_time_step = int(time.time() / 30)
    
    # Search window T-1, T, T+1
    for step_offset in [-1, 0, 1]:
        step = current_time_step + step_offset
        computed = get_totp_token(secret_base32, step)
        
        if hmac.compare_digest(computed.encode('utf-8'), code.encode('utf-8')):
            # Replay protection: assert this code is not re-submitted in the same time step
            # We persist code:step in the db (e.g. '123456:594323') to avoid token reuse.
            code_record = f"{code}:{step}"
            if last_used_code == code_record:
                return False, None  # Replay block
            return True, code_record
            
    return False, None

def generate_session_token() -> str:
    """Generate a high-entropy session token."""
    return secrets.token_hex(32)

def hash_session_token(token: str) -> str:
    """Generate SHA256 of session token to store in database."""
    return hashlib.sha256(token.encode('utf-8')).hexdigest()
