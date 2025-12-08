// Urine Monitor Case & Assembly
// Dimensions: mm

// --- Parameters ---

// PCB Dimensions (from KiCad Edge.Cuts)
pcb_w = 64;
pcb_h = 100;
pcb_th = 1.6;

// Clearance
clearance = 1.0; 

// Case Dimensions
wall_th = 2.5;
case_w = pcb_w + 2*clearance + 2*wall_th; // approx 71mm
case_h = pcb_h + 2*clearance + 2*wall_th + 15; // Extra space for hook mech at bottom
case_d = 35;
fillet_r = 4;

// Display (GDEY0213B74 2.13" E-Ink)
disp_w = 48.5; 
disp_h = 23.7; 
disp_pcb_w = 59.2; // Module PCB width
disp_pcb_h = 29.2;
disp_y_offset = 20;

// Components
batt_dia = 14.5;
batt_len = 50.5;

// Hook / Sensor
sensor_dia = 15;
sensor_h = 5;

// View Control
show_case_front = 1;
show_case_back = 1;
show_pcb = 1;
show_internals = 1;
exploded = 20; // Distance to separate parts for view

$fn = 50;

// --- Components Modules ---

module pcb_board() {
    color("green") 
        difference() {
            cube([pcb_w, pcb_h, pcb_th], center=true);
            // Mounting holes
            for(x=[-30, 30]) for(y=[-48, 48])
                translate([x, y, -1]) cylinder(d=3.2, h=5);
        }
}

module display_module() {
    // Glass
    color("white") translate([0, disp_y_offset, 1])
        cube([disp_w, disp_h, 1.2], center=true);
    // Ribbon / Driver area
    color("gray") translate([0, disp_y_offset - 15, 0.5])
        cube([30, 10, 1], center=true);
}

module battery_pack() {
    // 2x AA Holder
    color("black") translate([0, 0, 0])
        cube([batt_dia*2 + 4, batt_len + 4, batt_dia/2 + 2], center=true);
    // Batteries
    color("blue") translate([-batt_dia/2 - 1, 0, 2])
        rotate([90, 0, 0]) cylinder(d=batt_dia, h=batt_len, center=true);
    color("blue") translate([batt_dia/2 + 1, 0, 2])
        rotate([90, 0, 0]) cylinder(d=batt_dia, h=batt_len, center=true);
}

module load_cell_sensor() {
    color("silver") cylinder(d=sensor_dia, h=sensor_h);
    color("red") translate([0,0,sensor_h]) cylinder(d=4, h=2); // Button nip
}

module hook_bridge() {
    color("orange") {
        difference() {
            union() {
                // Cross bar
                translate([0, 0, 5]) cube([30, 10, 6], center=true);
                // Vertical legs down to hook
                translate([0, -5, -5]) cube([10, 5, 20], center=true);
            }
        }
        // Hook
        translate([0, -5, -15]) rotate([0, 90, 0]) cylinder(d=4, h=10, center=true);
    }
}

// --- Case Modules ---

module rounded_rect(w, h, d, r) {
    hull() {
        translate([-w/2+r, -h/2+r, 0]) cylinder(r=r, h=d);
        translate([w/2-r, -h/2+r, 0]) cylinder(r=r, h=d);
        translate([-w/2+r, h/2-r, 0]) cylinder(r=r, h=d);
        translate([w/2-r, h/2-r, 0]) cylinder(r=r, h=d);
    }
}

module front_shell() {
    color("whitesmoke", 0.8) 
    difference() {
        // Body
        rounded_rect(case_w, case_h, case_d/2, fillet_r);
        
        // Interior hollow
        translate([0, 0, wall_th])
            rounded_rect(case_w - 2*wall_th, case_h - 2*wall_th, case_d/2, fillet_r);
            
        // Window Cutout
        translate([0, disp_y_offset, -1])
            cube([disp_w, disp_h, wall_th+2], center=true);
            
        // Screw Bosses Recess (from inside)
        // ... omitted for brevity, implied standard boss
    }
    
    // Tube Clip (External feature)
    translate([case_w/2, -20, case_d/4]) rotate([0, 90, 0])
        difference() {
            cylinder(d=15, h=10); // Holder body
            translate([0,0,-1]) cylinder(d=6, h=12); // Tube hole
            translate([3, 0, -1]) cube([6, 15, 12], center=true); // Side opening
        }
}

module back_shell() {
    color("whitesmoke", 0.8)
    difference() {
        rounded_rect(case_w, case_h, case_d/2, fillet_r);
        
        translate([0, 0, wall_th])
            rounded_rect(case_w - 2*wall_th, case_h - 2*wall_th, case_d/2, fillet_r);
            
        // Battery Door Cutout (simplified)
        translate([0, -10, -1])
             rounded_rect(35, 55, wall_th+2, 2);
    }
    
    // Clamp Mount
    translate([0, 20, -5]) cube([20, 30, 5], center=true);
}


// --- Assembly ---

// Z-Stacking order:
// Front Shell -> Display -> PCB -> Batteries -> Back Shell

// 1. Front Shell
if (show_case_front)
    translate([0, 0, exploded*2 + 10]) rotate([180, 0, 0]) front_shell();

// 2. Internals
if (show_internals) {
    translate([0, 0, 0]) {
        // Display
        translate([0, 0, 3]) display_module();
        
        // PCB
        if (show_pcb) translate([0, 0, 0]) pcb_board();
        
        // Batteries (on back of PCB)
        translate([0, -10, -batt_dia/2 - 2]) battery_pack();
        
        // Sensor (Bottom of PCB)
        translate([0, -pcb_h/2 + 10, -3]) load_cell_sensor();
        
        // Hook Mechanism
        translate([0, -pcb_h/2 + 10, -10]) hook_bridge();
    }
}

// 3. Back Shell
if (show_case_back)
    translate([0, 0, -exploded - 15]) rotate([180, 0, 0]) scale([1, 1, -1]) back_shell();


