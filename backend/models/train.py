import os
import sys
import torch
import torch.nn as nn
import torch.optim as optim

# Add backend directory to sys.path to allow imports when running script directly
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from models.gnn import instantiate_model
from models.dataset import load_mumbai_data

def train_maas_gnn():
    print("--- MaaS GNN Training Pipeline ---")
    
    # 1. Load Data
    json_path = os.path.join(backend_dir, 'mumbai_network.json')
    json_path = os.path.abspath(json_path)
    print(f"Loading generated dataset from: {json_path}")
    
    try:
        data = load_mumbai_data(json_path)
        print("Data loaded and formatted into PyTorch Geometric format.")
    except FileNotFoundError:
        print(f"Error: {json_path} not found.")
        print("Please run `python backend/fetch_mumbai_data.py` first to generate the raw dataset.")
        return

    # 2. Instantiate Model
    print("Instantiating MaaSGraphNetwork model...")
    model = instantiate_model()
    model.train() # Set to training mode (enables dropout)
    
    # 3. Define Loss Function & Optimizer
    # We use Mean Squared Error for regression on our 3 target features 
    criterion = nn.MSELoss()
    
    # Adam optimizer is standard for GNNs
    optimizer = optim.Adam(model.parameters(), lr=0.01, weight_decay=5e-4)
    
    # 4. Training Loop
    epochs = 500
    print(f"\nStarting training loop for {epochs} epochs...")
    
    for epoch in range(1, epochs + 1):
        # Zero the gradients from the previous step
        optimizer.zero_grad()
        
        # Forward pass: predict outputs
        out = model(data)
        
        # Calculate loss against ground truth targets (data.y)
        loss = criterion(out, data.y)
        
        # Backward pass: compute gradients
        loss.backward()
        
        # Update weights
        optimizer.step()
        
        if epoch % 10 == 0:
            print(f"Epoch {epoch:03d}/{epochs:03d} | Loss: {loss.item():.4f}")
            
    print("\nTraining complete!")
    
    # Save the model state dictionary
    save_path = os.path.join(current_dir, 'maas_gnn_weights.pth')
    torch.save(model.state_dict(), save_path)
    print(f"Model parameters successfully saved to {save_path}")

if __name__ == "__main__":
    train_maas_gnn()
