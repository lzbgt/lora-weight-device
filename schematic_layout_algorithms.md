# Schematic Auto-Layout Algorithms (KiCad `.kicad_sch` generator)

This document proposes **practical, implementable algorithms** to improve:
1) **Human readability (highest priority)**  
2) **Functional grouping / block coherence**  
3) **Space efficiency (only after 1 & 2 are satisfied)**  
4) **Automatic multi-page splitting (last resort)**

It is written to map cleanly onto your current Python-based KiCad schematic generator.

---

## 0) What the current generator does (and why it gets messy)

From `gen_urine_schematic.py`:

- **Placement**: instances are **hard-coded** in `INSTANCES = { ... (x,y) ... }` → no auto-placement.
- **Connectivity**: `emit_net()` draws **only a short stub from each pin and a net label** at the stub end.  
  There is **no actual multi-pin wiring / bus / junction topology**—the “connection” is purely by identical net labels.
- **Labeling**: label position is `at (stub_x, stub_y)` with a simple `justify` direction based on pin rotation.
  - There is **no collision detection** (label–label / label–symbol / label–wire).
  - High-fanout nets (GND/VCC/etc.) get **a label at every pin**, creating label density around dense ICs.

That combination is fast to generate, but it tends to produce **label clouds** near chips with many pins (MCU/module, large connectors), and it does not visually communicate circuit structure (only names).

---

## 1) Model the problem explicitly

Represent the schematic as **objects** with geometry and constraints:

### 1.1 Objects
- **Symbol instance** `S`: position `(x,y)`, orientation `rot`, bounding box `bbox(S)`
- **Pin** `p`: absolute anchor point `(x_p,y_p)`, preferred stub direction `dir(p)`
- **Net** `n`: a hyperedge connecting pins `P(n) = {p1, p2, ...}`
- **Wire segment** `w`: orthogonal polyline with clearance
- **Label** `L`: rectangle `bbox(L)` with anchor `(x_a,y_a)` and chosen candidate `(x,y,justify)`

### 1.2 Constraints (hard)
- No symbol overlap (bbox separation ≥ margin).
- Wires do not pass through symbols (treat symbol bbox inflated by clearance as obstacle).
- Label boxes do not overlap symbols; label–label overlaps should be minimized, ideally eliminated.
- Grid snapping.

### 1.3 Objectives (soft, prioritized)
1. **Readability**
   - minimize label overlaps, wire crossings, wire bends, “untraceable” hops
   - align and simplify (straight lines, consistent directions)
2. **Functional grouping**
   - strongly-related components should be near each other and visually “boxed”
3. **Space**
   - reduce page area only after readability/grouping are good enough
4. **Split to pages**
   - only if constraints cannot be met on one page

A key implementation detail: use a **lexicographic / tiered optimizer**:
- First minimize *readability cost*;
- subject to that, minimize *grouping cost*;
- subject to both, minimize *area*.

This prevents the “packed but unreadable” failure mode.

---

## 2) Recommended pipeline (works for small and large schematics)

1. **Preprocess nets**
   - Identify *global nets* (power/ground/high-fanout) and remove them from clustering.
2. **Functional grouping (clustering / partitioning)**
   - Assign components into blocks: Power, MCU, Sensors, Display, UI, Connectors, etc.
3. **Block-level placement (macro layout)**
   - Place block rectangles on page with a clear flow (left→right, top→bottom).
4. **Within-block placement (micro layout)**
   - Place the anchor IC/connector; attach passives around relevant pins; enforce conventions.
5. **Routing strategy**
   - Draw explicit wires for *local nets*; use labels/buses/harnesses for long or inter-block nets.
6. **Label placement (collision-aware)**
   - Choose label positions from candidates via greedy + local repair (or ILP if you want).
7. **Compaction (gentle whitespace reduction)**
   - Tighten only where it does not harm readability.
8. **If it still doesn’t fit → multi-page split**
   - Partition blocks into pages minimizing inter-page nets.

---

## 3) Step 1: Net preprocessing / classification

