from fastapi import APIRouter
from pydantic import BaseModel
import random
import json
import os
import torch
from models.gnn import instantiate_model
from simulation.engine import SuperaggregatorEngine

router = APIRouter()

# Instantiate the GNN globally for the router to use
gnn_model = instantiate_model()

weights_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'maas_gnn_weights.pth')
if os.path.exists(weights_path):
    try:
        # Load the optimized weights that were learned during the dataset training script
        gnn_model.load_state_dict(torch.load(weights_path, weights_only=True))
        gnn_model.eval() # Set to evaluation mode for inference efficiency
        print(f"Successfully loaded trained GNN parameters from: {weights_path}")
    except Exception as e:
        print(f"Failed to load trained weights. Using naive initialization instead. Error: {e}")
else:
    print(f"Notice: Trained weights not found at {weights_path}. GNN is using untreated random initialization parameters.")

class SimulationConfig(BaseModel):
    fleet_reduction_percentage: float = 90.0
    use_motorways: bool = True
    maas_tier_distribution: dict = {
        "platinum": 10,
        "gold": 20,
        "silver": 40,
        "economy": 30
    }
    eliminate_parking: bool = True

@router.get("/status")
def get_status():
    return {"status": "ok", "message": "GNN Mobility Simulation API is running."}

@router.post("/simulate/baseline")
def simulate_baseline(config: SimulationConfig):
    # Mocking a baseline simulation result
    return {
        "scenario": "Baseline (Privately Owned Vehicles)",
        "conflict_density": round(float(random.uniform(80, 100)), 2),
        "avg_travel_time_mins": round(float(random.uniform(45, 60)), 1),
        "fleet_utilization_pct": round(float(random.uniform(2, 5)), 1),
    }

@router.post("/simulate/ultra")
def simulate_ultra(config: SimulationConfig):
    # The true MaaS / ULTRA Bill simulation result invoking the GNN over the Mumbai graph
    try:
        engine = SuperaggregatorEngine("mumbai_network.json", config)
        results = engine.run_simulation_step(gnn_model)
        
        return {
            "scenario": "ULTRA (MaaS Movement)",
            "conflict_density": results["conflict_density"],
            "avg_travel_time_mins": results["avg_travel_time_mins"],
            "fleet_utilization_pct": results["fleet_utilization_pct"],
            "config_applied": config.dict()
        }
    except Exception as e:
        return {"error": str(e), "message": "GNN Engine failed to run."}

@router.get("/data/mumbai")
def get_mumbai_graph_data():
    # Return the generated mock mumbai dataset
    try:
        with open("mumbai_network.json", "r") as f:
            data = json.load(f)
            return data
    except Exception as e:
        return {"error": str(e), "message": "Failed to load mumbai_network.json. Did you run fetch_mumbai_data.py?"}
