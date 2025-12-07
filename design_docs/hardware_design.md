# Hardware Design & Specification

## 1. System Compatibility & Role
*   **Device Type:** LoRaWAN Class A End-Node.
*   **Connectivity:** Sub-1GHz RF (Talks to the Gateway).
*   **Gateway Compatibility:** Compatible with standard LoRaWAN 1.0.3 Gateway **RAK7268V2**.
    *   *Note:* This device functions identically whether the Gateway is connected via **PoE (Ethernet)** or **Wi-Fi**.

## 2. Chip Selection & Justification

### A. Core Microcontroller / RF: **RAK3172 (STM32WLE5)**
*   **Why:** The STM32WLE5 is the world's first SoC with integrated LoRaWAN radio. The RAK3172 module packages this chip with necessary RF matching and regulatory certification (FCC/CE/etc.), drastically reducing design complexity and cost.
*   **Key Specs:** ARM Cortex-M4, Sub-1GHz Radio, Ultra-low power (< 2uA in sleep).
*   **Cost:** ~$6-7 USD per module.

### B. Sensor Interface: **HX711 (24-Bit ADC)**
*   **Why:** The industry standard for resistive load cells. It includes a built-in preamplifier (gain 128), essential for the millivolt-level signals from strain gauges.
*   **Key Specs:** 24-bit resolution, 2.6-5.5V operation, 2-wire digital interface.
*   **Sensor Compatibility:** Perfectly suited for **TE FX1901 Compression Load Cell**.
    *   **Output:** 20mV/V nominal.
    *   **Bridge Resistance:** 2400Ω (Typ).
    *   **Current Draw:** ~1.4mA at 3.3V Excitation.
*   **Cost:** < $0.50 USD.

### C. Power Management:
*   **Boost Converter:** **TI TPS61021A** to boost 2x AA (1.8V-3.0V) to stable 3.3V for the Load Cell.
*   **Power Gating:** **SI2301 (P-Channel MOSFET)** to cut power to the HX711 and Load Cell during sleep. This eliminates the quiescent current of the HX711 (<1uA) and the bridge excitation current (**~1mA** for the specified FX1901 2.4kΩ-3.6kΩ bridge).
*   **Battery Sense:** Voltage divider (**1MΩ / 1MΩ**) connected to **PB4 (ADC)** to monitor battery health.

