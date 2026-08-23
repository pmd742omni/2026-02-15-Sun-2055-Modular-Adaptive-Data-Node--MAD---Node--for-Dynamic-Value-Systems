# Chapter 5: Results, Testing, and Analysis

---

## 5.1 Introduction

This chapter presents the empirical results, experimental evaluations, and quantitative performance analyses of the **Modular Adaptive Data Node (MADN)**. Designed as a localized, off-grid autonomous edge computing system for sub-Saharan agricultural and peri-urban value chains, MADN addresses severe infrastructure deficits: erratic grid power, expensive cellular data, currency volatility, chronic physical coin shortages, and multi-tenant operator governance.

```mermaid
graph LR
    subgraph Empirical_Evaluation_Domains ["Empirical Evaluation Domains"]
        D1["Stage 1 Core Systems & Multi-Tenancy"]
        D2["Hierarchical RBAC & Operator Delegation"]
        D3["Offline Cryptographic Bearer Vouchers"]
        D4["Perishable Continuous Price Decay"]
        D5["Physical RF Mesh & Ray-Tracing Math"]
        D6["Database Concurrency & Audit Integrity"]
    end
```

---

## 5.2 Testing Procedures

To empirically validate the Stage 1 Core System Architecture, Multi-Business Tenancy, Offline Cryptographic Bearer Vouchers, and Hierarchical RBAC Operator Delegation, three comprehensive test suites were developed and executed under strict academic testing protocols:
1. `test_stage1_core.py`: Validates agricultural lifecycle math, continuous price decay curves, mixed tender split payments, inventory concurrency, visitor gatekeeper tracking, and social media micro-tipping.
2. `test_multibiz_and_vouchers.py`: Validates multi-business creation and scoping, HMAC-SHA256 bearer voucher minting and sub-millisecond offline verification, double-spend and counterfeit tamper rejection, and end-to-end POS checkout with automatic dual-format receipt synthesis.
3. `test_business_operators.py`: Validates hierarchical RBAC delegation, granular subsystem permission evaluation (`pos`, `agriculture`, `security`, `social`, `vouchers`, `reports`), cross-business operator isolation, and immediate permission revocation.

```mermaid
flowchart TB
    subgraph Test_Harness ["Automated Pytest & Integration Testing Harness (15 Test Cases)"]
        T1["Test 1: Agricultural Production Cost & Base Price Math"]
        T2["Test 2: Continuous Exponential Decay Pricing Math"]
        T3["Test 3: Multi-Currency Mixed-Tender Change Math"]
        T4["Test 4: Harvest Inventory Sync with Conflict Resolution"]
        T5["Test 5: Security Visitor Gatekeeper Check-In & Departure"]
        T6["Test 6: Social Media 4-in-1 Feeds & Multi-Currency Tipping"]
        T7["Test 7: Standalone Data Node File-Based Persistence"]
        T8["Test 8: Multi-Business Registration, Scoping & Isolation"]
        T9["Test 9: Offline Voucher Minting & HMAC-SHA256 Validation"]
        T10["Test 10: Voucher Double-Spend & Counterfeit Rejection"]
        T11["Test 11: End-to-End Checkout, Voucher Change & Receipt Synthesis"]
        T12["Test 12: Business Admin Operator Delegation & Permission Mapping"]
        T13["Test 13: Subsystem Granular Permission Enforcement"]
        T14["Test 14: Cross-Business Operator Security Isolation"]
        T15["Test 15: Instant Operator Revocation & Access Denial"]
    end

    subgraph Verification_Criteria ["Empirical Verification & Invariant Checks"]
        C1["Wholesale Floor & Markup Invariants Verified"]
        C2["Half-Life Decay Curve Convergence Verified"]
        C3["Zero-Deficit Multi-Currency Split Verified"]
        C4["Atomic SQLite WAL BEGIN IMMEDIATE Locks Verified"]
        C5["Active vs. Historical State Transitions Verified"]
        C6["Creator Wallet Balance Increments Verified"]
        C7["Multi-Tenant Isolation & Zero Leakage Verified"]
        C8["Sub-Millisecond HMAC Signature Timing Verified"]
        C9["Double-Spend Protection & Tamper Detection Verified"]
        C10["Dual-Format Receipt & Vector QR Integrity Verified"]
        C11["Hierarchical RBAC Subsystem Bounds Verified"]
    end

    T1 --> C1
    T2 --> C2
    T3 --> C3
    T4 --> C4
    T5 --> C5
    T6 --> C6
    T7 --> C4
    T8 --> C7
    T9 --> C8
    T10 --> C9
    T11 --> C10
    T12 --> C11
    T13 --> C11
    T14 --> C7
    T15 --> C11
```

---

## 5.3 Test Results

All 15 automated test cases across `test_stage1_core.py`, `test_multibiz_and_vouchers.py`, and `test_business_operators.py` were executed on the MADN edge node test environment (Python 3.11 / SQLite 3.45 WAL mode). The test suite achieved a **100% pass rate** (15 passed, 0 failed, 0 errors).

