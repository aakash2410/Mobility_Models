import json
import random

import json
import osmnx as ox
import networkx as nx
import random

def get_ward_info(lat, lon):
    """
    Returns the real Census Population Density (persons/sq km)
    and Ward Locality Name based on boundaries in South Mumbai.
    """
    if lat < 18.94:
        return 29000, "Ward A (Colaba, Fort)"
    elif 18.94 <= lat < 18.96:
        if lon > 72.83:
            return 49000, "Ward B (Sandhurst Rd, Dongri)"
        else:
            return 114000, "Ward C (Marine Lines, Kalbadevi)"
    else: # lat >= 18.96
        if lon <= 72.82:
            return 45000, "Ward D (Malabar Hill, Grant Rd)"
        else:
            return 53000, "Ward E (Byculla, Mumbai Central)"

def fetch_real_mumbai_network():
    print("Fetching real Mumbai road network via OSMnx (South Mumbai bounds)...")
    # Fetch a bounded section of South Mumbai to keep node count reasonable for local iteration (~2000-5000 nodes)
    # Using Colaba to Byculla roughly
    north, south, east, west = 18.98, 18.90, 72.85, 72.80
    
    # Download drivable roads
    # OSMnx 2.0+ uses a bbox tuple (left, bottom, right, top) -> (west, south, east, north)
    G = ox.graph_from_bbox(bbox=(west, south, east, north), network_type='drive')
    print(f"Graph dynamically downloaded. Nodes: {len(G.nodes)}, Edges: {len(G.edges)}")
    
    nodes_data = []
    edges_data = []
    
    # OSmnx node IDs are large integers. We need to map them to 0-N continuous integers for PyTorch
    node_mapping = {}
    current_idx = 0
    
    for osmid, data in G.nodes(data=True):
        node_mapping[osmid] = current_idx
        # Open-Source Ward Population Density Integration
        y_val = round(data.get('y', 19.0), 6)
        x_val = round(data.get('x', 72.8), 6)
        
        # Get raw density and ward name
        raw_density, ward_name = get_ward_info(y_val, x_val)
        pop_density = round(raw_density / 114000.0, 3)

        # Extract features (OSM doesn't have native "highway" node tags usually, so we default to residential, or infer)
        nodes_data.append({
            "id": current_idx,
            "y": y_val,
            "x": x_val,
            "highway": "standard", # Node level classification isn't strict in OSM
            "population_density": pop_density,
            "ward_name": ward_name
        })
        current_idx += 1
        
    for u, v, key, data in G.edges(keys=True, data=True):
        # Default speeds based on highway tag
        hw = data.get('highway', 'residential')
        if type(hw) == list: hw = hw[0] # Sometimes OSM returns lists
        
        # Base logic for maxspeed if not explicitly provided
        base_speed = "30"
        if "motorway" in hw or "trunk" in hw:
            base_speed = "80"
        elif "primary" in hw or "secondary" in hw:
            base_speed = "50"
            
        maxspeed = data.get('maxspeed', base_speed)
        if type(maxspeed) == list: maxspeed = maxspeed[0]
        
        name = data.get('name', 'Unnamed Road')
        if type(name) == list: name = name[0]
        
        edges_data.append({
            "source": node_mapping[u],
            "target": node_mapping[v],
            "length": round(data.get('length', 100), 1),
            "highway": hw,
            "maxspeed": str(maxspeed).replace(" ", "").replace("mph", "").replace("km/h", ""),
            "name": name
        })
        
    output_file = "mumbai_network.json"
    print(f"Formatting completed. Saving to {output_file}...")
    
    with open(output_file, 'w') as f:
        json.dump({
            "metadata": {
                "source": "OpenStreetMap Real Topography (South Mumbai)",
                "nodes_count": len(nodes_data),
                "edges_count": len(edges_data)
            },
            "nodes": nodes_data,
            "edges": edges_data
        }, f)
        
    print("Dataset successfully saved! PyTorch is ready to retrain on physical coordinates.")

if __name__ == "__main__":
    fetch_real_mumbai_network()
