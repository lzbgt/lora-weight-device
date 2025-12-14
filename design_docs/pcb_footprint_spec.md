# PCB Physical Specification (Current Plan)

This spec replaces earlier drafts that assumed a PCB‑mounted AA holder. In the current plan:
- The **battery is off‑board** (separate battery case) and connects via a **2‑wire JST‑PH** cable.
- The **display is off‑board** (mounted in the enclosure front) and connects via a **24‑pin FPC** cable.

## 1. Board Outline (Target)
- **Goal:** make the PCB as small as practical while keeping routing sane and respecting RF/HV keepouts.
- **Current generator default:** 60mm (W) × 80mm (H) rectangle (USB‑C centered on the bottom short edge, STM32F042 debug bridge + LDO/Schottky just above it, JST‑PH battery at the lower‑left, load cell on the left edge, FPC on the right edge, u.FL near the top edge).
- **Target after tightening:** shrink to the minimal envelope around connectors + functional blocks.

## 2. Edge Anchors (Must‑Haves)
- **USB‑C:** centered on one short edge (development power + console + flashing via UART bootloader).
- **FPC (Display):** placed on an edge so the cable exits cleanly to the display.
- **Battery JST:** currently on the bottom edge offset from USB to reduce crowding; keep clearance for harness strain relief.
- **u.FL:** on the top edge near RAK3172 RF pin (short 50 Ω feed).
- **Load cell header:** edge accessible for harness / strain relief.

## 3. Keepouts / Constraints
- **RF:** keep the RAK3172 RF feed short; use ground stitching; avoid copper “slots” under the feed.
- **E‑paper HV:** booster loop and HV caps stay close to the FPC pins; keep noisy HV away from HX711 analog inputs.
- **Thermal:** USB power entry (LDO + ORing diode) is a heat source; keep it away from HX711 and from the RF feed, and give it copper to spread heat.

## 4. Silkscreen / Assembly
- Reference designators (`U*`, `R*`, `C*`, `J*`) must be visible on `F.SilkS` and placed clear of pads so assembly/debug is possible without the 3D viewer.
