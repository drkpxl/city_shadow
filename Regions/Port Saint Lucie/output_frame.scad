// Frame for city model
// Outer size: 130.0mm x 130.0mm x 20mm
// Inner size: 120.0mm x 120.0mm x 20mm
// Frame width: 5mm

difference() {
    cube([130.0, 130.0, 20]);
    translate([5, 5, 0])
        cube([120.0, 120.0, 20]);
}