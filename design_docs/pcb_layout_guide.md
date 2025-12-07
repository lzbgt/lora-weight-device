# PCB Design Guide & Layout Guidelines

## 1. Stackup & Specifications
*   **Layers:** 2-Layer Standard FR4 (Cost effective).
*   **Thickness:** 1.6mm.
*   **Copper:** 1oz (35um).
*   **Finish:** HASL (Lead-free) or ENIG (for better pad flatness on RAK3172).

## 2. Component Placement
1.  **RAK3172 (RF Module):**
    *   Place on the Top Layer.
    *   **Position:** Near the edge of the board where the antenna connector is located to minimize RF trace length.
    *   **Orientation:** Ensure the "Keepout" area (if using internal antenna version) is respected, but for the IPEX version, focus on the connector path.
2.  **HX711 (ADC):**
    *   Place as close as physically possible to the Load Cell wire solder pads/connector.
    *   Keep it far away from the RF Antenna path to prevent noise induction.
3.  **Power (TPS61021A):**
    *   Place near the battery terminals.
    *   Keep the switching loop (Inductor + Diode + Caps) extremely tight to reduce EMI.

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
- [ ] **Boot0:** Connect BOOT0 to a header or button for easy firmware flashing (DFU mode).
- [ ] **Programming:** Expose UART2 (TX/RX) + GND + VCC to a 4-pin header.
- [ ] **Antenna:** IPEX connector (U.FL) footprint matches the part number.
- [ ] **Battery Protection:** Add a **SI2301** P-Channel MOSFET or **SS14** Schottky Diode for reverse polarity protection.
- [ ] **E-Ink Config:** Verify **BS1** is tied to GND (4-Wire SPI).
- [ ] **Booster Ratings:** Verify Diodes/Caps are rated >25V (Logic is 3.3V, but Booster is 20V).

## 5. Fabrication Files (Gerber)
*   Export: Top Copper, Bottom Copper, Top Solder Mask, Bottom Solder Mask, Top Silkscreen, Bottom Silkscreen, Drill, Outline.
*   Drill Chart: Ensure holes for the Battery Holder and Load Cell mounting are correct size (M3 clearance = 3.2mm).
