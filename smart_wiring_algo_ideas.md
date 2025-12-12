````markdown
# Advanced Auto-Wiring Algorithms in EDA Routers  
_Generic principles for PCB / FPGA / ASIC routing_

This document summarizes the core algorithms and techniques behind **“smart” auto wiring** in EDA tools: how routers connect nets while:

- Never routing **through** placed chips or keep-out regions.
- Avoiding messy crossings and congestion hotspots.
- Respecting timing, signal-integrity, and manufacturability constraints.

The focus is on **generic algorithmic structure** that applies across PCB, FPGA and ASIC flows.

---

## 1. Problem Model

At its core, auto wiring (routing) solves a constrained path-finding problem on a geometric domain:

- **Inputs**
  - Set of **pins** grouped into **nets**.
  - **Obstacles**: components, macros, keep-out regions, power planes.
  - **Resources**: routing layers, tracks or free space, via rules.
  - **Constraints**: design rules (DRC), timing, SI/EMI, power, cost weights.

- **Outputs**
  - For each net, a set of **wires + vias** forming a valid connection.
  - No DRC violations, no routing through obstacles, and acceptable PPA (power, performance, area / board area).

Most production routers decompose this into:

1. **Global Routing**
   - Coarse grid / tiles.
   - Decide **which regions and layers** each net will use.
   - Optimize congestion, wirelength, via count.

2. **Detailed Routing**
   - Fine-grained geometry.
   - Generate exact wire/via shapes that obey DRC and follow global guides.

This 2-level decomposition is universal across modern VLSI and PCB routers. :contentReference[oaicite:0]{index=0}  

---

## 2. Geometry Models: Grid vs Shape

### 2.1 Grid-Based (Gridded) Models

- Layout is discretized into a **grid graph**.
- Nodes: potential routing points; edges: allowable segments.
- Obstacles (chips, keep-outs) become **blocked nodes/edges**.
- Routing becomes **graph search** + resource allocation.

Pros:
- Simple implementation.
- Easy to integrate with classical shortest-path / maze algorithms.

Cons:
- Resolution limited by grid pitch.
- Geometry approximated; may waste space or miss tight opportunities.

Grid-based is standard for **global routing** and many detailed routers (e.g., TritonRoute’s A*-based worker). :contentReference[oaicite:1]{index=1}  

### 2.2 Shape-Based (Gridless) Models

- Wires and obstacles stored as **polygons / rectangles** in a shape database.
- Routing space computed as **free rectangles** or polygons.
- Path search “floods” free space, dynamically updating shapes and checking parasitics. :contentReference[oaicite:2]{index=2}  

Pros:
- Better packing efficiency, important for **analog / RF / custom**.
- Parasitic-driven path selection in real time.

Cons:
- More complex geometry checks.
- Harder to parallelize.

Many custom/analog routers are now **shape-based detailed routers**, sitting on top of a grid-based global router.

---

## 3. Core Routing Algorithms

### 3.1 Maze Routing (Lee / A*)

Classical **maze routing** sees the layout grid as a maze:

- **Lee’s Algorithm** (BFS):
  - Wavefront expansion from source until target reached.
  - Always finds a shortest path (if one exists) in unweighted grids. :contentReference[oaicite:3]{index=3}  
- **A\***:
  - Adds heuristic (e.g., Manhattan or Chebyshev distance) to guide search.
  - Much faster than pure BFS, especially with good heuristics. :contentReference[oaicite:4]{index=4}  

Generic cost for each edge (segment):

```text
cost = w_len * length
     + w_via * via_penalty
     + w_cong * congestion_cost
     + w_timing * timing_cost
     + w_SI * crosstalk_risk
````

Pseudo-A* skeleton used inside many detailed routers:

```pseudo
function route_net_Astar(net, grid, cost_fn):
    open_set  = min_heap()
    push(open_set, (0, src_node))
    g[src_node] = 0
    parent = {}

    while open_set not empty:
        (f, u) = pop_min(open_set)
        if u == dst_node:
            return reconstruct_path(parent, u)

        for each neighbor v of u:
            if v is blocked (obstacle or DRC):
                continue
            tentative_g = g[u] + cost_fn(u, v)
            if tentative_g < g[v]:
                g[v] = tentative_g
                parent[v] = u
                h = heuristic(v, dst_node)   # e.g. Manhattan
                f = g[v] + h
                push_or_update(open_set, (f, v))

    return FAIL  # net unroutable within current resources
