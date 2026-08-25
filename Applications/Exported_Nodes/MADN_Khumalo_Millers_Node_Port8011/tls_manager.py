#!/usr/bin/env python3
"""
MADN Sovereign TLS & SSL Certificate Manager
============================================
Automated generation and lifecycle management of X.509 SSL/TLS certificates
for zero-configuration, air-gapped, and offline HTTPS deployments.

Automatically attaches Subject Alternative Names (SANs) for:
- Local loopback interfaces (127.0.0.1, ::1, localhost)
- Local network adapter IPs (192.168.x.x, 10.x.x.x, 172.x.x.x)
- Hostname and local domain identifiers (madn.local, *.local)
"""

import os
import sys
import socket
import datetime
import ipaddress
from typing import Tuple, List, Optional

APPLICATIONS_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CERTS_DIR = os.path.join(APPLICATIONS_DIR, "certs")


def get_all_local_ip_addresses() -> List[str]:
    """Detects all active IPv4 addresses across local network adapters."""
    ips = set()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(0.2)
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


def generate_self_signed_certificate(
    certs_dir: str = DEFAULT_CERTS_DIR,
    validity_days: int = 3650,
    force_regenerate: bool = False
) -> Tuple[str, str]:
    """
    Generates a high-security 2048-bit RSA private key and self-signed X.509 certificate
    with all local SANs. Returns (cert_path, key_path).
    """
    os.makedirs(certs_dir, exist_ok=True)
    cert_path = os.path.join(certs_dir, "cert.pem")
    key_path = os.path.join(certs_dir, "key.pem")

    if not force_regenerate and os.path.exists(cert_path) and os.path.exists(key_path):
        return cert_path, key_path

    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
    except ImportError:
        print("[!] Note: cryptography package required for TLS generation. Attempting installation...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "cryptography"], capture_output=True)
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization

    # 1. Generate Private Key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    # 2. Build Subject & Issuer
    hostname = socket.gethostname()
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "ZW"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Bulawayo"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Bulawayo"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MADN Sovereign Mesh"),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Data Nodes Security Vault"),
        x509.NameAttribute(NameOID.COMMON_NAME, f"madn-{hostname.lower()}"),
    ])

    # 3. Assemble Subject Alternative Names (SANs)
    alt_names = [
        x509.DNSName("localhost"),
        x509.DNSName("madn.local"),
        x509.DNSName("vault.local"),
        x509.DNSName(hostname),
        x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        x509.IPAddress(ipaddress.IPv6Address("::1")),
    ]

    for ip_str in get_all_local_ip_addresses():
        try:
            alt_names.append(x509.IPAddress(ipaddress.IPv4Address(ip_str)))
        except ValueError:
            pass

    san_extension = x509.SubjectAlternativeName(alt_names)

    # 4. Sign Certificate (Valid for 10 Years)
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=validity_days))
        .add_extension(san_extension, critical=False)
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True
        )
        .sign(private_key, hashes.SHA256())
    )

    # 5. Write Private Key (PEM format)
    with open(key_path, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            )
        )

    # 6. Write Certificate (PEM format)
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print(f"[+] Successfully generated sovereign TLS certificates in: {certs_dir}")
    print(f"    - Certificate: {cert_path}")
    print(f"    - Private Key: {key_path}")
    return cert_path, key_path


def ensure_ssl_certificates(certs_dir: str = DEFAULT_CERTS_DIR) -> Tuple[str, str]:
    """Ensures that SSL certificates exist and are ready for use."""
    return generate_self_signed_certificate(certs_dir=certs_dir, force_regenerate=False)


if __name__ == "__main__":
    generate_self_signed_certificate(force_regenerate=True)
