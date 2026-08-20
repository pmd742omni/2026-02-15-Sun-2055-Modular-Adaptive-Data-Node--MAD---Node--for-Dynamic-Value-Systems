# Modular Adaptive Data Node (MADN) — Prototype Shopping List

This document lists the required hardware components, sensors, power modules, prototyping accessories, and fabrication materials needed to build a fully functional prototype of the **Modular Adaptive Data Node (MADN)** system. 

Consistent with the **Ukunciphisa (Cost-Reduction & Simplification)** milestones, this shopping list omits high-cost and complex elements (such as dedicated camera modules, OpenCV processing boards, copper micro-heatsinks, dedicated UPS shields, and port expanders). Instead, it relies on low-cost sensor-trigger logic, consumer-grade power bank buffers, native GPIO routing, and merchant-owned mobile devices for POS interactions.

*Estimated costs are in USD, with an approximate conversion to South African Rand (ZAR) at a rate of 1 USD = 18.00 ZAR. Local pricing in Bulawayo or Johannesburg may vary depending on import duties and shipping.*

---

## 1. Central Orchestrator Tier (The Vault)
The Vault serves as the central data aggregator, database server, network host, and visualization gateway for the local node cluster.

| Component | Description / Specifications | Qty | Est. Unit Cost (USD) | Est. Total Cost (USD) | Est. Total Cost (ZAR) | Purpose / Role in Prototype | Sourcing & Alternatives |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| **Raspberry Pi 4 Model B (4GB)** | Single-board computer with 4GB LPDDR4 RAM, quad-core CPU, Wi-Fi/Bluetooth. | 1 | $55.00 | $55.00 | R990.00 | Runs Kali Linux, Mosquitto MQTT broker, InfluxDB, SQLite, and Grafana dashboard. | Authorized resellers (PiShop, RS Components). 2GB model can be substituted if budget is highly constrained. |
| **High-Endurance MicroSD Card (128GB)** | Class 10, UHS-I write-intensive MicroSD card (e.g., SanDisk MAX/PRO Endurance). | 1 | $18.00 | $18.00 | R324.00 | Serves as system drive and local datastore; selected for high write endurance. | standard retail stores. Avoid cheap generic cards, which fail quickly under database writes. |
| **Active Dual-Fan Cooling Case** | Enclosure with dual active cooling fans and aluminum heatsink blocks. | 1 | $10.00 | $10.00 | R180.00 | Prevents thermal throttling of the Pi 4 CPU under Bulawayo's high ambient temperatures. | standard hobbyist shops. Omit copper heatsinks to save costs. |
| **USB-C Power Adapter (or Power Bank)** | 5V 3A USB-C power supply, or a standard 10,000mAh consumer power bank. | 1 | $12.00 | $12.00 | R216.00 | Powers the Vault. A generic power bank provides load-shedding backup. | standard retail. Replaces dedicated UPS shield. |
| **Portable LED Projector (USB-Powered)** | Low-power, lightweight LED projector with HDMI/AV inputs. | 1 | $45.00 | $45.00 | R810.00 | Projects Grafana diagnostics and community summaries to off-grid groups. | Optional/sharable. Can be omitted if users only view data on mobile browsers. |
| **Subtotal (The Vault)** | *With Projector*<br>*Without Projector* | | | **$140.00**<br>**$95.00** | **R2,520.00**<br>**R1,710.00** | | |

---

## 2. Edge Node Tier (Intelligent Cores) — For 2 Field-Deployed Nodes
Each Edge Node represents a local sensor terminal that monitors environmental and security conditions.

