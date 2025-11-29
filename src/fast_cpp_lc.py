"""
FAST CPP-LC Implementation with Documented Assumptions
Simplified for speed while maintaining core concepts
"""

import networkx as nx
import numpy as np
from typing import Dict, Tuple, List
from enum import Enum


class SimplifiedCPPLC:
    """
    Fast CPP-LC solver with simplifying assumptions
    
    ASSUMPTIONS (documented for paper):
    1. Single-vehicle routing (no fleet optimization)
    2. Greedy edge selection (no optimal reordering)
    3. Linear load-dependent cost function only
    4. Capacity feasibility pre-checked (assumes feasible)
    5. No dynamic programming (exponential complexity)
    
    These assumptions allow O(E²) complexity instead of NP-hard exact solution
    """
    
    def __init__(self, G: nx.Graph, edge_demands: Dict, capacity: float):
        self.G = G
        self.edge_demands = edge_demands
        self.capacity = capacity
        
    def solve_fast(self) -> Tuple[float, List, Dict]:
        """
        ULTRA-FAST greedy solution for CPP-LC
        Pre-computes all shortest paths to avoid repeated calls
        
        Returns:
            (total_cost, tour, metadata)
        """
        
        # PRE-COMPUTE all shortest paths (one-time cost)
        try:
            all_paths = dict(nx.all_pairs_dijkstra_path_length(self.G, weight='weight'))
        except:
            # Fallback for disconnected graphs
            all_paths = {}
            for u in self.G.nodes():
                all_paths[u] = {}
                for v in self.G.nodes():
                    if u == v:
                        all_paths[u][v] = 0
                    elif self.G.has_edge(u, v):
                        all_paths[u][v] = self.G[u][v].get('weight', 1.0)
                    else:
                        all_paths[u][v] = 1000  # Large penalty
        
        # Required edges
        required_edges = set(self.G.edges())
        visited = set()
        
        tour = [0]
        current_node = 0
        current_load = 0.0
        total_cost = 0.0
        trips = 0
        
        max_iterations = len(required_edges) * 2  # Safety limit
        iteration = 0
        
        while len(visited) < len(required_edges) and iteration < max_iterations:
            iteration += 1
            
            # Find nearest unvisited edge (using pre-computed distances)
            best_edge = None
            best_cost = float('inf')
            
            for edge in required_edges:
                if edge in visited or (edge[1], edge[0]) in visited:
                    continue
                
                u, v = edge
                demand = self.edge_demands.get(edge, self.edge_demands.get((v, u), 1.0))
                
                # Cost to reach edge (using pre-computed)
                if current_node == u:
                    reach_cost = 0
                    start, end = u, v
                elif current_node == v:
                    reach_cost = 0
                    start, end = v, u
                else:
                    # Use pre-computed shortest paths
                    dist_u = all_paths.get(current_node, {}).get(u, 1000)
                    dist_v = all_paths.get(current_node, {}).get(v, 1000)
                    
                    if dist_u < dist_v:
                        reach_cost = dist_u
                        start, end = u, v
                    else:
                        reach_cost = dist_v
                        start, end = v, u
                
                # Penalty if need depot return
                if current_load + demand > self.capacity:
                    reach_cost += 50
                
                if reach_cost < best_cost:
                    best_cost = reach_cost
                    best_edge = (start, end, demand)
            
            if best_edge is None:
                break
            
            start, end, demand = best_edge
            
            # Return to depot if needed
            if current_load + demand > self.capacity:
                depot_dist = all_paths.get(current_node, {}).get(0, 0)
                load_factor = 1 + 0.5 * current_load / self.capacity
                total_cost += depot_dist * load_factor
                
                current_node = 0
                current_load = 0
                tour.append(0)
                trips += 1
            
            # Travel to edge start
            if current_node != start:
                travel_dist = all_paths.get(current_node, {}).get(start, 0)
                load_factor = 1 + 0.5 * current_load / self.capacity
                total_cost += travel_dist * load_factor
                current_node = start
                tour.append(start)
            
            # Traverse edge
            edge_weight = self.G[start][end].get('weight', 1.0)
            load_factor = 1 + 1.0 * current_load / self.capacity
            edge_cost = edge_weight * load_factor
            
            total_cost += edge_cost
            current_load += demand
            current_node = end
            tour.append(end)
            
            visited.add((start, end))
            visited.add((end, start))
        
        # Return to depot
        if current_node != 0:
            depot_dist = all_paths.get(current_node, {}).get(0, 0)
            load_factor = 1 + 0.5 * current_load / self.capacity
            total_cost += depot_dist * load_factor
            tour.append(0)
        
        metadata = {
            'method': 'ultra_fast_greedy',
            'assumptions': [
                'Pre-computed shortest paths',
                'Linear load-dependent costs',
                'Greedy nearest edge selection',
                'Single vehicle'
            ],
            'complexity': 'O(E² + V² log V)',
            'trips_to_depot': trips,
            'edges_serviced': len(visited) // 2,
            'iterations': iteration
        }
        
        return total_cost, tour, metadata


def test_fast_cpp_lc():
    """Test fast CPP-LC"""
    
    # Simple test graph
    G = nx.Graph()
    G.add_edge(0, 1, weight=1.0)
    G.add_edge(1, 2, weight=1.5)
    G.add_edge(2, 3, weight=2.0)
    G.add_edge(3, 0, weight=1.2)
    
    edge_demands = {
        (0, 1): 5.0,
        (1, 2): 7.0,
        (2, 3): 6.0,
        (3, 0): 4.0
    }
    
    capacity = 12.0  # Tight capacity
    
    solver = SimplifiedCPPLC(G, edge_demands, capacity)
    cost, tour, meta = solver.solve_fast()
    
    print(f"Cost: {cost:.2f}")
    print(f"Tour length: {len(tour)}")
    print(f"Metadata: {meta}")
    
    return cost, tour, meta


if __name__ == "__main__":
    print("Testing Fast CPP-LC...")
    test_fast_cpp_lc()
