import uuid
from pathlib import Path
import re
import math

ROOT = Path(__file__).resolve().parents[1]
SYM_BASE = Path('/Applications/kicad/kicad.app/Contents/SharedSupport/symbols')
PAGE_W = 297.0  # A4 mm
PAGE_H = 210.0
SAFE = 12.0

# Library resolution
LIB_PATHS = {
    'Project_Lib': ROOT / 'hardware/pcb/project_lib.kicad_sym',
    'Analog_ADC': SYM_BASE / 'Analog_ADC.kicad_sym',
    'Connector_Generic': SYM_BASE / 'Connector_Generic.kicad_sym',
    'Connector': SYM_BASE / 'Connector.kicad_sym',
    'Device': SYM_BASE / 'Device.kicad_sym',
    'Transistor_FET': SYM_BASE / 'Transistor_FET.kicad_sym',
    'Regulator_Switching': SYM_BASE / 'Regulator_Switching.kicad_sym',
    'Regulator_Linear': SYM_BASE / 'Regulator_Linear.kicad_sym',
    'Switch': SYM_BASE / 'Switch.kicad_sym',
    'Power': SYM_BASE / 'power.kicad_sym',
}

class Pin:
    def __init__(self, num, name, at):
        self.num = num
        self.name = name
        parts = at.split()
        self.x, self.y = map(float, parts[:2])
        self.rot = float(parts[2]) if len(parts) > 2 else 0.0

    def dir_vec(self, length=2.54):
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
        raise KeyError(f'pin {num} not found in {self.lib_id}')

def extract_block(text, start_keyword):
    start = text.find(start_keyword)
    if start == -1:
        raise ValueError(f'{start_keyword} not found')
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    raise ValueError('unbalanced')

def extract_block_from(text, start_index):
    depth = 0
    for i in range(start_index, len(text)):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return text[start_index:i+1]
    raise ValueError('unbalanced')

def parse_symbol(lib, name):
    lib_path = LIB_PATHS[lib]
    text = lib_path.read_text()
    block = extract_block(text, f'(symbol "{name}"')
    block = block.replace(f'(symbol "{name}"', f'(symbol "{lib}:{name}"', 1)
    pins = []
    idx = 0
    while True:
        pin_start = block.find('(pin', idx)
        if pin_start == -1:
            break
        pin_block = extract_block_from(block, pin_start)
        at_m = re.search(r'\(at ([^)]+)\)', pin_block)
        name_m = re.search(r'\(name "([^"]*)"', pin_block)
        num_m = re.search(r'\(number "([^"]*)"', pin_block)
        if at_m and name_m and num_m:
            pins.append(Pin(num_m.group(1), name_m.group(1), at_m.group(1)))
        idx = pin_start + len(pin_block)
    if not pins:
        raise ValueError(f'no pins parsed for {lib}:{name}')
    return Symbol(f'{lib}:{name}', pins, block)

# Load symbols used
SYM_CACHE = {
    'RAK3172': parse_symbol('Project_Lib', 'RAK3172'),
    'GDEY0213B74': parse_symbol('Project_Lib', 'GDEY0213B74'),
    'HX711': parse_symbol('Analog_ADC', 'HX711'),
    'Conn_01x04': parse_symbol('Connector_Generic', 'Conn_01x04'),
    'Q_PMOS_GSD': parse_symbol('Transistor_FET', 'Q_PMOS_GSD'),
    'Q_NMOS_GSD': parse_symbol('Transistor_FET', 'Q_NMOS_GSD'),
    'R': parse_symbol('Device', 'R'),
    'L': parse_symbol('Device', 'L'),
    'D_Schottky_Small': parse_symbol('Device', 'D_Schottky_Small'),
    'C': parse_symbol('Device', 'C'),
    'Buzzer': parse_symbol('Device', 'Buzzer'),
    'LED': parse_symbol('Device', 'LED'),
    'SW_Push': parse_symbol('Switch', 'SW_Push'),
    'TPS61220DCK': parse_symbol('Regulator_Switching', 'TPS61220DCK'),
    'MIC5504-3.3YM5': parse_symbol('Regulator_Linear', 'MIC5504-3.3YM5'),
    'USB_C_Receptacle_PowerOnly_6P': parse_symbol('Connector', 'USB_C_Receptacle_PowerOnly_6P'),
    'PWR_FLAG': parse_symbol('Power', 'PWR_FLAG'),
}