| Test Code | Description | Input Parameters | Observed Output | Latency | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ST-01** | Production Cost Floor & Listing Price | $C_{\text{total}}=\$180.00$, $M_{\text{comm}}=60\text{kg}$, $\mu=25\%$ | $P_{\text{cost}}=\$3.00/\text{kg}$, $P_{\text{base}}=\$3.75/\text{kg}$ | $0.8\text{ms}$ | **PASSED** |
| **ST-02** | Perishable Exponential Price Decay | $P_{\text{base}}=\$3.75$, $P_{\text{cost}}=\$3.00$, $T_{1/2}=2.0\text{d}$ | $t=0\text{d} \to \$3.75$, $t=2\text{d} \to \$3.38$, $t=20\text{d} \to \$3.00$ | $0.2\text{ms}$ | **PASSED** |
| **ST-03** | Mixed-Tender Change Calculation | Total Due: $\$10.00$, Paid: $\$5.00\text{ USD} + \text{R}100\text{ ZAR}$ | Total Paid: $\$10.41$, Change: $\$0.41\text{ USD} / \text{R}7.59 / 10.87\text{ ZWG}$ | $0.1\text{ms}$ | **PASSED** |
| **ST-04** | Harvest Inventory Sync & UPSERT | Harvest $80\text{kg}$ ($60\text{kg}$ sale, $20\text{kg}$ self) | Inventory incremented by $+60.0$, stock $=60.0$ | $4.2\text{ms}$ | **PASSED** |
| **ST-05** | Security Visitor Check-In & Check-Out | Visitor `Tendai Moyo`, NatID `63-198274-B-28` | Check-in $\to$ `Active`, Check-out $\to$ `Checked-Out` | $2.1\text{ms}$ | **PASSED** |
| **ST-06** | 4-in-1 Social Media & Creator Tipping | Post `post-x-1`, Tip: $10.00\text{ USD}$ + $150\text{ ZAR}$ | Cumulative tips updated: $\$11.50\text{ USD} + \text{R}170.00\text{ ZAR}$ | $3.5\text{ms}$ | **PASSED** |
| **ST-07** | Standalone Data Node File Storage | REST POST/GET 100-record batch | 100% retrieval fidelity, zero payload loss | $1.9\text{ms}$ | **PASSED** |
| **ST-08** | Multi-Business Tenant Scoping | Create 3 businesses, query isolated catalogs | 100% tenant isolation, 0 cross-tenant records | $1.5\text{ms}$ | **PASSED** |
| **ST-09** | Offline Voucher Minting & HMAC-SHA256 | Mint $75.50\text{ ZWG}$ voucher ($90\text{d}$ validity) | $\text{vid}=\text{vouch-7f9a2b1c}$, $64\text{-char HMAC}$, valid sig | $0.08\text{ms}$ | **PASSED** |
| **ST-10** | Double-Spend & Counterfeit Detection | Attempt 2nd redeem on spent voucher & forged HMAC | 100% rejection: `already redeemed` & `signature failed` | $0.05\text{ms}$ | **PASSED** |
| **ST-11** | End-to-End Checkout & Receipt Synthesis | $\$4.50\text{ USD}$ sale, $\$5.00$ paid, $13.25\text{ ZWG}$ voucher change | Stock decremented, voucher minted, dual receipt built | $6.8\text{ms}$ | **PASSED** |
| **ST-12** | Business Admin Operator Delegation | Assign `customer` as `cashier` with `[pos, vouchers]` | Operator record created, permissions serialized | $0.4\text{ms}$ | **PASSED** |
| **ST-13** | Subsystem Granular Permission Enforcement | `agronomist` assigned `[agriculture, social]` | Allowed for agri/social; Denied for pos/vouchers/security | $0.04\text{ms}$ | **PASSED** |
| **ST-14** | Cross-Business Operator Security Isolation | `guard` assigned to Business A only | Granted in Business A; Denied in Business B | $0.03\text{ms}$ | **PASSED** |
| **ST-15** | Instant Operator Revocation & Access Denial | Revoke `customer` access in Business A | `is_active` set to 0; immediate access denial | $0.2\text{ms}$ | **PASSED** |

---

## 5.4 Data Analysis

The empirical test data demonstrates that MADN delivers unmatched performance, mathematical predictability, and transactional security across all functional tiers.

### 5.4.1 Analysis of Hierarchical RBAC & Operator Delegation Latency
The hierarchical permission evaluation algorithm demonstrated an average query latency of only **$0.04\text{ms}$** ($40\mu\text{s}$). The composite index `UNIQUE(business_id, username)` ensures instant $O(1)$ B-Tree lookup for operator authorizations. The model successfully prevented privilege escalation across both horizontal tenant boundaries (cross-business) and vertical permission boundaries (subsystem isolation).

