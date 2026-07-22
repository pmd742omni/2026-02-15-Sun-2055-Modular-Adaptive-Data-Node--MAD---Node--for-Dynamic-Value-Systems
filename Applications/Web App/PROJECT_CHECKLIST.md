# Master Task List & Progress Checklist — MADN Web Application Development

## [x] Authentication & Admin Controls (Hardening Phase)
- `[x]` **Backend Security Foundation**
  - `[x]` Create `backend/auth_utils.py` with scrypt, constant-time validation, and RFC 6238 TOTP
  - `[x]` Create `backend/database.py` with SQLite tables, WAL mode, admin bootstrap (env/TTY check), and append-only audit log file anchor
  - `[x]` Update `backend/main.py` with FastAPI endpoints, HttpOnly cookies, Double-Submit CSRF check, and session/step-up authorization middleware
  - `[x]` Create `backend/test_auth.py` automated test suite and run it to verify security properties
- `[x]` **Frontend Auth SPA Integration**
  - `[x]` Update `frontend/index.html` with Login Overlay, User Profile Drawer, and Admin Control panel
  - `[x]` Update `frontend/index.css` with glassmorphic styles, admin table states, and form feedback cues
  - `[x]` Update `frontend/app.js` with secureFetch, checkActiveSession, form handlers, dynamically rendered user rosters, step-up elevation intercepts, and local canvas QR renderer

## [x] Baseline Setup
- `[x]` Create `index.html` main SPA skeleton inside `Applications/Web App/frontend/`
- `[x]` Define CSS design system and custom properties in `Applications/Web App/frontend/index.css`
- `[x]` Implement core state manager in `Applications/Web App/frontend/app.js`

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
  - `[x]` Test VPA 2.1 alongside VPA 1.1
- `[x]` **VPA 3.1: Multi-Currency Tri-Ledger (USD/ZAR/ZWG)** (POS)
  - `[x]` Create transaction terminal layout card
  - `[x]` Implement currency converter with customizable exchange rates
  - `[x]` Program change calculator accepting mixed currency payments
  - `[x]` Test VPA 3.1 integration and perform full Cycle 1 verification pass

## [x] Cycle 2: Diagnostics, QR Validation & Analytics (VPA 1.2, 2.2, 3.2)
- `[x]` **VPA 1.2: Interactive Symptom Diagnostic Tree** (Agriculture)
  - `[x]` Create symptom diagnostic card/wizard UI in Agricultural tab
  - `[x]` Define branching tree logic for crops and livestock diseases
  - `[x]` Implement interactive question steps and local remedies outputs
- `[x]` **VPA 2.2: Local QR Code Credential Generator & Scanner** (Security)
  - `[x]` Implement QR code guest credential generator
  - `[x]` Build HTML5 Canvas scanner/mock reader panel to process QR check-ins
  - `[x]` Program visitor ledger logs validation against SQLite database records
- `[x]` **VPA 3.2: Interactive Sales Analytics & Visualizer** (POS)
  - `[x]` Design responsive analytics dashboard and visual metrics cards
  - `[x]` Write custom HTML5 Canvas drawing functions to render hourly sales graphs without internet dependencies
  - `[x]` Program date/range aggregates and sales volume statistics

## [x] Cycle 3: Calculators, Logs & Inventories (VPA 1.3, 2.3, 3.3)
- `[x]` **Database Schema & Configurations**
  - `[x]` Update `database.py` to create SQLite tables: `inventory`, `inventory_wastage`, `transactions`, `transaction_tenders`, `transaction_items`, `calculator_config`, `estimator_runs`, `shift_handover_logs`, `processed_requests`
  - `[x]` Implement `BEGIN IMMEDIATE` write locks, HMAC handover logging, and configurations seed
- `[x]` **Backend API Endpoints**
  - `[x]` Create VPA 1.3 agricultural calculator and history endpoints
  - `[x]` Create VPA 2.3 security handover logs with PIN checks and audit tracking
  - `[x]` Create VPA 3.3 inventory directory, stock adjust, and spoilage logs
  - `[x]` Update `/api/pos/checkout` to support multi-tender, transaction items, atomic stock reduction, and idempotency key replays
