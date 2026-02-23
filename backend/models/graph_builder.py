import networkx as nx
import random

def build_mumbai_baseline_graph(num_nodes=500):
    """
    Builds a standard, mixed-traffic baseline graph for Mumbai.
    All edges represent standard roads where private vehicles and public transport mix.
    """
    G = nx.erdos_renyi_graph(num_nodes, p=0.02)
    
    # Assign baseline attributes
    for u, v in G.edges():
        G[u][v]['type'] = 'mixed'
        G[u][v]['speed_limit'] = random.choice([30, 50, 60])  # kmph
        G[u][v]['capacity'] = random.randint(100, 500)       # vehicles per hour
    
    for i in G.nodes():
        G.nodes[i]['parking_spots'] = random.randint(50, 300)
    
    return G

def build_ultra_bifurcated_graph(num_nodes=500):
    """
    Builds the ULTRA graph representing Functional Separation.
    Separates graph into Motorways (high capacity, high speed, 4+ wheelers)
    and Micromobility Zones (low speed, small EVs).
    """
    G = nx.erdos_renyi_graph(num_nodes, p=0.02)
    
    for u, v in G.edges():
        # 10% of edges are turned into dedicated Motorways
        if random.random() < 0.1:
            G[u][v]['type'] = 'motorway'
            G[u][v]['speed_limit'] = 100  # Assured travel speed
            G[u][v]['capacity'] = random.randint(1000, 2500) 
        else:
            G[u][v]['type'] = 'micromobility'
            G[u][v]['speed_limit'] = 30  # max 30 kmph
            G[u][v]['capacity'] = random.randint(200, 600)
            
    # Parking eliminated, replaced by Mobility Hubs
    for i in G.nodes():
        G.nodes[i]['parking_spots'] = 0
        G.nodes[i]['has_micromobility_station'] = True if random.random() < 0.5 else False
        G.nodes[i]['has_motorway_hub'] = True if random.random() < 0.05 else False
        
    return G
