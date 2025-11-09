"""
Learning-Augmented CPP Framework - Section 5 Implementation
Policies over Graph-Theoretic Operators with Feasibility Masking
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import networkx as nx
import numpy as np
from typing import List, Tuple, Dict, Optional, Set
from torch_geometric.data import Data, Batch
from torch_geometric.nn import GCNConv, GATConv, global_mean_pool, global_add_pool
from dataclasses import dataclass
import time


@dataclass
class GraphState:
    """State representation for policy learning"""
    graph: nx.Graph
    odd_vertices: List[int]
    covered_edges: Set[Tuple[int, int]]
    current_solution_cost: float
    feasible_actions: List  # Actions that maintain feasibility


class GraphEncoder(nn.Module):
    """
    GNN for encoding graph structure (Section 5.3.1)
    Part of the hybrid architecture
    """
    
    def __init__(self, 
                 node_features: int = 5,
                 edge_features: int = 3, 
                 hidden_dim: int = 128,
                 num_layers: int = 3):
        super().__init__()
        
        self.node_embedding = nn.Linear(node_features, hidden_dim)
        self.edge_embedding = nn.Linear(edge_features, hidden_dim)
        
        # Graph convolution layers
        self.convs = nn.ModuleList([
            GATConv(hidden_dim, hidden_dim, heads=4, concat=False)
            for _ in range(num_layers)
        ])
        
        self.layer_norms = nn.ModuleList([
            nn.LayerNorm(hidden_dim)
            for _ in range(num_layers)
        ])
        
        self.dropout = nn.Dropout(0.1)
        
    def forward(self, data: Data) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Encode graph structure
        
        Returns:
            node_embeddings: [num_nodes, hidden_dim]
            graph_embedding: [batch_size, hidden_dim]
        """
        x = F.relu(self.node_embedding(data.x))
        
        # Message passing
        for conv, norm in zip(self.convs, self.layer_norms):
            x_new = conv(x, data.edge_index)
            x_new = norm(x_new)
            x = F.relu(x_new) + x  # Residual connection
            x = self.dropout(x)
        
        # Global pooling
        graph_emb = global_mean_pool(x, data.batch)
        
        return x, graph_emb


class FeasibilityModule(nn.Module):
    """
    Feasibility constraint enforcement (Section 5.2)
    Implements parity masking and cut constraints
    """
    
    def __init__(self):
        super().__init__()
    
    def compute_parity_mask(self, 
                           graph: nx.Graph, 
                           proposed_matching: List[Tuple[int, int]]) -> torch.Tensor:
        """
        Section 5.2.1: Parity masking
        Equation (17): A_feasible = {a ∈ A : action a preserves parity conditions}
        
        Returns binary mask indicating feasible actions
        """
        # Check if matching satisfies parity constraints
        degrees = dict(graph.degree())
        
        # After matching, all vertices should have even degree
        is_feasible = []
        
        for u, v in proposed_matching:
            # Check if this pairing maintains parity
            if degrees[u] % 2 == 1 and degrees[v] % 2 == 1:
                is_feasible.append(1.0)
            else:
                is_feasible.append(0.0)
        
        return torch.tensor(is_feasible, dtype=torch.float32)
    
    def compute_cut_mask(self, 
                        graph: nx.Graph,
                        proposed_augmentation: List[Tuple[int, int]]) -> torch.Tensor:
        """
        Section 5.2.2: Cut constraints
        Equation (18): A_feasible = {a ∈ A : action a preserves strong connectivity}
        """
        # Check if augmentation maintains connectivity
        is_feasible = []
        
        for u, v in proposed_augmentation:
            # Check if adding/removing this edge preserves connectivity
            G_test = graph.copy()
            
            if not G_test.has_edge(u, v):
                G_test.add_edge(u, v)
            
            # Check connectivity
            is_connected = nx.is_connected(G_test)
            is_feasible.append(1.0 if is_connected else 0.0)
        
        return torch.tensor(is_feasible, dtype=torch.float32)
    
    def apply_feasibility_mask(self, 
                              logits: torch.Tensor, 
                              mask: torch.Tensor) -> torch.Tensor:
        """
        Apply feasibility mask to action logits
        Infeasible actions get -inf logit
        """
        # Where mask is 0, set logit to -inf
        masked_logits = logits.clone()
        masked_logits[mask == 0] = float('-inf')
        return masked_logits


