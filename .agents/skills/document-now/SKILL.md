---
name: document-now
description: Automatically executes the standardized "Document Now" progress tracking workflow whenever the developer states "document now", "document progress", or requests a checkpoint update.
---

# Document Now Workflow Skill

This skill provides step-by-step instructions for executing the **Document Now** progress tracking workflow in accordance with the project's standard operating rules (`2026-05-28 Thu 0952 Document Now Rule.md`).

---

## 1. Trigger Conditions

Execute this workflow immediately when the developer specifies:
- `"document now"`
- `"document progress"`
- `"checkpoint"` or `"create checkpoint"`
- Requests progress tracking documentation for the project.

---

## 2. Execution Workflow

### Step -1: Zero-Config Self-Bootstrapping
Before performing progress analysis or creating files, execute the workspace bootstrap command:
```bash
python .agents/skills/document-now/scripts/version_registry.py bootstrap
```
This command automatically:
1. Detects the current project root directory dynamically.
2. Creates the `progress tracking/` folder if it does not exist.
3. Initializes `progress tracking/version_registry.json` and `progress tracking/Version_Registry.md` if missing.
4. Checks Git repository status. If `git_initialized` is `false`, run `git init` to initialize Git version control.
5. Returns `next_version` (defaults to `1.0.0` for brand-new projects) and `suggested_codename` (e.g., `Isisekelo` for initial foundation).

---

### Step 0: Collect System Date & Time Stamps
Run the timestamp utility script to obtain authoritative, formatted system date and time strings:
```bash
python .agents/skills/document-now/scripts/get_timestamp.py
```
Use the JSON output values:
- `file_prefix`: For progress filename `progress tracking/{file_prefix}_Description.md`.
- `human_date_time`: For the `## Date & Time` section in the progress markdown file.
- `git_prefix`: For constructing the Git commit header (`{git_prefix}: [Title] ([Codename] [Version])`).

---

### Step 1: Analyze & Gather Progress & Validate Codename Uniqueness
Review the conversation transcript, git diffs, modified files, and recent prompt commands since the previous checkpoint to synthesize:
1. **Description**: High-level summary of changes and architectural accomplishments.
2. **Progress**: Bullet points detailing specific technical, functional, and mathematical additions.
3. **Next Version Number**: Compute the next version number by running:
   ```bash
   python .agents/skills/document-now/scripts/version_registry.py next-version
   ```
4. **Codename Uniqueness Check (Mandatory)**: Select a proposed Ndebele word as the version codename and run:
   ```bash
   python .agents/skills/document-now/scripts/version_registry.py check <proposed_codename>
   ```
   If `"unique": false` is returned, a different Ndebele word **MUST** be chosen and checked until `"unique": true` is returned!
5. **Child-Friendly Explanation**: Write an English explanation of the version codename targeted at a 10-year-old child.
6. **Child-Friendly Next Steps**: Write bullet points of future actions targeted at a 10-year-old child.
7. **Development Attribution**: Credit `Peter Dube` and `Antigravity (AI Coding Assistant)` with their respective role allocations.

---

### Step 2: Create a Progress Tracking File
Create a new Markdown file inside the `progress tracking/` directory in the project root:

- **Path Format**: `progress tracking/YYYY-MM-DD_HHMM_Description.md` (no day name in the filename, use underscores only).
- **Required File Schema**:
  ```markdown
  # [Title]

  ## Description
  [High-level summary of changes]

  ## Progress
  * [Bullet points of accomplishments]

  ## Date & Time
  [E.g., Thursday, 28 May 2026, 09:52 AM (local time)]

  ## Version [Version] ([Version Codename])
  * **Codename**: [Ndebele word] ([Translation/Meaning])
  * **Explanation**: [English explanation targeted at a 10-year-old child]

  ## Next Steps
  * [Bullet points of future actions targeted at a 10-year-old child]

  ## Details of nature of development
  Co-developed by Peter Dube and Antigravity (AI Coding Assistant).
  * [Role allocations]
  ```

---

### Step 3: Synchronize System Internals, User Manual & Project Checklist (Mandatory)
Before registering the version, audit and synchronize the three core documentation files:
1. **`Applications/Web App/SYSTEM_INTERNALS.md`**: Update edition/version header, mathematical equations, relative path references (`./`, `../`, `../../`), and newly implemented kernel architectures.
2. **`Applications/Web App/USER_MANUAL.md`**: Update operational guides, demo account tables, and launcher instructions with relative paths.
3. **`Applications/Web App/PROJECT_CHECKLIST.md`**: Check off newly completed tasks and verify all relative file links.

---

### Step 4: Register Version in Registry Database via Python
Execute the version registration script to append the new version details to `progress tracking/version_registry.json` and `progress tracking/Version_Registry.md`:
```bash
python .agents/skills/document-now/scripts/version_registry.py register <version> <codename> "<meaning>" "<date_str>" <filename>
```

---

### Step 5: Stage & Git Commit
1. **Stage Changes**:
   Execute `git add .` to stage all newly created progress files, rules, documentation, and codebase modifications.
2. **Construct Commit Message**:
   Follow the project Git commit naming convention:
   `YYYY-MM-DD Day HHMM: [Progress Tracking File Title] ([Version Codename] [Version])`
   *(Example: `2026-07-20 Mon 1015: Full Implementation and Mathematical Verification of Cycles 1 through 4 Web Application Modules (Ukusebenza Version 1.16.0)`)*
3. **Execute Commit**:
   Run `git commit -m "<constructed commit message>"` using the terminal command tool on behalf of the developer.
