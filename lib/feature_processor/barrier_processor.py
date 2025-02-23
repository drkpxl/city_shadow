# lib/feature_processor/barrier_processor.py
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

def create_barrier_union(roads, railways, water, road_buffer=2.0, railway_buffer=2.0):
    """Combine roads, railways, and water into one shapely geometry used as a 'barrier'."""
    barrier_geoms = []

    # Roads -> buffered lines
    for road in roads:
        line = LineString(road["coords"])
        barrier_geoms.append(line.buffer(road_buffer))

    # Railways -> buffered lines
    for rail in railways:
        line = LineString(rail["coords"])
        barrier_geoms.append(line.buffer(railway_buffer))

    # Water -> polygons (no buffer)
    for wfeat in water:
        poly = Polygon(wfeat["coords"])
        barrier_geoms.append(poly)

    if barrier_geoms:
        return unary_union(barrier_geoms)
    else:
        return None
