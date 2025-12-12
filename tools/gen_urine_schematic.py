import math
import re
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "hardware" / "pcb"
SYM_BASE = Path("/Applications/kicad/kicad.app/Contents/SharedSupport/symbols")

GRID = 1.27  # 50 mil for clean snapping
STUB_LEN = GRID * 6  # longer stubs for label clearance
ANCHOR_DIST = GRID * 3
LABEL_NUDGE = GRID * 1.5  # keep text away from pin/body
PIN_TEXT_H = 1.27
FOOTPRINT_OFFSET = max(4 * PIN_TEXT_H, 3 * PIN_TEXT_H)  # 4x pin label height
TOP_NETS = {"VCC", "VBUS", "BAT", "HX_VCC", "U3_OUT", "U4_OUT"}
BOTTOM_NETS = {"GND"}
# KiCad default A4 frame is landscape: 297 mm x 210 mm.
A4_W = 297.0
A4_H = 210.0

LIB_PATHS = {
    "Project_Lib": ROOT / "hardware/pcb/project_lib.kicad_sym",
    "Analog_ADC": SYM_BASE / "Analog_ADC.kicad_sym",
    "Connector_Generic": SYM_BASE / "Connector_Generic.kicad_sym",
    "Connector": SYM_BASE / "Connector.kicad_sym",
    "Device": SYM_BASE / "Device.kicad_sym",
    "Transistor_FET": SYM_BASE / "Transistor_FET.kicad_sym",
    "Regulator_Switching": SYM_BASE / "Regulator_Switching.kicad_sym",
    "Regulator_Linear": SYM_BASE / "Regulator_Linear.kicad_sym",
    "Switch": SYM_BASE / "Switch.kicad_sym",
    "Power": SYM_BASE / "power.kicad_sym",
}


def fmt(val: float) -> str:
    return f"{val:.2f}"


def snap(val: float) -> float:
    return round(val / GRID) * GRID


def snap_pt(pt):
    return snap(pt[0]), snap(pt[1])


class Pin:
    def __init__(self, num, name, at):
        self.num = num
        self.name = name
        parts = at.split()
        self.x, self.y = map(float, parts[:2])
        self.rot = float(parts[2]) if len(parts) > 2 else 0.0

    def dir_vec(self, length=STUB_LEN):
        rad = math.radians(self.rot)
        dx = -length * math.cos(rad)
        dy = -length * math.sin(rad)
        dx = 0 if abs(dx) < 1e-6 else dx
        dy = 0 if abs(dy) < 1e-6 else dy
        return dx, dy


class Symbol:
    def __init__(self, lib_id, pins, raw_block):
        self.lib_id = lib_id
        self.pins = pins
        self.raw_block = raw_block
        self._bbox = None

    def pin(self, num):
        for p in self.pins:
            if p.num == num:
                return p
        raise KeyError(f"pin {num} not found in {self.lib_id}")

    def local_bbox(self):
        """Bounding box in symbol-local coords, padded to cover labels/body."""
        if self._bbox:
            return self._bbox
        xs = [p.x for p in self.pins]
        ys = [p.y for p in self.pins]
        if not xs or not ys:
            # Fallback to a small box if parsing ever fails.
            pad = STUB_LEN + LABEL_NUDGE
            self._bbox = (-pad, pad, -pad, pad)
            return self._bbox
        pad = STUB_LEN + LABEL_NUDGE  # leave room for pin text, stubs, labels
        min_x, max_x = min(xs) - pad, max(xs) + pad
        min_y, max_y = min(ys) - pad, max(ys) + pad
        # Guarantee a minimum footprint so skinny parts still repel neighbors.
        if max_x - min_x < GRID * 6:
            cx = 0.5 * (min_x + max_x)
            half = GRID * 3
            min_x, max_x = cx - half, cx + half
        if max_y - min_y < GRID * 6:
            cy = 0.5 * (min_y + max_y)
            half = GRID * 3
            min_y, max_y = cy - half, cy + half
        # Enlarge downward to cover the footprint label box and its keepout.
        extra_down = FOOTPRINT_OFFSET + 4 * PIN_TEXT_H  # 3x gap + 1x text height
        min_y -= extra_down
        # Slight horizontal padding so the label text width fits.
        min_x -= GRID * 4
        max_x += GRID * 4
        self._bbox = (min_x, max_x, min_y, max_y)
        return self._bbox


def extract_block(text, start_keyword):
    start = text.find(start_keyword)
    if start == -1:
        raise ValueError(f"{start_keyword} not found")
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    raise ValueError("unbalanced")


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