# Optional footprint assignments for clearer netlist/PCB flow
FOOTPRINTS = {
    'U1': 'RF_Module:RAK3172',
    'U2': 'Package_SO:SOIC-16_3.9x9.9mm_P1.27mm',
    'J1': 'Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical',
    'BT1': 'Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical',
    'Q1': 'Package_TO_SOT_SMD:SOT-23',
    'Q2': 'Package_TO_SOT_SMD:SOT-23',
    'Rgate': 'Resistor_SMD:R_0603_1608Metric',
    'Rtop': 'Resistor_SMD:R_0603_1608Metric',
    'Rbot': 'Resistor_SMD:R_0603_1608Metric',
    'Rled': 'Resistor_SMD:R_0603_1608Metric',
    'Rcc1': 'Resistor_SMD:R_0603_1608Metric',
    'Rcc2': 'Resistor_SMD:R_0603_1608Metric',
    'CHX1': 'Capacitor_SMD:C_0603_1608Metric',
    'CHX2': 'Capacitor_SMD:C_0603_1608Metric',
    'CVCC': 'Capacitor_SMD:C_0603_1608Metric',
    'L1': 'Inductor_SMD:L_0603_1608Metric',
    'Dboost': 'Diode_SMD:D_SOD-123',
    'Dusb': 'Diode_SMD:D_SOD-123',
    'B1': 'Buzzer_Beeper:MagneticBuzzer_CUI_CMT-8504-100-SMT',
    'LED': 'LED_SMD:LED_0603_1608Metric',
    'SW1': 'Button_Switch_SMD:SW_SPST_TL3342',
    'U3': 'Package_TO_SOT_SMD:SC-70-6_1.6x1.5mm_P0.5mm',
    'U4': 'Package_TO_SOT_SMD:SOT-23-5',
    'JUSB': 'Connector_USB:USB_C_Receptacle_GT-USB-7010',
}

# Global bounds (filled during build after placement)
BOUNDS = {}

class Instance:
    def __init__(self, ref, sym_name, at):
        self.ref = ref
        self.sym = SYM_CACHE[sym_name]
        self.at = at
        self.uuid = uuid.uuid4()

    def pin_abs(self, pin_num):
        p = self.sym.pin(pin_num)
        return (self.at[0] + p.x, self.at[1] + p.y)

# define instances
INSTANCES = {
    'U1': Instance('U1', 'RAK3172', (120, 100)),
    'U2': Instance('U2', 'HX711', (40, 110)),
    'J1': Instance('J1', 'Conn_01x04', (10, 100)),
    'Q1': Instance('Q1', 'Q_PMOS_GSD', (70, 138)),
    'Rgate': Instance('R3', 'R', (70, 128)),
    'Rtop': Instance('R1', 'R', (90, 120)),
    'Rbot': Instance('R2', 'R', (90, 110)),
    'Q2': Instance('Q2', 'Q_NMOS_GSD', (150, 116)),
    'B1': Instance('BZ1', 'Buzzer', (160, 120)),
    'Rled': Instance('R4', 'R', (150, 104)),
    'LED': Instance('D1', 'LED', (158, 104)),
    'SW1': Instance('SW1', 'SW_Push', (150, 90)),
    'J2': Instance('J2', 'GDEY0213B74', (220, 80)),
    'U3': Instance('U3', 'TPS61220DCK', (60, 70)),
    'L1': Instance('L1', 'L', (46, 70)),
    'Dboost': Instance('D2', 'D_Schottky_Small', (80, 76)),
    'U4': Instance('U4', 'MIC5504-3.3YM5', (180, 40)),
    'Dusb': Instance('D3', 'D_Schottky_Small', (200, 46)),
    'JUSB': Instance('J3', 'USB_C_Receptacle_PowerOnly_6P', (210, 20)),
}

# Net map: net name -> list of (ref, pin_number)
N = {}

def add(net, ref, pin):
    N.setdefault(net, []).append((ref, pin))

