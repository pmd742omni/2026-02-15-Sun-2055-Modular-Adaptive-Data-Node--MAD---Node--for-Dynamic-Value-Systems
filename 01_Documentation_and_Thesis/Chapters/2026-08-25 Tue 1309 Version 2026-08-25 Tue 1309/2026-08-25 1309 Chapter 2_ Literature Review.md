# CHAPTER 2: LITERATURE REVIEW

## 2.1 Introduction

This chapter conducts a comprehensive, multidisciplinary literature review establishing the theoretical, algorithmic, and architectural foundations of the **Modular Adaptive Data Node (MAD-Node) for Dynamic Value Systems**. The review examines the convergence of five major domains: (1) Cyber-Physical Systems (CPS) and Edge Computing Gateways, (2) Decoupled and Local-First Data Storage Architectures, (3) Human-in-the-Loop and Autonomous Agentic Operator Interfaces, (4) Behavioral Dynamics and UI/UX Paradigms of Modern Social Media Platforms (X, Instagram, Snapchat, TikTok), and (5) Resilient Multi-Currency Transaction Engines and Dynamic Economic Value Decay Models. 

By analyzing existing academic frameworks, open-source technological implementations, and contextual infrastructure realities within Sub-Saharan Africa, this review identifies fundamental limitations in current centralized paradigms and establishes the theoretical justification for MAD-Node's 4-Node Taxonomy and Phased Resource-Bootstrapping Model.

---

## 2.2 Theoretical Background

The architecture of the Modular Adaptive Data Node (MAD-Node) is built upon several foundational computing, spatial, physical, and socio-economic theories.

### 2.2.1 Cyber-Physical Systems (CPS) & Edge Gateway Architecture
Cyber-Physical Systems (CPS) represent deep integrations of computational engines, networking backbones, and physical processes [40]. In a classical CPS model, embedded computers monitor physical variables via sensors and execute physical actions via actuators, with continuous feedback loops between the physical environment and cyber control logic. 

Edge computing shifts processing tasks from centralized remote data centers directly to the edge of the local network, near data sources and end-users [1], [2], [8], [9]. In the MAD-Node framework, **Vault Nodes** serve as edge gateways that decouple physical device control from user interaction. Vault Nodes coordinate low-power microcontrollers (e.g., Raspberry Pi Pico W) communicating via lightweight protocols such as MQTT, and provide cryptographic security barriers preventing unauthorized physical manipulation of actuators (solenoids, sirens, and locks) [35], [47].

### 2.2.2 Decoupled Data Nodes & Local-First Storage Principles
Local-first software principles [41] prioritize data availability and user agency by ensuring applications read and write data directly to local storage devices, treating remote cloud networks as optional synchronization channels. 

The MAD-Node formalizes **Data Nodes** as decoupled, specialized cluster storage workers [29], [33]. By separating storage engines from gateway routing, Data Nodes can run in independent directories, distinct physical workstations, virtual machines, or containerized environments across the local subnet. Localized data integrity is maintained using SQLite with Write-Ahead Logging (`PRAGMA journal_mode=WAL;`), providing ACID transactional guarantees and supporting non-blocking concurrent readers during active write locks (`BEGIN IMMEDIATE`). Spatial indexing is accomplished using SQLite's R\*Tree virtual module, enabling sub-millisecond bounding box lookups for physical map obstacles.

### 2.2.3 Human-in-the-Loop & Agentic Operator Nodes
Modern distributed systems increasingly utilize mixed-initiative computing, where human domain experts and autonomous agentic AI assistants collaborate within shared workflow state machines [42]. In the MAD-Node taxonomy, **Operator Nodes** encompass both human actors (agronomists, security guards, merchants, customers) and autonomous background agents. Interfaces dynamically adapt to user roles via fine-grained Role-Based Access Control (RBAC), presenting tailored operational views while preserving system security through cryptographically enforced privilege boundaries (`scrypt` password derivation [47], RFC 6238 TOTP two-factor authentication, and step-up privileged elevation).

