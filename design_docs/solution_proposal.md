# Hospital Urine Drainage Bag Monitoring System - Solution Proposal

## 1. Executive Summary
This document proposes an optimized solution for the "Intelligent Monitoring Device for Hospital Urine Drainage Bag Volume". The original proposal (BLE + Wi-Fi Gateway) faces challenges regarding signal interference, gateway density, and battery maintenance in a high-density hospital environment. 

**Key Improvements:**
*   **Connectivity:** Switch from **BLE** to **Sub-1GHz (LoRaWAN or Proprietary 915/868 MHz)**.
*   **Infrastructure:** Reduce gateway count from "one per room" to "one per ward/floor".
*   **Sensing:** Stick with **Load Cell (Weight)** for compatibility but implement **Capacitive Sensing** for a next-gen "smart sticker" variant.

## 2. Comparison: Current vs. Proposed

| Feature | Current Idea (BLE + Wi-Fi) | Proposed Solution (Sub-1GHz + Load Cell) |
| :--- | :--- | :--- |
| **Frequency** | 2.4 GHz | Sub-1GHz (e.g., 868/915 MHz) |
| **Interference** | **High** (Wi-Fi, Zigbee, Medical Equip.) | **Low** (Separate from critical Wi-Fi) |
| **Range** | Short (~10-30m) | Long (Hundreds of meters indoor) |
| **Gateway Count** | High (1 per room recommended) | **Low** (1 per ward/floor can handle 1000+ nodes) |
| **Battery Life** | Moderate | **Extended** (Lower transmission power for range) |
| **Cost** | High infra cost (many gateways) | **Lower infra cost** (fewer gateways) |

## 3. Detailed Technical Architecture

### A. Bedside Monitoring Unit (The "Node")
*   **Sensor:** 
    *   *Primary:* **Strain Gauge (Load Cell)**. Robust, works with any standard bag.
    *   *Optimization:* Design the enclosure to clip onto standard bed rails with a retractable hook to minimize profile.
    *   *Alternative:* **Capacitive Level Strip**. A disposable or reusable adhesive strip. Benefits: No mechanical parts, extremely low profile. Drawbacks: Specific to bag geometry.
*   **Microcontroller:** Ultra-low power MCU (e.g., STM32L4 series or TI CC13xx).
*   **Radio:** Sub-1GHz Transceiver (LoRa or FSK). 
    *   *Why:* Penetrates walls easily; avoids the crowded 2.4GHz spectrum used by hospital Wi-Fi and monitoring equipment.
*   **Power:** Li-ion rechargeable or Replaceable AA batteries (2+ years life).
*   **User Interface:** E-Ink Display (Low power, high visibility) or simple LED indicators.

### B. The Gateway (The "Hub")
*   **Radio:** Sub-1GHz Concentrator (8-channel LoRaWAN or Proprietary).
*   **Uplink:** Wi-Fi / Ethernet (PoE preferred for reliability) / Cellular (LTE-M as backup).
*   **Capacity Analysis (High Density Scenario):** 
    *   *Scenario A (Standard):* 100 beds, reporting every **1 hour**.
        *   Load: 100 packets/hour.
        *   Utilization: < 0.2% of gateway capacity.
    *   *Scenario B (Stress Test - Client Request):* 100 beds, reporting every **10 minutes**.
        *   Traffic Load: 100 devices × 6 packets/hour = **600 packets/hour** (10 packets/minute).
        *   *Capability:* A standard 8-channel gateway handles ~60,000+ packets/hour.
        *   *Conclusion:* Even at 10-minute intervals, the network load is **~1%** of the gateway's maximum. The system is "bored" and can easily scale further or handle frequent alarm spikes.

## 4. Functional Workflow
1.  **Measurement:** Device wakes up every minute to sample weight.
2.  **Filtering:** Algorithms filter out "bed shaking" or "patient movement" artifacts.
3.  **Reporting:** 
    *   *Routine:* Transmits volume data once per hour.
    *   *Alarm:* Transmits **immediately** if:
        *   Volume > Threshold (e.g., 80% full).
        *   No flow detected for X hours (potential blockage).
        *   Sudden weight drop (leak/emptied).
4.  **Server:** Central dashboard shows status of all beds in the ward.
5.  **Integration:** HL7/FHIR interface to push data to the Hospital Information System (HIS).

## 5. Cost Analysis (Per 25-Bed Ward)

A direct cost comparison between the two architectures reveals significant savings with the Sub-1GHz approach, primarily driven by infrastructure reduction.

| Item | Option A: BLE + Wi-Fi (Original) | Option B: Sub-1GHz (Proposed) | Notes |
| :--- | :--- | :--- | :--- |
| **Node Hardware** | ~$15.00 / unit | ~$7.00 / unit | *STM32WLE5 SoC reduces BOM cost vs discrete BLE+MCU modules.* |
| **Node Total (25 beds)** | $375.00 | $175.00 | |
| **Gateway Unit Cost** | ~$30.00 (Simple Bridge) | ~$200.00 (Commercial Indoor) | *LoRa gateway is more expensive per unit, but...* |
| **Gateway Quantity** | 25 (1 per room) | 1 (1 per ward) | *...you only need ONE.* |
| **Gateway Total** | **$750.00** | **$200.00** | |
| **Installation (Labor)** | High (25 power outlets, 25 setups) | Low (1 central setup) | *Estimated 10x labor savings.* |
| **Total Hardware Cost** | **~$1,125.00** | **~$375.00** | **~66% Hardware Savings** |

### Economic Conclusion
The **Sub-1GHz solution is ~3x cheaper** in initial hardware capability. 
*   **Infrastructure Savings:** $550 per ward.
*   **Device Savings:** $200 per ward.
*   **Hidden Savings:** drastically reduced IT management (25 IP addresses vs 1 IP address per ward).

## 6. Why this is better
1.  **Reliability:** Sub-1GHz is far less likely to drop connections in a hospital filled with Wi-Fi signals.
2.  **Maintenance:** Fewer gateways mean fewer points of failure and less IT management overhead.
3.  **Scalability:** Easier to deploy. Just plug in one gateway at the nurses' station and deploy nodes in rooms.