# MCU pins
add('UART2_RX', 'U1', '1')
add('UART2_TX', 'U1', '2')
add('HX711_DT', 'U1', '3')
add('HX711_SCK', 'U1', '4')
add('EINK_DC', 'U1', '6')
add('EINK_MOSI', 'U1', '13')
add('EINK_SCK', 'U1', '15')
add('EINK_CS', 'U1', '16')
add('BUZZ_PWM', 'U1', '19')
add('LED_STATUS', 'U1', '26')
add('EINK_RST', 'U1', '27')
add('EINK_BUSY', 'U1', '29')
add('HX_GATE', 'U1', '30')
add('BAT_SENSE', 'U1', '31')
add('BTN_USER', 'U1', '32')
add('VCC', 'U1', '24')
for gpin in ['11','17','18','23','28']:
    add('GND', 'U1', gpin)

# HX711 pins
add('HX_VCC', 'U2', '1')
add('HX_VCC', 'U2', '3')
add('HX_VCC', 'U2', '16')
add('GND', 'U2', '5')
add('HX711_SCK', 'U2', '11')
add('HX711_DT', 'U2', '12')
add('HX_INB+', 'U2', '10')
add('HX_INB-', 'U2', '9')
add('GND', 'U2', '15')
add('GND', 'U2', '7')
add('GND', 'U2', '8')
add('GND', 'U2', '6')

# Load cell connector
add('HX_VCC', 'J1', '1')
add('GND', 'J1', '2')
add('HX_INB+', 'J1', '3')
add('HX_INB-', 'J1', '4')

# Power gate PMOS
add('HX_VCC', 'Q1', '3')
add('VCC', 'Q1', '2')
add('HX_GATE', 'Q1', '1')
add('VCC', 'Rgate', '1')
add('HX_GATE', 'Rgate', '2')

# Battery sense divider
add('VCC', 'Rtop', '1')
add('BAT_SENSE', 'Rtop', '2')
add('BAT_SENSE', 'Rbot', '1')
add('GND', 'Rbot', '2')

# Buzzer driver
add('VCC', 'B1', '1')
add('BUZZ_SINK', 'B1', '2')
add('BUZZ_SINK', 'Q2', '3')
add('GND', 'Q2', '2')
add('BUZZ_PWM', 'Q2', '1')

# LED
add('VCC', 'Rled', '1')
add('LED_NET', 'Rled', '2')
add('LED_NET', 'LED', '1')
add('LED_STATUS', 'LED', '2')

# Button
add('BTN_USER', 'SW1', '1')
add('GND', 'SW1', '2')

# E-ink
add('EINK_BUSY', 'J2', '9')
add('EINK_RST', 'J2', '10')
add('EINK_DC', 'J2', '11')
add('EINK_CS', 'J2', '12')
add('EINK_SCK', 'J2', '13')
add('EINK_MOSI', 'J2', '14')
add('VCC', 'J2', '15')
add('VCC', 'J2', '16')
add('GND', 'J2', '17')
add('VCC', 'J2', '18')
add('GND', 'J2', '8')

# Boost converter TPS61220
add('BAT', 'U3', '1')
add('BAT', 'U3', '5')
add('BAT', 'L1', '1')
add('U3_L', 'L1', '2')
add('U3_L', 'U3', '5')
add('GND', 'U3', '3')
add('BAT', 'U3', '6')
add('U3_OUT', 'U3', '4')
add('U3_OUT', 'U3', '2')
add('U3_OUT', 'Dboost', '2')
add('VCC', 'Dboost', '1')

# LDO MIC5504
add('VBUS', 'U4', '1')
add('GND', 'U4', '2')
add('VBUS', 'U4', '3')
add('U4_OUT', 'U4', '5')
add('GND', 'U4', '4')
add('U4_OUT', 'Dusb', '2')
add('VCC', 'Dusb', '1')

# USB-C connector
add('VBUS', 'JUSB', 'A9')
add('VBUS', 'JUSB', 'B9')
add('GND', 'JUSB', 'A12')
add('GND', 'JUSB', 'B12')
add('GND', 'JUSB', 'S1')
add('CC1', 'JUSB', 'A5')
add('CC2', 'JUSB', 'B5')