def parse_symbol(lib, name, alias_lib=None):
    print(f"Parsing {lib}:{name}...")
    lib_path = LIB_PATHS[lib]
    text = lib_path.read_text()
    
    # Using lib_id as "Lib:Name" for embedded symbols, as KiCad expects
    lib_id = f"{lib}:{name}"
    
    block = extract_block(text, f'(symbol "{name}"')
    
    # Rename symbol definition in the block
    block = block.replace(f'(symbol "{name}"', f'(symbol "{lib_id}"', 1)
    
    pins = []
    idx = 0
    print(f"  Searching for pins in block for {lib}:{name}, len: {len(block)}")
    while True:
        pin_start = block.find("(pin", idx)
        if pin_start == -1:
            print(f"  No more pins found for {lib}:{name}")
            break
        print(f"  Found pin at index {pin_start} for {lib}:{name}")
        pin_block = extract_block_from(block, pin_start)
        # Strip all whitespace and newlines for robust regex matching
        pin_block_clean = re.sub(r'\s+', ' ', pin_block).strip()
        
        at_m = re.search(r"\(at ([^)]*)\)", pin_block_clean)
        name_m = re.search(r'\(name "([^"]*)"', pin_block_clean)
        num_m = re.search(r'\(number "([^"]*)"', pin_block_clean)
        if at_m and name_m and num_m:
            pins.append(Pin(num_m.group(1), name_m.group(1), at_m.group(1)))
            print(f"    Parsed pin: num={num_m.group(1)}, name={name_m.group(1)}")
        else:
            print(f"    Failed to parse pin block: {pin_block}")
        idx = pin_start + len(pin_block)
    if not pins:
        print(f"  ERROR: No pins were parsed for {lib}:{name}")
        raise ValueError(f"no pins parsed for {lib}:{name}")
    print(f"  Successfully parsed {len(pins)} pins for {lib}:{name}")
    return Symbol(lib_id, pins, block)


SYM_CACHE = {
    "RAK3172": parse_symbol("Project_Lib", "RAK3172"),
    "GDEY0213B74": parse_symbol("Project_Lib", "GDEY0213B74"),
    "HX711": parse_symbol("Analog_ADC", "HX711"),
    "Conn_01x04": parse_symbol("Connector_Generic", "Conn_01x04"),
    "Conn_01x05": parse_symbol("Connector_Generic", "Conn_01x05"),
    "Conn_02x06_Odd_Even": parse_symbol("Connector_Generic", "Conn_02x06_Odd_Even"),
    "Q_PMOS_GSD": parse_symbol("Transistor_FET", "Q_PMOS_GSD"),
    "Q_NMOS_GSD": parse_symbol("Transistor_FET", "Q_NMOS_GSD"),
    "R": parse_symbol("Device", "R"),
    "L": parse_symbol("Device", "L"),
    "D_Schottky_Small": parse_symbol("Device", "D_Schottky_Small"),
    "C": parse_symbol("Device", "C"),
    "Buzzer": parse_symbol("Device", "Buzzer"),
    "LED": parse_symbol("Device", "LED"),
    "SW_Push": parse_symbol("Switch", "SW_Push"),
    "TPS61220DCK": parse_symbol("Regulator_Switching", "TPS61220DCK"),
    "MIC5504-3.3YM5": parse_symbol("Regulator_Linear", "MIC5504-3.3YM5"),
    "USB_C_Receptacle_PowerOnly_6P": parse_symbol("Connector", "USB_C_Receptacle_PowerOnly_6P"),
    "PWR_FLAG": parse_symbol("Project_Lib", "PWR_FLAG"),
}

FOOTPRINTS = {
    "U1": "RF_Module:RAK3172",
    "U2": "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
    "J1": "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
    "JDBG1": "Connector_PinHeader_2.54mm:PinHeader_2x06_P2.54mm_Vertical",
    "JDBG_I2C": "Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical",
    "BT1": "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
    "Q1": "Package_TO_SOT_SMD:SOT-23",
    "Q2": "Package_TO_SOT_SMD:SOT-23",
    "R1": "Resistor_SMD:R_0603_1608Metric",
    "R2": "Resistor_SMD:R_0603_1608Metric",
    "R3": "Resistor_SMD:R_0603_1608Metric",
    "R4": "Resistor_SMD:R_0603_1608Metric",
    "R5": "Resistor_SMD:R_0603_1608Metric",
    "R6": "Resistor_SMD:R_0603_1608Metric",
    "C1": "Capacitor_SMD:C_0603_1608Metric",
    "C2": "Capacitor_SMD:C_0603_1608Metric",
    "C3": "Capacitor_SMD:C_0603_1608Metric",
    "L1": "Inductor_SMD:L_0603_1608Metric",
    "D2": "Diode_SMD:D_SOD-123",
    "D3": "Diode_SMD:D_SOD-123",
    "BZ1": "Buzzer_Beeper:MagneticBuzzer_CUI_CMT-8504-100-SMT",
    "D1": "LED_SMD:LED_0603_1608Metric",
    "SW1": "Button_Switch_SMD:SW_SPST_TL3342",
    "U3": "Package_TO_SOT_SMD:SOT-363_SC-70-6",
    "U4": "Package_TO_SOT_SMD:SOT-23-5",
    "J3": "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
    "J2": "Connector_FFC-FPC:TE_2-1734839-4_1x24-1MP_P0.5mm_Horizontal",
}