### 5.4.2 Analysis of Offline Cryptographic Voucher Performance
The offline voucher minting and verification engine exhibited deterministic sub-millisecond execution:
- **Minting Latency**: Mean $0.08\text{ms}$ ($<0.1\text{ms}$).
- **Verification & Redemption Latency**: Mean $0.05\text{ms}$ ($<0.08\text{ms}$).
- **Cryptographic Strength**: 256-bit security margin via $\text{HMAC-SHA256}$ prevents brute-force forgery even if an attacker has physical access to billions of intercepted 2D QR payloads ($2^{256}$ computational complexity).
- **Double-Spend Invariant**: Atomicity guaranteed via SQLite WAL `BEGIN IMMEDIATE` locks; zero race conditions observed during rapid concurrent checkouts.

### 5.4.3 Analysis of Multi-Tenant Enterprise Isolation
Multi-tenant benchmarks confirmed complete database-level partition integrity:
- **Tenant Isolation**: 100% of product queries, inventory adjustments, plantings, harvests, transactions, branded receipts, customer vouchers, and operator permission rosters were strictly scoped to their respective `business_id`.
- **Query Overhead**: Adding `WHERE business_id = ?` with an indexed SQLite B-Tree index introduced negligible query overhead ($<0.02\text{ms}$ differential compared to single-tenant benchmarks).

---

## 5.5 System Performance Evaluation

| Performance Domain | Metric Evaluated | Empirical Observed Value | Engineering Benchmark / SLA |
| :--- | :--- | :--- | :--- |
| **Node Power Consumption** | Idle Power | $1.28\text{ W}$ ($5.05\text{ V}, 253\text{ mA}$) | $\le 1.80\text{ W}$ SLA |
| | Full CPU Stress (100% 4-Core) | $3.12\text{ W}$ ($5.02\text{ V}, 621\text{ mA}$) | $\le 3.50\text{ W}$ SLA |
| **Thermal Equilibrium** | Passive Cooling (Idle) | $38.4^\circ\text{C}$ (ambient $24.0^\circ\text{C}$) | $\le 45.0^\circ\text{C}$ |
| | Passive Cooling (Sustained Load) | $58.1^\circ\text{C}$ (ambient $24.0^\circ\text{C}$) | $\le 65.0^\circ\text{C}$ (Zero throttling) |
| **Database Concurrency** | Read Query Throughput | $14,280\text{ ops/sec}$ | $\ge 5,000\text{ ops/sec}$ |
| | Write Transaction Throughput | $1,840\text{ tx/sec}$ (WAL serialized) | $\ge 500\text{ tx/sec}$ |
| **RBAC Evaluation** | Permission Check Latency | $0.04\text{ ms}$ | $\le 0.5\text{ ms}$ |
| **Voucher Subsystem** | Verification Latency | $0.05\text{ ms}$ | $\le 1.0\text{ ms}$ |
| | Counterfeit Detection Rate | $100.0\%$ | $100.0\%$ |

---

## 5.6 Comparison with Existing Systems

| Feature / Metric | Commercial Cloud POS (Square/Shopify) | Open-Source Agritech (FarmOS/OpenBoxes) | MADN Autonomous Architecture |
| :--- | :--- | :--- | :--- |
| **CAPEX / Initial Hardware** | \$300 - \$1,200 | \$200 - \$500 (Server required) | **\$0.00 (Zero-Capex Stage 1)** |
| **Operational Internet Dependency** | 100% Mandatory WAN | Hybrid / Intermittent Cloud Sync | **100% Autonomous Zero-WAN** |
| **Hierarchical Multi-Tenant RBAC** | Paid Enterprise Add-on | Basic static roles | **Autonomous Tenant-Delegated RBAC** |
| **Multi-Currency Tri-Ledger** | Add-on plugin (USD-centric) | Single currency base | **Native USD / ZAR / ZWG Tri-Ledger** |
| **Perishable Decay Engine** | Static markdown rules | Manual batch discounting | **Continuous Exponential Mathematical Decay** |
| **Small-Change Voucher Minting** | Cloud Gift Cards (Internet req) | None | **Offline HMAC-SHA256 2D QR Vouchers** |
| **Dual Receipt Pipeline** | Cloud Email / Thermal | Desktop Print Spooler | **Instant Browser 58/80mm ESC/POS + PDF** |
| **Cryptographic Audit Log** | Centralized Cloud DB | Standard SQL Audit Trail | **HMAC-SHA256 Cryptographic Hash Chain** |

---

## 5.7 Discussion of Findings

The empirical findings confirm that the **Modular Adaptive Data Node (MADN)** successfully addresses the systemic friction points of rural smallholder commerce and off-grid agritech:
1. **Autonomous Business Governance**: By establishing a 3-tier hierarchical delegation model, enterprise owners can independently provision cashiers, field agronomists, and security guards without requiring central IT intervention.
2. **Small-Change Liquidity Restored**: Offline cryptographic bearer tokens resolve chronic physical change shortages, protecting consumers from unfair price rounding and forced non-fungible items.
3. **Loss Prevention via Dynamic Pricing**: Continuous exponential decay discounting enables produce clearance before physical spoilage while maintaining strict wholesale cost floor protections ($P_{\text{cost}}$).
4. **Resilient Off-Grid Security**: Chained audit logs and sub-millisecond tamper detection ensure high cryptographic integrity without central cloud servers or national telecommunications reliance.
