#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PCB_DIR="$ROOT/hardware/pcb"
ERC_RPT="$PCB_DIR/urine_monitor-erc.rpt"
DRC_RPT="$PCB_DIR/urine_monitor-drc.rpt"

KICAD_CLI="/Applications/kicad/kicad.app/Contents/MacOS/kicad-cli"
KICAD_PY="/Applications/kicad/kicad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3"

export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"

cd "$ROOT"

echo "[clean] removing generated artifacts…"
rm -rf \
  "$PCB_DIR/jlc_fab" \
  "$PCB_DIR/schematic_auto.svg" \
  "$PCB_DIR/urine_monitor_schematic.svg"

rm -f \
  "$PCB_DIR/drc_report.rpt" \
  "$PCB_DIR/urine_monitor_autolayout.kicad_pcb" \
  "$PCB_DIR/urine_monitor_autolayout.kicad_pro" \
  "$PCB_DIR/urine_monitor_autolayout.kicad_prl" \
  "$PCB_DIR/urine_monitor_autolayout.svg" \
  "$PCB_DIR/urine_monitor_autolayout.png" \
  "$PCB_DIR/urine_monitor_autoroute.dsn" \
  "$PCB_DIR/urine_monitor_autoroute.ses" \
  "$PCB_DIR/urine_monitor_autorouted.kicad_pcb" \
  "$PCB_DIR/urine_monitor_autorouted.kicad_pro" \
  "$PCB_DIR/urine_monitor_autorouted.svg" \
  "$PCB_DIR/urine_monitor_autorouted.png" \
  "$PCB_DIR/urine_monitor_board.png" \
  "$PCB_DIR/urine_monitor.png.svg" \
  "$PCB_DIR/urine_monitor.svg" \
  "$PCB_DIR/urine_monitor.png" \
  "$PCB_DIR/urine_monitor.pdf" \
  "$PCB_DIR/urine_monitor_pdf_p0.png" \
  "$PCB_DIR/urine_monitor_bom.csv" \
  "$PCB_DIR/urine_monitor_jlc_bom.csv" \
  "$PCB_DIR/urine_monitor.dsn" \
  "$PCB_DIR/urine_monitor.ses" \
  "$PCB_DIR/urine_monitor_routed.kicad_pcb" \
  "$PCB_DIR/urine_monitor_routed.kicad_pro" \
  "$PCB_DIR/urine_monitor_schematic.png" \
  "$ERC_RPT" \
  "$DRC_RPT" \
  "$ROOT/urine_monitor-erc.rpt" \
  "$ROOT/urine_monitor-drc.rpt" \
  "$ROOT/urine_monitor_autorouted-drc.rpt" \
  "$PCB_DIR/urine_monitor_jlc_fab.zip"

echo "[sch] generating schematic…"
python3 tools/gen_urine_schematic.py

echo "[erc] running ERC…"
"$KICAD_CLI" sch erc "$PCB_DIR/urine_monitor.kicad_sch" \
  --format report \
  -o "$ERC_RPT" \
  --exit-code-violations

echo "[bom] exporting BOM + JLC BOM…"
"$KICAD_CLI" sch export bom "$PCB_DIR/urine_monitor.kicad_sch" \
  -o "$PCB_DIR/urine_monitor_bom.csv"
python3 tools/process_bom_for_jlc.py

echo "[pcb] auto-place…"
"$KICAD_PY" tools/auto_layout_pcb.py \
  --sch "$PCB_DIR/urine_monitor.kicad_sch" \
  --out "$PCB_DIR/urine_monitor_autolayout.kicad_pcb"

echo "[pcb] autoroute (freerouting headless)…"
"$KICAD_PY" - <<'PY'
from pathlib import Path
import subprocess

ROOT = Path(".").resolve()
PCB_DIR = ROOT / "hardware" / "pcb"
BOARD_IN = PCB_DIR / "urine_monitor_autolayout.kicad_pcb"
DSN = PCB_DIR / "urine_monitor_autoroute.dsn"
SES = PCB_DIR / "urine_monitor_autoroute.ses"
BOARD_OUT = PCB_DIR / "urine_monitor_autorouted.kicad_pcb"
BOARD_FINAL = PCB_DIR / "urine_monitor.kicad_pcb"

import wx
_ = wx.GetApp() or wx.App(False)
import pcbnew

board = pcbnew.LoadBoard(str(BOARD_IN))
pcbnew.ExportSpecctraDSN(board, str(DSN))

subprocess.run(
    [
        "java",
        "-jar",
        str(ROOT / "tools" / "freerouting.jar"),
        "--guiSettings.isEnabled=false",
        "--apiServerSettings.isEnabled=false",
        "-de",
        str(DSN),
        "-do",
        str(SES),
        "-mt",
        "1",
        "-da",
    ],
    check=True,
)

pcbnew.ImportSpecctraSES(board, str(SES))
pcbnew.SaveBoard(str(BOARD_OUT), board)
pcbnew.SaveBoard(str(BOARD_FINAL), board)
print(f"wrote {BOARD_FINAL}")
PY

echo "[drc] running DRC (with schematic parity)…"
"$KICAD_CLI" pcb drc "$PCB_DIR/urine_monitor.kicad_pcb" \
  --format report \
  --schematic-parity \
  -o "$DRC_RPT" \
  --exit-code-violations

echo "[artifacts] exporting schematic PDF + previews…"
"$KICAD_CLI" sch export pdf "$PCB_DIR/urine_monitor.kicad_sch" -o "$PCB_DIR/urine_monitor.pdf"
"$KICAD_CLI" sch export svg "$PCB_DIR/urine_monitor.kicad_sch" -o "$PCB_DIR/urine_monitor_schematic.svg"
magick -density 300 "$PCB_DIR/urine_monitor_schematic.svg/urine_monitor.svg" "$PCB_DIR/urine_monitor_schematic.png"
magick -density 200 "$PCB_DIR/urine_monitor.pdf[0]" "$PCB_DIR/urine_monitor_pdf_p0.png"

echo "[artifacts] exporting PCB preview…"
"$KICAD_CLI" pcb export svg "$PCB_DIR/urine_monitor.kicad_pcb" \
  --layers F.Cu,F.SilkS,Edge.Cuts \
  --fit-page-to-board \
  --exclude-drawing-sheet \
  -o "$PCB_DIR/urine_monitor.png.svg"
magick -density 300 "$PCB_DIR/urine_monitor.png.svg" "$PCB_DIR/urine_monitor_board.png"

echo "[jlc] exporting fabrication package…"
mkdir -p "$PCB_DIR/jlc_fab"
"$KICAD_CLI" pcb export gerbers "$PCB_DIR/urine_monitor.kicad_pcb" -o "$PCB_DIR/jlc_fab" --no-protel-ext
"$KICAD_CLI" pcb export drill "$PCB_DIR/urine_monitor.kicad_pcb" -o "$PCB_DIR/jlc_fab"
"$KICAD_CLI" pcb export pos "$PCB_DIR/urine_monitor.kicad_pcb" --format csv --units mm --side both -o "$PCB_DIR/jlc_fab/urine_monitor_pos.csv"
"$KICAD_CLI" pcb export ipcd356 "$PCB_DIR/urine_monitor.kicad_pcb" -o "$PCB_DIR/jlc_fab/urine_monitor.ipcd356"
(cd "$PCB_DIR/jlc_fab" && zip -qr ../urine_monitor_jlc_fab.zip .)

echo "[done] ERC+DRC clean; artifacts regenerated."
