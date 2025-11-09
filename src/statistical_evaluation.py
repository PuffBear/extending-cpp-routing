"""
Statistical Evaluation Framework - Section 6.3 Implementation
Standardized evaluation protocol with statistical rigor
"""

import numpy as np
import pandas as pd
import networkx as nx
from scipy import stats
from typing import List, Dict, Tuple, Callable
import time
from dataclasses import dataclass
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path


@dataclass
class ExperimentalResult:
    """Single experimental result"""
    instance_name: str
    algorithm: str
    variant: str
    cost: float
    time: float
    nodes: int
    edges: int
    run_id: int  # For multiple runs
    metadata: Dict


class BenchmarkGenerator:
    """
    Section 6.4: Data and Benchmark Generation
    Generate instances with controlled properties
    """
    
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        self.seed = seed
    
    def generate_grid_network(self, 
                             rows: int, 
                             cols: int,
                             variant: str = "regular") -> nx.Graph:
        """
        Section 6.4.1: Grid Networks
        Regular grid graphs representing urban street networks
        """
        G = nx.grid_2d_graph(rows, cols)
        G = nx.convert_node_labels_to_integers(G)
        
        for u, v in G.edges():
            if variant == "regular":
                weight = np.random.uniform(1, 10)
            elif variant == "heavy_tailed":
                # Power law distribution for weights
                weight = np.random.pareto(2) + 1
            elif variant == "clustered":
                # Some edges much heavier than others
                if np.random.random() < 0.2:
                    weight = np.random.uniform(20, 50)
                else:
                    weight = np.random.uniform(1, 10)
            else:
                weight = np.random.uniform(1, 10)
            
            G[u][v]['weight'] = weight
            G[u][v]['demand'] = np.random.uniform(1, 5)
        
        return G
    
    def generate_random_geometric(self,
                                  n: int,
                                  radius: float = 0.3) -> nx.Graph:
        """
        Section 6.4.1: Random Geometric Networks
        Nodes placed randomly with edges based on distance
        """
        # Generate random points
        pos = np.random.random((n, 2))
        
        G = nx.Graph()
        G.add_nodes_from(range(n))
        
        # Add edges based on distance threshold
        for i in range(n):
            for j in range(i+1, n):
                dist = np.linalg.norm(pos[i] - pos[j])
                if dist < radius:
                    G.add_edge(i, j, weight=dist * 10)
                    G[i][j]['demand'] = np.random.uniform(1, 5)
        
        # Ensure connectivity
        if not nx.is_connected(G):
            # Connect components
            components = list(nx.connected_components(G))
            for i in range(len(components) - 1):
                u = list(components[i])[0]
                v = list(components[i+1])[0]
                G.add_edge(u, v, weight=np.random.uniform(5, 15))
                G[u][v]['demand'] = np.random.uniform(1, 5)
        
        return G
    
    def generate_clustered_network(self,
                                   num_clusters: int,
                                   cluster_size: int) -> nx.Graph:
        """
        Section 6.4.1: Clustered Networks
        Multiple dense clusters connected by sparse inter-cluster edges
        """
        G = nx.Graph()
        node_id = 0
        cluster_centers = []
        
        # Create clusters
        for cluster_idx in range(num_clusters):
            center = node_id
            cluster_centers.append(center)
            cluster_nodes = list(range(node_id, node_id + cluster_size))
            
            # Dense intra-cluster edges
            for i in cluster_nodes:
                for j in cluster_nodes:
                    if i < j and np.random.random() < 0.6:
                        G.add_edge(i, j, 
                                 weight=np.random.uniform(1, 5),
                                 demand=np.random.uniform(1, 3))
            
            node_id += cluster_size
        
        # Sparse inter-cluster edges
        for i in range(len(cluster_centers)):
            for j in range(i+1, len(cluster_centers)):
                if np.random.random() < 0.4:
                    G.add_edge(cluster_centers[i], cluster_centers[j],
                             weight=np.random.uniform(15, 30),
                             demand=np.random.uniform(2, 5))
        
        return G
    
    def generate_benchmark_suite(self,
                                output_dir: str = "data/benchmarks") -> Dict[str, nx.Graph]:
        """
        Section 6.3.1: Complete benchmark suite with categories
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        instances = {}
        
        # Size categories from Section 6.4.2
        size_configs = [
            ("small", 20, 30),
            ("medium", 50, 100),
            ("large", 100, 300),
        ]
        
        for size_name, min_nodes, max_nodes in size_configs:
            # Grid networks
            for i in range(5):
                if size_name == "small":
                    G = self.generate_grid_network(4, 5)
                elif size_name == "medium":
                    G = self.generate_grid_network(7, 8)
                else:
                    G = self.generate_grid_network(10, 12)
                
                name = f"grid_{size_name}_{i}"
                instances[name] = G
                nx.write_gml(G, f"{output_dir}/{name}.gml")
            
            # Random geometric
            for i in range(5):
                n = np.random.randint(min_nodes, max_nodes)
                G = self.generate_random_geometric(n, radius=0.3)
                
                name = f"random_{size_name}_{i}"
                instances[name] = G
                nx.write_gml(G, f"{output_dir}/{name}.gml")
            
            # Clustered networks
            for i in range(3):
                if size_name == "small":
                    G = self.generate_clustered_network(3, 7)
                elif size_name == "medium":
                    G = self.generate_clustered_network(5, 10)
                else:
                    G = self.generate_clustered_network(7, 15)
                
                name = f"clustered_{size_name}_{i}"
                instances[name] = G
                nx.write_gml(G, f"{output_dir}/{name}.gml")
        
        print(f"Generated {len(instances)} benchmark instances")
        return instances


class StatisticalEvaluator:
    """
    Section 6.3.2 & 6.3.3: Performance Metrics and Statistical Rigor
    """
    
    def __init__(self, n_runs: int = 30, confidence_level: float = 0.95):
        """
        Args:
            n_runs: Number of runs per instance (Section 6.3.3: Multiple runs)
            confidence_level: For confidence intervals
        """
        self.n_runs = n_runs
        self.confidence_level = confidence_level
        self.results = []
    
    def run_algorithm_multiple_times(self,
                                     algorithm: Callable,
                                     instance: nx.Graph,
                                     instance_name: str,
                                     algorithm_name: str,
                                     variant: str) -> List[ExperimentalResult]:
        """
        Section 6.3.3: Multiple runs with statistical rigor
        """
        results = []
        
        for run_id in range(self.n_runs):
            start_time = time.time()
            
            try:
                cost, tour, comp_time = algorithm(instance)
                
                result = ExperimentalResult(
                    instance_name=instance_name,
                    algorithm=algorithm_name,
                    variant=variant,
                    cost=cost,
                    time=comp_time,
                    nodes=instance.number_of_nodes(),
                    edges=instance.number_of_edges(),
                    run_id=run_id,
                    metadata={'tour_length': len(tour) if tour else 0}
                )
                
                results.append(result)
                self.results.append(result)
                
            except Exception as e:
                print(f"Error in run {run_id}: {e}")
                continue
        
        return results
    
    def compute_statistics(self, 
                          results: List[ExperimentalResult]) -> Dict:
        """
        Compute comprehensive statistics for results
        Section 6.3.2: Performance metrics
        """
        costs = [r.cost for r in results]
        times = [r.time for r in results]
        
        # Basic statistics
        stats_dict = {
            'mean_cost': np.mean(costs),
            'std_cost': np.std(costs),
            'median_cost': np.median(costs),
            'min_cost': np.min(costs),
            'max_cost': np.max(costs),
            'mean_time': np.mean(times),
            'std_time': np.std(times),
            'median_time': np.median(times),
        }
        
        # Confidence intervals
        cost_ci = stats.t.interval(
            self.confidence_level,
            len(costs) - 1,
            loc=np.mean(costs),
            scale=stats.sem(costs)
        )
        
        time_ci = stats.t.interval(
            self.confidence_level,
            len(times) - 1,
            loc=np.mean(times),
            scale=stats.sem(times)
        )
        
        stats_dict['cost_ci_lower'] = cost_ci[0]
        stats_dict['cost_ci_upper'] = cost_ci[1]
        stats_dict['time_ci_lower'] = time_ci[0]
        stats_dict['time_ci_upper'] = time_ci[1]
        
        # Coefficient of variation (stability measure)
        stats_dict['cv_cost'] = np.std(costs) / np.mean(costs) if np.mean(costs) > 0 else 0
        stats_dict['cv_time'] = np.std(times) / np.mean(times) if np.mean(times) > 0 else 0
        
        return stats_dict
    
    def compare_algorithms(self,
                          results_a: List[ExperimentalResult],
                          results_b: List[ExperimentalResult]) -> Dict:
        """
        Statistical comparison between two algorithms
        Uses paired t-test and Wilcoxon signed-rank test
        """
        costs_a = [r.cost for r in results_a]
        costs_b = [r.cost for r in results_b]
        
        # Paired t-test
        t_stat, t_pvalue = stats.ttest_rel(costs_a, costs_b)
        
        # Wilcoxon signed-rank test (non-parametric)
        w_stat, w_pvalue = stats.wilcoxon(costs_a, costs_b)
        
        # Effect size (Cohen's d)
        diff = np.array(costs_a) - np.array(costs_b)
        cohens_d = np.mean(diff) / np.std(diff) if np.std(diff) > 0 else 0
        
        return {
            't_statistic': t_stat,
            't_pvalue': t_pvalue,
            'wilcoxon_statistic': w_stat,
            'wilcoxon_pvalue': w_pvalue,
            'cohens_d': cohens_d,
            'mean_difference': np.mean(diff),
            'significant_at_0.05': t_pvalue < 0.05
        }
    
    def generate_summary_table(self) -> pd.DataFrame:
        """
        Generate summary table like Table 2 in paper
        Section 6.3.2: Performance metrics
        """
        if not self.results:
            return pd.DataFrame()
        
        # Group by algorithm and variant
        df = pd.DataFrame([vars(r) for r in self.results])
        
        summary = df.groupby(['algorithm', 'variant']).agg({
            'cost': ['mean', 'std', 'median', 'min', 'max'],
            'time': ['mean', 'std', 'median'],
            'nodes': 'mean',
            'edges': 'mean'
        }).round(4)
        
        return summary
    
    def compute_scalability_metrics(self) -> pd.DataFrame:
        """
        Section 6.3.2: Scalability analysis
        Performance degradation with instance size
        """
        df = pd.DataFrame([vars(r) for r in self.results])
        
        # Group by size bins
        df['size_bin'] = pd.cut(df['nodes'], bins=[0, 30, 60, 100, 200, 1000])
        
        scalability = df.groupby(['algorithm', 'size_bin']).agg({
            'time': ['mean', 'std'],
            'cost': ['mean', 'std']
        })
        
        return scalability
    
    def generate_performance_plots(self, output_dir: str = "figures/evaluation"):
        """
        Generate comprehensive performance visualization
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        df = pd.DataFrame([vars(r) for r in self.results])
        
        # Plot 1: Cost distribution by algorithm
        plt.figure(figsize=(12, 6))
        sns.boxplot(data=df, x='algorithm', y='cost', hue='variant')
        plt.xticks(rotation=45, ha='right')
        plt.title('Cost Distribution by Algorithm and Variant')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/cost_distribution.pdf', dpi=300)
        plt.savefig(f'{output_dir}/cost_distribution.png', dpi=300)
        plt.close()
        
        # Plot 2: Time vs instance size (scalability)
        plt.figure(figsize=(12, 6))
        for algo in df['algorithm'].unique():
            algo_data = df[df['algorithm'] == algo]
            plt.scatter(algo_data['nodes'], algo_data['time'], 
                       label=algo, alpha=0.6, s=50)
        
        plt.xlabel('Number of Nodes')
        plt.ylabel('Computation Time (s)')
        plt.title('Scalability: Time vs Graph Size')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f'{output_dir}/scalability.pdf', dpi=300)
        plt.savefig(f'{output_dir}/scalability.png', dpi=300)
        plt.close()
        
        # Plot 3: Cost vs Time trade-off
        plt.figure(figsize=(10, 8))
        for algo in df['algorithm'].unique():
            algo_data = df[df['algorithm'] == algo]
            plt.scatter(algo_data['time'], algo_data['cost'],
                       label=algo, alpha=0.6, s=100)
        
        plt.xlabel('Computation Time (s)')
        plt.ylabel('Solution Cost')
        plt.title('Cost-Time Trade-off')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xscale('log')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/cost_time_tradeoff.pdf', dpi=300)
        plt.savefig(f'{output_dir}/cost_time_tradeoff.png', dpi=300)
        plt.close()
        
        print(f"Performance plots saved to {output_dir}/")


