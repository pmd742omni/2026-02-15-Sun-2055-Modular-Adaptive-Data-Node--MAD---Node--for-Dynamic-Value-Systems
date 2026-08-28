#!/usr/bin/env python3
"""
MADN Sovereign Headless Terminal Interface & REPL Shell
======================================================
Unified command-line interface and interactive REPL shell for headless,
air-gapped, and automated administration of the Modular Adaptive Data Node
(MADN) ecosystem without requiring a graphical web browser.

Usage:
  Interactive Shell Mode:
    python cli.py
    python cli.py shell

  Direct Command Mode:
    python cli.py auth login <username> [password]
    python cli.py auth status
    python cli.py vault balances
    python cli.py vault transfer <recipient> <amount> <currency>
    python cli.py vault rates
    python cli.py store list
    python cli.py store products
    python cli.py store checkout <product_id> <qty> [currency]
    python cli.py agri fields
    python cli.py security visitors
    python cli.py data status
    python cli.py data put <collection> <key> <data>
    python cli.py data get <collection> <key>
    python cli.py mesh scan
    python cli.py system status
"""

import sys
import os
import time
import json
import socket
import struct
import getpass
import argparse
import requests
from typing import Optional, Dict, Any

# Windows terminal UTF-8 support
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cli_session.json")
DEFAULT_VAULT_URL = "http://127.0.0.1:8000"
DEFAULT_DATA_URL = "http://127.0.0.1:8002"
MULTICAST_GROUP = "224.0.0.251"
MULTICAST_PORT = 8001


class SessionManager:
    """Manages headless authentication session cookies and tokens."""
    @staticmethod
    def save_session(data: Dict[str, Any], cookies: Dict[str, str], vault_url: str):
        session_payload = {
            "user": data,
            "cookies": cookies,
            "vault_url": vault_url,
            "saved_at": time.time()
        }
        try:
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump(session_payload, f, indent=2)
        except Exception:
            pass

    @staticmethod
    def load_session() -> Optional[Dict[str, Any]]:
        if not os.path.exists(SESSION_FILE):
            return None
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    @staticmethod
    def clear_session():
        if os.path.exists(SESSION_FILE):
            try:
                os.remove(SESSION_FILE)
            except Exception:
                pass


