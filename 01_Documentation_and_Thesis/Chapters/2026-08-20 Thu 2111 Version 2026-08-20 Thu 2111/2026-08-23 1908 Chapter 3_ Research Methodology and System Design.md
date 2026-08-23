# CHAPTER 3: RESEARCH METHODOLOGY AND SYSTEM DESIGN

## 3.1 Introduction
This chapter details the research methodology, architectural specifications, and structural system design governing the development of the **Modular Adaptive Data Node (MAD-Node) for Dynamic Value Systems**. The system design translates the conceptual 4-Node Taxonomy (Operator Nodes, Vault Nodes, Data Nodes, Cyber-Physical Nodes) and Phased Resource-Bootstrapping Model (*Ukunciphisa*) into rigorous engineering specifications. 

This chapter outlines the Design Science Research (DSR) methodology, defines comprehensive functional and non-functional requirements for Stage 1 (immediate software foundation) and Stage 2 (scale-up hardware automation), presents formal discovery protocols and hardware pin mappings, details the database schemas and Role-Based Access Control (RBAC) matrix (including multi-tenant operator delegation, customer digital banking, and personal receipt vaulting), and establishes the experimental testing and ethical frameworks guiding prototype validation.

---

## 3.2 Research Design
The study follows the **Design Science Research Methodology (DSRM)** (Peffers et al., 2007), an established framework for creating and evaluating novel IT artifacts intended to solve identified organizational and infrastructural problems. DSRM is particularly suited for the MAD-Node as it emphasizes iterative prototyping, rigorous empirical evaluation, and pragmatic utility in resource-constrained environments.

```mermaid
flowchart LR
    P1["1. Problem Identification & Motivation"] --> P2["2. Objectives of a Solution"]
    P2 --> P3["3. Architectural Design & Artifact Development"]
    P3 --> P4["4. Empirical Demonstration & Benchmarking"]
    P4 --> P5["5. Evaluation & Evolution"]
    P5 -.->|Iterative Refinement| P3
```

---

## 3.3 System Requirements

### 3.3.1 Functional Requirements Matrix
* **FR1: Decentralized Tri-Node Discovery & Partition Tolerance**:
  - Independent execution of Operator Nodes (Browser :8000), Data Nodes (Edge daemon :8002), and Vault Nodes (Master Coordinator :8000).
  - Autonomous periodic UDP multicast heartbeats (`224.0.0.251:8001`) with dynamic zero-config subnet routing.
* **FR2: Multi-Tenant RBAC & Business Operator Access Delegation**:
  - Multi-business tenancy isolation across distinct stores (*Green Valley Organics*, *Khumalo Millers*, *Matopos Dairy*).
  - Granular subsystem access permissions (`pos`, `inventory`, `agriculture`, `security`, `social`, `reports`, `admin`) managed via `business_operators`.
* **FR3: Customer Digital Banking & Multi-Currency Tri-Ledger**:
  - Sovereign account provisioning (`ACC-2026-XXXXXX`) supporting multi-currency balances (USD, ZAR, ZWG).
  - Atomic double-entry bookkeeping in `wallet_ledger` signed with node HMAC-SHA256 signatures.
  - Peer-to-peer (P2P) transfers, kiosk cash deposits, and direct wallet debit tenders during POS checkouts.
* **FR4: Personal Digital Receipt Vault & Offline QR Vouchers**:
  - Automatic permanent archival of itemized digital receipts with SHA-256 integrity hash stamps.
  - Offline bearer voucher minting and instant single-use conversion to liquid wallet balance.
  - Dual-format receipt synthesis: HTML5 canvas QR slips and downloadable PDF invoices.
* **FR5: Continuous Exponential Decay Pricing & Mixed-Tender Change Reconciliation**:
  - Dynamic perishable pricing: \(P(t) = P_{\text{cost}} + (P_{\text{base}} - P_{\text{cost}}) \cdot e^{-\lambda t}\).
  - Tri-currency split payment tender processing with exact multi-currency change calculation.
