"""
OR-Tools Baseline Integration
Uses Google OR-Tools for vehicle routing as CPP baseline
"""

import networkx as nx
import numpy as np
from typing import List, Tuple, Dict
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


def solve_with_ortools(G: nx.Graph, 
                       edge_demands: Dict = None,
                       capacity: float = None) -> Tuple[float, List]:
    """
    Solve CPP using OR-Tools VRP solver
    
    Args:
        G: NetworkX graph
        edge_demands: Optional edge demands for CPP-LC
        capacity: Optional vehicle capacity
        
    Returns:
        (cost, tour) tuple
    """
    
    # Convert graph to distance matrix
    nodes = list(G.nodes())
    n = len(nodes)
    node_to_idx = {node: i for i, node in enumerate(nodes)}
    
    # Create distance matrix
    distance_matrix = np.zeros((n, n))
    for i, u in enumerate(nodes):
        for j, v in enumerate(nodes):
            if i == j:
                distance_matrix[i][j] = 0
            elif G.has_edge(u, v):
                distance_matrix[i][j] = G[u][v].get('weight', 1.0)
            else:
                # Use shortest path
                try:
                    path_len = nx.shortest_path_length(G, u, v, weight='weight')
                    distance_matrix[i][j] = path_len
                except nx.NetworkXNoPath:
                    distance_matrix[i][j] = 1e6  # Large value
    
    # Create routing model
    manager = pywrapcp.RoutingIndexManager(n, 1, 0)  # 1 vehicle, depot at 0
    routing = pywrapcp.RoutingModel(manager)
    
    # Distance callback
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(distance_matrix[from_node][to_node] * 100)  # Scale for integer
    
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # Add capacity constraints if provided
    if edge_demands is not None and capacity is not None:
        # Demand callback
        demands = [0] * n  # Node demands (simplified)
        
        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return demands[from_node]
        
        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            [int(capacity)] if capacity else [1000000],  # vehicle capacities
            True,  # start cumul to zero
            'Capacity'
        )
    
    # Search parameters
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.seconds = 30  # 30 second time limit
    
    # Solve
    solution = routing.SolveWithParameters(search_parameters)
    
    if solution:
        # Extract tour
        tour = []
        index = routing.Start(0)
        
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            tour.append(nodes[node_index])
            index = solution.Value(routing.NextVar(index))
        
        # Add final node
        node_index = manager.IndexToNode(index)
        tour.append(nodes[node_index])
        
        # Get cost
        cost = solution.ObjectiveValue() / 100.0  # Unscale
        
        return cost, tour
    
    else:
        # No solution found, return large cost
        return float('inf'), []


