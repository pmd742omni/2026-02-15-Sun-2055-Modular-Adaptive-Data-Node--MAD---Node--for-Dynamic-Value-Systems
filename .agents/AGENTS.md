# Project Rules & Customizations

## 1. Progress Tracking Rule ("Document Now")
Whenever the user states **"document now"**, **"document progress"**, or requests a new checkpoint:
1. Refer to and follow the instructions in the `document-now` skill ([SKILL.md](./skills/document-now/SKILL.md)).
2. Synchronize `../Applications/Web App/SYSTEM_INTERNALS.md`, `../Applications/Web App/USER_MANUAL.md`, and `../Applications/Web App/PROJECT_CHECKLIST.md` with relative destination paths (`./`, `../`, `../../`).
3. Synthesize progress, dynamically assign an authentic, culturally rich Ndebele version codename via the LLM (validated for uniqueness), and create `../progress tracking/YYYY-MM-DD_HHMM_Description.md` following the required schema (including 10-year-old child target explanations, child-friendly next steps, and developer attributions).
4. Stage all changes (`git add .`) and execute a git commit with the message format: `YYYY-MM-DD Day HHMM: [Title] ([Codename] [Version])`.

## 2. LLM Thesis Chapter Development Rule ("Chapter Development" / "Develop Chapter")
Whenever the user states **"develop chapter"**, **"write chapter"**, **"create chapter"**, or requests academic thesis writing:
1. Refer to and follow the instructions in the `chapter-development` skill ([SKILL.md](./skills/chapter-development/SKILL.md)).
2. **LLM Authorship Mandate**: All chapters, literature reviews, theoretical foundations, system design analyses, and empirical benchmark evaluations are authored directly by the LLM (Antigravity) using scholarly prose, KaTeX mathematics, and empirical evidence.
3. Acquire the authoritative local machine timestamp string (`YYYY-MM-DD HHMM` and `YYYY-MM-DD Day HHMM`) via `python .agents/skills/chapter-development/scripts/get_chapter_timestamp.py`.
4. **Iterative Edition Build-Up & Changelog Mandate**:
   - Each new edition of thesis chapters MUST be generated into a dedicated timestamped edition directory: `../01_Documentation_and_Thesis/Chapters/YYYY-MM-DD Day HHMM Version YYYY-MM-DD Day HHMM/`.
   - Every new edition is built up incrementally from previous editions, incorporating the latest system architecture, benchmarks, and mathematical models.
   - Every edition directory MUST contain an **`EDITION_CHANGELOG.md`** file systematically documenting what changed, evolved, and was expanded from previous editions.
5. Output individual sub-section files (`YYYY-MM-DD HHMM X.Y Section Title.md`), unified compiled chapter files (`YYYY-MM-DD HHMM Chapter X_ Title.md`), and the edition changelog into the new edition folder.

## 3. Universal Milestone Release Rule ("Milestone Release" / "Sync Chapters and Document")
Whenever the user states **"milestone release"**, **"sync chapters and document"**, or requests a new feature release milestone:
1. Refer to and follow the instructions in the `dynamic-value-milestone` skill ([SKILL.md](./skills/dynamic-value-milestone/SKILL.md)).
2. Execute the automated verification suite (`pytest -v`).
3. Dynamically generate and synchronize updated sub-section and compiled chapter files into a newly created versioned directory `../01_Documentation_and_Thesis/Chapters/YYYY-MM-DD Day HHMM Version YYYY-MM-DD Day HHMM/`.
4. Include `EDITION_CHANGELOG.md` detailing all architectural enhancements, algorithmic refinements, and benchmark improvements.
5. Trigger `.agents` optimization and the `document-now` progress tracking skill to register the new version and commit.

## 4. Adaptive System Evolution Rule ("Track Evolution" / "Suggest Adjustments")
Whenever the user states **"track evolution"**, **"suggest adjustments"**, **"analyze architecture"**, or **"optimize madn"**:
1. Refer to and follow the instructions in the `madn-evolution-tracker` skill ([SKILL.md](./skills/madn-evolution-tracker/SKILL.md)).
2. Intelligently inspect git history and architectural changes over time across frontend, backend, Data Node, and Vault Node.
3. Deliver a structured Architectural Diagnostic & Systematic Adjustment Plan with concrete, actionable enhancements.

## 5. Intelligent Feature Scaffolding Rule ("Scaffold Feature" / "Create Subsystem")
Whenever the user states **"scaffold feature [name]"**, **"create subsystem [name]"**, or requests implementing a new modular component:
1. Refer to and follow the instructions in the `madn-feature-scaffold` skill ([SKILL.md](./skills/madn-feature-scaffold/SKILL.md)).
2. Scaffold across the 5 architectural tiers: SQLite WAL schema, FastAPI REST endpoints, Data Node sync, Sovereign Obsidian Glassmorphic UI component, and automated pytest suite.

## 6. Automated System Verification Rule ("Verify System" / "Health Check")
Whenever the user states **"verify system"**, **"health check"**, or **"audit security"**:
1. Refer to and follow the instructions in the `madn-system-verifier` skill ([SKILL.md](./skills/madn-system-verifier/SKILL.md)).
2. Audit scrypt/TOTP security parameters, SQLite WAL locks, zero-seed balances, and run full test suites.

## 7. System Internals Documentation Rule ("System Internals")
Whenever the user states **"update system internals"**, **"generate internals doc"**, or requests deep technical reference documentation:
1. Refer to and follow the instructions in the `system-internals-doc` skill ([SKILL.md](./skills/system-internals-doc/SKILL.md)).
2. Update `../Applications/Web App/SYSTEM_INTERNALS.md` with low-level technical reference details, Mermaid diagrams, and LaTeX equations.

