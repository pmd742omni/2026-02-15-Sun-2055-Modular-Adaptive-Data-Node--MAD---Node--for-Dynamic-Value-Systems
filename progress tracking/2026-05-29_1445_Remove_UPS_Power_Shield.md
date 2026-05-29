# Checkpoint Twelve - Remove UPS Power Management Shield

## Description
Removing the dedicated UPS power management shield from the Raspberry Pi 4 (The Vault) configuration to reduce deployment costs. The central node will instead be powered directly via a standard 5V USB-C power supply unit (PSU) or a portable power bank.

## Progress
We have updated the system requirements and hardware diagrams to replace the UPS shield with a standard USB-C PSU/power bank source:
- **[3.3 System Requirements.md](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/2026-03-30%20Mon%200833%20Chapters/2026-05-13%20Wed%201220%20Version%202026-05-13%20Wed%201246/2026-05-27%200832%203.3%20System%20Requirements.md)**:
  - Replaced the `VaultUPS["UPS Power Management Shield"]` node in the central Vault tier of the hardware Mermaid diagram with `VaultPower["USB-C PSU / Power Bank"]`.
  - Replaced the power management hardware requirement with a flexible power supply option (USB-C PSU or power bank).
- **SVG Diagrams**: Updated text labels inside the rendered SVGs to display "USB-C Power Supply / Power Bank" instead of "UPS Power Management Shield":
  - **[2026-05-27 Wed 0857 Rendered Mermaid Code Output Hardware Requirements.svg](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/2026-03-30%20Mon%200833%20Chapters/2026-05-13%20Wed%201220%20Version%202026-05-13%20Wed%201246/2026-05-27%20Wed%200857%20Rendered%20Mermaid%20Code%20Output%20Hardware%20Requirements.svg)**
  - **[2026-05-27 Wed 0917 Rendered Mermaid Code Output Hardware Requirements.svg](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/2026-03-30%20Mon%200833%20Chapters/2026-05-13%20Wed%201220%20Version%202026-05-13%20Wed%201246/2026-05-27%20Wed%200917%20Rendered%20Mermaid%20Code%20Output%20Hardware%20Requirements.svg)**
  - **[2026-05-29 Fri 1433 Hardware Requirements.svg](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/2026-03-30%20Mon%200833%20Chapters/2026-05-13%20Wed%201220%20Version%202026-05-13%20Wed%201246/2026-05-29%20Fri%201433%20Hardware%20Requirements.svg)**

## Date & Time
2026-05-29 14:45

## Version 1.7.0 Ukunciphisa
**Ukunciphisa** is a Ndebele word that means "to reduce", "to simplify", or "to decrease". It describes the act of scaling down elements for efficiency or cost-containment. By removing the dedicated UPS power management shield and leveraging standard 5V USB-C power adapters or consumer power banks for the Raspberry Pi 4 orchestrator, *Ukunciphisa* lowers the economic barrier to deploying the MADN central hub in off-grid environments without sacrificing core computing capabilities!

## Next Steps
Continue refining requirements and designs, moving towards Chapter 4 for implementation details.

## Details of nature of development
Development was collaborative.
User: Peter Dube (Proposed removing the central Pi 4 UPS shield and replacing it with direct PSU / powerbank options to reduce initial deployment cost).
AI Agent Name: Antigravity (Updated diagram codes, requirement text, rendered SVGs, and documented progress).
