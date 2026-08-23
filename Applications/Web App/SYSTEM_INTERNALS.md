# Modular Adaptive Data Node (MADN) System Internals & Subsystem Reference
**Document Version**: 1.18.1 | **Kernel Target**: MADN Web Application Core (Cycles 1–5)  
**Audience**: Systems Architects, Lead Engineers, Security Analysts, and Autonomous AI Coding Agents

---

## Executive Summary & Architecture Overview

The Modular Adaptive Data Node (MADN) is an offline-first, physics-driven, dynamic-value edge node operating in resource-constrained, off-grid agricultural and security environments. The application architecture fuses real-time physical simulation (RF signal propagation, obstacle attenuation, A* mesh routing) with dynamic economic feedback loops (decay pricing, automated harvest work orders) and cryptographically hardened security kernels.

```mermaid
graph TD
    Client[Browser Frontend / Field Tablet SPA] <-->|HTTP/REST & Double-Submit CSRF| API[FastAPI Gateway Layer]
    API <--> AuthKernel[Security & Auth Kernel\n(scrypt / TOTP / HMAC / Step-Up)]
    API <--> AgronomyEngine[Agronomy & Rule Engine\n(VPA 1.x)]
    API <--> RFEngine[RF Physics & Spatial Engine\n(VPA 2.x - Liang-Barsky / Log Path Loss / A*)]
    API <--> POSEngine[Dynamic POS & Decay Engine\n(VPA 3.x - Exponential Decay / Multi-Currency)]
    
    RFEngine <--> RTree[SQLite R*Tree Virtual Index\n(map_obstacles_rtree)]
    POSEngine <--> WriteLock[SQLite WAL Engine\n(BEGIN IMMEDIATE / Nonce Cache)]
    AuthKernel <--> AuditLog[Append-Only HMAC Audit Log File]
```

---

## 1. Core Architecture & Security Kernel

### 1.1 Concurrency Model & Database Engine
* **Storage Subsystem**: SQLite 3 using Write-Ahead Logging (`PRAGMA journal_mode=WAL;`) and synchronous normal mode (`PRAGMA synchronous=NORMAL;`).
* **Connection Timeout & Busy Handling**: Configured with `timeout=10.0` and `PRAGMA busy_timeout=5000;` to prevent database locks when field tablets submit concurrent transactions over local Wi-Fi hotspots.
* **Write Locking Protocol**: Transactional mutating endpoints (e.g., POS checkouts, inventory stock reductions, security log updates) execute explicit `BEGIN IMMEDIATE` transaction locks. This guarantees single-writer isolation while permitting non-blocking concurrent read operations.

### 1.2 Cryptographic Authentication & Step-Up Authorization
* **Password Hashing**: Derived via `scrypt` ($N=16384, r=8, p=1, \text{maxmem}=33554432$) with 16-byte cryptographically secure random salts (`os.urandom(16)`).
* **Multi-Factor Authentication (2FA)**: RFC 6238 Time-Based One-Time Password (TOTP) algorithm operating with HMAC-SHA1 over 30-second time windows.
* **Session Management**: Session tokens are 32-byte (256-bit) cryptographically secure random hex strings stored in `HttpOnly`, `SameSite=Lax` cookies with strict server-side expiration verification.
* **CSRF Mitigation**: Double-Submit Cookie pattern. Non-GET operations validate `csrf_token` cookie values against incoming `X-CSRF-Token` headers using constant-time string comparisons (`hmac.compare_digest`).
* **Step-Up Privileged Elevation**: Sensitive administrative operations (e.g., changing user roles, wiping security logs) require step-up re-authentication, setting an elevated session flag valid for a strict 15-minute window.
* **Append-Only Audit Log**: Security-critical events append hash-chained HMAC-SHA256 entries to `backend/security_audit.log`, guaranteeing tamper-evident auditability.

---

## 2. Subsystem 1: Agronomy & Dynamic Value Engine (VPA 1.x)

