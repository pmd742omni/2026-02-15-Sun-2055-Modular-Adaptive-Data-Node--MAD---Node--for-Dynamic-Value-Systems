# Modular Adaptive Data Node (MADN) — User Manual & Operations Guide

**Version:** 1.16.0 (*Ukusebenza*)  
**System Architecture:** Offline-First Web Application (Python FastAPI + SQLite WAL + Vanilla JS/CSS/HTML5)  
**Target Deployment:** Edge Nodes (Raspberry Pi 4 / Laptop Orchestrators & Pico W Mesh Nodes)

---

## Table of Contents
1. [System Overview & Operating Principles](#1-system-overview--operating-principles)
2. [System Requirements & How to Run the Application](#2-system-requirements--how-to-run-the-application)
   - [2.1 System Prerequisites](#21-system-prerequisites)
   - [2.2 Quick Start Execution Commands](#22-quick-start-execution-commands)
   - [2.3 Accessing the Application & API Docs](#23-accessing-the-application--api-docs)
   - [2.4 Running Automated Verification Test Suites](#24-running-automated-verification-test-suites)
   - [2.5 Running as a Background Service (Linux / Raspberry Pi systemd)](#25-running-as-a-background-service-linux--raspberry-pi-systemd)
3. [Getting Started & Authentication](#3-getting-started--authentication)
   - [3.1 Initial Bootstrap Admin Login](#31-initial-bootstrap-admin-login)
   - [3.2 Mandatory Password Updates & Policy](#32-mandatory-password-updates--policy)
   - [3.3 Multi-Factor Authentication (TOTP) Setup](#33-multi-factor-authentication-totp-setup)
   - [3.4 Step-Up Elevation Authorization](#34-step-up-elevation-authorization)
   - [3.5 User Roster & Role Management](#35-user-roster--role-management)
4. [VPA 1: Agricultural Aid & Agronomy Automation](#4-vpa-1-agricultural-aid--agronomy-automation)
   - [4.1 VPA 1.1: Local Climate & Planting Scheduler](#41-vpa-11-local-climate--planting-scheduler)
   - [4.2 VPA 1.2: Symptom Diagnostic Tree](#42-vpa-12-symptom-diagnostic-tree)
   - [4.3 VPA 1.3: Yield & Livestock Feed Intakes Estimator](#43-vpa-13-yield--livestock-feed-intakes-estimator)
   - [4.4 VPA 1.4: Compound Agronomy Rules & Harvest Work Orders](#44-vpa-14-compound-agronomy-rules--harvest-work-orders)
5. [VPA 2: Perimeter Security Aid & RF Mesh Dynamics](#5-vpa-2-perimeter-security-aid--rf-mesh-dynamics)
   - [5.1 VPA 2.1: Perimeter Status Map & Alarms](#51-vpa-21-perimeter-status-map--alarms)
   - [5.2 VPA 2.2: Local QR Code Credential Generator & Scanner](#52-vpa-22-local-qr-code-credential-generator--scanner)
   - [5.3 VPA 2.3: Guard Shift Handovers & Cash Reconciliation](#53-vpa-23-guard-shift-handovers--cash-reconciliation)
   - [5.4 VPA 2.4: Physics RF Mesh, R\*Tree Spatial Drag & Digital Twin](#54-vpa-24-physics-rf-mesh-rtree-spatial-drag--digital-twin)
6. [VPA 3: Point of Sale (POS) & Dynamic Value System](#6-vpa-3-point-of-sale-pos--dynamic-value-system)
   - [6.1 VPA 3.1: Multi-Currency Tri-Ledger Terminal (USD/ZAR/ZWG)](#61-vpa-31-multi-currency-tri-ledger-terminal-usdzarzwg)
   - [6.2 VPA 3.2: Interactive Sales Analytics & Visualizer](#62-vpa-32-interactive-sales-analytics--visualizer)
   - [6.3 VPA 3.3: Inventory Catalog, Spoilage & Hotkeys](#63-vpa-33-inventory-catalog-spoilage--hotkeys)
   - [6.4 VPA 3.4: Continuous Exponential Decay POS Dynamic Pricing](#64-vpa-34-continuous-exponential-decay-pos-dynamic-pricing)
7. [System Administration & Cryptographic Auditing](#7-system-administration--cryptographic-auditing)
   - [7.1 Cryptographic Append-Only Audit Log](#71-cryptographic-append-only-audit-log)
   - [7.2 Startup Tamper Detection & Forensic Mode](#72-startup-tamper-detection--forensic-mode)
8. [Keyboard Shortcuts & Offline Operability](#8-keyboard-shortcuts--offline-operability)
9. [Troubleshooting & Error Codes](#9-troubleshooting--error-codes)

---

## 1. System Overview & Operating Principles

The **Modular Adaptive Data Node (MADN)** is an offline-first, local edge web application designed to maintain seamless operations in remote, resource-constrained, or off-grid agricultural and security installations. 

### Key Principles:
- **Zero Internet Dependency:** All database queries, signal propagation models, HTML5 Canvas visualizers, and dynamic pricing calculations execute 100% locally on the node device.
- **Cross-VPA Synergy:** Sensor anomalies in Agricultural fields (VPA 1) automatically trigger Harvest Work Orders and spawn Continuous Exponential Decay Flash Sales in the Point of Sale terminal (VPA 3).
- **Physics-Grounded Telemetry:** Security nodes (VPA 2) model real-world open-field log-distance RF path loss, R\*Tree obstacle attenuation, and graph-based A\* link routing.
- **Offline Multi-Master Sync Safety:** Uses Last-Write-Wins (LWW) timestamping and atomic SQLite write locks to eliminate data conflicts across field tablets.

---

## 2. System Requirements & How to Run the Application

### 2.1 System Prerequisites
- **Python Version:** Python 3.10 or higher installed.
- **Python Packages:** `fastapi`, `uvicorn`, `requests`, `pyotp`  
  *(Install via command: `pip install fastapi uvicorn requests pyotp`)*
- **Supported Platforms:** Windows 10/11, Linux (Debian, Ubuntu, Raspberry Pi OS), macOS.

---

### 2.2 Quick Start Execution Commands

#### Option A: Running on Windows (PowerShell)
Open PowerShell, navigate to the application folder, set the initial bootstrap password, and launch the Uvicorn web server:
```powershell
cd "Applications\Web App"
$env:MADN_BOOTSTRAP_ADMIN_PW="adminpassword"
python -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000
```

#### Option B: Running on Windows (Command Prompt / CMD)
```cmd
cd "Applications\Web App"
set MADN_BOOTSTRAP_ADMIN_PW=adminpassword
python -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000
```

#### Option C: Running on Linux / macOS / Raspberry Pi Orchestrator
To expose the web application across a local Wi-Fi Hotspot for field tablets and mobile clients, bind to `--host 0.0.0.0`:
```bash
cd "Applications/Web App"
export MADN_BOOTSTRAP_ADMIN_PW="adminpassword"
python3 -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000
```

---

### 2.3 Accessing the Application & API Docs
1. Once Uvicorn outputs `Application startup complete`, open a web browser.
2. **Local Machine Access:** Navigate to `http://127.0.0.1:8000` or `http://localhost:8000`.
3. **Local Wi-Fi Subnet Access (Field Tablets):** Navigate to `http://<orchestrator-ip>:8000` (e.g. `http://192.168.1.100:8000`).
4. **Interactive API Documentation:** OpenAPI Swagger docs are available at `http://127.0.0.1:8000/docs`.

---

### 2.4 Running Automated Verification Test Suites
To verify system functionality, database integrity, spatial math engines, and security controls, open a separate terminal window and execute:

- **Auth & Security Test Suite:** `python backend/test_auth.py`
- **Live Endpoints E2E Test Suite:** `python backend/test_endpoints_live.py`
- **Cycle 3 Concurrency & Inventory Test Suite:** `python backend/test_cycle3.py`
- **Cycle 4 Spatial R\*Tree, Mesh & Dynamic POS Test Suite:** `python backend/test_cycle4.py`

---

### 2.5 Running as a Background Service (Linux / Raspberry Pi systemd)
To ensure the application auto-starts when the edge node boots, create `/etc/systemd/system/madn.service`:

```ini
[Unit]
Description=Modular Adaptive Data Node (MADN) Edge Web Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/MADN/Applications/Web App
Environment="MADN_BOOTSTRAP_ADMIN_PW=adminpassword"
ExecStart=/usr/bin/python3 -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable madn.service
sudo systemctl start madn.service
```

---

## 3. Getting Started & Authentication

### 3.1 Initial Bootstrap Admin Login
When starting a newly initialized MADN server for the first time:
1. Open your browser and navigate to `http://127.0.0.1:8000/` (or the local node IP address).
2. The system presents a glassmorphic **Security Authentication Overlay**.
3. Enter the initial bootstrap credentials:
   - **Username:** `admin`
   - **Password:** `adminpassword` (or the custom password supplied in `$env:MADN_BOOTSTRAP_ADMIN_PW`).

> [!IMPORTANT]
> The bootstrap credentials are temporary. On your first successful login, access to the application will be restricted until a custom password is created.

### 3.2 Mandatory Password Updates & Policy
Upon logging in with bootstrap credentials:
- A mandatory modal prompts you to change your password immediately.
- **Password Requirements:** Minimum 10 characters, including uppercase, lowercase, numbers, and special symbols.
- Passwords are salted and hashed using **`hashlib.scrypt`** ($N=16384, r=8, p=1$).

### 3.3 Multi-Factor Authentication (TOTP) Setup
To elevate your account security:
1. Open the **User Profile Drawer** from the bottom-left sidebar.
2. Click **Enable Multi-Factor Authentication (MFA)**.
3. Scan the generated QR code using an RFC 6238 compliant authenticator app (Google Authenticator, Authy, etc.).
4. Enter the 6-digit TOTP token to confirm setup.

### 3.4 Step-Up Elevation Authorization
Administrative actions (e.g., approving user registrations, modifying system parameters) require temporary session elevation:
- When performing a sensitive operation, a **Step-Up Authorization Modal** appears.
- Enter your password or 6-digit MFA token to grant an elevated 15-minute administrative window.

### 3.5 User Roster & Role Management
Admins can review registered operators in the **Admin Control Panel**:
- **Pending Users:** Newly registered field operators default to `pending` status until approved by an administrator.
- **Roles:** `Admin` (full system access), `Operator` (VPA module access), `Guest/Visitor` (temporary QR badge access).

---

## 4. VPA 1: Agricultural Aid & Agronomy Automation

### 4.1 VPA 1.1: Local Climate & Planting Scheduler
- **Historical Climate Data:** Pre-loaded with regional Bulawayo temperature and precipitation trends.
- **Companion Planting Matrix:** Recommends optimal crop pairings (e.g., Maize + Beans) to naturally repel pests and enhance soil nitrogen fixation.

### 4.2 VPA 1.2: Symptom Diagnostic Tree
- **Interactive Wizard:** Step-by-step diagnostic wizard for crop diseases (e.g., Maize Streak Virus, Early Blight) and livestock ailments (e.g., Tick-borne gall sickness).
- **Organic Local Remedies:** Generates low-cost remedies using locally available materials.

### 4.3 VPA 1.3: Yield & Livestock Feed Intakes Estimator
- **Rainfall Anomaly Slider:** Adjust predicted seasonal rainfall from $-50\%$ (severe drought) to $+50\%$ (excess moisture).
- **Animal Feed Calculator:** Estimates daily dry-matter feed requirements based on animal body weight and growth phase.
- **Calculation History:** Archived run snapshots can be reviewed in the historical estimations log table.

### 4.4 VPA 1.4: Compound Agronomy Rules & Harvest Work Orders
- **Compound Rule Builder:** Define multi-condition triggers (e.g., `Temperature > 32°C AND Soil Moisture < 20%`).
- **Cross-Midnight Windows:** Supports rule time windows crossing midnight (e.g., `18:00` to `06:00`).
- **Harvest Work Order Lifecycle:**
  1. `Triggered`: Automatically spawned when a spoilage rule condition is breached.
  2. `Assigned`: Field team dispatched for crop picking.
  3. `Harvested`: Produce collected and transported to central storage.
  4. `POS_Listed`: Transferred to POS terminal with continuous decay pricing.

---

## 5. VPA 2: Perimeter Security Aid & RF Mesh Dynamics

### 5.1 VPA 2.1: Perimeter Status Map & Alarms
- Displays live connection status, IP addresses, and real-time RSSI signal bars for monitored physical perimeter zones.
- Includes manual tripwire alarm triggers to test field siren relays.

### 5.2 VPA 2.2: Local QR Code Credential Generator & Scanner
- **Badge Issuer:** Enter visitor full name, national ID, and access duration to generate a digital QR badge.
- **Local HTML5 Scanner:** Scans and verifies guest QR payload HMAC signatures offline against SQLite database records.

### 5.3 VPA 2.3: Guard Shift Handovers & Cash Reconciliation
- **Duty Transfer Form:** Outgoing and incoming guards log shift handovers.
- **HMAC PIN Verification:** Requires incoming guard's 4-digit PIN for authentication.
- **Audit Ledger:** Handover records are cryptographically chained to prevent retroactive log alteration.

### 5.4 VPA 2.4: Physics RF Mesh, R\*Tree Spatial Drag & Digital Twin
- **Pointer Events SVG Dragging:** Click/touch and drag node circles directly on the map. Releasing a node saves its normalized percentage coordinates via LWW sync.
- **R\*Tree Spatial Ray Tracing:** Visualizes spatial obstacles (Metal Silo: $-25\text{ dBm}$, Wooden Barn: $-8\text{ dBm}$) using Liang-Barsky 2D ray intersection lines.
- **Coverage Heatmap Canvas:** Click **Toggle Signal Heatmap** to render a 600x350 spatial signal quality canvas (Green $\ge -65\text{ dBm}$, Amber $\ge -85\text{ dBm}$, Red $< -85\text{ dBm}$).
- **24H Digital Twin Scrubber:** Drag the timeline slider ($0$ to $24$ hours) to simulate solar battery charging peaks and nighttime drain.

---

## 6. VPA 3: Point of Sale (POS) & Dynamic Value System

### 6.1 VPA 3.1: Multi-Currency Tri-Ledger Terminal (USD/ZAR/ZWG)
- **Real-Time Exchange Conversion:** Input base USD price to instantly compute ZAR and ZWG values using daily rates.
- **Mixed Tender Change Calculator:** Calculates exact change distribution options in any combination of USD, ZAR, or ZWG cash.

### 6.2 VPA 3.2: Interactive Sales Analytics & Visualizer
- Custom HTML5 Canvas rendering hourly sales volume trends without external JavaScript chart dependencies.

### 6.3 VPA 3.3: Inventory Catalog, Spoilage & Hotkeys
- **Catalog Integration:** Select products directly from the stock registry.
- **Wastage Log:** Record spoilage/breakage losses separately from consumer checkouts.
- **Reorder Manifest:** Automatically flags low-stock items (Qty $< 5$) and downloads a `.txt` reorder manifest.
- **Offline Cart Recovery:** Automatically caches unsubmitted carts in `localStorage` in case of power disruption.

### 6.4 VPA 3.4: Continuous Exponential Decay POS Dynamic Pricing
- **Cross-VPA Flash Sale Banner:** Highlights produce subject to active crop spoilage warnings.
- **Smooth Price Decay:** Markdown increases smoothly as produce approaches its spoilage cutoff deadline.
- **Margin Floor Protection:** Guarantees discounted prices never fall below the item's `cost_price_usd`.

---

## 7. System Administration & Cryptographic Auditing

### 7.1 Cryptographic Append-Only Audit Log
Every critical action (login, password change, shift handover, inventory adjustment) is recorded in two locations:
1. SQLite `audit_logs` table.
2. Flat text file `backend/audit_logs.log`.

Each log entry includes:
- `sequence_id` (monotonically increasing integer)
- `timestamp_utc`
- `actor` username
- `action` description
- `prev_hash` (SHA-256 hash of the previous record)
- `record_hash` (SHA-256 hash of current entry + `prev_hash`)

### 7.2 Startup Tamper Detection & Forensic Mode
Upon application startup:
1. The system reads all records from `audit_logs.log` and recalculates the hash chain.
2. If any line has been edited, deleted, or inserted out of order, startup halts and enters **Forensic Mode**.
3. Admin intervention is required to review tampered block hashes before unlocking the system.

---

## 8. Keyboard Shortcuts & Offline Operability

| Shortcut Key | Function | Active Context |
| :--- | :--- | :--- |
| **`F2`** | Quick-focus Product Search Select dropdown | POS View (`VPA 3`) |
| **`F8`** | Submit POS Sale Transaction | POS View (`VPA 3`) |
| **`F9`** | Clear Active POS Cart | POS View (`VPA 3`) |
| **`Esc`** | Close active modals / User Profile drawer | Global |

---

## 9. Troubleshooting & Error Codes

| Symptom / Error | Cause | Resolution |
| :--- | :--- | :--- |
| **`401 Unauthorized`** | Missing or expired session cookie. | Click **Login** and authenticate again. |
| **`403 Step-Up Required`** | Action requires elevated admin privileges. | Enter password in the Step-Up dialog to elevate session for 15 mins. |
| **`429 Too Many Requests`** | Lockout triggered by consecutive invalid password attempts. | Wait for the exponential lockout timer to expire (indicated in alert banner). |
| **`CSRF Token Mismatch`** | Cookie and header CSRF tokens out of sync. | Refresh browser page (`F5`). |
| **`SQLITE_BUSY / Database Locked`** | High write contention on database file. | Connection uses WAL mode with 5s busy timeout. Retry action; if persistent, restart server. |
| **Forensic Mode Alert** | File `audit_logs.log` hash chain does not match database record. | Inspect `audit_logs.log` for manual edits. Restore flat log file from valid backup. |

---

*Modular Adaptive Data Node (MADN) — Offline-First Architecture for Dynamic Value Systems*