class MadnClient:
    """HTTP Client for communicating with Vault Node and Data Node."""
    def __init__(self, vault_url: str = DEFAULT_VAULT_URL, data_url: str = DEFAULT_DATA_URL):
        self.vault_url = vault_url.rstrip("/")
        self.data_url = data_url.rstrip("/")
        self.session = requests.Session()
        
        # Load existing cookies if present
        saved = SessionManager.load_session()
        if saved and "cookies" in saved:
            for k, v in saved["cookies"].items():
                self.session.cookies.set(k, v)

    def login(self, username: str, password: str) -> Dict[str, Any]:
        url = f"{self.vault_url}/api/auth/login"
        resp = self.session.post(url, json={"username": username, "password": password}, timeout=10)
        if resp.status_code != 200:
            err = resp.json().get("detail", "Authentication failed") if resp.headers.get("content-type", "").startswith("application/json") else resp.text
            raise Exception(f"Login failed ({resp.status_code}): {err}")
        data = resp.json()
        cookies_dict = requests.utils.dict_from_cookiejar(self.session.cookies)
        SessionManager.save_session(data, cookies_dict, self.vault_url)
        return data

    def logout(self):
        try:
            self.session.post(f"{self.vault_url}/api/auth/logout", timeout=5)
        except Exception:
            pass
        SessionManager.clear_session()

    def get_session(self) -> Optional[Dict[str, Any]]:
        try:
            resp = self.session.get(f"{self.vault_url}/api/auth/session", timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return None

    def get_balances(self) -> Dict[str, Any]:
        resp = self.session.get(f"{self.vault_url}/api/banking/balances", timeout=5)
        if resp.status_code != 200:
            raise Exception(f"Failed to fetch balances: {resp.status_code} {resp.text}")
        return resp.json()

    def transfer(self, recipient: str, amount: float, currency: str, note: str = "") -> Dict[str, Any]:
        payload = {"to_user": recipient, "amount": amount, "currency": currency, "note": note}
        resp = self.session.post(f"{self.vault_url}/api/banking/transfer", json=payload, timeout=8)
        if resp.status_code != 200:
            raise Exception(f"Transfer failed: {resp.status_code} {resp.text}")
        return resp.json()

    def get_rates(self) -> Dict[str, Any]:
        resp = self.session.get(f"{self.vault_url}/api/banking/rates", timeout=5)
        if resp.status_code != 200:
            raise Exception(f"Failed to fetch rates: {resp.status_code}")
        return resp.json()

    def get_stores(self) -> list:
        resp = self.session.get(f"{self.vault_url}/api/business/stores", timeout=5)
        if resp.status_code != 200:
            raise Exception(f"Failed to fetch stores: {resp.status_code}")
        return resp.json()

    def get_products(self, business_id: Optional[str] = None) -> list:
        params = {"business_id": business_id} if business_id else {}
        resp = self.session.get(f"{self.vault_url}/api/business/products", params=params, timeout=5)
        if resp.status_code != 200:
            raise Exception(f"Failed to fetch products: {resp.status_code}")
        return resp.json()

    def pos_checkout(self, product_id: int, quantity: float, currency: str = "USD") -> Dict[str, Any]:
        payload = {"items": [{"product_id": product_id, "quantity": quantity}], "payment_currency": currency}
        resp = self.session.post(f"{self.vault_url}/api/pos/checkout", json=payload, timeout=8)
        if resp.status_code != 200:
            raise Exception(f"POS checkout failed: {resp.status_code} {resp.text}")
        return resp.json()

    def get_fields(self) -> list:
        resp = self.session.get(f"{self.vault_url}/api/agriculture/fields", timeout=5)
        if resp.status_code != 200:
            raise Exception(f"Failed to fetch agri fields: {resp.status_code}")
        return resp.json()

    def get_visitors(self) -> list:
        resp = self.session.get(f"{self.vault_url}/api/security/visitors", timeout=5)
        if resp.status_code != 200:
            raise Exception(f"Failed to fetch visitor log: {resp.status_code}")
        return resp.json()

    def security_checkin(self, full_name: str, host_name: str, purpose: str = "Visit") -> Dict[str, Any]:
        payload = {"full_name": full_name, "host_name": host_name, "purpose": purpose, "checkpoint_id": "MAIN_GATE"}
        resp = self.session.post(f"{self.vault_url}/api/security/visitors/checkin", json=payload, timeout=5)
        if resp.status_code != 200:
            raise Exception(f"Visitor check-in failed: {resp.status_code}")
        return resp.json()

    def security_broadcast(self, message: str, level: str = "INFO") -> Dict[str, Any]:
        payload = {"message": message, "severity": level}
        resp = self.session.post(f"{self.vault_url}/api/security/broadcast", json=payload, timeout=5)
        if resp.status_code != 200:
            raise Exception(f"Broadcast failed: {resp.status_code}")
        return resp.json()

    def get_data_node_status(self) -> Dict[str, Any]:
        resp = requests.get(f"{self.data_url}/api/node/status", timeout=5)
        return resp.json()

    def put_data_node(self, collection: str, key: str, data: str) -> Dict[str, Any]:
        resp = requests.post(f"{self.data_url}/api/storage/put", json={"collection": collection, "key": key, "data": data}, timeout=5)
        return resp.json()

    def get_data_node(self, collection: str, key: str) -> Dict[str, Any]:
        resp = requests.get(f"{self.data_url}/api/storage/get", params={"collection": collection, "key": key}, timeout=5)
        return resp.json()

    def list_data_node(self, collection: str, limit: int = 50) -> Dict[str, Any]:
        resp = requests.get(f"{self.data_url}/api/storage/list", params={"collection": collection, "limit": limit}, timeout=5)
        return resp.json()

    def sync_currencies(self) -> Dict[str, Any]:
        resp = requests.post(f"{self.data_url}/api/reference/currencies/sync", timeout=10)
        return resp.json()


def scan_mesh_peers(duration: float = 3.0) -> list:
    """Passively listens to UDP multicast beacons and returns discovered peers."""
    nodes = {}
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", MULTICAST_PORT))
        mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock.settimeout(0.5)

        start = time.time()
        while time.time() - start < duration:
            try:
                data, addr = sock.recvfrom(4096)
                payload = json.loads(data.decode("utf-8"))
                nid = payload.get("node_id", addr[0])
                nodes[nid] = {
                    "node_id": nid,
                    "node_type": payload.get("node_type", "node"),
                    "ip": payload.get("ip", addr[0]),
                    "port": payload.get("port", "?"),
                    "metadata": payload.get("metadata", {})
                }
            except socket.timeout:
                continue
            except Exception:
                break
        sock.close()
    except Exception as e:
        print(f"[!] UDP Multicast listen warning: {e}")
    return list(nodes.values())


def print_table(headers: list, rows: list):
    """Utility to print a cleanly formatted ASCII table."""
    if not rows:
        print("  (No records found)")
        return
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val)))
    
    header_line = "  " + " | ".join(f"{h:<{col_widths[i]}}" for i, h in enumerate(headers))
    sep_line = "  " + "-+-".join("-" * col_widths[i] for i in range(len(headers)))
    print(header_line)
    print(sep_line)
    for row in rows:
        print("  " + " | ".join(f"{str(val):<{col_widths[i]}}" for i, val in enumerate(row)))


