#!/usr/bin/env python3
"""
MADN Headless Mesh Discovery Monitor
=====================================
Live terminal dashboard that continuously listens on UDP multicast (224.0.0.251:8001)
to discover and display real-time peer topology across all active MADN Data Nodes,
Vault Nodes, and Custom Hardware Nodes.
"""

import sys
import os
import time
import json
import socket
import struct
import threading
from datetime import datetime

# Windows terminal UTF-8 encoding support
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MULTICAST_GROUP = "224.0.0.251"
MULTICAST_PORT = 8001

discovered_nodes = {}
packet_log = []
lock = threading.Lock()
running = True


def listen_multicast():
    global running
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Windows-specific socket reuse
        if hasattr(socket, "SO_REUSEPORT"):
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except Exception:
                pass

        sock.bind(("", MULTICAST_PORT))

        mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock.settimeout(1.0)
    except Exception as e:
        print(f"[!] Socket initialization error: {e}")
        return

    while running:
        try:
            data, addr = sock.recvfrom(4096)
            payload = json.loads(data.decode("utf-8"))
            node_id = payload.get("node_id", f"unknown-{addr[0]}")
            now = time.time()
            now_str = datetime.now().strftime("%H:%M:%S")

            with lock:
                discovered_nodes[node_id] = {
                    "node_id": node_id,
                    "node_type": payload.get("node_type", "unknown"),
                    "ip": payload.get("ip", addr[0]),
                    "port": payload.get("port", "?"),
                    "last_seen": now,
                    "last_seen_str": now_str,
                    "metadata": payload.get("metadata", {})
                }
                packet_log.append(f"[{now_str}] 📡 Heartbeat from {node_id} ({addr[0]}:{payload.get('port', '?')}) [{payload.get('node_type', 'node')}]")
                if len(packet_log) > 12:
                    packet_log.pop(0)
        except socket.timeout:
            continue
        except Exception as e:
            if running:
                continue

    try:
        sock.close()
    except Exception:
        pass


def render_dashboard():
    while running:
        os.system("cls" if os.name == "nt" else "clear")
        now = time.time()
        print("=" * 76)
        print("  🛰️  MAD-NODE HEADLESS MESH DISCOVERY MONITOR (REAL-TIME TOPOLOGY)")
        print("=" * 76)
        print(f"  * Multicast Channel:   {MULTICAST_GROUP}:{MULTICAST_PORT}")
        print(f"  * Local Monitor Time:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 76)

        with lock:
            active_count = 0
            print(f"  {'NODE ID':<24} {'TYPE':<14} {'ADDRESS':<18} {'STATUS':<10} {'SEEN'}")
            print("  " + "-" * 72)

            if not discovered_nodes:
                print("  [Waiting for incoming UDP Multicast Beacons on 224.0.0.251:8001...]")
            else:
                for nid, info in sorted(discovered_nodes.items()):
                    age = now - info["last_seen"]
                    is_active = info["metadata"].get("is_active", True)
                    
                    if age < 15:
                        status = "🟢 ACTIVE" if is_active else "🟡 STANDBY"
                        active_count += 1
                    elif age < 35:
                        status = "🟠 STALE"
                    else:
                        status = "🔴 OFFLINE"

                    addr_str = f"{info['ip']}:{info['port']}"
                    age_str = f"{int(age)}s ago" if age < 60 else f"{int(age//60)}m ago"
                    print(f"  {nid:<24} {info['node_type']:<14} {addr_str:<18} {status:<10} {age_str}")
                    
                    # Storage stats if available
                    meta = info.get("metadata", {})
                    if "free_mb" in meta:
                        print(f"    └─ Storage: {meta.get('storage_engine', 'sqlite_wal')} | Free Space: {meta.get('free_mb')} MB | Path: {meta.get('db_path', 'default')}")

            print("=" * 76)
            print("  📜 LIVE PACKET STREAM (LAST 10 BEACONS):")
            print("  " + "-" * 72)
            if not packet_log:
                print("  (No packets received yet)")
            else:
                for line in packet_log[-8:]:
                    print(f"  {line}")

        print("=" * 76)
        print("  [Press Ctrl+C to exit headless mesh monitor]")
        time.sleep(2.0)


def main():
    global running
    t = threading.Thread(target=listen_multicast, daemon=True)
    t.start()

    try:
        render_dashboard()
    except KeyboardInterrupt:
        running = False
        print("\n[+] Exiting Mesh Discovery Monitor.")
        sys.exit(0)


if __name__ == "__main__":
    main()