# CC pulldowns
INSTANCES['Rcc1'] = Instance('R5', 'R', (230, 10))
INSTANCES['Rcc2'] = Instance('R6', 'R', (234, 10))
add('CC1', 'Rcc1', '1'); add('GND', 'Rcc1', '2')
add('CC2', 'Rcc2', '1'); add('GND', 'Rcc2', '2')

# Battery holder placeholder using Conn_01x04 (pins 1+,2-)
INSTANCES['BT1'] = Instance('BT1', 'Conn_01x04', (0, 60))
add('BAT', 'BT1', '1')
add('GND', 'BT1', '2')

# HX711 decoupling
INSTANCES['CHX1'] = Instance('C1', 'C', (54, 124))
INSTANCES['CHX2'] = Instance('C2', 'C', (58, 118))
add('HX_VCC', 'CHX1', '1'); add('GND', 'CHX1', '2')
add('HX_VCC', 'CHX2', '1'); add('GND', 'CHX2', '2')

# System bulk decoupling on VCC
INSTANCES['CVCC'] = Instance('C3', 'C', (130, 80))
add('VCC', 'CVCC', '1'); add('GND', 'CVCC', '2')

# Power flags for ERC
INSTANCES['PF_VCC'] = Instance('PWR1', 'PWR_FLAG', (112, 72))
INSTANCES['PF_BAT'] = Instance('PWR2', 'PWR_FLAG', (12, 62))
INSTANCES['PF_VBUS'] = Instance('PWR3', 'PWR_FLAG', (190, 32))
INSTANCES['PF_GND'] = Instance('PWR4', 'PWR_FLAG', (0, 54))
add('VCC', 'PF_VCC', '1')
add('BAT', 'PF_BAT', '1')
add('VBUS', 'PF_VBUS', '1')
add('GND', 'PF_GND', '1')

# simple emitter

def sch_header():
    return [
        '(kicad_sch (version 20250114) (generator "gen_urine_schematic")',
        f'  (uuid {uuid.uuid4()})',
        '  (paper "A4")',
        '  (title_block)',
    ]

def emit_symbol(inst):
    x,y = inst.at
    fp = FOOTPRINTS.get(inst.ref)
    lines = [f'  (symbol (lib_id "{inst.sym.lib_id}") (at {x} {y} 0) (unit 1)',
             '    (in_bom yes) (on_board yes)',
             f'    (uuid {inst.uuid})',
             f'    (property "Reference" "{inst.ref}" (id 0) (at {x} {y-5} 0)',
             '      (effects (font (size 1.27 1.27)))',
             '    )',
             f'    (property "Value" "{inst.sym.lib_id.split(":")[-1]}" (id 1) (at {x} {y+5} 0)',
             '      (effects (font (size 1.27 1.27)))',
             '    )',
    ]
    if fp:
        lines.append(f'    (property "Footprint" "{fp}" (id 2) (at {x} {y+7} 0) (effects (font (size 1.27 1.27))))')
    lines.append('  )')
    return lines


def emit_stub_with_label(net, inst, pin):
    p = inst.sym.pin(pin)
    pin_x, pin_y = inst.pin_abs(pin)
    dx, dy = p.dir_vec()
    # ensure a minimum stub length
    if dx == 0 and dy == 0:
        dx = 2.54
    end_x, end_y = pin_x + dx, pin_y + dy
    return [
        f'  (wire (pts (xy {pin_x:.2f} {pin_y:.2f}) (xy {end_x:.2f} {end_y:.2f})))',
        f'  (label "{net}" (at {end_x:.2f} {end_y:.2f} 0) (effects (font (size 1.27 1.27))))'
    ]

