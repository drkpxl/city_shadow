// Frame for city model
// Outer size: 130.0mm x 130.0mm x 10.0mm
// Inner size: 120.0mm x 120.0mm x 10.0mm
// Frame width: 5mm

difference() {
    // Outer block (10mm larger than main model)
    cube([130.0, 130.0, 10.0]);
    
    // Inner cutout (sized to match main model exactly)
    translate([5, 5, 0])
        cube([120.0, 120.0, 10.0]);
}