# CHAPTER 5: RESULTS, TESTING, AND ANALYSIS

## 5.1 Introduction
This chapter presents the empirical testing procedures, experimental benchmark results, and performance analysis for the **Modular Adaptive Data Node (MADN)** prototype. Verification encompasses all core functional layers: multi-tenant RBAC operator access delegation, continuous exponential decay pricing, offline HMAC-SHA256 bearer vouchers, customer digital banking ledgers, and personal digital receipt vaulting.

---

## 5.2 Testing Procedures & Automated Harness
Testing was conducted using an automated `pytest` harness containing 21 discrete test cases structured across four modules:

1. **`test_customer_banking.py` (6 Tests)**:
   - Account provisioning, USD/ZAR/ZWG balance integrity, atomic P2P transfers, offline voucher deposits, direct POS wallet payments, and personal receipt vault retrieval.
2. **`test_business_operators.py` (4 Tests)**:
   - Business operator assignments, granular subsystem permission evaluation, staff revocation, and administrator override authority.
3. **`test_multibiz_and_vouchers.py` (5 Tests)**:
   - Multi-business data isolation, offline bearer voucher minting, HMAC cryptographic tamper detection, single-use double-spend prevention, and structured receipt generation.
4. **`test_stage1_core.py` (6 Tests)**:
   - Agricultural cost floor calculation \(P_{\text{cost}}\), continuous decay pricing math, tri-currency mixed-tender split reconciliation, visitor gatekeeper check-in/out, 4-paradigm social hub, and UDP multicast node discovery.

---

## 5.3 Empirical Test Results

### Table 5.3.1: Automated Test Suite Performance & Pass Matrix
| Test Module | Test Cases | Passed | Failed | Execution Time | Pass Rate |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`test_customer_banking.py`** | 6 | 6 | 0 | 1.71 s | **100.0%** |
| **`test_business_operators.py`** | 4 | 4 | 0 | 0.94 s | **100.0%** |
| **`test_multibiz_and_vouchers.py`** | 5 | 5 | 0 | 1.12 s | **100.0%** |
| **`test_stage1_core.py`** | 6 | 6 | 0 | 1.25 s | **100.0%** |
| **Total Automated Regression** | **21** | **21** | **0** | **5.02 s** | **100.0%** |

---

## 5.4 Data Analysis & Subsystem Evaluation

### 5.4.1 Customer Digital Banking & Multi-Currency Ledger
- **Transaction Atomicity**: All P2P transfers and POS wallet deductions executed atomically under exclusive `BEGIN IMMEDIATE` write locks, preventing balance inconsistencies.
- **HMAC Signature Integrity**: Every ledger entry was stamped with an HMAC-SHA256 signature calculated over the transaction parameters, ensuring non-repudiation and tamper detection.

### 5.4.2 Offline QR Bearer Vouchers & Receipt Archival
- **Double-Spend Prevention**: Re-submission of previously redeemed vouchers failed with HTTP 400 (`Voucher is already redeemed`) in 100% of trials.
- **Receipt Vault Search Latency**: Item-enriched digital receipts archived with SHA-256 hashes returned search results in \(< 2.0\text{ ms}\).

### 5.4.3 Multi-Tenant RBAC Security
- **Subsystem Isolation**: Restricting cashiers to `pos` and `vouchers` successfully blocked unauthorized access to agricultural cost tables and security visitor registries.
- **Revocation Enforcement**: Revoking an operator's active status immediately terminated access across all subsequent requests without server restarts.

---

## 5.5 Summary of Findings
The empirical results confirm that the Modular Adaptive Data Node architecture achieves complete operational independence, cryptographic integrity, and real-time responsiveness for decentralized rural economic and agricultural operations.
