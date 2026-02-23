import json
import matplotlib.pyplot as plt
import contextily as ctx
import os

def plot_mumbai_network(json_path="mumbai_network.json", output_path="mumbai_visualization.png"):
    print("Loading network data for visualization...")
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    nodes = data['nodes']
    edges = data['edges']
    
    # Extract coordinates
    # We invert x/y because contextily expects (longitude, latitude)
    lons = [node['x'] for node in nodes]
    lats = [node['y'] for node in nodes]
    
    print("Plotting nodes and edges...")
    fig, ax = plt.subplots(figsize=(12, 12))
    
    # 1. Plot Edges first (so they are underneath nodes)
    # To avoid plotting 3000+ line segments individually (very slow), 
    # we can just plot the nodes for the bounding box context, but drawing edges makes it look like a network.
    # We will sample 20% of edges to keep the plot clean
    import random
    sample_edges = random.sample(edges, k=int(len(edges) * 0.2))
    
    for edge in sample_edges:
        src = nodes[edge['source']]
        dst = nodes[edge['target']]
        ax.plot([src['x'], dst['x']], [src['y'], dst['y']], 
                color='blue', linewidth=0.5, alpha=0.3)
                
    # 2. Plot Nodes
    ax.scatter(lons, lats, c='red', s=10, alpha=0.8, edgecolors='none', zorder=5)
    
    # Remove axes for cleaner map look
    ax.set_axis_off()
    
    # 3. Add Contextily Basemap (Mumbai)
    print("Fetching map tiles for Mumbai bounding box...")
    # EPSG:4326 is standard GPS coordinates (lon/lat), contextily needs to project it.
    ctx.add_basemap(ax, crs="EPSG:4326", source=ctx.providers.CartoDB.Positron)
    
    plt.title("Synthetic Mumbai Routing Topography", fontsize=16, pad=20)
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Visualization saved to {output_path}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, 'mumbai_network.json')
    out_path = os.path.join(current_dir, 'mumbai_visualization.png')
    plot_mumbai_network(json_path, out_path)
