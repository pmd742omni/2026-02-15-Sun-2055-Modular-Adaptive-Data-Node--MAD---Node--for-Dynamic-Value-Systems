# Modular Adaptive Data Node (MADN) — Operations Manual & User Guide

**Document Version**: 1.19.3 (*Ingxubevange*)  
**Application Root**: `./` (Relative to `Applications/Web App/`)  
**Portable Launcher**: `../start.py` (Relative to `Applications/Web App/`)  
**Target Environment**: Edge Nodes (Raspberry Pi 4 / CM4, Linux / Windows / macOS Laptops & Mobile Tablets)

---

## Table of Contents
1. [System Overview & Operating Principles](#1-system-overview--operating-principles)
2. [How to Run the Application & Auto-Launch Browser](#2-how-to-run-the-application--auto-launch-browser)
   - [2.1 Quick Start (Single-Command Execution)](#21-quick-start-single-command-execution)
   - [2.2 Available CLI Options](#22-available-cli-options)
   - [2.3 Manual Server Launch (Direct Uvicorn)](#23-manual-server-launch-direct-uvicorn)
   - [2.4 Running Automated Verification Tests](#24-running-automated-verification-tests)
3. [User Authentication & Demo Accounts](#3-user-authentication--demo-accounts)
   - [3.1 Demo Accounts & Passwords](#31-demo-accounts--passwords)
   - [3.2 Quick Demo Role Login Buttons](#32-quick-demo-role-login-buttons)
   - [3.3 Multi-Factor Authentication (TOTP)](#33-multi-factor-authentication-totp)
4. [Dynamic Multi-Currency & World Catalog Collision Prevention](#4-dynamic-multi-currency--world-catalog-collision-prevention)
   - [4.1 Managing Active Currencies & Personalized Virtual Tokens](#41-managing-active-currencies--personalized-virtual-tokens)
   - [4.2 Real-Time Collision Prevention & Adoption](#42-real-time-collision-prevention--adoption)
   - [4.3 World Currency & Crypto Catalog Explorer](#43-world-currency--crypto-catalog-explorer)
5. [Customer Digital Banking & Receipt Vault](#5-customer-digital-banking--receipt-vault)
   - [5.1 Sovereign Multi-Currency Wallet](#51-sovereign-multi-currency-wallet)
   - [5.2 Peer-to-Peer (P2P) Fund Transfers](#52-peer-to-peer-p2p-fund-transfers)
   - [5.3 Converting Offline Bearer Vouchers to Wallet Balance](#53-converting-offline-bearer-vouchers-to-wallet-balance)
   - [5.4 Personal Receipt Vault Archiving & PDF Downloads](#54-personal-receipt-vault-archiving--pdf-downloads)
6. [Cluster Topology, Portable Node Export & Remote Lifecycle](#6-cluster-topology-portable-node-export--remote-lifecycle)
7. [Multi-Tenant Business Operator Management](#7-multi-tenant-business-operator-management)
8. [Troubleshooting & FAQs](#8-troubleshooting--faqs)

---

## 1. System Overview & Operating Principles

The **Modular Adaptive Data Node (MADN)** is an offline-first, local edge web application designed for off-grid agricultural enterprises, security posts, and rural retail stores.

### Core Architecture:
- **Zero Internet Dependency**: Operates 100% locally over Wi-Fi hotspots and local subnets without requiring WAN connectivity.
- **Tri-Node Topology**: Coordinates Operator Nodes (Web SPA :8000), Data Nodes (Edge daemons :8002), and Vault Nodes (Security Hub :8000).
- **Self-Replication & Portability**: Vault Nodes can generate standalone, copy-pasteable node directories with their own preflight launchers and embedded web UIs.

---

## 2. How to Run the Application & Auto-Launch Browser

### 2.1 Quick Start (Single-Command Execution)
Open a terminal in the `Applications` folder and execute the portable launcher:

```bash
# Navigate to Applications directory
cd Applications

# Start the cluster (auto-resolves dependencies and opens web browser)
python start.py
```

> [!NOTE]
> The launcher will automatically verify dependencies, initialize local databases, start the Vault Node (`:8000`), Data Node (`:8002`), and UDP multicast beacon (`224.0.0.251:8001`), and **automatically open your default web browser to the sign-in page (`http://127.0.0.1:8000`)**.

### 2.2 Available CLI Options
The portable bootstrapper (`Applications/start.py`) supports the following flags:

```bash
python start.py                          # Start all default nodes and open browser
python start.py --vault-only             # Start only the Vault Coordinator (:8000)
python start.py --data-only              # Start only the Standalone Data Node (:8002)
python start.py --status                 # Scan and display local port availability
python start.py --no-browser             # Run in headless mode without opening a browser
python start.py --create-node Alpha data_node 8005  # Generate a standalone portable node bundle
```

### 2.3 Manual Server Launch (Direct Uvicorn)
If starting manually without `start.py`:
```bash
cd "Applications/Web App"
python -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000
```

### 2.4 Running Automated Verification Tests
Execute the full 25-test regression suite from `Applications/Web App/backend`:
```bash
cd "Applications/Web App/backend"
python -m pytest test_portable_node_generation.py test_customer_banking.py test_business_operators.py test_multibiz_and_vouchers.py test_stage1_core.py -v
```

---

## 3. User Authentication & Demo Accounts

### 3.1 Demo Accounts & Passwords
The system is pre-seeded with six standard role accounts:

| Role | Username | Password | Default PIN | Granted Access |
| :--- | :--- | :--- | :---: | :--- |
| 👑 **Administrator** | `admin` | `Password123!` | `1234` | Full access across all systems, cluster management, and user rosters |
| 🌾 **Agronomist** | `agronomist` | `Password123!` | `1234` | VPA 1 (Planting cycles, itemized crop costs, harvest work orders) |
| 🏪 **Merchant** | `merchant` | `Password123!` | `1234` | VPA 3 (POS touch register, dynamic decay pricing, inventory, vouchers) |
| 🛡️ **Security Guard** | `guard` | `Password123!` | `1234` | VPA 2 (Visitor gatekeeper, RF signal map, guard shift handovers) |
| 🛒 **Customer** | `customer` | `Password123!` | `1234` | Digital banking wallet, P2P fund transfers, personal receipt vault |
| 👤 **Guest** | `guest` | `Password123!` | `1234` | Public social feed, stories, and catalog exploration |

### 3.2 Quick Demo Role Login Buttons
On the sign-in page (`http://127.0.0.1:8000`), click any button under **Quick Demo Role Login** (**`👑 Admin`**, **`🌾 Agronomist`**, **`🏪 Merchant`**, etc.) to immediately log into that role's interface without typing.

---

## 4. Customer Digital Banking & Receipt Vault

### 4.1 Sovereign Multi-Currency Wallet
1. Log in as `customer` (or switch to **💳 Banking** view).
2. View your multi-currency balances in **USD**, **ZAR**, and **ZWG**.
3. View your account number (e.g. `ACC-2026-A1B2C3`).

### 4.2 Peer-to-Peer (P2P) Fund Transfers
1. Click **`Send Funds 💸`**.
2. Enter the recipient account number, select currency, enter amount, and click **`Confirm Transfer`**.
3. The funds are instantly debited and credited under atomic SQLite WAL transaction locks with HMAC audit signature chaining.

### 4.3 Converting Offline Bearer Vouchers to Wallet Balance
1. Click **`Deposit Offline Voucher 🎟️`**.
2. Enter or scan the 16-character voucher code received from a POS change receipt.
3. The voucher value is immediately converted into spendable liquid wallet balance.

### 4.4 Personal Receipt Vault Archiving & PDF Downloads
1. Switch to the **Receipt Vault** tab.
2. View permanent digital receipt records archived automatically upon POS checkouts.
3. Click any receipt to preview item breakdowns, SHA-256 integrity hashes, and download formatted PDF or thermal slips.

---

## 5. Cluster Topology, Portable Node Export & Remote Lifecycle

### 5.1 Discovered Mesh Data Nodes & UDP Multicast
1. Navigate to **`📡 Cluster Nodes`** in the navigation sidebar.
2. View all active edge nodes discovered dynamically via UDP Multicast (`224.0.0.251:8001`).

### 5.2 Remote Node Activation & Standby Gating
1. Locate any discovered node in the cluster grid.
2. Click **`Deactivate Node ⚡`** to place the edge node into Standby / Maintenance Mode (suspending beacons and rejecting write mutations with HTTP 503 while maintaining read access).
3. Click **`Activate Node ⚡`** to restore the node to active operational status.

### 5.3 Exporting Standalone Portable Node Bundles
1. Click the blue **`📦 Export Portable Node Pack`** button in the Cluster view.
2. Enter the Node Name (e.g. `Matopos_Edge_Silo`), select Role (`data_node`, `vault_node`, `hybrid_node`), port number, and storage quota.
3. Click **`Create Bundle 🚀`**.
4. The system synthesizes a self-contained directory under `Applications/Exported_Nodes/MADN_<Name>_Port<Port>/`.

### 5.4 Running Exported Standalone Nodes
To run an exported node bundle on any computer:
```bash
python "Applications/Exported_Nodes/MADN_Matopos_Edge_Silo_Port8015/start.py"
```
The node will self-bootstrap and automatically launch its own glassmorphic web dashboard at `http://127.0.0.1:8015`.

---

## 6. Multi-Tenant Business Operator Management
1. Log in as `admin`.
2. Navigate to **`👥 Admin Control`** \(\to\) **🏢 Business Staff & Permissions**.
3. Click **`Grant Operator Access ➕`** to delegate granular access rights (`pos`, `inventory`, `agriculture`, `security`, `social`, `reports`) to staff members for specific business stores (*Green Valley Organics*, *Khumalo Millers*, *Matopos Dairy*).

---

## 7. Troubleshooting & FAQs

* **Port Already in Use**: If port `8000` or `8002` is in use by another instance, inspect active ports with `python Applications/start.py --status`.
* **Database Reset**: To re-seed fresh demo data, delete `Applications/Web App/backend/data_store/data_node.db` and run `python Applications/start.py`.
