# KiCad schematic generation (no ERC) + “smart” auto‑wiring (obstacle‑avoiding)

This note assumes KiCad **6+** (`.kicad_sch` s‑expression format).

---

## 1) Generate schematics with *no ERC violations* (especially “unconnected pins”)

### 1.1 Treat ERC as a build step (don’t eyeball it)
Run ERC automatically after you generate/edit a schematic:

```bash
kicad-cli sch erc --format json --exit-code-violations path/to/root.kicad_sch
```

- `--exit-code-violations` lets you gate CI on a clean report.
- `--format json` makes it scriptable.  
(See KiCad CLI docs: https://docs.kicad.org/8.0/en/cli/cli.html)

You can also export a netlist for connectivity audits:

```bash
kicad-cli sch export netlist --format kicadsexpr path/to/root.kicad_sch
```

---

### 1.2 The three classic ERC pain points, and how to eliminate them

#### A) Pins that are intentionally unused → **add a no‑connect flag**
KiCad’s “no‑connection flags” explicitly tell ERC a pin is *intentionally* left open (and avoid “unconnected pin” violations).  
Docs explain the behavior and the stacked-pin corner case (no-connect breaks stacking connectivity):  
https://docs.kicad.org/6.0/en/eeschema/eeschema.html  
https://sources.debian.org/src/kicad/9.0.5%2Bdfsg-1~bpo13%2B1/doc/src/eeschema/eeschema_schematic_creation_and_editing.adoc

**File-format token:** the schematic file format defines:

```lisp
(no_connect (at X Y) (uuid <uuid>))
```

Source: KiCad developer file format docs: https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/

**Script recipe**
1. Maintain an explicit “pin intent” list:
   - `CONNECTED` (must be in some net)
   - `NC` (must be intentionally unconnected)
2. For every `NC` pin, compute its absolute pin-end coordinate and emit a `no_connect` at that coordinate.
3. Re-run ERC; any remaining unconnected-pin issues are real mistakes.

> If a pin should *never* be connected in any schematic (true NC), set the **pin electrical type** to **Unconnected** in the *symbol library*. That also suppresses “unconnected pin” violations and prevents accidental wiring.

---

#### B) Power nets “not driven” → add **PWR_FLAG** (or a real power-output pin)
KiCad ERC often reports: **“Input Power pin not driven by any Output Power pins”** when power comes via connectors/batteries/etc. Add `PWR_FLAG` on those nets.

Docs:  
https://docs.kicad.org/6.0/en/eeschema/eeschema.html  
https://docs.kicad.org/8.0/en/getting_started_in_kicad/getting_started_in_kicad.pdf

**Script recipe**
- Identify nets with **power input** pins but **no power output** pins (via netlist export or ERC JSON).
- Place a `PWR_FLAG` symbol and wire it onto that net (or place the actual regulator output, etc.).

---

#### C) “It looks connected but ERC disagrees” → grid alignment & exact endpoints
KiCad connectivity is geometric: **wire endpoints must coincide** exactly with pin endpoints; wire crossings are not automatically connected.

Docs (grid + endpoint rule): https://docs.kicad.org/6.0/zh/eeschema/eeschema.html  
(“use a 50 mil grid”, and wires connect only when ends coincide)

**Script rule of thumb**
- Choose a grid (typically **50 mil = 1.27 mm**).
- Snap *every* generated coordinate to that grid.
- Ensure wires terminate **exactly** at pin ends (not “overlapping the symbol body”).

---

### 1.3 Minimal file-format snippets you’ll actually generate
Official s-expression format references:
- Schematic format: https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/
- Common syntax (`pts`, `stroke`, units in **mm**): https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html

**Wire**
```lisp
(wire
  (pts (xy X1 Y1) (xy X2 Y2) (xy X3 Y3))
  (stroke (width 0) (type default) (color 0 0 0 0))
  (uuid <uuid>)
)
```

**Junction** (use when you *intend* a connection at a 3+ segment intersection)
```lisp
(junction (at X Y) (diameter 0) (color 0 0 0 0) (uuid <uuid>))
```

**No-connect**
```lisp
(no_connect (at X Y) (uuid <uuid>))
```

---

## 2) Auto-wire pins “elegantly” (smart routing that avoids symbol bodies)

### 2.1 The big trick: separate *connectivity* from *ink*
In schematics, long wires are mostly UX debt. Net **labels** give correct connectivity without drawing a spaghetti bowl.

Docs: labels connect nets by name; you can connect without direct wire runs:  
https://docs.kicad.org/8.0/fr/eeschema/eeschema.html  (Labels section)

**Practical policy**
- **Local short connections** (inside a functional block): draw wires.
- **Global / long / high-fanout nets** (power, clocks, reset, buses, MCU GPIO groups): use *label stubs*.

That reduces the routing problem from “global autorouter” to “lots of tiny, clean stubs”.

---

### 2.2 Two-stage algorithm (what actually works in code)

#### Stage A — Placement (optional, but it’s where “smart” mostly lives)
No router can fully rescue bad placement. If you can, do a quick automatic placement pass:

- Build a graph: symbols = nodes, nets = hyperedges.
- Weight edges by:
  - number of pins on the net (fanout),
  - criticality (clock/reset), and/or
  - expected bus grouping (DATA[0..7]).
- Optimize a cost like:
  - total Manhattan distance of connected pins,
  - estimated crossings,
  - keep connectors on sheet edges, keep power at top/bottom, etc.

A force-directed layout or simulated annealing with grid snapping is usually “good enough”.

#### Stage B — Routing (orthogonal, obstacle-avoiding)
Model routing as grid-based Manhattan paths with obstacles.

**Geometry model**
- Coordinates: KiCad schematic s-expression uses **millimeters**.
- Use grid step: **1.27 mm** (50 mil) unless you have a reason not to.
- Obstacles:
  - symbol body bounding boxes (inflate by 1–2 grid steps as keepout),
  - optionally reference/value text boxes,
  - optionally existing wires as *soft* obstacles.

**Routing core**
- Use **A\*** on a 4-neighbor grid.
- Cost function (simple and effective):
  - `+1` per grid step (length)
  - `+BEND_PENALTY` when direction changes (minimize elbows)
  - `+CROSS_PENALTY` if you would cross an existing wire (prefer to detour)
  - `+NEAR_OBSTACLE_PENALTY` if too close to a symbol body (readability)
- Heuristic: Manhattan distance.

**Make it look human**
- After A\* returns a path (list of points), *compress* it:
  - remove collinear interior points so you emit 2–6 points, not 200.
- Use consistent posture:
  - default “horizontal then vertical” (or the reverse), and penalize “weird zigzags”.

---

### 2.3 Multi-pin nets: don’t route N² edges—build a trunk
For a net with many pins (e.g., `SPI_SCK` to 4 devices), you want a shared structure:

1. Compute a **hub** (Manhattan median):
   - `hub_x = median(pin_x)`, `hub_y = median(pin_y)`
2. Route each pin → hub (or pin → nearest point on a trunk line).
3. Merge overlapping segments.
4. Add junctions where branches meet.

This is a fast approximation to a rectilinear Steiner tree and works well visually.

**Even smarter heuristic**
- If pin points are mostly aligned horizontally, pick a **horizontal trunk** at `median(y)` and branch vertically.
- If mostly vertical, pick a vertical trunk.

---

### 2.4 Ultra-practical “elegant wiring” mode: stub + label
This is the cheat code for schematic legibility.

For each net:
- Place a label near each pin cluster.
- Draw a short orthogonal stub from pin end → label anchor.
- Don’t draw long inter-block wires at all.

You still get perfect connectivity and ERC cleanliness (as long as stub endpoints coincide with pin ends and label anchors are on the wire).

---

## 3) Skeleton Python approach (pseudo-code you can drop into a generator)

### 3.1 S-expression emitters (wire / junction / no_connect)
```python
from uuid import uuid4

def U(): return str(uuid4())

def sexpr_wire(points_mm):
    pts = " ".join(f"(xy {x:.3f} {y:.3f})" for x,y in points_mm)
    return f'(wire (pts {pts}) (stroke (width 0) (type default) (color 0 0 0 0)) (uuid {U()}))'

def sexpr_junction(x, y):
    return f'(junction (at {x:.3f} {y:.3f}) (diameter 0) (color 0 0 0 0) (uuid {U()}))'

def sexpr_no_connect(x, y):
    return f'(no_connect (at {x:.3f} {y:.3f}) (uuid {U()}))'
```

### 3.2 A* router (grid Manhattan, obstacle-avoiding) — minimal outline
```python
import heapq
from math import inf

DIRS = [(1,0),(-1,0),(0,1),(0,-1)]

def astar(start, goal, is_blocked, step=1):
    # start/goal are integer grid coords (gx, gy), not mm
    def h(a,b): return abs(a[0]-b[0]) + abs(a[1]-b[1])

    pq = [(h(start,goal), 0, start, None, None)]  # (f,g,node,parent,dir)
    best = {start: 0}
    parent = {}
    pdir = {}

    while pq:
        f,g,u,par,udir = heapq.heappop(pq)
        if u in parent:  # already expanded with best
            continue
        parent[u] = par
        pdir[u] = udir
        if u == goal:
            break

        for dx,dy in DIRS:
            v = (u[0]+dx, u[1]+dy)
            if is_blocked(v):
                continue
            bend = 0 if udir is None or udir==(dx,dy) else 5
            ng = g + 1 + bend
            if ng < best.get(v, inf):
                best[v] = ng
                heapq.heappush(pq, (ng + h(v,goal), ng, v, u, (dx,dy)))

    if goal not in parent:
        return None

    # reconstruct
    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    return path
```

You’d wrap `is_blocked()` around:
- symbol keepouts,
- (optional) already-routed wires as soft blocks / high-cost regions,
- sheet boundaries.

Then convert grid coords → mm (`mm = grid * 1.27`) and compress collinear points.

---

## 4) A boring-but-realistic pipeline that works

1. Generate/update `.kicad_sch` (symbols + labels/wires).
2. Snap everything to grid; ensure wire endpoints coincide with pins.
3. Place `no_connect` on all intentionally unused pins.
4. Add `PWR_FLAG` where needed.
5. Run `kicad-cli sch erc --format json --exit-code-violations`.
6. Export SVG for visual diffing in CI (`kicad-cli sch export svg ...`).

When this passes reliably, you’ve basically built a schematic compiler.

---

## 5) Key references (official)
- Schematic file format (KiCad 6+): https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/
- Common s-expression syntax (pts, stroke, **units in mm**): https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html
- KiCad CLI (`kicad-cli sch erc`, netlist export): https://docs.kicad.org/8.0/en/cli/cli.html
- Eeschema docs (no-connect flag, PWR_FLAG, grid rules): https://docs.kicad.org/6.0/en/eeschema/eeschema.html