def emit_net_manhattan(net, conns):
    """Connect all pins of a net to a shared local anchor with orthogonal segments and one label."""
    if not conns:
        return []
    # anchor near first pin, offset along its direction
    ref0, pin0, x0, y0, dx0, dy0 = conns[0]
    norm0 = math.hypot(dx0, dy0)
    if norm0 == 0:
        dirx0, diry0 = 1.0, 0.0
    else:
        dirx0, diry0 = dx0 / norm0, dy0 / norm0
    anchor_dist = 15.0
    ax = x0 + dirx0 * anchor_dist
    ay = y0 + diry0 * anchor_dist
    ax = min(max(ax, SAFE), PAGE_W - SAFE)
    ay = min(max(ay, SAFE), PAGE_H - SAFE)

    lines = []
    stub = 3.0
    for _, _, x, y, dx, dy in conns:
        norm = math.hypot(dx, dy)
        if norm == 0:
            dirx, diry = 1.0, 0.0
        else:
            dirx, diry = dx / norm, dy / norm
        sx = x + dirx * stub
        sy = y + diry * stub
        # route from stub to anchor (horizontal then vertical)
        if sx != ax:
            lines.append(f'  (wire (pts (xy {sx:.2f} {sy:.2f}) (xy {ax:.2f} {sy:.2f})))')
        if sy != ay:
            lines.append(f'  (wire (pts (xy {ax:.2f} {sy:.2f}) (xy {ax:.2f} {ay:.2f})))')
        if sx == ax and sy == ay:
            lines.append(f'  (wire (pts (xy {ax:.2f} {ay:.2f}) (xy {ax:.2f} {ay + 0.01:.2f})))')
    if len(conns) >= 2:
        lines.append(f'  (junction (at {ax:.2f} {ay:.2f}))')
    label_x, label_y = ax + 2.54, ay
    lines.append(f'  (wire (pts (xy {ax:.2f} {ay:.2f}) (xy {label_x:.2f} {label_y:.2f})))')
    lines.append(f'  (label "{net}" (at {label_x:.2f} {label_y:.2f} 0) (effects (font (size 1.27 1.27))))')
    return lines

def compute_shift(target=(150, 100)):
    xs = [inst.at[0] for inst in INSTANCES.values()]
    ys = [inst.at[1] for inst in INSTANCES.values()]
    if not xs or not ys:
        return (0, 0)
    mid_x = (min(xs) + max(xs)) / 2
    mid_y = (min(ys) + max(ys)) / 2
    return (target[0] - mid_x, target[1] - mid_y)

def apply_shift(shift):
    dx, dy = shift
    for inst in INSTANCES.values():
        x, y = inst.at
        inst.at = (x + dx, y + dy)

def compute_bounds(pad=10):
    xs = [inst.at[0] for inst in INSTANCES.values()]
    ys = [inst.at[1] for inst in INSTANCES.values()]
    if not xs or not ys:
        return {'min_x': 0, 'max_x': 0, 'min_y': 0, 'max_y': 0}
    return {
        'min_x': min(xs) - pad,
        'max_x': max(xs) + pad,
        'min_y': min(ys) - pad,
        'max_y': max(ys) + pad,
    }

def build():
    global BOUNDS
    shift = compute_shift()
    apply_shift(shift)
    BOUNDS = compute_bounds()
    lines = sch_header()
    # cache blocks for symbols actually used on the sheet
    seen = set()
    lines.append('  (lib_symbols')
    for inst in INSTANCES.values():
        sym = inst.sym
        if sym.lib_id in seen:
            continue
        seen.add(sym.lib_id)
        # indent embedded symbol definition to keep schematic self-contained
        for ln in sym.raw_block.splitlines():
            lines.append('    ' + ln)
    lines.append('  )')
    for inst in INSTANCES.values():
        lines.extend(emit_symbol(inst))
    # symbol instances for placed symbols
    lines.append('  (symbol_instances')
    for inst in INSTANCES.values():
        lines.append(f'    (path "/" (reference "{inst.ref}") (unit 1))')
    lines.append('  )')
    for net, conns in N.items():
        usable = []
        for ref, pin in conns:
            if ref not in INSTANCES:
                continue
            inst = INSTANCES[ref]
            try:
                x, y = inst.pin_abs(pin)
                p = inst.sym.pin(pin)
                dx, dy = p.dir_vec()
            except KeyError:
                continue
            usable.append((ref, pin, x, y, dx, dy))
        if not usable:
            continue
        lines.extend(emit_net_manhattan(net, usable))
    lines.append('  (sheet_instances (path "/" (page "1")))')
    lines.append('  (embedded_fonts no)')
    lines.append(')')
    return '\n'.join(lines)

out_path = ROOT / 'hardware/pcb/urine_monitor.kicad_sch'
out_path.write_text(build())
print(f'Wrote {out_path}')
