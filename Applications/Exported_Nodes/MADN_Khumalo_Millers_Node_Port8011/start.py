#!/usr/bin/env python3
"""
Portable Launcher for Khumalo_Millers_Node (DATA_NODE)
=====================================================
Run this file on any computer with Python 3.9+ installed to start this node.
"""

import os
import sys
import subprocess

REQUIRED_PACKAGES = ["fastapi", "uvicorn", "pydantic", "jinja2"]

def check_and_install():
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"[*] Installing dependencies for Khumalo_Millers_Node: {missing}")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)

if __name__ == "__main__":
    check_and_install()
    print(f"=======================================================")
    print(f"   STARTING PORTABLE NODE: Khumalo_Millers_Node (DATA_NODE)")
    print(f"   Port: 8011 | ID: data-node-khumalo_millers_node-5eaa91")
    print(f"   Web UI: http://127.0.0.1:8011")
    print(f"=======================================================")
    server_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server.py")
    subprocess.call([sys.executable, server_path])