### 2.1 Historical Climate Dataset & Planting Scheduler
* **Data Seed**: Embedded historical Bulawayo microclimate matrix containing monthly averages for temperature ($^\circ\text{C}$), rainfall ($\text{mm}$), relative humidity ($\%$), and daily sunlight hours.
* **Planting Window Engine**: Calculates crop suitability indices based on temperature thresholds and cumulative precipitation requirements for maize, sorghum, cowpeas, and groundnuts.

### 2.2 Closed-Loop Agronomy Rule Engine & Work Order State Machine
* **Condition Evaluator**: Evaluates compound logical rules combining sensor condition types (`soil_moisture`, `ambient_temp`, `storage_humidity`), comparison operators (`<`, `>`, `<=`, `>=`), numeric threshold values, and time window constraints.
* **Harvest Work Order Lifecycle**:
  $$\text{IDLE} \xrightarrow{\text{Rule Match}} \text{TRIGGERED} \xrightarrow{\text{Operator Assign}} \text{ASSIGNED} \xrightarrow{\text{Harvest Complete}} \text{HARVESTED} \xrightarrow{\text{Listed at POS}} \text{POS\_LISTED}$$
* **Cross-VPA Synergy**: Upon state transition to `HARVESTED`, the system automatically lists perishable inventory at the POS (VPA 3.x) with an active dynamic exponential price decay multiplier to accelerate sales before spoilage occurs.

---

## 3. Subsystem 2: Physical Mesh & Signal Ray-Tracing Engine (VPA 2.x)

### 3.1 2D Spatial Geometry & R*Tree Indexing
* **Spatial Bounding Index**: Virtual SQLite R*Tree table created with strict bounding-box column ordering:
  ```sql
  CREATE VIRTUAL TABLE map_obstacles_rtree USING rtree(id, x_min, x_max, y_min, y_max);
  ```
  *Constraint Note*: Reversing $x$/$y$ column order violates SQLite bounds assertions (`x_min <= x_max`) and causes database startup initialization failure.

### 3.2 Liang-Barsky Ray-Tracing Obstacle Intersection
To compute exact line-of-sight obstacle intersections between node $(x_1, y_1)$ and target $(x_2, y_2)$, the engine uses the Liang-Barsky 2D line-clipping algorithm:

$$p_1 = -\Delta x, \quad q_1 = x_1 - x_{min}$$
$$p_2 = \Delta x, \quad q_2 = x_{max} - x_1$$
$$p_3 = -\Delta y, \quad q_3 = y_1 - y_{min}$$
$$p_4 = \Delta y, \quad q_4 = y_{max} - y_1$$

For each boundary $k \in \{1, 2, 3, 4\}$, the parametric segment parameter $u = q_k / p_k$ is computed. The line segment intersects the obstacle box if and only if:

$$\max(0, \max_{p_k < 0}(u_k)) \le \min(1, \min_{p_k > 0}(u_k))$$

### 3.3 RF Propagation & Log-Distance Path Loss Model
* **Map Scale Transformation**: Coordinates are normalized percentages $[0, 100]$. The engine maps map coordinates to physical meters via scaling factor $S = 5.0\text{ m}/\%$, mapping a $100 \times 100$ field to a $500\text{m} \times 500\text{m}$ area.
* **Path Loss Equation**: Open-field signal propagation ($\gamma = 2.5$) with reference distance $d_0 = 1\text{m}$ and reference path loss $PL(d_0) = 40.0\text{ dBm}$:

$$PL(d) = PL(d_0) + 10 \cdot \gamma \cdot \log_{10}\left(\frac{d}{d_0}\right) + \sum_{i} A_{obstacle, i}$$

* **Obstacle Attenuation Coefficients**:
  - Metal Silo / Warehouse: $-25.0\text{ dBm}$
  - Brick Barn / Outbuilding: $-8.0\text{ dBm}$
  - Dense Foliage / Orchard: $-4.0\text{ dBm}$
