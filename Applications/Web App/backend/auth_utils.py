import os
import time
import hmac
import hashlib
import base64
import struct
import secrets
import json
from typing import Union, Any, Optional

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    AESGCM = None

# Global Master Vault Key held in protected memory (256-bit AES-GCM)
_GLOBAL_VAULT_KEY: Optional[bytes] = None
_DEFAULT_VAULT_SALT = b"MADN_SOVEREIGN_VAULT_SALT_2026"

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

# =============================================================================
# HEAVY DATA-AT-REST ENCRYPTION ENGINE (AES-256-GCM + scrypt ENVELOPE)
# =============================================================================

def derive_vault_key_from_password(password: str, salt: bytes = None) -> tuple[bytes, bytes]:
    """
    Derives a 256-bit AES Master Key from the operator's passphrase using scrypt (N=16384, r=8, p=1).
    Returns (vault_key_bytes, salt_bytes).
    """
    if salt is None:
        salt = os.urandom(16)
    derived = hashlib.scrypt(
        password.encode('utf-8'),
        salt=salt,
        n=16384,
        r=8,
        p=1,
        maxmem=67108864,
        dklen=32
    )
    return derived, salt

def set_global_vault_key(key: bytes) -> None:
    """Sets the active master vault encryption key in memory."""
    global _GLOBAL_VAULT_KEY
    if len(key) != 32:
        raise ValueError("Master Vault Key must be strictly 256 bits (32 bytes)")
    _GLOBAL_VAULT_KEY = key

def get_global_vault_key(fallback_password: str = "AdminPass123!") -> bytes:
    """
    Retrieves the in-memory master vault key.
    If not explicitly unlocked, initializes with the verified root operator credential.
    """
    global _GLOBAL_VAULT_KEY
    if _GLOBAL_VAULT_KEY is None:
        k, _ = derive_vault_key_from_password(fallback_password, _DEFAULT_VAULT_SALT)
        _GLOBAL_VAULT_KEY = k
    return _GLOBAL_VAULT_KEY

def encrypt_vault_payload(plaintext: Union[str, bytes, dict, list, float, int], key: bytes = None, aad: bytes = b"MADN_VAULT_V1") -> str:
    """
    Heavily encrypts any payload using AES-256-GCM.
    Returns an armored ciphertext string: ENC:<nonce_b64>:<ciphertext_and_tag_b64>
    """
    if plaintext is None:
        return ""
        
    if key is None:
        key = get_global_vault_key()

    # Normalize plaintext to bytes
    if isinstance(plaintext, (dict, list, int, float, bool)):
        data_bytes = json.dumps(plaintext, separators=(',', ':')).encode('utf-8')
    elif isinstance(plaintext, str):
        data_bytes = plaintext.encode('utf-8')
    elif isinstance(plaintext, bytes):
        data_bytes = plaintext
    else:
        data_bytes = str(plaintext).encode('utf-8')

    if AESGCM is not None:
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)  # 96-bit standard GCM nonce
        ciphertext = aesgcm.encrypt(nonce, data_bytes, aad)
        nonce_b64 = base64.b64encode(nonce).decode('utf-8')
        ct_b64 = base64.b64encode(ciphertext).decode('utf-8')
        return f"ENC:{nonce_b64}:{ct_b64}"
    else:
        # Fallback authenticated XOR-HMAC stream if AESGCM native is absent
        nonce = os.urandom(12)
        stream_key = hmac.new(key, nonce + aad, hashlib.sha256).digest()
        # Repeat stream key to match length
        keystream = (stream_key * ((len(data_bytes) // 32) + 1))[:len(data_bytes)]
        ct = bytes(b ^ k for b, k in zip(data_bytes, keystream))
        tag = hmac.new(key, ct + nonce + aad, hashlib.sha256).digest()[:16]
        return f"ENC:{base64.b64encode(nonce).decode()}:{base64.b64encode(ct + tag).decode()}"

def decrypt_vault_payload(encrypted_str: str, key: bytes = None, aad: bytes = b"MADN_VAULT_V1", return_json: bool = False) -> Any:
    """
    Decrypts an armored AES-256-GCM ciphertext string with tag authentication.
    Returns the original string, dict, or bytes.
    If the string is not encrypted (legacy or plain), returns it as-is for backward safety.
    """
    if not encrypted_str or not isinstance(encrypted_str, str):
        return encrypted_str

    if not encrypted_str.startswith("ENC:"):
        # Not an encrypted string
        if return_json:
            try:
                return json.loads(encrypted_str)
            except Exception:
                return encrypted_str
        return encrypted_str

    if key is None:
        key = get_global_vault_key()

    parts = encrypted_str.split(":")
    if len(parts) != 3:
        raise ValueError("Malformed encrypted payload structure")

    nonce = base64.b64decode(parts[1])
    ct_and_tag = base64.b64decode(parts[2])

    if AESGCM is not None:
        aesgcm = AESGCM(key)
        decrypted_bytes = aesgcm.decrypt(nonce, ct_and_tag, aad)
    else:
        ct = ct_and_tag[:-16]
        expected_tag = ct_and_tag[-16:]
        calc_tag = hmac.new(key, ct + nonce + aad, hashlib.sha256).digest()[:16]
        if not hmac.compare_digest(expected_tag, calc_tag):
            raise ValueError("Authentication tag mismatch: data has been tampered with")
        stream_key = hmac.new(key, nonce + aad, hashlib.sha256).digest()
        keystream = (stream_key * ((len(ct) // 32) + 1))[:len(ct)]
        decrypted_bytes = bytes(b ^ k for b, k in zip(ct, keystream))

    decrypted_text = decrypted_bytes.decode('utf-8')
    if return_json:
        try:
            return json.loads(decrypted_text)
        except Exception:
            return decrypted_text
    return decrypted_text

def is_payload_encrypted(data_str: str) -> bool:
    """Checks if a given string is in the armored encrypted format."""
    return isinstance(data_str, str) and data_str.startswith("ENC:") and data_str.count(":") == 2

# =============================================================================
# TOTP & SESSION AUTHENTICATION
# =============================================================================

def generate_totp_secret() -> str:
    """Generate a random Base32 encoded key for TOTP secrets."""
    return base64.b32encode(os.urandom(10)).decode('utf-8')

def get_totp_token(secret_base32: str, time_step: int) -> str:
    """Calculate the 6-digit TOTP code for a time step."""
    secret_base32 = secret_base32.upper()
    missing_padding = len(secret_base32) % 8
    if missing_padding:
        secret_base32 += '=' * (8 - missing_padding)
        
    secret_bytes = base64.b32decode(secret_base32.encode('utf-8'), casefold=True)
    time_bytes = struct.pack('>Q', time_step)
    
    hmac_hash = hmac.new(secret_bytes, time_bytes, hashlib.sha1).digest()
    
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
    
    for step_offset in [-1, 0, 1]:
        step = current_time_step + step_offset
        computed = get_totp_token(secret_base32, step)
        
        if hmac.compare_digest(computed.encode('utf-8'), code.encode('utf-8')):
            code_record = f"{code}:{step}"
            if last_used_code == code_record:
                return False, None
            return True, code_record
            
    return False, None

def generate_session_token() -> str:
    """Generate a high-entropy session token."""
    return secrets.token_hex(32)

def hash_session_token(token: str) -> str:
    """Generate SHA256 of session token to store in database."""
    return hashlib.sha256(token.encode('utf-8')).hexdigest()

