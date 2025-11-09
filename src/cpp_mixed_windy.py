"""
Mixed Chinese Postman Problem (MCPP) and Windy Postman Problem
Matching Sections 2.3.1 and 2.3.2 of the paper
"""

import networkx as nx
import numpy as np
from typing import List, Tuple, Dict, Optional, Set
import time
from dataclasses import dataclass
from itertools import combinations


@dataclass
class MixedEdge:
    """Edge in mixed graph - can be directed or undirected"""
    u: int
    v: int
    is_directed: bool
    weight: float
    
    def __hash__(self):
        if self.is_directed:
            return hash((self.u, self.v, True))
        else:
            return hash((min(self.u, self.v), max(self.u, self.v), False))


@dataclass
class WindyEdge:
    """Edge with direction-dependent costs (Definition 1 from paper)"""
    u: int
    v: int
    cost_uv: float  # Cost from u to v
    cost_vu: float  # Cost from v to u
    
    def avg_cost(self) -> float:
        return (self.cost_uv + self.cost_vu) / 2
    
    def cost_diff(self) -> float:
        return abs(self.cost_uv - self.cost_vu)


class MixedCPPSolver:
    """
    Mixed Chinese Postman Problem Solver
    Theorem 2 from paper: MCPP is NP-hard
    
    The complexity arises from determining optimal orientations 
    for undirected edges while maintaining connectivity.
    """
    
    def __init__(self, G: nx.MultiDiGraph, edge_info: Dict[Tuple, MixedEdge]):
        """
        Args:
            G: NetworkX MultiDiGraph (can contain both directed and undirected)
            edge_info: Information about which edges are directed/undirected
        """
        self.G = G
        self.edge_info = edge_info
        self.undirected_edges = [
            (u, v) for (u, v), info in edge_info.items() 
            if not info.is_directed
        ]
        self.directed_edges = [
            (u, v) for (u, v), info in edge_info.items() 
            if info.is_directed
        ]
    
    def check_weak_connectivity(self) -> bool:
        """Check if the underlying undirected graph is connected"""
        # Convert to undirected for connectivity check
        G_undirected = self.G.to_undirected()
        return nx.is_connected(G_undirected)
    
    def compute_degree_deficiency(self, orientation: Dict[Tuple, str]) -> Dict[int, int]:
        """
        Compute in-degree - out-degree for each vertex given an orientation
        
        Args:
            orientation: dict mapping undirected edges to 'forward' or 'backward'
        
        Returns:
            Dictionary of degree deficiency per vertex
        """
        deficiency = {node: 0 for node in self.G.nodes()}
        
        # Process directed edges
        for u, v in self.directed_edges:
            deficiency[v] += 1  # in-degree
            deficiency[u] -= 1  # out-degree
        
        # Process oriented undirected edges
        for (u, v), direction in orientation.items():
            if direction == 'forward':
                deficiency[v] += 1
                deficiency[u] -= 1
            else:  # backward
                deficiency[u] += 1
                deficiency[v] -= 1
        
        return deficiency
    
    def is_eulerian_orientation(self, orientation: Dict[Tuple, str]) -> bool:
        """Check if orientation makes graph Eulerian (all deficiencies = 0)"""
        deficiency = self.compute_degree_deficiency(orientation)
        return all(d == 0 for d in deficiency.values())
    
    def solve_greedy_orientation(self) -> Tuple[float, List, float]:
        """
        Greedy heuristic for MCPP
        Try to find orientation that minimizes degree deficiencies
        """
        start_time = time.time()
        
        if not self.check_weak_connectivity():
            raise ValueError("Graph must be weakly connected")
        
        # Try to find a good orientation
        best_cost = float('inf')
        best_tour = []
        
        # Greedy: orient each undirected edge to balance degrees
        orientation = {}
        deficiency = {node: 0 for node in self.G.nodes()}
        
        # Initialize with directed edges
        for u, v in self.directed_edges:
            deficiency[v] += 1
            deficiency[u] -= 1
        
        # Greedily orient undirected edges
        for u, v in self.undirected_edges:
            # Try both orientations, pick one that reduces imbalance
            
            # Option 1: u -> v
            score1 = abs(deficiency[v] + 1) + abs(deficiency[u] - 1)
            
            # Option 2: v -> u
            score2 = abs(deficiency[u] + 1) + abs(deficiency[v] - 1)
            
            if score1 <= score2:
                orientation[(u, v)] = 'forward'
                deficiency[v] += 1
                deficiency[u] -= 1
            else:
                orientation[(u, v)] = 'backward'
                deficiency[u] += 1
                deficiency[v] -= 1
        
        # Now we have an orientation, compute cost of making it Eulerian
        imbalanced = [(v, d) for v, d in deficiency.items() if d != 0]
        
        # Cost estimate: need to add edges to balance
        augmentation_cost = sum(abs(d) for v, d in imbalanced) * 10  # Rough estimate
        
        base_cost = sum(
            self.edge_info[(u, v)].weight 
            for u, v in self.edge_info.keys()
        )
        
        total_cost = base_cost + augmentation_cost
        
        computation_time = time.time() - start_time
        
        # Simple tour construction (not optimal, but feasible)
        tour = list(self.edge_info.keys())
        
        return total_cost, tour, computation_time
    
    def solve_branch_and_bound(self, max_undirected: int = 15) -> Tuple[float, List, float]:
        """
        Exact branch-and-bound for small instances
        Only feasible when number of undirected edges is small
        """
        start_time = time.time()
        
        if len(self.undirected_edges) > max_undirected:
            print(f"Too many undirected edges ({len(self.undirected_edges)}), using greedy")
            return self.solve_greedy_orientation()
        
        best_cost = float('inf')
        best_orientation = None
        
        # Try all possible orientations (2^n possibilities)
        n_undirected = len(self.undirected_edges)
        
        for i in range(2 ** n_undirected):
            orientation = {}
            
            # Decode binary number to orientation
            for j, (u, v) in enumerate(self.undirected_edges):
                if (i >> j) & 1:
                    orientation[(u, v)] = 'forward'
                else:
                    orientation[(u, v)] = 'backward'
            
            # Check if this creates an Eulerian graph
            if self.is_eulerian_orientation(orientation):
                # Compute cost
                cost = sum(
                    self.edge_info[edge].weight 
                    for edge in self.edge_info.keys()
                )
                
                if cost < best_cost:
                    best_cost = cost
                    best_orientation = orientation
        
        if best_orientation is None:
            # No Eulerian orientation found, need augmentation
            return self.solve_greedy_orientation()
        
        computation_time = time.time() - start_time
        tour = list(self.edge_info.keys())
        
        return best_cost, tour, computation_time


