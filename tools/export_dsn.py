import sys
import pcbnew
from pathlib import Path

def export_dsn(board_path, dsn_path):
    board = pcbnew.LoadBoard(str(board_path))
    success = pcbnew.ExportSpecctraDSN(board, str(dsn_path))
    if success:
        print(f"Successfully exported DSN to {dsn_path}")
    else:
        print(f"Failed to export DSN to {dsn_path}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python export_dsn.py <input.kicad_pcb> <output.dsn>")
        sys.exit(1)
    
    export_dsn(sys.argv[1], sys.argv[2])
