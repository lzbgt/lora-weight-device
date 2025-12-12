import uuid
from pathlib import Path

OUT_DIR = Path("hardware/pcb")
ROOT_UUID = str(uuid.uuid4())
SHEET_UUID = str(uuid.uuid4())

# Create a sub-sheet file
sub_content = f"""(kicad_sch (version 20231105) (generator "test_minimal")
  (uuid {SHEET_UUID})
  (paper "A4")
  (title_block
    (title "Sub Sheet")
  )
  (lib_symbols)
  (sheet_instances
    (path "/{ROOT_UUID}/{SHEET_UUID}" (page "2"))
  )
)"""
(OUT_DIR / "test_sub.kicad_sch").write_text(sub_content)

# Create root sheet with one sheet
root_content = f"""(kicad_sch (version 20231105) (generator "test_minimal")
  (uuid {ROOT_UUID})
  (paper "A4")
  (title_block
    (title "Test Root")
  )
  (lib_symbols)
  (sheet
    (at 100 100)
    (size 50 50)
    (uuid {SHEET_UUID})
    (property "Sheetname" "Sub" (at 100 100 0)
      (effects (font (size 1.27 1.27)) (justify left bottom))
    )
    (property "Sheetfile" "test_sub.kicad_sch" (at 100 150 0)
      (effects (font (size 1.27 1.27)) (justify left top))
    )
    (instances
      (project "test" (path "/{ROOT_UUID}/{SHEET_UUID}" (page "2")))
    )
  )
  (sheet_instances
    (path "/" (page "1"))
    (path "/{ROOT_UUID}/{SHEET_UUID}" (page "2"))
  )
)"""

(OUT_DIR / "test.kicad_sch").write_text(root_content)
print(f"Wrote test.kicad_sch with sub-sheet")