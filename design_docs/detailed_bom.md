# Detailed Bill of Materials (Current Plan)

This BOM reflects the *current* architecture: **USB‑C + STM32F042 bridge** for development (power + console + CMSIS‑DAP SWD / UART bootloader), **JST 2‑wire battery connector** for field deployment, and a **24‑pin FPC connector** for the e‑paper cable.

## 1. Core Electronics (PCBA)

| Block | Part | Manufacturer | Part Number | Notes / Datasheet |
|---|---|---|---|---|
| MCU + LoRa | RAK3172 module | RAKwireless | RAK3172 | `datasheets/RAK3172_C19723904.pdf` |
| Load cell ADC | HX711 | Avia | HX711 | `datasheets/hx711.pdf` |
| E‑paper display | GDEY0213B74 | Good Display | GDEY0213B74 | `datasheets/GDEY0213B74.pdf` |
| E‑paper connector | 24‑pin 0.5 mm FPC | TE Connectivity | 2‑1734839‑4 | `datasheets/TE_2-1734839-4_C3168150.pdf` |
| USB connector | USB‑C receptacle (dev power/console/boot) | HRO | TYPE‑C‑31‑M‑12 | `datasheets/HRO_TYPE-C-31-M-12_C165948.pdf` |
| USB bridge | STM32F042F6P6 (USB CDC + CMSIS‑DAP SWD) | ST | STM32F042F6P6 | `https://www.st.com/resource/en/datasheet/stm32f042f6.pdf` |
| USB LDO | 3.3 V LDO | Microchip | MIC5504‑3.3YM5 | `datasheets/MIC5504.pdf` |
| Battery boost | boost converter | TI | TPS61220DCKR | `datasheets/TPS61220.pdf` |
| Rail ORing | Schottky diode | onsemi (or equiv) | SS14 | `datasheets/SS14.pdf` (x2) |
| Battery connector | JST‑PH 2‑pin (field battery harness) | JST | S2B‑PH‑SM4‑TB | `datasheets/JST_S2B-PH-SM4-TB_C295747.pdf` |
| RF connector | u.FL / I‑PEX | Hirose | U.FL‑R‑SMT‑1 | `datasheets/U.FL-R-SMT-1_C88373.pdf` |
| HX power gate | P‑MOSFET | Vishay | SI2301CDS | `datasheets/SI2301CDS-T1-GE3_C10487.pdf` |
| Buzzer driver | N‑MOSFET | onsemi (or equiv) | 2N7002 | `datasheets/2N7002LT1G_C16338.pdf` |
| Buzzer | magnetic SMD | CUI | CMT‑8504‑100‑SMT | (KiCad footprint: `Buzzer_Beeper:MagneticBuzzer_CUI_CMT-8504-100-SMT`) |
| Button | tactile switch | C&K | PTS645 | `datasheets/pts645.pdf` |
| LED | 0603 red | generic | LED 0603 red | (assembly‑friendly footprint) |
| Passives | R/C/L | generic | 0603 | values per schematic |

## 2. E‑Paper HV Booster (Required for SSD1680)

The SSD1680 requires an external booster/regulator application circuit (inductor + MOSFET + diodes + capacitors) for the HV rails. Reference:
- `datasheets/SSD1680.pdf` (Section 6.3 “Booster & Regulator”)
- `datasheets/GDEY0213B74.pdf` (module reference circuit)

Recommended parts (package choices are driven by availability and placement near the FPC connector):
- **Inductor:** 47 µH (≥500 mA), SMD (size TBD; avoid 0603 for this value/current)
- **MOSFET:** Si1308EDL (SOT‑323)
- **Schottky diodes:** MBR0530 (SOD‑123) ×3
- **Sense resistor:** 2.2 Ω
- **Caps:** 4.7 µF / 25 V and 1 µF / 25 V (multiple, per reference circuit)

## 3. Mechanical / Off‑Board
- **Battery pack:** housed in a separate battery case; connects to the PCB via JST‑PH 2‑wire cable.
- **Display module:** mounted in the enclosure front; connects to the PCB via the 24‑pin FPC cable.
