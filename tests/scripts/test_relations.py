#!/usr/bin/env python3
"""
Test relation fetching from OSM
"""

import requests
import json

def test_direct_overpass():
    """Test Overpass API directly to see what relations we should get"""
    
    # Test bbox
    bbox = "40.688765,-74.020901,40.714110,-73.987598"
    
    # Query specifically for water relations
    query = f"""
[out:json][timeout:180];
(
  relation["natural"="water"]({bbox});
  relation["waterway"="riverbank"]({bbox});
  relation["type"="multipolygon"]["natural"="water"]({bbox});
);
out body;
>;
out skel qt;
"""
    
    print("Testing Overpass API directly for water relations...")
    print(f"Query:\n{query}")
    print("-" * 80)
    
    try:
        response = requests.post(
            "https://overpass-api.de/api/interpreter",
            data=query.encode('utf-8'),
            headers={'Content-Type': 'text/plain; charset=utf-8'},
            timeout=30
        )
        
        data = response.json()
        elements = data.get('elements', [])
        
        print(f"Total elements: {len(elements)}")
        
        # Analyze relations
        relations = [e for e in elements if e['type'] == 'relation']
        print(f"Relations found: {len(relations)}")
        
        for rel in relations:
            tags = rel.get('tags', {})
            members = rel.get('members', [])
            print(f"\nRelation {rel['id']}:")
            print(f"  Name: {tags.get('name', 'Unnamed')}")
            print(f"  Type: {tags.get('type')}")
            print(f"  Natural: {tags.get('natural')}")
            print(f"  Water: {tags.get('water')}")
            print(f"  Waterway: {tags.get('waterway')}")
            print(f"  Members: {len(members)}")
            
            # Count member types
            member_types = {}
            for m in members:
                key = f"{m['type']}-{m.get('role', 'none')}"
                member_types[key] = member_types.get(key, 0) + 1
            print(f"  Member breakdown: {member_types}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_direct_overpass()