### 2.2.4 The Phased Resource-Bootstrapping Model (*Ukunciphisa*)
Capital constraints in developing economies often prevent upfront adoption of expensive cyber-physical automation [48]. The *Ukunciphisa* (Ndebele: "to reduce / optimize frugally") paradigm posits that a distributed architecture must be economically self-funding:
1. **Stage 1 (Software Foundation)**: Deploy zero-capex software applications (the VisionPro Glassmorphic Web App) on existing commodity hardware, enabling manual agricultural logging, manual security gatekeeping, localized social media, and multi-currency commercial POS transactions [7], [12], [28].
2. **Resource Generation**: Operational transactions, bandwidth vouchers, and produce sales accumulate digital value and community capital.
3. **Stage 2 (Hardware Scale-Up)**: Accumulated revenue is reinvested into fabricating and deploying specialized Cyber-Physical Nodes, automated robotic solenoids, and edge sensor arrays [19], [21], [42].

### 2.2.5 Behavioral Dynamics & UI Hybridization in Social Media
Research into user engagement on digital social platforms indicates distinct behavioral affordances across major paradigms [43], [49], [50]:
* **Microblogging & Threaded Discussions (X / Twitter)**: Optimizes rapid dissemination of factual alerts, agricultural notices, and public town-hall debates through concise, linear text streams.
* **Visual Grids & Carousels (Instagram)**: Maximizes aesthetic evaluation and marketplace browsing through structured multi-image cards, highlighting agricultural produce quality and community crafts.
* **Ephemeral Stories (Snapchat)**: Fosters daily informal participation and localized presence through 24-hour disappearing status updates, lowering the psychological friction of publishing.
* **Algorithmic Short Video Reels (TikTok)**: Drives high immersion and practical knowledge transfer through vertical, full-screen swipe video streams, ideal for farming tutorials and equipment demonstrations.

MAD-Node synthesizes these four proven UX paradigms into a unified, offline-first local social media hub, allowing off-grid communities to communicate, share knowledge, and monetize content without incurring mobile data charges [10], [14], [30].

### 2.2.6 Dynamic Value Systems & Continuous Exponential Price Decay
Perishable agricultural goods undergo biological decay over time, reducing commercial value [44]. Static pricing models lead to unsold stock spoilage and total revenue loss. The MAD-Node implements a continuous exponential price decay model:

$$P(t) = P_{\text{cost}} + (P_{\text{base}} - P_{\text{cost}}) \cdot e^{-\lambda t}$$

where $P_{\text{cost}}$ is derived from accumulated production costs (seeds, fertilizer, water, labor, logistics), $P_{\text{base}}$ is the initial retail price with target markup, and $\lambda = \frac{\ln(2)}{T_{\text{half\_life}}}$ is the decay constant based on crop shelf-life half-life $T_{\text{half\_life}}$. This mathematical engine dynamically optimizes inventory clearance, ensuring smallholder farmers recover capital before produce spoils [4], [11], [22].

### 2.2.7 RF Propagation & Spatial Ray-Tracing Models
To model local Wi-Fi mesh coverage and physical intrusion vectors across physical obstacles (silos, barns, orchards), the system incorporates the Log-Distance Path Loss Model [46]:

$$PL(d) = PL(d_0) + 10 \cdot \gamma \cdot \log_{10}\left(\frac{d}{d_0}\right) + \sum_{i} A_{\text{obstacle}, i}$$

Line-of-sight signal clearance is evaluated using the Liang-Barsky 2D line-clipping algorithm [45], and multi-node intrusion locations are triangulated via 3-point RSSI trilateration.

---

## 2.3 Review of Existing Systems and Technologies

A comparative analysis of existing distributed systems, agricultural management platforms, access control mechanisms, and social networking technologies reveals critical insights into modern architectural trends and trade-offs.

### 2.3.1 Cloud-Centric IoT Platforms vs. Edge Micro-Clouds
Commercial Internet-of-Things (IoT) platforms (e.g., AWS IoT Core, Google Cloud IoT, Microsoft Azure IoT Hub) provide robust horizontal scaling, centralized device management, and high-availability cloud telemetry ingestion [31], [36]. However, their fundamental architectural assumption is constant, high-bandwidth, and low-latency bidirectional internet connectivity. When deployed in remote African agricultural environments such as Tsholotsho, cloud-based architectures suffer from total failure modes during network blackouts, excessive cellular data uplink costs, and hidden recurring fees [13].

