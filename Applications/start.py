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

# Ensure UTF-8 output formatting on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import time
import json
import signal
import socket
import shutil
import argparse
import subprocess
import threading
import webbrowser
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
    "requests"
]

OPTIONAL_PACKAGES = [
    "qrcode",
    "jinja2"
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
            try:
                cmd = [sys.executable, "-m", "pip", "install"] + missing
                subprocess.run(cmd, capture_output=True, timeout=10)
            except Exception:
                pass

    @staticmethod
    def is_port_in_use(port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex(('127.0.0.1', port)) == 0

    @staticmethod
    def get_local_ip_addresses() -> List[str]:
        ips = set()
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
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

        return sorted(list(ips))


def launch_browser_when_ready(port: int, use_https: bool = False, path: str = ""):
    """Spawns a daemon thread that waits for the web server to start, then launches the web browser."""
    def _worker():
        protocol = "https" if use_https else "http"
        url = f"{protocol}://127.0.0.1:{port}{path}"
        for _ in range(30):
            if PreflightManager.is_port_in_use(port):
                time.sleep(0.6)  # brief pause for router initialization
                print(f"\n[+] Opening web browser to Vault Node Sign-in: {url}")
                try:
                    webbrowser.open(url)
                except Exception as e:
                    print(f"[!] Note: Could not auto-launch browser ({e}). Please navigate to: {url}")
                return
            time.sleep(0.5)
        print(f"[!] Timed out waiting for port {port} to become active.")

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()


class NodeSupervisor:
    """Manages and monitors local child node processes."""

    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.running = False

    def start_process(self, name: str, cmd: List[str], cwd: str, port: int, launch_in_new_terminal: bool = False):
        if PreflightManager.is_port_in_use(port):
            print(f"[!] Port {port} is already in use. Assuming {name} is running or occupied.")
            return

        print(f"[*] Starting {name} on port {port}...")
        try:
            # If launch_in_new_terminal is requested (e.g. Data Nodes on Windows), spawn in a dedicated terminal window
            if launch_in_new_terminal and sys.platform == "win32":
                window_title = f"MADN {name} [Port {port}] - Live Activity Tracker"
                cmd_line = subprocess.list2cmdline(cmd)
                full_cmd = f'cmd.exe /k "title {window_title} && {cmd_line}"'
                proc = subprocess.Popen(
                    full_cmd,
                    cwd=cwd,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                self.processes[name] = proc
                print(f"[+] Spawned dedicated terminal tracking window: [{window_title}]")
                return

            # Default / Headless fallback: process group handling with stdout multiplexing
            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP

            proc = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=creation_flags
            )
            self.processes[name] = proc

            # Start thread to multiplex stdout
            def stream_logs(p_name, p_proc):
                for line in p_proc.stdout:
                    if not self.running:
                        break
                    line_clean = line.strip()
                    if line_clean:
                        print(f"[{p_name}] {line_clean}")

            t = threading.Thread(target=stream_logs, args=(name, proc), daemon=True)
            t.start()

        except Exception as e:
            print(f"[!] Failed to start {name}: {e}")

    def stop_all(self):
        self.running = False
        print("\n[*] Gracefully terminating node services...")
        for name, proc in list(self.processes.items()):
            try:
                if sys.platform == "win32":
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
                else:
                    proc.terminate()
                    proc.wait(timeout=3)
                print(f"[+] Stopped {name}.")
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass


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


def prompt_transport_protocol(cli_https: bool, cli_http: bool) -> bool:
    """
    Prompts the operator in the terminal to select HTTP or HTTPS if no CLI flag was passed.
    Returns True for HTTPS, False for HTTP.
    """
    if cli_https:
        return True
    if cli_http:
        return False

    # Non-interactive fallback (e.g. background automation, pipes, or tests)
    if not sys.stdin.isatty():
        return False

    print("\n-------------------------------------------------------")
    print("             SELECT TRANSPORT PROTOCOL                 ")
    print("-------------------------------------------------------")
    print("  [1] HTTP  - Recommended for Localhost / Zero Browser Warnings (Default)")
    print("  [2] HTTPS - Encrypted TLS 1.3 for LAN / Multi-device Wi-Fi Mesh")
    print("-------------------------------------------------------")
    
    try:
        choice = input("Select protocol [1/2] (Press Enter for HTTP): ").strip()
        if choice in ("2", "https", "HTTPS", "s", "S"):
            print("[*] Selected: HTTPS Mode (Encrypted TLS)")
            return True
        print("[*] Selected: HTTP Mode (Zero-Friction Localhost)")
        return False
    except (EOFError, KeyboardInterrupt):
        print("\n[*] Defaulting to HTTP Mode.")
        return False


def main():
    parser = argparse.ArgumentParser(description="MADN Portable Multi-Node Launcher")
    parser.add_argument("--all", action="store_true", help="Launch Vault Coordinator and all Data Nodes (Default)")
    parser.add_argument("--vault-only", action="store_true", help="Launch only Vault Coordinator (:8000)")
    parser.add_argument("--data-only", action="store_true", help="Launch only Data Node (:8002)")
    parser.add_argument("--status", action="store_true", help="Check status of all local node ports")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open web browser on startup")
    parser.add_argument("--headless", "--cli", action="store_true", help="Run headlessly and launch the interactive Sovereign Terminal Shell (cli.py)")
    parser.add_argument("--mesh-monitor", action="store_true", help="Launch the headless real-time UDP multicast mesh discovery monitor")
    parser.add_argument("--https", action="store_true", help="Enforce HTTPS TLS encryption (Self-signed X.509 certificates)")
    parser.add_argument("--http", action="store_true", help="Launch in clean HTTP mode for zero-friction browser access (Default)")
    parser.add_argument("--separate-terminals", action="store_true", default=True, help="Launch Data Nodes in dedicated tracking terminal windows (Default on Windows)")
    parser.add_argument("--single-terminal", action="store_true", help="Run all node services within this single unified terminal window")
    parser.add_argument("--create-node", nargs=3, metavar=("NAME", "TYPE", "PORT"), help="Generate a new standalone portable node package (e.g. --create-node Alpha data_node 8005)")
    args = parser.parse_args()

    # CLI command: Mesh Monitor
    if args.mesh_monitor:
        mesh_script = os.path.join(DATA_NODE_DIR, "mesh_monitor.py")
        subprocess.run([sys.executable, mesh_script])
        return

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

    # Terminal tracking mode determination
    use_separate_terminals = (sys.platform == "win32") and not args.single_terminal

    # Headless mode suppresses browser launch
    no_browser = args.no_browser or args.headless

    # Protocol selection (Interactive prompt if neither --http nor --https was explicitly passed)
    if args.headless:
        use_https = args.https
    else:
        use_https = prompt_transport_protocol(cli_https=args.https, cli_http=args.http)
    scheme = "https" if use_https else "http"
    os.environ["MADN_HTTPS_ENABLED"] = "1" if use_https else "0"

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
    print(f"[*] Applications Root:     {APPLICATIONS_DIR}")
    print(f"[*] Transport Protocol:    {scheme.upper()}")
    print(f"[*] Data Node Tracking:    {'Dedicated Terminal Windows' if use_separate_terminals else 'Unified Console Stream'}")

    cert_file, key_file = None, None
    if use_https:
        try:
            from tls_manager import ensure_ssl_certificates
            cert_file, key_file = ensure_ssl_certificates()
        except Exception as e:
            print(f"[!] Warning: Could not initialize TLS certificates ({e}). Falling back to HTTP.")
            use_https = False
            scheme = "http"

    start_vault = not args.data_only
    start_data = not args.vault_only

    if start_vault:
        vault_cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(v_port)]
        if use_https and cert_file and key_file:
            vault_cmd.extend(["--ssl-keyfile", key_file, "--ssl-certfile", cert_file])
        supervisor.start_process("Vault-Node", vault_cmd, cwd=BACKEND_DIR, port=v_port, launch_in_new_terminal=False)
        if not no_browser:
            launch_browser_when_ready(v_port, use_https=use_https)

    if start_data:
        data_cmd = [sys.executable, "data_node.py", str(d_port)]
        if use_https and cert_file and key_file:
            data_cmd.extend(["--ssl-keyfile", key_file, "--ssl-certfile", cert_file])
        supervisor.start_process("Data-Node-Primary", data_cmd, cwd=DATA_NODE_DIR, port=d_port, launch_in_new_terminal=use_separate_terminals)

    # Start any configured additional nodes
    for add_node in cfg.get("additional_nodes", []):
        if add_node.get("enabled", True):
            node_dir = add_node.get("path")
            node_name = add_node.get("name")
            node_port = add_node.get("port")
            if node_dir and os.path.exists(node_dir):
                cmd = [sys.executable, "server.py", str(node_port)]
                if use_https and cert_file and key_file:
                    cmd.extend(["--ssl-keyfile", key_file, "--ssl-certfile", cert_file])
                supervisor.start_process(node_name, cmd, cwd=node_dir, port=node_port, launch_in_new_terminal=use_separate_terminals)

    local_ips = PreflightManager.get_local_ip_addresses()

    print(f"\n[+] System services initialized successfully in {scheme.upper()} mode!")
    print("\n-------------------------------------------------------")
    print(f"               NETWORK ACCESS ADDRESSES ({scheme.upper()})        ")
    print("-------------------------------------------------------")
    print(f"  * Local Host (This Machine):      {scheme}://127.0.0.1:{v_port}")
    if local_ips:
        print("  * LAN / Wi-Fi URLs (Phones, Tablets, Other PCs):")
        for ip in local_ips:
            print(f"      -> {scheme}://{ip}:{v_port}")
    print(f"  * Standalone Data Node API:       {scheme}://127.0.0.1:{d_port}")
    print("  * UDP Multicast Beacon:           224.0.0.251:8001")
    print("-------------------------------------------------------")
    if use_https:
        print("[!] Note: When using HTTPS on localhost, Chrome/Edge may show a self-signed warning.")
        print("    -> To bypass: click 'Advanced' > 'Proceed to 127.0.0.1 (unsafe)' or type 'thisisunsafe'")
        print("    -> Or launch in clean HTTP mode: python start.py")
    
    if args.headless:
        print("\n[*] Initializing Sovereign Headless Terminal Shell...")
        time.sleep(1.2)
        try:
            from cli import MadnClient, start_repl_shell
            client = MadnClient(vault_url=f"{scheme}://127.0.0.1:{v_port}", data_url=f"{scheme}://127.0.0.1:{d_port}")
            start_repl_shell(client)
        except Exception as e:
            print(f"[!] CLI Shell error: {e}")
        finally:
            supervisor.stop_all()
            return

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
