# Project Rules & Customizations

## 1. Progress Tracking Rule ("Document Now")
Whenever the user states **"document now"**, **"document progress"**, or requests a new checkpoint:
1. Refer to and follow the instructions in the `document-now` skill ([SKILL.md](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/.agents/skills/document-now/SKILL.md)).
2. Synchronize `Applications/Web App/SYSTEM_INTERNALS.md`, `Applications/Web App/USER_MANUAL.md`, and `Applications/Web App/PROJECT_CHECKLIST.md` with relative destination paths (`./`, `../`, `../../`).
3. Synthesize progress, dynamically assign an authentic, culturally rich Ndebele version codename via the LLM (validated for uniqueness), and create `progress tracking/YYYY-MM-DD_HHMM_Description.md` following the required schema (including 10-year-old child target explanations, child-friendly next steps, and developer attributions).
4. Stage all changes (`git add .`) and execute a git commit with the message format: `YYYY-MM-DD Day HHMM: [Title] ([Codename] [Version])`.

## 2. LLM Thesis Chapter Development Rule ("Chapter Development" / "Develop Chapter")
Whenever the user states **"develop chapter"**, **"write chapter"**, **"create chapter"**, or requests academic thesis writing:
1. Refer to and follow the instructions in the `chapter-development` skill ([SKILL.md](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/.agents/skills/chapter-development/SKILL.md)).
2. **LLM Authorship Mandate**: All chapters, literature reviews, theoretical foundations, system design analyses, and empirical benchmark evaluations are authored directly by the LLM (Antigravity) using scholarly prose, KaTeX mathematics, and empirical evidence.
3. Acquire the authoritative local machine timestamp string (`YYYY-MM-DD HHMM`) via `python .agents/skills/chapter-development/scripts/get_chapter_timestamp.py`.
4. Output individual sub-section files (`YYYY-MM-DD HHMM 5.X Section Title.md`) and unified compiled chapter files (`YYYY-MM-DD HHMM Chapter X_ Title.md`) into `01_Documentation_and_Thesis/Chapters/`.

## 3. Universal Milestone Release Rule ("Milestone Release" / "Sync Chapters and Document")
Whenever the user states **"milestone release"**, **"sync chapters and document"**, or requests a new feature release milestone:
1. Refer to and follow the instructions in the `dynamic-value-milestone` skill ([SKILL.md](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/.agents/skills/dynamic-value-milestone/SKILL.md)).
2. Execute the automated verification suite (`pytest -v`).
3. Dynamically generate and synchronize updated sub-section and compiled chapter files into a newly created versioned directory `01_Documentation_and_Thesis/Chapters/YYYY-MM-DD Day HHMM Version YYYY-MM-DD Day HHMM/`.
4. Trigger `.agents` optimization and the `document-now` progress tracking skill to register the new version and commit.

## 4. Adaptive System Evolution Rule ("Track Evolution" / "Suggest Adjustments")
Whenever the user states **"track evolution"**, **"suggest adjustments"**, **"analyze architecture"**, or **"optimize madn"**:
1. Refer to and follow the instructions in the `madn-evolution-tracker` skill ([SKILL.md](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/.agents/skills/madn-evolution-tracker/SKILL.md)).
2. Intelligently inspect git history and architectural changes over time across frontend, backend, Data Node, and Vault Node.
3. Deliver a structured Architectural Diagnostic & Systematic Adjustment Plan with concrete, actionable enhancements.

## 5. Intelligent Feature Scaffolding Rule ("Scaffold Feature" / "Create Subsystem")
Whenever the user states **"scaffold feature [name]"**, **"create subsystem [name]"**, or requests implementing a new modular component:
1. Refer to and follow the instructions in the `madn-feature-scaffold` skill ([SKILL.md](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/.agents/skills/madn-feature-scaffold/SKILL.md)).
2. Scaffold across the 5 architectural tiers: SQLite WAL schema, FastAPI REST endpoints, Data Node sync, glassmorphic Operator UI, and automated pytest suite.

## 6. Automated System Verification Rule ("Verify System" / "Health Check")
Whenever the user states **"verify system"**, **"health check"**, or **"audit security"**:
1. Refer to and follow the instructions in the `madn-system-verifier` skill ([SKILL.md](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/.agents/skills/madn-system-verifier/SKILL.md)).
2. Audit scrypt/TOTP security parameters, SQLite WAL locks, zero-seed balances, and run full test suites.

## 7. System Internals Documentation Rule ("System Internals")
Whenever the user states **"update system internals"**, **"generate internals doc"**, or requests deep technical reference documentation:
1. Refer to and follow the instructions in the `system-internals-doc` skill ([SKILL.md](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/.agents/skills/system-internals-doc/SKILL.md)).
2. Update `Applications/Web App/SYSTEM_INTERNALS.md` with low-level technical reference details, Mermaid diagrams, and LaTeX equations.

---

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
6. **Automated Verification Matrix**: Always execute the full test suite (`pytest -v`) before creating documentation or thesis updates.
