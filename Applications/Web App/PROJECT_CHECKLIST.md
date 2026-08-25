# Master Task List & Progress Checklist — MADN Web Application Development

**Root Directory**: `./` (Relative to `Applications/Web App/`)  
**Workspace Base**: `../../` (Relative to project root)

---

## [x] Authentication & Admin Controls (Hardening Phase)
- `[x]` **Backend Security Foundation**
  - `[x]` Create `./backend/auth_utils.py` with scrypt hashing, constant-time validation, and RFC 6238 TOTP
  - `[x]` Create `./backend/database.py` with SQLite tables, WAL mode, admin bootstrap, and append-only audit log file anchor
  - `[x]` Update `./backend/main.py` with FastAPI endpoints, HttpOnly cookies, Double-Submit CSRF check, and session/step-up authorization middleware
  - `[x]` Create `./backend/test_auth.py` automated test suite and run it to verify security properties
- `[x]` **Frontend Auth SPA Integration**
  - `[x]` Update `./frontend/index.html` with Login Overlay, Quick Demo Role Switcher, User Profile Drawer, and Admin Control panel
  - `[x]` Update `./frontend/index.css` with glassmorphic styles, admin table states, and form feedback cues
  - `[x]` Update `./frontend/app.js` with secureFetch, checkActiveSession, form handlers, dynamically rendered user rosters, step-up elevation intercepts, and local canvas QR renderer

---

## [x] Baseline Setup & Design System
- `[x]` Create `./frontend/index.html` main Single Page Application skeleton
- `[x]` Define CSS design system and custom properties in `./frontend/index.css`
- `[x]` Implement core state manager in `./frontend/app.js`

---

## [x] Cycle 1: Core Foundation & Initial Visualizers
- `[x]` **VPA 1.1: Local Climate & Planting Scheduler** (Agriculture)
  - `[x]` Create layout card and calendar scheduler in frontend UI
  - `[x]` Seed local historical Bulawayo climate data in client database
  - `[x]` Write calculation engine and recommendations logic
  - `[x]` Test VPA 1.1 functionality and layout ergonomics
- `[x]` **VPA 2.1: Real-Time Node Status Map** (Security)
  - `[x]` Render Zone SVG map in frontend UI
  - `[x]` Add mock node connection toggle controls
  - `[x]` Integrate live signal strength (RSSI) visual status indicators
- `[x]` **VPA 3.1: Multi-Currency Tri-Ledger (USD/ZAR/ZWG)** (POS)
  - `[x]` Create transaction terminal layout card
  - `[x]` Implement currency converter with customizable exchange rates
  - `[x]` Program change calculator accepting mixed currency payments

---

## [x] Cycle 2: Diagnostics, QR Validation & Analytics (VPA 1.2, 2.2, 3.2)
- `[x]` **VPA 1.2: Interactive Symptom Diagnostic Tree** (Agriculture)
  - `[x]` Create symptom diagnostic card/wizard UI in Agricultural tab
  - `[x]` Define branching tree logic for crops and livestock diseases
- `[x]` **VPA 2.2: Local QR Code Credential Generator & Scanner** (Security)
  - `[x]` Implement QR code guest credential generator
  - `[x]` Build HTML5 Canvas scanner/mock reader panel to process QR check-ins
- `[x]` **VPA 3.2: Interactive Sales Analytics & Visualizer** (POS)
  - `[x]` Design responsive analytics dashboard and visual metrics cards
  - `[x]` Write custom HTML5 Canvas drawing functions to render hourly sales graphs without internet dependencies

---

## [x] Cycle 3: Calculators, Logs & Inventories (VPA 1.3, 2.3, 3.3)
- `[x]` **Database Schema & Configurations**
  - `[x]` Update `./backend/database.py` with tables: `inventory`, `inventory_wastage`, `transactions`, `transaction_tenders`, `transaction_items`, `calculator_config`, `estimator_runs`, `shift_handover_logs`, `processed_requests`
  - `[x]` Implement `BEGIN IMMEDIATE` write locks, HMAC handover logging, and configurations seed
- `[x]` **Backend API Endpoints**
  - `[x]` Create VPA 1.3 agricultural calculator and history endpoints
  - `[x]` Create VPA 2.3 security handover logs with PIN checks and audit tracking
  - `[x]` Create VPA 3.3 inventory directory, stock adjust, and spoilage logs
  - `[x]` Update `/api/pos/checkout` to support multi-tender, transaction items, atomic stock reduction, and idempotency key replays

---

