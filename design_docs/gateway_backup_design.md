# Backup Gateway Design (Plan B)

> **⚠️ WARNING: UNVERIFIED DESIGN**
> This design proposal (Plan B) lacks validating datasheets for the core components (**ESP32-S3** and **RAK5146**) in the project repository. It serves as a conceptual backup only. The primary, validated solution is the **RAK7268V2 Commercial Gateway** (see `system_architecture.md` and `datasheets/rak7268v2_datasheet.md`). Implementation of this custom gateway should not proceed without full component validation.

## 1. Objective
To provide a proprietary, cost-effective custom gateway design as a backup to the commercial RAK7268V2. This design focuses on component availability and stripped-down functionality (LoRaWAN Packet Forwarder only).

## 2. Architecture
A **"Hybrid-Gateway"** architecture: High-performance ESP32-S3 drives a standard LoRaWAN Concentrator.

*   **Host Processor:** **Espressif ESP32-S3-WROOM-1-N8R2** (8MB Flash, 2MB PSRAM).
    *   *Interfaces:* SPI (LoRa), SPI/RMII (Ethernet), USB (Debug/Power).
*   **LoRa Concentrator:** **RAK5146** (SPI Version, SX1303).
    *   *Connector:* Standard Mini-PCIe.
*   **Ethernet:** **WIZnet W5500** (SPI) or **LAN8720** (RMII). *Selection: W5500 for simpler SPI routing.*

## 3. Power Design (Critical)
The SX1303 Concentrator bursts up to **500mA**. A standard LDO is insufficient.
*   **Input:** USB-C (5V).
*   **Regulation:** **Buck Converter** (Step-Down) to 3.3V.
    *   **Chip:** **MPS MP2359** (1.2A High Efficiency).
    *   **Inductor:** 4.7uH Shielded Power Inductor.
    *   **Capacitors:** 22uF Ceramic on Input and Output.

## 4. Pin Mapping (ESP32-S3)

| ESP32 Pin | Function | Connection |
| :--- | :--- | :--- |
| **GPIO 1** | SPI_MOSI | **RAK5146 MOSI** & **W5500 MOSI** |
| **GPIO 2** | SPI_MISO | **RAK5146 MISO** & **W5500 MISO** |
| **GPIO 3** | SPI_CLK | **RAK5146 SCLK** & **W5500 SCLK** |
| **GPIO 4** | GPIO | **RAK5146 CS#** (Chip Select) |
| **GPIO 5** | GPIO | **W5500 CS#** (Chip Select) |
| **GPIO 6** | GPIO | **RAK5146 RST** (Reset) |
| **GPIO 7** | GPIO | **W5500 RST** (Reset) |
| **GPIO 8** | GPIO | **W5500 INT** (Interrupt) |
| **GPIO 9** | GPIO | **Status LED** (Green) |
| **GPIO 10** | GPIO | **Error LED** (Red) |
| **USB D+/D-** | USB | **USB-C Connector** (Programming) |

## 5. Mini-PCIe Slot Pinout (RAK5146 Target)
*   **Pin 2 (3.3V):** Connect to MP2359 Output.
*   **Pin 24 (3.3V):** Connect to MP2359 Output.
*   **Pin 52 (3.3V):** Connect to MP2359 Output.
*   **Pin 4, 9, 15, 18, 21... (GND):** Connect to GND Plane.
*   **Pin 19 (SPI_MOSI):** Connect to ESP32 GPIO 1.
*   **Pin 21 (SPI_MISO):** Connect to ESP32 GPIO 2.
*   **Pin 23 (SPI_SCK):** Connect to ESP32 GPIO 3.
*   **Pin 25 (SPI_CS):** Connect to ESP32 GPIO 4.
*   **Pin 17 (RST):** Connect to ESP32 GPIO 6.

## 6. Detailed Bill of Materials (BOM)

| Item | Manufacturer | Part Number | Description | Qty | Unit Cost |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Host MCU** | Espressif | **ESP32-S3-WROOM-1-N8R2** | Wi-Fi/BLE Module, 8MB/2MB | 1 | $2.80 |
| **Concentrator** | RAKwireless | **RAK5146 (SPI)** | SX1303 LoRaWAN Card | 1 | $45.00 |
| **Ethernet Chip** | WIZnet | **W5500** | SPI to Ethernet Controller | 1 | $1.50 |
| **Ethernet Jack** | Pulse | **J0011D21BNL** | RJ45 with Magnetics | 1 | $1.20 |
| **Buck Converter** | MPS | **MP2359** | 1.2A 3.3V Step-Down | 1 | $0.40 |
| **Inductor** | Generic | **CDRH4D28-4R7** | 4.7uH Power Inductor | 1 | $0.15 |
| **PCIe Socket** | Generic | **AS0B221-S68Q-7H** | 52-Pin Mini-PCIe H=4mm | 1 | $1.00 |
| **USB Connector** | Generic | **Type-C 16-Pin** | Power + Data | 1 | $0.40 |
| **PCB** | JLCPCB | **Custom** | 2-Layer, Thermal Vias | 1 | $3.00 |
| **Enclosure** | Generic | **100x100 ABS** | Waterproof Box | 1 | $5.00 |
| **TOTAL** | | | | | **~$60.45** |

## 7. Layout Guidelines
1.  **Thermal Management:** The MP2359 and RAK5146 generate heat. Place large copper pours on Top and Bottom layers connected by multiple vias under the Mini-PCIe latch area and power regulators.
2.  **Ethernet:** Keep differential pairs (TX+/TX-, RX+/RX-) from the W5500 to the RJ45 jack short and length-matched.
3.  **RF:** The RF is handled on the RAK5146 card, so the baseboard only deals with digital signals. Keep SPI lines direct.