VALUES = {
    # Resistors
    "R1": "1M",
    "R2": "1M",
    "R3": "100k",
    "R4": "1k",
    "R5": "5k1",
    "R6": "5k1",
    # Capacitors / inductors
    "C1": "10uF",
    "C2": "0.1uF",
    "C3": "10uF",
    "L1": "4.7uH",
    # Diodes
    "D1": "RED",
    "D2": "SS14",
    "D3": "SS14",
    # ICs / active
    "U1": "RAK3172",
    "U2": "HX711",
    "U3": "TPS61220",
    "U4": "MIC5504-3.3",
    "Q1": "SI2301",
    "Q2": "2N7002",
    # Connectors / misc
    "J1": "LoadCell",
    "J2": "EInk_FPC",
    "J3": "USB-C_Power",
    "JDBG1": "DBG/SWD/I2C/UART",
    "JDBG_I2C": "I2C+BOOT0+PWR",
    "BT1": "Battery",
    "BZ1": "Buzzer",
    "SW1": "USER_BTN",
}


class Instance:
    def __init__(self, ref, sym_name, at):
        self.ref = ref  # printed reference designator
        self.key = None  # logical key in INSTANCES dict, set after construction
        self.sym = SYM_CACHE[sym_name]
        self.at = snap_pt(at)
        self.uuid = uuid.uuid4()

    def pin_abs(self, pin_num):
        p = self.sym.pin(pin_num)
        return snap(self.at[0] + p.x), snap(self.at[1] - p.y)

    def pin_dir(self, pin_num, length=STUB_LEN):
        p = self.sym.pin(pin_num)
        dx, dy = p.dir_vec(length)
        return dx, -dy  # invert Y for KiCad sheet coordinates

    def bbox_abs(self, margin=0.0):
        """Absolute bounding box (min_x, max_x, min_y, max_y) with optional margin."""
        min_x, max_x, min_y, max_y = self.sym.local_bbox()
        cx, cy = self.at
        # KiCad Y grows downward, so invert Y axis for bounds.
        abs_min_x = snap(cx + min_x - margin)
        abs_max_x = snap(cx + max_x + margin)
        abs_min_y = snap(cy - max_y - margin)
        abs_max_y = snap(cy - min_y + margin)
        return abs_min_x, abs_max_x, abs_min_y, abs_max_y


INSTANCES = {
    "U1": Instance("U1", "RAK3172", (205.74, 113.03)),
    "U2": Instance("U2", "HX711", (74.93, 130.81)),
    "J1": Instance("J1", "Conn_01x04", (46.99, 130.81)),
    "JDBG1": Instance("JDBG1", "Conn_02x06_Odd_Even", (142.24, 88.90)),
    "JDBG_I2C": Instance("JDBG_I2C", "Conn_01x05", (170.18, 52.07)),
    "Q1": Instance("Q1", "Q_PMOS_GSD", (121.92, 144.78)),
    "Rgate": Instance("R3", "R", (121.92, 133.35)),
    "Rtop": Instance("R1", "R", (139.7, 95.25)),
    "Rbot": Instance("R2", "R", (139.7, 106.68)),
    "Q2": Instance("Q2", "Q_NMOS_GSD", (220.98, 153.67)),
    "B1": Instance("BZ1", "Buzzer", (228.60, 170.18)),
    "Rled": Instance("R4", "R", (210.82, 142.24)),
    "LED": Instance("D1", "LED", (220.98, 142.24)),
    "SW1": Instance("SW1", "SW_Push", (207.01, 125.73)),
    "J2": Instance("J2", "GDEY0213B74", (250.19, 110.49)),
    "U3": Instance("U3", "TPS61220DCK", (71.12, 190.50)),
    "L1": Instance("L1", "L", (55.88, 190.50)),
    "Dboost": Instance("D2", "D_Schottky_Small", (91.44, 190.50)),
    "U4": Instance("U4", "MIC5504-3.3YM5", (220.98, 81.28)),
    "Dusb": Instance("D3", "D_Schottky_Small", (231.14, 81.28)),
    "J3": Instance("J3", "USB_C_Receptacle_PowerOnly_6P", (240.03, 44.45)),
    "Rcc1": Instance("R5", "R", (224.79, 30.48)),
    "Rcc2": Instance("R6", "R", (232.41, 30.48)),
    "BT1": Instance("BT1", "Conn_01x04", (48.26, 165.10)),
    "CHX1": Instance("C1", "C", (81.28, 146.05)),
    "CHX2": Instance("C2", "C", (91.44, 151.13)),
    "CVCC": Instance("C3", "C", (193.04, 95.25)),
    "PF_VCC": Instance("PWR1", "PWR_FLAG", (25.4, 25.4)),
    "PF_BAT": Instance("PWR2", "PWR_FLAG", (25.4, 38.1)),
    "PF_VBUS": Instance("PWR3", "PWR_FLAG", (25.4, 50.8)),
    "PF_GND": Instance("PWR4", "PWR_FLAG", (25.4, 63.5)),
    "PF_HX": Instance("PWR5", "PWR_FLAG", (25.4, 76.2)),
    "PF_U3L": Instance("PWR6", "PWR_FLAG", (25.4, 88.9)),
}

