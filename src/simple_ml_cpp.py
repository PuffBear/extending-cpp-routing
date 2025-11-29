"""
Simple ML/RL Baseline for CPP
Learning-based edge selection heuristic

ASSUMPTIONS (documented):
1. Feature-based learning (not deep RL)
2. Simple linear model (快速训练)
3. Greedy deployment (no planning lookahead)
4. Supervised from classical solutions
"""

import networkx as nx
import numpy as np
from typing import List, Tuple, Dict
from sklearn.linear_model import LinearRegression
import pickle


class SimpleMLCPP:
    """
    Simple ML-augmented CPP solver
    
    Approach:
    - Learn edge selection from classical CPP solutions
    - Features: degree, weight, centrality
    - Model: Linear regression (fast)
    - Deployment: Greedy with learned priorities
    """
    
    def __init__(self):
        self.model = LinearRegression()
        self.trained = False
        
    def extract_edge_features(self, G: nx.Graph, edge: Tuple) -> np.ndarray:
        """
        Extract features for an edge
        
        Features:
        1. Edge weight
        2. Source node degree
        3. Target node degree
        4. Edge betweenness (simplified)
        5. Distance from depot
        """
        u, v = edge
        
        features = [
            G[u][v].get('weight', 1.0),  # Weight
            G.degree(u),  # Source degree
            G.degree(v),  # Target degree
            (G.degree(u) + G.degree(v)) / 2,  # Avg degree
            min(u, v),  # Distance from depot (simplified)
        ]
        
        return np.array(features)
    
    def train_from_solutions(self, training_data: List[Tuple[nx.Graph, List]]):
        """
        Train from classical CPP solutions

        Args:
            training_data: List of (graph, tour) pairs
        """

        X_train = []
        y_train = []

        for G, tour in training_data:
            # Handle empty tours (approximation mode)
            if not tour or len(tour) < 2:
                # Fallback: use all edges with equal priority
                for edge in G.edges():
                    features = self.extract_edge_features(G, edge)
                    priority = 1.0  # Equal priority
                    X_train.append(features)
                    y_train.append(priority)
                continue

            # Extract edge traversal order from tour
            for i, (u, v) in enumerate(zip(tour[:-1], tour[1:])):
                if G.has_edge(u, v):
                    features = self.extract_edge_features(G, (u, v))
                    priority = len(tour) - i  # Earlier = higher priority

                    X_train.append(features)
                    y_train.append(priority)

        if len(X_train) >= 5:  # Need minimum data
            X_train = np.array(X_train)
            y_train = np.array(y_train)

            self.model.fit(X_train, y_train)
            self.trained = True

            return True

        return False
    
    def solve_with_learning(self, G: nx.Graph) -> Tuple[float, List, Dict]:
        """
        Solve CPP using learned edge priorities
        
        Returns:
            (cost, tour, metadata)
        """
        
        if not self.trained:
            # Fallback to greedy
            return self._greedy_solve(G)
        
        # Get all edges
        edges = list(G.edges())
        
        # Predict priorities
        features = np.array([self.extract_edge_features(G, e) for e in edges])
        priorities = self.model.predict(features)
        
        # Sort by priority
        sorted_edges = [e for _, e in sorted(zip(priorities, edges), reverse=True)]
        
        # Build tour greedily following priorities
        tour = [0]
        current = 0
        total_cost = 0
        visited = set()
        
        for edge in sorted_edges:
            u, v = edge
            
            if (u, v) in visited or (v, u) in visited:
                continue
            
            # Go to edge and traverse it
            if current == u:
                next_node = v
                path = [u, v]
            elif current == v:
                next_node = u
                path = [v, u]
            else:
                # Find path to edge
                try:
                    path_to_u = nx.shortest_path(G, current, u, weight='weight')
                    path = path_to_u + [v]
                    next_node = v
                except:
                    try:
                        path_to_v = nx.shortest_path(G, current, v, weight='weight')
                        path = path_to_v + [u]
                        next_node = u
                    except:
                        continue
            
            # Add to tour
            for i in range(len(path) - 1):
                if G.has_edge(path[i], path[i+1]):
                    total_cost += G[path[i]][path[i+1]].get('weight', 1.0)
            
            tour.extend(path[1:])
            current = next_node
            visited.add((u, v))
            visited.add((v, u))
        
        # Return to depot
        if current != 0:
            try:
                path_home = nx.shortest_path(G, current, 0, weight='weight')
                tour.extend(path_home[1:])
                for i in range(len(path_home) - 1):
                    if G.has_edge(path_home[i], path_home[i+1]):
                        total_cost += G[path_home[i]][path_home[i+1]].get('weight', 1.0)
            except:
                pass
        
        metadata = {
            'method': 'ml_learned_priorities',
            'model': 'linear_regression',
            'features': ['weight', 'degree', 'centrality'],
            'assumptions': [
                'Supervised from classical solutions',
                'Linear model (fast training)',
                'Greedy deployment'
            ]
        }
        
        return total_cost, tour, metadata
    
    def _greedy_solve(self, G: nx.Graph) -> Tuple[float, List, Dict]:
        """Fallback greedy solver"""
        tour = [0]
        current = 0
        total_cost = 0
        visited = set()
        
        edges = list(G.edges())
        
        while len(visited) < len(edges):
            best_edge = None
            best_cost = float('inf')
            
            for edge in edges:
                if edge in visited or (edge[1], edge[0]) in visited:
                    continue
                
                u, v = edge
                
                # Cost to reach edge
                try:
                    if current == u:
                        cost = G[u][v].get('weight', 1.0)
                    elif current == v:
                        cost = G[v][u].get('weight', 1.0)
                    else:
                        cost = nx.shortest_path_length(G, current, u, weight='weight')
                        cost += G[u][v].get('weight', 1.0)
                except:
                    continue
                
                if cost < best_cost:
                    best_cost = cost
                    best_edge = edge
            
            if best_edge is None:
                break
            
            u, v = best_edge
            
            # Move to edge
            if current != u:
                try:
                    path = nx.shortest_path(G, current, u, weight='weight')
                    tour.extend(path[1:])
                    for i in range(len(path) - 1):
                        total_cost += G[path[i]][path[i+1]].get('weight', 1.0)
                    current = u
                except:
                    pass
            
            # Traverse edge
            tour.append(v)
            total_cost += G[u][v].get('weight', 1.0)
            current = v
            visited.add((u, v))
            visited.add((v, u))
        
        # Return home
        if current != 0:
            try:
                path = nx.shortest_path(G, current, 0, weight='weight')
                tour.extend(path[1:])
                for i in range(len(path) - 1):
                    total_cost += G[path[i]][path[i+1]].get('weight', 1.0)
            except:
                pass
        
        metadata = {
            'method': 'greedy_fallback',
            'ml_model': 'not_trained'
        }
        
        return total_cost, tour, metadata


if __name__ == "__main__":
    print("Simple ML-CPP loaded")
