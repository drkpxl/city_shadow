// Frame for city model
// Outer size: 210.0mm x 210.0mm x 20.0mm
// Inner size: 200.0mm x 200.0mm x 20.0mm
// Frame width: 5mm

difference() {
    // Outer block (10mm larger than main model)
    cube([210.0, 210.0, 20.0]);
    
    // Inner cutout (sized to match main model exactly)
    translate([5, 5, 0])
        cube([200.0, 200.0, 20.0]);
}