### 3.1 Detect nets that should NOT drive grouping
These nets connect almost everything and destroy clustering:
- `GND`, `VCC`, `VBUS`, `BAT`, `3V3`, `5V`, etc.
- Any net with degree ≥ `fanout_global` (e.g., ≥ 8 pins)

**Algorithm:**
```
global_nets = { n | degree(n) >= fanout_global } ∪ { n | name matches power_regex }
```

### 3.2 Net types drive drawing style
Classify nets into:
- **Global**: power rails, ground, high-fanout  
  → use *power symbols* or *one label per block*, not per-pin labels.
- **Local**: connects pins within same block and small degree (≤ 3)  
  → draw explicit wires (pattern routing).
- **Inter-block**: connects pins across blocks  
  → use ports + labels, or bus/harness if many nets cross between same two blocks.

---

## 4) Step 2: Functional grouping (block extraction)

### 4.1 Build a weighted component graph from the hypergraph
Construct a graph `G=(V,E)` where each component is a node. For each net `n` (excluding global nets):
- For all pairs of components `(u,v)` connected by `n`, add edge weight:
  - **Option A (simple):** `w += 1`
  - **Option B (better):** `w += 1/(degree(n)-1)`  
    (downweights medium-fanout nets so they don’t glue everything together)

Also add heuristics:
- Boost weights for “tight” relationships:
  - decoupling caps to IC VDD pins
  - crystal + load caps to MCU
  - regulator + inductor + diode + feedback resistors

You can infer these by net names (`VDD`, `VCC`, `FB`, `SW`, `XI/XO`) and component types.

### 4.2 Two practical clustering strategies

#### Strategy A: Anchor-based assignment (very practical)
1. Identify **anchors**: ICs/modules/connectors/regulators (high pin count or known library class).
2. Assign passives to nearest anchor by graph distance:
   - compute shortest-path distance in `G` from passive to each anchor
   - assign to the closest; tie-break by sum of incident edge weights

This produces blocks that match human intuition.

#### Strategy B: Community detection / partitioning (more general)
Run Louvain/Leiden (modularity) or spectral clustering on `G`.  
Then optionally label clusters by anchor types (power cluster, MCU cluster, etc.).

**Good hybrid**: Strategy A for passives + Strategy B to merge/split anchor clusters.

### 4.3 Block constraints you should enforce
- Minimum/maximum block size (component count) to avoid tiny or huge blocks.
- “Keep together” rules:
  - parts sharing a local analog reference should not be split
- “Separate” rules:
  - noisy power switching block should be spatially separated from sensitive analog block

---

## 5) Step 3: Block-level placement (macro layout)

### 5.1 Build the block graph
Nodes = blocks; edge weight = number of inter-block nets (excluding globals), or sum of net weights.

### 5.2 Place blocks with readable flow
A robust heuristic layout (works well for schematics):

1. Pick a **central block** (often MCU/module) as root.
2. Categorize blocks:
   - Power (sources/rails)
   - IO/connectors (edges)
   - Sensors/analog (near MCU but separated from switching power)
   - Display/UI (near MCU, usually right side)
3. Use a **constrained force model** on block rectangles:
   - attraction ∝ inter-block edge weight
   - repulsion to avoid overlap
   - soft constraints:
     - Power blocks prefer bottom-left / left
     - Connectors prefer page edges
     - UI/display prefer right/top-right
4. Snap block origins to grid.

This gives a good first macro layout.

### 5.3 Convert to a clean orthogonal macro arrangement (optional but recommended)
After force placement, apply **orthogonalization / rectilinear cleanup**:
- enforce a small set of canonical x-columns and y-rows for blocks
- align blocks to form clean “lanes” for buses

This increases readability more than it costs area.

---

## 6) Step 4: Within-block placement (micro layout)

### 6.1 Anchor-first placement
For each block:
1. Place the **anchor** (main IC/connector) at the block center.
2. Choose anchor **orientation** to minimize wire/label conflicts:
   - place high-traffic nets on left/right sides according to flow
   - keep power pins on top (if symbol supports that convention), ground bottom

Orientation selection can be done by minimizing:
```
rot_cost = Σ_n traffic(n) * projected_distance(pin_side(rot,n), preferred_side(n))
```

