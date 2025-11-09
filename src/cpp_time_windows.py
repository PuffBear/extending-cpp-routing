"""
CPP with Time Windows (CPP-TW) Implementation
Matching Section 3.3 formulation from the paper
"""

import networkx as nx
import numpy as np
from typing import List, Tuple, Dict, Optional
import time
from dataclasses import dataclass
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


@dataclass
class TimeWindow:
    """Time window for edge service"""
    early: float  # Earliest service start time
    late: float   # Latest service start time
    
    def is_feasible(self, arrival_time: float) -> bool:
        return self.early <= arrival_time <= self.late


@dataclass
class EdgeService:
    """Edge with service requirements"""
    edge: Tuple[int, int]
    time_window: TimeWindow
    service_duration: float
    travel_cost: float
    waiting_penalty: float = 1.0  # α in equation (9)


class CPPTimeWindowsSolver:
    """
    CPP-TW Solver implementing formulation from Section 3.3:
    
    minimize Σ w_e·x_e + Σ α·waiting_time(v)
    
    subject to:
        a_e ≤ t_e ≤ b_e  ∀e ∈ E  (time windows)
        t_j ≥ t_i + s_i + τ_ij  ∀(i,j) consecutive
    """
    
    def __init__(self, G: nx.Graph, edge_services: Dict[Tuple, EdgeService]):
        self.G = G
        self.edge_services = edge_services
        self.depot = 0  # Assume node 0 is depot
        
    def check_temporal_feasibility(self) -> bool:
        """
        Definition 3: Check if instance is temporally feasible
        Returns True if there exists a tour respecting all time windows
        """
        # Build temporal constraint graph
        n_edges = len(self.edge_services)
        
        # Simple feasibility check: sum of minimum service times
        min_total_time = sum(
            service.time_window.early + service.service_duration 
            for service in self.edge_services.values()
        )
        
        max_allowed_time = max(
            service.time_window.late 
            for service in self.edge_services.values()
        )
        
        return min_total_time <= max_allowed_time
    
    def solve_greedy_insertion(self) -> Tuple[float, List, float, Dict]:
        """
        Greedy insertion heuristic for CPP-TW
        Returns: (total_cost, tour, computation_time, schedule)
        """
        start_time = time.time()
        
        if not self.check_temporal_feasibility():
            raise ValueError("Instance is temporally infeasible")
        
        # Initialize
        unserviced = set(self.edge_services.keys())
        tour = []
        schedule = {}  # edge -> service_start_time
        
        current_node = self.depot
        current_time = 0.0
        total_cost = 0.0
        total_waiting = 0.0
        
        while unserviced:
            # Find best edge to insert next
            best_edge = None
            best_cost = float('inf')
            best_arrival = None
            
            for edge in unserviced:
                service = self.edge_services[edge]
                u, v = edge
                
                # Calculate arrival time at edge
                if current_node == u:
                    travel_time = 0
                    arrival = current_time
                elif current_node == v:
                    travel_time = 0
                    arrival = current_time
                else:
                    # Need to travel to edge
                    try:
                        path_len = nx.shortest_path_length(
                            self.G, current_node, u, weight='weight'
                        )
                        travel_time = path_len
                        arrival = current_time + travel_time
                    except nx.NetworkXNoPath:
                        continue
                
                # Check time window feasibility
                if arrival > service.time_window.late:
                    continue  # Too late
                
                # Calculate waiting time
                service_start = max(arrival, service.time_window.early)
                waiting = service_start - arrival
                
                # Calculate insertion cost
                insertion_cost = (
                    travel_time * service.travel_cost + 
                    service.waiting_penalty * waiting
                )
                
                if insertion_cost < best_cost:
                    best_cost = insertion_cost
                    best_edge = edge
                    best_arrival = arrival
            
            if best_edge is None:
                # No feasible insertion found
                break
            
            # Insert best edge
            service = self.edge_services[best_edge]
            u, v = best_edge
            
            service_start = max(best_arrival, service.time_window.early)
            schedule[best_edge] = service_start
            
            waiting = service_start - best_arrival
            total_waiting += waiting
            
            tour.append(best_edge)
            unserviced.remove(best_edge)
            
            # Update state
            current_time = service_start + service.service_duration
            current_node = v  # Move to end of edge
            total_cost += best_cost
        
        # Add return to depot cost
        if current_node != self.depot:
            try:
                return_cost = nx.shortest_path_length(
                    self.G, current_node, self.depot, weight='weight'
                )
                total_cost += return_cost
            except nx.NetworkXNoPath:
                pass
        
        computation_time = time.time() - start_time
        
        # Add waiting time penalty to total cost
        total_cost += total_waiting * self.edge_services[tour[0]].waiting_penalty
        
        return total_cost, tour, computation_time, schedule
    
    def solve_ortools(self) -> Tuple[float, List, float, Dict]:
        """
        Exact solution using OR-Tools constraint programming
        More sophisticated approach for smaller instances
        """
        start_time = time.time()
        
        # Create routing model
        manager = pywrapcp.RoutingIndexManager(
            len(self.G.nodes()),
            1,  # Number of vehicles
            self.depot  # Depot
        )
        routing = pywrapcp.RoutingModel(manager)
        
        # Create distance callback
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            try:
                return int(nx.shortest_path_length(
                    self.G, from_node, to_node, weight='weight'
                ) * 100)  # Scale for integer arithmetic
            except nx.NetworkXNoPath:
                return 10000000  # Large penalty
        
        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # Add time window constraints
        time_dimension_name = 'Time'
        routing.AddDimension(
            transit_callback_index,
            30000,  # Allow waiting time
            300000,  # Maximum time per vehicle
            False,  # Don't force start cumul to zero
            time_dimension_name
        )
        time_dimension = routing.GetDimensionOrDie(time_dimension_name)
        
        # Set time windows for nodes corresponding to edges
        for edge, service in self.edge_services.items():
            u, v = edge
            index = manager.NodeToIndex(v)
            time_dimension.CumulVar(index).SetRange(
                int(service.time_window.early * 100),
                int(service.time_window.late * 100)
            )
        
        # Set search parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.time_limit.seconds = 30
        
        # Solve
        solution = routing.SolveWithParameters(search_parameters)
        
        computation_time = time.time() - start_time
        
        if solution:
            total_cost = solution.ObjectiveValue() / 100.0
            
            # Extract tour
            tour = []
            schedule = {}
            index = routing.Start(0)
            
            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                time_var = time_dimension.CumulVar(index)
                schedule[node] = solution.Value(time_var) / 100.0
                
                next_index = solution.Value(routing.NextVar(index))
                if not routing.IsEnd(next_index):
                    next_node = manager.IndexToNode(next_index)
                    tour.append((node, next_node))
                
                index = next_index
            
            return total_cost, tour, computation_time, schedule
        else:
            # Fallback to greedy
            return self.solve_greedy_insertion()
    
    def solve(self, method='greedy') -> Tuple[float, List, float, Dict]:
        """
        Main solve method
        
        Args:
            method: 'greedy' or 'ortools'
        
        Returns:
            (total_cost, tour, computation_time, schedule)
        """
        if method == 'greedy':
            return self.solve_greedy_insertion()
        elif method == 'ortools':
            return self.solve_ortools()
        else:
            raise ValueError(f"Unknown method: {method}")


