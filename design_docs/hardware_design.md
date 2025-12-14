# Hardware Design (Current Plan)

This document is the *current* hardware plan used by the programmatic KiCad generators in `tools/`. It replaces earlier drafts that assumed a PCB‑mounted AA holder and large debug headers.

## Recent schematic/PCB updates
- **USB-C is now the single development connector**: full USB2 D+/D- feed an on‑board STM32F042 acting as USB CDC (UART) + CMSIS‑DAP SWD.
- **CH340C removed; STM32F042F6P6 replaces it** to provide both UART console and SWD/JTAG‑style debug over the same cable (3.3 V powered, with local decoupling).
- **Field power is via a 2‑wire JST‑PH** feeding the TPS61220 boost and Schottky OR-ing with the USB LDO.

## 1. System Role
- **Device:** LoRaWAN Class‑A end node
- **Connectivity:** Sub‑1 GHz LoRa (RAK3172 module)
- **UI:** 2.13" e‑paper (SSD1680) connected by FPC cable; local button + buzzer + status LED
- **Power:** USB‑C for development power; external battery pack for field deployment (2‑wire JST)

## 2. External Interfaces (Connectors)
- **USB‑C (Dev)**: single connector for development **power + console + flashing**
  - Power: `VBUS` (5 V) into an LDO → 3.3 V
  - Data: USB2 D+/D‑ into **STM32F042F6P6** (USB CDC + CMSIS‑DAP SWD)
  - Flashing: via STM32 UART bootloader over the USB CDC path (requires `BOOT0` + reset access; see `design_docs/firmware_design.md`)
  - SWD/JTAG: kept as **optional** pogo‑pad footprint (preferred) rather than a large 2.54 mm header
- **Battery (Field)**: 2‑wire JST‑PH (`BAT`, `GND`) to an external battery case/pack
- **Load Cell**: 4‑wire header (`E+`, `E-`, `A+`, `A-`) into HX711
- **Display**: 24‑pin 0.5 mm FPC connector for the GDEY0213B74 flex cable
- **Antenna**: u.FL/I‑PEX RF connector near the RAK3172 RF pin (short 50 Ω trace)

## 3. Key Silicon & Roles
### A. MCU + RF: RAK3172 (STM32WLE5)
- Integrated LoRa radio; certified module reduces RF risk.

### B. Load cell ADC: HX711 (SOIC‑16)
- 24‑bit ADC with PGA; reads strain gauge bridge.
- `HX_VCC` is **power‑gated** during sleep to eliminate bridge + HX711 draw.

### C. Power
- **Battery boost (field):** TI **TPS61220** (wide VIN, 3.3 V rail generation).
- **USB LDO (dev power):** Microchip **MIC5504‑3.3** from `VBUS` → 3.3 V.
- **Power ORing:** Schottky diodes into the system rail `VCC` (one from battery boost, one from USB LDO).
- **Battery sense:** 1 MΩ / 1 MΩ divider from `BAT` to ADC (`BAT_SENSE`) so firmware can report battery health even when on USB power.

### D. USB Console + Debug Bridge
- **STM32F042F6P6** provides USB CDC (console/logs, UART bootloader access) and CMSIS‑DAP SWD over the same USB‑C connector. Target SWDIO/SWCLK/NRST and UART2 RX/TX are wired to this bridge and also brought out to the pogo/debug header.

## 4. Pin Mapping (Summary)
### A. RAK3172 → System
| RAK3172 Pin | Net | Function | Notes |
|---:|---|---|---|
| 1 | `UART2_RX` | console RX | From USB bridge (STM32F042) TXD |
| 2 | `UART2_TX` | console TX | To USB bridge (STM32F042) RXD |
| 3 | `HX711_DT` | HX711 data | `PA15` |
| 4 | `HX711_SCK` | HX711 clock | `PB6` (must be LOW before gating) |
| 6 | `EINK_DC` | E‑ink D/C | `PA1` |
| 7 | `SWDIO` | SWD IO | optional pogo pads |
| 8 | `SWCLK` | SWD CLK | optional pogo pads |
| 9 | `I2C_SCL` | I2C | expansion |
| 10 | `I2C_SDA` | I2C | expansion |
| 13 | `EINK_MOSI` | SPI MOSI | `PA7` |
| 15 | `EINK_SCK` | SPI SCK | `PA5` |
| 16 | `EINK_CS` | SPI CS | `PA4` |
| 19 | `BUZZ_PWM` | buzzer PWM | `PA8` |
| 26 | `LED_STATUS` | status LED | `PB2` |
| 27 | `EINK_RST` | e‑ink reset | `PB12` |
| 29 | `EINK_BUSY` | e‑ink busy | `PA0` |
| 30 | `HX_GATE` | HX gate | drives SI2301 |
| 31 | `BAT_SENSE` | battery ADC | divider from `BAT` |
| 32 | `BTN_USER` | button | active‑low |