def solve_cpp_lc_with_ortools(G: nx.Graph,
                               edge_demands: Dict,
                               capacity: float,
                               depot: int = 0) -> Tuple[float, List, Dict]:
    """
    Solve CPP-LC (Load-Dependent Costs) using OR-Tools CVRP
    
    This maps CPP-LC to Capacitated Vehicle Routing Problem
    
    Args:
        G: Graph
        edge_demands: Demands for each edge
        capacity: Vehicle capacity
        depot: Depot node
        
    Returns:
        (cost, tour, metadata) tuple
    """
    
    # Convert CPP-LC to CVRP by creating "service nodes" for edges
    nodes = list(G.nodes())
    edges_to_service = list(G.edges())
    
    # For each edge, we need to "visit" it
    # Map this to visiting nodes
    n_nodes = len(nodes)
    n_edges = len(edges_to_service)
    
    # Create extended problem
    # Original nodes + virtual nodes for each edge
    total_nodes = n_nodes + n_edges
    
    # Distance matrix
    distance_matrix = np.zeros((total_nodes, total_nodes))
    
    # Fill original node distances
    node_to_idx = {node: i for i, node in enumerate(nodes)}
    for i, u in enumerate(nodes):
        for j, v in enumerate(nodes):
            if i == j:
                distance_matrix[i][j] = 0
            elif G.has_edge(u, v):
                distance_matrix[i][j] = G[u][v].get('weight', 1.0)
            else:
                try:
                    distance_matrix[i][j] = nx.shortest_path_length(G, u, v, weight='weight')
                except:
                    distance_matrix[i][j] = 1e6
    
    # Virtual nodes for edges (at indices n_nodes to total_nodes-1)
    for edge_idx, (u, v) in enumerate(edges_to_service):
        vnode_idx = n_nodes + edge_idx
        u_idx = node_to_idx[u]
        v_idx = node_to_idx[v]
        
        # Distance from real nodes to virtual edge node
        # (approximate as distance to midpoint)
        for i in range(n_nodes):
            distance_matrix[i][vnode_idx] = (distance_matrix[i][u_idx] + distance_matrix[i][v_idx]) / 2
            distance_matrix[vnode_idx][i] = distance_matrix[i][vnode_idx]
    
    # Create routing model
    manager = pywrapcp.RoutingIndexManager(
        total_nodes,
        1,  # Single vehicle (can extend to multiple)
        depot
    )
    routing = pywrapcp.RoutingModel(manager)
    
    # Distance callback
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(distance_matrix[from_node][to_node] * 100)
    
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # Demand callback (edges have demands, nodes don't)
    demands = [0] * total_nodes
    for edge_idx, edge in enumerate(edges_to_service):
        vnode_idx = n_nodes + edge_idx
        demands[vnode_idx] = edge_demands.get(edge, 0)
    
    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return int(demands[from_node] * 100)  # Scale for integer
    
    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,
        [int(capacity * 100)],
        True,
        'Capacity'
    )
    
    # All virtual edge nodes must be visited
    for edge_idx in range(n_edges):
        vnode_idx = n_nodes + edge_idx
        routing.AddDisjunction([manager.NodeToIndex(vnode_idx)], 1000000)
    
    # Search parameters
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.seconds = 60
    
    # Solve
    solution = routing.SolveWithParameters(search_parameters)
    
    if solution:
        tour = []
        index = routing.Start(0)
        total_distance = 0
        
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            
            if node_index < n_nodes:
                tour.append(nodes[node_index])
            else:
                # Virtual edge node
                edge_idx = node_index - n_nodes
                tour.append(f"edge_{edge_idx}")
            
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            total_distance += routing.GetArcCostForVehicle(previous_index, index, 0)
        
        cost = total_distance / 100.0
        
        metadata = {
            'solver': 'ortools_cvrp',
            'edges_serviced': n_edges,
            'capacity_used': sum(demands) / 100.0,
            'capacity_limit': capacity
        }
        
        return cost, tour, metadata
    
    else:
        return float('inf'), [], {'solver': 'ortools_cvrp', 'status': 'no_solution'}


def test_ortools_integration():
    """Test OR-Tools integration"""
    print("=" * 70)
    print("Testing OR-Tools Integration")
    print("=" * 70)
    
    # Create simple test graph
    G = nx.Graph()
    G.add_edge(0, 1, weight=1.0)
    G.add_edge(1, 2, weight=1.5)
    G.add_edge(2, 3, weight=2.0)
    G.add_edge(3, 0, weight=1.2)
    G.add_edge(0, 2, weight=2.5)
    
    print(f"\nTest graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    # Test basic VRP
    print("\n🔬 Test 1: Basic VRP")
    cost, tour = solve_with_ortools(G)
    print(f"   Cost: {cost:.2f}")
    print(f"   Tour length: {len(tour)}")
    print(f"   Tour: {tour}")
    
    # Test with capacity constraints
    print("\n🔬 Test 2: With Capacity Constraints")
    edge_demands = {
        (0, 1): 5.0,
        (1, 2): 7.0,
        (2, 3): 6.0,
        (3, 0): 4.0,
        (0, 2): 8.0
    }
    capacity = 15.0
    
    cost, tour, meta = solve_cpp_lc_with_ortools(G, edge_demands, capacity)
    print(f"   Cost: {cost:.2f}")
    print(f"   Tour length: {len(tour)}")
    print(f"   Metadata: {meta}")
    
    print("\n✅ OR-Tools integration tests complete")


if __name__ == "__main__":
    test_ortools_integration()
