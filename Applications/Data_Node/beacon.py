"""
UDP Multicast Discovery Beacon Module for MAD-Node
Allows Data Nodes, Vault Nodes, and Operator Nodes to discover each other
across different directories, physical workstations, or VMs on a local subnet.
"""

import json
import socket
import struct
import threading
import time
import logging

logger = logging.getLogger("madn.beacon")

MULTICAST_GROUP = "224.0.0.251"
MULTICAST_PORT = 8001


class BeaconBroadcaster:
    """Broadcaster sending periodic UDP multicast JSON announcements."""

    def __init__(self, node_id: str, node_type: str, port: int, metadata: dict = None, interval: float = 3.0):
        self.node_id = node_id
        self.node_type = node_type
        self.port = port
        self.metadata = metadata or {}
        self.interval = interval
        self.running = False
        self.thread = None

    def _get_local_ip(self) -> str:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Connect to a dummy non-routable address to discover the primary outbound local IP
            s.connect(("10.255.255.255", 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip

    def _broadcast_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack("b", 2))
        try:
            # Allow loopback for same-machine testing
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        except Exception:
            pass

        while self.running:
            try:
                local_ip = self._get_local_ip()
                payload = {
                    "node_id": self.node_id,
                    "node_type": self.node_type,
                    "ip": local_ip,
                    "port": self.port,
                    "timestamp": time.time(),
                    "metadata": self.metadata
                }
                message = json.dumps(payload).encode("utf-8")
                sock.sendto(message, (MULTICAST_GROUP, MULTICAST_PORT))
            except Exception as e:
                logger.debug(f"Broadcast error: {e}")
            time.sleep(self.interval)
        sock.close()

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._broadcast_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)


class BeaconListener:
    """Listener capturing UDP multicast JSON announcements from remote nodes."""

    def __init__(self, on_node_discovered_callback=None):
        self.callback = on_node_discovered_callback
        self.running = False
        self.thread = None
        self.discovered_nodes = {}

    def _listen_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except AttributeError:
            pass

        try:
            sock.bind(("", MULTICAST_PORT))
        except Exception as e:
            logger.warning(f"Could not bind to multicast port {MULTICAST_PORT}: {e}")
            return

        mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
        try:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        except Exception as e:
            logger.warning(f"Could not join multicast group {MULTICAST_GROUP}: {e}")

        sock.settimeout(2.0)

        while self.running:
            try:
                data, addr = sock.recvfrom(2048)
                payload = json.loads(data.decode("utf-8"))
                node_id = payload.get("node_id")
                if node_id:
                    payload["last_seen"] = time.time()
                    payload["sender_addr"] = addr[0]
                    self.discovered_nodes[node_id] = payload
                    if self.callback:
                        self.callback(payload)
            except socket.timeout:
                continue
            except Exception as e:
                logger.debug(f"Listener error: {e}")
        sock.close()

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def get_active_nodes(self, max_age_seconds: float = 10.0) -> list:
        now = time.time()
        active = []
        for nid, info in list(self.discovered_nodes.items()):
            if now - info.get("last_seen", 0) <= max_age_seconds:
                active.append(info)
            else:
                # Node has timed out
                pass
        return active
