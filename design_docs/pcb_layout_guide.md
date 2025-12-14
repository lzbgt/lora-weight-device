# PCB Design Guide & Layout Guidelines

## 1. Stackup & Specifications
*   **Layers:** 2-Layer Standard FR4 (Cost effective).
*   **Thickness:** 1.6mm.
*   **Copper:** 1oz (35um).
*   **Finish:** HASL (Lead-free) or ENIG (for better pad flatness on RAK3172).

## 2. Component Placement
This project is designed around **edge‑anchored connectors** and **functional grouping** to keep routing short and predictable.

1. **USB‑C (Dev) edge (thermal + mechanical priority):**
   - Place the **USB‑C receptacle centered on a short edge** (mechanical alignment + cable strain relief).
   - Place the **STM32F042 debug bridge + its decoupling** close to the USB‑C D+/D‑ pins (USB CDC + CMSIS‑DAP).
   - Place the **MIC5504 LDO** close to VBUS input; leave copper for heat spreading; keep the USB power area away from HX711 analog inputs.

2. **Battery (Field) connector:**
   - Use a **2‑wire JST‑PH** connector (`BAT`, `GND`).
   - Place it on the bottom edge offset from USB so the harness exits downward without crowding the dev connector.

3. **RF section:**
   - Place the **RAK3172** near the top edge.
   - Place the **u.FL** connector very close to the module RF pin; keep the 50 Ω feed short and straight.

4. **Analog section (HX711):**
   - Place HX711 and its local decoupling **right next to** the load cell connector.
   - Keep digital/HV switching away from the bridge inputs.

5. **Display section (FPC + HV booster):**
   - Place the **24‑pin FPC connector on a board edge** to simplify cable routing to the display.
   - Place the **SSD1680 booster circuit and HV capacitors** tightly around the connector pins.
   - Keep this HV area away from the HX711 and RF feed.

Current auto-generated placement (60×80 mm rectangle) keeps USB‑C centered on the bottom short edge with the STM32F042 bridge + USB Schottky just above it, the JST battery at the lower‑left, HX711/load cell mid‑left, the FPC mid‑right, RAK3172 + u.FL near the top, and the buzzer away from the RF/debug corner.

## 3. Routing Guidelines

### A. RF Trace (Critical)
*   **Impedance:** The trace from RAK3172 pin `RF` to the IPEX connector must be **50 Ohms**.
*   **Calculation:** For 1.6mm FR4 (Er ~4.5), a 50-ohm microstrip trace is roughly **~2.8mm to 3.0mm wide**.
    *   *Tip:* Since this is wide, keep the trace very short (< 5mm) to minimize mismatch issues if you can't match the width perfectly.
*   **Grounding:** Place a solid Ground Pour on the Bottom Layer directly underneath the RF trace. Stitch with vias along the trace.

### B. Analog Signals (HX711)
*   **Differential Pairs:** Route `E+`/`E-` and `A+`/`A-` as differential pairs. Keep them parallel and close together.
*   **Isolation:** Surround these traces with Ground signals (Guard Traces) if possible.
*   **No Crossing:** Do NOT route digital signals (SCK/DT) under or over these analog lines.

### C. Power Routing
*   **VCC Trace:** Use at least 0.5mm width for main 3.3V lines.
*   **GND:** Use a "Star Ground" topology if possible, or a solid Ground Plane (Bottom Layer) for the entire board.
*   **Decoupling:** Place 0.1uF capacitors **immediately** next to the VCC pins of the RAK3172 and HX711.

### D. E-Ink Booster & High Voltage
*   **Switching Loop:** The connection between the Inductor (L1), MOSFET (Q1), and Diodes (D1-D3) switches at high frequency. Keep this loop **extremely small** to minimize EMI.
*   **High Voltage Caps:** The capacitors for VGH, VGL, VSH, VSL (+/-20V, +/-15V) must be rated for **25V** minimum.
*   **Placement:** Place these capacitors as close as possible to the FPC connector pins to stabilize the drive voltages.
*   **Isolation:** Keep these noisy switching signals away from the sensitive Analog (HX711) and RF sections.

## 4. Schematic Checklist
- [ ] **Reset:** Pull-up resistor (10k) on RAK3172 RST pin? (Module usually has internal, check datasheet).
- [ ] **Boot0 + Reset:** Provide a way to enter the STM32 ROM bootloader for UART flashing (BOOT0 strap + reset access).
- [ ] **Console/Debug:** Route UART2 + SWD to the STM32F042 bridge (USB CDC + CMSIS‑DAP) for logs/flashing.
- [ ] **Antenna:** IPEX connector (U.FL) footprint matches the part number.
- [ ] **Battery input:** JST‑PH 2‑wire connector; consider reverse‑polarity protection if needed.
- [ ] **E-Ink Config:** Verify **BS1** is tied to GND (4-Wire SPI).
- [ ] **Booster Ratings:** Verify Diodes/Caps are rated >25V (Logic is 3.3V, but Booster is 20V).

## 5. Fabrication Files (Gerber)
*   Export: Top Copper, Bottom Copper, Top Solder Mask, Bottom Solder Mask, Top Silkscreen, Bottom Silkscreen, Drill, Outline.
*   Silkscreen: Keep reference designators visible (`U*`, `R*`, `C*`, `J*`) with sane text size (e.g., 1.0mm height, 0.15mm stroke) and away from pads.
