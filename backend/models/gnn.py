import torch
import torch.nn.functional as F
from torch_geometric.nn import GATConv, SAGEConv, GraphNorm
from torch_geometric.data import Data

class MaaSGraphNetwork(torch.nn.Module):
    """
    Advanced Graph Neural Network for the ULTRA Bill Simulation.
    
    This model mathematically models the transition from Privately Owned Vehicles
    (POV) to a centralized, Superaggregator-controlled MaaS fleet.
    
    Key Mathematical Mechanisms:
    1. Spatial Dependency Capture: GraphSAGE for aggregating neighborhood congestion.
    2. Dynamic Routing Prioritization: Graph Attention Network (GAT) to model
       Superaggregator logic. Edge attention weights simulate subscription tier priorities
       and Motorway vs Micromobility speed differentials.
    """
    def __init__(self, in_channels, hidden_channels, out_channels):
        super(MaaSGraphNetwork, self).__init__()
        
        # SAGEConv is excellent for inductive learning on large city graphs
        # It aggregates features from neighboring nodes (simulating traffic spillover)
        self.sage1 = SAGEConv(in_channels, hidden_channels)
        self.norm1 = GraphNorm(hidden_channels)
        
        # GATConv uses attention mechanisms to weigh incoming edges.
        # This is where the mathematical model of the "Superaggregator" lives.
        # Edge weights can be biased by subscription tier (Platinum/Gold) 
        # and physical infrastructure (Motorway vs Micromobility).
        self.gat1 = GATConv(hidden_channels, hidden_channels, heads=4, concat=True, edge_dim=2)
        self.norm2 = GraphNorm(hidden_channels * 4)
        
        # Final projection to outputs
        # Output 0: Predicted Traffic Flow (normalized 0-1)
        # Output 1: Optimal ETA (normalized 0-1, to be scaled by max_eta)
        # Output 2: Fleet Allocation Score (higher score = more MaaS vehicles routed here)
        self.out_proj = torch.nn.Linear(hidden_channels * 4, out_channels)

    def forward(self, data: Data):
        """
        Forward Pass.
        
        Args:
            data.x: Node features [num_nodes, in_channels]
                    Current structure: [population_density, traffic_volume, speed_limit, is_motorway, pending_requests]
            data.edge_index: Graph connectivity [2, num_edges]
            data.edge_attr: Edge features [num_edges, 2]
                    Current structure: [edge_length, max_speed]
        """
        x, edge_index, edge_attr = data.x, data.edge_index, data.edge_attr

        # 1. Neighborhood Aggregation (Simulating Traffic Spreading)
        x = self.sage1(x, edge_index)
        x = self.norm1(x)
        x = F.elu(x) # ELU preserves slight negative values, useful for normalization states
        x = F.dropout(x, p=0.1, training=self.training)
        
        # 2. Attention-based Superaggregator Allocation
        # The attention heads will learn which paths to prioritize based on the edge attributes
        # (e.g., heavily weighting Motorway edges if the user distribution has high Platinum tier)
        x = self.gat1(x, edge_index, edge_attr=edge_attr)
        x = self.norm2(x)
        x = F.elu(x)
        
        # 3. Final Prediction
        out = self.out_proj(x)
        
        # ReLU prevents negative outputs while allowing for the >1.0 target predictions
        return F.relu(out)

    def calculate_fleet_reduction_impact(self, graph_data: Data, reduction_pct: float) -> float:
        """
        Custom PyTorch utility function to evaluate the mathematical impact
        of the "Abolition of PVO" hypothesis.
        """
        with torch.no_grad():
            self.eval()
            predictions = self.forward(graph_data)
            base_efficiency = predictions[:, 2].mean().item() # Mean Fleet Allocation Score
            
            # Simulated mathematical relationship:
            # Under a unified Superaggregator, routing efficiency scales logarithmically
            # with the reduction of private vehicle noise, until diminishing returns.
            efficiency_gain = torch.log(torch.tensor(reduction_pct + 1.0)) * 0.5
            
            return min(base_efficiency * (1.0 + efficiency_gain.item()), 1.0)
            
def instantiate_model():
    # 5 Node Features: [population_density, traffic_volume, base_speed, is_motorway, pending_requests]
    # 3 Output Features: [Predicted Flow, Optimal ETA, Fleet Allocation Score]
    model = MaaSGraphNetwork(in_channels=5, hidden_channels=32, out_channels=3)
    return model