## [x] Cycle 4: Physics-Based RF Mesh, Smart Rules & Continuous Decay POS (VPA 1.4, 2.4, 3.4)
- `[x]` **Database Schema & Math Engines**
  - `[x]` Update `./backend/database.py` with tables: `security_nodes`, `map_obstacles_rtree`, `map_obstacles_meta`, `harvest_orders`, `agricultural_rules`, `pricing_multipliers`
  - `[x]` Implement R*Tree ray-tracing attenuation math, A* multi-hop pathfinding, continuous exponential decay pricing, and field-level LWW sync helpers
- `[x]` **Backend API Endpoints (`./backend/main.py`)**
  - `[x]` Endpoints `GET/POST /api/agriculture/rules` & `POST /api/agriculture/rules/evaluate` (closed-loop & Cross-VPA harvest orders / spoilage flash sales)
  - `[x]` Endpoints `GET /api/security/nodes` & `PUT /api/security/nodes/{node_id}/position` (R*Tree obstacle attenuation, A* multi-hop routing, LWW sync)
  - `[x]` Endpoint `GET /api/pos/promotions` (continuous exponential decay pricing calculation)

---

## [x] Stage 1 Core Enhancements: Multi-Tenancy, Vouchers & Customer Digital Banking
- `[x]` **Multi-Tenant Business Operations & RBAC**
  - `[x]` Create `businesses` and `business_operators` tables in `./backend/database.py`
  - `[x]` Implement staff permission delegation for `pos`, `inventory`, `agriculture`, `security`, `social`, `reports`
- `[x]` **Offline QR Bearer Vouchers & Double-Spend Prevention**
  - `[x]` Create `offline_vouchers` table with HMAC-SHA256 signature chains
  - `[x]` Implement single-use redemption and POS voucher change issuing
- `[x]` **Customer Digital Banking & Receipt Vault**
  - `[x]` Create `customer_wallets` (`ACC-2026-XXXXXX`) and double-entry `wallet_ledger`
  - `[x]` Implement atomic P2P transfers, voucher-to-wallet conversion, and POS wallet payments
  - `[x]` Create `customer_receipts` table with SHA-256 integrity hash verification and PDF generation

---

## [x] Portability, Self-Replication & Node Lifecycle Management
- `[x]` **Zero-Configuration Portable Bootstrapper (`../start.py`)**
  - `[x]` Preflight requirement inspection and dependency auto-resolution
  - `[x]` Multi-node process supervision (Vault Node :8000, Data Node :8002, Beacons :8001)
  - `[x]` Automatic web browser launch to sign-in page upon server startup
  - `[x]` CLI flags: `--all`, `--vault-only`, `--data-only`, `--status`, `--no-browser`, `--create-node`
- `[x]` **Self-Replicating Node Generator Engine (`../node_generator.py`)**
  - `[x]` Standalone bundle synthesis into `../Exported_Nodes/MADN_<name>_Port<port>/`
  - `[x]` Bundle includes autonomous `start.py`, `server.py`, `storage.py`, `beacon.py`, `node_config.json`, `requirements.txt`, and embedded `frontend/` UI
- `[x]` **Remote Edge Node Lifecycle Control**
  - `[x]` Standardized `/api/node/status`, `/api/node/activate`, and `/api/node/deactivate` on standalone Data Nodes
  - `[x]` HTTP 503 Maintenance Mode gating when nodes are placed in standby
  - `[x]` Subnet-wide remote activation via Vault Node API `/api/cluster/nodes/{node_id}/toggle-active`
## [x] Dynamic Extensible Multi-Currency & World Currency Ingestion Engine
- `[x]` **Extensible Multi-Currency & Virtual Token Architecture**
  - `[x]` Create `currencies` and `wallet_balances` dynamic tables in `./backend/database.py`
  - `[x]` Support custom community tokens (e.g. `ECO`, `AGRI`, `LABOR`) with user-defined names, symbols, and USD rates
  - `[x]` Align official ISO 4217 standard representation for **Zimbabwe Gold (ZiG)** (`ZWG`, symbol: `ZiG`, classification: `gold_backed`)
  - `[x]` Enforce authentic `0.00` zero-balance account initialization across all active currencies
- `[x]` **Global World Currency (ISO 4217) & Crypto Continuous Collector**
  - `[x]` Create `../Data_Node/currency_collector.py` with 170+ ISO world fiat currencies and top 50+ cryptocurrencies
  - `[x]` Create `global_currency_catalog` table in `./backend/database.py` with multi-tier collision detection (`validate_currency_code_collision`)
  - `[x]` Add REST endpoints `GET /api/currencies/catalog`, `GET /api/currencies/validate`, `POST /api/currencies/catalog/sync`
  - `[x]` Integrate real-time collision badge, "Adopt Official Standard 🪄" button, and World Catalog Explorer in `./frontend/app.js` and `./frontend/index.html`