# Tag each instance with its logical key for placement routines.
for _key, _inst in INSTANCES.items():
    _inst.key = _key

N = {}

def add(net, ref, pin):
    N.setdefault(net, []).append((ref, pin))


# MCU
add("UART2_RX", "U1", "1")
add("UART2_TX", "U1", "2")
add("HX711_DT", "U1", "3")
add("HX711_SCK", "U1", "4")
add("EINK_DC", "U1", "6")
add("SWDIO", "U1", "7")
add("SWCLK", "U1", "8")
add("I2C_SCL", "U1", "9")
add("I2C_SDA", "U1", "10")
for gpin in ["11", "17", "18", "23", "28"]:
    add("GND", "U1", gpin)
add("EINK_MOSI", "U1", "13")
add("EINK_SCK", "U1", "15")
add("EINK_CS", "U1", "16")
add("BUZZ_PWM", "U1", "19")
add("BOOT0", "U1", "21")
add("NRST", "U1", "22")
add("VCC", "U1", "24")
add("LED_STATUS", "U1", "26")
add("EINK_RST", "U1", "27")
add("EINK_BUSY", "U1", "29")
add("HX_GATE", "U1", "30")
add("BAT_SENSE", "U1", "31")
add("BTN_USER", "U1", "32")

# HX711
add("HX_VCC", "U2", "1")
add("HX_VCC", "U2", "3")
add("GND", "U2", "5")
add("GND", "U2", "6")
add("HX_INB-", "U2", "9")
add("HX_INB+", "U2", "10")
add("HX711_SCK", "U2", "11")
add("HX711_DT", "U2", "12")
add("GND", "U2", "15")  # RATE tied low
add("HX_VCC", "U2", "16")
add("GND", "U2", "7")
add("GND", "U2", "8")

# Load cell connector
add("HX_VCC", "J1", "1")
add("GND", "J1", "2")
add("HX_INB+", "J1", "3")
add("HX_INB-", "J1", "4")

# Battery connector
add("BAT", "BT1", "1")
add("GND", "BT1", "2")

# HX power gate
add("HX_VCC", "Q1", "3")
add("VCC", "Q1", "2")
add("HX_GATE", "Q1", "1")
add("VCC", "Rgate", "1")
add("HX_GATE", "Rgate", "2")

# Battery sense divider
add("VCC", "Rtop", "1")
add("BAT_SENSE", "Rtop", "2")
add("BAT_SENSE", "Rbot", "1")
add("GND", "Rbot", "2")

# Buzzer driver
add("VCC", "B1", "1")
add("BUZZ_SINK", "B1", "2")
add("BUZZ_PWM", "Q2", "1")
add("GND", "Q2", "2")
add("BUZZ_SINK", "Q2", "3")

# LED
add("VCC", "Rled", "1")
add("LED_NET", "Rled", "2")
add("LED_NET", "LED", "1")
add("LED_STATUS", "LED", "2")

# Button
add("BTN_USER", "SW1", "1")
add("GND", "SW1", "2")

# E-ink connector
add("EINK_BUSY", "J2", "9")
add("EINK_RST", "J2", "10")
add("EINK_DC", "J2", "11")
add("EINK_CS", "J2", "12")
add("EINK_SCK", "J2", "13")
add("EINK_MOSI", "J2", "14")
add("VCC", "J2", "15")
add("VCC", "J2", "16")
add("GND", "J2", "17")
add("VCC", "J2", "18")
add("GND", "J2", "8")

