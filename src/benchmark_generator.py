"""
Comprehensive Benchmark Dataset Generator for CPP Research
Generates reproducible instances across 4 network families
"""

import numpy as np
import networkx as nx
import json
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
from datetime import datetime


class NetworkFamily(Enum):
    """Types of network topologies"""
    GRID = "grid"
    RANDOM_GEOMETRIC = "random_geometric"
    CLUSTERED = "clustered"
    OSM_DERIVED = "osm_derived"


class GraphSize(Enum):
    """Standardized graph sizes"""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


@dataclass
class InstanceMetadata:
    """Metadata for each benchmark instance"""
    instance_id: str
    network_family: str
    size: str
    num_nodes: int
    num_edges: int
    density: float
    avg_degree: float
    clustering_coeff: float
    diameter: int
    is_connected: bool
    generation_timestamp: str
    random_seed: int
    parameters: Dict
    
    def to_dict(self):
        return asdict(self)


@dataclass
class CPPInstance:
    """Complete CPP instance with all variants"""
    graph: nx.Graph
    metadata: InstanceMetadata
    
    # CPP-LC (Load-Dependent Costs) data
    edge_demands: Optional[Dict] = None
    vehicle_capacity: Optional[float] = None
    cost_function: Optional[str] = None
    
    # CPP-TW (Time Windows) data
    time_windows: Optional[Dict] = None
    service_times: Optional[Dict] = None
    travel_times: Optional[Dict] = None
    
    # Mixed CPP data
    edge_types: Optional[Dict] = None  # directed/undirected
    
    # Windy Postman data
    directional_costs: Optional[Dict] = None


