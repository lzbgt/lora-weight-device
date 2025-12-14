import sys
import pcbnew
from pathlib import Path

def import_ses(board_path, ses_path, out_path):
    board = pcbnew.LoadBoard(str(board_path))
    success = pcbnew.ImportSpecctraSES(board, str(ses_path))
    if success:
        print(f"Successfully imported SES from {ses_path}")
        pcbnew.SaveBoard(str(out_path), board)
        print(f"Saved routed board to {out_path}")
    else:
        print(f"Failed to import SES from {ses_path}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python import_ses.py <input.kicad_pcb> <input.ses> <output.kicad_pcb>")
        sys.exit(1)
    
    import_ses(sys.argv[1], sys.argv[2], sys.argv[3])
