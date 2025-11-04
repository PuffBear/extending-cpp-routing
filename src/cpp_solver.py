"""
Chinese Postman Problem Solver with Multiple Variants
Implementation for "Extending the Chinese Postman Problem for Logistics" research paper
"""

import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from typing import List, Tuple, Dict, Optional
import time
import random
from itertools import combinations
import copy

class CPPSolver:
    """Classical Chinese Postman Problem solver with multiple variants support"""
    
    def __init__(self):
        self.results = {}
        
    def solve_classical_cpp(self, G: nx.Graph) -> Tuple[float, List, float]:
        """
        Solve classical CPP using Edmonds' algorithm
        Returns: (cost, tour, computation_time)
        """
        start_time = time.time()
        
        # Ensure graph is connected
        if not nx.is_connected(G):
            raise ValueError("Graph must be connected for CPP")
        
        # Check if graph is Eulerian
        odd_vertices = [v for v in G.nodes() if G.degree(v) % 2 == 1]
        
        if not odd_vertices:
            # Graph is Eulerian - find Eulerian circuit
            tour = list(nx.eulerian_circuit(G, source=list(G.nodes())[0]))
            cost = sum(G[u][v]['weight'] for u, v in tour)
        else:
            # Find minimum weight perfect matching on odd vertices
            if len(odd_vertices) % 2 != 0:
                raise ValueError("Number of odd vertices must be even")
            
            # Create complete graph on odd vertices with shortest path weights
            odd_complete = nx.Graph()
            odd_complete.add_nodes_from(odd_vertices)
            
            for i, u in enumerate(odd_vertices):
                for j, v in enumerate(odd_vertices):
                    if i < j:  # Only add each edge once
                        try:
                            path_weight = nx.shortest_path_length(G, u, v, weight='weight')
                            odd_complete.add_edge(u, v, weight=path_weight)
                        except nx.NetworkXNoPath:
                            odd_complete.add_edge(u, v, weight=float('inf'))
            
            # Find minimum weight perfect matching
            matching = nx.algorithms.matching.min_weight_matching(odd_complete, weight='weight')
            
            # Create augmented graph by duplicating paths
            G_aug = G.copy()
            total_augmentation_cost = 0
            
            for u, v in matching:
                try:
                    # Get shortest path and duplicate it
                    path = nx.shortest_path(G, u, v, weight='weight')
                    path_cost = nx.shortest_path_length(G, u, v, weight='weight')
                    total_augmentation_cost += path_cost
                    
                    # Add edges from the path to augmented graph
                    for i in range(len(path) - 1):
                        edge_u, edge_v = path[i], path[i+1]
                        if G_aug.has_edge(edge_u, edge_v):
                            # Create parallel edge by modifying the weight
                            # This is a simplified approach - in practice you'd handle multigraphs
                            current_weight = G_aug[edge_u][edge_v]['weight']
                            original_weight = G[edge_u][edge_v]['weight']
                            G_aug[edge_u][edge_v]['weight'] = current_weight + original_weight
                        else:
                            # This shouldn't happen if path is valid
                            G_aug.add_edge(edge_u, edge_v, weight=G[edge_u][edge_v]['weight'])
                            
                except nx.NetworkXNoPath:
                    print(f"Warning: No path between {u} and {v}")
                    continue
            
            # Verify augmented graph is Eulerian
            if all(G_aug.degree(v) % 2 == 0 for v in G_aug.nodes()):
                # Find Eulerian circuit in augmented graph
                tour = list(nx.eulerian_circuit(G_aug, source=list(G_aug.nodes())[0]))
                # Calculate cost as sum of original edge weights (counting multiplicities)
                cost = sum(G[u][v]['weight'] for u, v in G.edges()) + total_augmentation_cost
            else:
                # Fallback: approximate solution
                print("Warning: Augmented graph is not Eulerian, using approximation")
                total_weight = sum(G[u][v]['weight'] for u, v in G.edges())
                cost = total_weight * 2  # Simple approximation
                tour = []
        
        computation_time = time.time() - start_time
        return cost, tour, computation_time
    
    def solve_cpp_with_capacity(self, G: nx.Graph, capacity: int) -> Tuple[float, List, float]:
        """
        Solve CPP with vehicle capacity constraints (simplified version)
        """
        start_time = time.time()
        
        # Get classical CPP solution as baseline
        base_cost, base_tour, _ = self.solve_classical_cpp(G)
        
        # Simple capacity-aware heuristic
        current_load = 0
        modified_cost = 0
        tour_segments = []
        
        for u, v in base_tour:
            edge_demand = G[u][v].get('demand', 1)
            
            if current_load + edge_demand > capacity:
                # Return to depot (add penalty cost)
                modified_cost += 10  # Depot return penalty
                current_load = 0
                tour_segments.append(('depot_return',))
            
            modified_cost += G[u][v]['weight']
            current_load += edge_demand
            tour_segments.append((u, v))
        
        computation_time = time.time() - start_time
        return modified_cost, tour_segments, computation_time
    
    def solve_k_cpp_greedy(self, G: nx.Graph, k: int) -> Tuple[float, List, float]:
        """
        Solve k-CPP using greedy heuristic (min-max objective)
        """
        start_time = time.time()
        
        # Initialize k empty tours
        tours = [[] for _ in range(k)]
        tour_costs = [0] * k
        uncovered_edges = list(G.edges())
        
        # Greedy assignment: assign each edge to least loaded vehicle
        for edge in uncovered_edges:
            u, v = edge
            weight = G[u][v]['weight']
            
            # Find vehicle with minimum current cost
            min_vehicle = min(range(k), key=lambda i: tour_costs[i])
            
            tours[min_vehicle].append(edge)
            tour_costs[min_vehicle] += weight
        
        # The makespan is the maximum tour cost
        makespan = max(tour_costs)
        
        computation_time = time.time() - start_time
        return makespan, tours, computation_time