In response, edge micro-cloud architectures (such as Raspberry Pi-based local clusters running K3s or Docker Swarm) have been explored [9], [18], [37]. While these systems bring processing local, they frequently suffer from high software overhead, complex container orchestration requirements, and significant idle power consumption unsuitable for off-grid battery/solar operation.

### 2.3.2 Agricultural Planning & Produce Management Systems
Existing digital agricultural solutions typically fall into two categories:
1. **Commercial Farm Management Information Systems (FMIS)** (e.g., FarmERP, Climate FieldView): Comprehensive cloud-native suites designed for large industrial agribusinesses [4], [24], [25]. They require expensive monthly subscription licenses, intensive user training, and assume continuous cloud connectivity.
2. **SMS/USSD-Based Advisory Services** (e.g., EcoFarmer in Zimbabwe): Accessible on basic feature phones, but restricted to coarse, one-way regional text bulletins [10]. They cannot collect granular farm-specific soil telemetry, manage localized planting/harvest ledgers, or integrate with Point-of-Sale commerce [5], [27].

### 2.3.3 Physical Access Control & Security Logging Systems
Enterprise access management solutions rely on centralized identity providers (e.g., Active Directory, Okta) coupled with IP-connected electronic turnstiles and biometric readers [6], [23]. In rural and peri-urban facilities, such infrastructure is cost-prohibitive. Conversely, manual paper logbooks commonly used in regional Zimbabwean institutions are prone to physical degradation, lack searchable indexes, and provide zero verification against forged visitor credentials.

### 2.3.4 Decentralized Social Media & Local Content Networks
Federated and peer-to-peer social protocols (e.g., ActivityPub, Mastodon, Nostr, Scuttlebutt) have emerged to counter corporate platform centralization. While architecturally decentralized, protocols like Nostr and Mastodon still rely on globally reachable internet relays. Off-grid local-mesh media platforms (e.g., Serval Mesh, Briar) offer peer-to-peer messaging, but often lack rich visual media carousels, video reel playback, and integrated micro-monetization mechanisms necessary for vibrant community adoption [38], [39], [49].

### 2.3.5 Comparative System Summary Matrix

| System Dimension | Traditional Cloud IoT (AWS/Azure) [31], [36] | Standard Edge (K3s/Docker) [9], [37] | Manual / Paper Systems | MAD-Node Framework |
| :--- | :--- | :--- | :--- | :--- |
| **Network Dependency** | Continuous Internet Required | Local Subnet / Semi-Offline | None (Physical) | **Offline-First / Zero Internet Required [41]** |
| **Node Taxonomy** | Monolithic Cloud + Dumb Edge | Virtualized Containers | Unstructured Human | **Decoupled 4-Node Functional Taxonomy** |
| **Deployment Model** | High Upfront Capex + Opex [13] | Moderate Capex + High Setup | Low Capex / High Error Rate | **Phased Bootstrapping (*Ukunciphisa*) [48]** |
| **Multi-Currency POS** | Cloud Gateway (Stripe/PayPal) | Third-Party API Integration | Cash Only (Unreconciled) | **Local Tri-Ledger (USD / ZAR / ZWG)** |
| **Produce Pricing** | Static / Manual Catalog | Static Database Values | Arbitrary Bargaining | **Dynamic Continuous Exponential Decay [44]** |
| **Power Consumption** | Enterprise Server Power | $>15\text{W}$ (Multi-SBC Cluster) | $0\text{W}$ | **$<5.1\text{W}$ Peak (Pi 4 + Pico W Nodes)** |

---

## 2.4 Contextual Challenges

Designing a dependable distributed computing system for Matabeleland North and Bulawayo requires confronting acute socio-technical and environmental realities:

