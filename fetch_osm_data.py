#!/usr/bin/env python3
"""
Fetch OpenStreetMap data using Overpass API and convert to GeoJSON
"""

import argparse
import json
import sys
import time
import requests
from typing import Dict, List, Tuple, Any
import logging
from shapely.geometry import shape, box, Point, LineString, Polygon, MultiPolygon, MultiLineString
from shapely.ops import unary_union
import warnings
from osm_relation_builder import build_multipolygon_from_relation

# Suppress shapely warnings
warnings.filterwarnings('ignore', category=UserWarning)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Overpass API endpoint
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def build_overpass_query(bbox: Tuple[float, float, float, float], features: Dict[str, bool]) -> str:
    """
    Build Overpass API query based on selected features
    
    Args:
        bbox: (south, west, north, east)
        features: Dictionary of feature types to include
    
    Returns:
        Overpass QL query string
    """
    south, west, north, east = bbox
    bbox_str = f"{south},{west},{north},{east}"
    
    # Start building the query
    query_parts = [
        "[out:json][timeout:180];",
        "("
    ]
    
    # Add feature queries based on what's selected
    if features.get('buildings', False):
        query_parts.extend([
            f'  way["building"]({bbox_str});',
            f'  relation["building"]({bbox_str});',
            f'  way["building:part"]({bbox_str});',
            f'  relation["building:part"]({bbox_str});'
        ])
    
    if features.get('roads', False):
        query_parts.append(f'  way["highway"]({bbox_str});')
    
    if features.get('railways', False):
        query_parts.append(f'  way["railway"]({bbox_str});')
    
    if features.get('water', False):
        query_parts.extend([
            f'  way["natural"="water"]({bbox_str});',
            f'  relation["natural"="water"]({bbox_str});',
            f'  way["natural"="bay"]({bbox_str});',
            f'  relation["natural"="bay"]({bbox_str});',
            f'  way["water"="bay"]({bbox_str});',
            f'  relation["water"="bay"]({bbox_str});',
            f'  way["waterway"]({bbox_str});',
            f'  relation["waterway"]({bbox_str});',
            f'  way["waterway"="riverbank"]({bbox_str});',
            f'  relation["waterway"="riverbank"]({bbox_str});',
            f'  way["natural"="coastline"]({bbox_str});'
        ])
    
    if features.get('parks', False):
        query_parts.extend([
            f'  way["leisure"]({bbox_str});',
            f'  relation["leisure"]({bbox_str});',
            f'  way["landuse"~"park|forest|grass|meadow|recreation_ground"]({bbox_str});',
            f'  relation["landuse"~"park|forest|grass|meadow|recreation_ground"]({bbox_str});'
        ])
    
    # Close the union and request full geometry
    query_parts.extend([
        ");",
        "(._;>;);",
        "out body;"
    ])
    
    return "\n".join(query_parts)

def osm_to_geojson_feature(element: Dict[str, Any], nodes: Dict[int, Tuple[float, float]], ways: Dict[int, List[List[float]]] = None) -> Dict[str, Any]:
    """
    Convert an OSM element to a GeoJSON feature
    
    Args:
        element: OSM element (node, way, or relation)
        nodes: Dictionary mapping node IDs to (lon, lat) coordinates
    
    Returns:
        GeoJSON feature dictionary
    """
    feature = {
        "type": "Feature",
        "properties": element.get("tags", {}),
        "geometry": None
    }
    
    # Add OSM metadata
    feature["properties"]["osm_id"] = element["id"]
    feature["properties"]["osm_type"] = element["type"]
    
    if element["type"] == "node":
        feature["geometry"] = {
            "type": "Point",
            "coordinates": [element["lon"], element["lat"]]
        }
    
    elif element["type"] == "way":
        if "nodes" in element and element["nodes"]:
            coordinates = []
            for node_id in element["nodes"]:
                if node_id in nodes:
                    lon, lat = nodes[node_id]
                    coordinates.append([lon, lat])
            
            if len(coordinates) >= 2:
                # Check if it's a closed way (polygon)
                if coordinates[0] == coordinates[-1] and len(coordinates) >= 4:
                    feature["geometry"] = {
                        "type": "Polygon",
                        "coordinates": [coordinates]
                    }
                else:
                    feature["geometry"] = {
                        "type": "LineString",
                        "coordinates": coordinates
                    }
    
    elif element["type"] == "relation":
        # Handle multipolygon relations (common for water bodies)
        if element.get("tags", {}).get("type") == "multipolygon":
            outer_ways = []
            inner_ways = []
            
            # Collect all ways for this relation
            for member in element.get("members", []):
                if member["type"] == "way" and ways and member["ref"] in ways:
                    way_coords = ways[member["ref"]]
                    if len(way_coords) >= 2:  # Valid way
                        if member["role"] == "outer":
                            outer_ways.append(way_coords)
                        elif member["role"] == "inner":
                            inner_ways.append(way_coords)
            
            # Build multipolygon using the helper
            if outer_ways:
                geometry = build_multipolygon_from_relation(outer_ways, inner_ways)
                if geometry:
                    feature["geometry"] = geometry
    
    return feature

