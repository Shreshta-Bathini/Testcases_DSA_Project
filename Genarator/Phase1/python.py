import json
import random
import argparse
import math
import os

# --- Constants for Graph Generation ---
ROAD_TYPES = ["primary", "secondary", "tertiary", "local", "expressway"]
POIS = ["restaurant", "hospital", "pharmacy", "hotel", "atm", "petrol station"]
# -------------------------------------

# -----------------------------------
# GRAPH GENERATOR (Your original function)
# -----------------------------------
def generate_graph(num_nodes, num_edges):
    """
    Creates a valid, randomly connected graph structure with required node 
    and edge attributes (lat, lon, length, speed_profile, etc.).
    """
    nodes = []
    for i in range(num_nodes):
        # Generate coordinates within a small, localized area (e.g., Mumbai)
        lat = 19.0 + random.random() * 0.2
        lon = 72.8 + random.random() * 0.2
        # Assign 0 to 2 random POIs to the node
        pois = random.sample(POIS, random.randint(0, 2))
        nodes.append({
            "id": i,
            "lat": lat,
            "lon": lon,
            "pois": pois
        })

    edges = []
    edge_set = set()
    while len(edges) < num_edges:
        # Select two distinct nodes
        u, v = random.sample(range(num_nodes), 2)
        if u == v or (u, v) in edge_set or (v, u) in edge_set:
            continue
        edge_set.add((u, v))

        # Generate realistic-looking edge attributes
        length = round(random.uniform(50, 500), 2)  # Distance in meters
        avg_time = round(length / random.uniform(5, 25), 2) # A simple average time
        # 96 entries for 15-minute intervals (24 hours * 4)
        speed_profile = [round(random.uniform(20, 60), 2) for _ in range(96)]

        edges.append({
            "id": 1000 + len(edges),
            "u": u,
            "v": v,
            "length": length,
            "average_time": avg_time,
            "speed_profile": speed_profile,
            "oneway": random.choice([True, False]),
            "road_type": random.choice(ROAD_TYPES)
        })

    return {
        "meta": {
            "id": "autogen_graph",
            "nodes": num_nodes,
            "description": "Auto-generated graph for full system test"
        },
        "nodes": nodes,
        "edges": edges
    }

# -----------------------------------
# QUERY GENERATOR (Modified to handle missing 'patch')
# -----------------------------------

def generate_queries(graph_data, num_events):
    """Generates a list of random query/update events."""
    
    events = []
    event_id = 1
    
    # Extract IDs and relevant data
    node_ids = [node["id"] for node in graph_data["nodes"]]
    edge_ids = [edge["id"] for edge in graph_data["edges"]]
    all_nodes = graph_data["nodes"]
    
    for _ in range(num_events):
        # Weighted random choice of event type
        event_type = random.choices(
            ["shortest_path", "knn", "modify_edge", "remove_edge"],
            weights=[40, 30, 20, 10],  
            k=1
        )[0]
        
        event = {"id": event_id}
        
        if event_type == "shortest_path":
            # --- Shortest Path Query ---
            event["type"] = "shortest_path"
            event["source"] = random.choice(node_ids)
            event["target"] = random.choice(node_ids)
            event["mode"] = random.choice(["distance", "time"])
            
            # Constraints (optional)
            if random.random() < 0.6: 
                cons = {}
                if random.random() < 0.5 and len(node_ids) > 5:
                    cons["forbidden_nodes"] = random.sample(node_ids, random.randint(1, min(5, len(node_ids) // 5)))
                if random.random() < 0.5:
                    cons["forbidden_road_types"] = random.sample(ROAD_TYPES, random.randint(1, 2))
                
                if cons:
                    event["constraints"] = cons

        elif event_type == "knn":
            # --- KNN Query (Shortest Path Distance) ---
            event["type"] = "knn"
            event["k"] = random.randint(3, 10)
            
            # Ensure a meaningful POI is chosen
            valid_pois = [p for node in all_nodes for p in node["pois"]]
            event["poi"] = random.choice(valid_pois) if valid_pois else random.choice(POIS)
            
            # Generate a query point near a random existing node 
            ref_node = random.choice(all_nodes)
            event["query_point"] = {
                "lat": round(ref_node["lat"] + random.uniform(-0.005, 0.005), 6),
                "lon": round(ref_node["lon"] + random.uniform(-0.005, 0.005), 6)
            }
            event["metric"] = "shortest_path" 

        elif event_type == "modify_edge":
            # --- Modify Edge Update ---
            event["type"] = "modify_edge"
            event["edge_id"] = random.choice(edge_ids)
            
            # MODIFICATION: Randomly skip adding the "patch" key (20% chance)
            if random.random() >= 0.2: 
                # 80% chance to generate a patch
                patch = {}
                patch_type = random.choice(["length", "speed_profile", "road_type"])
                
                if patch_type == "length":
                    patch["length"] = round(random.uniform(50, 500), 2)
                elif patch_type == "speed_profile":
                    # Update just one time bin or the whole profile
                    if random.random() < 0.3:
                        patch["speed_profile"] = [round(random.uniform(20, 60), 2) for _ in range(96)]
                    else:
                        # Test partial updates if your system supports it, otherwise update the whole array
                        patch["speed_profile"] = [round(random.uniform(20, 60), 2) for _ in range(96)] 

                elif patch_type == "road_type":
                    patch["road_type"] = random.choice(ROAD_TYPES)
                
                event["patch"] = patch
            # If the random check fails (20% of the time), the "patch" field is omitted.
                
        elif event_type == "remove_edge":
            # --- Remove Edge Update ---
            event["type"] = "remove_edge"
            event["edge_id"] = random.choice(edge_ids)
            
        events.append(event)
        event_id += 1
        
    return events


# -----------------------------------
# MAIN EXECUTION
# -----------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate graph and a set of test queries for Phase 1.")
    parser.add_argument("--nodes", type=int, default=100, help="Number of nodes in the graph.")
    parser.add_argument("--edges", type=int, default=200, help="Number of edges in the graph.")
    parser.add_argument("--events", type=int, default=50, help="Number of query/update events to generate.")
    parser.add_argument("--graph_file", type=str, default="graph.json", help="Output file for the generated graph.")
    parser.add_argument("--queries_file", type=str, default="queries.json", help="Output file for the generated queries.")
    
    args = parser.parse_args()

    # 1. Generate Graph Data
    print(f"Generating graph with {args.nodes} nodes and {args.edges} edges...")
    graph_data = generate_graph(args.nodes, args.edges)
    
    # Save Graph
    with open(args.graph_file, 'w') as f:
        json.dump(graph_data, f, indent=4)
    print(f"Graph saved to {args.graph_file}")
    
    # 2. Generate Query Data
    print(f"Generating {args.events} query/update events...")
    events = generate_queries(graph_data, args.events)
    
    query_set = {
        "meta": {"id": "test_qset_1"},
        "events": events
    }
    
    # Save Queries
    with open(args.queries_file, 'w') as f:
        json.dump(query_set, f, indent=4)
    print(f"Queries saved to {args.queries_file}")