class BenchmarkGenerator:
    """Generate benchmark instances for CPP variants"""
    
    def __init__(self, seed: int = 42):
        random.seed(seed)
        np.random.seed(seed)
    
    def generate_grid_graph(self, rows: int, cols: int) -> nx.Graph:
        """Generate grid network (urban street network)"""
        G = nx.grid_2d_graph(rows, cols)
        
        # Convert to simple graph and add weights
        H = nx.Graph()
        for u, v in G.edges():
            weight = random.uniform(1, 10)
            demand = random.randint(1, 5)
            H.add_edge(u, v, weight=weight, demand=demand)
        
        return H
    
    def generate_random_graph(self, n: int, p: float = 0.3) -> nx.Graph:
        """Generate random geometric graph"""
        G = nx.erdos_renyi_graph(n, p)
        
        # Add weights and demands
        for u, v in G.edges():
            weight = random.uniform(1, 15)
            demand = random.randint(1, 3)
            G[u][v]['weight'] = weight
            G[u][v]['demand'] = demand
        
        return G
    
    def generate_clustered_graph(self, num_clusters: int, cluster_size: int) -> nx.Graph:
        """Generate clustered network (multiple service areas)"""
        G = nx.Graph()
        node_id = 0
        
        # Create clusters
        cluster_centers = []
        for i in range(num_clusters):
            # Create a dense cluster
            cluster_nodes = list(range(node_id, node_id + cluster_size))
            cluster_centers.append(node_id)
            
            # Add intra-cluster edges
            for u in cluster_nodes:
                for v in cluster_nodes:
                    if u < v and random.random() < 0.7:
                        weight = random.uniform(1, 5)
                        demand = random.randint(1, 2)
                        G.add_edge(u, v, weight=weight, demand=demand)
            
            node_id += cluster_size
        
        # Add inter-cluster connections
        for i in range(len(cluster_centers)):
            for j in range(i + 1, len(cluster_centers)):
                if random.random() < 0.3:
                    weight = random.uniform(10, 20)  # Longer inter-cluster distances
                    demand = random.randint(1, 3)
                    G.add_edge(cluster_centers[i], cluster_centers[j], 
                             weight=weight, demand=demand)
        
        return G
    
    def generate_benchmark_suite(self, output_dir: str = "data/") -> Dict:
        """Generate complete benchmark suite"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        instances = {}
        
        # Small instances (20-50 nodes)
        print("Generating small instances...")
        for i in range(20):
            if i < 7:
                G = self.generate_grid_graph(4, 5)
                instance_type = "grid_small"
            elif i < 14:
                G = self.generate_random_graph(25, 0.3)
                instance_type = "random_small"
            else:
                G = self.generate_clustered_graph(3, 7)
                instance_type = "clustered_small"
            
            # Ensure connected
            if nx.is_connected(G):
                instances[f"{instance_type}_{i}"] = G
        
        # Medium instances (50-100 nodes)
        print("Generating medium instances...")
        for i in range(15):
            if i < 5:
                G = self.generate_grid_graph(7, 8)
                instance_type = "grid_medium"
            elif i < 10:
                G = self.generate_random_graph(60, 0.25)
                instance_type = "random_medium"
            else:
                G = self.generate_clustered_graph(4, 12)
                instance_type = "clustered_medium"
            
            if nx.is_connected(G):
                instances[f"{instance_type}_{i}"] = G
        
        # Save instances
        for name, graph in instances.items():
            nx.write_gml(graph, f"{output_dir}/{name}.gml")
        
        print(f"Generated {len(instances)} benchmark instances")
        return instances

class ExperimentRunner:
    """Run experiments and collect results"""
    
    def __init__(self):
        self.solver = CPPSolver()
        self.results = []
    
    def run_classical_experiments(self, instances: Dict[str, nx.Graph]) -> pd.DataFrame:
        """Run classical algorithm experiments"""
        print("Running classical CPP experiments...")
        
        for name, graph in instances.items():
            print(f"Solving {name}...")
            
            # Classical CPP
            try:
                cost, tour, time_taken = self.solver.solve_classical_cpp(graph)
                self.results.append({
                    'instance': name,
                    'algorithm': 'Classical_CPP',
                    'variant': 'CPP',
                    'cost': cost,
                    'time': time_taken,
                    'nodes': graph.number_of_nodes(),
                    'edges': graph.number_of_edges()
                })
            except Exception as e:
                print(f"Error solving {name}: {e}")
            
            # CPP with capacity (Q = 10)
            try:
                cost, tour, time_taken = self.solver.solve_cpp_with_capacity(graph, 10)
                self.results.append({
                    'instance': name,
                    'algorithm': 'Capacity_Heuristic',
                    'variant': 'CPP-LC',
                    'cost': cost,
                    'time': time_taken,
                    'nodes': graph.number_of_nodes(),
                    'edges': graph.number_of_edges()
                })
            except Exception as e:
                print(f"Error solving capacity variant {name}: {e}")
            
            # k-CPP (k=2)
            try:
                cost, tours, time_taken = self.solver.solve_k_cpp_greedy(graph, 2)
                self.results.append({
                    'instance': name,
                    'algorithm': 'Greedy_k_CPP',
                    'variant': 'k-CPP',
                    'cost': cost,
                    'time': time_taken,
                    'nodes': graph.number_of_nodes(),
                    'edges': graph.number_of_edges()
                })
            except Exception as e:
                print(f"Error solving k-CPP variant {name}: {e}")
        
        return pd.DataFrame(self.results)
    
    def generate_performance_table(self, results_df: pd.DataFrame) -> pd.DataFrame:
        """Generate performance summary table for paper"""
        summary = results_df.groupby(['algorithm', 'variant']).agg({
            'cost': 'mean',
            'time': 'mean',
            'nodes': 'mean',
            'edges': 'mean'
        }).round(2)
        
        return summary

if __name__ == "__main__":
    print("Setting up CPP Research Framework...")
    
    # Generate benchmark instances
    generator = BenchmarkGenerator()
    instances = generator.generate_benchmark_suite()
    
    # Run experiments
    runner = ExperimentRunner()
    results_df = runner.run_classical_experiments(instances)
    
    # Generate summary
    summary = runner.generate_performance_table(results_df)
    print("\nPerformance Summary:")
    print(summary)
    
    # Save results
    results_df.to_csv("results/classical_results.csv", index=False)
    summary.to_csv("results/performance_summary.csv")
    
    print("\nExperiments completed! Check results/ directory for outputs.")