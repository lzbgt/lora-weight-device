// Parameters
case_w = 70;
case_h = 120;
case_d = 35;
wall_th = 3;
fillet_r = 4;

window_w = 48.5; // E-Ink 2.13" visible width approx
window_h = 23.7; // E-Ink 2.13" visible height approx
window_y_offset = 20;

button_d = 12;
button_y_offset = -30;

hook_slot_w = 10;
hook_slot_d = 5;

screw_hole_d = 3.2;

$fn = 60;

// Main Body Module
module rounded_box(w, h, d, r) {
    hull() {
        translate([-w/2 + r, -h/2 + r, 0]) cylinder(r=r, h=d);
        translate([w/2 - r, -h/2 + r, 0]) cylinder(r=r, h=d);
        translate([-w/2 + r, h/2 - r, 0]) cylinder(r=r, h=d);
        translate([w/2 - r, h/2 - r, 0]) cylinder(r=r, h=d);
    }
}

module front_shell() {
    difference() {
        // Outer Shell
        rounded_box(case_w, case_h, case_d/2, fillet_r);
        
        // Inner Cavity (Hollow)
        translate([0, 0, wall_th]) 
            rounded_box(case_w - 2*wall_th, case_h - 2*wall_th, case_d/2, fillet_r);
            
        // Display Window Cutout
        translate([0, window_y_offset, -1])
            cube([window_w, window_h, wall_th + 2], center=true);
            
        // Button Hole
        translate([0, button_y_offset, -1])
            cylinder(d=button_d, h=wall_th + 2);
            
        // Hook Shaft Exit (Bottom)
        translate([0, -case_h/2 + wall_th, 0])
             cube([hook_slot_w, wall_th*4, hook_slot_d*2], center=true);
             
        // Screw Holes (Corners)
        screw_pos_w = case_w/2 - fillet_r - 2;
        screw_pos_h = case_h/2 - fillet_r - 2;
        for(x = [-screw_pos_w, screw_pos_w]) {
            for(y = [-screw_pos_h, screw_pos_h]) {
                translate([x, y, -1]) cylinder(d=screw_hole_d, h=case_d);
            }
        }
    }
    
    // Internal Mounting Posts (PCB Standoffs)
    post_pos_w = case_w/2 - 10;
    post_pos_h = case_h/2 - 20;
    for(x = [-post_pos_w, post_pos_w]) {
        for(y = [-post_pos_h, post_pos_h]) {
            translate([x, y, wall_th]) difference() {
                cylinder(d=6, h=5);
                translate([0,0,1]) cylinder(d=2.8, h=5);
            }
        }
    }
}

module back_shell() {
    difference() {
        // Outer Shell
        rounded_box(case_w, case_h, case_d/2, fillet_r);
        
        // Inner Cavity
        translate([0, 0, wall_th]) 
            rounded_box(case_w - 2*wall_th, case_h - 2*wall_th, case_d/2, fillet_r);
            
        // Screw Holes (Countersunk)
        screw_pos_w = case_w/2 - fillet_r - 2;
        screw_pos_h = case_h/2 - fillet_r - 2;
        for(x = [-screw_pos_w, screw_pos_w]) {
            for(y = [-screw_pos_h, screw_pos_h]) {
                translate([x, y, -1]) cylinder(d=screw_hole_d, h=case_d);
                translate([x, y, -1]) cylinder(d=6, h=wall_th); // Head recess
            }
        }
    }
    
    // Clamp Mount Boss (Center Back)
    translate([0, 10, -5]) difference() {
        cube([20, 30, 5], center=true);
        translate([0,0,-6]) cylinder(d=4, h=10); // Mounting screw for clamp
    }
}

// Render
translate([0, 0, 0]) front_shell();
translate([case_w + 10, 0, 0]) back_shell();
