# Checkpoint Eight - Security Gateway Cost-Reduction & Alert Logic

## Description
Updating the MADN objectives, research questions, scope, significance, theoretical background, and system requirements to reflect the removal of the Camera Module and OpenCV dependency, redefining the Edge-Vision Gateway as the Edge-Alert Security Gateway, and omitting copper micro-heatsinks.

## Progress
We have successfully updated all thesis chapters in the [Version 2026-05-13 Wed 1246](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/2026-03-30%20Mon%200833%20Chapters/2026-05-13%20Wed%201220%20Version%202026-05-13%20Wed%201246) directory:
- **[1.4 Objectives of the Project.txt](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/2026-03-30%20Mon%200833%20Chapters/2026-05-13%20Wed%201220%20Version%202026-05-13%20Wed%201246/1.4%20Objectives%20of%20the%20Project.txt)**: Renamed the component to Edge-Alert Security Gateway, replacing OpenCV frame processing with lightweight trigger logic.
- **[1.5 Research Questions.txt](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/2026-03-30%20Mon%200833%20Chapters/2026-05-13%20Wed%201220%20Version%202026-05-13%20Wed%201246/1.5%20Research%20Questions.txt)**: Modified Question 3 to focus on intrusion detection and perimeter security alerts without computer vision references.
- **[1.6 Scope of the Project.txt](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/2026-03-30%20Mon%200833%20Chapters/2026-05-13%20Wed%201220%20Version%202026-05-13%20Wed%201246/1.6%20Scope%20of%20the%20Project.txt)**: Adjusted the functional boundaries to PIR/ultrasonic sensor integration and real-time state alerts.
- **[1.7 Significance of the Study.txt](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/2026-03-30%20Mon%200833%20Chapters/2026-05-13%20Wed%201220%20Version%202026-05-13%20Wed%201246/1.7%20Significance%20of%20the%20Study.txt)**: Rewrote the Public Security paragraph to center on low-power, affordable sensor-trigger alerts, bypassing the high costs and bandwidth of camera surveillance.
- **[2.2 Theoretical Background.md](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/2026-03-30%20Mon%200833%20Chapters/2026-05-13%20Wed%201220%20Version%202026-05-13%20Wed%201246/2026-05-11%200818%202.2%20Theoretical%20Background.md)**: Removed reference to OpenCV for object recognition under Embedded Machine Learning.
- **[3.3 System Requirements.md](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/2026-03-30%20Mon%200833%20Chapters/2026-05-13%20Wed%201220%20Version%202026-05-13%20Wed%201246/2026-05-27%200832%203.3%20System%20Requirements.md)**:
  - Removed the `Cam` node and `Vault --- Cam` link from the Mermaid flowchart block.
  - Renamed the subgraph from `Edge-Vision Gateway` to `Edge-Alert Security Gateway`.
  - Replaced "image logs" with "intrusion alert logs" in storage specifications.
  - Deleted the Camera Capture Interface from Swappable Value Modules.
  - Removed OpenCV from the Software Requirements table and headless OS specifications.
  - Replaced the vision-processing section with custom event-handler Python logic in the Application Logic tier.
  - Substituted Blender's camera simulation with sensor coverage simulation in the workstation requirements.
  - Removed references to copper micro-heatsinks from the active cooling system.

## Date & Time
2026-05-29 13:13

## Version 1.3.0 Qaphela
**Qaphela** is a Ndebele word that means "be alert", "pay attention", or "watch out". Imagine you are playing hide-and-seek, and your friend tells you to "watch out" because the seeker is near! *Qaphela* is like that warning. It is about keeping watch and sending a quick message when something moves, which is exactly how our new, low-cost Edge-Alert Security Gateway keeps communities safe without expensive cameras!

## Next Steps
Now that the methodology and requirements chapters are fully aligned with the cost-reduced hardware stack, we will move forward to **"3.4 System Design"**, drafting the physical block diagrams, circuit schematics, and sensor state machine flowcharts.

## Details of nature of development
Development was collaborative.
User: Peter Mthokozisi Dube (Requested further cost-reduction by removing the camera module and visual capture, shifting focus entirely to triggers and network alerting).
AI Agent Name: Antigravity (Implemented the search-and-replace updates across all chapter files, updated the Mermaid code, and documented the transition).
