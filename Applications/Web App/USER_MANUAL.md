# Modular Adaptive Data Node (MADN) — Operations Manual & User Guide

**Document Version**: 1.19.9 (*Ukuvuleka — Dynamic Progressive Disclosure & Condition-Gated UX*)  
**Application Root**: `./` (Relative to `Applications/Web App/`)  
**Portable Launcher**: `../start.py` (Relative to `Applications/Web App/`)  
**Target Environment**: Edge Nodes (Raspberry Pi 4 / CM4, Linux / Windows / macOS Laptops & Mobile Tablets)

---

## Table of Contents
1. [System Overview & Operating Principles](#1-system-overview--operating-principles)
2. [How to Run the Application & Auto-Launch Browser](#2-how-to-run-the-application--auto-launch-browser)
3. [User Authentication & Security Credentials](#3-user-authentication--demo-accounts)
4. [Multi-Enterprise Store Setup & Unified POS Register](#4-multi-enterprise-store-setup--unified-pos-register)
5. [Dynamic Multi-Currency & World Catalog Collision Prevention](#5-dynamic-multi-currency--world-catalog-collision-prevention)
6. [Customer & Business Digital Banking](#6-customer--business-digital-banking)
7. [Cluster Topology, Portable Node Export & Remote Lifecycle](#7-cluster-topology-portable-node-export--remote-lifecycle)
8. [Multi-Tenant Business Operator Management](#8-multi-tenant-business-operator-management)
9. [Sovereign Heavy Encryption & Continuous Data Replication](#9-sovereign-heavy-encryption--continuous-data-replication)
10. [Troubleshooting & FAQs](#10-troubleshooting--faqs)

---

## 4. Multi-Enterprise Store Setup & Unified POS Register

### 4.1 Store Setup Prerequisite
Before an operator can register inventory products or log crop harvests, at least one store must be created:
1. Open the **`🏬 Business`** tab.
2. If no stores exist, click **`+ Set Up Business Store`**.
3. Complete the mandatory fields:
   - **Business / Store Name**: e.g., *Umguza Valley Organics*
   - **Tagline**: e.g., *Fresh Soil-Grown Vegetables*
   - **Description**: e.g., *Agro-ecological family farm.*
4. Select modular optional pills:
   - `+ 🖼️ Logo & Banner`: Upload image files or paste image URLs.
   - `+ 📞 Contact & Location`: Add phone, email, and farm/store address.
   - `+ 🏷️ Tax ID & Industry`: Add VAT registration and category.
   - `+ 💳 Settlement Currency`: Choose default accounting currency.
   - `+ ⏰ Operating Hours` & `+ 🛡️ Return Policy`.
5. Click **`Register Store & Open Banking Wallet 🚀`**.

### 4.2 Adding Store Products
1. Click **`+ Add Store Product`**.
2. Select which store owns the item from the **Assigned Business / Store** dropdown.
3. Provide item details, cost price (COGS), selling price, unit, stock quantity, and optional specifications.

### 4.3 Unified Multi-Store POS Checkout
1. Add items from multiple different stores to the same POS cart.
2. Enter tendered amounts (cash USD, ZAR, ZWG, or Digital Wallet balance).
3. Complete checkout. The backend automatically routes each store's proceeds to its own dedicated `BIZ-ACC-...` wallet!

### 4.4 Business Sales & Spoilage Analytics
1. Use the **`🌐 All Stores`** or store-specific filter switcher pills.
2. View Gross Revenue, Total Cost of Goods Sold (COGS), Gross Profit Margin %, and the 24-hour hourly velocity chart.

---

## 8. Troubleshooting & FAQs

* **Port Already in Use**: If port `8000` or `8002` is in use by another instance, inspect active ports with `python Applications/start.py --status`.
* **Database Reset**: To re-seed clean databases with authentic 0.00 balances, delete `Applications/Web App/backend/data_store/` and run `python Applications/start.py`.

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
| 🌾 **Agronomist** | `agronomist` | `Password123!` | `1234` | Precision Agriculture (Planting cycles, itemized crop costs, harvest work orders) |
| 🏪 **Merchant** | `merchant` | `Password123!` | `1234` | Business & Retail (POS touch register, dynamic decay pricing, inventory, vouchers) |
| 🛡️ **Security Guard** | `guard` | `Password123!` | `1234` | Security Gatekeeper (Visitor gatekeeper, RF signal map, guard shift handovers) |
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

## 8. Multi-Tenant Business Operator Management
1. Log in as `admin`.
2. Navigate to **`👥 Admin Control`** $\to$ **🏢 Business Staff & Permissions**.
3. Click **`Grant Operator Access ➕`** to delegate granular access rights (`pos`, `inventory`, `agriculture`, `security`, `social`, `reports`) to staff members for specific business stores (*Green Valley Organics*, *Khumalo Millers*, *Matopos Dairy*).

---

## 9. Sovereign Heavy Encryption & Continuous Data Replication

### 9.1 Military-Grade Data-at-Rest Encryption (AES-256-GCM)
All business accounts, personal wallets, customer digital receipts, visitor records, and replicated key-value entries are encrypted with AES-256-GCM using keys derived via scrypt. If the device or disk is seized, data cannot be read without the authorized operator passphrase.

### 9.2 What is "Continuous Data Node Replication"?
"Continuous Data Node Replication" means that whenever any price, product, harvest record, or exchange rate changes on the main Vault Node, the system automatically and silently replicates the encrypted data to all other connected Data Nodes across your local Wi-Fi, Ethernet, or mesh network. 

**Why is this important?**
* **Never Lose Sales**: Even if the primary computer goes down or loses power, edge tablets and remote checkout registers keep working because they read locally replicated data from nearby Data Nodes.
* **Automatic Recovery**: When nodes reconnect, they automatically synchronize and resolve updates without manual file copying or configuration.

---

## 10. Troubleshooting & FAQs

* **Port Already in Use**: If port `8000` or `8002` is in use by another instance, inspect active ports with `python Applications/start.py --status`.
* **Database Reset**: To re-seed fresh clean data, delete `Applications/Web App/backend/database.db` and start the system cleanly with `python Applications/start.py`.

