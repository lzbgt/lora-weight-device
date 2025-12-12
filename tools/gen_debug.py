import math
import re
import uuid
from pathlib import Path

# =============================================================================
# CONSTANTS & CONFIGURATION
# =============================================================================

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "hardware" / "pcb"
SYM_BASE = Path("/Applications/kicad/kicad.app/Contents/SharedSupport/symbols")

GRID = 1.27  # 50 mil for clean snapping
STUB_LEN = GRID * 4  # medium stubs to push labels away from the body
ANCHOR_DIST = GRID * 3
LABEL_NUDGE = GRID * 0.5  # small offset to keep text off the wire

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

    def pin(self, num):
        for p in self.pins:
            if p.num == num:
                return p
        raise KeyError(f"pin {num} not found in {self.lib_id}")


# FIXED PARSER
def extract_block_from(text, start_index):
    depth = 0
    in_quote = False
    escaped = False
    
    for i in range(start_index, len(text)):
        char = text[i]
        
        if in_quote:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                in_quote = False
        else:
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
                if depth == 0:
                    return text[start_index : i + 1]
            elif char == '"':
                in_quote = True
                
    raise ValueError(f"unbalanced block starting at {start_index}")

def extract_block(text, start_keyword):
    start = text.find(start_keyword)
    if start == -1:
        raise ValueError(f"{start_keyword} not found")
    return extract_block_from(text, start)


def parse_symbol(lib, name, alias_lib=None):
    lib_path = LIB_PATHS[lib]
    text = lib_path.read_text()
    lib_id = alias_lib or lib
    block = extract_block(text, f'(symbol "{name}"')
    block = block.replace(f'(symbol "{name}"', f'(symbol "{lib_id}:{name}"', 1)
    pins = []
    idx = 0
    while True:
        pin_start = block.find("(pin", idx)
        if pin_start == -1:
            break
        pin_block = extract_block_from(block, pin_start) # Use fixed parser
        at_m = re.search(r"\\(at ([^)]+))\", pin_block)
        name_m = re.search(r'\\(name "([^"]*)")', pin_block)
        num_m = re.search(r'\\(number "([^"]*)")', pin_block)
        if at_m and name_m and num_m:
            pins.append(Pin(num_m.group(1), name_m.group(1), at_m.group(1)))
        idx = pin_start + len(pin_block)
    if not pins:
        raise ValueError(f"no pins parsed for {lib}:{name}")
    return Symbol(f"{lib_id}:{name}", pins, block)


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
        self.ref = ref
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
        key="mcu_debug",
        title="MCU + Debug",
        filename="urine_monitor_mcu.kicad_sch",
        refs=["U1", "JDBG1", "JDBG_I2C", "Rled", "LED", "SW1", "B1", "Q2"],
        at=(35.56, 38.1),
        page=2,
    ),
    Sheet(
        key="load_cell",
        title="Load Cell + HX711",
        filename="urine_monitor_hx711.kicad_sch",
        refs=["U2", "J1", "Q1", "Rgate", "CHX1", "CHX2", "PF_HX"],
        at=(125.73, 38.1),
        page=3,
    ),
    Sheet(
        key="power",
        title="Power Entry + Regulation",
        filename="urine_monitor_power.kicad_sch",
        refs=[
            "U3",
            "L1",
            "Dboost",
            "BT1",
            "U4",
            "Dusb",
            "J3",
            "Rcc1",
            "Rcc2",
            "PF_VCC",
            "PF_BAT",
            "PF_VBUS",
            "PF_GND",
            "PF_U3L",
            "Rtop",
            "Rbot",
            "CVCC",
        ],
        at=(35.56, 114.3),
        page=4,
    ),
    Sheet(
        key="display",
        title="E-Ink Display",
        filename="urine_monitor_display.kicad_sch",
        refs=["J2"],
        at=(125.73, 114.3),
        page=5,
    ),
]


def sch_header(title=None, sheet_uuid=None):
    lines = [
        '(kicad_sch (version 20231105) (generator "gen_urine_schematic")',
        f