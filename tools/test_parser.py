import uuid
from pathlib import Path
import re

# Copy-paste of extraction logic
def extract_block_from(text, start_index):
    depth = 0
    for i in range(start_index, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return text[start_index : i + 1]
    raise ValueError("unbalanced")

# Test on a problematic string case
# Case 1: Balanced parens in quotes (Should work)
case1 = '(property "Desc" "balanced (parens)")'
print(f"Case 1 extracted: {extract_block_from(case1, 0)}")

# Case 2: Unbalanced parens in quotes (Should fail)
case2 = '(property "Desc" "smiley :) ends here")'
try:
    print(f"Case 2 extracted: {extract_block_from(case2, 0)}")
except Exception as e:
    print(f"Case 2 failed as expected (or not?): {e}")
    # Wait, it won't fail with "unbalanced", it will return early!
    # It will return '(property "Desc" "smiley :)' 
    # leaving ' ends here")'
    
res2 = extract_block_from(case2, 0)
print(f"Case 2 actual result: {res2}")
if res2 != case2:
    print("FAIL: Case 2 extracted incomplete string due to ignoring quotes.")

# Case 3: Actual symbol test
# I will try to extract RAK3172 from the file I just read (simulating)
project_lib = Path("hardware/pcb/project_lib.kicad_sym").read_text()
start = project_lib.find('(symbol "RAK3172"')
if start != -1:
    block = extract_block_from(project_lib, start)
    print(f"RAK3172 extracted length: {len(block)}")
    print(f"Ends with: {block[-20:]}")
else:
    print("RAK3172 not found")
