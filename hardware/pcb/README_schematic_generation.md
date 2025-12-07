# Programmatic KiCad Schematic Generation (urine_monitor.kicad_sch)

This project auto-generates the schematic instead of hand-wiring in the GUI. The generator lives in `tools/gen_urine_schematic.py` and produces `hardware/pcb/urine_monitor.kicad_sch`, plus a verification SVG.

## Dependencies
- KiCad 7/8/9 CLI on macOS (path: `/Applications/kicad/kicad.app/Contents/MacOS/kicad-cli`).
- KiCad symbol libraries available at `/Applications/kicad/kicad.app/Contents/SharedSupport/symbols`.
- Python 3.9+.

## One-shot regeneration
```bash
python tools/gen_urine_schematic.py
/Applications/kicad/kicad.app/Contents/MacOS/kicad-cli sch export svg hardware/pcb/urine_monitor.kicad_sch -o hardware/pcb/schematic_auto.svg
```
Outputs:
- `hardware/pcb/urine_monitor.kicad_sch`
- `hardware/pcb/schematic_auto.svg/urine_monitor.svg` (quick visual check)
- Netlist can be exported with `kicad-cli sch export netlist ...`.

## How the generator works
- **Symbol sources**: It embeds required symbols directly into the schematic to avoid library path issues. Sources include:
  - Project-specific symbols: `hardware/pcb/project_lib.kicad_sym`.
  - KiCad libraries: `Analog_ADC`, `Connector_Generic`, `Connector`, `Device`, `Transistor_FET`, `Regulator_Switching`, `Regulator_Linear`, `Switch`, `power`.
- **Footprints**: A `FOOTPRINTS` map in the script assigns realistic footprints per instance (SOIC-16 for HX711, SOT-23 for FETs, 0603 R/C, SOD-123 diodes, SC70-6 boost, SOT-23-5 LDO, USB-C receptacle, etc.).
- **Instances**: Each component is instantiated with a reference designator, symbol name, and a coarse XY placement. UUIDs are auto-assigned.
- **Nets and wiring**:
  - A net map (`N`) lists `(ref, pin)` pairs per net.
  - Each pin gets a real wire segment to a shared anchor for that net; one label sits on the anchor. This is what fixes the “no wires/disconnected nets” problem—labels alone were not enough.
  - Wires are emitted in horizontal/vertical (Manhattan) segments to reduce crossing through symbols; the orthogonal style is for readability, not correctness (the key fix was adding real wire geometry to an anchor).
  - Pin snapping: the first segment starts exactly at the pin’s coordinate and extends outward (non-zero length) before heading to the anchor, which avoids the “wire ends on the pin body but isn’t connected” failure.
  - This approach addresses two earlier failure modes:
    * **“No chip”/missing symbols in CLI**: symbols are embedded into `lib_symbols` inside the schematic, so `kicad-cli` resolves them without external paths.
    * **“No wires”/nets missing in netlist**: per-pin wires to an anchor plus a single anchor label ensure KiCad forms the intended nets.

## Customizing symbols and footprints
1) Add or edit symbols:
   - Project symbols: `hardware/pcb/project_lib.kicad_sym`.
   - KiCad symbols: ensure the library path is listed in `LIB_PATHS` inside the script.
2) Assign footprints:
   - Extend the `FOOTPRINTS` dict with `ref: "Library:Footprint"` entries.
   - KiCad will carry these into the netlist and PCB association.

## Adding or changing nets
1) Edit the `add(net, ref, pin)` declarations in `tools/gen_urine_schematic.py`.
2) Regenerate the schematic (see commands above).
3) Export SVG to visually verify and adjust anchor spacing if wires are too close to symbols.

## Verification
- Visual: open `hardware/pcb/schematic_auto.svg/urine_monitor.svg`.
- Netlist: `kicad-cli sch export netlist hardware/pcb/urine_monitor.kicad_sch -o /tmp/urine.net`.
- ERC: `kicad-cli sch erc hardware/pcb/urine_monitor.kicad_sch` (expect warnings until all nets are finalized).

## Tips for refinement
- If anchors sit too close to symbols, increase the `margin` in `emit_net_manhattan` or choose per-net offsets.
- For strict style (no wires through symbols), bias anchors to the side where the majority of pins exit (already done in the script) and increase margin in dense areas.
- Keep coordinates coarse; the goal is connectivity and repeatability. Final drafting can be done in KiCad if desired, but regeneration should remain deterministic.
