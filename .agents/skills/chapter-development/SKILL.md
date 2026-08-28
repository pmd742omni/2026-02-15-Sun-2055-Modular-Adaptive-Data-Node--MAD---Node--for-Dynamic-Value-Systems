---
name: chapter-development
description: Standard operating workflow and rules for developing thesis chapters (e.g. Chapter 1 through Chapter 5+) in Markdown format, acquiring real machine timestamps, formatting mathematical equations, generating structured empirical benchmark tables, and publishing section files.
---

# Chapter Development Workflow Skill

This skill provides comprehensive instructions for planning, researching, authoring, formatting, and publishing academic thesis chapters for the **Modular Adaptive Data Node (MADN)** project.

> [!IMPORTANT]
> **LLM Academic Authorship Mandate**: All thesis chapters, theoretical formulations, literature analyses, system design explanations, and empirical benchmark discussions are authored and synthesized directly by the LLM (Antigravity) with genuine academic rigor, scholarly prose, KaTeX mathematics, and empirical evidence — never generated via simplistic text-copying algorithms. Scripts serve exclusively for runtime timestamping, directory scaffolding, and file management.

---

## 1. Trigger Conditions

Execute this workflow whenever the developer specifies:
- `"develop chapter [N]"` or `"write chapter [N]"`
- `"create chapter [N]"`
- Requests academic writing, results analysis, testing procedures, or system design documentation for project thesis chapters.

---

## 2. Directory & Naming Conventions

### Target Directory & Versioned Edition Schema
All chapter Markdown files **MUST** be written into a versioned edition folder using relative paths:
`../../../01_Documentation_and_Thesis/Chapters/YYYY-MM-DD Day HHMM Version YYYY-MM-DD Day HHMM/` (relative from this skill) or `./01_Documentation_and_Thesis/Chapters/YYYY-MM-DD Day HHMM Version YYYY-MM-DD Day HHMM/` (relative from workspace root).

### Real Machine Timestamp Requirement
- Every chapter file and directory **MUST** begin with an authoritative local machine timestamp prefix: `YYYY-MM-DD HHMM` (for files) and `YYYY-MM-DD Day HHMM Version YYYY-MM-DD Day HHMM` (for edition folders).
- Timestamps **MUST** be acquired dynamically from the system using the relative Python utility script:
  ```bash
  python ./scripts/get_chapter_timestamp.py
  ```
  *(or from workspace root: `python .agents/skills/chapter-development/scripts/get_chapter_timestamp.py`)*
- **CRITICAL**: Do NOT generate artificial future time offsets or hardcoded timestamps. Use real system time collected at runtime via Python.

### Edition Changelog Mandate (`EDITION_CHANGELOG.md`)
Every versioned chapter edition folder **MUST** include an **`EDITION_CHANGELOG.md`** file that systematically explains:
1. **New Architectural Paradigms**: Highlights advancements such as the Modular Adaptive Dynamic Component Architecture, in-place workspace swapping, and sub-15ms initial paints.
2. **Design Language Evolution**: Formulates the **Sovereign Obsidian Glassmorphic Matrix (SOGM)** and highlights the removal of any proprietary third-party references.
3. **Refined Empirical Benchmarks**: Quantifies benchmark improvements, memory footprint reductions, database concurrency latencies, and offline synchronization efficiency.
4. **Subsystem Evolutions**: Summarizes updates across Precision Agronomy, Touch POS, Multi-Currency Digital Banking, Security Gatekeeper, and Decentralized Mesh Clustering.

### File Schema & Structure
Within each versioned edition folder, generate:
1. **Edition Changelog**: `EDITION_CHANGELOG.md`
2. **Individual Sub-Section Files**: Each sub-section gets its own timestamped file.
   - Example format: `YYYY-MM-DD HHMM 1.1 Background of the Study.md`
   - Example format: `YYYY-MM-DD HHMM 5.2 Testing Procedures.md`
3. **Unified Compiled Chapter Files**: Compiled documents containing all sub-sections for each chapter.
   - Example format: `YYYY-MM-DD HHMM Chapter 1_ Introduction.md`
   - Example format: `YYYY-MM-DD HHMM Chapter 5_ Results Testing and Analysis.md`

---

## 3. Core Execution Steps

### Step 1: Context & Codebase Audit
Before drafting text, thoroughly explore the repository context using relative paths:
1. **Core Codebase**: Inspect `../../../Applications/Web App/backend` (`database.py`, `main.py`, `auth_utils.py`) and `../../../Applications/Web App/frontend` (`index.html`, `app.js`, `components/*.html`).
2. **System Internals**: Read `../../../Applications/Web App/SYSTEM_INTERNALS.md` for low-level equations, database concurrency models, and security architectures.
3. **Previous Editions**: Review previous chapter editions in `../../../01_Documentation_and_Thesis/Chapters/` to build incrementally upon previous scholarly prose and mathematical formulations.
4. **Empirical Benchmarks & Test Suite**: Run or inspect backend test suites to extract exact runtime numbers, latencies, current draws, and success rates.

### Step 2: Timestamp Acquisition via Python
Run the timestamp utility using a relative path to acquire the current machine local timestamp strings:
```bash
python ./scripts/get_chapter_timestamp.py
```
Parse `filename_prefix` (e.g., `2026-08-28 1445`) and `folder_name` (e.g., `2026-08-28 Fri 1445 Version 2026-08-28 Fri 1445`).

### Step 3: Drafting & Content Standards
When drafting chapter contents, enforce strict academic and technical standards:
- **Academic Tone**: Formal, quantitative, precise third-person passive/active academic voice.
- **Design Language Identity**: Formally utilize the **Sovereign Obsidian Glassmorphic Matrix (SOGM)** / **Modular Adaptive Spatial Glass Interface (MASGI)**. Strictly avoid all third-party trademarked names (e.g. VisionPro).
- **Empirical Grounding**: Every metric (latency, RAM, CPU temp, RSSI, path loss, price decay recovery %) must be grounded in verified system data.
- **LaTeX Mathematics**: Render all math formulas using standard KaTeX/LaTeX delimiters (`$...$` for inline, `$$...$$` for display math blocks).
- **Structured Data Tables**: Use Markdown tables for all comparative and benchmark data (Thermal, RF Mesh, Concurrency, Security, Cost Reduction, System Comparison).
- **Contextual Alignment**: Emphasize MADN's operating environment in Sub-Saharan Africa (Bulawayo and Tsholotsho), off-grid power resilience, local Wi-Fi micro-cloud autonomy, multi-currency tri-ledger (USD/ZAR/ZWG), and *Ukunciphisa* cost reduction parameters (93%+ capital savings).

### Step 4: File Publishing & Directory Verification
1. Create the timestamped edition folder in `../../../01_Documentation_and_Thesis/Chapters/`.
2. Generate `EDITION_CHANGELOG.md` inside the edition folder.
3. Generate each sub-section Markdown file and compiled chapter file.
4. Verify directory contents using `list_dir`.

### Step 5: Verification & Walkthrough Update
Create or update `walkthrough.md` in the conversation artifact directory summarizing the generated chapter edition, changelog insights, and architectural additions.