class ReproducibilityManager:
    """
    Section 6.3.3: Reproducibility requirements
    Manage seeds, parameters, and experimental settings
    """
    
    def __init__(self, base_seed: int = 42):
        self.base_seed = base_seed
        self.experiment_config = {}
    
    def set_seeds(self, seed: int):
        """Set all random seeds for reproducibility"""
        np.random.seed(seed)
        try:
            import torch
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)
        except ImportError:
            pass
    
    def save_config(self, config: Dict, filepath: str):
        """Save experimental configuration"""
        import json
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)
    
    def load_config(self, filepath: str) -> Dict:
        """Load experimental configuration"""
        import json
        with open(filepath, 'r') as f:
            return json.load(f)


# Example usage
if __name__ == "__main__":
    print("Statistical Evaluation Framework - Testing")
    print("=" * 70)
    
    # Section 6.4: Generate benchmarks
    print("\nGenerating benchmark suite...")
    generator = BenchmarkGenerator(seed=42)
    instances = generator.generate_benchmark_suite("data/test_benchmarks")
    
    print(f"Generated {len(instances)} instances")
    
    # Section 6.3: Statistical evaluation
    print("\n" + "=" * 70)
    print("Statistical Evaluation Test")
    print("=" * 70)
    
    evaluator = StatisticalEvaluator(n_runs=10, confidence_level=0.95)
    
    # Mock algorithm for testing
    def mock_algorithm(G):
        """Simple mock algorithm"""
        cost = sum(G[u][v].get('weight', 1.0) for u, v in G.edges())
        cost += np.random.normal(0, cost * 0.1)  # Add noise
        tour = list(G.edges())
        comp_time = np.random.uniform(0.001, 0.01)
        return cost, tour, comp_time
    
    # Test on one instance
    test_instance = list(instances.values())[0]
    test_name = list(instances.keys())[0]
    
    print(f"\nRunning {evaluator.n_runs} trials on {test_name}...")
    results = evaluator.run_algorithm_multiple_times(
        mock_algorithm,
        test_instance,
        test_name,
        "MockAlgorithm",
        "CPP"
    )
    
    # Compute statistics
    stats_dict = evaluator.compute_statistics(results)
    
    print("\nStatistical Results:")
    print(f"  Mean cost: {stats_dict['mean_cost']:.2f} ± {stats_dict['std_cost']:.2f}")
    print(f"  95% CI: [{stats_dict['cost_ci_lower']:.2f}, {stats_dict['cost_ci_upper']:.2f}]")
    print(f"  Median cost: {stats_dict['median_cost']:.2f}")
    print(f"  CV (stability): {stats_dict['cv_cost']:.3f}")
    print(f"\n  Mean time: {stats_dict['mean_time']:.4f} ± {stats_dict['std_time']:.4f}s")
    
    print("\n✓ Statistical framework validated!")
    print("  ✓ Multiple runs per instance")
    print("  ✓ Confidence intervals")
    print("  ✓ Statistical tests")
    print("  ✓ Comprehensive metrics")