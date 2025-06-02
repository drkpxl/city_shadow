#!/usr/bin/env python3
"""
Test script for OSM data fetching
Tests the fetch_osm_data.py script with a known bbox (lower Manhattan)
"""

import subprocess
import json
import os
import sys
from collections import Counter

def run_fetch_test():
    """Run the fetch_osm_data.py script with test parameters"""
    
    # Test bbox: lower Manhattan, NYC
    bbox = {
        'south': 40.688765,
        'west': -74.020901,
        'north': 40.714110,
        'east': -73.987598
    }
    
    output_file = 'test_manhattan.geojson'
    
    # Build command
    cmd = [
        'python', 'fetch_osm_data.py',
        '--south', str(bbox['south']),
        '--west', str(bbox['west']),
        '--north', str(bbox['north']),
        '--east', str(bbox['east']),
        '--output', output_file,
        '--buildings',
        '--roads',
        '--water',
        '--railways',
        '--parks'
    ]
    
    print(f"Testing OSM fetch for bbox: {bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 80)
    
    # Run the command
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error: Command failed with return code {result.returncode}")
            print(f"STDERR: {result.stderr}")
            return False
            
        print(f"STDOUT: {result.stdout}")
        
        # Check if file was created
        if not os.path.exists(output_file):
            print(f"Error: Output file {output_file} was not created")
            return False
            
        # Analyze the GeoJSON
        with open(output_file, 'r') as f:
            geojson = json.load(f)
            
        analyze_geojson(geojson)
        
        # Clean up
        os.remove(output_file)
        
        return True
        
    except Exception as e:
        print(f"Error running test: {e}")
        return False

def analyze_geojson(geojson):
    """Analyze the fetched GeoJSON data"""
    
    features = geojson.get('features', [])
    total_features = len(features)
    
    print(f"\nTotal features: {total_features}")
    print("-" * 80)
    
    # Count by OSM type
    osm_types = Counter()
    
    # Count by primary tag
    buildings = 0
    roads = 0
    railways = 0
    water_features = 0
    parks = 0
    
    # Count by geometry type
    geometry_types = Counter()
    
    # Detailed road type breakdown
    road_types = Counter()
    
    for feature in features:
        props = feature.get('properties', {})
        geom = feature.get('geometry', {})
        
        # Count OSM types
        osm_types[props.get('osm_type', 'unknown')] += 1
        
        # Count geometry types
        geometry_types[geom.get('type', 'unknown')] += 1
        
        # Categorize features
        if 'building' in props or 'building:part' in props:
            buildings += 1
            
        if 'highway' in props:
            roads += 1
            road_type = props.get('highway', 'unknown')
            road_types[road_type] += 1
            
        if 'railway' in props:
            railways += 1
            
        if ('natural' in props and props['natural'] in ['water', 'coastline']) or 'waterway' in props:
            water_features += 1
            
        if 'leisure' in props or ('landuse' in props and props['landuse'] in ['park', 'forest', 'grass', 'meadow', 'recreation_ground']):
            parks += 1
    
    # Print summary
    print("Feature Categories:")
    print(f"  Buildings:      {buildings:,}")
    print(f"  Roads:          {roads:,}")
    print(f"  Railways:       {railways:,}")
    print(f"  Water features: {water_features:,}")
    print(f"  Parks/Leisure:  {parks:,}")
    
    print(f"\nOSM Types:")
    for osm_type, count in osm_types.most_common():
        print(f"  {osm_type}: {count:,}")
    
    print(f"\nGeometry Types:")
    for geom_type, count in geometry_types.most_common():
        print(f"  {geom_type}: {count:,}")
    
    print(f"\nTop 10 Road Types:")
    for road_type, count in road_types.most_common(10):
        print(f"  {road_type}: {count}")
    
    # Some basic validation
    print("\nValidation:")
    print(f"  ✓ Features have properties: {all('properties' in f for f in features)}")
    print(f"  ✓ Features have geometry: {all('geometry' in f for f in features)}")
    print(f"  ✓ All geometries have type: {all('type' in f.get('geometry', {}) for f in features)}")
    
    # Sample feature
    if features:
        print("\nSample feature:")
        sample = features[0]
        print(f"  Type: {sample['geometry']['type']}")
        print(f"  Properties: {list(sample['properties'].keys())[:5]}...")

if __name__ == "__main__":
    print("OSM Data Fetch Test")
    print("=" * 80)
    
    success = run_fetch_test()
    
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed!")
        sys.exit(1)