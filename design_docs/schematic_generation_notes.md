# Programmatic Schematic Generation Notes

This repo generates the KiCad schematic *from code* (`tools/gen_urine_schematic.py`) to keep the design reproducible and reviewable.

## Current design intent (high level)
- **Dev interface:** USB‑C + STM32F042 bridge (power + USB‑UART console + CMSIS‑DAP SWD + UART bootloader flashing)
- **Field power:** external battery pack via 2‑wire JST‑PH
- **Display:** off‑board e‑paper connected via 24‑pin FPC cable (PCB only hosts the connector + required HV booster parts)
- **RF:** u.FL connector and short 50 Ω feed from RAK3172

## Generator conventions
- Snap all placements to a 1.27 mm grid.
- Use per‑pin stubs + global labels (readable PDFs; minimizes accidental wire merges).
- Add `PWR_FLAG` on driven rails to keep ERC clean.
- Add explicit `no_connect` markers for unused pins.
- Keep reference/value/footprint text away from pins so exported PDFs are readable.

## How to regenerate everything (headless)
Use the single entrypoint script:
```bash
bash tools/regen_kicad_project.sh
```
This regenerates the schematic, runs ERC, generates/places/routs the PCB, runs DRC, exports PDFs/PNGs, and produces JLCPCB fabrication artifacts.

## Notes
- If ERC shows merged nets, it is usually caused by overlapping stub endpoints; nudging the responsible instance a few grid steps fixes it.
- Keep the schematic “blocky”: USB/Power, RF, HX711 analog, and Display/HV should each read as a separate cluster even in a single‑page sheet.
- USB-C is wired with full D+/D- pins into the STM32F042 bridge (powered from the 3.3 V rail with CC pulldowns) so a single cable provides development power + UART (CDC) + CMSIS‑DAP SWD.
