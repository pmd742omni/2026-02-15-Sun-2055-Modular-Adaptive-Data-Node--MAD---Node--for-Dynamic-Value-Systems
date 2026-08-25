#!/usr/bin/env python3
"""
Universal .agents Directory & Rules Optimizer for MADN
=====================================================
Dynamically discovers all skills under .agents/skills/ and ensures that
.agents/AGENTS.md and agent guidelines are consistently structured, indexed,
and aligned with current and future architectural standards.
"""

import os
import sys
import glob

def find_project_root():
    cwd = os.getcwd()
    curr = cwd
    while True:
        if os.path.exists(os.path.join(curr, ".git")) or os.path.exists(os.path.join(curr, ".agents")):
            return curr
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent
    return cwd

def discover_available_skills(agents_dir):
    skills_dir = os.path.join(agents_dir, "skills")
    if not os.path.exists(skills_dir):
        return []
    
    discovered = []
    for item in os.listdir(skills_dir):
        skill_md = os.path.join(skills_dir, item, "SKILL.md")
        if os.path.exists(skill_md):
            discovered.append((item, skill_md))
    return discovered

def optimize_agents_directory():
    root = find_project_root()
    agents_dir = os.path.join(root, ".agents")
    agents_file = os.path.join(agents_dir, "AGENTS.md")
    
    if not os.path.exists(agents_dir):
        os.makedirs(agents_dir, exist_ok=True)

    skills = discover_available_skills(agents_dir)
    print(f"[*] Discovered {len(skills)} active skills in .agents/skills/:")
    for name, path in skills:
        print(f"    - {name} ({os.path.relpath(path, root)})")

    # Generate or synchronize AGENTS.md
    agents_md_content = """# Project Rules & Customizations

## Progress Tracking Rule ("Document Now")
Whenever the user states **"document now"**, **"document progress"**, or requests a new checkpoint:
1. Refer to and follow the instructions in the `document-now` skill ([SKILL.md](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/.agents/skills/document-now/SKILL.md)).
2. Synchronize `Applications/Web App/SYSTEM_INTERNALS.md`, `Applications/Web App/USER_MANUAL.md`, and `Applications/Web App/PROJECT_CHECKLIST.md` with relative destination paths (`./`, `../`, `../../`).
3. Synthesize progress, create the progress tracking file under `progress tracking/YYYY-MM-DD_HHMM_Description.md` following the required schema (including Ndebele version codename, 10-year-old child target explanations and next steps, and developer attributions).
4. Stage all changes (`git add .`) and execute a git commit with the message format: `YYYY-MM-DD Day HHMM: [Title] ([Codename] [Version])`.

## System Internals Documentation Rule ("System Internals")
Whenever the user states **"update system internals"**, **"generate internals doc"**, or requests deep technical reference documentation:
1. Refer to and follow the instructions in the `system-internals-doc` skill ([SKILL.md](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/.agents/skills/system-internals-doc/SKILL.md)).
2. Audit the system architecture, database locks, scrypt/TOTP security parameters, mesh routing, multi-currency tri-ledger, and continuous exponential decay math.
3. Update `Applications/Web App/SYSTEM_INTERNALS.md` with low-level technical reference details, Mermaid diagrams, and LaTeX equations.

## Chapter Development Rule ("Chapter Development" / "Develop Chapter")
Whenever the user states **"develop chapter"**, **"write chapter"**, **"create chapter"**, or requests development of a thesis chapter:
1. Refer to and follow the instructions in the `chapter-development` skill ([SKILL.md](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/.agents/skills/chapter-development/SKILL.md)).
2. Acquire the authoritative local machine system timestamp string (`YYYY-MM-DD HHMM`) by running `python .agents/skills/chapter-development/scripts/get_chapter_timestamp.py` dynamically at runtime.
3. Audit codebase, backend test results, system internals, math models, and hardware benchmarks.
4. Output individual sub-section files (`YYYY-MM-DD HHMM 5.X Section Title.md`) and a unified compiled chapter file (`YYYY-MM-DD HHMM Chapter X_ Title.md`) into `01_Documentation_and_Thesis/Chapters/`.

## Dynamic Value Milestone Release Rule ("Milestone Release" / "Sync Chapters and Document")
Whenever the user states **"milestone release"**, **"sync chapters and document"**, or requests a new feature release milestone:
1. Refer to and follow the instructions in the `dynamic-value-milestone` skill ([SKILL.md](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/.agents/skills/dynamic-value-milestone/SKILL.md)).
2. Execute the full automated verification suite (`pytest -v`).
3. Automatically generate updated sub-section and compiled chapter files into a newly created versioned directory `01_Documentation_and_Thesis/Chapters/YYYY-MM-DD Day HHMM Version YYYY-MM-DD Day HHMM/`.
4. Optimize `.agents` directory rules for universal Modular Adaptive Data Node systems.
5. Trigger the `document-now` progress tracking skill to synchronize `SYSTEM_INTERNALS.md`, `USER_MANUAL.md`, `PROJECT_CHECKLIST.md`, register the version codename, and execute the Git commit.

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
"""

    with open(agents_file, "w", encoding="utf-8") as f:
        f.write(agents_md_content.strip() + "\n")

    print("[+] Successfully optimized .agents/AGENTS.md across all discovered skills and standards!")
    return True

if __name__ == "__main__":
    optimize_agents_directory()
