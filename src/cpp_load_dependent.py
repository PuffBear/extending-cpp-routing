"""
CPP with Load-Dependent Costs (CPP-LC) - Proper Implementation
Matching Section 3.2 formulation from the paper
Based on Corberán et al. [5] work
"""

import networkx as nx
import numpy as np
from typing import List, Tuple, Dict, Optional, Callable
import time
from dataclasses import dataclass
from enum import Enum


class LoadCostFunction(Enum):
    """Different load-dependent cost function types"""
    LINEAR = "linear"
    QUADRATIC = "quadratic"
    PIECEWISE = "piecewise"
    FUEL_CONSUMPTION = "fuel"


@dataclass
class LoadState:
    """Current state during tour execution"""
    current_node: int
    current_load: float
    current_time: float
    visited_edges: List[Tuple[int, int]]
    total_cost: float


class CPPLoadDependentCosts:
    """
    CPP with Load-Dependent Costs Implementation
    
    Formulation (Section 3.2):
    minimize Σ c_e(L)  where L is load when traversing edge e
    
    subject to:
    - tour traverses each edge at least once
    - L ≤ Q throughout tour (capacity constraint)
    - L_after_e = L_before_e + q_e (load accumulation)
    """
    
    def __init__(self, 
                 G: nx.Graph,
                 edge_demands: Dict[Tuple, float],
                 capacity: float,
                 cost_function_type: LoadCostFunction = LoadCostFunction.LINEAR,
                 depot: int = 0):
        """
        Args:
            G: Base graph
            edge_demands: Demand collected at each edge
            capacity: Vehicle capacity Q
            cost_function_type: Type of load-dependent cost function
            depot: Depot node for vehicle
        """
        self.G = G
        self.edge_demands = edge_demands
        self.capacity = capacity
        self.depot = depot
        self.cost_function_type = cost_function_type
        
        # Initialize cost functions
        self._setup_cost_functions()
    
    def _setup_cost_functions(self):
        """Setup load-dependent cost functions c_e(L)"""
        
        if self.cost_function_type == LoadCostFunction.LINEAR:
            # c_e(L) = base_cost * (1 + α * L/Q)
            self.cost_function = lambda base_cost, load: base_cost * (1 + 0.5 * load / self.capacity)
        
        elif self.cost_function_type == LoadCostFunction.QUADRATIC:
            # c_e(L) = base_cost * (1 + α * (L/Q)^2)
            self.cost_function = lambda base_cost, load: base_cost * (1 + 0.8 * (load / self.capacity) ** 2)
        
        elif self.cost_function_type == LoadCostFunction.PIECEWISE:
            # Piecewise linear: different rates for different load ranges
            def piecewise_cost(base_cost, load):
                ratio = load / self.capacity
                if ratio < 0.33:
                    return base_cost * (1 + 0.2 * ratio)
                elif ratio < 0.67:
                    return base_cost * (1 + 0.5 * ratio)
                else:
                    return base_cost * (1 + 1.0 * ratio)
            self.cost_function = piecewise_cost
        
        elif self.cost_function_type == LoadCostFunction.FUEL_CONSUMPTION:
            # Realistic fuel consumption model
            def fuel_cost(base_cost, load):
                empty_weight = 50.0  # More realistic empty vehicle weight
                vehicle_load = empty_weight + load
                # Fuel ∝ total weight, moderate non-linearity
                return base_cost * (vehicle_load / empty_weight) ** 0.8
            self.cost_function = fuel_cost
    
    def check_capacity_feasibility(self) -> bool:
        """
        Definition 2 from paper: Check if instance is capacity-feasible
        Returns True if there exists a tour that never exceeds capacity
        """
        # Simple check: can we service all edges in one trip?
        total_demand = sum(self.edge_demands.values())
        
        if total_demand <= self.capacity:
            return True
        
        # Check if we can partition edges into feasible trips
        # This is a bin packing problem - use greedy heuristic
        edges_by_demand = sorted(
            self.edge_demands.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Try to fit into trips
        trips = []
        for edge, demand in edges_by_demand:
            # Try to add to existing trip
            placed = False
            for trip in trips:
                if sum(self.edge_demands[e] for e in trip) + demand <= self.capacity:
                    trip.append(edge)
                    placed = True
                    break
            
            if not placed:
                trips.append([edge])
        
        # Feasible if we can complete all trips
        return all(
            sum(self.edge_demands[e] for e in trip) <= self.capacity 
            for trip in trips
        )
    
    def compute_edge_cost(self, edge: Tuple[int, int], current_load: float) -> float:
        """
        Compute cost of traversing edge with current load
        Implements c_e(L) from formulation
        """
        base_cost = self.G[edge[0]][edge[1]].get('weight', 1.0)
        return self.cost_function(base_cost, current_load)
    
    def solve_greedy_insertion(self) -> Tuple[float, List, float, List[LoadState]]:
        """
        Greedy insertion heuristic for CPP-LC
        Build tour by inserting edges that minimize load-dependent cost
        
        Returns: (total_cost, tour, computation_time, state_history)
        """
        start_time = time.time()
        
        if not self.check_capacity_feasibility():
            print("Warning: Instance may require multiple trips")
        
        unserviced = set(self.edge_demands.keys())
        tour = []
        state_history = []
        
        # Initialize state
        state = LoadState(
            current_node=self.depot,
            current_load=0.0,
            current_time=0.0,
            visited_edges=[],
            total_cost=0.0
        )
        
        while unserviced:
            best_edge = None
            best_cost = float('inf')
            best_new_load = None
            
            for edge in unserviced:
                u, v = edge
                demand = self.edge_demands[edge]
                
                # Check if we can service this edge without exceeding capacity
                potential_load = state.current_load + demand
                
                if potential_load > self.capacity:
                    # Need to return to depot first
                    # Calculate cost of depot return + edge service
                    depot_cost = self._compute_travel_cost(
                        state.current_node, 
                        self.depot, 
                        state.current_load
                    )
                    travel_cost = self._compute_travel_cost(
                        self.depot,
                        u,
                        0.0  # Empty after depot return
                    )
                    edge_cost = self.compute_edge_cost(edge, demand)
                    total_insertion_cost = depot_cost + travel_cost + edge_cost
                    new_load = demand
                else:
                    # Can service without depot return
                    travel_cost = self._compute_travel_cost(
                        state.current_node,
                        u,
                        state.current_load
                    )
                    edge_cost = self.compute_edge_cost(edge, potential_load)
                    total_insertion_cost = travel_cost + edge_cost
                    new_load = potential_load
                
                if total_insertion_cost < best_cost:
                    best_cost = total_insertion_cost
                    best_edge = edge
                    best_new_load = new_load
            
            if best_edge is None:
                print("No feasible insertion found!")
                break
            
            # Execute best insertion
            u, v = best_edge
            
            # Check if depot return needed
            if best_new_load < state.current_load:
                # Returned to depot
                depot_cost = self._compute_travel_cost(
                    state.current_node,
                    self.depot,
                    state.current_load
                )
                state.total_cost += depot_cost
                tour.append(('depot_return', None))
                state.current_node = self.depot
                state.current_load = 0.0
            
            # Travel to edge
            travel_cost = self._compute_travel_cost(
                state.current_node,
                u,
                state.current_load
            )
            state.total_cost += travel_cost
            
            # Service edge
            edge_cost = self.compute_edge_cost(best_edge, best_new_load)
            state.total_cost += edge_cost
            state.current_load = best_new_load
            state.current_node = v
            tour.append(best_edge)
            
            unserviced.remove(best_edge)
            state_history.append(LoadState(
                current_node=state.current_node,
                current_load=state.current_load,
                current_time=state.current_time,
                visited_edges=list(tour),
                total_cost=state.total_cost
            ))
        
        # Return to depot
        if state.current_node != self.depot:
            return_cost = self._compute_travel_cost(
                state.current_node,
                self.depot,
                state.current_load
            )
            state.total_cost += return_cost
            tour.append(('depot_return', None))
        
        computation_time = time.time() - start_time
        
        return state.total_cost, tour, computation_time, state_history
    
    def _compute_travel_cost(self, from_node: int, to_node: int, load: float) -> float:
        """Compute cost of traveling between nodes with given load"""
        if from_node == to_node:
            return 0.0
        
        try:
            path_length = nx.shortest_path_length(
                self.G, from_node, to_node, weight='weight'
            )
            return self.cost_function(path_length, load)
        except nx.NetworkXNoPath:
            return float('inf')
    
    def solve_dynamic_programming(self, max_states: int = 10000) -> Tuple[float, List, float]:
        """
        Dynamic programming approach for smaller instances
        
        State: (current_node, remaining_edges, current_load)
        Too expensive for large instances due to state space explosion
        """
        start_time = time.time()
        
        # Only feasible for very small instances
        if len(self.edge_demands) > 10:
            print("Instance too large for DP, using greedy")
            return self.solve_greedy_insertion()[:3]
        
        from functools import lru_cache
        
        edges_tuple = tuple(sorted(self.edge_demands.keys()))
        
        @lru_cache(maxsize=max_states)
        def dp(node: int, remaining: frozenset, load: float) -> Tuple[float, List]:
            """
            DP function: minimum cost to service remaining edges
            starting from node with given load
            """
            if not remaining:
                # All edges serviced, return to depot
                return self._compute_travel_cost(node, self.depot, load), []
            
            best_cost = float('inf')
            best_tour = []
            
            for edge in remaining:
                u, v = edge
                demand = self.edge_demands[edge]
                new_remaining = remaining - {edge}
                
                # Option 1: Service edge directly
                if load + demand <= self.capacity:
                    travel = self._compute_travel_cost(node, u, load)
                    edge_cost = self.compute_edge_cost(edge, load + demand)
                    future_cost, future_tour = dp(v, new_remaining, load + demand)
                    
                    total = travel + edge_cost + future_cost
                    if total < best_cost:
                        best_cost = total
                        best_tour = [edge] + future_tour
                
                # Option 2: Return to depot first
                depot_return = self._compute_travel_cost(node, self.depot, load)
                travel = self._compute_travel_cost(self.depot, u, 0)
                edge_cost = self.compute_edge_cost(edge, demand)
                future_cost, future_tour = dp(v, new_remaining, demand)
                
                total = depot_return + travel + edge_cost + future_cost
                if total < best_cost:
                    best_cost = total
                    best_tour = [('depot_return', None), edge] + future_tour
            
            return best_cost, best_tour
        
        remaining_edges = frozenset(self.edge_demands.keys())
        cost, tour = dp(self.depot, remaining_edges, 0.0)
        
        computation_time = time.time() - start_time
        
        return cost, tour, computation_time
    
    def compare_with_classical_cpp(self) -> Dict[str, float]:
        """
        Compare load-dependent costs with classical CPP
        Shows the cost increase due to load dependency
        """
        # Classical CPP cost (no load dependency)
        classical_cost = sum(
            self.G[u][v].get('weight', 1.0)
            for u, v in self.edge_demands.keys()
        )
        
        # Add augmentation for odd vertices
        odd_vertices = [v for v in self.G.nodes() if self.G.degree(v) % 2 == 1]
        if odd_vertices:
            # Rough estimate of matching cost
            classical_cost *= 1.2
        
        # CPP-LC cost
        lc_cost, _, _, _ = self.solve_greedy_insertion()
        
        return {
            'classical_cost': classical_cost,
            'cpp_lc_cost': lc_cost,
            'cost_increase_ratio': lc_cost / classical_cost,
            'cost_increase_percent': (lc_cost - classical_cost) / classical_cost * 100
        }


# Testing and validation
if __name__ == "__main__":
    print("CPP with Load-Dependent Costs - Testing")
    print("=" * 60)
    
    # Create test graph
    G = nx.grid_2d_graph(4, 4)
    G = nx.convert_node_labels_to_integers(G)
    
    for u, v in G.edges():
        G[u][v]['weight'] = np.random.uniform(5, 15)
    
    # Generate demands
    edge_demands = {}
    for u, v in G.edges():
        edge_demands[(u, v)] = np.random.uniform(5, 20)
    
    total_demand = sum(edge_demands.values())
    capacity = total_demand * 0.4  # Tight capacity
    
    print(f"\nInstance properties:")
    print(f"  Nodes: {G.number_of_nodes()}")
    print(f"  Edges: {G.number_of_edges()}")
    print(f"  Total demand: {total_demand:.2f}")
    print(f"  Vehicle capacity: {capacity:.2f}")
    print(f"  Capacity ratio: {capacity/total_demand:.2%}")
    
    # Test different cost functions
    cost_functions = [
        LoadCostFunction.LINEAR,
        LoadCostFunction.QUADRATIC,
        LoadCostFunction.PIECEWISE,
        LoadCostFunction.FUEL_CONSUMPTION
    ]
    
    print("\n" + "=" * 60)
    print("TESTING DIFFERENT COST FUNCTIONS")
    print("=" * 60)
    
    results = {}
    
    for cost_type in cost_functions:
        print(f"\n{cost_type.value.upper()} cost function:")
        print("-" * 40)
        
        solver = CPPLoadDependentCosts(
            G, edge_demands, capacity, cost_type
        )
        
        # Check feasibility
        is_feasible = solver.check_capacity_feasibility()
        print(f"  Capacity feasible: {is_feasible}")
        
        # Solve
        cost, tour, comp_time, state_history = solver.solve_greedy_insertion()
        
        # Count depot returns
        depot_returns = sum(1 for edge in tour if edge[0] == 'depot_return')
        
        print(f"  Total cost: {cost:.2f}")
        print(f"  Tour length: {len(tour)} steps")
        print(f"  Depot returns: {depot_returns}")
        print(f"  Computation time: {comp_time:.4f}s")
        
        # Show load evolution
        if state_history:
            max_load = max(s.current_load for s in state_history)
            avg_load = np.mean([s.current_load for s in state_history])
            print(f"  Max load: {max_load:.2f} ({max_load/capacity:.1%} of capacity)")
            print(f"  Avg load: {avg_load:.2f} ({avg_load/capacity:.1%} of capacity)")
        
        # Compare with classical
        comparison = solver.compare_with_classical_cpp()
        print(f"\n  Comparison with Classical CPP:")
        print(f"    Classical cost: {comparison['classical_cost']:.2f}")
        print(f"    CPP-LC cost: {comparison['cpp_lc_cost']:.2f}")
        print(f"    Increase: {comparison['cost_increase_percent']:.1f}%")
        
        results[cost_type.value] = {
            'cost': cost,
            'time': comp_time,
            'depot_returns': depot_returns,
            'comparison': comparison
        }
    
    # Summary comparison
    print("\n" + "=" * 60)
    print("SUMMARY: Cost Function Comparison")
    print("=" * 60)
    print(f"{'Cost Function':<20} {'Total Cost':<15} {'vs Classical':<15} {'Time (s)':<10}")
    print("-" * 60)
    
    for cost_type, result in results.items():
        print(f"{cost_type:<20} {result['cost']:<15.2f} "
              f"+{result['comparison']['cost_increase_percent']:<14.1f}% "
              f"{result['time']:<10.4f}")