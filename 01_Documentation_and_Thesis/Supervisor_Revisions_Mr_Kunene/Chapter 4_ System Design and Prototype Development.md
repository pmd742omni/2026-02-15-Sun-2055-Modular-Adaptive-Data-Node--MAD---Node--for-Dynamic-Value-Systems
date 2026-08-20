# **CHAPTER 4: SYSTEM DESIGN AND PROTOTYPE DEVELOPMENT**

## **4.1 System Architecture**

The system architecture of the Modular Adaptive Data Node (MADN) was engineered to prioritize decentralized, local-first data processing, offline network resiliency, and cost-efficient hardware scaling. By fundamentally shifting the computational burden away from centralized cloud servers, the architecture operates seamlessly in the resource-constrained and infrastructure-unstable environments of Bulawayo and Tsholotsho.

The architecture is structurally divided into three functional tiers:

1. **The Central Orchestration Tier (The Vault):** Serving as the core of the localized micro-cloud, this tier is powered by a Raspberry Pi 4 Model B running a headless ARM64 Kali Linux OS. It acts as the primary coordination point for local data accumulation, machine learning inference, and local network routing. It hosts a Mosquitto MQTT broker, an InfluxDB time-series database, and an SQLite transactional ledger.  
2. **The Edge Sensing and Processing Tier (Intelligent Core):** Deployed at the environmental boundary, this tier utilizes Raspberry Pi Pico W microcontrollers. These edge nodes process raw data from physical sensors, apply local filtering, and transmit structured telemetry payloads to the Vault over a localized Wi-Fi mesh.  
3. **The Mobile Point-of-Sale (POS) Client Tier:** This tier temporarily integrates existing third-party idle devices (such as local smartphones or laptops) into the network. These "guest" nodes operate as client terminals for the Mesh-POS system, scanning NFC tokens and QR codes, and routing transaction payloads directly to the Vault via local Wi-Fi or Bluetooth RFCOMM protocols.

## **4.2 Detailed Design Explanation**

The MADN system design relies on direct hardware mapping and event-driven operational logic to minimize component count and computational overhead.

### **4.2.1 Hardware Circuit Design**

To satisfy strict cost-reduction parameters, the edge nodes were designed to route all telemetry sensors, displays, and physical inputs directly to the native GPIO pins of the Raspberry Pi Pico W, eliminating the need for complex I2C port expanders.

* **Agri-Analytics Routing:** Capacitive soil moisture sensors interface via the GP26 (ADC0) pin to capture analog voltage readouts. A DHT22 digital temperature and humidity sensor connects via a single-bus digital line to GP15, stabilized with an external 4.7kΩ pull-up resistor.  
* **Security Gateway Routing:** The HC-SR501 Passive Infrared (PIR) motion sensor outputs digital triggers to GP14. The HC-SR04 ultrasonic sensor utilizes GP16 (trigger) and GP17 (echo) to maintain virtual tripwires.  
* **User Interface & Power:** An ST7735 SPI TFT display connects via the hardware SPI0 bus (GP18-GP22). Power is regulated by a TP4056 module stepping up a 3.7V 18650 Li-Ion cell to a 5V VBUS rail, which in turn feeds the Pico W's 3.3V regulator for low-voltage components.

### **4.2.2 Operational Logic Design**

The system's logic flows through three distinct loops:

1. **Telemetry Accumulation & Inference Loop:** Edge nodes sample environmental variables, apply an arithmetic moving-average filter, and publish the data via MQTT. The Pi 4 caches these records and schedules a localized TensorFlow Lite execution to infer watering requirements without cloud dependency.  
2. **Security Trigger Loop:** A low-latency polling loop continuously monitors PIR and ultrasonic sensors. Threshold violations instantly bypass local storage constraints on the edge, pushing high-priority MQTT alert messages to the Pi 4, which immediately logs the intrusion and pushes state-change notifications.  
3. **Resilient Commerce Loop:** Designed for offline integrity, mobile POS clients submit checkout JSON payloads via WebSocket or Bluetooth SPP to the Pi 4\. The Vault evaluates balances and commits the transaction using SQLite ACID-compliant transactional locks, ensuring zero data loss during power outages.

## **4.3 Prototype Construction**

The physical construction of the MADN prototype transitioned the theoretical design into ruggedized, field-ready hardware.

### **4.3.1 Edge Node Assembly**

To ensure durability in agricultural and remote settings, standard breadboards were discarded in favor of rigid mechanical joints. 2x20-pin male short plug headers were soldered to the Raspberry Pi Pico W GPIO rails at 350°C. These were then mated into 2x20-pin female socket headers soldered onto Adafruit Terminal PiCowbell expansion boards. This stacking technique firmly secured the microcontroller while routing all active pins to spring-loaded screw terminals, allowing for rapid, solderless field swapping of broken sensor wires.

### **4.3.2 Enclosure Fabrication**

