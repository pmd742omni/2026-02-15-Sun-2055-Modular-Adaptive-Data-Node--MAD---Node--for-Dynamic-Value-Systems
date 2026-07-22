# "Document Now" Workflow Rules

This document outlines the systematic steps and expectations whenever the developer triggers the "document now" (or "document progress") command.

---

## 1. Trigger Conditions

This rule is executed immediately whenever the developer states **"document now"**, **"document progress"**, or requests a new checkpoint.

---

## 2. Standardized Workflow Steps

Upon receiving the trigger, the AI assistant must perform the following actions:

### Step 1: Analyze & Gather Progress
Review the session logs, modified files, and user inputs since the last checkpoint to synthesize:
* The description of the work.
* The detailed list of progress points.
* The next steps for the project.
* The contribution details (who developed what, including specific AI agents and roles).
* **Registry Query**: Check the [Version and Codename Registry](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-03-11%20Wed%200824%20Telone%20Unpaid%20Industrial%20Attachment/2026-05-28%20Thu%200944%20Rules/2026-05-28%20Thu%201009%20Version%20and%20Codename%20Registry.md) to identify the last version number and ensure the new Ndebele codename selected has not been used previously.

### Step 2: Create a Progress Tracking File
Create a new Markdown file inside the [progress tracking](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-03-11%20Wed%200824%20Telone%20Unpaid%20Industrial%20Attachment/progress%20tracking) directory:
* **File Naming Format**: `YYYY-MM-DD_HHMM_Description.md` (no day name, underscores only).
* **Content Structure**: The file must strictly follow the schema:
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
  * **Explanation**: [English explanation targetted at a 10-year-old child]

  ## Next Steps
  * [Bullet points of future actions targetted at a 10-year-old child]

  ## Details of nature of development
  Co-developed by [Developer] and [AI Agent Name] (AI Coding Assistant).
  * [Role allocations]
  ```

### Step 3: Initialize/Update Log Folders (If Applicable)
If the progress relates to daily log compilation:
* Create or update the dedicated folder inside the [Logs](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-03-11%20Wed%200824%20Telone%20Unpaid%20Industrial%20Attachment/Logs) directory using the Day-Name Timestamp format.
* Add or update the core Markdown log inside that folder.

### Step 4: Update Registry
Append the new version details (Version, Codename, Translation, Date, and Progress File link) to the table inside [Version and Codename Registry](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-03-11%20Wed%200824%20Telone%20Unpaid%20Industrial%20Attachment/2026-05-28%20Thu%200944%20Rules/2026-05-28%20Thu%201009%20Version%20and%20Codename%20Registry.md).

### Step 5: Stage and Git Commit
1. **Stage**: Add all new rules, registry updates, log files, assets, and progress files to Git (`git add .`).
2. **Commit**: Construct the commit message according to the [Git Commit Message Rules](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-03-11%20Wed%200824%20Telone%20Unpaid%20Industrial%20Attachment/2026-05-28%20Thu%200944%20Rules/2026-05-28%20Thu%200944%20Git%20Commit%20Message%20Rules.md):
   `YYYY-MM-DD Day HHMM: [Progress Tracking File Title] ([Version Codename] [Version])`
3. **Commit Command Execution**: Run the Git commit command on behalf of the developer.