| Component | Description / Specifications | Qty | Est. Unit Cost (USD) | Est. Total Cost (USD) | Est. Total Cost (ZAR) | Purpose / Role in Prototype | Sourcing & Alternatives |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| **Raspberry Pi Pico W** | Dual ARM Cortex-M0+ cores, 264KB SRAM, 2MB Flash, CYW43439 Wi-Fi. | 2 | $7.00 | $14.00 | R252.00 | Runs MicroPython firmware to collect sensor data and publish MQTT messages. | "WH" model with pre-soldered headers is recommended to save soldering labor. |
| **Adafruit Terminal PiCowbell** | Screw terminal breakout board for Pico (Product ID: 5904). | 2 | $7.95 | $15.90 | R286.20 | Routes Pico W pins to spring terminals for solderless field installation. | Adafruit, DigiKey, or Mouser. |
| **ST7735 1.8" SPI TFT Display** | 128x160 resolution color screen. | 2 | $5.00 | $10.00 | R180.00 | Renders real-time telemetry, battery state, and security triggers at the node. | standard hobbyist shops. |
| **Tactile Push Buttons** | Momentary tactile switch buttons. | 1 pack | $2.00 | $2.00 | R36.00 | Menu navigation, sensor state reset, and manual alert acknowledgment. | Pack of 10 or 20 buttons. |
| **Subtotal (Edge Cores)** | | | | **$41.90** | **R754.20** | | |

---

## 3. Sensor Arrays & Modules
These sensors feed raw data into the Agri-Analytics Engine and the Edge-Alert Security Gateway.

| Component | Description / Specifications | Qty | Est. Unit Cost (USD) | Est. Total Cost (USD) | Est. Total Cost (ZAR) | Purpose / Role in Prototype | Sourcing & Alternatives |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| **Capacitive Soil Moisture Sensor (v1.2)** | Analog soil moisture probe (corrosion-resistant). | 2 | $2.50 | $5.00 | R90.00 | Measures ground moisture for the Agri-Analytics watering recommendations. | Must be capacitive (v1.2 or v2.0), NOT resistive, to prevent probe corrosion. |
| **DHT22 Temperature & Humidity Sensor** | High-precision digital microclimate sensor (AM2302). | 2 | $4.50 | $9.00 | R162.00 | Captures ambient temperature and humidity for climate profiling. | DHT22 provides better accuracy and range than the cheaper DHT11. |
| **HC-SR501 Passive Infrared (PIR) Sensor** | Pyroelectric human/biological heat signature sensor. | 2 | $2.00 | $4.00 | R72.00 | Triggers intrusion alerts in the Edge-Alert Security Gateway. | Core perimeter security module. |
| **HC-SR04 Ultrasonic Distance Sensor** | Sonar-based distance transmitter and receiver module. | 2 | $2.00 | $4.00 | R72.00 | Acts as proximity verification to filter out false alerts. | Paired with PIR sensor to create logical virtual tripwires. |
| **Subtotal (Sensors)** | | | | **$22.00** | **R396.00** | | |

---

## 4. Power Management & Power Reserves (Edge Nodes)
Provides localized, rechargeable, off-grid power to each field node.

| Component | Description / Specifications | Qty | Est. Unit Cost (USD) | Est. Total Cost (USD) | Est. Total Cost (ZAR) | Purpose / Role in Prototype | Sourcing & Alternatives |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| **18650 Li-Ion Batteries (2500mAh)** | Rechargeable lithium-ion cell, 3.7V nominal. | 4 | $4.00 | $16.00 | R288.00 | Powers the field nodes; allows swappable operations (2 cells active, 2 charging). | Use reputable brands (LG, Samsung, Panasonic). |
| **18650 Battery Holder (with JST-PH 2.0)** | Single-cell holder with pre-soldered JST leads. | 2 | $1.50 | $3.00 | R54.00 | Houses the rechargeable cell and plugs directly into the power board. | Select JST-PH 2.0 connectors for simple field swaps. |
| **TP4056 USB Lithium Charging Board** | Charging controller module with battery protection IC. | 2 | $1.00 | $2.00 | R36.00 | Charges 18650 cells safely from standard micro-USB/USB-C chargers. | Includes over-discharge/short-circuit protection. |
| **MT3608 DC-DC Step-Up Boost Converter** | Boost module (3.7V input to stable 5V output). | 2 | $1.50 | $3.00 | R54.00 | Supplies standard 5V power to the Pico W and the 5V sensors (e.g., HC-SR04). | Required because 18650 voltage drops below Pico operating threshold when low. |
| **Subtotal (Edge Power)** | | | | **$24.00** | **R432.00** | | |

---