### B. STM32F042F6 (USB Bridge) → System
| STM32F042 Pin | Net | Function | Notes |
|---:|---|---|---|
| 16 / VDDA | `VCC` | 3.3 V | shared decoupling with C4 |
| 15 / VSSA | `GND` | ground | analog/digital common |
| 17 / PA11 | `USB_DM` | USB D– | to J3 |
| 18 / PA12 | `USB_DP` | USB D+ | to J3 |
| 19 / PA13 | `SWDIO` | target SWDIO | feeds RAK3172 / pogo |
| 20 / PA14 | `SWCLK` | target SWCLK | feeds RAK3172 / pogo |
| 14 / PB1  | `NRST`  | target reset | drives module reset |
| 8  / PA2  | `UART2_RX` | UART TX to RAK | bridge → target |
| 9  / PA3  | `UART2_TX` | UART RX from RAK | target → bridge |
| 4  / NRST | `NRST` | MCU reset | pulled up, brought to USB-C reset strap |

### C. Connectors (External)
| Ref | Pins | Nets | Purpose |
|---|---|---|---|
| J3 | USB‑C | `VBUS`, `USB_DP`, `USB_DM`, `CC1`, `CC2`, `GND` | Dev power + CDC + CMSIS‑DAP |
| J1 | 1x4 | `E+`, `E-`, `A+`, `A-` | Load cell |
| J2 | 24‑pin FPC | SPI + HV rails | E‑ink flex |
| J4 | 1x05 | `GND`, `VCC`, `I2C_SCL`, `I2C_SDA`, `BOOT0` | Minimal breakout |
| J5 | u.FL | RF feed | Antenna |
| BT1 | JST‑PH‑2 | `BAT`, `GND` | Battery input |

## 5. E‑Ink Display Notes (GDEY0213B74 / SSD1680)
- The PCB hosts only the **24‑pin FPC connector**; the display module mounts elsewhere in the enclosure and connects via the flex cable.
- SPI interface uses `BUSY/RES#/D/C#/CS#/SCL/SDA` and `BS1` strapped for 4‑wire SPI.
- The SSD1680 requires an **external booster/regulator application circuit** (inductor + MOSFET + Schottky diodes + capacitors) for the HV rails. Reference:
  - `datasheets/GDEY0213B74.pdf` (module reference circuit)
  - `datasheets/SSD1680.pdf` (Section 6.3 “Booster & Regulator”)
- Layout requirements (important):
  - Place the HV booster parts and HV capacitors **right next to the FPC connector**.
  - Keep the switching loop (L + MOSFET + diodes) **extremely small**.
  - Keep the HV area away from HX711 analog inputs and away from the RF feed.

## 6. PCB Placement Priorities (Professional Layout)
- **USB edge:** USB‑C centered on a short edge; STM32F042 bridge + LDO close to it; keep copper for heat spreading.
- **Analog corner:** Load cell connector + HX711 + its decoupling close together; keep noisy switching/HV away.
- **RF edge:** RAK3172 near top edge with u.FL near RF pin; short 50 Ω feed; ground stitching.
- **Display edge:** FPC connector on board edge to simplify cable routing; HV caps clustered next to pins.
- **Silkscreen:** keep `U* / R* / C* / J*` reference designators visible on `F.SilkS` (assembly‑friendly).

## 7. Known Issues / TODO
- Implement the SSD1680/GDEY0213B74 HV booster circuit in the schematic generator (currently some HV pins are stubbed as NC).
- Ensure `BAT_SENSE` measures the battery input (`BAT`) and not the post-OR system rail (`VCC`).