## 8. Dynamic Progressive Disclosure & Intuitive UX Rule
Whenever developing frontend navigation or subview controllers:
1. Subnav options and containers must dynamically evaluate live data preconditions via `getSubNavItems(mainTarget)`:
   - **Business & POS**: Gated strictly behind $N_{\text{biz}} \ge 1$ (Store Setup) and $N_{\text{products}} \ge 1$ (POS, Marketplace, and Analytics appear only when products exist).
   - **Precision Agriculture**: Sequential disclosure: Fields ($N \ge 1$) $\to$ Plantings ($N \ge 1$) $\to$ Cost Calc & Harvest Sync $\to$ Yield Dispositions ($N_{\text{harvests}} \ge 1$).
   - **Digital Banking**: Business Settlement Accounts appear only when business entities are provisioned.
2. UI containers must initialize with `display: none;` where appropriate to prevent initial visual bleed before state evaluation.
3. Clean domain route names (`agriculture`, `security`, `business`, `banking`, `social`, `cluster`, `admin`, `tutorials`) must be used exclusively.

## 9. Sovereign Operator Profile & Obsidian Glassmorphic Matrix Aesthetics Rule
Whenever developing form inputs, authentication, operator profiles, or UI frameworks:
1. **Authentic Sovereign Obsidian Glassmorphic Matrix (SOGM) Design Language**:
   - The MADN design language is uniquely defined as the **Sovereign Obsidian Glassmorphic Matrix (SOGM)** / **Modular Adaptive Spatial Glass Interface (MASGI)**.
   - NEVER reference third-party proprietary trademark names (e.g. VisionPro, Apple, etc.) across UI microcopy, code comments, documentation, or academic thesis chapters.
   - Core visual identity anchors:
     - **Obsidian Dark Foundation (`#06080d`)**: High-contrast, zero-paint baseline canvas engineered for outdoor daylight and low-light community environments.
     - **Translucent Obsidian Glass (`rgba(20, 26, 38, 0.85)`) with Dual-Glow Depth**: Refractive frosted panels with cyan (`#00e5ff`) and emerald (`#10b981`) state halos.
     - **Organic Geometric Halo Identity**: Concentric circular pulse rings framing operator identities and live node badges.
2. **Autofill Shielding**: Form inputs must enforce dark glassmorphic backgrounds via `-webkit-autofill` inset box-shadow overrides and `color-scheme: dark;` to prevent bright white browser autofill bleeding.
3. **Coherent Non-Intrusive Validation**: All `<form>` tags must include `novalidate` to suppress jarring OS/browser native validation balloons. All validation feedback must strictly utilize glassmorphic toast notifications (`showErrorToast`, `showSuccessToast`) or subtle inline glowing labels.
4. **Operator Identity & Avatar Customization**: Operator profiles must support client-side image compression ($\le 256\times 256$ Canvas data URLs), live visual previews, and foreign-key safe database cascading across all sub-ledgers.

## 10. Enterprise Global Scale, Security Invariance & Modular Universality Standard
Whenever designing or modifying system gateways, authentication portals, or universal UI frameworks:
1. **Modular Dynamic Component Architecture**:
   - The frontend enforces a lightweight shell (`index.html`) that dynamically mounts modular on-demand component templates (`components/*.html`) into `<div id="app-viewport">` with in-memory caching (`templateCache`).
   - Monolithic DOM bloat is strictly prohibited to guarantee sub-15ms initial paints and zero layout lag.
2. **Architectural Universality on Generic Gateways**:
   - Generic gateways (such as login cards, landing pages, and node bootstrapping overlays) must NEVER enumerate or hardcode specific functional domain implementations (such as precision agriculture, touch POS, etc.).
   - Subsystem modules are dynamic and composable, revealed strictly via dynamic progressive disclosure (`getSubNavItems`) only after authenticated role and data precondition evaluations.
3. **Security & Identity Confidentiality in UI Elements**:
   - Form inputs, placeholder prompts, and help labels must NEVER expose mock user accounts, real or example operator usernames, or sample passwords (e.g. never use `e.g. pmd742omni`).
   - All placeholders must remain strictly generic, clean, and professional (`"Enter your username or operator ID"`, `"Enter password"`).
4. **Heritage Identity Anchor vs. Global Internationalization**:
   - Cultural naming (`MADN • Isango LomPhakathi`) serves as an authentic sovereign identity anchor honoring the creator's heritage.
   - All surrounding UI microcopy, feature descriptors, action verbs, and system guides must be authored in polished, international English built for global adoption across billions of users.
5. **Action Crispness & Anti-Bureaucracy**:
   - Interactive triggers, buttons, and call-to-actions must favor direct, clean, and unambiguous phrasing (`"Sign In"`, `"Submit"`, `"Confirm"`, `"Activate"`).
6. **Proactive Architectural Anticipation**:
   - Proactively evaluate every interface component and data pipeline against the overarching thesis: MADN as an enterprise-grade, offline-first, decentralized data mesh for dynamic value systems worldwide.

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
5. **Portable Bootstrapper (`../Applications/start.py`)**: Zero-config launcher auto-resolving Python dependencies, supervising multi-node child processes, and providing an interactive terminal dashboard.
6. **Automated Verification Matrix**: Always execute the full test suite (`pytest -v`) before creating documentation or thesis updates.
