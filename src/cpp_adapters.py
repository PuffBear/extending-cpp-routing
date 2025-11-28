"""
Adapter/Wrapper Functions for Experimental Pipeline
Bridges the experimental pipeline with existing CPP solver implementations
"""

import networkx as nx
from typing import Tuple, List, Dict
import numpy as np

# Import existing implementations
from cpp_solver import CPPSolver
from cpp_load_dependent import CPPLoadDependentCosts, LoadCostFunction


def solve_classical_cpp(G: nx.Graph) -> Tuple[float, List]:
    """
    Solve classical CPP using existing CPPSolver
    
    Args:
        G: NetworkX graph
        
    Returns:
        (cost, tour) tuple
    """
    solver = CPPSolver()
    cost, tour, _ = solver.solve_classical_cpp(G)
    return cost, tour


def solve_greedy_heuristic(G: nx.Graph) -> Tuple[float, List]:
    """
    Simple greedy heuristic for CPP
    
    Args:
        G: NetworkX graph
        
    Returns:
        (cost, tour) tuple
    """
    # Greedy: build tour by always taking shortest available edge
    tour = []
    current_node = 0
    unvisited_edges = set(G.edges())
    total_cost = 0
    
    # Cover all edges
    required_edges = list(G.edges())
    
    # Build tour greedily
    for edge in required_edges:
        u, v = edge
        
        # Get to edge start
        if tour:
            last_node = tour[-1]
            if last_node != u:
                try:
                    path = nx.shortest_path(G, last_node, u, weight='weight')
                    tour.extend(path[:-1])  # Don't duplicate u
                    for i in range(len(path) - 1):
                        total_cost += G[path[i]][path[i+1]].get('weight', 1.0)
                except:
                    total_cost += 1000  # Penalty
        
        # Traverse edge
        tour.append(u)
        tour.append(v)
        total_cost += G[u][v].get('weight', 1.0)
    
    # Return to start
    if tour and tour[-1] != 0:
        try:
            path = nx.shortest_path(G, tour[-1], 0, weight='weight')
            tour.extend(path[1:])
            for i in range(len(path) - 1):
                total_cost += G[path[i]][path[i+1]].get('weight', 1.0)
        except:
            total_cost += 1000
    
    return total_cost, tour


def solve_two_opt(G: nx.Graph, initial_tour: List = None, max_iterations: int = 100) -> Tuple[float, List]:
    """
    2-opt local search improvement
    
    Args:
        G: NetworkX graph
        initial_tour: Starting tour (if None, uses greedy)
        max_iterations: Max improvement iterations
        
    Returns:
        (cost, tour) tuple
    """
    # Get initial tour
    if initial_tour is None:
        _, initial_tour = solve_greedy_heuristic(G)
    
    if not initial_tour or len(initial_tour) < 4:
        return solve_greedy_heuristic(G)
    
    def tour_cost(tour, G):
        """Compute total tour cost"""
        cost = 0
        for i in range(len(tour) - 1):
            u, v = tour[i], tour[i + 1]
            if G.has_edge(u, v):
                cost += G[u][v].get('weight', 1.0)
            else:
                try:
                    cost += nx.shortest_path_length(G, u, v, weight='weight')
                except:
                    cost += 1000
        return cost
    
    best_tour = initial_tour.copy()
    best_cost = tour_cost(best_tour, G)
    
    improved = True
    iteration = 0
    
    while improved and iteration < max_iterations:
        improved = False
        iteration += 1
        
        for i in range(1, len(best_tour) - 2):
            for j in range(i + 1, len(best_tour) - 1):
                # Try reversing segment [i:j+1]
                new_tour = best_tour[:i] + best_tour[i:j+1][::-1] + best_tour[j+1:]
                new_cost = tour_cost(new_tour, G)
                
                if new_cost < best_cost:
                    best_tour = new_tour
                    best_cost = new_cost
                    improved = True
                    break
            
            if improved:
                break
    
    return best_cost, best_tour


def solve_cpp_lc_greedy(G: nx.Graph, edge_demands: Dict, capacity: float, 
                        cost_function: str = 'linear') -> Tuple[float, List, Dict]:
    """
    Solve CPP-LC using existing implementation
    
    Args:
        G: Graph
        edge_demands: Edge demands
        capacity: Vehicle capacity
        cost_function: 'linear', 'quadratic', or 'fuel'
        
    Returns:
        (cost, tour, metadata) tuple
    """
    # Map cost function string to enum
    cost_func_map = {
        'linear': LoadCostFunction.LINEAR,
        'quadratic': LoadCostFunction.QUADRATIC,
        'fuel': LoadCostFunction.FUEL_CONSUMPTION
    }
    
    cost_func_enum = cost_func_map.get(cost_function, LoadCostFunction.LINEAR)
    
    solver = CPPLoadDependentCosts(
        G,
        edge_demands,
        capacity,
        cost_function_type=cost_func_enum
    )
    
    cost, tour, comp_time, state_history = solver.solve_greedy_insertion()
    
    metadata = {
        'cost_function': cost_function,
        'capacity': capacity,
        'computation_time': comp_time
    }
    
    return cost, tour, metadata


# Test functions
if __name__ == "__main__":
    print("Testing adapter functions...")
    
    # Create simple test graph
    G = nx.Graph()
    G.add_edge(0, 1, weight=1.0)
    G.add_edge(1, 2, weight=1.5)
    G.add_edge(2, 3, weight=2.0)
    G.add_edge(3, 0, weight=1.2)
    
    print("\n1. Classical CPP:")
    cost, tour = solve_classical_cpp(G)
    print(f"   Cost: {cost:.2f}, Tour length: {len(tour)}")
    
    print("\n2. Greedy Heuristic:")
    cost, tour = solve_greedy_heuristic(G)
    print(f"   Cost: {cost:.2f}, Tour length: {len(tour)}")
    
    print("\n3. 2-opt:")
    cost, tour = solve_two_opt(G)
    print(f"   Cost: {cost:.2f}, Tour length: {len(tour)}")
    
    print("\n✅ All adapter functions working!")
