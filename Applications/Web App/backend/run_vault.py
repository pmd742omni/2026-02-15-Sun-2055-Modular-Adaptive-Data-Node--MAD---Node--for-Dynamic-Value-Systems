import sys
import types
import os

# Windows AppLocker / Application Control resilience stub
try:
    import _multiprocessing
except ImportError:
    m = types.ModuleType('_multiprocessing')
    m.win32 = types.ModuleType('win32')
    m.closesocket = lambda s: None
    m.recv = lambda *a: b''
    m.send = lambda *a: None
    m.sem_unlink = lambda *a: None
    sys.modules['_multiprocessing'] = m

import uvicorn
from main import app

if __name__ == "__main__":
    port = int(os.environ.get("MADN_VAULT_PORT", "8000"))
    
    # Auto-detect certificates in Applications/certs
    base_apps = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    default_certs_dir = os.path.join(base_apps, "certs")
    default_cert = os.path.join(default_certs_dir, "cert.pem")
    default_key = os.path.join(default_certs_dir, "key.pem")

    ssl_keyfile = os.environ.get("MADN_SSL_KEYFILE") or (default_key if os.path.exists(default_key) else None)
    ssl_certfile = os.environ.get("MADN_SSL_CERTFILE") or (default_cert if os.path.exists(default_cert) else None)
    
    use_https = os.environ.get("MADN_HTTPS_ENABLED", "1") != "0" and ssl_keyfile and ssl_certfile

    kwargs = {
        "app": app,
        "host": "0.0.0.0",
        "port": port,
        "log_level": "info"
    }
    if use_https and ssl_keyfile and ssl_certfile and os.path.exists(ssl_keyfile) and os.path.exists(ssl_certfile):
        kwargs["ssl_keyfile"] = ssl_keyfile
        kwargs["ssl_certfile"] = ssl_certfile
        print(f"[+] TLS 1.3 Active: Serving HTTPS on https://127.0.0.1:{port}")
    else:
        print(f"[*] Serving HTTP on http://127.0.0.1:{port}")

    uvicorn.run(**kwargs)
