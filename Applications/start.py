#!/usr/bin/env python3
"""
MADN Portable Multi-Node Bootstrapper & Process Supervisor
==========================================================
Zero-configuration portable launcher for the Modular Adaptive Data Node (MADN)
ecosystem. Can be executed on any machine with Python 3.9+ installed.

Features:
- Preflight dependency validation and automatic requirement resolution.
- Multi-node process supervision (Vault Coordinator :8000 + Data Node :8002 + Custom Nodes).
- Dynamic node discovery and active/deactive lifecycle control.
- Built-in Portable Node Generator CLI (`--create-node <name> <type> <port>`).
"""

import os
import sys
import time
import json
import signal
import socket
import shutil
import argparse
import subprocess
import threading
from typing import Dict, List, Optional

APPLICATIONS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(APPLICATIONS_DIR)
DATA_NODE_DIR = os.path.join(APPLICATIONS_DIR, "Data_Node")
WEB_APP_DIR = os.path.join(APPLICATIONS_DIR, "Web App")
BACKEND_DIR = os.path.join(WEB_APP_DIR, "backend")
EXPORTED_NODES_DIR = os.path.join(APPLICATIONS_DIR, "Exported_Nodes")
CONFIG_FILE = os.path.join(APPLICATIONS_DIR, "applications_config.json")

REQUIRED_PACKAGES = [
    "fastapi",
    "uvicorn",
    "pydantic",
    "cryptography",
    "qrcode",
    "jinja2",
    "requests"
]

class PreflightManager:
    """Verifies and ensures environment readiness across any host operating system."""

    @staticmethod
    def check_python_version():
        if sys.version_info < (3, 9):
            print(f"[!] Warning: Python 3.9+ is recommended. Detected: {sys.version}")

    @staticmethod
    def ensure_dependencies():
        missing = []
        for pkg in REQUIRED_PACKAGES:
            try:
                __import__(pkg)
            except ImportError:
                missing.append(pkg)

        if missing:
            print(f"[*] Missing required packages: {', '.join(missing)}")
            print("[*] Automatically installing dependencies via pip...")
            cmd = [sys.executable, "-m", "pip", "install"] + missing
            try:
                subprocess.check_call(cmd)
                print("[+] Dependencies successfully installed.")
            except subprocess.CalledProcessError as e:
                print(f"[!] Failed to auto-install dependencies: {e}")
                print(f"    Please manually run: pip install {' '.join(missing)}")
                sys.exit(1)

    @staticmethod
    def is_port_in_use(port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex(('127.0.0.1', port)) == 0


class NodeSupervisor:
    """Orchestrates and monitors background node child processes."""

    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.running = False

    def start_process(self, name: str, cmd: List[str], cwd: str, port: int) -> bool:
        if PreflightManager.is_port_in_use(port):
            print(f"[!] Warning: Port {port} is already in use. Skipping start for '{name}'.")
            return False

        print(f"[+] Starting {name} on port {port}...")
        env = os.environ.copy()
        env["PYTHONPATH"] = cwd + os.pathsep + env.get("PYTHONPATH", "")
        
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        self.processes[name] = proc

        # Thread to read and display logs
        def stream_logs(p, p_name):
            for line in p.stdout:
                if not self.running:
                    break
                print(f"[{p_name}] {line.strip()}")

        t = threading.Thread(target=stream_logs, args=(proc, name), daemon=True)
        t.start()
        return True

    def stop_all(self):
        self.running = False
        print("\n[*] Gracefully stopping all MADN node processes...")
        for name, proc in list(self.processes.items()):
            try:
                print(f"[-] Terminating {name} (PID {proc.pid})...")
                proc.terminate()
                proc.wait(timeout=2)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        self.processes.clear()
        print("[+] All node services halted.")


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "vault_port": 8000,
        "primary_data_node_port": 8002,
        "additional_nodes": []
    }