def fetch_osm_data(bbox: Tuple[float, float, float, float], features: Dict[str, bool]) -> Dict[str, Any]:
    """
    Fetch data from Overpass API
    
    Args:
        bbox: (south, west, north, east)
        features: Dictionary of feature types to include
    
    Returns:
        OSM data as dictionary
    """
    query = build_overpass_query(bbox, features)
    logger.info(f"Overpass query:\n{query}")
    
    # Make the request
    try:
        response = requests.post(OVERPASS_URL, data=query.encode('utf-8'), 
                               headers={'Content-Type': 'text/plain; charset=utf-8'},
                               timeout=180)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Received {len(data.get('elements', []))} elements from Overpass API")
        return data
        
    except requests.exceptions.Timeout:
        logger.error("Overpass API request timed out")
        raise Exception("Request timed out. Try a smaller area or fewer features.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching from Overpass API: {e}")
        raise Exception(f"Failed to fetch data from Overpass API: {str(e)}")

def clip_geometry_to_bbox(geometry: Dict[str, Any], bbox_polygon: Polygon) -> Dict[str, Any]:
    """
    Clip a geometry to the bounding box
    
    Args:
        geometry: GeoJSON geometry dict
        bbox_polygon: Shapely polygon representing the bbox
    
    Returns:
        Clipped geometry dict or None if outside bbox
    """
    try:
        # Convert GeoJSON to shapely geometry
        geom = shape(geometry)
        
        # Check if geometry intersects with bbox
        if not geom.intersects(bbox_polygon):
            return None
        
        # For points, just check if inside
        if geometry["type"] == "Point":
            return geometry if geom.within(bbox_polygon) else None
        
        # For lines and polygons, clip to bbox
        clipped = geom.intersection(bbox_polygon)
        
        # Convert back to GeoJSON
        if clipped.is_empty:
            return None
            
        # Handle geometry collections resulting from clipping
        if clipped.geom_type == 'GeometryCollection':
            # Extract the relevant geometry type
            geoms = list(clipped.geoms)
            if len(geoms) == 1:
                clipped = geoms[0]
            else:
                # Find the geometry with the same type as original
                for g in geoms:
                    if g.geom_type == geom.geom_type:
                        clipped = g
                        break
        
        # Convert back to GeoJSON format
        if clipped.geom_type == 'Point':
            return {
                "type": "Point",
                "coordinates": list(clipped.coords)[0]
            }
        elif clipped.geom_type == 'LineString':
            return {
                "type": "LineString",
                "coordinates": list(clipped.coords)
            }
        elif clipped.geom_type == 'Polygon':
            return {
                "type": "Polygon",
                "coordinates": [list(clipped.exterior.coords)] + [list(hole.coords) for hole in clipped.interiors]
            }
        elif clipped.geom_type == 'MultiLineString':
            return {
                "type": "MultiLineString",
                "coordinates": [list(line.coords) for line in clipped.geoms]
            }
        elif clipped.geom_type == 'MultiPolygon':
            return {
                "type": "MultiPolygon",
                "coordinates": [
                    [list(poly.exterior.coords)] + [list(hole.coords) for hole in poly.interiors]
                    for poly in clipped.geoms
                ]
            }
        else:
            logger.warning(f"Unhandled geometry type after clipping: {clipped.geom_type}")
            return None
            
    except Exception as e:
        logger.warning(f"Error clipping geometry: {e}")
        return None

