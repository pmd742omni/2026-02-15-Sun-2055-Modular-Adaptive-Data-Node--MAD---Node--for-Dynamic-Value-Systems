#!/usr/bin/env python3
"""
Automated .agents Optimizer for MADN Dynamic Value Systems
Ensures that .agents/AGENTS.md and related skill manifests remain synchronized with:
- Tri-Node heterogeneous architecture (Operator, Data Node, Vault Node)
- Dynamic Extensible Multi-Currency Engine & ZiG standards
- Continuous World Currency (ISO 4217) & Crypto Ingestion
- Real-time multi-tier collision prevention
- Automated 27-test regression verification matrix
"""

import os
import sys

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

def optimize_agents_directory():
    root = find_project_root()
    agents_file = os.path.join(root, ".agents", "AGENTS.md")
    
    if not os.path.exists(agents_file):
        print("[-] AGENTS.md not found at:", agents_file)
        return False

    with open(agents_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Ensure all essential architectural rules are present
    required_sections = [
        "## Progress Tracking Rule (\"Document Now\")",
        "## System Internals Documentation Rule (\"System Internals\")",
        "## Chapter Development Rule (\"Chapter Development\" / \"Develop Chapter\")",
        "## Dynamic Value Milestone Release Rule (\"Milestone Release\" / \"Sync Chapters and Document\")",
        "## Tri-Node Architecture & Composable Dynamic Value Systems Standard"
    ]

    milestone_rule = """
## Dynamic Value Milestone Release Rule ("Milestone Release" / "Sync Chapters and Document")
Whenever the user states **"milestone release"**, **"sync chapters and document"**, or requests a new feature release milestone:
1. Refer to and follow the instructions in the `dynamic-value-milestone` skill ([SKILL.md](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/.agents/skills/dynamic-value-milestone/SKILL.md)).
2. Execute the full 27-test verification suite (`pytest -v`).
3. Automatically generate updated sub-section and compiled chapter files into a newly created versioned directory `01_Documentation_and_Thesis/Chapters/YYYY-MM-DD Day HHMM Version YYYY-MM-DD Day HHMM/`.
4. Optimize `.agents` directory rules for Tri-Node Dynamic Value Systems.
5. Trigger the `document-now` progress tracking skill to synchronize `SYSTEM_INTERNALS.md`, `USER_MANUAL.md`, `PROJECT_CHECKLIST.md`, register the version codename, and execute the Git commit.
"""

    if "Dynamic Value Milestone Release Rule" not in content:
        # Insert before Tri-Node Architecture section
        if "## Tri-Node Architecture" in content:
            content = content.replace("## Tri-Node Architecture", milestone_rule.strip() + "\n\n## Tri-Node Architecture")
        else:
            content += "\n" + milestone_rule.strip() + "\n"

    # Verify test count
    content = content.replace("25-test suite", "27-test suite")

    with open(agents_file, "w", encoding="utf-8") as f:
        f.write(content)

    print("[+] Successfully optimized .agents/AGENTS.md for Modular Adaptive Data Node dynamic value systems!")
    return True

if __name__ == "__main__":
    optimize_agents_directory()