def save_config(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def create_portable_node_cli(name: str, node_type: str, port: int, output_dir: Optional[str] = None):
    """Invokes the generator engine to create a new portable node bundle."""
    try:
        from node_generator import generate_portable_node
        res = generate_portable_node(name=name, node_type=node_type, port=port, target_dir=output_dir)
        print(f"\n[+] Successfully generated portable {node_type} '{name}' on port {port}!")
        print(f"    Location: {res['node_dir']}")
        print(f"    Launch by running: python \"{os.path.join(res['node_dir'], 'start.py')}\"")
        return res
    except ImportError:
        print("[!] Error: node_generator.py not found in Applications folder.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="MADN Portable Multi-Node Launcher")
    parser.add_argument("--all", action="store_true", help="Launch Vault Coordinator and all Data Nodes (Default)")
    parser.add_argument("--vault-only", action="store_true", help="Launch only Vault Coordinator (:8000)")
    parser.add_argument("--data-only", action="store_true", help="Launch only Data Node (:8002)")
    parser.add_argument("--status", action="store_true", help="Check status of all local node ports")
    parser.add_argument("--create-node", nargs=3, metavar=("NAME", "TYPE", "PORT"), help="Generate a new standalone portable node package (e.g. --create-node Alpha data_node 8005)")
    args = parser.parse_args()

    # Preflight validation
    PreflightManager.check_python_version()
    PreflightManager.ensure_dependencies()

    cfg = load_config()
    v_port = cfg.get("vault_port", 8000)
    d_port = cfg.get("primary_data_node_port", 8002)

    # CLI command: Status
    if args.status:
        print("\n=== MADN Node Status Check ===")
        print(f"Vault Node (: {v_port}): {'[ACTIVE / IN-USE]' if PreflightManager.is_port_in_use(v_port) else '[AVAILABLE / OFFLINE]'}")
        print(f"Data Node  (: {d_port}): {'[ACTIVE / IN-USE]' if PreflightManager.is_port_in_use(d_port) else '[AVAILABLE / OFFLINE]'}")
        for add_node in cfg.get("additional_nodes", []):
            np = add_node.get("port")
            nn = add_node.get("name")
            print(f"Custom Node '{nn}' (: {np}): {'[ACTIVE / IN-USE]' if PreflightManager.is_port_in_use(np) else '[AVAILABLE / OFFLINE]'}")
        print("==============================\n")
        return

    # CLI command: Create node
    if args.create_node:
        c_name, c_type, c_port = args.create_node
        create_portable_node_cli(c_name, c_type, int(c_port))
        return

    # Start services
    supervisor = NodeSupervisor()
    supervisor.running = True

    def sig_handler(sig, frame):
        supervisor.stop_all()
        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    print("\n=======================================================")
    print("      MODULAR ADAPTIVE DATA NODE (MADN) ECOSYSTEM       ")
    print("           Portable Tri-Node Execution Platform        ")
    print("=======================================================")
    print(f"[*] Applications Root: {APPLICATIONS_DIR}")

    start_vault = not args.data_only
    start_data = not args.vault_only

    if start_vault:
        vault_cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(v_port)]
        supervisor.start_process("Vault-Node", vault_cmd, cwd=BACKEND_DIR, port=v_port)

    if start_data:
        data_cmd = [sys.executable, "data_node.py"]
        supervisor.start_process("Data-Node-Primary", data_cmd, cwd=DATA_NODE_DIR, port=d_port)

    # Start any configured additional nodes
    for add_node in cfg.get("additional_nodes", []):
        if add_node.get("enabled", True):
            node_dir = add_node.get("path")
            node_name = add_node.get("name")
            node_port = add_node.get("port")
            if node_dir and os.path.exists(node_dir):
                cmd = [sys.executable, "server.py"]
                supervisor.start_process(node_name, cmd, cwd=node_dir, port=node_port)

    print("\n[+] System services initialized successfully!")
    print(f"    - Vault & Operator Web UI: http://127.0.0.1:{v_port}")
    print(f"    - Standalone Data Node API: http://127.0.0.1:{d_port}")
    print("    - UDP Multicast Beacon:     224.0.0.251:8001")
    print("\n[*] Press Ctrl+C at any time to gracefully stop all node services.\n")

    # Process monitor loop
    try:
        while True:
            time.sleep(1)
            for name, proc in list(supervisor.processes.items()):
                if proc.poll() is not None:
                    print(f"[!] Warning: Process {name} exited with code {proc.returncode}")
    except KeyboardInterrupt:
        supervisor.stop_all()


if __name__ == "__main__":
    main()
