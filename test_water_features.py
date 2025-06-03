#!/usr/bin/env python3
"""
Test water feature fetching for NYC area
"""

import subprocess
import json
import os
from collections import Counter

def test_water_features():
    """Test water feature fetching specifically"""
    
    # Test bbox: lower Manhattan, NYC (includes Hudson River and East River)
    bbox = {
        'south': 40.688765,
        'west': -74.020901,
        'north': 40.714110,
        'east': -73.987598
    }
    
    output_file = 'test_manhattan_water.geojson'
    
    # Build command - only fetch water features
    cmd = [
        'python', 'fetch_osm_data.py',
        '--south', str(bbox['south']),
        '--west', str(bbox['west']),
        '--north', str(bbox['north']),
        '--east', str(bbox['east']),
        '--output', output_file,
        '--water'  # Only water features
    ]
    
    print(f"Testing water features for bbox: {bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']}")
    print("-" * 80)
    
    # Run the command
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return
            
        print(f"Output: {result.stdout}")
        
        # Analyze the water features
        with open(output_file, 'r') as f:
            geojson = json.load(f)
            
        features = geojson.get('features', [])
        print(f"\nTotal water features: {len(features)}")
        print("-" * 80)
        
        # Categorize water features
        water_types = Counter()
        natural_types = Counter()
        waterway_types = Counter()
        geometry_types = Counter()
        names = []
        
        for feature in features:
            props = feature.get('properties', {})
            geom = feature.get('geometry', {})
            
            geometry_types[geom.get('type', 'unknown')] += 1
            
            # Check natural tag
            if 'natural' in props:
                natural_types[props['natural']] += 1
                
            # Check waterway tag
            if 'waterway' in props:
                waterway_types[props['waterway']] += 1
            
            # Check water tag
            if 'water' in props:
                water_types[props['water']] += 1
                
            # Collect names
            if 'name' in props:
                names.append(props['name'])
        
        print("Geometry Types:")
        for geom_type, count in geometry_types.most_common():
            print(f"  {geom_type}: {count}")
            
        print("\nNatural Types:")
        for natural_type, count in natural_types.most_common():
            print(f"  {natural_type}: {count}")
            
        print("\nWaterway Types:")
        for waterway_type, count in waterway_types.most_common():
            print(f"  {waterway_type}: {count}")
            
        print("\nWater Types:")
        for water_type, count in water_types.most_common():
            print(f"  {water_type}: {count}")
            
        print("\nNamed Water Features:")
        for name in set(names):
            print(f"  - {name}")
            
        # Check for specific water bodies we expect
        print("\nExpected Water Bodies Check:")
        expected = ['Hudson River', 'East River', 'Upper New York Bay']
        found = [e for e in expected if any(e in str(name) for name in names)]
        print(f"  Found: {found}")
        
        # Sample some polygon features
        print("\nSample Polygon Water Features:")
        polygon_count = 0
        for feature in features:
            if feature['geometry']['type'] in ['Polygon', 'MultiPolygon']:
                props = feature['properties']
                print(f"  - {props.get('name', 'Unnamed')} | natural={props.get('natural')} | water={props.get('water')} | waterway={props.get('waterway')}")
                polygon_count += 1
                if polygon_count >= 5:
                    break
                    
        # Clean up
        os.remove(output_file)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_water_features()