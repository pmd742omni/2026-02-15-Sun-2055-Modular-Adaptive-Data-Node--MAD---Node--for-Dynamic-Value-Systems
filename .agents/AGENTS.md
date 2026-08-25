# Project Rules & Customizations

## Progress Tracking Rule ("Document Now")
Whenever the user states **"document now"**, **"document progress"**, or requests a new checkpoint:
1. Refer to and follow the instructions in the `document-now` skill ([SKILL.md](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/.agents/skills/document-now/SKILL.md)).
2. Synchronize `Applications/Web App/SYSTEM_INTERNALS.md`, `Applications/Web App/USER_MANUAL.md`, and `Applications/Web App/PROJECT_CHECKLIST.md` with relative destination paths (`./`, `../`, `../../`).
3. Synthesize progress, create the progress tracking file under `progress tracking/YYYY-MM-DD_HHMM_Description.md` following the required schema (including Ndebele version codename, 10-year-old child target explanations and next steps, and developer attributions).
4. Stage all changes (`git add .`) and execute a git commit with the message format: `YYYY-MM-DD Day HHMM: [Title] ([Codename] [Version])`.

## System Internals Documentation Rule ("System Internals")
Whenever the user states **"update system internals"**, **"generate internals doc"**, or requests deep technical reference documentation:
1. Refer to and follow the instructions in the `system-internals-doc` skill ([SKILL.md](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/.agents/skills/system-internals-doc/SKILL.md)).
2. Audit the system architecture, database locks, scrypt/TOTP security parameters, Liang-Barsky ray-tracing, Log-distance path loss, A* mesh routing, multi-currency tri-ledger, and continuous exponential decay math.
3. Update `Applications/Web App/SYSTEM_INTERNALS.md` with low-level technical reference details, Mermaid diagrams, and LaTeX equations.

## Chapter Development Rule ("Chapter Development" / "Develop Chapter")
Whenever the user states **"develop chapter"**, **"write chapter"**, **"create chapter"**, or requests development of a thesis chapter:
1. Refer to and follow the instructions in the `chapter-development` skill ([SKILL.md](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/.agents/skills/chapter-development/SKILL.md)).
2. Acquire the authoritative local machine system timestamp string (`YYYY-MM-DD HHMM`) by running `python .agents/skills/chapter-development/scripts/get_chapter_timestamp.py` dynamically at runtime.
3. Audit codebase, backend test results, system internals, math models, and hardware benchmarks.
4. Output individual sub-section files (`YYYY-MM-DD HHMM 5.X Section Title.md`) and a unified compiled chapter file (`YYYY-MM-DD HHMM Chapter X_ Title.md`) into `01_Documentation_and_Thesis/Chapters/`.

## Tri-Node Architecture & Composable Dynamic Value Systems Standard
1. **Operator Node**: Zero-installation web client executing in modern browsers (:8000). Handles dynamic pricing views, touch POS, peer-to-peer transfers, and live receipt vault lookups.
2. **Data Node**: Standalone storage, discovery, and global currency collector service (:8002) broadcasting periodic UDP multicast heartbeats (224.0.0.251:8001). Exposes remote lifecycle endpoints (`/api/node/activate`, `/api/node/deactivate`) and reference catalog endpoints (`/api/reference/currencies`).
3. **Vault Node**: Security coordinator and extensible multi-currency tri-ledger (:8000) enforcing scrypt/TOTP credentials, SQLite WAL concurrency (`BEGIN IMMEDIATE`), HMAC-SHA256 bearer signatures, world currency collision-prevention, and self-replicating portable node packaging (`node_generator.py`).
4. **Dynamic Extensible Multi-Currency Engine**:
   - Official ISO 4217 standard alignment: Zimbabwe Gold (`ZWG`, name: Zimbabwe Gold (ZiG), symbol: `ZiG`, type: `gold_backed`).
   - Global World Currency & Cryptocurrency Registry (170+ ISO fiats + 50+ cryptos) with continuous online collection and offline air-gapped fallback.
   - Real-time multi-tier collision validation (`OFFICIAL_ISO_FIAT`, `MAJOR_CRYPTO`, `EXISTING_ACTIVE_CURRENCY`, `UNIQUE_AVAILABLE`) to protect financial namespaces.
   - Zero-seed balances rule: All accounts initialize strictly with `0.00` balances.
5. **Portable Bootstrapper (`Applications/start.py`)**: Zero-config launcher auto-resolving Python dependencies, supervising multi-node child processes, and providing an interactive terminal dashboard.
6. **Automated Verification Matrix**: Always execute the full 27-test suite (`pytest test_portable_node_generation.py test_customer_banking.py test_business_operators.py test_multibiz_and_vouchers.py test_stage1_core.py -v`) before creating documentation or thesis updates.