class BenchmarkGenerator:
    """
    Main class for generating reproducible benchmark datasets
    """
    
    def __init__(self, output_dir: str = "benchmarks", base_seed: int = 42):
        self.output_dir = Path(output_dir)
        self.base_seed = base_seed
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        for family in NetworkFamily:
            (self.output_dir / family.value).mkdir(exist_ok=True)
        
        self.instances = []
        
    def generate_full_suite(self, instances_per_config: int = 10) -> List[CPPInstance]:
        """
        Generate complete benchmark suite across all network families
        
        Args:
            instances_per_config: Number of instances per configuration
            
        Returns:
            List of all generated instances
        """
        print("=" * 70)
        print("GENERATING COMPLETE BENCHMARK SUITE")
        print("=" * 70)
        
        all_instances = []
        
        # Generate each network family
        for family in NetworkFamily:
            if family == NetworkFamily.OSM_DERIVED:
                # OSM requires special handling (download real data)
                print(f"\n⚠️  {family.value}: Requires manual OSM download")
                print("    We'll create placeholder for now, implement OSM loader separately")
                continue
            
            print(f"\n📊 Generating {family.value} instances...")
            
            for size in GraphSize:
                print(f"  Size: {size.value}")
                
                for seed_offset in range(instances_per_config):
                    seed = self.base_seed + seed_offset
                    
                    try:
                        # Generate base graph
                        G = self._generate_network(family, size, seed)
                        
                        # Create instance with metadata
                        instance = self._create_instance(G, family, size, seed)
                        
                        # Add variant-specific data
                        self._add_cpp_lc_data(instance, seed)
                        self._add_cpp_tw_data(instance, seed)
                        self._add_mixed_cpp_data(instance, seed)
                        self._add_windy_data(instance, seed)
                        
                        # Save instance
                        self._save_instance(instance)
                        
                        all_instances.append(instance)
                        self.instances.append(instance)
                        
                        if (seed_offset + 1) % 5 == 0:
                            print(f"    ✓ Generated {seed_offset + 1}/{instances_per_config}")
                    
                    except Exception as e:
                        print(f"    ✗ Error generating instance (seed={seed}): {e}")
        
        print(f"\n✅ Total instances generated: {len(all_instances)}")
        
        # Generate summary report
        self._generate_summary_report(all_instances)
        
        return all_instances
    
    def _generate_network(self, family: NetworkFamily, size: GraphSize, seed: int) -> nx.Graph:
        """Generate base network topology"""
        np.random.seed(seed)
        
        if family == NetworkFamily.GRID:
            return self._generate_grid(size)
        elif family == NetworkFamily.RANDOM_GEOMETRIC:
            return self._generate_random_geometric(size, seed)
        elif family == NetworkFamily.CLUSTERED:
            return self._generate_clustered(size, seed)
        else:
            raise ValueError(f"Unknown network family: {family}")
    
    def _generate_grid(self, size: GraphSize) -> nx.Graph:
        """Generate grid graph"""
        size_map = {
            GraphSize.SMALL: (5, 5),
            GraphSize.MEDIUM: (10, 10),
            GraphSize.LARGE: (20, 20)
        }
        
        rows, cols = size_map[size]
        G = nx.grid_2d_graph(rows, cols)
        
        # Convert to standard graph with integer nodes
        H = nx.Graph()
        node_mapping = {node: i for i, node in enumerate(G.nodes())}
        H.add_nodes_from(range(len(node_mapping)))
        
        # Add edges with random weights
        for u, v in G.edges():
            u_idx = node_mapping[u]
            v_idx = node_mapping[v]
            weight = np.random.uniform(1.0, 10.0)
            H.add_edge(u_idx, v_idx, weight=weight)
        
        return H
    
    def _generate_random_geometric(self, size: GraphSize, seed: int) -> nx.Graph:
        """Generate random geometric graph"""
        size_map = {
            GraphSize.SMALL: (50, 0.25),
            GraphSize.MEDIUM: (100, 0.18),
            GraphSize.LARGE: (200, 0.13)
        }
        
        n, radius = size_map[size]
        
        # Generate with connectivity guarantee
        max_attempts = 10
        for attempt in range(max_attempts):
            G = nx.random_geometric_graph(n, radius, seed=seed + attempt)
            if nx.is_connected(G):
                break
        else:
            # Force connectivity by adding edges
            G = nx.random_geometric_graph(n, radius, seed=seed)
            components = list(nx.connected_components(G))
            for i in range(len(components) - 1):
                u = list(components[i])[0]
                v = list(components[i + 1])[0]
                G.add_edge(u, v)
        
        # Add random weights
        for u, v in G.edges():
            weight = np.random.uniform(1.0, 10.0)
            G[u][v]['weight'] = weight
        
        return G
    
    def _generate_clustered(self, size: GraphSize, seed: int) -> nx.Graph:
        """Generate clustered graph with community structure"""
        size_map = {
            GraphSize.SMALL: (5, 10),    # 5 clusters, 10 nodes each
            GraphSize.MEDIUM: (10, 10),  # 10 clusters, 10 nodes each
            GraphSize.LARGE: (20, 10)    # 20 clusters, 10 nodes each
        }
        
        num_clusters, nodes_per_cluster = size_map[size]
        
        # Parameters for community structure
        p_in = 0.7   # Probability of intra-cluster edge
        p_out = 0.1  # Probability of inter-cluster edge
        
        # Generate stochastic block model
        sizes = [nodes_per_cluster] * num_clusters
        probs = [[p_in if i == j else p_out for j in range(num_clusters)] 
                 for i in range(num_clusters)]
        
        G_temp = nx.stochastic_block_model(sizes, probs, seed=seed)
        
        # Convert to plain graph (removes node attributes like 'block')
        G = nx.Graph()
        G.add_nodes_from(G_temp.nodes())
        G.add_edges_from(G_temp.edges())
        
        # Ensure connectivity
        if not nx.is_connected(G):
            components = list(nx.connected_components(G))
            for i in range(len(components) - 1):
                u = list(components[i])[0]
                v = list(components[i + 1])[0]
                G.add_edge(u, v)
        
        # Add random weights
        for u, v in G.edges():
            weight = np.random.uniform(1.0, 10.0)
            G[u][v]['weight'] = weight
        
        return G
    
    def _create_instance(self, G: nx.Graph, family: NetworkFamily, 
                        size: GraphSize, seed: int) -> CPPInstance:
        """Create CPP instance with metadata"""
        
        # Compute graph statistics
        n = G.number_of_nodes()
        m = G.number_of_edges()
        density = (2 * m) / (n * (n - 1)) if n > 1 else 0
        avg_degree = sum(dict(G.degree()).values()) / n if n > 0 else 0
        clustering = nx.average_clustering(G)
        
        try:
            diameter = nx.diameter(G) if nx.is_connected(G) else -1
        except:
            diameter = -1
        
        # Generate unique instance ID
        instance_id = self._generate_instance_id(family, size, seed)
        
        metadata = InstanceMetadata(
            instance_id=instance_id,
            network_family=family.value,
            size=size.value,
            num_nodes=n,
            num_edges=m,
            density=density,
            avg_degree=avg_degree,
            clustering_coeff=clustering,
            diameter=diameter,
            is_connected=nx.is_connected(G),
            generation_timestamp=datetime.now().isoformat(),
            random_seed=seed,
            parameters={}
        )
        
        return CPPInstance(graph=G, metadata=metadata)
    
    def _add_cpp_lc_data(self, instance: CPPInstance, seed: int):
        """Add Load-Dependent Cost variant data"""
        np.random.seed(seed)
        G = instance.graph
        
        # Generate edge demands
        edge_demands = {}
        for u, v in G.edges():
            demand = np.random.uniform(5.0, 20.0)
            edge_demands[(u, v)] = demand
            edge_demands[(v, u)] = demand  # Symmetric
        
        # Calculate total demand
        total_demand = sum(edge_demands.values()) / 2  # Divide by 2 for symmetric
        
        # Vehicle capacity (40% of total demand - tight constraint)
        vehicle_capacity = total_demand * 0.4
        
        instance.edge_demands = edge_demands
        instance.vehicle_capacity = vehicle_capacity
        instance.cost_function = "linear"  # Default, can vary
        
        instance.metadata.parameters['cpp_lc'] = {
            'total_demand': total_demand,
            'capacity': vehicle_capacity,
            'capacity_ratio': 0.4
        }
    
    def _add_cpp_tw_data(self, instance: CPPInstance, seed: int):
        """Add Time Windows variant data"""
        np.random.seed(seed + 1000)
        G = instance.graph
        
        # Generate time windows for each edge
        time_windows = {}
        service_times = {}
        
        # Tightness factor (1.0 = medium, <1 = tight, >1 = loose)
        tightness = 1.0
        
        for u, v in G.edges():
            # Service time (time to traverse edge)
            service_time = G[u][v].get('weight', 1.0)
            service_times[(u, v)] = service_time
            
            # Time window [earliest, latest]
            earliest = np.random.uniform(0, 100)
            window_width = service_time * tightness * np.random.uniform(2, 10)
            latest = earliest + window_width
            
            time_windows[(u, v)] = (earliest, latest)
        
        instance.time_windows = time_windows
        instance.service_times = service_times
        
        instance.metadata.parameters['cpp_tw'] = {
            'tightness': tightness,
            'num_windows': len(time_windows)
        }
    
    def _add_mixed_cpp_data(self, instance: CPPInstance, seed: int):
        """Add Mixed CPP variant data (directed/undirected edges)"""
        np.random.seed(seed + 2000)
        G = instance.graph
        
        # Randomly designate edges as directed or undirected
        directed_fraction = 0.4  # 40% of edges are directed
        
        edge_types = {}
        for u, v in G.edges():
            is_directed = np.random.random() < directed_fraction
            edge_types[(u, v)] = {
                'is_directed': is_directed,
                'weight': G[u][v].get('weight', 1.0)
            }
        
        instance.edge_types = edge_types
        
        instance.metadata.parameters['mixed_cpp'] = {
            'directed_fraction': directed_fraction,
            'num_directed': sum(1 for e in edge_types.values() if e['is_directed'])
        }
    
    def _add_windy_data(self, instance: CPPInstance, seed: int):
        """Add Windy Postman variant data (directional costs)"""
        np.random.seed(seed + 3000)
        G = instance.graph
        
        # Asymmetry factor (0 = symmetric, 1 = fully asymmetric)
        asymmetry = 0.6
        
        directional_costs = {}
        for u, v in G.edges():
            base_cost = G[u][v].get('weight', 1.0)
            
            # Cost in u->v direction
            cost_uv = base_cost
            
            # Cost in v->u direction (asymmetric)
            if np.random.random() < asymmetry:
                cost_vu = base_cost * np.random.uniform(0.5, 2.0)
            else:
                cost_vu = base_cost
            
            directional_costs[(u, v)] = cost_uv
            directional_costs[(v, u)] = cost_vu
        
        instance.directional_costs = directional_costs
        
        instance.metadata.parameters['windy'] = {
            'asymmetry_factor': asymmetry
        }
    
    def _generate_instance_id(self, family: NetworkFamily, size: GraphSize, seed: int) -> str:
        """Generate unique instance identifier"""
        base_string = f"{family.value}_{size.value}_{seed}"
        hash_suffix = hashlib.md5(base_string.encode()).hexdigest()[:8]
        return f"{family.value}_{size.value}_{seed:04d}_{hash_suffix}"
    
    def _save_instance(self, instance: CPPInstance):
        """Save instance to disk"""
        family_dir = self.output_dir / instance.metadata.network_family
        instance_id = instance.metadata.instance_id
        
        # Create a copy of the graph for GraphML export (remove position data)
        G_export = instance.graph.copy()
        
        # Remove 'pos' attribute if it exists (GraphML doesn't support list values)
        for node in G_export.nodes():
            if 'pos' in G_export.nodes[node]:
                del G_export.nodes[node]['pos']
        
        # Save graph as GraphML (human-readable)
        graphml_path = family_dir / f"{instance_id}.graphml"
        nx.write_graphml(G_export, graphml_path)
        
        # Save complete instance as pickle (includes all data, including positions)
        pickle_path = family_dir / f"{instance_id}.pkl"
        with open(pickle_path, 'wb') as f:
            pickle.dump(instance, f)
        
        # Save metadata as JSON (human-readable)
        json_path = family_dir / f"{instance_id}_metadata.json"
        with open(json_path, 'w') as f:
            json.dump(instance.metadata.to_dict(), f, indent=2)
    
    def _generate_summary_report(self, instances: List[CPPInstance]):
        """Generate summary statistics report"""
        report = []
        report.append("# Benchmark Dataset Summary Report\n")
        report.append(f"Generated: {datetime.now().isoformat()}\n")
        report.append(f"Total instances: {len(instances)}\n\n")
        
        # Group by family and size
        from collections import defaultdict
        stats = defaultdict(lambda: defaultdict(list))
        
        for inst in instances:
            family = inst.metadata.network_family
            size = inst.metadata.size
            stats[family][size].append(inst.metadata)
        
        # Generate statistics table
        report.append("## Instance Breakdown\n\n")
        report.append("| Family | Size | Count | Avg Nodes | Avg Edges | Avg Density |\n")
        report.append("|--------|------|-------|-----------|-----------|-------------|\n")
        
        for family in sorted(stats.keys()):
            for size in sorted(stats[family].keys()):
                metas = stats[family][size]
                count = len(metas)
                avg_nodes = np.mean([m.num_nodes for m in metas])
                avg_edges = np.mean([m.num_edges for m in metas])
                avg_density = np.mean([m.density for m in metas])
                
                report.append(f"| {family} | {size} | {count} | {avg_nodes:.1f} | "
                            f"{avg_edges:.1f} | {avg_density:.3f} |\n")
        
        report.append("\n## Graph Statistics\n\n")
        all_metas = [inst.metadata for inst in instances]
        
        report.append(f"- Total nodes: {sum(m.num_nodes for m in all_metas)}\n")
        report.append(f"- Total edges: {sum(m.num_edges for m in all_metas)}\n")
        report.append(f"- Avg clustering: {np.mean([m.clustering_coeff for m in all_metas]):.3f}\n")
        report.append(f"- Connected graphs: {sum(m.is_connected for m in all_metas)}/{len(all_metas)}\n")
        
        # Save report
        with open(self.output_dir / "BENCHMARK_SUMMARY.md", 'w') as f:
            f.writelines(report)
        
        print("\n" + "".join(report))
    
    def load_instance(self, instance_id: str) -> CPPInstance:
        """Load a saved instance"""
        # Search all family directories
        for family in NetworkFamily:
            pickle_path = self.output_dir / family.value / f"{instance_id}.pkl"
            if pickle_path.exists():
                with open(pickle_path, 'rb') as f:
                    return pickle.load(f)
        
        raise FileNotFoundError(f"Instance {instance_id} not found")
    
    def get_instance_list(self, family: Optional[NetworkFamily] = None, 
                         size: Optional[GraphSize] = None) -> List[str]:
        """Get list of instance IDs matching criteria"""
        instance_ids = []
        
        families = [family] if family else list(NetworkFamily)
        
        for fam in families:
            fam_dir = self.output_dir / fam.value
            if not fam_dir.exists():
                continue
            
            for pkl_file in fam_dir.glob("*.pkl"):
                instance_id = pkl_file.stem
                
                # Filter by size if specified
                if size and size.value not in instance_id:
                    continue
                
                instance_ids.append(instance_id)
        
        return sorted(instance_ids)


