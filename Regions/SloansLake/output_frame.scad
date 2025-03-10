// Frame for city model
// Outer size: 90.0mm x 90.0mm x 20mm
// Inner size: 80.0mm x 80.0mm x 20mm
// Frame width: 5mm

difference() {
    // Outer block (10mm larger than main model)
    cube([90.0, 90.0, 20]);
    
    // Inner cutout (sized to match main model exactly)
    translate([5, 5, 0])
        cube([80.0, 80.0, 20]);
}