from pathlib import Path
import subprocess
import os

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

print(f"Loading {BOARD_IN}...")
board = pcbnew.LoadBoard(str(BOARD_IN))
print(f"Exporting DSN to {DSN}...")
pcbnew.ExportSpecctraDSN(board, str(DSN))

print("Running FreeRouting...")
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

print(f"Importing SES from {SES}...")
pcbnew.ImportSpecctraSES(board, str(SES))
print(f"Saving to {BOARD_OUT} and {BOARD_FINAL}...")
pcbnew.SaveBoard(str(BOARD_OUT), board)
pcbnew.SaveBoard(str(BOARD_FINAL), board)
print(f"Done.")