# Boost converter TPS61220
add("BAT", "U3", "1")  # VIN
add("U3_OUT", "U3", "2")  # FB tied to VOUT
add("GND", "U3", "3")
add("U3_OUT", "U3", "4")  # VOUT
add("U3_L", "U3", "5")  # L
add("BAT", "U3", "6")  # EN
add("BAT", "L1", "1")
add("U3_L", "L1", "2")
add("U3_OUT", "Dboost", "2")
add("VCC", "Dboost", "1")

# LDO MIC5504
add("VBUS", "U4", "1")
add("GND", "U4", "2")
add("VBUS", "U4", "3")
add("U4_OUT", "U4", "5")
add("U4_OUT", "Dusb", "2")
add("VCC", "Dusb", "1")

# USB-C connector
add("VBUS", "J3", "A9")
add("VBUS", "J3", "B9")
add("GND", "J3", "A12")
add("GND", "J3", "B12")
add("GND", "J3", "S1")
add("CC1", "J3", "A5")
add("CC2", "J3", "B5")

# CC pulldowns
add("CC1", "Rcc1", "1")
add("GND", "Rcc1", "2")
add("CC2", "Rcc2", "1")
add("GND", "Rcc2", "2")

# Decoupling
add("HX_VCC", "CHX1", "1")
add("GND", "CHX1", "2")
add("HX_VCC", "CHX2", "1")
add("GND", "CHX2", "2")
add("VCC", "CVCC", "1")
add("GND", "CVCC", "2")

# Debug / expansion header (2x6)
add("GND", "JDBG1", "1")
add("VCC", "JDBG1", "2")
add("UART2_RX", "JDBG1", "3")
add("UART2_TX", "JDBG1", "4")
add("SWDIO", "JDBG1", "5")
add("SWCLK", "JDBG1", "6")
add("NRST", "JDBG1", "7")
add("BOOT0", "JDBG1", "8")
add("I2C_SCL", "JDBG1", "9")
add("I2C_SDA", "JDBG1", "10")
add("GND", "JDBG1", "11")
add("VCC", "JDBG1", "12")

# Dedicated I2C/BOOT0 breakout (1x05)
add("GND", "JDBG_I2C", "1")
add("VCC", "JDBG_I2C", "2")
add("I2C_SCL", "JDBG_I2C", "3")
add("I2C_SDA", "JDBG_I2C", "4")
add("BOOT0", "JDBG_I2C", "5")

# Power flags
add("VCC", "PF_VCC", "1")
add("BAT", "PF_BAT", "1")
add("VBUS", "PF_VBUS", "1")
add("GND", "PF_GND", "1")
add("HX_VCC", "PF_HX", "1")
add("U3_L", "PF_U3L", "1")

NO_CONNECTS = [
    ("U1", "5"),
    ("U1", "12"),
    ("U1", "14"),
    ("U1", "20"),
    ("U1", "25"),
    ("U2", "2"),
    ("U2", "4"),
    ("U2", "13"),
    ("U2", "14"),
    ("J2", "1"),
    ("J2", "2"),
    ("J2", "3"),
    ("J2", "4"),
    ("J2", "5"),
    ("J2", "6"),
    ("J2", "7"),
    ("J2", "19"),
    ("J2", "20"),
    ("J2", "21"),
    ("J2", "22"),
    ("J2", "23"),
    ("J2", "24"),
    ("BT1", "3"),
    ("BT1", "4"),
    ("U4", "4"),
]

def clamp(val, lo, hi):
    return max(lo, min(hi, val))


class Sheet:
    def __init__(self, key, title, filename, refs, at, size=(80.0, 60.0), page=2):
        self.key = key
        self.title = title
        self.filename = filename
        self.refs = refs
        self.at = snap_pt(at)
        self.size = size
        self.page = page
        self.uuid = uuid.uuid4()
        self.file_uuid = uuid.uuid4()


ROOT_SHEET_UUID = uuid.uuid4()

SHEETS = [
    Sheet(
        key="all",
        title="Urine Monitor",
        filename="urine_monitor.kicad_sch",
        refs=list(INSTANCES.keys()),
        at=(0.0, 0.0),
        page=1,
        size=(A4_W, A4_H),
    ),
]

# Flattening support: when there is only one sheet and it is already the root filename,
# keep every path at "/" so KiCad CLI treats the file as a single-page design.
FLAT_MODE = len(SHEETS) == 1 and SHEETS[0].filename == "urine_monitor.kicad_sch"


