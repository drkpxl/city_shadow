#!/usr/bin/env python3
"""
Helper module to build polygons from OSM relations
"""

from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def connect_ways(way_coords_list: List[List[List[float]]]) -> List[List[List[float]]]:
    """
    Connect a list of ways into continuous rings.
    
    Args:
        way_coords_list: List of ways, where each way is a list of [lon, lat] coordinates
        
    Returns:
        List of connected rings
    """
    if not way_coords_list:
        return []
    
    # Work with a copy
    remaining_ways = [way[:] for way in way_coords_list]
    rings = []
    
    while remaining_ways:
        # Start a new ring with the first available way
        current_ring = remaining_ways.pop(0)
        
        # Try to connect more ways
        made_connection = True
        while made_connection and remaining_ways:
            made_connection = False
            
            # Get the end points of current ring
            ring_start = current_ring[0]
            ring_end = current_ring[-1]
            
            # Check if ring is already closed
            if ring_start == ring_end and len(current_ring) >= 4:
                rings.append(current_ring)
                break
            
            # Try to find a connecting way
            for i, way in enumerate(remaining_ways):
                way_start = way[0]
                way_end = way[-1]
                
                # Check all possible connections
                if points_equal(ring_end, way_start):
                    # Connect at the end
                    current_ring.extend(way[1:])  # Skip duplicate point
                    remaining_ways.pop(i)
                    made_connection = True
                    break
                elif points_equal(ring_end, way_end):
                    # Connect reversed way at the end
                    current_ring.extend(reversed(way[:-1]))  # Skip duplicate point
                    remaining_ways.pop(i)
                    made_connection = True
                    break
                elif points_equal(ring_start, way_end):
                    # Connect at the beginning
                    current_ring = way[:-1] + current_ring  # Skip duplicate point
                    remaining_ways.pop(i)
                    made_connection = True
                    break
                elif points_equal(ring_start, way_start):
                    # Connect reversed way at the beginning
                    current_ring = list(reversed(way[1:])) + current_ring  # Skip duplicate point
                    remaining_ways.pop(i)
                    made_connection = True
                    break
        
        # Check if we created a valid ring
        if len(current_ring) >= 4:
            # Close the ring if needed
            if current_ring[0] != current_ring[-1]:
                # Check if start and end are close enough to close
                if points_close(current_ring[0], current_ring[-1], tolerance=0.000001):
                    current_ring.append(current_ring[0])
            
            if current_ring[0] == current_ring[-1]:
                rings.append(current_ring)
    
    return rings

def points_equal(p1: List[float], p2: List[float]) -> bool:
    """Check if two points are equal."""
    return p1[0] == p2[0] and p1[1] == p2[1]

def points_close(p1: List[float], p2: List[float], tolerance: float = 0.000001) -> bool:
    """Check if two points are close enough to be considered equal."""
    return abs(p1[0] - p2[0]) < tolerance and abs(p1[1] - p2[1]) < tolerance

def build_multipolygon_from_relation(
    outer_ways: List[List[List[float]]], 
    inner_ways: List[List[List[float]]]
) -> Optional[Dict]:
    """
    Build a MultiPolygon geometry from outer and inner ways.
    
    Args:
        outer_ways: List of outer ways
        inner_ways: List of inner ways
        
    Returns:
        GeoJSON geometry dict or None if invalid
    """
    # Connect outer ways into rings
    outer_rings = connect_ways(outer_ways)
    
    if not outer_rings:
        return None
    
    # Connect inner ways into rings
    inner_rings = connect_ways(inner_ways) if inner_ways else []
    
    # Build geometry
    if len(outer_rings) == 1 and not inner_rings:
        # Simple polygon
        return {
            "type": "Polygon",
            "coordinates": outer_rings
        }
    elif len(outer_rings) == 1:
        # Polygon with holes
        coordinates = outer_rings + inner_rings
        return {
            "type": "Polygon",
            "coordinates": coordinates
        }
    else:
        # MultiPolygon
        # For simplicity, create separate polygons
        # In production, would need to properly associate holes with their polygons
        polygons = []
        for outer in outer_rings:
            polygons.append([outer])
        
        return {
            "type": "MultiPolygon",
            "coordinates": polygons
        }

if __name__ == "__main__":
    # Test the connection algorithm
    test_ways = [
        [[0, 0], [1, 0], [1, 1]],  # First segment
        [[1, 1], [0, 1], [0, 0]]   # Second segment that completes the square
    ]
    
    rings = connect_ways(test_ways)
    print(f"Connected {len(test_ways)} ways into {len(rings)} rings")
    for i, ring in enumerate(rings):
        print(f"Ring {i}: {len(ring)} points, closed: {ring[0] == ring[-1]}")