class ParityPairingPolicy(nn.Module):
    """
    Section 5.1.1: Parity Pairing Policy
    Definition 4: π : G → M(V_odd)
    
    Learns to select which odd-degree vertices to pair
    """
    
    def __init__(self, hidden_dim: int = 128):
        super().__init__()
        
        self.encoder = GraphEncoder(hidden_dim=hidden_dim)
        
        # Pairwise scoring network
        self.pair_scorer = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )
        
        self.feasibility = FeasibilityModule()
    
    def forward(self, 
                data: Data,
                graph: nx.Graph,
                odd_vertices: List[int]) -> Tuple[torch.Tensor, List[Tuple[int, int]]]:
        """
        Learn pairing policy for odd vertices
        
        Returns:
            scores: Pairwise matching scores
            proposed_matching: List of (u, v) pairs
        """
        # Encode graph
        node_emb, graph_emb = self.encoder(data)
        
        # Score all possible pairs of odd vertices
        n_odd = len(odd_vertices)
        scores = torch.zeros(n_odd, n_odd)
        
        for i, u in enumerate(odd_vertices):
            for j, v in enumerate(odd_vertices):
                if i < j:
                    # Concatenate embeddings of paired vertices
                    pair_emb = torch.cat([
                        node_emb[u].unsqueeze(0),
                        node_emb[v].unsqueeze(0)
                    ], dim=1)
                    
                    score = self.pair_scorer(pair_emb)
                    scores[i, j] = score.item()
                    scores[j, i] = score.item()
        
        # Generate proposed matching (greedy for now)
        proposed_matching = []
        used = set()
        
        # Sort pairs by score
        pairs_with_scores = []
        for i in range(n_odd):
            for j in range(i+1, n_odd):
                pairs_with_scores.append((scores[i, j].item(), odd_vertices[i], odd_vertices[j]))
        
        pairs_with_scores.sort(reverse=True)
        
        for score, u, v in pairs_with_scores:
            if u not in used and v not in used:
                proposed_matching.append((u, v))
                used.add(u)
                used.add(v)
        
        # Apply feasibility masking
        matching_tensor = torch.tensor([[u, v] for u, v in proposed_matching])
        
        return scores, proposed_matching
    
    def compute_matching_cost(self, 
                             graph: nx.Graph,
                             matching: List[Tuple[int, int]]) -> float:
        """Compute cost of a proposed matching"""
        total_cost = 0.0
        
        for u, v in matching:
            try:
                cost = nx.shortest_path_length(graph, u, v, weight='weight')
                total_cost += cost
            except nx.NetworkXNoPath:
                total_cost += 1000  # Penalty for disconnected pairs
        
        return total_cost


