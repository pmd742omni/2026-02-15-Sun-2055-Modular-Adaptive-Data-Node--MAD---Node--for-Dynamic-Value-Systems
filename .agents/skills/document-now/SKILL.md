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

### Step 1: Analyze & Gather Progress
Review the conversation transcript, git diffs, modified files, and recent prompt commands since the previous checkpoint to synthesize:
1. **Description**: High-level summary of changes and architectural accomplishments.
2. **Progress**: Bullet points detailing specific technical, functional, and mathematical additions.
3. **Version & Codename**: Select a unique Ndebele word as the version codename (verify against previously used codenames in `progress tracking/` logs to avoid duplicates).
4. **Child-Friendly Explanation**: Write an English explanation of the version codename targeted at a 10-year-old child.
5. **Child-Friendly Next Steps**: Write bullet points of future actions targeted at a 10-year-old child.
6. **Development Attribution**: Credit `Peter Dube` and `Antigravity (AI Coding Assistant)` with their respective role allocations.

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

### Step 3: Update Version Registry (If Applicable)
If a `Version and Codename Registry.md` file exists in the workspace or `progress tracking/` folder, append a new row to the table containing:
- Version Number
- Ndebele Codename & Meaning
- Local Date & Time
- Link to the created progress file

---

### Step 4: Stage & Git Commit
1. **Stage Changes**:
   Execute `git add .` to stage all newly created progress files, rules, documentation, and codebase modifications.
2. **Construct Commit Message**:
   Follow the project Git commit naming convention:
   `YYYY-MM-DD Day HHMM: [Progress Tracking File Title] ([Version Codename] [Version])`
   *(Example: `2026-07-20 Mon 1015: Full Implementation and Mathematical Verification of Cycles 1 through 4 Web Application Modules (Ukusebenza Version 1.16.0)`)*
3. **Execute Commit**:
   Run `git commit -m "<constructed commit message>"` using the terminal command tool on behalf of the developer.