1. **Electrical Grid Instability & Load Shedding**: Scheduled and unscheduled electrical grid dropouts frequently exceed 12 to 18 hours per day in Bulawayo and peri-urban districts. Distributed nodes must operate on low-power DC battery systems (e.g., 3.7V 18650 Li-Ion cells boosted to 5V via TP4056 modules) and execute non-blocking ACID transactions that withstand sudden power loss without SQLite journal corruption [35].
2. **Extreme Thermal Environments**: Ambient summer temperatures in Tsholotsho regularly reach $38^\circ\text{C}$ to $42^\circ\text{C}$. Fanless single-board computers (such as the Raspberry Pi 4 Model B) running continuous database writes and ML inferences rapidly throttle above $80^\circ\text{C}$ unless equipped with targeted dual-fan active cooling and parametric exhaust enclosures.
3. **Telecommunications Tariff Barriers**: Mobile data bandwidth in Zimbabwe is among the most expensive in Southern Africa relative to average household income [10], [14], [30]. Systems requiring continuous cloud synchronization impose an unsustainable recurring operational cost on farmers, schools, and small enterprises [13].
4. **Multi-Currency Monetary Complexity**: Due to historical hyperinflation and currency reforms, daily commerce in Zimbabwe operates simultaneously across multiple currencies: the United States Dollar (USD - primary accounting base), the South African Rand (ZAR - regional trade), and Zimbabwe Gold (ZWG - national sovereign currency). Transaction systems must support mixed-tender split payments (e.g., paying partially in USD cash and partially in ZAR, with change returned in ZWG) using dynamic, configurable exchange multipliers [7], [12].
5. **Harsh Soil Chemistry**: Sandy loam and acidic soils across Matabeleland accelerate galvanic corrosion and electrolysis on standard resistive soil moisture probes, necessitating solid-state capacitive probes and strain-relieved screw-terminal wiring [5], [25].

---

## 2.5 Gaps in Existing Solutions

A synthesis of the reviewed literature reveals five profound research and technological gaps:

1. **Lack of a Unified 4-Node Functional Taxonomy**: Existing edge IoT literature treats nodes either as monolithic central servers or dumb microcontrollers. There is an absence of a formalized architectural model that distinctly decouples **Operator Nodes** (human/agentic interaction), **Vault Nodes** (cryptographic gateway orchestration), **Data Nodes** (independent storage workers), and **Cyber-Physical Nodes** (hardware sensing/actuation).
2. **Absence of Cross-Machine Zero-Configuration Storage Discovery**: Current distributed storage engines (e.g., Ceph, MinIO, Cassandra) require complex network configuration, static IP topologies, or cloud DNS. There is no lightweight, zero-configuration protocol allowing Data Nodes running in separate directories or physical workstations to be dynamically discovered by local Vault gateways via mDNS/UDP multicast.
3. **Failure to Address Perishable Value Decay in Rural Systems**: Standard supply chain software assumes static pricing or relies on manual merchant discounts. There is a lack of integrated mathematical price decay engines ($P(t) = P_{\text{cost}} + (P_{\text{base}} - P_{\text{cost}})e^{-\lambda t}$) operating directly on localized edge ledgers to maximize smallholder harvest monetization.
4. **Lack of Multi-Domain Synthesis in Offline-First Architecture**: Existing offline systems are siloed—either handling messaging, agricultural sensing, or POS transactions in isolation. None synthesize social media engagement (X/Instagram/Snapchat/TikTok hybrid UX), agricultural lifecycle tracking, perimeter security logging, and multi-currency enterprise commerce into a unified local micro-cloud.
5. **Absence of a Phased Self-Funding Deployment Methodology**: Most IoT research assumes full upfront capital expenditure. There is an absence of a verified phased model (*Ukunciphisa*) demonstrating how zero-capex software tools (Stage 1) can generate economic resources to systematically fund Cyber-Physical hardware automation (Stage 2).

---

## 2.6 Implications for MADN Design

The findings and gaps identified in this literature review directly establish the engineering specifications and architectural decisions for the MAD-Node framework:

1. **Adoption of the 4-Node Taxonomy**: The MAD-Node must be explicitly partitioned into Operator, Vault, Data, and Cyber-Physical tiers, ensuring modular separation of concerns, multi-platform portability, and strict security isolation.
2. **Decoupled Cross-Folder / Cross-Machine Storage Protocol**: Data Nodes must be designed to execute independently on any local folder, workstation, or VM, broadcasting JSON discovery beacons (`224.0.0.251:8001` or mDNS `_madn-data._tcp.local`) for seamless Vault pairing.
3. **Phased Bootstrapping Implementation (*Ukunciphisa*)**:
   - **Stage 1 (Software Core)**: Prioritize the Glassmorphic Web Application (SPA) on existing consumer devices, featuring manual agriculture tracking (planting/harvest mass/disposition splits), manual visitor gatekeeping, hybrid social feeds, and Composable Enterprise RBAC with dynamic decay pricing.
   - **Stage 2 (Scale-Up Hardware)**: Schedule automated Cyber-Physical Pico W nodes, Liang-Barsky ray tracing, 3-point RSSI trilateration, and robotic solenoid valves as revenue-funded upgrades.
4. **Multi-Currency Tri-Ledger Engine**: Implement native support for USD base accounting, ZAR conversions, and ZWG change calculation to withstand monetary volatility in Zimbabwe.
5. **Local-First Zero-Internet Autonomy**: Rely exclusively on local Wi-Fi hotspots (Hostapd), MQTT brokers (Mosquitto), and SQLite Write-Ahead Logging (WAL), completely eliminating cloud dependencies.

---

## 2.7 Summary of Literature Review

This literature review surveyed foundational and contemporary research across edge computing architectures, local-first data paradigms, human-in-the-loop agentic systems, social media UX dynamics, and perishable supply chain economics. The analysis demonstrated that while individual technologies exist in isolation, current solutions fail to address the compounding infrastructure vulnerabilities of Sub-Saharan Africa—characterized by severe load shedding, expensive cellular bandwidth, extreme ambient temperatures, and multi-currency volatility.

By synthesizing these theoretical pillars into a novel 4-Node Functional Taxonomy, integrating continuous exponential price decay mathematics, and establishing the *Ukunciphisa* phased deployment methodology, the MAD-Node framework bridges the critical gap between academic cyber-physical systems theory and resilient, real-world community implementation.

---

## 2.8 Bibliography

