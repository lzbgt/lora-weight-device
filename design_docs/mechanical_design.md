# Mechanical & Enclosure Design

## 1. Design Requirements
*   **Environment:** Clinical Hospital Ward (Clean, but potential splashes).
*   **Rating:** **IP65** (Dust tight + Water jets). Essential for cleaning/disinfection.
*   **Mounting:** Must attach securely to standard Hospital Bed Rails (0.8" - 1.5" diameter) or hang from the bed frame.
*   **Load Interface:** Must securely hold a 2000mL (approx 2kg) urine bag.

## 2. Enclosure Concept (The "Shell")
*   **Material:** **ASA (Acrylonitrile Styrene Acrylate)** or **PC-ABS**.
    *   *Why:* UV stable (won't yellow under hospital lights), chemical resistant (alcohol/bleach wipes), high impact strength.
*   **Form Factor:** "Handheld" style vertical box with a hook at the bottom.
    *   *Dimensions (Approx):* 120mm (H) x 70mm (W) x 35mm (D).
*   **Assembly:** 2-part Snap-fit or Screw-together (4x M3 Stainless Steel screws from the back).
*   **Sealing:** Silicone O-ring groove around the perimeter of the mating surfaces.

## 3. Mounting Mechanism (Top)
The device needs to hang *from* the bed rail.
*   **Option A: Integrated Hook:**
    *   A large, robust hook molded into the back of the case.
    *   *Pros:* Cheap, no moving parts.
    *   *Cons:* Might not fit all rail shapes; can slide.
*   **Option B: Adjustable Clamp (Recommended):**
    *   A "C-clamp" style mechanism attached to the back.
    *   Rotatable knob to tighten onto the rail (0.8" - 1.5" range).
    *   Rubber pads inside the clamp to prevent slipping and scratching the bed rail.

## 4. Load Cell Integration (Ultra-Compact Button)
To achieve a minimal device footprint, we utilize a **Compression Load Button** (Coin-style sensor) instead of a large beam.

1.  **Sensor Selection:** **TE FX1901** or Generic **10-20mm Load Button** (Range: 10-20lb / 5-10kg).
    *   *Size:* ~15mm Diameter.
    *   *Type:* Compression Force Sensor.
2.  **Mechanical Interface ("Pull-to-Push"):**
    *   **Shelf:** The sensor sits on a structural PCB or plastic shelf inside the case, facing **UP**.
    *   **Hook Shaft:** Passes *through* a hole next to (or under) the sensor assembly.
    *   **Bridge/Yoke:** The top of the hook connects to a rigid "Bridge" piece that spans over the sensor.
    *   **Action:** When the bag pulls the hook **DOWN**, the Bridge presses **DOWN** onto the sensor's "button" surface.
3.  **Sealing:**
    *   Standard O-ring or Rubber Boot where the hook shaft exits the bottom shell.
4.  **Overload Protection:**
    *   **Hard Stop:** The Bridge hits the PCB/Shelf supports after 0.5mm of travel, preventing sensor crushing during gross overload.

## 5. Tube Management (Strain Relief) - Critical
*   **Problem:** Tension on the catheter tube (from patient movement) creates variable lift/force on the bag, corrupting weight data.
*   **Solution:** Integrated **Tube Retention Clip** molded into the **Stationary Front Shell**.
*   **Usage:** 
    1.  The nurse clips the incoming catheter tube into this holder.
    2.  This absorbs all pulling forces into the device body (and bed rail).
    3.  A consistent "slack loop" of tubing hangs between the Clip and the Bag Inlet, ensuring only the bag's weight is measured.

## 6. RF & Antenna Placement
*   **Location:** The antenna (Flex PCB type) must be adhered to the **Top Front** of the inside of the plastic shell.
*   **Separation:** Keep the antenna at least **20mm away** from the metal Bed Rail Clamp mechanism (Back) and the Load Cell/Hook assembly (Bottom).
*   **Orientation:** Vertical polarization is preferred for best omnidirectional coverage in a single-story ward.

## 7. User Interface & Battery
*   **Display:** E‑Ink (GDEY0213B74) mounted behind a clear PC (Polycarbonate) window glued into the Front Shell. The window should have a black masked border to hide the glue line.
*   **Buttons:** **Membrane Keypad** (Stick-on) on the front surface.
    *   *Routing:* The FPC tail from the keypad must pass through a sealed slot (potted with resin) to reach the PCB.
    *   *Functions:* "Tare/Zero" (Short Press), "Range Toggle" (Long Press).
*   **Battery (Current Plan):**
    *   The battery pack is in a **separate battery case** and connects to the PCB via a **2‑wire JST‑PH cable**.
    *   *Why:* reduces PCB size, reduces mechanical constraints on the PCB, and allows battery service without opening the electronics compartment.
*   **USB‑C (Development):**
    *   USB‑C should be accessible for bench power + console + flashing (via UART bootloader).
    *   For IP‑rating, consider a gasketed rubber plug or a recessed port with a sealing cap.

## 7. 3D Printing for Prototype
*   **Process:** FDM or SLA.
*   **Material:** PETG (easy to print, durable) or Resin (SLA for smooth finish).
*   **Draft Angle:** If moving to injection molding later, ensure vertical walls have 1-2 degrees of draft.
