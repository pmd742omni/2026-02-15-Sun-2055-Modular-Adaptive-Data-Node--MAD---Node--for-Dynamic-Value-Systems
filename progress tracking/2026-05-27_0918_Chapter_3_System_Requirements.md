# Checkpoint Seven - Chapter 3.3 System Requirements

## Description
Drafting and refining the complete system requirements specifications (covering all hardware components, sensor systems, local-first software, and workstation design toolchains) for Chapter 3.3 of the MADN research.

## Progress
We have successfully developed, refined, and saved the content for **Chapter 3.3**: [2026-05-27 0832 3.3 System Requirements.md](file:///c:/Users/ignaz/OneDrive/Documents/Projects/2026-02-15%20Sun%202055%20Modular%20Adaptive%20Data%20Node%20%28MAD%20-%20Node%29%20for%20Dynamic%20Value%20Systems/2026-03-30%20Mon%200833%20Chapters/2026-05-13%20Wed%201220%20Version%202026-05-13%20Wed%201246/2026-05-27%200832%203.3%20System%20Requirements.md):
- Established the hardware requirements divided into three functional tiers: Central Orchestration (Pi 4 with a 128GB MicroSD card and portable projector), Edge Sensing (Pico W and screw terminal shield), and Swappable Modules (Agri, Security, and POS).
- Coded an elegant **Mermaid hardware diagram** modeling the physical ecosystem, including the newly clarified Camera Module link.
- Resolved the architectural separation between physical triggers (PIR and ultrasonic sensors on the Pico W) and the camera pipeline (processed on the Pi 4 via OpenCV contour and frame analysis triggered by MQTT state changes).
- Specified all software layers, database solutions (InfluxDB and SQLite), visualization tools (Grafana), application intelligence runtimes (TensorFlow Lite and OpenCV), and CAD workstation software (FreeCAD, KiCAD, Blender, and Inkscape).

## Date & Time
2026-05-27 09:18

## Version 1.2.0 Izidingo
**Izidingo** is a Ndebele word that means "needs" or "requirements". Think of it like a recipe for a cake. Before you start mixing, you need to write down all the ingredients—like flour, sugar, and eggs. *Izidingo* is that exact list of ingredients, but for our computer project, showing exactly what hardware parts and software tools we need to make it work!

## Next Steps
Now that the system requirements are formalized, we will proceed to **"3.4 System Design (Block Diagrams, Circuit Diagrams, Flowcharts, etc.)"**. We will design systemic layouts showing how the components wired in the requirements map physically and how data flows step-by-step through our modules.

## Details of nature of development
Development was collaborative.
User: Peter Mthokozisi Dube (Identified critical omissions like the 128GB MicroSD and portable projector, clarified the OpenCV video-input constraints, and directed the shift to a Mermaid diagram).
AI Agent Name: Antigravity (Drafted the chapter text, refined the architectural roles of sensors and cameras, and structured the Mermaid flowchart).
