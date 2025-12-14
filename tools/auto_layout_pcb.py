#!/Applications/kicad/kicad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
Quick-and-dirty PCB auto layout helper for KiCad.

Given a KiCad schematic, this script:
 1) Exports a kicadsexpr netlist via kicad-cli.
 2) Builds a new board, instantiates footprints, assigns nets.
 3) Places parts on a loose grid with simple clustering.
 4) Writes a .kicad_pcb you can open in KiCad and route.

This is NOT a full autorouter; it only gets you to a placed, net-connected board.
"""
import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import wx

# pcbnew/pcbnew.wx is sensitive to wxApp init ordering in headless mode.
_WX_APP = wx.GetApp() or wx.App(False)

import pcbnew
import sexpdata

ROOT = Path(__file__).resolve().parents[1]
KI_FOOTPRINTS = Path("/Applications/kicad/kicad.app/Contents/SharedSupport/footprints")
PROJECT_FP = ROOT / "hardware" / "pcb"
KICAD_CLI = Path("/Applications/kicad/kicad.app/Contents/MacOS/kicad-cli")
# Default to a tall board so the USB-C connector can sit centered on a short edge.
DEFAULT_BOARD_W_MM = 60.0
DEFAULT_BOARD_H_MM = 80.0


def run(cmd):
    subprocess.run(cmd, check=True)


def export_netlist(sch_path: Path) -> Path:
    tmp = Path(tempfile.mkstemp(suffix=".net")[1])
    run(
        [
            str(KICAD_CLI),
            "sch",
            "export",
            "netlist",
            str(sch_path),
            "-o",
            str(tmp),
        ]
    )
    return tmp


def export_board_svg(board_path: Path, svg_path: Path):
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            str(KICAD_CLI),
            "pcb",
            "export",
            "svg",
            str(board_path),
            "--layers",
            "F.Cu,F.SilkS,Edge.Cuts",
            "--fit-page-to-board",
            "--exclude-drawing-sheet",
            "-o",
            str(svg_path),
        ]
    )


def convert_svg_to_png(svg_path: Path, png_path: Path):
    png_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["magick", "-density", "300", str(svg_path), str(png_path)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def verify_placement(board_w_mm: float, board_h_mm: float, footprints, fixed_targets):
    def mm(x):
        return pcbnew.FromMM(x)

    def bbox(fp):
        r = fp.GetBoundingBox(False)
        return (r.GetLeft(), r.GetRight(), r.GetTop(), r.GetBottom())

    def pad_bbox(fp):
        min_l = min_t = None
        max_r = max_b = None
        for pad in fp.Pads():
            r = pad.GetBoundingBox()
            l, rr, t, b = r.GetLeft(), r.GetRight(), r.GetTop(), r.GetBottom()
            min_l = l if min_l is None else min(min_l, l)
            max_r = rr if max_r is None else max(max_r, rr)
            min_t = t if min_t is None else min(min_t, t)
            max_b = b if max_b is None else max(max_b, b)
        if min_l is None:
            l, rr, t, b = bbox(fp)
            return l, rr, t, b
        return min_l, max_r, min_t, max_b

    out_of_bounds = []
    for fp in footprints:
        l, r, t, b = pad_bbox(fp)
        if l < 0 or t < 0 or r > mm(board_w_mm) or b > mm(board_h_mm):
            out_of_bounds.append(fp.GetReference())

    overlaps = []
    for i, fp_a in enumerate(footprints):
        la, ra, ta, ba = bbox(fp_a)
        for fp_b in footprints[i + 1 :]:
            lb, rb, tb, bb = bbox(fp_b)
            overlap_x = min(ra, rb) - max(la, lb)
            overlap_y = min(ba, bb) - max(ta, tb)
            if overlap_x > mm(0.2) and overlap_y > mm(0.2):
                overlaps.append((fp_a.GetReference(), fp_b.GetReference()))

    anchor_bad = []
    for ref, (tx, ty) in fixed_targets.items():
        fp = next((f for f in footprints if f.GetReference() == ref), None)
        if not fp:
            continue
        pos = fp.GetPosition()
        dx = abs(pcbnew.ToMM(pos.x) - tx)
        dy = abs(pcbnew.ToMM(pos.y) - ty)
        if dx > 15 or dy > 15:
            anchor_bad.append(ref)

    ok = not out_of_bounds and not overlaps and not anchor_bad
    if not ok:
        print("[placement_check] FAILED")
        if out_of_bounds:
            print(" - out_of_bounds:", ", ".join(sorted(out_of_bounds)))
        if overlaps:
            print(" - overlaps:", ", ".join(f"{a}/{b}" for a, b in overlaps[:30]))
        if anchor_bad:
            print(" - anchors_off:", ", ".join(sorted(anchor_bad)))
    else:
        print("[placement_check] OK")
    return ok


def parse_netlist(net_path: Path):
    data = sexpdata.loads(net_path.read_text())
    comps = []
    nets = []
    # netlist format: (export (...) (components (...)) (nets (...)))
    for entry in data:
        if isinstance(entry, list) and entry and isinstance(entry[0], sexpdata.Symbol):
            tag = entry[0].value()
            if tag == "components":
                for comp in entry[1:]:
                    if not isinstance(comp, list) or not comp:
                        continue
                    if comp[0].value() != "comp":
                        continue
                    ref = comp[1][1]
                    footprint = None
                    value = None
                    for c in comp:
                        if isinstance(c, list) and c:
                            if (
                                isinstance(c[0], sexpdata.Symbol)
                                and c[0].value() == "footprint"
                            ):
                                footprint = c[1]
                            if (
                                isinstance(c[0], sexpdata.Symbol)
                                and c[0].value() == "value"
                            ):
                                value = c[1]
                    comps.append({"ref": ref, "fp": footprint, "value": value})
            if tag == "nets":
                for net in entry[1:]:
                    if not isinstance(net, list) or not net:
                        continue
                    if net[0].value() != "net":
                        continue
                    name = None
                    nodes = []
                    for n in net[1:]:
                        if isinstance(n, list) and n:
                            sym = n[0].value() if isinstance(n[0], sexpdata.Symbol) else ""
                            if sym == "name":
                                name = n[1]
                            if sym == "node":
                                ref = ""
                                pin = ""
                                for field in n[1:]:
                                    if isinstance(field, list) and field:
                                        ftag = field[0].value()
                                        if ftag == "ref":
                                            ref = field[1]
                                        if ftag == "pin":
                                            pin = field[1]
                                nodes.append((ref, pin))
                    nets.append({"name": name, "nodes": nodes})
    return comps, nets


def resolve_fp_path(lib: str, name: str):
    # Check project-local lib first
    proj_dir = PROJECT_FP / f"{lib}.pretty"
    if proj_dir.exists():
        return proj_dir
    sys_dir = KI_FOOTPRINTS / f"{lib}.pretty"
    if sys_dir.exists():
        return sys_dir
    return None


def load_footprint(lib_and_name: str):
    if ":" not in lib_and_name:
        return None
    lib, name = lib_and_name.split(":", 1)
    lib_path = resolve_fp_path(lib, name)
    if not lib_path:
        return None
    return pcbnew.FootprintLoad(str(lib_path), name)


def ensure_net(board, net_name):
    nets = board.GetNetsByName()
    if net_name in nets:
        return nets[net_name]
    ni = pcbnew.NETINFO_ITEM(board, net_name)
    board.Add(ni)
    return ni


def auto_place(board, footprints, nets):
    """Heuristic placement: edge anchors, functional clustering, spread across board, avoid overlaps."""
    BOARD_W_MM = DEFAULT_BOARD_W_MM
    BOARD_H_MM = DEFAULT_BOARD_H_MM
    BOARD_MARGIN_MM = 5.0
    SLOT_STEP_MM = 10.0
    # Keep this close to the verification threshold to ensure the repel pass
    # actually resolves overlaps that would fail placement checks.
    OVERLAP_CLEAR_MM = 0.30

    def mm(x):
        return pcbnew.FromMM(x)

    def set_pos(fp, xm, ym):
        fp.SetPosition(pcbnew.VECTOR2I(mm(xm), mm(ym)))
        fp.SetOrientationDegrees(0)

    def bbox(fp):
        # Use pads/graphics only (exclude texts) to keep bboxes sane.
        r = fp.GetBoundingBox(False)
        return (r.GetLeft(), r.GetRight(), r.GetTop(), r.GetBottom())

    def bbox_center(fp):
        l, r, t, b = bbox(fp)
        return (l + r) / 2, (t + b) / 2

    ref_to_fp = {fp.GetReference(): fp for fp in footprints}

    # Fixed edge-biased placements for connectors/power/RF.
    specials = {
        "U1": (BOARD_W_MM * 0.55, 18),  # RF module near top edge
        # Keep antenna on the top-right edge.
        "J5": (BOARD_W_MM - 5.5, 8.5),
        # E-ink FPC pulled off edge
        "J2": (BOARD_W_MM - 13, BOARD_H_MM * 0.52),
        # Load cell header pulled to left edge near debug header for strain gauge wiring.
        "J1": (6, BOARD_H_MM * 0.55),
        # USB-C: centered on the bottom short edge for dev power/debug.
        "J3": (BOARD_W_MM * 0.50, BOARD_H_MM - 9),
        # USB-UART bridge placed close to the USB connector.
        "U5": (BOARD_W_MM * 0.50, BOARD_H_MM - 36),
        # USB OR-ing diode kept near the USB connector.
        "D3": (BOARD_W_MM * 0.65, BOARD_H_MM - 24),
        "C4": (BOARD_W_MM * 0.55, BOARD_H_MM - 24),
        # LDO regulator kept with other power passives away from edges.
        "U4": (BOARD_W_MM * 0.60, BOARD_H_MM - 30),
        # USB CC resistors inset from the edge, grouped with USB power path.
        "R5": (BOARD_W_MM * 0.58, BOARD_H_MM - 16),
        "R6": (BOARD_W_MM * 0.64, BOARD_H_MM - 16),
        # Decoupling caps kept close to their IC domains.
        "C1": (BOARD_W_MM * 0.18, BOARD_H_MM * 0.60),
        "C2": (BOARD_W_MM * 0.16, BOARD_H_MM * 0.44),
        "C3": (BOARD_W_MM * 0.50, BOARD_H_MM - 26),
        # Battery JST kept on the bottom edge but offset to avoid the USB connector.
        "BT1": (BOARD_W_MM * 0.30, BOARD_H_MM - 16),
        # Battery boost parts kept near the battery connector.
        "U3": (BOARD_W_MM * 0.45, BOARD_H_MM - 22),
        "L1": (BOARD_W_MM * 0.52, BOARD_H_MM - 22),
        "D2": (BOARD_W_MM * 0.40, BOARD_H_MM - 26),
        # HX711 (load cell ADC) kept mid-left but off the RF can.
        "U2": (BOARD_W_MM * 0.26, BOARD_H_MM * 0.40),
        # Sense divider grouped close to HX711/load-cell domain.
        "R1": (BOARD_W_MM * 0.22, BOARD_H_MM * 0.50),
        "R2": (BOARD_W_MM * 0.28, BOARD_H_MM * 0.54),
        # Buzzer pushed to the upper-right away from RF, USB, and debug connectors.
        "BZ1": (BOARD_W_MM * 0.85, BOARD_H_MM * 0.20),
        # Aux header on edge; user button inset with more clearance.
        "J4": (10, BOARD_H_MM * 0.68),
        "SW1": (BOARD_W_MM * 0.15, BOARD_H_MM - 8),
        # USB-side PMOS kept near the USB power path but off the edge.
        "Q1": (BOARD_W_MM * 0.58, BOARD_H_MM - 20),
        # NMOS for e-ink power gating kept mid-right with clearance.
        "Q2": (BOARD_W_MM * 0.70, BOARD_H_MM * 0.62),
        # USB-side gate bias resistor kept with the PMOS but off the MCU cluster.
        "R3": (BOARD_W_MM * 0.70, BOARD_H_MM - 14),
        # LED/buzzer resistor pulled toward the user interface corner.
        "R4": (BOARD_W_MM * 0.78, BOARD_H_MM * 0.32),
        # Status LED clustered with its resistor in the UI corner.
        "D1": (BOARD_W_MM * 0.74, BOARD_H_MM * 0.38),
    }
    fixed_targets = {}
    fixed_refs = set()
    for ref, pos in specials.items():
        fp = ref_to_fp.get(ref)
        if not fp:
            continue
        set_pos(fp, *pos)
        fixed_refs.add(ref)
        fixed_targets[ref] = pos

    # Define functional clusters (by reference designators).
    rf_refs = {"U1", "J5"}
    analog_refs = {"U2", "J1", "C1", "C2"}
    power_refs = {"U3", "U4", "J3", "BT1", "L1", "D2", "D3", "R5", "R6", "C3"}
    digital_core = {"J4", "J2", "Q2", "BZ1", "SW1", "D1", "R4"}

    # Compute connectivity weight to cluster remaining parts
    conn = {ref: 0 for ref in ref_to_fp}
    for net in nets:
        for ref, _ in net["nodes"]:
            if ref in conn:
                conn[ref] += len(net["nodes"])

    remaining = [fp for fp in footprints if fp.GetReference() not in specials]
    # Rough priority: analog near center-left, power lower-right, core center.
    def cluster_priority(fp):
        ref = fp.GetReference()
        if ref in rf_refs:
            return -1
        if ref in analog_refs:
            return 0
        if ref in power_refs:
            return 1
        if ref in digital_core:
            return 2
        return 3

    ordered = sorted(remaining, key=lambda f: (cluster_priority(f), -conn.get(f.GetReference(), 0)))

    def desired_center(ref: str):
        # Regions are expressed in mm, roughly:
        # - rf: top-right
        # - analog: left-middle (near load cell)
        # - power: bottom-right (near USB-C + battery JST)
        # - digital: mid / upper-mid
        if ref in rf_refs:
            return (BOARD_W_MM * 0.72, BOARD_H_MM * 0.20)
        if ref in analog_refs:
            return (BOARD_W_MM * 0.22, BOARD_H_MM * 0.55)
        if ref in power_refs:
            return (BOARD_W_MM * 0.72, BOARD_H_MM * 0.78)
        if ref in digital_core:
            return (BOARD_W_MM * 0.42, BOARD_H_MM * 0.55)
        return (BOARD_W_MM * 0.50, BOARD_H_MM * 0.55)

    # Build a grid of candidate slots across the board interior (no wrapping).
    xs = []
    x = BOARD_MARGIN_MM
    while x <= BOARD_W_MM - BOARD_MARGIN_MM:
        xs.append(x)
        x += SLOT_STEP_MM
    ys = []
    y = BOARD_MARGIN_MM
    while y <= BOARD_H_MM - BOARD_MARGIN_MM:
        ys.append(y)
        y += SLOT_STEP_MM
    slots = [(cx, cy) for cy in ys for cx in xs]
    # Keep slots away from fixed anchors to avoid immediate clashes.
    slot_keep = []
    keep_radius = mm(12)  # Increased from 7mm to 12mm to avoid connector collisions
    for cx, cy in slots:
        ok = True
        for ref in fixed_refs:
            tx, ty = fixed_targets.get(ref, (None, None))
            if tx is None:
                continue
            if abs(mm(cx) - mm(tx)) < keep_radius and abs(mm(cy) - mm(ty)) < keep_radius:
                ok = False
                break
        if ok:
            slot_keep.append((cx, cy))
    slots = slot_keep

    def clamp_fp(fp):
        l, r, t, b = bbox(fp)
        dx = dy = 0
        if l < 0:
            dx = -l + mm(2)
        if r > mm(BOARD_W_MM):
            dx = mm(BOARD_W_MM) - r - mm(2)
        if t < 0:
            dy = -t + mm(2)
        if b > mm(BOARD_H_MM):
            dy = mm(BOARD_H_MM) - b - mm(2)
        if dx or dy:
            pos = fp.GetPosition()
            fp.SetPosition(pcbnew.VECTOR2I(pos.x + dx, pos.y + dy))

    # Slot assignment: greedily pick nearest free slot to desired center.
    free_slots = list(slots)
    for fp in ordered:
        ref = fp.GetReference()
        dcx, dcy = desired_center(ref)
        best_i = None
        best_cost = None
        for i, (sx, sy) in enumerate(free_slots):
            cost = (sx - dcx) ** 2 + (sy - dcy) ** 2
            if best_cost is None or cost < best_cost:
                best_cost = cost
                best_i = i
        if best_i is None:
            # Fallback: center
            set_pos(fp, BOARD_W_MM * 0.5, BOARD_H_MM * 0.5)
        else:
            sx, sy = free_slots.pop(best_i)
            set_pos(fp, sx, sy)
        clamp_fp(fp)

    # Overlap repulsion + clamping (do not move fixed anchors).
    reps = 50  # Increased from 18 to 50 for better convergence
    for _ in range(reps):
        moved = False
        for i, fp_a in enumerate(footprints):
            ref_a = fp_a.GetReference()
            for fp_b in footprints[i + 1 :]:
                ref_b = fp_b.GetReference()
                la, ra, ta, ba = bbox(fp_a)
                lb, rb, tb, bb = bbox(fp_b)
                overlap_x = min(ra, rb) - max(la, lb)
                overlap_y = min(ba, bb) - max(ta, tb)
                if overlap_x > mm(OVERLAP_CLEAR_MM) and overlap_y > mm(OVERLAP_CLEAR_MM):
                    # Compute a small separating vector along the cheaper axis.
                    axc, ayc = bbox_center(fp_a)
                    bxc, byc = bbox_center(fp_b)
                    move_a = ref_a not in fixed_refs
                    move_b = ref_b not in fixed_refs
                    if not move_a and not move_b:
                        continue

                    if overlap_x < overlap_y:
                        step = mm(10)
                        sign = -1 if axc < bxc else 1
                        dx_a = sign * step if move_a else 0
                        dx_b = -sign * step if move_b else 0
                        dy_a = dy_b = 0
                    else:
                        step = mm(10)
                        sign = -1 if ayc < byc else 1
                        dy_a = sign * step if move_a else 0
                        dy_b = -sign * step if move_b else 0
                        dx_a = dx_b = 0

                    pa = fp_a.GetPosition()
                    pb = fp_b.GetPosition()
                    if dx_a or dy_a:
                        fp_a.SetPosition(pcbnew.VECTOR2I(pa.x + dx_a, pa.y + dy_a))
                    if dx_b or dy_b:
                        fp_b.SetPosition(pcbnew.VECTOR2I(pb.x + dx_b, pb.y + dy_b))
                    moved = True
        # Re-enforce anchors and clamp
        for ref in fixed_refs:
            fp = ref_to_fp.get(ref)
            if fp and ref in fixed_targets:
                set_pos(fp, *fixed_targets[ref])
        for fp in footprints:
            clamp_fp(fp)
        if not moved:
            break

    return BOARD_W_MM, BOARD_H_MM, fixed_targets


def build_board(sch_path: Path, out_path: Path):
    netlist_path = export_netlist(sch_path)
    comps, nets = parse_netlist(netlist_path)

    board = pcbnew.BOARD()
    board.GetDesignSettings().m_SolderMaskClearance = pcbnew.FromMM(0.05)

    footprints = []
    for comp in comps:
        fp = load_footprint(comp["fp"])
        if fp is None:
            print(f"[warn] footprint not found for {comp['ref']} ({comp['fp']})")
            continue
        # Preserve the schematic footprint link (Lib:Name) so schematic-parity checks pass.
        if comp.get("fp"):
            fp.SetFPIDAsString(comp["fp"])
        fp.SetReference(comp["ref"])
        fp.SetValue(comp["value"] or "")
        board.Add(fp)
        footprints.append(fp)

    # Nets
    for net in nets:
        netinfo = ensure_net(board, net["name"])
        for ref, pin in net["nodes"]:
            fp = next((f for f in footprints if f.GetReference() == ref), None)
            if not fp:
                continue
            matched = False
            for pad in fp.Pads():
                if pad.GetPadName() == pin:
                    pad.SetNet(netinfo)
                    matched = True
            if not matched:
                pad = fp.FindPadByNumber(pin)
                if pad:
                    pad.SetNet(netinfo)

    # Footprint-specific net tying fixes (mainly for power-only symbols on full footprints).
    net_gnd = board.FindNet("GND")
    net_vbus = board.FindNet("VBUS")
    for fp in footprints:
        if fp.GetReference() != "J3":
            continue
        if net_gnd:
            for pad in fp.Pads():
                if pad.GetPadName() in {"S1", "A1", "B1"} and not pad.GetNetname():
                    pad.SetNet(net_gnd)
        if net_vbus:
            for pad in fp.Pads():
                if pad.GetPadName() in {"A4", "B4"} and not pad.GetNetname():
                    pad.SetNet(net_vbus)

    # Add a simple rectangular board outline if none exists.
    if not any(sh.GetLayer() == pcbnew.Edge_Cuts for sh in board.GetDrawings()):
        W = pcbnew.FromMM(DEFAULT_BOARD_W_MM)
        H = pcbnew.FromMM(DEFAULT_BOARD_H_MM)
        corners = [
            pcbnew.VECTOR2I(0, 0),
            pcbnew.VECTOR2I(W, 0),
            pcbnew.VECTOR2I(W, H),
            pcbnew.VECTOR2I(0, H),
        ]
        for i in range(4):
            seg = pcbnew.PCB_SHAPE(board)
            seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
            seg.SetLayer(pcbnew.Edge_Cuts)
            seg.SetStart(corners[i])
            seg.SetEnd(corners[(i + 1) % 4])
            seg.SetWidth(pcbnew.FromMM(0.1))
            board.Add(seg)

    board_w_mm, board_h_mm, fixed_targets = auto_place(board, footprints, nets)
    if not verify_placement(board_w_mm, board_h_mm, footprints, fixed_targets):
        raise SystemExit(2)
    # Keep reference designators visible on silkscreen for assembly/debug.
    for fp in footprints:
        ref = fp.Reference()
        ref.SetLayer(pcbnew.F_SilkS)
    pcbnew.SaveBoard(str(out_path), board)
    print(f"Wrote board to {out_path}")

    # Always generate a preview image for manual inspection.
    svg_path = out_path.with_suffix(".svg")
    png_path = out_path.with_suffix(".png")
    export_board_svg(out_path, svg_path)
    try:
        convert_svg_to_png(svg_path, png_path)
        print(f"Wrote preview to {png_path}")
    except Exception as e:
        print(f"[warn] preview PNG generation failed: {e}")


def main():
    ap = argparse.ArgumentParser(description="Autoplace KiCad PCB from schematic")
    ap.add_argument(
        "--sch",
        type=Path,
        default=ROOT / "hardware" / "pcb" / "urine_monitor.kicad_sch",
        help="Input schematic (.kicad_sch)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "hardware" / "pcb" / "urine_monitor_autolayout.kicad_pcb",
        help="Output PCB file",
    )
    args = ap.parse_args()
    build_board(args.sch, args.out)


if __name__ == "__main__":
    main()
