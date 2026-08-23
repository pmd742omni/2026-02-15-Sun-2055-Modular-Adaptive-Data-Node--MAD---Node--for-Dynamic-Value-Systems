"""
Node Discovery & Cluster Topology Manager for Vault Node
Listens for UDP Multicast discovery announcements from Data Nodes across the network,
executes health checks, and registers active storage workers.
"""

import os
import sys
import time
import logging
import threading
from typing import Dict, Any, List
import requests

# Add Data Node directory to path to share beacon module if needed
DATA_NODE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Data_Node"))
if DATA_NODE_DIR not in sys.path:
    sys.path.append(DATA_NODE_DIR)

try:
    from beacon import BeaconListener
except ImportError:
    # Inline fallback if beacon module is isolated
    BeaconListener = None

logger = logging.getLogger("madn.vault.discovery")


class NodeDiscoveryManager:
    """Manages discovery and live topology of cluster nodes."""

    def __init__(self):
        self.listener = None
        self.registered_nodes: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self._lock = threading.Lock()

    def _on_node_beacon(self, payload: dict):
        node_id = payload.get("node_id")
        ip = payload.get("ip") or payload.get("sender_addr")
        port = payload.get("port")
        node_type = payload.get("node_type", "unknown")

        if not node_id or not ip or not port:
            return

        with self._lock:
            if node_id not in self.registered_nodes:
                logger.info(f"Discovered new {node_type}: {node_id} at {ip}:{port}")
            self.registered_nodes[node_id] = {
                "node_id": node_id,
                "node_type": node_type,
                "ip": ip,
                "port": port,
                "last_seen": time.time(),
                "metadata": payload.get("metadata", {}),
                "status": "online"
            }

    def start(self):
        if BeaconListener:
            try:
                self.listener = BeaconListener(on_node_discovered_callback=self._on_node_beacon)
                self.listener.start()
                self.running = True
                logger.info("Node Discovery Manager started listening on UDP 224.0.0.251:8001")
            except Exception as e:
                logger.warning(f"Could not start BeaconListener: {e}")
        else:
            logger.warning("BeaconListener not available, discovery disabled.")

    def stop(self):
        self.running = False
        if self.listener:
            self.listener.stop()

    def get_cluster_nodes(self, max_age: float = 12.0) -> List[Dict[str, Any]]:
        now = time.time()
        result = []
        with self._lock:
            for nid, node in list(self.registered_nodes.items()):
                age = now - node.get("last_seen", 0)
                if age <= max_age:
                    node["age_seconds"] = round(age, 1)
                    node["status"] = "online"
                    result.append(node)
                else:
                    node["status"] = "offline"
                    node["age_seconds"] = round(age, 1)
                    result.append(node)
        return result

    def probe_node_health(self, ip: str, port: int) -> bool:
        try:
            url = f"http://{ip}:{port}/health"
            resp = requests.get(url, timeout=2.0)
            return resp.status_code == 200
        except Exception:
            return False

    def get_remote_node_status(self, ip: str, port: int) -> dict:
        try:
            url = f"http://{ip}:{port}/api/node/status"
            resp = requests.get(url, timeout=2.0)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.debug(f"Status check failed for {ip}:{port} - {e}")
        return {"is_active": False, "status": "unreachable"}

    def toggle_remote_node_state(self, ip: str, port: int, active: bool) -> dict:
        endpoint = "/api/node/activate" if active else "/api/node/deactivate"
        try:
            url = f"http://{ip}:{port}{endpoint}"
            resp = requests.post(url, timeout=3.0)
            return resp.json()
        except Exception as e:
            return {"status": "error", "message": f"Could not contact node at {ip}:{port}: {e}"}


discovery_manager = NodeDiscoveryManager()