Parametric 3D modeling was executed using FreeCAD to design snap-fit, weather-resistant enclosures. The models were sliced in PrusaSlicer with a 20% gyroid infill and 3 shell perimeters for structural integrity. The enclosures were 3D printed using UV-stable PETG (Polyethylene Terephthalate Glycol) filament. The central Vault enclosure specifically incorporated ventilation ducts aligned with a dual-fan heat-sink assembly mounted on the Pi 4 CPU block to facilitate active heat extraction.

## **4.4 Integration of Components**

Hardware and software were integrated to establish a localized, self-sustaining network environment entirely independent of standard internet infrastructure.

* **Network Integration:** The Raspberry Pi 4 was configured as a standalone Wi-Fi Access Point using hostapd and dnsmasq, broadcasting the MADN-Vault-Local SSID and assigning DHCP leases to the edge nodes and mobile clients.  
* **Message Broker Integration:** A Mosquitto MQTT broker was bound to the Pi 4's local subnet on port 1883\. Edge nodes utilized the umqtt.simple package to publish JSON-formatted telemetry to distinct topics (e.g., madn/node1/telemetry or madn/node1/security).  
* **Database and Dashboarding:** InfluxDB (v2) was initialized on the Pi 4 to catch telemetry streams, which were mapped directly to Grafana. Grafana's interface was subsequently outputted via the Pi 4's HDMI port to a low-power portable projector, enabling community-facing diagnostic displays in off-grid environments.

## **4.5 Programming**

Programming the MADN required highly specialized, lightweight scripting tailored to the hardware limits of the respective tiers.

* **MicroPython Edge Scripting:** The Pico W nodes run main.py upon boot. The scripts execute asynchronous loops to poll the DHT22 and ADC pins, format variables into JSON, update the local SPI TFT display via a custom driver, and publish to the MQTT broker. Interrupt Service Routines (ISRs) were programmed for the PIR sensor to guarantee immediate alert transmission upon motion detection, bypassing the standard sleep cycles.  
* **Central Hub Daemons (Python):** Python scripts were written to run continuously as headless daemons on the Pi 4\. The *Security Event Daemon* subscribes to security topics, writing triggers directly into the SQLite database. The *POS Daemon* utilizes Python SocketServer and PyBluez to hold open WebSocket and RFCOMM channels, awaiting commerce payloads from guest phones.  
* **TensorFlow Lite Quantization:** A dense feed-forward neural network for predicting irrigation needs was trained on a workstation in standard TensorFlow/Keras. To conform to the Pi 4's processing limits and minimize latency, the model underwent post-training dynamic range quantization. This compressed the floating-point weights into 8-bit integers, shrinking the model into a highly efficient \<15KB .tflite FlatBuffer file deployed on the Pi 4's interpreter runtime.

## **4.6 Challenges Faced During Development**

Developing an edge-native framework for harsh infrastructural contexts introduced several notable engineering challenges:

1. **Thermal Throttling of the Central Orchestrator:** Initial bench testing of the Pi 4 running continuous database writes and TensorFlow inferences under simulated ambient temperatures of 38°C (mimicking Tsholotsho's dry season) caused the CPU to regularly exceed 80°C, leading to severe thermal throttling and system lockups.  
2. **Corrosive Degradation of Soil Probes:** Early iterations of the Agri-Analytics edge nodes utilized standard resistive soil moisture sensors. Due to the constant electrolysis occurring in damp, acidic soil, the metal contacts on these probes corroded entirely within a matter of weeks, rendering readings useless.  
3. **Database Corruption from Power Fluctuations:** Frequent, simulated grid dropouts mimicking the local power instability caused half-written transaction states and corrupted database journals within the Mesh-POS system during checkout executions.  
4. **Wiring Shearing in the Field:** During physical deployment simulations, standard female-to-female jumper wires connected to edge node GPIO pins easily vibrated loose or sheared off when exposed to the elements or accidentally brushed by farm equipment.

## **4.7 Solutions to Challenges**

To ensure the resilience and practical viability of the MADN prototype, the following engineering solutions were implemented:

1. **Active Cooling Integration:** Passive copper micro-heatsinks were abandoned. An active dual-fan cooling shield was wired directly to the Pi 4's 5V GPIO pins, paired with targeted exhaust ducts designed into the PETG 3D-printed enclosure. This stabilized CPU temperatures below 60°C even under maximum inference loads.  
2. **Capacitive Sensor Adoption:** Resistive probes were permanently replaced with capacitive soil moisture sensors. Because capacitive sensors measure moisture via changes in capacitance rather than direct electrical contact with the soil, they are immune to electrolysis, dramatically extending the operational lifespan in alkaline and acidic fields.  
3. **ACID and WAL Protocol Activation:** To resolve power-loss corruption, the Mesh-POS ledger was engineered using SQLite with Write-Ahead Logging (WAL) and strict ACID transactional locks. Furthermore, a 5V USB portable power bank was introduced as an inline, swappable uninterruptible power supply (UPS) buffer to handle sudden grid failures.  
4. **Terminal Block Routing:** The wiring vulnerability was eliminated by stacking the Pico W onto Adafruit Terminal PiCowbell expansion boards. All connections from external sensors were securely screwed into spring-loaded terminal blocks, providing massive mechanical strain relief and preventing accidental disconnections in rugged operational environments.