# Project Rules & Customizations

## Progress Tracking Rule ("Document Now")
Whenever the user states **"document now"**, **"document progress"**, or requests a new checkpoint:
1. Refer to and follow the instructions in the `document-now` skill ([SKILL.md](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/.agents/skills/document-now/SKILL.md)).
2. Synthesize progress, create the progress tracking file under `progress tracking/YYYY-MM-DD_HHMM_Description.md` following the required schema (including Ndebele version codename, 10-year-old child target explanations and next steps, and developer attributions).
3. Stage all changes (`git add .`) and execute a git commit with the message format: `YYYY-MM-DD Day HHMM: [Title] ([Codename] [Version])`.
