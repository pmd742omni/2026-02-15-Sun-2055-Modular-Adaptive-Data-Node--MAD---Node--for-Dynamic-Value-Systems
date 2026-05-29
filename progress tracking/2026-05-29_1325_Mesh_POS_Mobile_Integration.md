# Checkpoint Nine - Mesh-POS Mobile Integration & Hardware Cost-Reduction

## Description
Updating the MADN scope and system requirements to reflect:
1. The complete removal of dedicated RFID/NFC (RC522) and Barcode/QR reader hardware modules from the swappable modules, and offloading all Point-of-Sale (POS) client functionality to local guest mobile devices (smartphones/tablets) communicating with the Vault (Pi 4) via local Wi-Fi and/or Bluetooth.
2. The removal of the MCP23017 I2C Port Expander module from the interface/expansion specifications, routing I/O directly from the Pico W to swappable sensors/controls to further reduce system cost.
3. The specification of Kali Linux (ARM64 headless) as the base operating system for the central Vault (Raspberry Pi 4) orchestrator platform, replacing Raspberry Pi OS.

## Progress
We have successfully updated the thesis chapters in the [Version 2026-05-13 Wed 1246](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/2026-03-30%20Mon%200833%20Chapters/2026-05-13%20Wed%201220%20Version%202026-05-13%20Wed%201246) directory:
- **[1.6 Scope of the Project.txt](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/2026-03-30%20Mon%200833%20Chapters/2026-05-13%20Wed%201220%20Version%202026-05-13%20Wed%201246/1.6%20Scope%20of%20the%20Project.txt)**: Explicitly integrated smartphones as temporary computational guest nodes and mobile POS client terminals.
- **[3.3 System Requirements.md](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/2026-03-30%20Mon%200833%20Chapters/2026-05-13%20Wed%201220%20Version%202026-05-13%20Wed%201246/2026-05-27%200832%203.3%20System%20Requirements.md)**:
  - Removed `POSModule` from swappable modules and added `MobilePOS` subgraph to the Mermaid flowchart, indicating direct local Wi-Fi and Bluetooth communication between mobile POS clients and the central Vault.
  - Removed `UI2["MCP23017 I2C Port Expander"]` from the `UIModule` subgraph in the Mermaid flowchart.
  - Omitted the dedicated RC522 RFID/NFC and Barcode/QR reader hardware module specifications.
  - Omitted the MCP23017 I2C Port Expander hardware module specification from Swappable Value Modules and renamed the list header to `User Interface & Controls`.
  - Added a new subsection **#### 4. Mobile Point-of-Sale (POS) Client Tier** detailing how native smartphone sensors (built-in camera for QR/barcodes, integrated NFC chip, and Wi-Fi/Bluetooth transceivers) replace the dedicated POS leaf-node hardware modules.
  - Updated the Software Requirements table to add rows for the Web-POS client interface (`HTML5 / Vanilla JS`) and the local socket daemon server (`Python SocketServer / PyBluez` on the Pi 4).
  - Updated the base Operating System for the orchestrator to `Kali Linux (ARM64 headless)` in the software requirements table and details.
  - Expanded the communication middleware section to detail the Bluetooth RFCOMM socket server daemon configured on the Pi 4.
  - Adjusted the application logic specifications for the Mesh-POS Transaction Ledger to incorporate mobile checkout API requests over Wi-Fi and Bluetooth.
  - Updated KiCAD workstation software requirements to specify routing I/O from the Pico W directly to swappable sensor/interface connections, removing the expander routing reference.

## Date & Time
2026-05-29 13:49

## Version 1.4.0 Ukonga
**Ukonga** is a Ndebele word that means "saving", "economizing", or "conservation". When we talk about *ukonga*, we mean making sure we use our resources as carefully as possible to avoid waste and keep costs down. By removing dedicated physical RFID and barcode reader modules from every edge node, utilizing existing smartphones, and removing the MCP23017 I2C Port Expander module to route signals directly, we are practicing *ukonga*—significantly reducing hardware overhead and making the MADN system much more accessible for rural communities!

## Next Steps
Having finalized the methodology adjustments and cost-reduction for triggers, transactions, and GPIO expansion systems, we are ready to proceed with system architecture designs, including logical data flow diagrams and edge network topology.

## Details of nature of development
Development was collaborative.
User: Peter Dube (Requested replacing dedicated physical POS scanning/reading modules with guest mobile devices, removing the I2C port expander, and setting Kali Linux as the Vault base operating system).
AI Agent Name: Antigravity (Implemented the search-and-replace updates across all chapter files, updated the Mermaid code, and documented the transition).