def generate_parameter_sweep_instances(output_dir: str = "benchmarks_sweep"):
    """
    Generate instances with systematic parameter sweeps
    For detailed experimental analysis
    """
    generator = BenchmarkGenerator(output_dir=output_dir)
    
    print("=" * 70)
    print("GENERATING PARAMETER SWEEP BENCHMARK")
    print("=" * 70)
    
    all_instances = []
    
    # CPP-LC: Vary capacity and cost function
    capacity_ratios = [0.3, 0.5, 0.8]  # Tight, medium, loose
    cost_functions = ['linear', 'quadratic', 'fuel']
    
    # CPP-TW: Vary time window tightness
    tightness_values = [0.5, 1.0, 1.5, 2.0]
    
    # Mixed CPP: Vary directed fraction
    directed_fractions = [0.2, 0.4, 0.6, 0.8]
    
    # Windy: Vary asymmetry
    asymmetry_values = [0.3, 0.5, 0.7]
    
    print("\n📊 This will generate instances for comprehensive parameter analysis")
    print(f"   Capacity ratios: {capacity_ratios}")
    print(f"   Tightness values: {tightness_values}")
    print(f"   Directed fractions: {directed_fractions}")
    print(f"   Asymmetry values: {asymmetry_values}")
    
    # TODO: Implement parameter sweep generation
    # This would create instances with systematic variation of parameters
    
    return all_instances


if __name__ == "__main__":
    # Generate complete benchmark suite
    generator = BenchmarkGenerator(output_dir="benchmarks")
    instances = generator.generate_full_suite(instances_per_config=10)
    
    print(f"\n✅ Benchmark generation complete!")
    print(f"   Total instances: {len(instances)}")
    print(f"   Saved to: {generator.output_dir}")
    print(f"\n📊 Summary report: {generator.output_dir}/BENCHMARK_SUMMARY.md")