def convert_to_geojson(osm_data: Dict[str, Any], bbox: Tuple[float, float, float, float]) -> Dict[str, Any]:
    """
    Convert OSM data to GeoJSON format with bbox clipping
    
    Args:
        osm_data: Raw OSM data from Overpass API
        bbox: (south, west, north, east) for clipping
    
    Returns:
        GeoJSON FeatureCollection with clipped features
    """
    # Create bbox polygon for clipping
    south, west, north, east = bbox
    bbox_polygon = box(west, south, east, north)
    
    # First, build a dictionary of all nodes for quick lookup
    nodes = {}
    for element in osm_data.get("elements", []):
        if element["type"] == "node":
            nodes[element["id"]] = (element["lon"], element["lat"])
    
    # Build dictionary of ways for relation processing
    ways = {}
    for element in osm_data.get("elements", []):
        if element["type"] == "way" and "nodes" in element:
            way_coords = []
            for node_id in element["nodes"]:
                if node_id in nodes:
                    lon, lat = nodes[node_id]
                    way_coords.append([lon, lat])
            if way_coords:
                ways[element["id"]] = way_coords
    
    # Convert elements to GeoJSON features
    features = []
    clipped_count = 0
    
    for element in osm_data.get("elements", []):
        if element["type"] in ["way", "node", "relation"]:
            feature = osm_to_geojson_feature(element, nodes, ways)
            if feature["geometry"] is not None:
                # Clip geometry to bbox
                clipped_geom = clip_geometry_to_bbox(feature["geometry"], bbox_polygon)
                if clipped_geom:
                    feature["geometry"] = clipped_geom
                    features.append(feature)
                else:
                    clipped_count += 1
    
    logger.info(f"Converted {len(features)} features to GeoJSON ({clipped_count} features were outside bbox)")
    
    return {
        "type": "FeatureCollection",
        "features": features
    }

def main():
    parser = argparse.ArgumentParser(description="Fetch OSM data and convert to GeoJSON")
    parser.add_argument("--south", type=float, required=True, help="Southern boundary")
    parser.add_argument("--west", type=float, required=True, help="Western boundary")
    parser.add_argument("--north", type=float, required=True, help="Northern boundary")
    parser.add_argument("--east", type=float, required=True, help="Eastern boundary")
    parser.add_argument("--output", required=True, help="Output GeoJSON file path")
    
    # Feature flags
    parser.add_argument("--buildings", action="store_true", help="Include buildings")
    parser.add_argument("--roads", action="store_true", help="Include roads")
    parser.add_argument("--water", action="store_true", help="Include water features")
    parser.add_argument("--railways", action="store_true", help="Include railways")
    parser.add_argument("--parks", action="store_true", help="Include parks and leisure areas")
    
    args = parser.parse_args()
    
    # Build bbox and features dictionary
    bbox = (args.south, args.west, args.north, args.east)
    features = {
        'buildings': args.buildings,
        'roads': args.roads,
        'water': args.water,
        'railways': args.railways,
        'parks': args.parks
    }
    
    # If no features selected, default to buildings and roads
    if not any(features.values()):
        logger.warning("No features selected, defaulting to buildings and roads")
        features['buildings'] = True
        features['roads'] = True
    
    try:
        logger.info(f"Fetching OSM data for bbox: {bbox}")
        logger.info(f"Selected features: {[k for k, v in features.items() if v]}")
        
        # Fetch data from Overpass API
        osm_data = fetch_osm_data(bbox, features)
        
        # Convert to GeoJSON with clipping
        geojson = convert_to_geojson(osm_data, bbox)
        
        # Save to file
        with open(args.output, 'w') as f:
            json.dump(geojson, f, indent=2)
        
        logger.info(f"Successfully saved GeoJSON to {args.output}")
        print(f"Success: Saved {len(geojson['features'])} features to {args.output}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()