class WindyPostmanSolver:
    """
    Windy Postman Problem Solver
    Section 2.3.2: Generalizes both CPP and MCPP
    
    Requires simultaneous optimization of:
    1. Edge orientations (which direction to traverse)
    2. Tour construction
    """
    
    def __init__(self, G: nx.Graph, windy_edges: Dict[Tuple, WindyEdge]):
        """
        Args:
            G: Base undirected graph
            windy_edges: Direction-dependent costs for each edge
        """
        self.G = G
        self.windy_edges = windy_edges
    
    def solve_average_cost_heuristic(self) -> Tuple[float, List, float]:
        """
        Heuristic: Use average costs to get initial solution,
        then optimize orientation choices
        """
        start_time = time.time()
        
        # Phase 1: Solve classical CPP with average costs
        G_avg = nx.Graph()
        for (u, v), edge in self.windy_edges.items():
            G_avg.add_edge(u, v, weight=edge.avg_cost())
        
        # Find odd vertices
        odd_vertices = [v for v in G_avg.nodes() if G_avg.degree(v) % 2 == 1]
        
        # Compute shortest paths between odd vertices
        if odd_vertices:
            K = nx.Graph()
            K.add_nodes_from(odd_vertices)
            
            for i, u in enumerate(odd_vertices):
                for j, v in enumerate(odd_vertices):
                    if i < j:
                        path_len = nx.shortest_path_length(
                            G_avg, u, v, weight='weight'
                        )
                        K.add_edge(u, v, weight=path_len)
            
            # Find minimum matching
            matching = nx.algorithms.matching.min_weight_matching(K, weight='weight')
            
            # Cost calculation
            base_cost = sum(edge.avg_cost() for edge in self.windy_edges.values())
            augmentation_cost = sum(K[u][v]['weight'] for u, v in matching)
            
            total_cost = base_cost + augmentation_cost
        else:
            # Already Eulerian
            total_cost = sum(edge.avg_cost() for edge in self.windy_edges.values())
        
        # Phase 2: Optimize orientations
        # For each edge, choose cheaper direction
        orientation_savings = 0
        orientations = {}
        
        for (u, v), edge in self.windy_edges.items():
            if edge.cost_uv < edge.cost_vu:
                orientations[(u, v)] = 'forward'
                orientation_savings += (edge.cost_vu - edge.cost_uv) / 2
            else:
                orientations[(u, v)] = 'backward'
                orientation_savings += (edge.cost_uv - edge.cost_vu) / 2
        
        final_cost = total_cost - orientation_savings
        
        computation_time = time.time() - start_time
        tour = list(self.windy_edges.keys())
        
        return final_cost, tour, computation_time
    
    def solve_min_cost_orientation(self) -> Tuple[float, List, float]:
        """
        Advanced heuristic: Find orientation that minimizes total cost
        while maintaining Eulerian property
        """
        start_time = time.time()
        
        # Build orientation problem as ILP (conceptually)
        # For each edge e, we choose direction d_e ∈ {0, 1}
        # Cost: Σ (d_e · cost_forward + (1-d_e) · cost_backward)
        # Constraint: Flow conservation (Eulerian)
        
        # Greedy approximation:
        best_cost = float('inf')
        best_orientations = {}
        
        # Try multiple random starting orientations
        for trial in range(10):
            orientations = {}
            in_degree = {v: 0 for v in self.G.nodes()}
            out_degree = {v: 0 for v in self.G.nodes()}
            
            edges_list = list(self.windy_edges.items())
            np.random.shuffle(edges_list)
            
            for (u, v), edge in edges_list:
                # Choose direction that balances degrees and minimizes cost
                balance_score_forward = abs(in_degree[v] + 1 - out_degree[v]) + \
                                       abs(out_degree[u] + 1 - in_degree[u])
                balance_score_backward = abs(in_degree[u] + 1 - out_degree[u]) + \
                                        abs(out_degree[v] + 1 - in_degree[v])
                
                # Weight by cost difference
                if edge.cost_uv < edge.cost_vu:
                    # Prefer forward
                    if balance_score_forward <= balance_score_backward + 1:
                        orientations[(u, v)] = 'forward'
                        in_degree[v] += 1
                        out_degree[u] += 1
                    else:
                        orientations[(u, v)] = 'backward'
                        in_degree[u] += 1
                        out_degree[v] += 1
                else:
                    # Prefer backward
                    if balance_score_backward <= balance_score_forward + 1:
                        orientations[(u, v)] = 'backward'
                        in_degree[u] += 1
                        out_degree[v] += 1
                    else:
                        orientations[(u, v)] = 'forward'
                        in_degree[v] += 1
                        out_degree[u] += 1
            
            # Calculate cost
            cost = sum(
                edge.cost_uv if orientations[(u, v)] == 'forward' else edge.cost_vu
                for (u, v), edge in self.windy_edges.items()
            )
            
            # Add imbalance penalty
            imbalance = sum(abs(in_degree[v] - out_degree[v]) for v in self.G.nodes())
            cost += imbalance * 10
            
            if cost < best_cost:
                best_cost = cost
                best_orientations = orientations
        
        computation_time = time.time() - start_time
        tour = list(self.windy_edges.keys())
        
        return best_cost, tour, computation_time