## 5. Prototyping, Interconnects, & Fabrication Supplies
Includes assembly wiring, structural components, and fabrication materials.

| Component | Description / Specifications | Qty | Est. Unit Cost (USD) | Est. Total Cost (USD) | Est. Total Cost (ZAR) | Purpose / Role in Prototype | Sourcing & Alternatives |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| **Mini Solderless Breadboard** | 400-point breadboard for experimental layout. | 2 | $2.50 | $5.00 | R90.00 | Used for early wiring validation and testing sensor combinations. | Reusable across prototypes. |
| **Jumper Wire Kit** | 120-piece ribbon pack (Male-Male, Male-Female, Female-Female). | 1 pack | $5.00 | $5.00 | R90.00 | Signal routing and interconnection during development. | standard multi-colored Dupont wires. |
| **PETG 3D Printing Filament (1kg)** | Polyethylene Terephthalate Glycol filament, 1.75mm. | 1 spool | $22.00 | $22.00 | R396.00 | Used to print weatherproof, outdoor snap-fit edge enclosures. | PETG is highly recommended for outdoors due to its high UV resistance. |
| **PLA 3D Printing Filament (1kg)** | Polylactic Acid filament, 1.75mm. | 1 spool | $18.00 | R18.00 | R324.00 | Used to print indoor enclosures for the Vault, clips, and mounting brackets. | Lower cost and easier to print than PETG. |
| **Stacking Connectors & Headers Pack** | Stacking headers (Adafruit 5583, 5584, 5585). | 1 set | $15.00 | $15.00 | R270.00 | Pins, sockets, and low-profile stacking headers for PiCowbell and Pico W. | Standard Adafruit parts. |
| **Subtotal (Supplies)** | | | | **$65.00** | **R1,170.00** | | |

---

## Summary of Estimated Prototype Budget

| System Layer | Estimated Cost (USD) | Estimated Cost (ZAR) | Key Included Components |
| :--- | :---: | :---: | :--- |
| **Central Orchestrator (The Vault)** | $140.00 *(or $95.00)* | R2,520.00 *(or R1,710.00)* | Pi 4 (4GB), 128GB High-Endurance Card, Cooling Case, power supply, *and LED Projector*. |
| **Edge Cores (2 Nodes)** | $41.90 | R754.20 | 2x Pico W, 2x Terminal PiCowbells, 2x ST7735 Screens, Navigation Buttons. |
| **Distributed Sensor Array** | $22.00 | R396.00 | 2x Capacitive Soil, 2x DHT22 Temp/Humid, 2x PIR Motion, 2x Ultrasonic Proximity. |
| **Edge Power Reserves** | $24.00 | R432.00 | 4x 18650 Cells, Battery Holders, TP4056 Chargers, MT3608 Boost Converters. |
| **Prototyping & Filament** | $65.00 | R1,170.00 | Breadboards, Jumper Wires, 1kg PLA Spool, 1kg PETG Spool, Stackable Headers. |
| **GRAND TOTAL** | **$292.90** *(or **$247.90**)* | **R5,272.20** *(or **R4,462.20**)* | **Full 3-node localized network prototype package (1 Vault + 2 Edge Nodes).** |

---

## Strategic Procurement & Local Sourcing Notes
1. **Leveraging Existing Equipment**: The total cost drops significantly if the user already has standard tools (like a soldering iron, solder, or a 3D printer) and if the **Portable LED Projector** is omitted or shared.
2. **Mobile Device Offloading**: Point-of-Sale (POS) operations are optimized to use the local merchants' personal smartphones/tablets. Standard web browser pages handle inventory management and QR/NFC reads via local Wi-Fi, saving hundreds of dollars on custom barcode scanners and RFID reader boards.
3. **Power Bank Scavenging**: Standard consumer USB power banks are highly competitive and easily sourced locally. They provide built-in pass-through charging, acting as an off-the-shelf UPS backup for the central Pi 4.
4. **Resiliency Sourcing**: High-endurance microSD cards are critical. Normal microSD cards fail rapidly under continuous InfluxDB time-series logs. Sourcing an endurance-rated card prevents data loss in off-grid field testing.
