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
    use_https = os.environ.get("MADN_HTTPS_ENABLED", "0") == "1"
    ssl_keyfile = os.environ.get("MADN_SSL_KEYFILE")
    ssl_certfile = os.environ.get("MADN_SSL_CERTFILE")

    kwargs = {
        "app": app,
        "host": "0.0.0.0",
        "port": port,
        "log_level": "info"
    }
    if use_https and ssl_keyfile and ssl_certfile and os.path.exists(ssl_keyfile) and os.path.exists(ssl_certfile):
        kwargs["ssl_keyfile"] = ssl_keyfile
        kwargs["ssl_certfile"] = ssl_certfile

    uvicorn.run(**kwargs)
