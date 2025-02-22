// Frame for city model
// Outer size: 170.0mm x 170.0mm x 20mm
// Inner size: 160.0mm x 160.0mm x 20mm
// Frame width: 5mm

difference() {
    // Outer block (10mm larger than main model)
    cube([170.0, 170.0, 20]);
    
    // Inner cutout (sized to match main model exactly)
    translate([5, 5, 0])
        cube([160.0, 160.0, 20]);
}