def handle_command(client: MadnClient, cmd_tokens: list):
    if not cmd_tokens:
        return

    cmd = cmd_tokens[0].lower()

    # --- AUTH SUBCOMMANDS ---
    if cmd == "auth":
        if len(cmd_tokens) < 2:
            print("Usage: auth [login <user> [pass] | status | whoami | logout]")
            return
        sub = cmd_tokens[1].lower()
        if sub == "login":
            user = cmd_tokens[2] if len(cmd_tokens) > 2 else input("Username: ").strip()
            pw = cmd_tokens[3] if len(cmd_tokens) > 3 else getpass.getpass("Password: ")
            try:
                data = client.login(user, pw)
                print(f"[+] Successfully authenticated as: {data.get('username')} (Role: {data.get('role', 'operator').upper()})")
            except Exception as e:
                print(f"[!] {e}")
        elif sub in ("status", "whoami"):
            sess = client.get_session()
            if sess:
                print(f"[+] Active Session: {sess.get('username')} | Role: {sess.get('role')} | Operator ID: {sess.get('user_id', 'N/A')}")
            else:
                print("[-] Not authenticated. Use 'auth login <user>' to sign in.")
        elif sub == "logout":
            client.logout()
            print("[+] Logged out and cleared local credentials.")

    # --- VAULT SUBCOMMANDS ---
    elif cmd == "vault":
        if len(cmd_tokens) < 2:
            print("Usage: vault [balances | transfer <to> <amt> <curr> | rates | vouchers | audit]")
            return
        sub = cmd_tokens[1].lower()
        if sub in ("balances", "balance", "bal"):
            try:
                data = client.get_balances()
                print("\n=== MULTI-CURRENCY VAULT BALANCES ===")
                rows = []
                for curr, val in data.get("balances", {}).items():
                    rows.append([curr, f"{val:,.2f}"])
                print_table(["Currency", "Available Balance"], rows)
                print()
            except Exception as e:
                print(f"[!] {e}")
        elif sub in ("rates", "exchange"):
            try:
                data = client.get_rates()
                print("\n=== LIVE CURRENCY CONVERSION RATES ===")
                rows = []
                for pair, rate in data.get("rates", {}).items():
                    rows.append([pair, f"{rate:.6f}"])
                print_table(["Currency Pair", "Exchange Rate"], rows)
                print()
            except Exception as e:
                print(f"[!] {e}")
        elif sub == "transfer":
            if len(cmd_tokens) < 5:
                print("Usage: vault transfer <recipient> <amount> <currency> [note]")
                return
            to_user = cmd_tokens[2]
            amt = float(cmd_tokens[3])
            curr = cmd_tokens[4].upper()
            note = " ".join(cmd_tokens[5:]) if len(cmd_tokens) > 5 else "CLI Transfer"
            try:
                res = client.transfer(to_user, amt, curr, note)
                print(f"[+] Transfer successful: {amt} {curr} sent to {to_user}. Ref: {res.get('transaction_id', 'TX')}")
            except Exception as e:
                print(f"[!] {e}")

    # --- STORE & POS SUBCOMMANDS ---
    elif cmd == "store":
        if len(cmd_tokens) < 2:
            print("Usage: store [list | products [biz_id] | checkout <product_id> <qty> [curr]]")
            return
        sub = cmd_tokens[1].lower()
        if sub == "list":
            try:
                stores = client.get_stores()
                print("\n=== REGISTERED SOVEREIGN STORES ===")
                rows = [[s.get("id"), s.get("name"), s.get("currency", "USD"), s.get("owner_id", "N/A")] for s in stores]
                print_table(["ID", "Store Name", "Settlement", "Owner"], rows)
                print()
            except Exception as e:
                print(f"[!] {e}")
        elif sub in ("products", "items"):
            biz_id = cmd_tokens[2] if len(cmd_tokens) > 2 else None
            try:
                prods = client.get_products(biz_id)
                print("\n=== STORE PRODUCT CATALOG & DECAY PRICING ===")
                rows = [[p.get("id"), p.get("name"), f"${p.get('price', 0):.2f}", p.get("stock", 0), p.get("category", "General")] for p in prods]
                print_table(["ID", "Item Name", "Current Price", "In Stock", "Category"], rows)
                print()
            except Exception as e:
                print(f"[!] {e}")
        elif sub == "checkout":
            if len(cmd_tokens) < 4:
                print("Usage: store checkout <product_id> <qty> [currency]")
                return
            pid = int(cmd_tokens[2])
            qty = float(cmd_tokens[3])
            curr = cmd_tokens[4].upper() if len(cmd_tokens) > 4 else "USD"
            try:
                res = client.pos_checkout(pid, qty, curr)
                print(f"[+] POS Sale Completed! Receipt ID: {res.get('receipt_id', 'N/A')} | Total: {res.get('total_paid', 'N/A')} {curr}")
            except Exception as e:
                print(f"[!] {e}")

    # --- DATA NODE SUBCOMMANDS ---
    elif cmd == "data":
        if len(cmd_tokens) < 2:
            print("Usage: data [status | put <coll> <key> <data> | get <coll> <key> | list <coll> | sync]")
            return
        sub = cmd_tokens[1].lower()
        if sub == "status":
            try:
                st = client.get_data_node_status()
                print(json.dumps(st, indent=2))
            except Exception as e:
                print(f"[!] Data Node connection error: {e}")
        elif sub == "put":
            if len(cmd_tokens) < 5:
                print("Usage: data put <collection> <key> <data>")
                return
            res = client.put_data_node(cmd_tokens[2], cmd_tokens[3], cmd_tokens[4])
            print(json.dumps(res, indent=2))
        elif sub == "get":
            if len(cmd_tokens) < 4:
                print("Usage: data get <collection> <key>")
                return
            res = client.get_data_node(cmd_tokens[2], cmd_tokens[3])
            print(json.dumps(res, indent=2))
        elif sub == "list":
            if len(cmd_tokens) < 3:
                print("Usage: data list <collection> [limit]")
                return
            limit = int(cmd_tokens[3]) if len(cmd_tokens) > 3 else 50
            res = client.list_data_node(cmd_tokens[2], limit)
            print(json.dumps(res, indent=2))
        elif sub in ("sync", "sync-currencies"):
            print("[*] Triggering Data Node global currency collector sync...")
            res = client.sync_currencies()
            print(json.dumps(res, indent=2))

    # --- MESH DISCOVERY SCAN ---
    elif cmd == "mesh":
        print("[*] Scanning UDP Multicast Channel (224.0.0.251:8001) for active peer nodes...")
        peers = scan_mesh_peers(duration=2.5)
        print(f"\n=== DISCOVERED MESH PEER TOPOLOGY ({len(peers)} Nodes Detected) ===")
        rows = [[p["node_id"], p["node_type"], f"{p['ip']}:{p['port']}", p["metadata"].get("free_mb", "N/A")] for p in peers]
        print_table(["Node ID", "Node Type", "Network Address", "Free Space (MB)"], rows)
        print()

    # --- AGRICULTURE ---
    elif cmd == "agri":
        if len(cmd_tokens) < 2 or cmd_tokens[1].lower() in ("fields", "plots"):
            try:
                fields = client.get_fields()
                print("\n=== REGISTERED AGRICULTURAL FIELDS & CROPS ===")
                rows = [[f.get("id"), f.get("name"), f.get("crop_type", "N/A"), f"{f.get('area_hectares', 0)} ha", f.get("health_status", "GOOD")] for f in fields]
                print_table(["Field ID", "Field Name", "Crop", "Area", "Status"], rows)
                print()
            except Exception as e:
                print(f"[!] {e}")

    # --- SECURITY ---
    elif cmd == "security":
        if len(cmd_tokens) < 2:
            print("Usage: security [visitors | checkin <name> <host> [purpose] | broadcast <message>]")
            return
        sub = cmd_tokens[1].lower()
        if sub in ("visitors", "log"):
            try:
                visitors = client.get_visitors()
                print("\n=== SECURITY CHECKPOINT VISITOR REGISTRY ===")
                rows = [[v.get("id"), v.get("full_name"), v.get("host_name"), v.get("purpose", "Visit"), v.get("status", "ACTIVE")] for v in visitors]
                print_table(["ID", "Visitor Name", "Host Contact", "Purpose", "State"], rows)
                print()
            except Exception as e:
                print(f"[!] {e}")
        elif sub == "checkin":
            if len(cmd_tokens) < 4:
                print("Usage: security checkin <full_name> <host_name> [purpose]")
                return
            fname = cmd_tokens[2]
            hname = cmd_tokens[3]
            purpose = " ".join(cmd_tokens[4:]) if len(cmd_tokens) > 4 else "Visit"
            try:
                res = client.security_checkin(fname, hname, purpose)
                print(f"[+] Visitor Registered: {fname} (Host: {hname})")
            except Exception as e:
                print(f"[!] {e}")
        elif sub == "broadcast":
            if len(cmd_tokens) < 3:
                print("Usage: security broadcast <message>")
                return
            msg = " ".join(cmd_tokens[2:])
            try:
                res = client.security_broadcast(msg)
                print(f"[+] Broadcast transmitted: {msg}")
            except Exception as e:
                print(f"[!] {e}")

    # --- SYSTEM HEALTH ---
    elif cmd == "system":
        print("\n=== TRI-NODE SYSTEM HEALTH CHECK ===")
        # Vault Node check
        try:
            r = requests.get(f"{client.vault_url}/api/network/info", timeout=3)
            v_stat = f"🟢 ONLINE ({client.vault_url})"
        except Exception:
            v_stat = f"🔴 OFFLINE ({client.vault_url})"
        
        # Data Node check
        try:
            r = requests.get(f"{client.data_url}/health", timeout=3)
            d_stat = f"🟢 ONLINE ({client.data_url})"
        except Exception:
            d_stat = f"🔴 OFFLINE ({client.data_url})"

        print(f"  * Vault Coordinator:   {v_stat}")
        print(f"  * Primary Data Node:   {d_stat}")
        print(f"  * Mesh Multicast:      224.0.0.251:8001 (Active Beaconing)")
        print()

    elif cmd in ("help", "?"):
        print_help()

    elif cmd in ("cls", "clear"):
        os.system("cls" if os.name == "nt" else "clear")

    else:
        print(f"[!] Unknown command '{cmd}'. Type 'help' for a list of commands.")