1. E. Ahmed, A. Ahmed, I. Yaqoob, J. Shuja, A. Gani, M. Imran, and M. Shoaib, "Bringing Computation Closer toward the User Network: Is Edge Computing the Solution?," *IEEE Communications Magazine*, vol. 55, no. 11, pp. 138–144, Nov. 2017, doi: 10.1109/MCOM.2017.1700120.
2. T. Taleb, K. Samdanis, B. Mada, H. Flinck, S. Dutta, and D. Sabella, "On Multi-Access Edge Computing: A Survey of the Emerging 5G Network Edge Cloud Architecture and Orchestration," *IEEE Communications Surveys & Tutorials*, vol. 19, no. 3, pp. 1657–1681, 2017, doi: 10.1109/COMST.2017.2705720.
3. M. Y. Arslan, I. Singh, S. Singh, H. V. Madhyastha, K. Sundaresan, and S. V. Krishnamurthy, "Computing while Charging: Building a Distributed Computing Infrastructure Using Smartphones," in *Proc. 8th Int. Conf. Emerging Netw. Experiments Technol. (CoNEXT)*, Nice, France, Dec. 2012, pp. 193–204, doi: 10.1145/2413176.2413199.
4. L. Tan, "Cloud-based Decision Support and Automation for Precision Agriculture in Orchards," *IFAC-PapersOnLine*, vol. 49, no. 16, pp. 330–335, 2016, doi: 10.1016/j.ifacol.2016.10.061.
5. S. R. Schultze, M. N. Campbell, S. Walley, K. Pfeiffer, and B. Wilkins, "Exploration of Sub-Field Microclimates and Winter Temperatures: Implications for Precision Agriculture," *International Journal of Biometeorology*, vol. 65, no. 7, pp. 1043–1052, Jul. 2021, doi: 10.1007/s00484-021-02086-0.
6. A. C. Cob-Parro, C. Losada-Gutiérrez, M. Marrón-Romera, A. Gardel-Vicente, and I. Bravo-Muñoz, "Smart Video Surveillance System Based on Edge Computing," *Sensors*, vol. 21, no. 9, Art. no. 2958, Apr. 2021, doi: 10.3390/s21092958.
7. G. T. Li and L. K. Lau, "Mobile Point of Sales System with Cloud-Based Inventory Management for Micro and Small Enterprises," in *Proc. World Congr. Eng. Comput. Sci. (WCECS)*, San Francisco, CA, USA, Oct. 2015, pp. 664–669.
8. K.-D. Kang, D. S. Menascé, G. Küçük, T. Zhu, and P. Yi, "Edge Computing in the Internet of Things," *International Journal of Distributed Sensor Networks*, vol. 13, no. 11, Art. no. 1550147717732446, Nov. 2017, doi: 10.1177/1550147717732446.
9. M. Satyanarayanan, P. Bahl, R. Cáceres, and N. Davies, "The Case for VM-Based Cloudlets in Mobile Computing," *IEEE Pervasive Computing*, vol. 8, no. 4, pp. 14–23, Oct.–Dec. 2009, doi: 10.1109/MPRV.2009.82.
10. S. Hove, "Zimbabwe’s Mobile Penetration Rate Surges to 116.37% as Active Mobile Subscriptions Rise to 18.91 Million," *TechZim*, Sept. 30, 2024.
11. J. Everingham, J. Sexton, D. Skocaj, and H. Inman-Bamber, "Accurate Prediction of Sugarcane Yield Using a Random Forest Algorithm," *Agronomy for Sustainable Development*, vol. 36, no. 2, Art. no. 27, May 2016, doi: 10.1007/s13593-016-0364-z.
12. S. Kochar, H. Nikam, R. Tripathi, and A. Vidhate, "Offline Transaction System," *ITM Web of Conferences*, vol. 44, Art. no. 03072, 2022, doi: 10.1051/itmconf/20224403072.
13. K. M. Khan, J. Han, and H. K. Zhang, "Hidden Costs in Cloud Computing," in *Proc. IEEE 6th Int. Conf. Cloud Comput.*, Santa Clara, CA, USA, June–July 2013, pp. 652–659, doi: 10.1109/CLOUD.2013.97.
14. Freedom House, "Freedom on the Net 2024: Zimbabwe," Washington, DC, USA, 2024.
15. S. M. Otero Corrales and K. Fach Gomez, "Volunteer Computing for Scalability in Fog-Computing Systems: A Systematic Review," *PeerJ Computer Science*, vol. 10, Art. no. e2542, 2024, doi: 10.7717/peerj-cs.2542.
16. A. Al-Hawawreh, M. C. Yuen, A. Shahabi, Y. Ma, M. Moh, and T.-S. Moh, "A Decentralized Collaborative Framework for Scalable Edge AI: A Systematic Approach," *Sensors*, vol. 24, no. 1, Art. no. 236, Jan. 2024, doi: 10.3390/s24010236.
17. J. Chen and X. Ran, "Deep Learning with Edge Computing: A Review," *Proceedings of the IEEE*, vol. 107, no. 8, pp. 1655–1674, Aug. 2019, doi: 10.1109/JPROC.2019.2921977.
18. G. Rjoub, O. A. Wahab, J. Bentahar, and A. A. Bataineh, "Distributed Data Stream Processing and Edge Computing: A Survey on Resource Elasticity and Future Directions," *Sensors*, vol. 21, no. 16, Art. no. 5348, Aug. 2021, doi: 10.3390/s21165348.
19. E. E. Ogiemwonyi, M. Bodunde, O. O. Obe, and V. O. Matthews, "On-Device AI for Climate-Resilient Farming: Lightweight Models on Smart Agricultural Devices," *Scientific Reports*, vol. 15, Art. no. 18745, 2025, doi: 10.1038/s41598-025-03389-z.
20. M. Singha and S. K. Das, "Real-Time and Accurate Object Detection on Edge Device with TensorFlow Lite," *Journal of Physics: Conference Series*, vol. 1651, no. 1, Art. no. 012114, Oct. 2020, doi: 10.1088/1742-6596/1651/1/012114.
21. S. Kumar, A. A. Khan, K. P. Singh, and T. Shankar, "Advancing Smart Systems with TinyML: A Review of Applications, Challenges, and Future Prospects," *IEEE Access*, vol. 13, pp. 1924–1954, 2025, doi: 10.1109/ACCESS.2024.3525393.
22. P. K. Sethy, A. Kumar Barik, and S. K. Rath, "A Cloud Enabled Crop Recommendation Platform for Machine Learning Driven Precision Farming," *Computers and Electronics in Agriculture*, vol. 216, Art. no. 108527, Jan. 2024, doi: 10.1016/j.compag.2023.108527.
23. H. Xu, L. Wang, Z. Liu, and Y. Li, "A Privacy-Preserving Video Surveillance System Based on Edge Computing," *IEEE Access*, vol. 9, pp. 112055–112067, 2021, doi: 10.1109/ACCESS.2021.3103010.
24. S. S. Gill, M. Xu, P. Garraghan, R. Bahsoon, A. K. Kar, S. Kaddoum, T. Baker, and O. Rana, "Edge Computing for Smart Agriculture: Opportunities, Challenges, and Future Directions," *IEEE/CAA Journal of Automatica Sinica*, vol. 9, no. 5, pp. 908–929, May 2022, doi: 10.1109/JAS.2022.105690.
25. B. Ahmed, H. Shabbir, S. R. Naqvi, and L. Peng, "Smart Agriculture: Current State, Opportunities and Challenges," *IEEE Access*, vol. 12, pp. 140762–140802, 2024, doi: 10.1109/ACCESS.2024.3471647.
26. G. S. Aujla, A. Singh, S. K. Garg, K. K. R. Choo, and R. Buyya, "Distributed Intelligence for Edge-to-Cloud Computing: A Systematic Review," *ACM Computing Surveys*, vol. 56, no. 10, Art. no. 253, 2024, doi: 10.1145/3649449.
27. A. R. Matin, S. Kamal, M. M. U. Rathore, T. Amgoth, and G. Srivastava, "A Review of Smart Agriculture Using Internet of Things, Artificial Intelligence, and Computer Vision," *Sensors*, vol. 22, no. 23, Art. no. 9309, Dec. 2022, doi: 10.3390/s22239309.
28. J. C. West, "Why Your Company Needs More Mobile Apps," *Engineering Management Review*, vol. 43, no. 2, pp. 12–15, June 2015, doi: 10.1109/EMR.2015.2437354.
29. H. Cui and A. R. Butt, "The Challenge of Exploiting Idle System Resources in a Virtually Integrated End-to-End Computing Environment," in *Proc. USENIX Conf. File Storage Technol. (FAST)*, San Jose, CA, USA, Feb. 2007, pp. 33–48.
30. Postal and Telecommunications Regulatory Authority of Zimbabwe (POTRAZ), "Third Quarter 2024 Abridged Sector Performance Report," Harare, Zimbabwe, 2025.
31. F. C. Andriulo, M. Fiore, M. Mongiello, E. Traversa, and V. Zizzo, "Edge Computing and Cloud Computing for Internet of Things: A Review," *Informatics*, vol. 11, no. 4, Art. no. 71, Sept. 2024, doi: 10.3390/informatics11040071.
32. M. E. Hirsch, C. Mateos, and A. Zunino, "Augmenting Computing Capabilities at the Edge by Jointly Exploiting Mobile Devices: A Survey," *Future Generation Computer Systems*, vol. 88, pp. 644–662, Nov. 2018, doi: 10.1016/j.future.2018.06.005.
33. D. Rosendo, A. Costan, P. Valduriez, and G. Antoniu, "Distributed Intelligence on the Edge-to-Cloud Continuum: A Systematic Literature Review," *Journal of Parallel and Distributed Computing*, vol. 166, pp. 71–94, Aug. 2022, doi: 10.1016/j.jpdc.2022.04.004.
34. H.-L. Truong, T. Truong-Huu, and T.-D. Cao, "Making Distributed Edge Machine Learning for Resource-Constrained Communities and Environments Smarter: Contexts and Challenges," *Journal of Reliable Intelligent Environments*, vol. 9, pp. 119–134, June 2023, doi: 10.1007/s40860-022-00176-3.
35. S. Bagchi, M.-B. Siddiqui, P. Wood, and H. Zhang, "Dependability in Edge Computing," *Communications of the ACM*, vol. 63, no. 1, pp. 58–66, Jan. 2020, doi: 10.1145/3364118.
36. P. Mell and T. Grance, "The NIST Definition of Cloud Computing," NIST Special Publication 800-145, Gaithersburg, MD, USA, Sept. 2011, doi: 10.6028/NIST.SP.800-145.
37. D. Balouek-Thomert, E. G. Renart, A. R. Zamani, A. Simonet, and M. Parashar, "Towards a Computing Continuum: Enabling Edge-to-Cloud Integration for Data-Driven Workflows," *The Journal of Supercomputing*, vol. 76, pp. 9020–9044, Nov. 2020, doi: 10.1007/s11227-019-03102-3.
38. G. Dosi, "Technological Paradigms and Technological Trajectories: A Suggested Interpretation of the Determinants and Directions of Technical Change," *Research Policy*, vol. 11, no. 3, pp. 147–162, June 1982, doi: 10.1016/0048-7333(82)90016-6.
39. M. de Reuver, C. Sørensen, and R. C. Basole, "The Digital Platform: A Research Agenda," *Journal of Information Technology*, vol. 33, no. 2, pp. 124–135, June 2018, doi: 10.1057/s41265-016-0033-3.
40. E. A. Lee, "Cyber Physical Systems: Design Challenges," in *11th IEEE International Symposium on Object and Component-Oriented Real-Time Distributed Computing (ISORC)*, Orlando, FL, USA, 2008, pp. 363–369, doi: 10.1109/ISORC.2008.25.
41. M. Kleppmann, A. Wiggins, P. van Hardenberg, and M. McGranaghan, "Local-First Software: You Own Your Data, in Spite of the Cloud," in *Proc. ACM SIGPLAN Int. Symp. New Ideas, New Paradigms, and Reflections on Programming and Software (Onward!)*, Athens, Greece, 2019, pp. 154–178, doi: 10.1145/3359591.3359737.
42. E. Horvitz, "Principles of Mixed-Initiative User Interfaces," in *Proc. SIGCHI Conf. Human Factors in Computing Systems (CHI)*, Pittsburgh, PA, USA, 1999, pp. 159–166, doi: 10.1145/302979.303030.
43. J. H. Kietzmann, K. Hermkens, I. P. McCarthy, and B. S. Silvestre, "Social Media? Get Serious! Understanding the Functional Building Blocks of Social Media," *Business Horizons*, vol. 54, no. 3, pp. 241–251, May–June 2011, doi: 10.1016/j.bushor.2011.01.005.
44. J. Blackburn and G. Scudder, "Supply Chain Strategies for Perishable Products: The Case of Fresh Produce," *Production and Operations Management*, vol. 18, no. 2, pp. 129–137, Mar.–Apr. 2009, doi: 10.1111/j.1937-5956.2009.01016.x.
45. Y. D. Liang and B. A. Barsky, "A New Concept and Method for Line Clipping," *ACM Transactions on Graphics (TOG)*, vol. 3, no. 1, pp. 1–22, Jan. 1984, doi: 10.1145/357332.357333.
46. T. S. Rappaport, *Wireless Communications: Principles and Practice*, 2nd ed. Upper Saddle River, NJ, USA: Prentice Hall, 2002.
47. C. Percival, "Stronger Key Derivation via Sequential Memory-Hard Functions," in *Proc. BSDCan '09*, Ottawa, Canada, May 2009.
48. World Bank, *World Development Report 2021: Data for Better Lives*. Washington, DC, USA: World Bank, 2021, doi: 10.1596/978-1-4648-1600-0.
49. K. Kapoor, A. Z. Bigdeli, Y. K. Dwivedi, A. Schroeder, A. Beltagui, and T. Baines, "A Socio-Technical View of Platform Ecosystems: Systematic Review and Research Agenda," *Journal of Business Research*, vol. 128, pp. 94–108, May 2021, doi: 10.1016/j.jbusres.2021.01.060.
50. M. G. Jacobides, A. Cennamo, and A. Gawer, "The Value and Structuring Role of Web APIs in Digital Innovation Ecosystems: The Case of the Online Travel Ecosystem," *Research Policy*, vol. 53, no. 1, Art. no. 104931, Jan. 2024, doi: 10.1016/j.respol.2023.104931.
