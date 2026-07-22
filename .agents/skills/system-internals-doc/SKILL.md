---
name: system-internals-doc
description: Automatically generates, updates, or publishes a new edition of the deep technical reference manual (SYSTEM_INTERNALS.md) modeled after "Windows Internals" / "Understanding the Linux Kernel" whenever requested or when major architectural changes occur.
---

# System Internals Documentation Skill

This skill provides step-by-step instructions for AI agents and developers to generate, maintain, update, and publish new editions of the low-level **System Internals Reference Manual** (`SYSTEM_INTERNALS.md`).

---

## 1. Trigger Conditions

Execute this workflow when:
- The developer requests `"update system internals"`, `"generate internals doc"`, or `"publish new edition of system internals"`.
- Major architectural changes are introduced (e.g., database schema migrations, cryptographic updates, physical propagation math changes, or new network protocols).
- Preparing a major release checkpoint.

---

## 2. Analysis & Extraction Procedure

Before writing or editing `SYSTEM_INTERNALS.md`, perform a comprehensive code audit of the following subsystems:

1. **Core Kernel & Concurrency Subsystem**:
   - Inspect `backend/database.py` for SQLite PRAGMAs (`journal_mode=WAL`, `busy_timeout`), transaction write locks (`BEGIN IMMEDIATE`), connection pooling parameters, and schema definitions.
   - Inspect `backend/auth_utils.py` and `backend/main.py` for scrypt parameters ($N, r, p$), RFC 6238 TOTP window sizes, Double-Submit CSRF cookie validation, step-up elevation timeouts, and HMAC audit logging.

2. **Agronomy & Dynamic Value Subsystem (VPA 1.x)**:
   - Audit historical microclimate seeds, crop planting scheduler algorithms, diagnostic trees, and closed-loop agronomy rule engines (`TRIGGERED` -> `ASSIGNED` -> `HARVESTED` -> `POS_LISTED`).

3. **Physical Mesh & Spatial Ray-Tracing Subsystem (VPA 2.x)**:
   - Audit SQLite R*Tree table schemas (`map_obstacles_rtree`), Liang-Barsky 2D line clipping ray-tracing functions, Log-distance path loss equation ($\gamma$, $PL(d_0)$, obstacle attenuation summing), A* Max-Min link quality mesh pathfinding, battery level penalties, Fresnel zone clearance math, and Last-Write-Wins (LWW) field conflict resolution rules.

4. **Dynamic Multi-Currency POS & Spoilage Decay Subsystem (VPA 3.x)**:
   - Audit multi-currency tri-ledger conversion logic (USD/ZAR/ZWG), mixed-tender change algorithms, idempotent checkout nonce caching (`X-Client-Request-Id`), and continuous exponential price decay formulas ($P(t) = P_{cost} + (P_{base} - P_{cost}) \cdot e^{-\lambda t}$) with margin floor protection.

5. **Network & Protocol Specs (Cycle 5+)**:
   - Audit ESP-NOW / P2P local Wi-Fi sync endpoints (`/api/sync/peers`, `/api/sync/pull-push`), 3-point RSSI signal trilateration math (`/api/security/triangulate`), and captive portal Wi-Fi access voucher vending (`/api/pos/vouchers/generate`).

---

## 3. Document Generation Guidelines

When updating or generating `Applications/Web App/SYSTEM_INTERNALS.md`:

- **Style & Depth**: Write in an authoritative, low-level technical reference style (similar to *Windows Internals* or *Understanding the Linux Kernel*).
- **Diagrams**: Include GitHub Flavored Markdown Mermaid diagrams for subsystem flow and memory/data layouts.
- **Mathematical Formats**: Express all physical, cryptographic, and dynamic decay equations using clear LaTeX math syntax (`$ ... $` for inline, `$$ ... $$` for display blocks).
- **Code & SQL Snippets**: Include exact SQL table declarations, parameter values, and code contracts.
- **Edition Versioning**: Increment the document edition header (e.g., `Edition 1.0.0` -> `Edition 1.1.0`) matching the project release state.

---

## 4. Execution Workflow

```bash
# Step 1: Run Timestamp Utility
python .agents/skills/document-now/scripts/get_timestamp.py

# Step 2: Update SYSTEM_INTERNALS.md with audited technical details
# (Write to Applications/Web App/SYSTEM_INTERNALS.md)

# Step 3: Run Backend Test Suite to verify documentation claims
python Applications/Web App/backend/test_cycle4.py

# Step 4: Stage & Git Commit
git add "Applications/Web App/SYSTEM_INTERNALS.md" .agents/skills/
git commit -m "<YYYY-MM-DD Day HHMM>: Updated System Internals Technical Reference Manual (Edition X.Y.Z)"
```