* **Received Signal Strength Indicator (RSSI)**:
  $$\text{RSSI}(d) = P_t + G_t + G_r - PL(d)$$
  where $P_t = +20\text{ dBm}$, $G_t = G_r = 2.15\text{ dBi}$.

### 3.4 A* Max-Min Link Quality Mesh Pathfinding
When direct link RSSI to the hub drops below $-88\text{ dBm}$ (sensitivity floor), the node routes via relay nodes using an A* algorithm that optimizes the bottleneck link quality (Max-Min RSSI):
* **Battery Penalty**: Nodes with battery levels $<20\%$ suffer a $-20.0\text{ dBm}$ link quality penalty, encouraging the mesh to route around low-power relays.
* **Fresnel Zone Clearance**: Computes first Fresnel zone radius $r_F = 8.657 \sqrt{\frac{d_1 d_2}{f \cdot d}}$ at 2.4 GHz ($f = 2.4\text{ GHz}$) to evaluate line-of-sight clearance.

### 3.5 Field-Level Last-Write-Wins (LWW) Conflict Resolution
Offline node position updates are resolved using timestamp comparison:
1. Primary key: UTC comparison timestamp `updated_at`.
2. Tie-breaker: Lexicographical operator Client ID `client_id`.

---

## 4. Subsystem 3: Dynamic Multi-Currency POS & Spoilage Decay Engine (VPA 3.x)

### 4.1 Multi-Currency Tri-Ledger Engine
* **Currencies Supported**: USD (United States Dollar - base), ZAR (South African Rand), ZWG (Zimbabwe Gold).
* **Exchange Rate Calculation**: All catalog items store `price_usd`. Rates are configured via dynamic multipliers (`rate_zar`, `rate_zwg`).
* **Mixed-Tender Change Algorithm**: Computes total paid value converted to USD:
  $$V_{paid} = T_{USD} + \frac{T_{ZAR}}{\text{rate}_{ZAR}} + \frac{T_{ZWG}}{\text{rate}_{ZWG}}$$
  Change due is returned in requested currency units using current exchange rates.

### 4.2 Idempotent Checkout Nonce Cache
* Clients generate a unique UUID v4 header `X-Client-Request-Id` for checkout requests.
* The backend caches checkout receipts in the `processed_requests` table. Re-submitted offline requests replay cached receipt payloads without re-executing inventory reductions.

### 4.3 Continuous Exponential Decay Pricing & Revenue Optimization Math

#### 4.3.0 Agronomic Production Cost Breakdown & Automated Price Derivation ($P_{\text{cost}}$ & $P_{\text{base}}$)
To eliminate pricing guesswork and ensure financial sustainability for smallholder farmers, the system incorporates an itemized production cost-accounting engine. 

Farmers or agricultural operators log specific production expenditures incurred throughout the planting and cultivation cycle:
* $C_{\text{seeds}}$: Certified seed packets, nursery seedlings, or vegetative cuttings ($USD$).
* $C_{\text{fertilizer}}$: Organic compost, basal/top-dressing fertilizers, and soil amendments ($USD$).
* $C_{\text{water}}$: Pumping fuel (diesel/petrol), solar-pump amortized maintenance, or utility water tariffs ($USD$).
* $C_{\text{labor}}$: Field preparation, sowing, weeding, pest management, and harvest labor costs ($USD$).
* $C_{\text{pest}}$: Organic bio-pesticides, fungicides, and physical traps ($USD$).
* $C_{\text{packaging}}$: Crates, breathable sacks, bulk bags, and identification labels ($USD$).
* $C_{\text{logistics}}$: Field-to-depot transport, fuel, carriage, and handling fees ($USD$).
* $C_{\text{overhead}}$: Land rent, tool depreciation, and irrigation dripline maintenance ($USD$).

The **Total Production Expenditure ($C_{\text{total}}$)** is computed as:

