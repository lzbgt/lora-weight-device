# PCB Physical Specification & Footprint Definition

## 1. PCB Outline & Mounting
*   **Dimensions:** 64mm (W) x 100mm (H)
    *   *Constraint:* Fits inside 70x120mm case with 3mm walls + 1mm clearance per side.
*   **Corner Radius:** 3mm (Matches enclosure internal fillet).
*   **Thickness:** 1.6mm (Standard FR4).
*   **Mounting Holes (4x):**
    *   **Diameter:** 3.2mm (Fits M3 Standoff).
    *   **Keepout:** 6.5mm Diameter (Screw Head / Washer).
    *   **Locations (Relative to PCB Center 0,0):**
        *   Top-Left: (-28, +46)
        *   Top-Right: (+28, +46)
        *   Bottom-Left: (-28, -46)
        *   Bottom-Right: (+28, -46)

## 2. Component Placement Strategy (Z-Axis Stackup)
The case depth is 35mm. The stackup must accommodate the Screen (Front) and Battery (Back).

*   **Front Side (Facing User/Screen):**
    *   **E-Ink Display (GDEY0213B74):**
        *   *Position:* Centered Horizontally, Top-Offset Y=+15mm.
        *   *Connection:* 24-Pin FPC Connector (Bottom Contact) placed below the screen area.
        *   *Clearance:* NO components > 2mm height allowed behind the screen area.
    *   **User Button:** Membrane Keypad tail enters via slot at Y=-20mm. FPC Connector on Front.
    *   **Antenna:** IPEX Connector at Top Edge (Y=+48mm).

*   **Back Side (Facing Battery/Wall):**
    *   **Battery Holder (Keystone 1028):**
        *   *Size:* 57mm x 32mm x 16mm (Height).
        *   *Position:* Bottom Half of PCB (Y center approx -25mm).
        *   *Clearance:* Ensures >16mm height available (Enclosure Back shell is deep).
    *   **Tall Components:** Electrolytic Caps, Inductor, RAK3172 Module.
    *   **Load Cell Bridge:** The "Pull-to-Push" mechanism requires a clear vertical channel through the PCB bottom center.

## 3. Critical Keepouts & Mechanics
### A. Load Cell Aperture (Bottom Center)
*   **Purpose:** Allows the Hook Shaft to pass through the PCB to pull down on the bridge.
*   **Location:** Center X=0, Y=-40mm (Between bottom mounting holes).
*   **Cutout Size:** 8mm x 15mm Slot (allows shaft movement/assembly).
*   **Sensor Footprint (FX1901):**
    *   Placed on a rigid section *adjacent* to the slot (e.g., Y=-32mm).
    *   Requires a 16mm Diameter Keepout circle for the sensor body.

### B. Antenna Keepout (Top Edge)
*   **Location:** Top 10mm of the PCB (Y > +40mm).
*   **Rule:** NO Copper Pour on Top or Bottom layers (except RF Trace).
*   **Why:** prevents detuning the Flex PCB antenna glued to the case roof.

### C. Battery Connector
*   **Type:** 2x Through-Hole Pads (Large) or JST-PH (Right Angle).
*   **Location:** Near Battery Holder pins (Y ~ -25mm).

## 4. Height Map Summary
| Zone | X/Y Range | Max Component Height (Front) | Max Component Height (Back) | Note |
| :--- | :--- | :--- | :--- | :--- |
| **Display Area** | X: -25 to +25, Y: +5 to +45 | 1.5mm (Slim Connectors/Caps) | 10mm (RAK3172, LDO) | Front restricted by Screen |
| **Battery Area** | X: -28 to +28, Y: -45 to -10 | 10mm (Inductor, Caps) | 0mm (Occupied by Battery) | Back restricted by Battery |
| **Antenna Zone** | Y > +45 | 2mm | 2mm | Keep clear for RF |
| **Edges (3mm)** | Perimeter | 0mm | 0mm | Case Walls / Rails |

## 5. Summary Check vs Enclosure (35mm Depth)
*   **Stackup:**
    *   Front Case Wall: 2mm
    *   Window/Screen: 1.5mm
    *   **PCB:** 1.6mm
    *   Battery Holder: 16mm
    *   Back Case Wall: 2mm
    *   **Total Stack:** ~23.1mm.
*   **Result:** ~12mm remaining "Air Gap" for clearance, wires, and assembly tolerances. **Fits comfortably.**
