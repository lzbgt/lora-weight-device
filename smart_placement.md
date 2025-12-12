Here’s a practical recipe for auto‑placing schematic blocks so pages look “hand‑crafted” but come from an algorithmic flow.

---

# Multi‑objective schematic auto‑placement (readability → grouping → space)

**Goal order (hard → soft):**

1. Label readability (no overlaps, sane angles)
2. Preserve functional grouping (keep net clusters tight)
3. Minimize whitespace before deciding to split pages

## Core model

* Treat each symbol `i` with a **rect bbox** `(xi, yi, wi, hi)` and **label bboxes** (refdes, pin names).
* Nets define a **graph**: nodes = symbols, edges = electrical connections (optionally hyperedges per net).
* Page is a rectangular canvas with soft margins.

### Cost terms (weighted sum; enforce priority via large weight ratios W1 ≫ W2 ≫ W3)

* **Readability** `C_read`

  * Label overlap: sum IoU between all label bboxes (penalty)
  * Label–symbol overlap (penalty)
  * Label angle penalty: prefer 0°, 90° (hinged L1 penalty from nearest canonical angle)
  * Minimum label font size violations (big penalty)
* **Grouping** `C_group`

  * Net tension: Σ over edges `||pos(i) − pos(j)||` with edge weights (e.g., bus > power > signal)
  * Cluster compactness: for detected communities (Louvain/Leiden on net graph), Σ pairwise distances to cluster centroid
* **Space/page usage** `C_space`

  * Dead‑space entropy: encourage even packing by penalizing large empty rectangles
  * Aspect ratio deviation from target (e.g., A4 landscape)
  * Page overflow penalty (very large if any bbox leaves page)

**Total cost:**
`C = W1*C_read + W2*C_group + W3*C_space`, with `W1:W2:W3 ≈ 100:10:1`.

## Optimizer: simulated annealing (SA)

* **State:** positions (and optional orientations) of symbols; label anchor/angle choices.
* **Moves:**

  * Nudge symbol (small random Δx, Δy)
  * Swap two symbols’ regions within a cluster
  * Rotate/flip symbol if allowed (orthogonal orientations)
  * Re‑anchor a label (top/bottom/left/right) and snap angle to {0°, 90°} with jitter
* **Schedule:** geometric `T ← αT` (α≈0.95 per k iterations), reheats if stuck.
* **Acceptance:** Metropolis on ΔC (always accept if readability improves; use **lexicographic** accept to respect priorities).

## Page splitting (only after good packing)

1. Run SA to convergence on a **single large canvas**.
2. Build a **connection‑cut graph**: edge weight between clusters = number/importance of inter‑cluster nets.
3. Solve a **balanced min‑cut** (or recursive bisection) to partition clusters into pages while:

   * respecting maximum page density (total bbox area / page area)
   * minimizing cut edges (prefer connector/bus stubs at page boundaries)
4. For each page, re‑run a **local SA** with fixed node set to polish.

## Practical heuristics that help a lot

* **Grid‑snap** symbols to 8–16 px; free‑place labels within a small continuous window—this kills micro‑overlaps.
* **Orthogonal label angles only** (0/90) unless absolutely needed; dramatically improves legibility.
* **Pin‑side bias**: penalize routes crossing through bboxes by preferring placements that keep likely wires on free sides.
* **Power/ground rails**: treat as “gravity fields” (attract VCC up, GND down) to get familiar visual structure.
* **Buses first**: place bus‑heavy clusters along a spine; satellites arrange around it.

## Tiny reference implementation (pseudo‑Python)

```python
def cost(state):
    C_read = label_overlaps(state) + label_angle_penalty(state) + label_on_symbol_overlap(state)
    C_group = net_tension(state) + cluster_compactness(state)
    C_space = whitespace_penalty(state) + aspect_ratio_penalty(state) + overflow_penalty(state)
    return 100*C_read + 10*C_group + 1*C_space

def anneal(state, T0=1.0, T_min=1e-3, alpha=0.95):
    T, best = T0, state.copy()
    Cb = cost(best)
    while T > T_min:
        for _ in range(200):  # inner loop
            s2 = propose_move(state)  # nudge/swap/re-anchor/rotate
            dC = cost(s2) - cost(state)
            # lexicographic accept: prioritize readability
            if improves_readability(s2, state) or dC < 0 or rand() < exp(-dC/T):
                state = s2
                if cost(state) < Cb:
                    best, Cb = state.copy(), cost(state)
        T *= alpha
    return best
```

## Testing & acceptance (fast)

* **Unit checks:** no label overlaps; all symbols in page; min text size met.
* **Graph metrics:** average edge length within cluster ≤ threshold; cut‑edge count per page minimized.
* **Golden examples:** run on 3–5 hand‑drawn schematics and compare:

  * wire crossings vs. baseline
  * page count and fill factor (aim 65–85%)
  * review time by a human (qualitative)

## Integration hooks (KiCad/EDA)

* Export/import **bboxes + pins** from the schematic format (JSON/IPC).
* Keep a deterministic **seed** and write back **placements + label anchors**; leave wiring to your router, but your cost’s “pin‑side bias” will make routing cleaner.
* Store **cluster IDs** in fields so page‑splitter is repeatable.

If you want, I can turn this into a runnable Python script that ingests a simple JSON of symbols/nets and outputs placed coordinates + page assignments.