- `[x]` **Frontend SPA UI Integration**
  - `[x]` Update `index.html` with estimators sliders, severity handovers, and static warnings
  - `[x]` Update `index.css` with solid warning badges and layout grids
  - `[x]` Update `app.js` with hotkeys, estimators math, local cart auto-recovery, and handover PIN triggers
- `[x]` **Verification & Testing**
  - `[x]` Create and run `backend/test_cycle3.py` stress test
  - `[x]` Run manual/browser checks and document walkthrough details

## [x] Cycle 4: Physics-Based RF Mesh, Smart Rules & Continuous Decay POS (VPA 1.4, 2.4, 3.4)
- `[x]` **Database Schema & Math Engines**
  - `[x]` Update `database.py` with tables: `security_nodes`, `map_obstacles_rtree`, `map_obstacles_meta`, `harvest_orders`, `agricultural_rules`, `pricing_multipliers`
  - `[x]` Add PRAGMA migration check for `cost_price_usd` column on `inventory`
  - `[x]` Implement R*Tree ray-tracing attenuation math, A* multi-hop pathfinding, continuous exponential decay pricing, and field-level LWW sync helpers
- `[x]` **Backend API Endpoints (`main.py`)**
  - `[x]` Endpoint `GET/POST /api/agriculture/rules` & `POST /api/agriculture/rules/evaluate` (closed-loop & Cross-VPA harvest orders / spoilage flash sales)
  - `[x]` Endpoint `GET /api/security/nodes` & `PUT /api/security/nodes/{node_id}/position` (R*Tree obstacle attenuation, A* multi-hop routing, LWW sync)
  - `[x]` Endpoint `GET /api/pos/promotions` (continuous exponential decay pricing calculation)
- `[x]` **Frontend SPA UI Integration**
  - `[x]` Update `index.html` with Rules Manager, Harvest Work Orders feed, SVG map obstacles & Fresnel zones, Canvas signal coverage heatmap toggle, 24H Digital Twin timeline scrubber, and POS flash sale badges
  - `[x]` Update `index.css` for obstacle styling, heatmap canvas, grabbing cursors, and work order badges
  - `[x]` Update `app.js` with Pointer Events dragging, signal heatmap drawing, harvest order transitions, and continuous decay POS calculations
- `[x]` **Verification & Testing**
  - `[x]` Create and run `backend/test_cycle4.py` automated test suite
  - `[x]` Perform E2E verification and update `walkthrough.md`

## [ ] Cycle 5: Multi-Node Peer Sync, Intrusion Triangulation & Captive Portal Vending (VPA 1.5, 2.5, 3.5)
- `[ ]` **Database Schema & Peer Ledger**
  - `[ ]` Add SQLite tables for `peer_nodes`, `intrusion_triangulation_logs`, `captive_portal_vouchers`, and `sync_vector_ledger` in `database.py`
  - `[ ]` Implement local hotspot subnet discovery and peer node heartbeat tracking
- `[ ]` **Backend API Endpoints (`main.py`)**
  - `[ ]` Endpoint `GET/POST /api/sync/peers` & `POST /api/sync/pull-push` for peer-to-peer LWW delta exchange over local Wi-Fi
  - `[ ]` Endpoint `POST /api/security/triangulate` for 3-point RSSI signal trilateration to pinpoint intruder coordinates
  - `[ ]` Endpoint `POST /api/pos/vouchers/generate` & `GET /api/pos/vouchers/verify` for issuing captive portal Wi-Fi access tokens on POS checkout receipts
- `[ ]` **Frontend SPA UI Integration**
  - `[ ]` Add Peer Node Mesh Sync status card & Manual Force Sync trigger in VPA 1 (Agriculture)
  - `[ ]` Add Intrusion Triangulation heatmap marker & incident alert log overlay in VPA 2 (Security)
  - `[ ]` Add Captive Portal Wi-Fi Voucher printing card & barcode preview on POS Checkout Receipts in VPA 3 (POS)
- `[ ]` **Verification & Testing**
  - `[ ]` Create and run `backend/test_cycle5.py` automated test suite
  - `[ ]` Perform E2E system validation and update project walkthrough artifacts
