#!/usr/bin/env python3
"""
MADN Standalone Data Node Headless CLI
======================================
Interact directly with any MADN Data Node instance via terminal over REST/JSON.
Can connect to local (:8002) or any remote Data Node over LAN/Internet.

Usage:
  python data_node_cli.py status [--url http://127.0.0.1:8002]
  python data_node_cli.py stats
  python data_node_cli.py put <collection> <key> <data>
  python data_node_cli.py get <collection> <key>
  python data_node_cli.py list <collection>
  python data_node_cli.py activate
  python data_node_cli.py deactivate
  python data_node_cli.py sync-currencies
  python data_node_cli.py benchmark [--n 100]
"""

import sys
import os
import time
import json
import argparse
import requests

# Windows terminal UTF-8 encoding support
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def format_json(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="MADN Data Node Headless CLI")
    parser.add_argument("--url", default="http://127.0.0.1:8002", help="Target Data Node URL (default: http://127.0.0.1:8002)")
    subparsers = parser.add_subparsers(dest="command", help="Data Node commands")

    # Status / Health
    subparsers.add_parser("status", help="Get node status and health")
    subparsers.add_parser("stats", help="Get storage engine and disk capacity metrics")

    # Storage operations
    p_put = subparsers.add_parser("put", help="Put/encrypt a record in storage")
    p_put.add_argument("collection", help="Target collection name")
    p_put.add_argument("key", help="Unique record key")
    p_put.add_argument("data", help="JSON data payload or string")

    p_get = subparsers.add_parser("get", help="Get/decrypt a record by key")
    p_get.add_argument("collection", help="Collection name")
    p_get.add_argument("key", help="Record key")

    p_list = subparsers.add_parser("list", help="List records in a collection")
    p_list.add_argument("collection", help="Collection name")
    p_list.add_argument("--limit", type=int, default=50, help="Max records (default: 50)")

    # Lifecycle
    subparsers.add_parser("activate", help="Activate Data Node (enables beacon & storage writes)")
    subparsers.add_parser("deactivate", help="Deactivate Data Node (standby mode)")

    # Currencies
    subparsers.add_parser("currencies", help="Fetch currency reference catalog")
    subparsers.add_parser("sync-currencies", help="Trigger background collector sync for 170+ currencies")

    # Benchmark
    p_bench = subparsers.add_parser("benchmark", help="Run storage throughput benchmark")
    p_bench.add_argument("--n", type=int, default=50, help="Number of records (default: 50)")

    args = parser.parse_args()
    base_url = args.url.rstrip("/")

    if not args.command:
        parser.print_help()
        sys.exit(0)

    try:
        if args.command == "status":
            r = requests.get(f"{base_url}/api/node/status", timeout=5)
            print(format_json(r.json()))

        elif args.command == "stats":
            r = requests.get(f"{base_url}/api/storage/stats", timeout=5)
            print(format_json(r.json()))

        elif args.command == "put":
            payload = {"collection": args.collection, "key": args.key, "data": args.data}
            r = requests.post(f"{base_url}/api/storage/put", json=payload, timeout=5)
            print(format_json(r.json()))

        elif args.command == "get":
            r = requests.get(f"{base_url}/api/storage/get", params={"collection": args.collection, "key": args.key}, timeout=5)
            if r.status_code == 200:
                print(format_json(r.json()))
            else:
                print(f"[!] Record not found: {r.status_code}")

        elif args.command == "list":
            r = requests.get(f"{base_url}/api/storage/list", params={"collection": args.collection, "limit": args.limit}, timeout=5)
            print(format_json(r.json()))

        elif args.command == "activate":
            r = requests.post(f"{base_url}/api/node/activate", timeout=5)
            print(format_json(r.json()))

        elif args.command == "deactivate":
            r = requests.post(f"{base_url}/api/node/deactivate", timeout=5)
            print(format_json(r.json()))

        elif args.command == "currencies":
            r = requests.get(f"{base_url}/api/reference/currencies", timeout=5)
            print(format_json(r.json()))

        elif args.command == "sync-currencies":
            r = requests.post(f"{base_url}/api/reference/currencies/sync", timeout=10)
            print(format_json(r.json()))

        elif args.command == "benchmark":
            print(f"[*] Running AES-GCM + SQLite WAL storage benchmark ({args.n} writes)...")
            start = time.perf_counter()
            for i in range(args.n):
                payload = {"collection": "bench_test", "key": f"key_{i}", "data": json.dumps({"iter": i, "val": i * 1.5, "ts": time.time()})}
                requests.post(f"{base_url}/api/storage/put", json=payload, timeout=5)
            dur = time.perf_counter() - start
            ops = args.n / dur
            print(f"[+] Completed {args.n} encrypted writes in {dur:.3f}s ({ops:.1f} ops/sec)")

    except requests.exceptions.ConnectionError:
        print(f"[!] Error: Could not connect to Data Node at {base_url}. Ensure the node process is running.")
        sys.exit(1)
    except Exception as e:
        print(f"[!] Error executing command: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