### 6.2 Attach passives near the pins they serve
For each passive `c` in block:
- Determine its **attachment pin(s)**:
  - For 2-pin passive: attach to the *more specific* net end (not GND/VCC)
  - For decoupling cap: attach to the IC VDD pin
- Compute target point = anchor pin position + outward offset.
- Place passives on a “ring” around anchor, grouped by side (left/right/top/bottom).
- Sort by the anchor pin y-order (for left/right sides) to reduce crossings.

This mimics how humans draw: passives line up alongside the pins they connect to.

### 6.3 Collision resolution (simple but effective)
After initial placement:
- Run a discrete “push-out” pass:
  - detect overlaps between symbol bboxes
  - for each overlap pair, move the lighter/smaller part outward along the nearest free direction
  - re-snap to grid
Repeat for a few iterations.

---

## 7) Step 5: Wiring strategy (make the topology legible)

### 7.1 Don’t label everything
Your current “stub+label for every pin” is the biggest readability killer.

Instead:
- **Global nets**: power symbols or one label per local rail, not per pin.
- **Local nets** (within a block): draw real wires (short, orthogonal).
- **Inter-block nets**: labels/ports; group many nets as buses.

### 7.2 Local-net orthogonal routing (pattern first, maze fallback)
For a connection between two pins A and B:

1. Try **I-route** (straight) if aligned and unobstructed.
2. Else try **L-route** (one bend) with two candidate elbows:
   - `(xA, yB)` and `(xB, yA)` if unobstructed.
3. Else try **Z-route** (two bends) using a small set of channel y-levels or x-levels.
4. Else run a lightweight **grid A*** router:
   - nodes on GRID
   - obstacles = inflated symbol bboxes + existing wires
   - cost = length + bend_penalty + near_wire_penalty

This keeps most wiring clean without heavy computation.

### 7.3 High-degree nets inside a block: use a local bus spine
If a net connects to many pins in the same block (but you don’t want global):
- create a **spine** (a horizontal or vertical trunk line)
- connect each pin to the spine with short orthogonal branches
- put **one net label** on the spine

This reduces label duplication dramatically and improves traceability.

---

## 8) Step 6: Label placement (collision-aware, practical)

Label placement is a classic “annotate anchors without collisions” problem.

### 8.1 Generate candidate label positions per anchor
For each label with anchor point `(x_a, y_a)` and a preferred direction `dir`:
- create candidates at increasing distance along `dir`: `d ∈ {0, 1, 2} * GRID`
- for each, create perpendicular nudges `p ∈ {-1, 0, +1} * GRID`
- include a “flip side” candidate if all else fails

For horizontal stubs, candidates are typically:
- right/left with above/below nudges

For vertical stubs:
- top/bottom with left/right nudges

### 8.2 Approximate text box size (good enough for collision tests)
If KiCad font size is `h` (e.g., 1.27mm), approximate:
- `char_w ≈ 0.6*h`
- `w = char_w * len(text)`
- `bbox = (x, y, x+w, y+h)` adjusted by justification

This is sufficient to avoid obvious overlaps.

### 8.3 Cost function (readability-first)
For each candidate `c` for label `i`:
```
cost(c) =
  W_overlap * (overlap_area_with_symbols + overlap_area_with_labels)
+ W_wire    * crossings_or_close_proximity_to_wires
+ W_dist    * distance(anchor, label)
+ W_edge    * outside_page_penalty
+ W_style   * (breaks_consistency_penalty)
```

Make `W_overlap` dominant.

### 8.4 Solver options

#### Option A (fast): Greedy + repair
1. Sort labels by congestion:
   - longer names first, then anchors in dense regions
2. Place each label at lowest cost candidate given already placed.
3. Repair pass: for remaining overlaps, push labels outward along least-colliding direction.

This handles 95% of cases.

#### Option B (strong): ILP for per-block label placement
Binary variable `x_{i,c}` = 1 if label i chooses candidate c.

Constraints:
- each label chooses exactly one candidate
- no overlap constraints for pairs that overlap (precompute conflict graph)