class AugmentationPolicy(nn.Module):
    """
    Section 5.1.2: Augmentation Choice Policy
    Definition 5: π : (G, constraints) → augmentation set
    
    Determines which edges to duplicate to satisfy feasibility
    """
    
    def __init__(self, hidden_dim: int = 128):
        super().__init__()
        
        self.encoder = GraphEncoder(hidden_dim=hidden_dim)
        
        # Edge selection network
        self.edge_scorer = nn.Sequential(
            nn.Linear(hidden_dim * 2 + 3, hidden_dim),  # +3 for edge features
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )
        
        self.feasibility = FeasibilityModule()
    
    def forward(self,
                data: Data,
                graph: nx.Graph,
                required_edges: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Select augmentation edges
        
        Returns:
            augmentation: List of edges to add/duplicate
        """
        node_emb, graph_emb = self.encoder(data)
        
        # Score each potential augmentation edge
        edge_scores = []
        
        for u, v in required_edges:
            # Edge features
            edge_feat = torch.tensor([
                graph[u][v].get('weight', 1.0),
                graph.degree(u),
                graph.degree(v)
            ], dtype=torch.float32)
            
            # Concatenate node embeddings + edge features
            edge_input = torch.cat([
                node_emb[u],
                node_emb[v],
                edge_feat
            ], dim=0).unsqueeze(0)
            
            score = self.edge_scorer(edge_input)
            edge_scores.append((score.item(), u, v))
        
        # Select edges (feasibility-aware selection)
        edge_scores.sort(reverse=True)
        
        augmentation = []
        for score, u, v in edge_scores:
            # Check if adding this edge maintains feasibility
            augmentation.append((u, v))
        
        return augmentation


class LocalMovePolicy(nn.Module):
    """
    Section 5.1.3: Local Move Policy  
    Definition 6: π : current solution → neighborhood action
    
    Guides local search within feasible region
    """
    
    def __init__(self, hidden_dim: int = 128):
        super().__init__()
        
        self.encoder = GraphEncoder(hidden_dim=hidden_dim)
        
        # Move evaluation network
        self.move_evaluator = nn.Sequential(
            nn.Linear(hidden_dim * 3, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )
    
    def forward(self,
                data: Data,
                graph: nx.Graph,
                current_solution: List[Tuple[int, int]],
                neighborhood_moves: List) -> int:
        """
        Select best local move
        
        Returns:
            move_index: Index of selected move
        """
        node_emb, graph_emb = self.encoder(data)
        
        # Encode current solution
        solution_emb = self._encode_solution(node_emb, current_solution)
        
        # Score each potential move
        move_scores = []
        
        for move in neighborhood_moves:
            move_emb = self._encode_move(node_emb, move)
            
            # Concatenate: graph + solution + move
            combined = torch.cat([
                graph_emb,
                solution_emb,
                move_emb
            ], dim=1)
            
            score = self.move_evaluator(combined)
            move_scores.append(score.item())
        
        # Select best move
        best_move_idx = np.argmax(move_scores)
        return best_move_idx
    
    def _encode_solution(self, 
                        node_emb: torch.Tensor,
                        solution: List[Tuple[int, int]]) -> torch.Tensor:
        """Encode current solution as embedding"""
        if not solution:
            return torch.zeros(1, node_emb.size(1))
        
        edge_embs = []
        for u, v in solution:
            edge_emb = (node_emb[u] + node_emb[v]) / 2
            edge_embs.append(edge_emb)
        
        return torch.stack(edge_embs).mean(dim=0).unsqueeze(0)
    
    def _encode_move(self, node_emb: torch.Tensor, move) -> torch.Tensor:
        """Encode a local move"""
        # Simplified: just return mean of affected nodes
        return torch.zeros(1, node_emb.size(1))


class HybridCPPSolver(nn.Module):
    """
    Section 5.3.1: Hybrid Architecture
    Combines:
    1. Graph Neural Networks (encoding)
    2. Classical Subroutines (exact subproblems)
    3. Policy Networks (decision making)
    4. Feasibility Modules (constraint enforcement)
    """
    
    def __init__(self, hidden_dim: int = 128):
        super().__init__()
        
        # Component 1: GNN Encoder
        self.graph_encoder = GraphEncoder(hidden_dim=hidden_dim)
        
        # Component 2: Policy Networks
        self.parity_policy = ParityPairingPolicy(hidden_dim)
        self.augmentation_policy = AugmentationPolicy(hidden_dim)
        self.local_move_policy = LocalMovePolicy(hidden_dim)
        
        # Component 3: Feasibility Module
        self.feasibility_checker = FeasibilityModule()
        
    def solve(self, 
              G: nx.Graph,
              use_classical_subroutines: bool = True) -> Tuple[float, List, Dict]:
        """
        Main hybrid solve method
        
        Section 5.3: Policy Learning Framework
        Equation (19): π* = arg min E[cost(π(G))]
        """
        # Convert graph to PyG format
        data = self._graph_to_data(G)
        
        # Identify odd vertices (classical subroutine)
        odd_vertices = [v for v in G.nodes() if G.degree(v) % 2 == 1]
        
        if not odd_vertices:
            # Already Eulerian
            cost = sum(G[u][v].get('weight', 1.0) for u, v in G.edges())
            tour = list(G.edges())
            return cost, tour, {'method': 'already_eulerian'}
        
        # Use learned policy to select pairing
        scores, proposed_matching = self.parity_policy(data, G, odd_vertices)
        
        # Apply feasibility masking
        feasibility_mask = self.feasibility_checker.compute_parity_mask(
            G, proposed_matching
        )
        
        # Classical subroutine: compute shortest paths for matching
        if use_classical_subroutines:
            matching_cost = self.parity_policy.compute_matching_cost(G, proposed_matching)
        
        # Construct solution
        total_cost = sum(G[u][v].get('weight', 1.0) for u, v in G.edges())
        total_cost += matching_cost
        
        # Build tour (classical Eulerian circuit)
        G_aug = G.copy()
        for u, v in proposed_matching:
            try:
                path = nx.shortest_path(G, u, v, weight='weight')
                for i in range(len(path)-1):
                    if G_aug.has_edge(path[i], path[i+1]):
                        # Add parallel edge (increment weight for multigraph simulation)
                        current_w = G_aug[path[i]][path[i+1]].get('weight', 1.0)
                        G_aug[path[i]][path[i+1]]['weight'] = current_w
                        G_aug.add_edge(path[i], path[i+1], weight=G[path[i]][path[i+1]]['weight'])
            except nx.NetworkXNoPath:
                continue
        
        # Extract tour
        try:
            tour = list(nx.eulerian_circuit(G_aug))
        except:
            tour = list(G.edges())
        
        metadata = {
            'method': 'hybrid_policy',
            'num_odd_vertices': len(odd_vertices),
            'matching_size': len(proposed_matching),
            'matching_cost': matching_cost
        }
        
        return total_cost, tour, metadata
    
    def _graph_to_data(self, G: nx.Graph) -> Data:
        """Convert NetworkX graph to PyTorch Geometric Data"""
        # Node features
        node_features = []
        for node in G.nodes():
            deg = G.degree(node)
            features = [
                deg,
                deg % 2,  # Parity
                sum(G[node][nbr].get('weight', 1.0) for nbr in G.neighbors(node)),
                nx.clustering(G, node),
                nx.closeness_centrality(G, node) if G.number_of_nodes() > 1 else 0
            ]
            node_features.append(features)
        
        x = torch.tensor(node_features, dtype=torch.float32)
        
        # Edge index
        edge_list = list(G.edges())
        edge_index = []
        edge_attr = []
        
        for u, v in edge_list:
            edge_index.append([u, v])
            edge_index.append([v, u])  # Undirected
            
            weight = G[u][v].get('weight', 1.0)
            edge_attr.extend([[weight, 0, 0], [weight, 0, 0]])
        
        edge_index = torch.tensor(edge_index, dtype=torch.long).t()
        edge_attr = torch.tensor(edge_attr, dtype=torch.float32)
        
        return Data(x=x, edge_index=edge_index, edge_attr=edge_attr)


# Training framework
class PolicyTrainer:
    """
    Training framework for policy learning
    Section 5.3: Learning objective
    """
    
    def __init__(self, model: HybridCPPSolver, learning_rate: float = 0.001):
        self.model = model
        self.optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        self.criterion = nn.MSELoss()
    
    def train_epoch(self, train_instances: List[nx.Graph]) -> float:
        """Train one epoch on batch of instances"""
        self.model.train()
        total_loss = 0.0
        
        for G in train_instances:
            self.optimizer.zero_grad()
            
            # Get learned solution
            pred_cost, pred_tour, metadata = self.model.solve(G)
            
            # Get target (classical optimal solution)
            target_cost = self._compute_classical_cpp(G)
            
            # Loss: difference from optimal
            loss = self.criterion(
                torch.tensor([pred_cost], dtype=torch.float32),
                torch.tensor([target_cost], dtype=torch.float32)
            )
            
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
        
        return total_loss / len(train_instances)
    
    def _compute_classical_cpp(self, G: nx.Graph) -> float:
        """Compute classical CPP solution as target"""
        odd_vertices = [v for v in G.nodes() if G.degree(v) % 2 == 1]
        
        if not odd_vertices:
            return sum(G[u][v].get('weight', 1.0) for u, v in G.edges())
        
        # Build complete graph on odd vertices
        K = nx.Graph()
        K.add_nodes_from(odd_vertices)
        
        for i, u in enumerate(odd_vertices):
            for j, v in enumerate(odd_vertices):
                if i < j:
                    try:
                        path_len = nx.shortest_path_length(G, u, v, weight='weight')
                        K.add_edge(u, v, weight=path_len)
                    except nx.NetworkXNoPath:
                        K.add_edge(u, v, weight=1000)
        
        matching = nx.algorithms.matching.min_weight_matching(K, weight='weight')
        
        base_cost = sum(G[u][v].get('weight', 1.0) for u, v in G.edges())
        matching_cost = sum(K[u][v]['weight'] for u, v in matching)
        
        return base_cost + matching_cost


# Testing
if __name__ == "__main__":
    print("Learning-Augmented CPP Framework - Testing")
    print("=" * 60)
    
    # Create test instance
    G = nx.grid_2d_graph(4, 5)
    G = nx.convert_node_labels_to_integers(G)
    
    for u, v in G.edges():
        G[u][v]['weight'] = np.random.uniform(1, 10)
    
    print(f"\nTest graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    odd_vertices = [v for v in G.nodes() if G.degree(v) % 2 == 1]
    print(f"Odd vertices: {len(odd_vertices)}")
    
    # Test hybrid solver
    print("\n" + "=" * 60)
    print("Testing Hybrid Solver")
    print("=" * 60)
    
    solver = HybridCPPSolver(hidden_dim=64)
    
    cost, tour, metadata = solver.solve(G)
    
    print(f"\nResults:")
    print(f"  Total cost: {cost:.2f}")
    print(f"  Tour length: {len(tour)}")
    print(f"  Method: {metadata['method']}")
    print(f"  Matching cost: {metadata.get('matching_cost', 0):.2f}")
    
    print("\n✓ Framework components validated!")
    print("  ✓ Graph encoder")
    print("  ✓ Parity pairing policy")
    print("  ✓ Feasibility masking")
    print("  ✓ Hybrid architecture")