* **FR6: Agricultural Lifecycle Accounting & Security Gatekeeping**:
  - Itemized cost tracking (\(C_{\text{seeds}}, C_{\text{fert}}, C_{\text{water}}, C_{\text{labor}}\)) and automatic cost floor \(P_{\text{cost}}\) derivation.
  - Real-time visitor access registry with departure timestamps and tamper-evident audit logging.

---

## 3.4 System Design & Architectural Decomposition

### 3.4.1 Tri-Node Architectural Decomposition
The architecture decouples responsibilities across three operational nodes:

```mermaid
graph TD
    subgraph "Operator Node (Browser / Mobile POS)"
        ON[Web Client UI :8000]
        POS[Touch POS Register]
        WAL[Customer Digital Banking]
        RCV[Personal Receipt Vault]
    end

    subgraph "Data Node (Edge Cache Daemon :8002)"
        DN[Storage Manager]
        KV[(SQLite WAL kv_records)]
        BEACON[UDP Multicast Beacon 224.0.0.251:8001]
    end

    subgraph "Vault Node (Master Coordinator :8000)"
        VN[FastAPI Engine]
        AUTH[scrypt & TOTP Security]
        RBAC[Multi-Tenant Operator RBAC]
        DB[(Master SQLite WAL Tri-Ledger)]
        HMAC[HMAC-SHA256 Bearer Signer]
    end

    ON -->|REST / HTTPS| VN
    ON -.->|Local Edge Cache| DN
    DN <-->|Mesh Sync & Heartbeats| VN
```

### 3.4.2 Mathematical Formalisms
1. **Continuous Perishable Decay Pricing**:
   \[
   P(t) = P_{\text{cost}} + (P_{\text{base}} - P_{\text{cost}}) \cdot e^{-\lambda t}, \quad \lambda = \frac{\ln(2)}{T_{\text{half\_life}}}
   \]
2. **Tri-Currency Tender Split Valuation**:
   \[
   V_{\text{paid}} = T_{\text{USD}} + \frac{T_{\text{ZAR}}}{\text{rate}_{\text{ZAR}}} + \frac{T_{\text{ZWG}}}{\text{rate}_{\text{ZWG}}}
   \]
3. **Double-Entry Ledger HMAC Audit Signature**:
   \[
   \sigma_{\text{ledger}} = \text{HMAC-SHA256}\Big(K_{\text{vault}}, \; \text{tx\_id} \parallel \text{acc\_num} \parallel \text{type} \parallel \text{curr} \parallel \text{amount} \parallel \text{bal\_after} \parallel t_{\text{utc}}\Big)
   \]
4. **Receipt Cryptographic Audit Hash**:
   \[
   H_{\text{receipt}} = \text{SHA-256}\Big(\text{receipt\_json}\Big)
   \]

---

## 3.5 Database Schemas & Storage Design
The master database (`database.db`) enforces relational integrity via SQLite Write-Ahead Logging (WAL) and strict foreign keys across 15 normalized tables:
- `users`: User profiles, scrypt password hashes, TOTP secrets, roles, and PINs.
- `businesses`: Multi-business entities with address, tax ID, and footer notes.
- `business_operators`: Composite multi-tenant RBAC operator permissions.
- `wallets`: Sovereign multi-currency accounts (`balance_usd`, `balance_zar`, `balance_zwg`).
- `wallet_ledger`: Immutable signed double-entry account ledger records.
- `vouchers`: Offline bearer voucher records with cryptographic HMAC signatures.
- `customer_receipts`: Permanent personal receipt vault records with SHA-256 audit hashes.
- `inventory`, `transactions`, `transaction_items`, `transaction_tenders`, `agri_plantings`, `agri_production_costs`, `agri_harvests`, `security_visitor_logs`, `social_posts`.

---

## 3.6 Testing & Evaluation Methodology
The prototype validation employs automated regression suites (`pytest`) and physical test harnesses to verify concurrency locks (`BEGIN IMMEDIATE`), sub-millisecond cryptographic hash performance, and zero-loss multi-currency ledger reconciliations under disconnected operation.
