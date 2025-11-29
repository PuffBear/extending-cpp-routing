"""
Improved ML-augmented CPP for Real-World Networks
Focus on realistic features and better learning
"""

import networkx as nx
import numpy as np
from typing import List, Tuple, Dict
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import pickle


class ImprovedMLCPP:
    """
    Better ML approach for CPP on real-world networks

    Improvements:
    1. Better graph features (betweenness, closeness, clustering)
    2. Random Forest instead of linear regression
    3. Smarter edge selection strategy
    4. Use greedy baseline as fallback training
    """

    def __init__(self):
        self.model = RandomForestRegressor(
            n_estimators=50,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.trained = False
        self.feature_cache = {}

    def compute_graph_features(self, G: nx.Graph):
        """
        Compute rich graph features once per graph
        Cache for efficiency
        """
        graph_id = id(G)

        if graph_id in self.feature_cache:
            return self.feature_cache[graph_id]

        # Compute centralities
        try:
            betweenness = nx.betweenness_centrality(G, weight='weight')
        except:
            betweenness = {n: 0.0 for n in G.nodes()}

        try:
            closeness = nx.closeness_centrality(G, distance='weight')
        except:
            closeness = {n: 0.0 for n in G.nodes()}

        try:
            clustering = nx.clustering(G)
        except:
            clustering = {n: 0.0 for n in G.nodes()}

        # Compute degree centrality
        degree_cent = nx.degree_centrality(G)

        features = {
            'betweenness': betweenness,
            'closeness': closeness,
            'clustering': clustering,
            'degree_cent': degree_cent
        }

        self.feature_cache[graph_id] = features
        return features

    def extract_edge_features(self, G: nx.Graph, edge: Tuple) -> np.ndarray:
        """
        Extract rich features for an edge

        Features (10 total):
        1. Edge weight
        2. Source betweenness
        3. Target betweenness
        4. Source closeness
        5. Target closeness
        6. Source clustering
        7. Target clustering
        8. Source degree centrality
        9. Target degree centrality
        10. Weight / avg_weight ratio
        """
        u, v = edge

        # Get cached graph features
        graph_feats = self.compute_graph_features(G)

        # Edge weight
        edge_weight = G[u][v].get('weight', 1.0)

        # Average edge weight
        avg_weight = np.mean([G[a][b].get('weight', 1.0) for a, b in G.edges()])

        features = [
            edge_weight,
            graph_feats['betweenness'].get(u, 0.0),
            graph_feats['betweenness'].get(v, 0.0),
            graph_feats['closeness'].get(u, 0.0),
            graph_feats['closeness'].get(v, 0.0),
            graph_feats['clustering'].get(u, 0.0),
            graph_feats['clustering'].get(v, 0.0),
            graph_feats['degree_cent'].get(u, 0.0),
            graph_feats['degree_cent'].get(v, 0.0),
            edge_weight / max(avg_weight, 0.001)  # Relative weight
        ]

        return np.array(features)

    def train_from_solutions(self, training_data: List[Tuple[nx.Graph, List]]):
        """
        Train from tour solutions

        Strategy: Use both tour order AND greedy baseline
        """
        X_train = []
        y_train = []

        for G, tour in training_data:
            # Strategy 1: If we have a valid tour, use traversal order
            if tour and len(tour) > 2:
                edge_set = set()
                for i, (u, v) in enumerate(zip(tour[:-1], tour[1:])):
                    if G.has_edge(u, v) and (u, v) not in edge_set:
                        edge_set.add((u, v))
                        edge_set.add((v, u))

                        features = self.extract_edge_features(G, (u, v))
                        # Priority = inverse of position (earlier = higher)
                        priority = len(tour) - i

                        X_train.append(features)
                        y_train.append(priority)

            # Strategy 2: For all graphs, use edge characteristics
            # High-weight short edges should be traversed early
            else:
                for u, v in G.edges():
                    features = self.extract_edge_features(G, (u, v))

                    # Heuristic priority based on features
                    # Lower weight = higher priority (traverse cheap edges first)
                    edge_weight = G[u][v].get('weight', 1.0)
                    avg_weight = np.mean([G[a][b].get('weight', 1.0) for a, b in G.edges()])
                    priority = avg_weight / max(edge_weight, 0.001)

                    X_train.append(features)
                    y_train.append(priority)

        if len(X_train) >= 10:  # Need minimum data
            X_train = np.array(X_train)
            y_train = np.array(y_train)

            # Normalize features
            X_train = self.scaler.fit_transform(X_train)

            # Train
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

        # Get all edges with predicted priorities
        edges = list(G.edges())

        # Extract features and predict priorities
        features = np.array([self.extract_edge_features(G, e) for e in edges])
        features = self.scaler.transform(features)
        priorities = self.model.predict(features)

        # Sort edges by priority (highest first)
        sorted_edges = [e for _, e in sorted(zip(priorities, edges), reverse=True)]

        # Build tour using nearest-neighbor with learned priorities
        tour = [0]
        current = 0
        total_cost = 0
        visited = set()

        # Create edge priority map
        edge_priority = {e: p for e, p in zip(edges, priorities)}

        while len(visited) < len(edges):
            # Find best unvisited edge from current position
            best_edge = None
            best_score = -float('inf')
            best_path = None

            for u, v in edges:
                if (u, v) in visited or (v, u) in visited:
                    continue

                # Score = priority - travel_cost (trade-off)
                try:
                    if current == u:
                        travel_cost = 0
                        path = [u, v]
                    elif current == v:
                        travel_cost = 0
                        path = [v, u]
                    else:
                        travel_cost = nx.shortest_path_length(G, current, u, weight='weight')
                        path = nx.shortest_path(G, current, u, weight='weight') + [v]

                    # Combine learned priority with travel cost
                    score = edge_priority.get((u, v), 0) - 0.5 * travel_cost

                    if score > best_score:
                        best_score = score
                        best_edge = (u, v)
                        best_path = path

                except nx.NetworkXNoPath:
                    continue

            if best_edge is None:
                break

            # Execute best choice
            if best_path:
                for i in range(len(best_path) - 1):
                    a, b = best_path[i], best_path[i+1]
                    if G.has_edge(a, b):
                        total_cost += G[a][b].get('weight', 1.0)
                    elif G.has_edge(b, a):
                        total_cost += G[b][a].get('weight', 1.0)

                tour.extend(best_path[1:])
                current = best_path[-1]

            visited.add(best_edge)
            visited.add((best_edge[1], best_edge[0]))

        # Return to depot
        if current != 0:
            try:
                path = nx.shortest_path(G, current, 0, weight='weight')
                tour.extend(path[1:])
                for i in range(len(path) - 1):
                    total_cost += G[path[i]][path[i+1]].get('weight', 1.0)
            except:
                pass

        metadata = {
            'method': 'improved_ml_priorities',
            'model': 'random_forest',
            'features': ['weight', 'betweenness', 'closeness', 'clustering', 'degree'],
            'num_features': 10,
            'trained': True
        }

        return total_cost, tour, metadata

    def _greedy_solve(self, G: nx.Graph) -> Tuple[float, List, Dict]:
        """Fallback greedy solver"""
        from cpp_adapters import solve_greedy_heuristic
        cost, tour = solve_greedy_heuristic(G)

        metadata = {
            'method': 'greedy_fallback',
            'ml_model': 'not_trained'
        }

        return cost, tour, metadata


if __name__ == "__main__":
    print("Improved ML-CPP loaded")
    print("Features: 10 rich graph-based features")
    print("Model: Random Forest with 50 trees")