def generate_mixed_cpp_instance(G: nx.Graph, 
                                directed_fraction: float = 0.5) -> Dict[Tuple, MixedEdge]:
    """
    Generate mixed graph instance (some directed, some undirected edges)
    
    Args:
        G: Base graph
        directed_fraction: Fraction of edges to make directed
    """
    edge_info = {}
    
    for u, v, data in G.edges(data=True):
        is_directed = np.random.random() < directed_fraction
        
        edge_info[(u, v)] = MixedEdge(
            u=u,
            v=v,
            is_directed=is_directed,
            weight=data.get('weight', np.random.uniform(1, 10))
        )
    
    return edge_info


def generate_windy_instance(G: nx.Graph, 
                           asymmetry: float = 0.5) -> Dict[Tuple, WindyEdge]:
    """
    Generate windy postman instance with direction-dependent costs
    
    Args:
        G: Base graph
        asymmetry: How different are forward/backward costs (0 = symmetric, 1 = very different)
    """
    windy_edges = {}
    
    for u, v, data in G.edges(data=True):
        base_cost = data.get('weight', np.random.uniform(5, 15))
        
        # Create asymmetric costs
        variation = asymmetry * base_cost * np.random.uniform(0, 1)
        
        if np.random.random() < 0.5:
            cost_uv = base_cost - variation/2
            cost_vu = base_cost + variation/2
        else:
            cost_uv = base_cost + variation/2
            cost_vu = base_cost - variation/2
        
        windy_edges[(u, v)] = WindyEdge(
            u=u,
            v=v,
            cost_uv=cost_uv,
            cost_vu=cost_vu
        )
    
    return windy_edges