def print_help():
    print("""
MADN Headless Terminal Commands:
-------------------------------------------------------------------------------
  auth login <user> [pass]        Authenticate operator session headlessly
  auth status / whoami            Inspect active operator session & role
  auth logout                     Clear active session credentials

  vault balances                  List all multi-currency account balances
  vault transfer <to> <amt> <c>   Execute direct peer-to-peer balance transfer
  vault rates                     Inspect real-time currency conversion rates

  store list                      List registered sovereign businesses/stores
  store products [biz_id]         View store inventory and decay pricing
  store checkout <id> <qty> [c]   Execute direct touchless POS checkout

  agri fields                     List agricultural field plots & crop states
  security visitors               Inspect visitor check-in registry log
  security checkin <name> <host>  Register new visitor at gate checkpoint
  security broadcast <message>    Transmit community-wide alert broadcast

  data status                     Query standalone Data Node storage & health
  data put <coll> <key> <data>    Encrypt and write record to Data Node
  data get <coll> <key>           Decrypt and fetch record from Data Node
  data list <coll> [limit]        List all stored records in collection
  data sync                       Trigger global currency sync (170+ fiats)

  mesh scan                       Actively scan UDP mesh beacons for live peers
  system status                   Inspect overall tri-node infrastructure health
  clear                           Clear terminal screen
  exit / quit                     Exit headless terminal shell
-------------------------------------------------------------------------------
""")