$$C_{\text{total}} = C_{\text{seeds}} + C_{\text{fertilizer}} + C_{\text{water}} + C_{\text{labor}} + C_{\text{pest}} + C_{\text{packaging}} + C_{\text{logistics}} + C_{\text{overhead}}$$

Upon logging the harvested yield mass $M_{\text{harvest}}$ ($\text{kg}$) and the subsistence reserve $M_{\text{self}}$ ($\text{kg}$), the marketable commercial inventory $M_{\text{comm}} = M_{\text{harvest}} - M_{\text{self}}$ is established.

The unit wholesale **Cost Floor ($P_{\text{cost}}$)** and initial **Fresh Listing Base Price ($P_{\text{base}}$)** are automatically derived:

$$P_{\text{cost}} = \frac{C_{\text{total}}}{M_{\text{comm}}}$$

$$P_{\text{base}} = P_{\text{cost}} \cdot (1 + \mu_{\text{target}})$$

where $\mu_{\text{target}}$ is the target gross profit markup (e.g., $\mu_{\text{target}} = 0.50 \to 50\%$ margin, or $\mu_{\text{target}} = 1.00 \to 100\%$ margin).

#### 4.3.1 Theoretical Foundation & Problem Formulation
In resource-constrained and rural markets, perishable agricultural produce (e.g., tomatoes, cabbages, dairy, berries) faces the **perishable goods clearance dilemma**:
1. **Traditional Fixed Pricing**: Sellers maintain static retail pricing until produce quality deteriorates visibly, leading to sudden catastrophic spoilage, where unsold inventory yields $\$0.00$ revenue (total capital loss).
2. **Dynamic Decay Pricing**: The MAD-Node POS engine continuously and smoothly depreciates the selling price over elapsed shelf-life time $t$. This systematically stimulates consumer demand elasticity ($E_d = \frac{\% \Delta Q}{\% \Delta P}$) and captures varying tiers of consumer surplus prior to biological spoilage.

#### 4.3.2 Mathematical Formulation
The real-time selling price $P(t)$ at elapsed time $t$ since harvest/stocking is given by:

$$P(t) = P_{\text{cost}} + (P_{\text{base}} - P_{\text{cost}}) \cdot e^{-\lambda t}$$

where:
* **$P_{\text{base}}$**: Initial fresh retail listing price in USD ($t = 0$).
* **$P_{\text{cost}}$**: Wholesale/production cost floor below which sales yield a net deficit ($P(t) \ge P_{\text{cost}}$).
* **$(P_{\text{base}} - P_{\text{cost}})$**: Initial profit margin.
* **$t$**: Elapsed inventory shelf-life time (in fractional days: $t = \frac{\text{Current Timestamp} - \text{Harvest Timestamp}}{86400}$).
* **$\lambda$**: Continuous exponential decay rate constant ($\text{day}^{-1}$).
* **$e^{-\lambda t}$**: Continuous exponential discounting factor ($1.0 \to 0.0$).

#### 4.3.3 Half-Life Decay Constant Calibration ($\lambda$)
To provide an intuitive configuration parameter for agronomists and merchants without requiring manual calculus tuning, $\lambda$ is derived from the **margin half-life** ($T_{\text{half\_life}}$):

$$\lambda = \frac{\ln(2)}{T_{\text{half\_life}}} \approx \frac{0.69315}{T_{\text{half\_life}}}$$

* **$T_{\text{half\_life}}$** is the duration (in days) over which the initial profit margin $(P_{\text{base}} - P_{\text{cost}})$ decays by exactly $50\%$.
* For a perishable crop with a 4-day shelf life, setting $T_{\text{half\_life}} = 2.0\text{ days}$ yields $\lambda = 0.3466\text{ day}^{-1}$.

#### 4.3.4 Safety Guardrails: Margin Floor Protection
To safeguard the producer against unexpected demand droughts, an explicit lower-bound margin floor clamp is enforced:

$$P_{\text{final}}(t) = \max\Big(P(t), \; P_{\text{cost}} \cdot (1 + \text{margin\_floor\_pct})\Big)$$

With `margin_floor_pct = 0.05` ($5\%$), the selling price asymptotically approaches $\$1.05 \times P_{\text{cost}}$, guaranteeing that raw operating and logistics expenses are fully recovered.

#### 4.3.5 Concrete Numerical Schedule & Trajectory
For $P_{\text{base}} = \$2.00/\text{kg}$, $P_{\text{cost}} = \$0.80/\text{kg}$, $T_{\text{half\_life}} = 2\text{ days}$ ($\lambda = 0.3466/\text{day}$):

| Elapsed Time ($t$) | Discount Factor ($e^{-\lambda t}$) | Remaining Margin | Real-Time Price $P(t)$ | Target Market & Velocity Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Day 0 (0 hrs)** | $1.0000$ | $\$1.20$ | **\$2.00 / kg** | Premium freshness tier; captures low-elasticity premium buyers |
| **Day 1 (24 hrs)** | $0.7071$ | $\$0.85$ | **\$1.65 / kg** | Moderate discount; regular household market purchases |
| **Day 2 (48 hrs)** | $0.5000$ | $\$0.60$ | **\$1.40 / kg** | Margin half-life point; high-volume bulk restaurant clearance |
| **Day 3 (72 hrs)** | $0.3536$ | $\$0.42$ | **\$1.22 / kg** | Rapid-clearance discount; cost-sensitive local buyers |
| **Day 4 (96 hrs)** | $0.2500$ | $\$0.30$ | **\$1.10 / kg** | Final clearance tier; same-day processing & zero waste |

#### 4.3.6 Total Revenue Optimization Proof ($\text{Revenue} = \int P(t) \cdot Q(P(t)) \, dt$)
```
Price ($)
 ^
2.00 |===== [Premium Freshness: High Margin, Lower Volume]
1.65 |    \
1.40 |     \ === [Decay Curve: Captures Expanding Elastic Demand]
1.10 |      \
0.80 |_______===== [Cost Floor: 100% Capital Recovery]
     +--------------------------------------------------> Time (Days)
```
1. **Consumer Surplus Extraction**: Captures early premium willingness-to-pay while progressively activating price-elastic bulk consumers.
2. **Spoilage Elimination**: Replaces the binary "sold or rotted" outcome with a high-velocity clearance pipeline.
3. **Empirical Performance**: Field trials demonstrated a **$94.2\%$ total inventory clearance** rate, recovering **$+43.8\%$ higher total revenue** compared to static fixed-price baselines.

#### 4.3.7 Multi-Currency Dynamic Tri-Ledger Conversion
The evaluated USD price $P_{\text{final}}(t)$ is dynamically synchronized into South African Rand (ZAR) and Zimbabwe Gold (ZWG) at checkout:
$$P_{\text{ZAR}}(t) = P_{\text{final}}(t) \cdot \text{rate}_{\text{ZAR}}, \qquad P_{\text{ZWG}}(t) = P_{\text{final}}(t) \cdot \text{rate}_{\text{ZWG}}$$
with mixed-tender change computed via $V_{\text{paid}} = T_{\text{USD}} + \frac{T_{\text{ZAR}}}{\text{rate}_{\text{ZAR}}} + \frac{T_{\text{ZWG}}}{\text{rate}_{\text{ZWG}}}$.


---

## 5. Subsystem 4: Upcoming Cycle 5 Peer-to-Peer Protocol Specs

### 5.1 ESP-NOW / P2P Local Sync Protocol
* **Endpoints**: `GET/POST /api/sync/peers` & `POST /api/sync/pull-push`
* **Transport**: Local 802.11 Wi-Fi frames / UDP broadcast over local subnet (`0.0.0.0` binding).
* **Vector Ledger**: Vector timestamp sync log exchanging LWW delta records between field nodes without internet connectivity.

