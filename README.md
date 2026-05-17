# Hospital Urine Bag Monitoring System (LoRaWAN)


[![Paid_IoT_Review](https://img.shields.io/badge/Paid_IoT_Review-brightgreen)](https://x2.brucelu.top/iot/checkout/?source=github-badge-lora-weight-device) [![Ask_First](https://img.shields.io/badge/Ask_First-blue)](https://x2.brucelu.top/products/contact/?offer=iot&source=github-badge-lora-weight-device) [![Sample](https://img.shields.io/badge/Sample-informational)](https://x2.brucelu.top/iot/sample/)

## Project Overview
A low-power, connected IoT device designed to automatically monitor urine output in hospital wards. It replaces manual visual checks with real-time digital logging, improving patient care and reducing nurse workload.

**Key Features:**
*   **Sensing:** Weight-based (Load Cell) for non-contact, universal bag compatibility.
*   **Connectivity:** **LoRaWAN** (Sub-1GHz) for deep indoor penetration and low infrastructure cost (1 gateway per ward).
*   **Battery Life:** Multi-year operation on AA batteries or Li-SoCl2.
*   **User Interface:** E-Ink Display for always-on visibility and local "Tare" button.
*   **Infrastructure:** Supports both **PoE** and **Wi-Fi** backhaul for the Gateway.

## Repository Structure

### Design Documents (`design_docs/`)
*   **`system_architecture.md`**: High-level topology, data flow, and server stack (ChirpStack).
*   **`hardware_design.md`**: Schematic concepts, chip selection (RAK3172, HX711), and detailed pin mapping.
*   **`mechanical_design.md`**: Enclosure styling, IP65 sealing, and the miniature load cell integration (Hook mechanism).
*   **`firmware_design.md`**: Software logic, state machine (Deep Sleep), and LoRaWAN payload format.
*   **`pcb_layout_guide.md`**: Critical routing rules for RF impedance and Analog noise reduction.
*   **`detailed_bom.md`**: Bill of Materials with part numbers and cost estimates.
*   **`solution_proposal.md`**: original proposal.

### Datasheets (`datasheets/`)
Contains reference specifications for critical components:
*   **RAK3172**: LoRaWAN Module.
*   **GDEY0213B74**: 2.13" E-Ink Display.
*   **HX711**: 24-Bit ADC.
*   **SSD1680**: Display Controller (Command Table).

## Getting Started

### 1. Hardware Development
*   Review `hardware_design.md` for the schematic connectivity.
*   Follow `pcb_layout_guide.md` for board layout, paying special attention to the **50Ω RF Trace** and **E-Ink Booster** loop.
*   Ensure the **Schottky Diode OR-ing** is implemented to protect the 3.3V rail.

### 2. Firmware Development
*   **Toolchain:** STM32CubeWL SDK + CMake + GCC ARM.
*   **Key Logic:** Implement the "Deep Sleep Loop" (Wait 400ms for HX711 -> Read -> Sleep).
*   **Display:** Use the SSD1680 driver with the specific bias voltages (+20V/-20V/+15V/-15V) defined in the hardware spec.

### 3. Mechanical Prototyping
*   Design the enclosure to fit the **Miniature Load Cell** (40mm).
*   Ensure the **Tube Retention Clip** is molded into the front shell to prevent measurement errors.

## License
Proprietary / Internal Company Use.

## Commercial support

For teams adapting this repo for ESP32, Bluetooth, Wi-Fi provisioning, LoRa/LoRaWAN, low-power sensing, gateway handoff, or prototype-to-pilot embedded device work, I offer a paid bring-up review:

- Review page: https://x2.brucelu.top/iot/?source=github-lora-weight-device
- Sample deliverable: https://x2.brucelu.top/iot/sample/
- Checkout: https://x2.brucelu.top/iot/checkout/?source=github-lora-weight-device
- Product catalog: https://x2.brucelu.top/products/?source=github-lora-weight-device

Boundary: this is paid engineering review/support. It does not include medical/regulatory approval, guaranteed RF range, hardware repair, credential-managed operation, or custom firmware delivery.