## [x] Modular Dynamic Field Product Engine & Business Subsystem
- `[x]` **Core Inventory Architecture & System SKU Generation**
  - `[x]` Enhanced `./backend/database.py` with columns: `cost_price_usd`, `barcode`, `category`, `subcategory`, `brand`, `description`, `specifications`, `image_url`, `wholesale_price_usd`, `wholesale_min_qty`, `extra_attributes`, `business_id`
  - `[x]` Deterministic system SKU generation function `generate_system_sku(name, category)` in `./backend/database.py`
  - `[x]` Enforced mandatory non-negative Cost Price (COGS) and positive Selling Price validations in `./backend/main.py`
  - `[x]` Zero dummy data cleanup across all initialization tables
- `[x]` **Modular Dynamic Intake Interface & Empty State POS Bypass**
  - `[x]` Rebranded all frontend navigation, dashboard cards, and subnav tabs from legacy "POS & Market" to **💼 Business**
  - `[x]` Implemented empty-state POS bypass: When catalog item count is $N=0$, the POS terminal hides the checkout register and renders a direct store setup intake form
  - `[x]` Built modular product intake modal (`#modal-add-store-product`) with clickable dynamic attribute pills:
    - `+ 🖼️ Image`: File upload reader converting to base64 Data URL + direct URL input + live preview thumbnail
    - `+ 🏷️ Barcode`: Universal scannable product identifier (EAN/UPC/ISBN) with automatic random generator
    - `+ 🗂️ Category & Subcategory`: Taxonomic hierarchy builder with quick presets (`Drinks > Energy Drinks`, `Hardware > Cables`, `Crops > Grains`, `Electronics > Solar`)
    - `+ 🏢 Brand / Manufacturer`: Manufacturer branding attribute
    - `+ 📝 Description & Specs`: Textarea plus dynamic key-value spec rows with `+ Add Custom Specification`
    - `+ 💎 Wholesale Price`: Bulk tier unit price & minimum order quantity
    - `+ ⚠️ Low Stock Threshold`: Custom alert trigger
- `[x]` **Store Setup Prerequisite & Multi-Enterprise Business Banking (Version 1.19.6 - Inzuzo)**
  - `[x]` Enforced store setup prerequisite: Gated inventory addition behind mandatory business store creation in `./backend/database.py` and `POST /api/inventory` (HTTP 400 when 0 stores exist)
  - `[x]` Modular dynamic field choice store creation modal (`#modal-create-business`) with mandatory fields (`name`, `tagline`, `description`) and modular pills (`Logo & Banner`, `Contact & Location`, `Tax ID & Industry`, `Settlement Currency`, `Operating Hours`, `Return Policy`, `Receipt Footer`)
  - `[x]` Auto-provisioned dedicated enterprise banking accounts (`BIZ-ACC-...`) in `wallets` table with multi-currency balance tracking
  - `[x]` Multi-store unified POS cart checkout routing proceeds directly to respective business wallets with HMAC-SHA256 ledger signatures
  - `[x]` Multi-business sales analytics dashboard (`GET /api/businesses/analytics`) calculating Gross Revenue, COGS, Profit Margins, and 24h velocity for single stores or aggregated across all stores
  - `[x]` Automated test suite `./backend/test_store_setup_and_multibiz_banking.py` (100% pass rate)
  - `[x]` Full regression matrix: 42 passed, 3 skipped live server tests, 0 failed

---

## [ ] Cycle 5: Direct P2P Mesh Data Sync & Captive Portal Vending (Next Milestone)
- `[ ]` **Database Schema & Vector Ledger**
  - `[ ]` Add `sync_vector_ledger` and `peer_nodes` tables to `../Data_Node/storage.py` and `./backend/database.py`
- `[ ]` **Backend API Endpoints**
  - `[ ]` Endpoint `POST /api/sync/pull-push` for bidirectional delta sync across edge nodes using LWW timestamps
  - `[ ]` Endpoint `POST /api/network/access-tokens/generate` for issuing timed captive portal Wi-Fi access tokens on POS receipts
- `[ ]` **Frontend SPA UI Integration**
  - `[ ]` Add Peer Mesh Sync Center in Cluster view with manual `[ 🔄 Sync Mesh Data ]` action
  - `[ ]` Add Wi-Fi token QR slip renderer to POS checkout receipts