def sch_header(title=None, sheet_uuid=None):
    lines = [
        '(kicad_sch (version 20231105) (generator "gen_urine_schematic")',
        f'  (uuid {sheet_uuid or uuid.uuid4()})',
        '  (paper "A4")',
        '  (title_block',
    ]
    if title:
        lines.append(f'    (title "{title}")')
    lines.append('  )')
    return lines


def emit_lib_symbols(instances):
    lines = ["  (lib_symbols"]
    seen = set()
    for inst in instances:
        sym = inst.sym
        if sym.lib_id in seen:
            continue
        seen.add(sym.lib_id)
        for ln in sym.raw_block.splitlines():
            lines.append("    " + ln)
    lines.append("  )")
    return lines


def emit_symbol(inst: Instance):
    x, y = inst.at
    fp = FOOTPRINTS.get(inst.ref)
    val = VALUES.get(inst.ref, inst.sym.lib_id.split(":")[-1])

    min_x, max_x, min_y, max_y = inst.sym.local_bbox()
    abs_top = y - max_y
    abs_bottom = y - min_y

    ref_y = snap(abs_top - 3 * PIN_TEXT_H)
    val_y = snap(abs_top - 1.5 * PIN_TEXT_H)
    lines = [
        f'  (symbol (lib_id "{inst.sym.lib_id}") (at {fmt(x)} {fmt(y)} 0) (unit 1)',
        '    (in_bom yes) (on_board yes)',
        f'    (uuid {inst.uuid})',
        f'    (property "Reference" "{inst.ref}" (id 0) (at {fmt(x)} {fmt(ref_y)} 0)',
        '      (effects (font (size 1.27 1.27)))',
        '    )',
        f'    (property "Value" "{val}" (id 1) (at {fmt(x)} {fmt(val_y)} 0)',
        '      (effects (font (size 1.27 1.27)))',
        '    )',
    ]
    if fp:
        fp_y = snap(abs_bottom + FOOTPRINT_OFFSET)
        lines.append(
            f'    (property "Footprint" "{fp}" (id 2) (at {fmt(x)} {fmt(fp_y)} 0) '
            f'(effects (font (size 1.27 1.27))))'
        )
    lines.append('  )')
    return lines

def emit_net(net, conns):
    """Place a short stub off each pin with an adjacent global label so nets join across sheets."""
    lines = []
    for _, _, x, y, dx, dy in conns:
        dx_use, dy_use = dx, dy
        if dx_use == 0 and dy_use == 0:
            dx_use = STUB_LEN
        stub_x = snap(x + dx_use)
        stub_y = snap(y + dy_use)
        lines.append(f'  (wire (pts (xy {fmt(x)} {fmt(y)}) (xy {fmt(stub_x)} {fmt(stub_y)})))')
        if abs(dx_use) >= abs(dy_use):
            justify = "right" if dx_use > 0 else "left"
            lx = stub_x
            ly = stub_y
        else:
            justify = "bottom" if dy_use > 0 else "top"
            lx = stub_x
            ly = stub_y
        lines.append(
            f'  (global_label "{net}" (shape passive) (at {fmt(lx)} {fmt(ly)} 0) '
            f'(effects (font (size 1.27 1.27)) (justify {justify})) (uuid {uuid.uuid4()}))'
        )
    return lines

def emit_no_connect(inst: Instance, pin):
    x, y = inst.pin_abs(pin)
    return f"  (no_connect (at {fmt(x)} {fmt(y)}) (uuid {uuid.uuid4()}))"

def sheet_path(sheet: Sheet) -> str:
    if FLAT_MODE:
        return "/"
    return f"/{ROOT_SHEET_UUID}/{sheet.uuid}"

def emit_sheet_block(sheet: Sheet):
    x, y = sheet.at
    w, h = sheet.size
    name_y = y - GRID
    file_y = y + h - GRID
    lines = [
        "  (sheet",
        f"    (at {fmt(x)} {fmt(y)})",
        f"    (size {fmt(w)} {fmt(h)})",
        "    (exclude_from_sim no)",
        "    (in_bom yes)",
        "    (on_board yes)",
        "    (dnp no)",
        "    (stroke (width 0) (type solid))",
        "    (fill (color 0 0 0 0.0000))",
        f"    (uuid {sheet.uuid})",
        f'    (property "Sheetname" "{sheet.title}" (at {fmt(x)} {fmt(name_y)} 0)',
        '      (effects (font (size 1.27 1.27)) (justify left bottom))',
        '    )',
        f'    (property "Sheetfile" "{sheet.filename}" (at {fmt(x)} {fmt(file_y)} 0)',
        '      (effects (font (size 1.27 1.27)) (justify left top))',
        '    )',
        '    (instances',
        f'      (project "urine_monitor" (path "{sheet_path(sheet)}" (page "{sheet.page}")))',
        '    )',
        '  )',
    ]
    return lines


