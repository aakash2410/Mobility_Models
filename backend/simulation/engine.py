import torch
from torch_geometric.data import Data
import json
import random

class SuperaggregatorEngine:
    def __init__(self, json_graph_path, config):
        """
        Initializes the Simulation Engine for the MaaS Movement Superaggregator.
        Reads the physical/mock JSON graph and converts it to a PyTorch Geometric Data object.
        """
        self.config = config
        self.pyg_data = self._load_and_convert_graph(json_graph_path)
        
    def _load_and_convert_graph(self, filepath):
        with open(filepath, 'r') as f:
            raw_data = json.load(f)
            
        nodes = raw_data['nodes']
        edges = raw_data['edges']
        
        # --- Node Features ---
        # 0: population_density (structural demand)
        # 1: traffic volume (stochastic start)
        # 2: base speed limit (assume 30 for micromobility zones, up to 100 for motorways)
        # 3: is_motorway_hub (boolean 0/1)
        # 4: pending_requests (stochastic start tied to density)
        x = []
        reduction_factor = (100.0 - self.config.fleet_reduction_percentage) / 100.0
        
        for node in nodes:
            pop_density = node.get("population_density", 0.5)
            
            # Fleet reduction logically removes POV congestion from the network.
            # 0% reduction = massive traffic limits constraints. 90% = highly controlled sparse transit pods.
            base_traffic = random.uniform(0.7, 1.0)
            traffic = base_traffic * pop_density * max(0.05, reduction_factor)
            
            # If motorway separation is active, randomly designate hubs. Normalize speeds to 0-1 for GNN.
            is_hub = 1.0 if (self.config.use_motorways and random.random() < 0.1) else 0.0
            speed = 1.0 if is_hub else 0.3
            
            # Demand remains structural regardless of fleet size
            requests = random.uniform(1.0, 5.0) * pop_density
            
            x.append([pop_density, traffic, speed, is_hub, requests])
            
        x_tensor = torch.tensor(x, dtype=torch.float)
        
        # --- Edge Indices & Features ---
        edge_indices = []
        edge_attrs = []
        
        for edge in edges:
            source = edge['source']
            target = edge['target']
            edge_indices.append([source, target])
            # Bidirectional for undirected physical roads
            edge_indices.append([target, source])
            
            # Features: length, max_speed constraint normalized to 0-1 mapping
            length = float(edge.get('length', 100))
            is_motorway_edge = 1.0 if (self.config.use_motorways and random.random() < 0.15) else 0.0
            m_speed = 1.0 if is_motorway_edge else 0.3
            
            edge_attrs.append([length, m_speed])
            edge_attrs.append([length, m_speed]) # Match bidirectional
            
        edge_index_tensor = torch.tensor(edge_indices, dtype=torch.long).t().contiguous()
        edge_attr_tensor = torch.tensor(edge_attrs, dtype=torch.float)
        
        # Construct PyG Data object
        data = Data(x=x_tensor, edge_index=edge_index_tensor, edge_attr=edge_attr_tensor)
        return data

    def run_simulation_step(self, gnn_model):
        """
        Runs one forward pass of the GNN over the current graph state.
        Returns the overall efficiency and conflict metrics.
        """
        # Pass graph to PyG model
        fleet_efficiency = gnn_model.calculate_fleet_reduction_impact(
            self.pyg_data, 
            reduction_pct=self.config.fleet_reduction_percentage / 100.0
        )
        
        # Extract general predictions for UI
        with torch.no_grad():
            preds = gnn_model(self.pyg_data)
            base_flow = preds[:, 0].mean().item()
            base_eta = preds[:, 1].mean().item()
            
            # The GNN computes the structural baseline constraints based on Mumbai's dense topology.
            # We scale the actual physical traffic conflict linearly as POV vehicles are abolished.
            reduction_factor = max(0.05, (100.0 - self.config.fleet_reduction_percentage) / 100.0)
            
            # Dedicated motorways drastically lower interaction conflict
            motorway_multiplier = 0.7 if self.config.use_motorways else 1.3
            
            # 0% reduction = 80-100% Conflict. 90% reduction + Motorways = ~5% Conflict
            avg_flow = (base_flow * 2.0) * reduction_factor * motorway_multiplier
            
            # Travel time drops significantly but has a structural physical floor (cannot teleport)
            avg_eta_normalized = base_eta * max(0.3, reduction_factor * motorway_multiplier)
            
        return {
            "fleet_utilization_pct": round(fleet_efficiency * 100, 1),
            "conflict_density": round(min(avg_flow * 100, 100.0), 2), 
            "avg_travel_time_mins": round(avg_eta_normalized * 100, 1) # scaling normalized output
        }