Objective:
- minimize Σ x_{i,c} * cost_{i,c}

This gives near-optimal label placement per block (typically small enough to solve quickly).

---

## 9) Step 7: Gentle compaction (space efficiency without hurting readability)

Once blocks, symbols, wires, labels are placed and collision-free:
- perform **compaction** to remove large unused gaps while preserving constraints.

### 9.1 Constraint-graph compaction (robust)
Build constraints:
- If object A must be left of B (because they overlap in y-range), add:
  `x_B ≥ x_A + width(A) + margin`
- Similar for vertical.

Solve by longest-path in a DAG (if you maintain a consistent ordering), or by iterative relaxation.

### 9.2 Heuristic “sweep” compaction (easy)
Repeat a few times:
- left-sweep: move each object left until it would violate any constraint
- top-sweep: move up similarly
- snap to grid

Stop when improvement is small.

Important: do compaction **after** label routing, otherwise you’ll reintroduce collisions.

---

## 10) Step 8: Multi-page splitting (last resort)

Only do this if:
- after grouping + placement + compaction, the layout cannot fit page bounds **without violating readability constraints**, or
- label density exceeds a threshold in one region even after rerouting.

### 10.1 Partition blocks into pages (min-cut with capacity)
Treat blocks as items with “area” (estimated block bbox) and “complexity” (component count, label count).  
Partition the block graph to minimize cut edges (inter-page nets), subject to:
- page area capacity
- max complexity per page

Practical algorithm:
- Start with one page; place largest/central block (MCU) first.
- Iteratively add neighboring blocks that:
  - fit capacity
  - add minimal new cut weight
- When no block fits, start a new page.
- Optionally run a KL/FM refinement pass to swap blocks between pages and reduce cuts.

### 10.2 Represent inter-page connectivity cleanly
- For a few nets: use **sheet ports** (hierarchical labels) or off-page connectors.
- For many nets between same two pages: create a **bus/harness**:
  - bus label like `EINK[CS,RST,DC,BUSY,SCK,MOSI]`
  - keep per-signal labels near endpoints, but route as a single bus trunk

### 10.3 Add a top-level overview page (recommended)
Generate a page 0:
- one block symbol per sheet
- buses between sheets
- power distribution

This massively improves human readability for multi-page designs.

---

## 11) How this maps back to your Python generator

### 11.1 Replace hard-coded `INSTANCES` positions
- Compute blocks and placements; assign `(x,y)` per instance from the algorithm.
- Keep your symbol parsing; add:
  - symbol bbox estimation
  - orientation (`rot`) selection support

### 11.2 Stop emitting one label per pin for global/high-degree nets
- Emit KiCad **power symbols** where possible.
- Or emit exactly one label per block spine and connect to it.

### 11.3 Add a label-placement module
- Maintain label objects; generate candidates; compute bbox overlaps; choose candidates.

### 11.4 Optional: generate actual wires for local nets
- Implement pattern routing; fallback to A* in a grid with obstacles.

---

## 12) Metrics & regression tests (so improvements are measurable)

Track:
- number of label–label overlaps (should be 0)
- number of label–symbol overlaps (must be 0)
- wire crossings (minimize)
- average pin-to-label distance (small)
- pages used (minimize *after* readability)
- block cut weight (minimize)

Create a golden-image regression:
- render PDF from KiCad and compare to baseline with perceptual diff (optional).

---

## 13) Practical defaults (good starting values)

- `GRID = 1.27mm`
- `fanout_global = 8`
- label candidate distances: `{0, 1, 2} * GRID`
- minimum symbol spacing: `2 * GRID`
- dominant label overlap weight: `W_overlap = 1000`
- wire bend penalty: `bend_penalty = 2*GRID` (in A* cost units)

---

### TL;DR
The biggest wins come from:
1) **Cluster into blocks** (ignore global nets for clustering)  
2) **Draw real wires inside blocks** and **use fewer labels** (spines/buses/global rails)  
3) **Collision-aware label placement** (candidates + greedy/ILP)  
4) **Only then** compact and split pages if truly necessary