def resolve_overlaps(instances, margin=GRID * 1.0, max_iter=25):
    """Simple repel pass: nudge overlapping symbols apart while staying on grid."""
    for _ in range(max_iter):
        moved = False
        bboxes = [inst.bbox_abs(margin) for inst in instances]
        for i in range(len(instances)):
            for j in range(i + 1, len(instances)):
                ax1, ax2, ay1, ay2 = bboxes[i]
                bx1, bx2, by1, by2 = bboxes[j]
                overlap_x = min(ax2, bx2) - max(ax1, bx1)
                overlap_y = min(ay2, by2) - max(ay1, by1)
                if overlap_x <= 0 or overlap_y <= 0:
                    continue
                # Move along the cheaper axis to break overlap.
                if overlap_x < overlap_y:
                    shift = snap(overlap_x / 2 + GRID)
                    xi, yi = instances[i].at
                    xj, yj = instances[j].at
                    instances[i].at = snap_pt((xi - shift, yi))
                    instances[j].at = snap_pt((xj + shift, yj))
                else:
                    shift = snap(overlap_y / 2 + GRID)
                    xi, yi = instances[i].at
                    xj, yj = instances[j].at
                    instances[i].at = snap_pt((xi, yi - shift))
                    instances[j].at = snap_pt((xj, yj + shift))
                moved = True
        if not moved:
            break


def build_edges(sheet_refs):
    """Return weighted pairwise edges between instances that share a net."""
    edges = []
    for net, conns in N.items():
        refs = [ref for ref, pin in conns if ref in sheet_refs]
        unique = sorted(set(refs))
        if len(unique) < 2:
            continue
        w = 1.0 / (len(unique) - 1)
        if net in ("SWDIO", "SWCLK", "I2C_SCL", "I2C_SDA"):
            w *= 1.5
        if net in ("UART2_RX", "UART2_TX", "EINK_SCK", "EINK_MOSI", "EINK_CS"):
            w *= 1.2
        for i in range(len(unique)):
            for j in range(i + 1, len(unique)):
                edges.append((unique[i], unique[j], w))
    return edges


def inst_net_map(sheet_refs):
    net_map = {ref: set() for ref in sheet_refs}
    for net, conns in N.items():
        for ref, pin in conns:
            if ref in net_map:
                net_map[ref].add(net)
    return net_map


def relax_layout(instances, sheet_refs):
    """Iteratively pull connected parts together, apply power/ground gravity, then de-overlap."""
    ref_to_inst = {inst.key: inst for inst in instances}
    edges = build_edges(sheet_refs)
    neighbors = {ref: [] for ref in sheet_refs}
    for a, b, w in edges:
        neighbors[a].append((b, w))
        neighbors[b].append((a, w))
    net_map = inst_net_map(sheet_refs)

    xs = [inst.at[0] for inst in instances]
    ys = [inst.at[1] for inst in instances]
    pad = GRID * 10
    bounds = (
        min(xs) - pad,
        max(xs) + pad,
        min(ys) - pad,
        max(ys) + pad,
    )

    def clamp_to_bounds(pt):
        x, y = pt
        return clamp(x, bounds[0], bounds[1]), clamp(y, bounds[2], bounds[3])

    for _ in range(12):
        moved = False
        for inst in instances:
            neigh = neighbors.get(inst.key)
            if not neigh:
                continue
            wx = wy = 0.0
            wsum = 0.0
            for nb_ref, w in neigh:
                nb = ref_to_inst[nb_ref]
                wx += nb.at[0] * w
                wy += nb.at[1] * w
                wsum += w
            if wsum == 0:
                continue
            tx = wx / wsum
            ty = wy / wsum
            dx = tx - inst.at[0]
            dy = ty - inst.at[1]
            step_x = 0.0
            step_y = 0.0
            if abs(dx) > GRID * 0.5:
                step_x = GRID if dx > 0 else -GRID
            if abs(dy) > GRID * 0.5:
                step_y = GRID if dy > 0 else -GRID

            nets = net_map.get(inst.key, set())
            if nets & TOP_NETS:
                step_y -= GRID * 0.5
            if nets & BOTTOM_NETS:
                step_y += GRID * 0.5

            if step_x or step_y:
                nx = snap(inst.at[0] + step_x)
                ny = snap(inst.at[1] + step_y)
                nx, ny = clamp_to_bounds((nx, ny))
                nx, ny = snap_pt((nx, ny))
                if (nx, ny) != inst.at:
                    inst.at = (nx, ny)
                    moved = True
        resolve_overlaps(instances, margin=GRID * 1.0, max_iter=6)
        if not moved:
            break

    # Center the cluster on the A4 page to avoid drifting to corners.
    bboxes = [inst.bbox_abs(0) for inst in instances]
    min_x = min(b[0] for b in bboxes)
    max_x = max(b[1] for b in bboxes)
    min_y = min(b[2] for b in bboxes)
    max_y = max(b[3] for b in bboxes)
    cx = (min_x + max_x) / 2
    cy = (min_y + max_y) / 2
    target_cx = A4_W / 2
    target_cy = A4_H / 2
    dx = snap(target_cx - cx)
    dy = snap(target_cy - cy)
    for inst in instances:
        inst.at = snap_pt((inst.at[0] + dx, inst.at[1] + dy))

    # Fit the cluster within page margins.
    margin = GRID * 8  # ~10 mm
    bboxes = [inst.bbox_abs(0) for inst in instances]
    min_x = min(b[0] for b in bboxes)
    max_x = max(b[1] for b in bboxes)
    min_y = min(b[2] for b in bboxes)
    max_y = max(b[3] for b in bboxes)
    shift_x = 0.0
    shift_y = 0.0
    if min_x < margin:
        shift_x = margin - min_x
    if max_x > A4_W - margin:
        shift_x = -(max_x - (A4_W - margin)) if shift_x == 0 else shift_x
    if min_y < margin:
        shift_y = margin - min_y
    if max_y > A4_H - margin:
        shift_y = -(max_y - (A4_H - margin)) if shift_y == 0 else shift_y
    if shift_x or shift_y:
        for inst in instances:
            inst.at = snap_pt((inst.at[0] + shift_x, inst.at[1] + shift_y))

