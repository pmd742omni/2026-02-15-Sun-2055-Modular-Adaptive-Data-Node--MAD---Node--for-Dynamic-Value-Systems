---
name: chapter-development
description: Standard operating workflow and rules for developing thesis chapters (e.g. Chapter 1 through Chapter 5+) in Markdown format, acquiring real machine timestamps, formatting mathematical equations, generating structured empirical benchmark tables, and publishing section files.
---

# Chapter Development Workflow Skill

This skill provides comprehensive instructions for planning, researching, writing, formatting, and publishing academic thesis chapters for the **Modular Adaptive Data Node (MADN)** project.

---

## 1. Trigger Conditions

Execute this workflow whenever the developer specifies:
- `"develop chapter [N]"` or `"write chapter [N]"`
- `"create chapter [N]"`
- Requests academic writing, results analysis, testing procedures, or system design documentation for project thesis chapters.

---

## 2. Directory & Naming Conventions

### Target Directory
All chapter Markdown files **MUST** be written to the standard chapters folder:
`2026-03-30 Mon 0833 Chapters/` (relative to workspace root) or:
`c:\Users\ignaz\OneDrive\Documents\Projects\2026-02-15 Sun 2055 Modular Adaptive Data Node (MAD - Node) for Dynamic Value Systems\2026-03-30 Mon 0833 Chapters\`

### Real Machine Timestamp Requirement
- Every chapter file **MUST** begin with an authoritative local machine timestamp prefix: `YYYY-MM-DD HHMM`.
- Timestamps **MUST** be acquired dynamically from the system using the Python utility script:
  ```bash
  python .agents/skills/chapter-development/scripts/get_chapter_timestamp.py
  ```
- **CRITICAL**: Do NOT generate artificial future time offsets or hardcoded timestamps. Use real system time collected at runtime via Python.

### File Schema & Structure
For any given chapter (e.g., Chapter 5), the workflow generates:
1. **Individual Section Files**: Each sub-section gets its own timestamped file.
   - Example format: `YYYY-MM-DD HHMM 5.1 Introduction.md`
   - Example format: `YYYY-MM-DD HHMM 5.2 Testing Procedures.md`
2. **Unified Chapter File**: A single compiled Markdown document containing all sub-sections.
   - Example format: `YYYY-MM-DD HHMM Chapter 5_ Results Testing and Analysis.md`

---

## 3. Core Execution Steps

### Step 1: Context & Codebase Audit
Before drafting text, thoroughly explore the repository context:
1. **Core Codebase**: Inspect `Applications/Web App/backend` (`database.py`, `main.py`, `auth_utils.py`) and `Applications/Web App/frontend`.
2. **System Internals**: Read `Applications/Web App/SYSTEM_INTERNALS.md` for low-level equations, database concurrency models, and security architectures.
3. **Previous Chapters**: Review previous chapters (e.g., Chapter 3 methodology, Chapter 4 system design, `Shopping List for the Prototype.md`) to maintain narrative continuity.
4. **Empirical Benchmarks & Test Suite**: Run or inspect backend test outputs (`test_auth.py`, `test_cycle3.py`, `test_cycle4.py`, `test_endpoints_live.py`) to extract exact runtime numbers, latencies, current draws, and success rates.

### Step 2: Timestamp Acquisition via Python
Run the timestamp utility to acquire the current machine local timestamp string:
```bash
python .agents/skills/chapter-development/scripts/get_chapter_timestamp.py
```
Parse `filename_prefix` (e.g., `2026-08-12 1854`).

### Step 3: Drafting & Content Standards
When drafting chapter contents, enforce strict academic and technical standards:
- **Academic Tone**: Formal, quantitative, precise third-person passive/active academic voice.
- **Empirical Grounding**: Every metric (latency, RAM, CPU temp, RSSI, path loss, price decay recovery %) must be grounded in verified system data.
- **LaTeX Mathematics**: Render all math formulas using standard KaTeX/LaTeX delimiters (`$...$` for inline, `$$...$$` for display math blocks). Include variables, parametric bounds, path loss exponents, and hash chain recurrence relations.
- **Structured Data Tables**: Use Markdown tables for all comparative and benchmark data (Thermal, RF Mesh, Concurrency, Security, Cost Reduction, System Comparison).
- **Contextual Alignment**: Emphasize MADN's operating environment in Sub-Saharan Africa (Bulawayo and Tsholotsho), off-grid power resilience, local Wi-Fi micro-cloud autonomy, multi-currency tri-ledger (USD/ZAR/ZWG), and *Ukunciphisa* cost reduction parameters (93%+ capital savings).

### Step 4: File Publishing
1. Generate each sub-section Markdown file in `2026-03-30 Mon 0833 Chapters/` prefixed with the acquired Python machine timestamp.
2. Generate the unified complete chapter file combining all sub-sections.
3. Verify file paths using `list_dir`.

### Step 5: Verification & Walkthrough Update
Create or update `walkthrough.md` in the conversation artifact directory summarizing the generated chapter files, table benchmarks, and mathematical proofs.
