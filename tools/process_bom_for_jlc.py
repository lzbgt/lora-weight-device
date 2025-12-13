import csv
import sys
from pathlib import Path

# Mappings based on design_docs/detailed_bom.md and analysis
# Key: Value from Schematic (or Reference prefix)
# Value: (Manufacturer, Part Number, LCSC Part #)
BOM_MAPPING = {
    "RAK3172": ("RAKwireless", "RAK3172", ""),
    "HX711": ("Avia Semiconductor", "HX711", ""),
    "TPS61220": ("Texas Instruments", "TPS61220DCKR", ""),
    "MIC5504-3.3": ("Microchip", "MIC5504-3.3YM5-TR", ""),
    "SI2301": ("Vishay", "SI2301CDS-T1-GE3", ""),
    "2N7002": ("OnSemi", "2N7002", ""),
    "SS14": ("OnSemi", "SS14", ""),
    "RED": ("Cree", "LED Red 0603", ""), # Generic
    "10uF": ("Yageo", "CC0603KRX7R9BB106", ""), # Example generic 0603 10uF
    "0.1uF": ("Yageo", "CC0603KRX7R9BB104", ""), # Example generic
    "4.7uH": ("Murata", "LQM18PN4R7MFRD", ""), # Example generic 0603 inductor
    "Buzzer": ("CUI", "CPT-9019S", ""),
    "LoadCell": ("Generic", "Header 1x4", ""),
    "EInk_FPC": ("TE Connectivity", "2-1734839-4", ""), # Connector for GDEY0213B74
    "USB-C_Power": ("HRO", "TYPE-C-31-M-12", "C165948"),
    "USER_BTN": ("C&K", "PTS645", ""),
    "BAT_JST": ("JST", "S2B-PH-SM4-TB", ""),
    "Antenna_UFL": ("Hirose", "U.FL-R-SMT-1", ""),
}

def process_bom():
    root_dir = Path(__file__).resolve().parents[1]
    input_csv = root_dir / "hardware" / "pcb" / "urine_monitor_bom.csv"
    output_csv = root_dir / "hardware" / "pcb" / "urine_monitor_jlc_bom.csv"

    if not input_csv.exists():
        print(f"Error: {input_csv} not found.")
        return

    print(f"Reading {input_csv}...")
    
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    # Add new columns
    new_fieldnames = ["Comment", "Designator", "Footprint", "Manufacturer", "Part Number", "LCSC Part #"]
    
    jlc_rows = []

    for row in rows:
        refs = row.get("Refs", "")
        value = row.get("Value", "")
        footprint = row.get("Footprint", "")
        
        # Determine Manufacturer/Part Number
        manufacturer = ""
        part_number = ""
        lcsc_part = ""

        # Direct Value Match
        if value in BOM_MAPPING:
            manufacturer, part_number, lcsc_part = BOM_MAPPING[value]
        
        # Generic resistor fallback.
        elif refs.startswith("R"):
            manufacturer = "Generic"
            part_number = f"Resistor 0603 {value}"

        jlc_row = {
            "Comment": value,
            "Designator": refs,
            "Footprint": footprint,
            "Manufacturer": manufacturer,
            "Part Number": part_number,
            "LCSC Part #": lcsc_part
        }
        jlc_rows.append(jlc_row)

    print(f"Writing {output_csv}...")
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames)
        writer.writeheader()
        writer.writerows(jlc_rows)
    
    print("Done.")

if __name__ == "__main__":
    process_bom()