def build_sheet(sheet: Sheet):
    inst_map = {ref: INSTANCES[ref] for ref in sheet.refs}
    instances = list(inst_map.values())
    relax_layout(instances, sheet.refs)
    lines = sch_header(sheet.title, sheet.file_uuid)
    lines.extend(emit_lib_symbols(instances))

    for inst in instances:
        lines.extend(emit_symbol(inst))

    lines.append("  (symbol_instances")
    for inst in instances:
        lines.append(f'    (path "{sheet_path(sheet)}" (reference "{inst.ref}") (unit 1))')
    lines.append("  )")

    for net, conns in sorted(N.items()):
        usable = []
        for ref, pin in conns:
            if ref not in sheet.refs:
                continue
            inst = INSTANCES.get(ref)
            if not inst:
                continue
            x, y = inst.pin_abs(pin)
            dx, dy = inst.pin_dir(pin, STUB_LEN)
            if dx == 0 and dy == 0:
                dx = STUB_LEN
            usable.append((ref, pin, x, y, dx, dy))
        if usable:
            lines.extend(emit_net(net, usable))

    for ref, pin in NO_CONNECTS:
        if ref in sheet.refs:
            lines.append(emit_no_connect(INSTANCES[ref], pin))

    lines.append("  (sheet_instances")
    lines.append(f'    (path "{sheet_path(sheet)}" (page "{sheet.page if not FLAT_MODE else 1}"))')
    lines.append("  )")
    lines.append("  (embedded_fonts no)")
    lines.append(")")
    return "\n".join(ln for ln in lines if ln is not None)

def build_root():
    lines = sch_header("Urine Monitor", ROOT_SHEET_UUID)
    lines.append("  (lib_symbols)")
    for sheet in SHEETS:
        lines.extend(emit_sheet_block(sheet))

    lines.append("  (sheet_instances")
    lines.append('    (path "/" (page "1"))')
    for sheet in SHEETS:
        lines.append(f'    (path "{sheet_path(sheet)}" (page "{sheet.page}"))')
    lines.append("  )")
    lines.append("  (embedded_fonts no)")
    lines.append(")")
    return "\n".join(ln for ln in lines if ln is not None)

def build_all():
    out_files = []
    if len(SHEETS) == 1 and SHEETS[0].filename == "urine_monitor.kicad_sch":
        contents = build_sheet(SHEETS[0])
        path = OUT_DIR / "urine_monitor.kicad_sch"
        path.write_text(contents)
        out_files.append(path)
        return out_files

    for sheet in SHEETS:
        contents = build_sheet(sheet)
        path = OUT_DIR / sheet.filename
        path.write_text(contents)
        out_files.append(path)
    root_path = OUT_DIR / "urine_monitor.kicad_sch"
    root_path.write_text(build_root())
    out_files.append(root_path)
    return out_files


written = build_all()
print("Wrote:")
for p in written:
    print(f" - {p}")