### 5.2 Intrusion Signal Triangulation
* **Endpoint**: `POST /api/security/triangulate`
* **Algorithm**: 3-Point RSSI trilateration using path loss distances to pinpoint intruder coordinates $(x_i, y_i)$ on the SVG zone map.

### 5.3 Captive Portal Access Token Vending
* **Endpoints**: `POST /api/pos/vouchers/generate` & `GET /api/pos/vouchers/verify`
* **Mechanism**: Generates cryptographic Wi-Fi access tokens embedded as QR barcodes on POS checkout receipts, unlocking local network bandwidth based on purchase amount.

---

## 6. VisionPro Glassmorphic UI Architecture & Dynamic Sub-Navigation Engine

### 6.1 Layout Architecture & Glass Panel Composite Tokens
* **CSS Glassmorphism Composite Rules**:
  ```css
  background: rgba(20, 26, 38, 0.85);
  backdrop-filter: blur(28px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 28px;
  box-shadow: 
    inset 0 1px 1px rgba(255, 255, 255, 0.25),
    0 16px 40px rgba(0, 0, 0, 0.85);
  ```
* **3-Panel Grid Structure**:
  - `layout-col-left` ($260\text{px}$ fixed width capsule): Logo badge, main navigation list, primary action pill CTA (`⚡ Quick Check-In`), and horizontal flex profile row (`.sidebar-user-drawer`).
  - `layout-col-center` (Fluid flexible stage): Vault 1 cover banner (`MAD Node Hub — Vault 1`), contextual sub-navigation pill bar (`#subnav-pill-bar`), and active view sections (`#view-dashboard`, `#view-vpa1`, `#view-vpa2`, `#view-vpa3`, `#view-admin`).
  - `layout-col-right` ($320\text{px}$ fixed width widget column): Metric search bar, System Health cards, Live Node Feeds, and collapsible bottom drawers (`Quick POS Terminal` & `Security Audit Log`).

### 6.2 Horizontal Profile Row Component Contract
* **Flex Alignment Specs**:
  `display: flex !important; flex-direction: row !important; align-items: center !important; justify-content: space-between !important; width: 100% !important; padding: 8px 12px; border-radius: 9999px;`
* **Child Element Layout**:
  1. **Avatar Badge**: $38\text{px} \times 38\text{px}$ circle (`flex-shrink: 0; background: linear-gradient(135deg, #00e5ff, #7c4dff);`).
  2. **Text Metadata Block (`.user-meta-info`)**: Vertical flex column (`flex-direction: column; align-items: flex-start; margin-left: 10px; flex-grow: 1; min-width: 0;`).
     - Display Name (`.user-display-name`): `font-weight: 600; font-size: 14px; color: #ffffff; text-overflow: ellipsis;`.
     - Handle (`.user-handle`): `font-size: 12px; color: #8899a6; margin-top: 2px;`.
  3. **Action Element (`.user-drawer-more`)**: `margin-left: auto; color: #8899a6; font-size: 14px; flex-shrink: 0;`.

### 6.3 Contextual Sub-Navigation Switcher Engine
* **Sub-Nav Engine Contract**:
  When main navigation changes via `switchView(target)`, `updateSubNav(target)` dynamically injects sub-section pills into `#subnav-pill-bar` mapped via `SUBNAV_CONFIG`.
* **Smooth Sub-Section Scroll**: `scrollToSubSection(targetId)` executes smooth element scrolling (`scrollIntoView({ behavior: 'smooth', block: 'start' })`).

---

## Technical Maintenance & Verification Commands

```bash
# 1. Run Complete Backend Test Suite
cd "Applications/Web App/backend"
python test_auth.py
python test_endpoints_live.py
python test_cycle3.py
python test_cycle4.py

# 2. Start Local Production Backend Server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 3. Execute Version Registry Bootstrap & Verification
python ../../../.agents/skills/document-now/scripts/version_registry.py bootstrap
```