```

The **“smart” behavior** comes from a good `cost_fn` and a good `heuristic`, not from the search skeleton itself.

---

### 3.2 Steiner Trees & Obstacle-Avoidance

For multi-pin nets, routers often:

1. Build an **obstacle-aware Steiner tree** in a coarse model.
2. Route tree edges with maze routing.

Recent work proposes **rule-based obstacle-avoiding rectilinear Steiner minimal trees (OARSMT)** to avoid obstacles *early*, then uses sparse maze routing to avoid violations and overflow. ([arXiv][1])

Key points:

* Obstacles (chips, IP blocks, slots) are treated as **hard keep-out** nodes in the topology.
* The Steiner tree algorithm is modified to:

  * Prefer branches that skirt around obstacles with minimal wirelength increase.
  * Avoid creating branches that force later detours and via spikes.

This is exactly what prevents **“wires crossing chips”** at the global level.

---

### 3.3 Rip-Up and Reroute / Negotiation-Based Routing

Routing all nets at once leads to conflicts. Modern routers use **iterative negotiation**:

1. **Initial pass**:

   * Route nets one-by-one (often in a heuristic order) with simple costs.
   * Some resources become overused (overflow).

2. **Congestion analysis**:

   * For each edge/tile, compute usage vs capacity.
   * Congested edges get **penalty cost** increased.

3. **Rip-up & reroute loops**:

   * Select congested nets.
   * Rip up their routes.
   * Reroute them using updated congestion costs.

4. **Termination**:

   * Stop when no overflow or when improvement plateaus.

Dynamic congestion penalties and routing order are the heart of negotiation-based routers (e.g., DpRouter, ISPD contest winners). ([UCLA Electrical and Computer Engineering][2])

This **negotiation** is what gradually untangles messy crossings and spreads wires to less congested regions.

---

## 4. Constraint-Driven “Smartness”

The same search skeleton can support many “smart” behaviors by embedding more physics into the **cost model**.

### 4.1 Timing-Driven Routing

* Critical nets get:

  * Higher weight on **delay**, lower weight on wirelength.
  * Prefer shorter paths, fewer vias, thicker / top-layer routes.
* Non-critical nets:

  * Can detour to relieve congestion.

Timing-driven costs use estimates from **pre-routing timing prediction** or ML-based slack predictors. ([arXiv][3])

### 4.2 Signal Integrity & EMI-Aware Routing

* Cost terms penalize:

  * Parallel long runs between aggressor/victim nets.
  * Routing near noisy blocks (DC-DC, clock trees, high-speed links).
  * Excessive layer changes (via stubs).

RL and AI-enhanced routers have been proposed that explicitly consider crosstalk regions and vias to minimize SI issues. ([ResearchGate][4])

### 4.3 Power / Thermal / Reliability

Routers can:

* Prefer wider, shorter paths for high-current nets.
* Avoid thermal hotspots and E-field concentration regions.
* Reduce via stacks and stressed geometries.

These are baked into `cost_fn` and possibly into net ordering.

---

## 5. Net Ordering, Layer Assignment, and Batching

Even with a perfect inner router, **order matters**:

* Early nets have more freedom; late nets get squeezed.
* Poor net ordering creates chaotic crossing patterns.

Modern work uses:

* **Dynamic pattern routing / batching**:

  * Group nets that interact strongly (same region, layer competition).
  * Route these jointly or in carefully chosen sequences. ([UCLA Electrical and Computer Engineering][2])
* **ML-based ordering**:

  * Train models to predict an ordering of nets (and layer assignment) that minimizes congestion and via count. ([Nature][5])

This is one of the simplest yet high-impact levers to prevent “spaghetti routing.”

---

## 6. Detailed Routing and Shape-Based Cleanup

Once global routing and guides exist:

1. **Pin Access Generation**

   * For each pin, compute legal access points on layers.
   * Avoid overlapping obstacles and macros.

2. **Track-Based / Shape-Based Detailed Routing**

   * Within each global tile or “window,” the router:

     * Builds local grid or free-space rectangles.
     * Runs A* / maze with full DRC checks (spacing, enclosure, etc.).
   * Uses local rip-up/reroute to fix violations.

3. **Post-Route Optimization**

   * Shortening and straightening detours.
   * Replacing zig-zags with clean lines where resources free up.
   * Swapping layers or via locations to reduce coupling.

Shape-based routers integrate **real-time RC extraction** with path exploring, so they can reject paths that are DRC-clean but parasitic-terrible. ([EE Times][6])

---

## 7. Reinforcement Learning and Generative Models

Recent arXiv work goes beyond hand-tuned heuristics:

### 7.1 RL Global / Detailed Routing

* Treat routing as an **RL environment**:

  * **State**: partial layout, congestion map, current net segments.
  * **Action**: choose the next segment direction / layer / via.
  * **Reward**: negative wirelength, penalties for DRC, overflow, vias, timing violations.

Deep Q-Network (DQN) and policy-gradient approaches have shown improved results over classical A* in some settings. ([Carnegie Mellon University VDE ][7])

### 7.2 Generative / GAN-Assisted Global Routing

* Use GANs or generative models to **predict routability and congestion maps** or even propose routing patterns.
* Routers then refine these suggestions with classical algorithms. ([arXiv][8])

The typical pattern is **hybrid**:

* ML predicts *where* to route or *how* to order.
* Classical A* / maze + negotiation still does the hard DRC-exact work.

---

## 8. Ensuring “No Wires Crossing Chips” in Practice

Putting it all together, a robust “smart auto wiring” stack enforces:

1. **Obstacle Modeling**

   * Components, macro blocks, BGAs, mounting holes, forbidden regions → obstacles in both global and detailed models.
   * Any grid nodes or shapes overlapping these areas are permanently blocked.

2. **Guide-Respecting Routers**

   * Global routing creates **channels around obstacles**, never through them.
   * Detailed routers are constrained to these guides unless rip-up/reroute explicitly allows deviation.

3. **Congestion-Aware Negotiation**

   * If wires form messy crossings in one corridor, congestion cost spikes.
   * Rip-up/reroute redistributes nets to alternative corridors or layers.

4. **Net Ordering & Priority**

   * Critical nets routed first with wide, clean paths.
   * Bulk low-priority nets fill in remaining space, often allowed to bend more.

5. **Post-Route Cleanup**

   * Local shape optimizations remove unnecessary jogs and crossings.
   * DRC + parasitic checks ensure the final picture is both **clean** and **electrically sane**.

---

## 9. Practical Design Notes for Implementers

If you want to implement a **minimal but non-toy smart router** (for PCB/FPGA/ASIC):

1. Start with a **grid-based global router**:

   * Graph model with capacities, obstacles, and a basic A* + rip-up/reroute loop.
2. Add **multi-objective costs** in A*:

   * `length`, `via`, `congestion`; later add timing/SI terms.
3. Implement **net ordering + batching**:

   * Simple heuristics (critical first, long nets first) pay off quickly.
4. Add a **window-based detailed router**:

   * A* in local boxes, checking DRC (clearances, width, via rules).
5. Layer in **ML assistance** later:

   * Use ML to predict congestion, net ordering, or cost weights rather than to replace the entire router.

---

## 10. Selected References

* Global/detailed routing tutorials and models: ([NTU EECS][9])
* A*-based detailed routing (TritonRoute, open-source): ([VLSI CAD Laboratory][10])
* Obstacle-aware global routing with OARSMT trees: ([arXiv][1])
* Shape-based routing and parasitic-aware flows: ([EE Times][6])
* PCB routing algorithms and region-aware methods: ([Iowa State University Digital Repository][11])
* Deep RL global routing and follow-ups: ([Carnegie Mellon University VDE ][7])
* ML-based routing surveys and applications in EDA: ([ACM Digital Library][12])
* GAN-assisted and batching-oriented global routing: ([arXiv][13])

---

```
::contentReference[oaicite:22]{index=22}
```

[1]: https://arxiv.org/abs/2503.07268?utm_source=chatgpt.com "A High Efficient and Scalable Obstacle-Avoiding VLSI Global Routing Flow"
[2]: https://eda.ee.ucla.edu/pub/c95.pdf?utm_source=chatgpt.com "DpRouter: A Fast and Accurate Dynamic-Pattern-Based ..."
[3]: https://arxiv.org/abs/2501.07564?utm_source=chatgpt.com "E2ESlack: An End-to-End Graph-Based Framework for Pre-Routing Slack Prediction"
[4]: https://www.researchgate.net/publication/347449313_Reinforcement_Learning-based_Auto-router_considering_Signal_Integrity?utm_source=chatgpt.com "Reinforcement Learning-based Auto-router considering ..."
[5]: https://www.nature.com/articles/s41598-024-82226-9.pdf?utm_source=chatgpt.com "Machine learning optimal ordering in global routing ..."
[6]: https://www.eetimes.com/automatic-shape-based-routing-to-achieve-parasitic-constraint-closure-in-custom-design/?utm_source=chatgpt.com "Automatic shape-based routing to achieve parasitic ..."
[7]: https://vdel.me.cmu.edu/vdelresource/publications/2020jmdglobalrouting/paper.pdf?utm_source=chatgpt.com "a deep reinforcement learning approach for global routing"
[8]: https://arxiv.org/abs/2511.17665?utm_source=chatgpt.com "GAN-Assisted Scalable and Efficient Global Routing ..."
[9]: https://cc.ee.ntu.edu.tw/~ywchang/Courses/PD_Source/EDA_routing.pdf?utm_source=chatgpt.com "Global and detailed routing"
[10]: https://vlsicad.ucsd.edu/Publications/Journals/j133.pdf?utm_source=chatgpt.com "TritonRoute: The Open Source Detailed Router"
[11]: https://dr.lib.iastate.edu/bitstreams/baa06fe6-541d-4f4a-888d-94f3083cd518/download?utm_source=chatgpt.com "Towards automated PCB routing"
[12]: https://dl.acm.org/doi/10.1016/j.vlsi.2022.05.003?utm_source=chatgpt.com "A survey on machine learning-based routing for VLSI ..."
[13]: https://arxiv.org/html/2511.17665v1?utm_source=chatgpt.com "GAN-Assisted Scalable and Efficient Global Routing ..."
