#!/bin/bash
set -e

# Setup paths
KICAD_CLI="/Applications/kicad/kicad.app/Contents/MacOS/kicad-cli"
PYTHON="/Applications/kicad/kicad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3"
TOOLS_DIR="tools"
PCB_DIR="hardware/pcb"
SCH_FILE="$PCB_DIR/urine_monitor.kicad_sch"
PCB_FILE="$PCB_DIR/urine_monitor.kicad_pcb"
DSN_FILE="$PCB_DIR/urine_monitor.dsn"
SES_FILE="$PCB_DIR/urine_monitor.ses"
ROUTED_PCB="$PCB_DIR/urine_monitor_routed.kicad_pcb"
GERBER_DIR="$PCB_DIR/gerbers"

echo "=== 1. Generating Schematic PDF ==="
"$KICAD_CLI" sch export pdf "$SCH_FILE" -o "$PCB_DIR/urine_monitor_schematic.pdf"

echo "=== 2. Auto-Placing PCB ==="
"$PYTHON" "$TOOLS_DIR/auto_layout_pcb.py" --out "$PCB_FILE"

echo "=== 3. Exporting to Specctra DSN ==="
"$PYTHON" "$TOOLS_DIR/export_dsn.py" "$PCB_FILE" "$DSN_FILE"

echo "=== 4. Auto-Routing (Freerouting) ==="
# Using -de (design input) and -do (design output)
java -jar "$TOOLS_DIR/freerouting.jar" -de "$DSN_FILE" -do "$SES_FILE" -mt 1

echo "=== 5. Importing Route (SES) ==="
"$PYTHON" "$TOOLS_DIR/import_ses.py" "$PCB_FILE" "$SES_FILE" "$ROUTED_PCB"

echo "=== 6. Generating Manufacturing Files ==="
mkdir -p "$GERBER_DIR"

# Gerbers
"$KICAD_CLI" pcb export gerbers "$ROUTED_PCB" -o "$GERBER_DIR/"

# Drill
"$KICAD_CLI" pcb export drill "$ROUTED_PCB" -o "$GERBER_DIR/"

# Pick and Place
"$KICAD_CLI" pcb export pos "$ROUTED_PCB" -o "$PCB_DIR/urine_monitor_pos.csv" --units mm --format csv

# Visual PDF of the PCB
"$KICAD_CLI" pcb export pdf "$ROUTED_PCB" -o "$PCB_DIR/urine_monitor_routed_view.pdf" --layers "F.Cu,F.SilkS,F.Fab,B.Cu,B.SilkS,B.Fab,Edge.Cuts"

echo "=== Done! Dataset Ready in $PCB_DIR ==="
