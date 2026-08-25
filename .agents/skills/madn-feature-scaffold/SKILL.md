---
name: madn-feature-scaffold
description: Intelligently scaffolds and implements new modular subsystems, hardware nodes, or feature modules across the entire Tri-Node stack (UI, Data Node collector, Vault Node ledger/security, and automated pytest suites) with zero boilerplate and full architectural alignment.
---

# MADN Intelligent Feature & Subsystem Scaffolder

This skill empowers Antigravity to rapidly design, scaffold, and implement new modular components, hardware node interfaces, or domain subsystems (e.g. IoT Sensor Node, Agricultural Drone Mesh, Solar Micro-Ledger, Dynamic Barcodes, Voice-guided Touch POS) with full Tri-Node stack integration and rigorous unit test coverage.

---

## 1. Trigger Conditions

Activate this skill whenever the developer specifies:
- `"scaffold feature [name]"` or `"create subsystem [name]"`
- `"implement module [name]"` or `"add modular component [name]"`
- `"build new node [type]"` (e.g. Weather Sensor Node, Grain Mill Node, Gatekeeper Node)
- Requests end-to-end implementation of a new capability for the MADN.

---

## 2. Standardized 5-Tier Scaffolding Architecture

When creating any new subsystem, scaffold across all 5 tiers:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Database Schema & WAL Concurrency (database.py)          │
│    - SQLite table with UUID, timestamps, indexes            │
│    - Zero-seed balance rule & BEGIN IMMEDIATE lock safety    │
├─────────────────────────────────────────────────────────────┤
│ 2. Backend REST API Endpoints (main.py)                     │
│    - Protected by get_current_user / step-up auth           │
│    - Pydantic models with input sanitization                │
├─────────────────────────────────────────────────────────────┤
│ 3. Standalone Data Node Collector / Sync (Data_Node/)       │
│    - Autonomous background collector / reference sync       │
│    - Multicast heartbeat & cluster registration             │
├─────────────────────────────────────────────────────────────┤
│ 4. Operator Glassmorphism UI (index.html, index.css, app.js)│
│    - Responsive segmented sub-tabs & search filter          │
│    - Universal fullscreen expand/restore controls (⛶ / 🗗)   │
├─────────────────────────────────────────────────────────────┤
│ 5. Automated Verification Test Suite (test_<name>.py)       │
│    - Comprehensive unit & regression tests with pytest      │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Step-by-Step Implementation Workflow

### Step 1: Subsystem Design & Requirements Synthesis
- Analyze the requested feature's role in the decentralized ecosystem.
- Determine whether the subsystem requires Data Node background ingestion, Vault Node ledger transactions, or both.

### Step 2: Database Schema & Transaction Helpers (`database.py`)
- Define dedicated SQLite table with proper foreign keys and constraints.
- Implement CRUD operations using `BEGIN IMMEDIATE` for transactional writes.

### Step 3: API Endpoint Implementation (`main.py`)
- Expose `/api/<subsystem>/...` endpoints with role-based access control (`ROLE_ADMIN`, `ROLE_OPERATOR`, `ROLE_CUSTOMER`).
- Enforce CSRF token verification and HMAC authentication.

### Step 4: Operator UI View (`index.html`, `index.css`, `app.js`)
- Add a new glassmorphic panel in `index.html` with:
  * Inspiring header title and friendly description.
  * Universal `btn-panel-expand` (`⛶ Expand` / `🗗 Restore (Esc)`).
  * Segmented sub-tabs for clean layout separation.
- Wire frontend event listeners and API calls in `app.js`.

### Step 5: Automated Test Suite & Regression Verification
- Create `Applications/Web App/backend/test_<subsystem>.py`.
- Run `pytest test_<subsystem>.py -v` and ensure **100% pass rate**.
