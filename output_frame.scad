// Frame for city model
// Outer size: 110.0mm x 110.0mm x 20mm
// Inner size: 100.0mm x 100.0mm x 20mm
// Frame width: 5mm

difference() {
    // Outer block (10mm larger than main model)
    cube([110.0, 110.0, 20]);
    
    // Inner cutout (sized to match main model exactly)
    translate([5, 5, 0])
        cube([100.0, 100.0, 20]);
}