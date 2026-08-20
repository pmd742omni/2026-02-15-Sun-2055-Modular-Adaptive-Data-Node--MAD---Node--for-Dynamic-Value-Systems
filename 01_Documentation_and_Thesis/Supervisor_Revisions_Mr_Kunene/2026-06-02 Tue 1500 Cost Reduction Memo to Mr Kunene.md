# MEMORANDUM

**TO:** Mr. Kunene (Project Supervisor)  
**FROM:** Peter Mthokozisi Dube  
**DATE:** June 2, 2026  
**SUBJECT:** Technical Report: Cost-Reduction Design Modifications and System Optimization for the Modular Adaptive Data Node (MADN)

---

Dear Mr. Kunene,

I am writing to provide a detailed overview of the cost-reduction modifications implemented in the design and prototyping phases of the Modular Adaptive Data Node (MADN). To ensure that the MADN ecosystem remains economically viable, physically reproducible, and scalable within the resource-constrained and infrastructure-unstable environments of Bulawayo and Tsholotsho, a series of strategic engineering adjustments were made to the hardware bill of materials (BOM) and software architecture.

These design decisions have significantly lowered the initial unit cost of both the central orchestrator (The Vault) and the edge sensing nodes (Intelligent Core) without sacrificing system performance, data integrity, or localized operational security. The key modifications are detailed below:

### 1. Transition to the Edge-Alert Security Gateway (Omitting Cameras & OpenCV)
*   **Original Configuration:** The initial design proposed an "Edge-Vision Gateway" utilizing active camera modules mounted on edge nodes and running real-time OpenCV image-processing libraries on the central orchestrator to perform object recognition.
*   **Modified Configuration:** The system was optimized into the "Edge-Alert Security Gateway," which completely omits camera hardware and the OpenCV software dependency. Instead, the edge nodes rely on a combination of Passive Infrared (PIR) motion sensors (HC-SR501) and Ultrasonic distance sensors (HC-SR04) to establish virtual tripwires.
*   **Cost & Performance Benefit:** Camera modules and real-time computer vision algorithms demand high processing overhead (CPU/RAM) and substantial local storage, which would require expensive edge single-board computers (SBCs). Shifting to binary state-change triggers allows us to run edge nodes on the highly affordable Raspberry Pi Pico W ($6 USD) rather than costly edge microcomputers. Additionally, it eliminates camera module costs, minimizes local storage capacity requirements, and provides a privacy-preserving security solution that does not capture facial images of community members.

### 2. Removal of the Dedicated UPS Power Management Shield
*   **Original Configuration:** The central orchestrator (The Vault) was designed to host a dedicated Uninterruptible Power Supply (UPS) expansion shield with built-in battery charging and monitoring integrated circuits.
*   **Modified Configuration:** The dedicated UPS power shield has been removed from the Raspberry Pi 4 configuration. The central node is instead powered directly via a standard 5V USB-C Power Supply Unit (PSU) or a generic consumer-grade portable power bank.
*   **Cost & Performance Benefit:** Dedicated UPS shields are expensive, niche hardware additions that introduce power conversion overhead and battery management complexity. Mass-produced portable power banks are cheap, widely available in local markets, and can serve as a simple plug-and-play backup power source to keep the Pi 4 running during electrical load shedding. This change substantially reduces the orchestrator's hardware cost (aligned with the Ndebele checkpoint milestone *Ukunciphisa*—to reduce or simplify).

### 3. Direct GPIO Pin Routing (Eliminating Port Expanders)
*   **Original Configuration:** To accommodate future expansion, early designs included I2C port expanders (such as the MCP23017 IC) on custom shields to interface the edge sensors, buttons, and displays.
*   **Modified Configuration:** All edge sensors (DHT22, capacitive soil sensor, PIR, and ultrasonic sensors), the ST7735 SPI TFT color display, and tactile push buttons are routed directly to the native GPIO and ADC pins of the Raspberry Pi Pico W.
*   **Cost & Performance Benefit:** By utilizing the native pinout capabilities of the RP2040 microcontroller, we eliminated the need for external port expander chips. This direct-routing strategy simplifies custom PCB layouts, lowers individual component counts, reduces assembly labor, and avoids the additional hardware cost of port expansion ICs.

### 4. Offloading POS Scanning Peripherals to Consumer-Grade Mobile Devices
*   **Original Configuration:** The Point-of-Sale (POS) subsystem on each node was planned to include integrated NFC/RFID reader boards and barcode scanner camera modules.
*   **Modified Configuration:** The transaction scanning and user interface components have been offloaded to the client's own mobile device (smartphone or tablet) via a lightweight, web-based Web-POS client interface (HTML5/Vanilla JS). The merchant's device uses its built-in camera for QR/barcode scanning and its native NFC transceiver for scanning customer store credits or token badges.
*   **Cost & Performance Benefit:** Rather than paying to equip every single MADN node with dedicated hardware keyboard interfaces, NFC chips, and barcode readers, the design leverages existing consumer hardware. This offloading strategy drastically cuts down the node BOM cost while maintaining a secure, local connection (via WebSocket over the local Wi-Fi Access Point or Bluetooth SPP RFCOMM sockets) to the central SQLite ledger on the Pi 4.

### 5. Omission of Copper Micro-Heatsinks
*   **Original Configuration:** The thermal management system for the central Raspberry Pi 4 included custom-milled copper heatsinks in addition to active cooling fans to mitigate high ambient operating temperatures.
*   **Modified Configuration:** The copper micro-heatsinks were omitted from the BOM, relying instead on an active, dual-fan cooling case to extract core heat.
*   **Cost & Performance Benefit:** High-grade copper heatsinks add custom manufacturing costs. Practical testing confirmed that a low-cost, active dual-fan cooling system provides sufficient airflow to prevent the Pi 4 CPU from reaching its thermal throttling limit (80°C) under the hot climatic conditions of Bulawayo and Tsholotsho, yielding savings on unnecessary metal accessories.

### 6. Software Stack Optimization and Headless Configuration
*   **Original Configuration:** Running a full desktop-based Linux OS on the central hub with a heavy enterprise database server.
*   **Modified Configuration:** The orchestrator runs Kali Linux in a headless (CLI-only) configuration. It hosts lightweight, open-source, serverless middleware: Mosquitto MQTT for message passing, InfluxDB for time-series telemetry, Grafana for local visualization, and an embedded SQLite database engine for ACID-compliant transactions.
*   **Cost & Performance Benefit:** The CLI-only configuration and serverless database model minimize RAM and CPU cycles. This efficiency enables the entire system to run smoothly on an affordable 4GB Raspberry Pi 4 Model B, saving us from having to purchase the more expensive 8GB model or standard computer server hardware.

### Summary of Impact

By implementing these engineering revisions, we have transitioned the MADN prototype from an expensive, alt-hardware reliant platform into a highly optimized, local-first IoT solution. The BOM cost for an edge sensing node is now under $15 USD, and the central hub can be assembled for under $80 USD. This design directly addresses the economic constraints of our target deployees while ensuring the technical viability of precision agriculture, perimeter security, and offline commerce.

Please let me know if you require further details or schematic schemata illustrating these changes.

Sincerely,

**Peter Mthokozisi Dube**  
Project Developer  
*Modular Adaptive Data Node (MADN) Project*
