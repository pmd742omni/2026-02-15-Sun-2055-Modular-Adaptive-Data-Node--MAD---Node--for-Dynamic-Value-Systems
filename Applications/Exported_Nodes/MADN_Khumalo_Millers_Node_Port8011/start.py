#!/usr/bin/env python3
"""
Portable Launcher for Khumalo_Millers_Node (DATA_NODE)
=====================================================
Run this file on any computer with Python 3.9+ installed to start this node.
"""

import os
import sys
import time
import subprocess
import threading
import webbrowser

REQUIRED_PACKAGES = ["fastapi", "uvicorn", "pydantic", "jinja2", "cryptography"]

def check_and_install():
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"[*] Installing dependencies for Khumalo_Millers_Node: {missing}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
        except Exception as e:
            print(f"[!] Pip warning: {e}")

def open_browser():
    time.sleep(1.2)
    url = f"https://127.0.0.1:8011"
    print(f"[*] Opening browser at {url} ...")
    try:
        webbrowser.open(url)
    except Exception:
        pass

if __name__ == "__main__":
    check_and_install()

    # Generate or verify local X.509 TLS Certificates
    cert_file, key_file = None, None
    try:
        if os.path.exists("tls_manager.py"):
            from tls_manager import ensure_ssl_certificates
            cert_file, key_file = ensure_ssl_certificates(certs_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), "certs"))
    except Exception as e:
        print(f"[!] TLS Notice: {e}")

    print(f"=======================================================")
    print(f"   STARTING PORTABLE NODE: Khumalo_Millers_Node (DATA_NODE)")
    print(f"   Port: 8011 | ID: data-node-khumalo_millers_node-9c0295")
    print(f"   Web UI: https://127.0.0.1:8011")
    print(f"=======================================================")
    threading.Thread(target=open_browser, daemon=True).start()
    server_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server.py")
    cmd = [sys.executable, server_path, str(8011)]
    if cert_file and key_file:
        cmd.extend(["--ssl-keyfile", key_file, "--ssl-certfile", cert_file])
    subprocess.call(cmd)