def start_repl_shell(client: MadnClient):
    """Runs the interactive REPL shell."""
    os.system("cls" if os.name == "nt" else "clear")
    print("=" * 76)
    print("   🌐  MAD-NODE SOVEREIGN HEADLESS TERMINAL INTERFACE & SHELL")
    print("       Modular Adaptive Data Node for Dynamic Value Systems")
    print("=" * 76)
    sess = client.get_session()
    user_str = sess.get("username", "guest") if sess else "guest"
    print(f"  * Operator:   {user_str.upper()}")
    print(f"  * Vault Node: {client.vault_url}")
    print(f"  * Data Node:  {client.data_url}")
    print("  * Type 'help' for commands, 'exit' or Ctrl+C to quit.")
    print("=" * 76 + "\n")

    while True:
        try:
            sess = client.get_session()
            user_str = sess.get("username", "guest") if sess else "guest"
            prompt = f"MADN [{user_str}@{client.vault_url.split('://')[-1]}] > "
            line = input(prompt).strip()
            if not line:
                continue
            if line.lower() in ("exit", "quit", "q"):
                print("\n[+] Exiting MADN Headless Terminal Shell.")
                break
            tokens = line.split()
            handle_command(client, tokens)
        except (KeyboardInterrupt, EOFError):
            print("\n[+] Exiting MADN Headless Terminal Shell.")
            break
        except Exception as e:
            print(f"[!] Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="MADN Headless Terminal Interface")
    parser.add_argument("--vault-url", default=DEFAULT_VAULT_URL, help=f"Vault Node URL (default: {DEFAULT_VAULT_URL})")
    parser.add_argument("--data-url", default=DEFAULT_DATA_URL, help=f"Data Node URL (default: {DEFAULT_DATA_URL})")
    parser.add_argument("command", nargs="*", help="Direct command to execute (omit for interactive shell)")
    args = parser.parse_args()

    client = MadnClient(vault_url=args.vault_url, data_url=args.data_url)

    if not args.command or (len(args.command) == 1 and args.command[0].lower() == "shell"):
        start_repl_shell(client)
    else:
        handle_command(client, args.command)


if __name__ == "__main__":
    main()
