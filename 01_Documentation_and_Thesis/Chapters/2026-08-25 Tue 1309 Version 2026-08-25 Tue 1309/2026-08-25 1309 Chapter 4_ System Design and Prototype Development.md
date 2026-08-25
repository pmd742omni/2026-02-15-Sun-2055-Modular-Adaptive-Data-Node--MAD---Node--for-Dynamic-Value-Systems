# CHAPTER 4: SYSTEM DESIGN AND PROTOTYPE DEVELOPMENT

## 4.1 Introduction & Architectural Implementation
Chapter 4 details the software engineering and architectural implementation of the **Modular Adaptive Data Node (MADN)** prototype. Built on a clean Python / FastAPI / SQLite WAL backend and a responsive glassmorphic Single Page Application frontend, the prototype unifies offline multi-tenant point-of-sale operations, dynamic perishable decay valuation, customer digital banking, personal receipt vaulting, and automated portable node generation.

```mermaid
flowchart TD
    subgraph OperatorNode ["Operator Node (Client Web SPA :8000)"]
        SPA["HTML5 / Glassmorphic UI"]
        POS_MOD["POS Register & Tender Split"]
        BANK_MOD["Customer Digital Wallet"]
        VAULT_MOD["Personal Receipt Vault"]
        LIFECYCLE_UI["Node Lifecycle Control Center"]
    end

    subgraph DataNode ["Data Node (Edge Cache Daemon :8002)"]
        STORAGE["Standalone Storage Manager"]
        KV_DB[("SQLite WAL kv_records")]
        UDP_BEACON["UDP Multicast Engine :8001"]
        LC_ENDPOINT["Lifecycle Endpoints (Active / Standby)"]
    end

    subgraph VaultNode ["Vault Node (Master Coordinator :8000)"]
        FASTAPI["FastAPI REST Gateway"]
        AUTH_SEC["scrypt & TOTP Security"]
        TENANCY["Multi-Tenant Business RBAC"]
        TRI_LEDGER["Multi-Currency Tri-Ledger"]
        SIGNER_ENG["HMAC-SHA256 Signer"]
        NODE_GEN["Portable Node Generator Engine"]
        CORE_DB[("Master SQLite WAL Database")]
    end

    SPA -->|HTTPS REST| FASTAPI
    POS_MOD -->|Direct Wallet Payment| TRI_LEDGER
    BANK_MOD -->|P2P / Top-up / Deposit| TRI_LEDGER
    VAULT_MOD -->|Archived Receipt Lookup| CORE_DB
    LIFECYCLE_UI -->|Remote Toggle| LC_ENDPOINT
    NODE_GEN -->|Generates Standalone Pack| DataNode
    STORAGE <-->|Mesh Sync| CORE_DB
    UDP_BEACON -.->|Periodic Heartbeat| SPA
```

---

## 4.2 Portable Multi-Node Bootstrapper & Self-Replication
The prototype introduces `Applications/start.py`, a zero-dependency launcher providing preflight validation, dependency resolution, and multi-process coordination for Vault Coordinator (`:8000`) and Data Nodes (`:8002`).

The Vault Node exposes `/api/cluster/nodes/generate-portable`, allowing operators to export complete standalone node bundles containing their own `start.py`, FastAPI backend, and embedded glassmorphic web dashboard.

---

## 4.3 Remote Lifecycle Control & Maintenance Mode
Data Nodes expose `/api/node/activate` and `/api/node/deactivate`. When deactivated, write transactions are blocked with HTTP 503 Maintenance Mode and beacon broadcasts are suspended to conserve mesh bandwidth.

---

## 4.4 Customer Digital Banking & Personal Receipt Vault
Every user account receives a sovereign multi-currency digital wallet (`ACC-2026-XXXXXX`) tracking USD, ZAR, and ZWG with atomic double-entry bookkeeping in `wallet_ledger`. Itemized receipts are archived to `customer_receipts` with SHA-256 integrity hashes upon POS checkout completion.
