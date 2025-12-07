# Detailed Bill of Materials (BOM)

## 1. Core Electronics (PCBA)

| Item | Manufacturer | Part Number | Description | Qty | Unit Cost (Est.) | Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **MCU + LoRa SoC** | RAKwireless | **RAK3172** | STM32WLE5 Module, Sub-1GHz, IPEX, SMD | 1 | $6.00 | [RAK Store](https://store.rakwireless.com/products/rak3172-wisduo-lpwan-module) |
| **ADC (Load Cell)** | Avia Semiconductor | **HX711** | 24-Bit Analog-to-Digital Converter (SOIC-16) | 1 | $0.50 | DigiKey / LCSC |
| **Display** | Good Display | **GDEY0213B74** | 2.13" E-Paper, 250x122, SPI, SSD1680 Driver | 1 | $4.50 | [Good Display](https://www.good-display.com/) |
| **Buzzer** | CUI / Generic | **CPT-9019S** | Piezo Transducer, SMD or TH, 3V-25V Drive | 1 | $0.30 | DigiKey |
| **Buzzer Driver** | OnSemi / Generic | **2N7002** | N-Channel MOSFET (SOT-23) | 1 | $0.05 | DigiKey |
| **Power Gate** | Vishay / Generic | **SI2301** | P-Channel MOSFET (SOT-23) | 1 | $0.10 | DigiKey |
| **Power Management** | Texas Instruments | **TPS61021A** | 3A Boost Converter (0.9V to 3.3V High Eff.) | 1 | $0.85 | DigiKey |
| **Wall Power LDO** | Torex | **XC6220B331MR** | 3.3V LDO (5V In), SOT-23-5 | 1 | $0.35 | DigiKey |
| **Power Connector** | Generic | **USB Type-C** | 16-pin Power Only Receptacle, SMD | 1 | $0.40 | LCSC / DigiKey |
| **Power Diode** | OnSemi | **SS14** | Schottky Diode (Low Vf) for OR-ing | 2 | $0.10 | DigiKey |
| **Battery Holder** | Keystone | **1028** | Holder for 2x AA Cells, PCB Mount | 1 | $1.20 | DigiKey |
| **Antenna** | Molex | **1461530050** | Flex Internal Antenna, 868/915MHz, IPEX | 1 | $1.50 | DigiKey |
| **User Button** | C&K | **PTS645** | Tactile Switch, 6mm | 1 | $0.20 | DigiKey |
| **LED** | Cree | **SMD 0603** | Red/Green Status LED | 2 | $0.05 | DigiKey |
| **Passive Components** | Yageo / Murata | **0402/0603** | Resistors, Caps (10uF, 0.1uF, 1uF) | ~35 | $1.30 | DigiKey |
| **E-Ink Booster** | Various | **Booster Kit** | 47uH (CDRH2D18), Si1308EDL, 3x MBR0530 | 1 | $0.80 | DigiKey |
| **PCB** | JLCPCB / PCBWay | **Custom** | 2-Layer FR4, 1.6mm, Green Solder Mask | 1 | $2.00 | JLCPCB |

**Total PCBA Cost:** ~$20.20

---

## 2. Sensor & Mechanical Components

| Item | Specifications | Description | Qty | Unit Cost (Est.) |
| :--- | :--- | :--- | :--- | :--- |
| **Force Sensor** | 25lbf (~11kg) | **FX1901-0001-0025-L** Compression Load Cell | 1 | $16.50 |
| **Enclosure** | Custom Injection Mold / 3D Print | ABS/ASA Plastic, IP65 Design, White | 1 | $4.00 |
| **Bed Rail Hook** | Stainless Steel / ABS | Universal Clamp or Hook (Fits 0.8"-1.5" rails) | 1 | $2.50 |
| **Carabiner/Hook** | Stainless Steel | To hang the urine bag on the load cell | 1 | $1.00 |
| **Screws/Fasteners** | M3 / M4 Stainless | For mounting PCB and Load Cell | Set | $0.50 |
| **Gasket** | Silicone | For IP65 sealing of enclosure halves | 1 | $0.50 |

**Total Mechanical Cost:** ~$25.00

---

## 3. Gateway Infrastructure (Per Ward)

| Item | Manufacturer | Part Number | Description | Qty | Unit Cost |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LoRaWAN Gateway** | RAKwireless | **RAK7268V2** | WisGate Edge Lite 2 (Indoor, 8-ch, Wi-Fi/Eth, PoE) | 1 | $150.00 |
| **Mounting Kit** | Generic | - | Wall mount screws/anchors | 1 | $5.00 |
| **Power Adapter (Opt.)** | Generic | **12V / 1A** | **Required for Wi-Fi Line install** (if PoE unavailable) | 1 | $5.00 |

**Total Infrastructure Cost:** ~$155.00 - $160.00
*Note: Gateway is a purchased finished product (COTS). No custom PCB design is required for the Gateway.*

---

## 4. Total Unit Cost Estimate (Mass Production > 1k units)

| Category | Prototype Cost (1 Unit) | Mass Production Cost (Est.) |
| :--- | :--- | :--- |
| **PCBA** | $20.20 | $15.00 |
| **Mechanical** | $25.00 | $18.00 |
| **Assembly & Testing** | $3.00 | $3.00 |
| **Packaging** | $1.00 | $1.00 |
| **TOTAL DEVICE** | **~$49.20** | **~$37.00** |