### D. User Interface
*   **Display:** **Good Display GDEY0213B74** (2.13", 250x122, SSD1680 Driver). SPI Interface.
*   **Audio:** **CPT-9019S Piezo Transducer** driven by **2N7002 (N-Channel MOSFET)** for louder sound/safety. Driven by MCU PWM.
*   **LED:** Simple Status LED (Red) for boot/error indication.
*   **Button:** Single User Button for interaction.
    *   **Short Press (<2s):** Tare / Zero Scale.
    *   **Long Press (>2s):** Toggle Measurement Range (Standard 2000mL vs Extended).

---

## 2. Wiring & Schematic Concept

### Power Tree & Voltage Rails
*   **RAK3172 Input Range:** 2.0V to 3.6V.
*   **Regulation Target:** **3.3V** (via TPS61021A Boost or XC6220B331MR LDO).
*   **Safety & OR-ing Logic:**
    *   **Mechanism:** Dual **SS14 Schottky Diodes**.
    *   **Safety Calculation (Temp -20°C to +60°C):**
        *   **Cold / High Load:** Vf increases ≈ 0.4V -> Net VDD = 3.3V - 0.4V = **2.9V** (> 2.0V Min Limit).
        *   **Hot / Low Load:** Vf decreases ≈ 0.15V -> Net VDD = 3.3V - 0.15V = **3.15V** (< 3.6V Max Limit).
    *   **Conclusion:** The rail is strictly constrained within the safe operating window under all environmental conditions.

### Pin Mapping (RAK3172 Module - 32-Pin Stamp)

| RAK3172 Pin | Pin Name | Function | Connection |
| :--- | :--- | :--- | :--- |
| **1** | PA3 | UART2_RX | Debug/Log RX |
| **2** | PA2 | UART2_TX | Debug/Log TX |
| **3** | PA15 | GPIO | **HX711 DT** (Data) |
| **4** | PB6 | GPIO | **HX711 SCK** (Clock) |
| **6** | PA1 | GPIO | **E-Ink D/C** (Data/Command) |
| **13** | PA7 | SPI1_MOSI | **E-Ink MOSI** |
| **15** | PA5 | SPI1_SCK | **E-Ink SCK** |
| **16** | PA4 | SPI1_NSS | **E-Ink CS** |
| **19** | PA8 | PWM | **Buzzer Driver** (Gate of 2N7002) |
| **26** | PB2 | GPIO | **Status LED** |
| **27** | PB12 | GPIO | **E-Ink RST** (Note: Internal Pull-Up/Down) |
| **29** | PA0 | GPIO | **E-Ink BUSY** |
| **30** | PB5 | GPIO | **Power Gate** (Gate of SI2301) |
| **31** | PB4 | ADC_IN | **Battery Sense** (1MΩ/1MΩ Divider) |
| **32** | PB3 | GPIO | **User Button** (Short: Tare, Long: Toggle Range) |
| **-** | - | Power In | **USB-C VBUS** (Connects to XC6220) |

### E-Ink Display Pinout (GDEY0213B74)
*   **Bias Generation:** The external booster (**Inductor L1, MOSFET Si1308EDL, Diodes MBR0530**) generates the high-voltage drive rails from the 3.3V supply.
    *   **Required Voltages (Source: SSD1680 Datasheet P.41 Table 11-2):**
        *   **VGH:** +20V (Typ)
        *   **VGL:** -20V (Derived, VGL = -VGH)
        *   **VSH1:** +15V (Typ)
        *   **VSH2:** +5V (Typ)
        *   **VSL:** -15V (Typ)
        *   **VCOM:** -2V (Typ)
    *   **Safety:** These voltages are generated *inside* the display module's power loop and do not expose the MCU or main VDD rail to >3.6V.

| Pin | Name | Function | Connection |
| :--- | :--- | :--- | :--- |
| 1 | NC | No Connect | - |
| 2 | GDR | Gate Drive | **Si1308EDL Gate** |
| 3 | RESE | Source Drive | **2.2Ω Resistor** to GND (Current Sense) |
| 4 | NC | No Connect | - |
| 5 | VSH2 | Source High | **4.7uF/25V** Cap to GND (**+15V**) |
| 6 | TSCL | Temp Clock | NC (Internal Sensor Used) |
| 7 | TSDA | Temp Data | NC (Internal Sensor Used) |
| 8 | BS1 | Bus Select | **GND** (4-Wire SPI) |
| 9 | BUSY | Busy | MCU **PA0** |
| 10 | RES# | Reset | MCU **PB12** |
| 11 | D/C# | Data/Cmd | MCU **PA1** |
| 12 | CS# | Chip Select | MCU **PA4** |
| 13 | SCL | Clock | MCU **PA5** |
| 14 | SDA | MOSI | MCU **PA7** |
| 15 | VDDIO | IO Power | **VDD_RAK** (~3.0V) |
| 16 | VCI | Logic Power | **VDD_RAK** (~3.0V) |
| 17 | VSS | Ground | **GND** |
| 18 | VDD | Core Volt | **1uF** Cap to GND |
| 19 | VPP | OTP Power | NC (or 1uF Cap) |
| 20 | VSH1 | Source High | **1uF/25V** Cap to GND (**+15V**) |
| 21 | VGH | Gate High | **1uF/25V** Cap to GND (**+20V**) |
| 22 | VSL | Source Low | **1uF/25V** Cap to GND (**-15V**) |
| 23 | VGL | Gate Low | **1uF/25V** Cap to GND (**-20V**) |
| 24 | VCOM | VCOM | **1uF/25V** Cap to GND |

**Reference Circuit Note:** The GDEY0213B74 requires an external booster circuit (Reference: Datasheet Section 12).
*   **Inductor:** 47uH (L1).
*   **MOSFET:** Si1308EDL (Q1).
*   **Diode:** MBR0530 (D1-D3).
*   **Resistor:** 2.2Ω (R2) for current sense.
*   **Capacitors:** 1uF/25V (C5-C12) and 4.7uF/25V (C4).

### Buzzer Driver Note
*   **Component:** 2N7002 (N-Channel MOSFET).
*   **Sizing:** Rds(on) ~7.5Ω @ Vgs=2.5V. Load current (Piezo) < 20mA. Voltage drop < 0.15V. Sufficient for 3V drive.

### Critical Design Note: Power Gating
*   **Power Cut:** When the P-Channel MOSFET cuts power to the HX711 (VCC = 0V), the MCU **MUST** set the `HX711 SCK` pin to **LOW** (or High-Z with pull-down) before sleeping.
*   **Why:** If SCK is High while HX711 VCC is 0V, current will flow through the SCK ESD protection diode into the HX711's internal power rail, causing "Ghost Powering" and draining the battery.

### Load Cell to HX711
*   **Sensor:** **TE FX1901-0001-0025-L** (25lbf / 11kg).
*   **Saturation Limitation:** The FX1901 Full Scale output (~66mV) exceeds the HX711 Gain 32 input range (+/- 51.5mV).
    *   **Impact:** Measurement will be **clamped/saturated at approximately 8.5kg**.
    *   **Acceptance:** This is acceptable as the primary application (Urine Bag) volume is 0-2000mL (2kg), well within the linear range.
*   **Wiring:**
    *   **Red (Excitation +):** Connected to **Switched 3.3V** (via MOSFET)
    *   **Black (Excitation -):** Connected to GND
    *   **Green (Signal +):** HX711 INB+
    *   **White (Signal -):** HX711 INB-

---

## 3. PCB Design Guidelines

### A. RF Section (Crucial)
*   **Antenna Path:** Keep the trace from the RAK3172 RF pin to the antenna connector (IPEX or SMA) as short as possible.
*   **Impedance:** Use a calculator to ensure the RF trace is **50 Ohms**.
*   **Ground Plane:** Solid ground plane under the module, *except* under the antenna area if using a PCB antenna. Use plenty of stitching vias.

### B. Analog Section (HX711)
*   **Isolation:** Place the HX711 and its capacitors as close to the load cell connector as possible.
*   **Separation:** Keep digital traces (SCK/DT) away from the analog input traces (E+/E-/A+/A-) to avoid noise coupling.
*   **Power:** Use a dedicated decoupling capacitor (10uF + 0.1uF) right next to the HX711 VCC pin.

### C. Power Routing
*   **VCC Trace:** Use at least 0.5mm width for main 3.3V lines.
*   **GND:** Use a "Star Ground" topology if possible, or a solid Ground Plane (Bottom Layer) for the entire board.
*   **Decoupling:** Place 0.1uF capacitors **immediately** next to the VCC pins of the RAK3172 and HX711.

### D. E-Ink Booster & High Voltage
*   **Switching Loop:** The connection between the Inductor (L1), MOSFET (Q1), and Diodes (D1-D3) switches at high frequency. Keep this loop **extremely small** to minimize EMI.
*   **High Voltage Caps:** The capacitors for VGH, VGL, VSH, VSL (+/-20V, +/-15V) must be rated for **25V** minimum.
*   **Placement:** Place these capacitors as close as possible to the FPC connector pins to stabilize the drive voltages.
*   **Isolation:** Keep these noisy switching signals away from the sensitive Analog (HX711) and RF sections.