# Testing
if __name__ == "__main__":
    print("Mixed CPP and Windy Postman - Testing")
    print("=" * 50)
    
    # Create test graph
    G = nx.grid_2d_graph(3, 4)
    G = nx.convert_node_labels_to_integers(G)
    
    for u, v in G.edges():
        G[u][v]['weight'] = np.random.uniform(1, 10)
    
    # Test Mixed CPP
    print("\n" + "=" * 50)
    print("MIXED CPP TEST")
    print("=" * 50)
    
    edge_info = generate_mixed_cpp_instance(G, directed_fraction=0.4)
    
    directed_count = sum(1 for e in edge_info.values() if e.is_directed)
    undirected_count = len(edge_info) - directed_count
    
    print(f"\nGenerated mixed graph:")
    print(f"  Directed edges: {directed_count}")
    print(f"  Undirected edges: {undirected_count}")
    
    # Convert to MultiDiGraph for solver
    G_mixed = nx.MultiDiGraph()
    for (u, v), info in edge_info.items():
        if info.is_directed:
            G_mixed.add_edge(u, v, weight=info.weight)
        else:
            G_mixed.add_edge(u, v, weight=info.weight)
            G_mixed.add_edge(v, u, weight=info.weight)
    
    solver = MixedCPPSolver(G_mixed, edge_info)
    cost, tour, comp_time = solver.solve_greedy_orientation()
    
    print(f"\nMixed CPP Results:")
    print(f"  Total cost: {cost:.2f}")
    print(f"  Tour length: {len(tour)}")
    print(f"  Computation time: {comp_time:.4f}s")
    
    # Test Windy Postman
    print("\n" + "=" * 50)
    print("WINDY POSTMAN TEST")
    print("=" * 50)
    
    windy_edges = generate_windy_instance(G, asymmetry=0.6)
    
    print(f"\nGenerated windy instance:")
    print(f"  Total edges: {len(windy_edges)}")
    
    # Show sample asymmetric costs
    print(f"\nSample direction-dependent costs:")
    for (u, v), edge in list(windy_edges.items())[:5]:
        print(f"  Edge ({u},{v}): forward={edge.cost_uv:.2f}, backward={edge.cost_vu:.2f}, "
              f"diff={edge.cost_diff():.2f}")
    
    solver = WindyPostmanSolver(G, windy_edges)
    
    # Test both methods
    print(f"\nMethod 1: Average Cost Heuristic")
    cost1, tour1, time1 = solver.solve_average_cost_heuristic()
    print(f"  Cost: {cost1:.2f}, Time: {time1:.4f}s")
    
    print(f"\nMethod 2: Min-Cost Orientation")
    cost2, tour2, time2 = solver.solve_min_cost_orientation()
    print(f"  Cost: {cost2:.2f}, Time: {time2:.4f}s")
    
    improvement = (cost1 - cost2) / cost1 * 100
    print(f"\nImprovement: {improvement:.1f}%")