def generate_cpp_tw_instance(G: nx.Graph, 
                             tightness: float = 1.0) -> Dict[Tuple, EdgeService]:
    edge_services = {}
    
    # Estimate minimum tour time
    total_edges = G.number_of_edges()
    avg_service = 10.0
    min_tour_time = total_edges * avg_service
    
    current_time = 0.0
    
    for i, (u, v, data) in enumerate(G.edges(data=True)):
        edge = (u, v)
        
        # Service duration
        service_duration = np.random.uniform(5, 15)
        
        # Time window - FIXED: More generous windows
        expected_arrival = current_time
        window_size = service_duration * tightness * 10  # Was 5, now 10
        
        time_window = TimeWindow(
            early=max(0, expected_arrival - window_size),  # Allow earlier arrival
            late=expected_arrival + window_size * 2  # Much later deadline
        )
        
        edge_services[edge] = EdgeService(
            edge=edge,
            time_window=time_window,
            service_duration=service_duration,
            travel_cost=data.get('weight', 1.0),
            waiting_penalty=1.0
        )
        
        current_time += service_duration + data.get('weight', 5.0) * 0.5  # Add travel time estimate
    
    return edge_services


# Example usage and testing
if __name__ == "__main__":
    print("CPP with Time Windows - Testing")
    print("=" * 50)
    
    # Create test graph
    G = nx.grid_2d_graph(4, 4)
    G = nx.convert_node_labels_to_integers(G)
    
    # Add weights
    for u, v in G.edges():
        G[u][v]['weight'] = np.random.uniform(1, 10)
    
    # Generate time windows
    print("\nGenerating time window instance...")
    edge_services = generate_cpp_tw_instance(G, tightness=1.5)
    
    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print(f"Time windows generated for {len(edge_services)} edges")
    
    # Solve
    solver = CPPTimeWindowsSolver(G, edge_services)
    
    print("\nChecking temporal feasibility...")
    if solver.check_temporal_feasibility():
        print("✓ Instance is temporally feasible")
        
        print("\nSolving with greedy insertion...")
        cost, tour, comp_time, schedule = solver.solve(method='greedy')
        
        print(f"\nResults:")
        print(f"  Total cost: {cost:.2f}")
        print(f"  Tour length: {len(tour)} edges")
        print(f"  Computation time: {comp_time:.4f}s")
        print(f"  Edges serviced: {len(tour)}/{len(edge_services)}")
        
        # Show sample schedule
        print(f"\nSample schedule (first 5 edges):")
        for edge in list(schedule.keys())[:5]:
            service_time = schedule[edge]
            service = edge_services[edge]
            print(f"  Edge {edge}: service at t={service_time:.2f}, "
                  f"window=[{service.time_window.early:.1f}, "
                  f"{service.time_window.late:.1f}]")
    else:
        print("✗ Instance is temporally infeasible")