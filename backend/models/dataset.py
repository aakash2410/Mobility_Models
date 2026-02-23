import json
import torch
from torch_geometric.data import Data
import random

def load_mumbai_data(filepath="mumbai_network.json"):
    """
    Loads mock Mumbai road network and converts it into PyTorch Geometric format.
    Generates synthetic target labels for training purposes.
    """
    with open(filepath, 'r') as f:
        data = json.load(f)
        
    nodes = data['nodes']
    edges = data['edges']
    
    # 1. Create edge_index array
    # PyTorch Geometric expects edge_index to be structured as [2, num_edges]
    source_nodes = []
    target_nodes = []
    edge_attr_list = []
    
    for edge in edges:
        source_nodes.append(edge['source'])
        target_nodes.append(edge['target'])
        
        edge_length = float(edge.get('length', 100.0))
        max_speed = float(edge.get('maxspeed', 50)) / 100.0
        edge_attr_list.append([edge_length, max_speed])
        
    # Convert lists to tensor
    edge_index = torch.tensor([source_nodes, target_nodes], dtype=torch.long)
    edge_attr = torch.tensor(edge_attr_list, dtype=torch.float)
    
    # 2. Extract and Synthesize Node Features (x) and Targets (y)
    x_list = []
    y_list = []
    
    for node in nodes:
        # GNN expects 5 input features per node: [population_density, traffic_volume, speed_limit, node_type (motorway=1, micromob=0), pending_requests]
        pop_density = node.get("population_density", 0.5)
        traffic_volume = random.uniform(0.1, 1.0) * pop_density
        speed_limit = random.choice([30, 50, 80]) / 100.0
        node_type = 1.0 if node.get('highway') == 'primary' else 0.0
        pending_requests = random.uniform(0, 5) * pop_density
        
        x_list.append([pop_density, traffic_volume, speed_limit, node_type, pending_requests])
        
        # GNN outputs 3 target features: [predicted_traffic_flow, optimal_eta, fleet_allocation_score]
        # We synthesize ground truth (y) based somewhat on the input features so the model actually learns a mapping
        # Removing uniform noise to prevent training unpredictability
        predicted_flow = traffic_volume * (1.2 - speed_limit) + (pending_requests * 0.05)
        optimal_eta = (1.0 - speed_limit) + traffic_volume * 0.5 # slower speed + high volume = higher ETA
        fleet_score = pending_requests / 5.0 # more requests = higher allocation score needed
        
        y_list.append([predicted_flow, optimal_eta, fleet_score])
        
    x = torch.tensor(x_list, dtype=torch.float)
    y = torch.tensor(y_list, dtype=torch.float)
    
    # Smooth the mock ground truth targets across the network edges 
    # This ensures that a node's targets directly mathematically depend on its neighbors.
    # Without this, the model's graph convolution layers (which blend neighbors) 
    # get punished for acting like a topological network.
    for src, dst in zip(source_nodes, target_nodes):
        y[dst] += y[src] * 0.1
    
    # 3. Create PyTorch Geometric Data object
    graph_data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y)
    
    return graph_data

if __name__ == "__main__":
    import os
    json_path = os.path.join(os.path.dirname(__file__), '..', 'mumbai_network.json')
    data = load_mumbai_data(json_path)
    print("Graph Data loaded successfully!")
    print(f"Num Nodes: {data.num_nodes}")
    print(f"Num Edges: {data.num_edges}")
    print(f"Node Features Shape: {data.x.shape}")
    print(f"Edge Index Shape: {data.edge_index.shape}")
    print(f"Labels Shape: {data.y.shape}")
