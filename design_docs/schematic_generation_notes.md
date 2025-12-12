# Programmatic Schematic Update (Dec 2025)

This note captures the automated changes to `hardware/pcb/urine_monitor.kicad_sch`, the intent behind them, and how to regenerate artifacts without opening the GUI.

## What changed
- **Generator refresh (`tools/gen_urine_schematic.py`)**
  - Snap all placements to a 1.27 mm grid and draw short per-pin stubs with labels (no shared anchors) to keep PDFs readable and clickable.
  - Emits a **multi-sheet schematic** for readability: root sheet only holds four sheet blocks (`MCU + Debug`, `Load Cell + HX711`, `Power Entry + Regulation`, `E-Ink Display`) so each logical block is on its own page with global labels tying nets together.
  - Corrected KiCad Y orientation and pin vectors so wires actually land on pins.
  - Added NO_CONNECT markers for unused pins (MCU spares, HX711 extras, E-ink NC/HV rails, battery holder spares, U4 pin4).
  - Added power flags for `VCC`, `BAT`, `VBUS`, `HX_VCC`, `U3_L`, `GND` (local `PWR_FLAG` cloned into `Project_Lib` to avoid missing-library warnings).
  - Exposed a 2×06 debug/expansion header (GND, VCC, UART2, SWDIO/SWCLK, NRST, BOOT0, I2C_SCL/SDA) on a 2.54 mm footprint.
  - Relocated parts to avoid label/wire collisions: moved LDO/USB diode cluster away from the debug header and spread the HX711 decouplers so `HX_VCC` no longer shorts to GND.
  - Footprints aligned to stock KiCad libs to silence footprint warnings (e.g., `SOT-363_SC-70-6` for U3, `TE_2-1734839-4_1x24-1MP_P0.5mm_Horizontal` for the E-ink FPC, standard USB-C and pin headers).
  - Added explicit Value map so BOM shows specs and intent (e.g., `R3 100k`, `R5/R6 5k1 CC pulldowns, JDBG` debug label).
- **Outputs regenerated**
  - Schematic: `hardware/pcb/urine_monitor.kicad_sch`
  - PDF: `hardware/pcb/urine_monitor.pdf`
  - BOM CSV: `hardware/pcb/urine_monitor_bom.csv`
  - ERC report: `urine_monitor-erc.rpt` (now only library/footprint warnings; no errors).

## How to regenerate
```bash
python tools/gen_urine_schematic.py
/Applications/kicad/kicad.app/Contents/MacOS/kicad-cli sch export pdf hardware/pcb/urine_monitor.kicad_sch -o hardware/pcb/urine_monitor.pdf
/Applications/kicad/kicad.app/Contents/MacOS/kicad-cli sch export bom hardware/pcb/urine_monitor.kicad_sch -o hardware/pcb/urine_monitor_bom.csv
/Applications/kicad/kicad.app/Contents/MacOS/kicad-cli sch erc hardware/pcb/urine_monitor.kicad_sch -o urine_monitor-erc.rpt
```

## ERC status
- **Errors:** none (clean).
- **Warnings:** none (clean) after localizing `PWR_FLAG` and using stock footprints.

## Readability / navigation
- Each pin has its own labeled stub (no overlapping anchors), making PDF search/click reliable.
- The root sheet is a simple map to four logical sheets so you can skim by page (MCU/Debug, HX711 + load cell, Power, Display). Signals stay connected via global labels across sheets.
- Labels are offset slightly from the wire ends to avoid overlap with pins or wires.
- LDO/USB cluster and HX711 decouplers were spaced to prevent unintended shorts to GND.

## Recipe to reuse on other projects
- **Grid discipline:** pick a grid (we use 1.27 mm) and snap all instance coordinates and wire endpoints to it. Avoid zero-length stubs.
- **Y orientation:** KiCad sheet space is Y-down; compute absolute pin positions as `(inst.x + pin.x, inst.y - pin.y)` and flip `dir_vec` Y.
- **Per-pin stubs + labels:** draw a short wire off every pin and place the net label near (not on) the stub end. This keeps ERC/netlisting reliable and PDFs clickable.
- **Power flags:** place `PWR_FLAG` on every driven rail (VCC/BAT/VBUS/HX_VCC/U3_L/GND here) so ERC stops complaining about unpowered nets.
- **NO_CONNECT markers:** explicitly mark unused pins. Safer than leaving them floating and lets ERC stay green.
- **Footprints in code:** set realistic footprints in the generator; KiCad CLI then exports BOM/PCB associations without manual edits.
- **Separation for readability:** move dense clusters (e.g., power entry, decouplers) apart so labels do not touch each other or wires. If ERC shows merged nets, nudge the offending parts a few grid steps.
- **Headless outputs:** always emit PDF, BOM, and ERC report from CLI; they act as the “what you see in GUI” proof without opening KiCad.

## Notes for future edits
- If you add nets, only extend the `add(net, ref, pin)` lists; the stub/label emitter will take care of the wiring.
- If you see net merges in ERC, check for overlapping stub endpoints—nudging instances a few grid steps usually fixes it.
- Keep the grid at 1.27 mm so labels line up cleanly in the exported PDF.***
