"""
Test/Demo: Generate and inspect a small benchmark dataset
Run this to verify the benchmark system works
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from benchmark_generator import BenchmarkGenerator, NetworkFamily, GraphSize
import networkx as nx


def demo_basic_generation():
    """Demo: Generate small test dataset"""
    print("=" * 70)
    print("DEMO 1: Basic Benchmark Generation")
    print("=" * 70)
    
    # Create generator
    generator = BenchmarkGenerator(output_dir="benchmarks_test", base_seed=42)
    
    # Generate just 2 instances per config for quick testing
    print("\n🔨 Generating test dataset (2 instances per config)...")
    instances = generator.generate_full_suite(instances_per_config=2)
    
    print(f"\n✅ Generated {len(instances)} instances")
    
    return generator, instances


def demo_inspect_instance(generator, instances):
    """Demo: Inspect instance details"""
    print("\n" + "=" * 70)
    print("DEMO 2: Inspect Instance Details")
    print("=" * 70)
    
    # Pick first instance
    instance = instances[0]
    
    print(f"\n📋 Instance: {instance.metadata.instance_id}")
    print(f"   Family: {instance.metadata.network_family}")
    print(f"   Size: {instance.metadata.size}")
    print(f"   Nodes: {instance.metadata.num_nodes}")
    print(f"   Edges: {instance.metadata.num_edges}")
    print(f"   Density: {instance.metadata.density:.3f}")
    print(f"   Clustering: {instance.metadata.clustering_coeff:.3f}")
    print(f"   Diameter: {instance.metadata.diameter}")
    print(f"   Connected: {instance.metadata.is_connected}")
    
    # Inspect CPP-LC data
    print(f"\n📦 CPP-LC Data:")
    if instance.edge_demands:
        total_demand = sum(instance.edge_demands.values()) / 2  # Symmetric
        print(f"   Total demand: {total_demand:.2f}")
        print(f"   Vehicle capacity: {instance.vehicle_capacity:.2f}")
        print(f"   Capacity ratio: {instance.vehicle_capacity / total_demand:.2%}")
        print(f"   Number of edges with demands: {len(instance.edge_demands) // 2}")
    
    # Inspect CPP-TW data
    print(f"\n⏰ CPP-TW Data:")
    if instance.time_windows:
        print(f"   Number of time windows: {len(instance.time_windows)}")
        first_edge = list(instance.time_windows.keys())[0]
        window = instance.time_windows[first_edge]
        print(f"   Example window for edge {first_edge}: [{window[0]:.1f}, {window[1]:.1f}]")
    
    # Inspect Mixed CPP data
    print(f"\n🔀 Mixed CPP Data:")
    if instance.edge_types:
        num_directed = sum(1 for e in instance.edge_types.values() if e['is_directed'])
        num_total = len(instance.edge_types)
        print(f"   Directed edges: {num_directed}/{num_total} ({num_directed/num_total:.1%})")
    
    # Inspect Windy data
    print(f"\n💨 Windy Postman Data:")
    if instance.directional_costs:
        # Sample asymmetry
        edges_sample = list(instance.directional_costs.keys())[:5]
        asymmetries = []
        for u, v in edges_sample:
            if (v, u) in instance.directional_costs:
                cost_uv = instance.directional_costs[(u, v)]
                cost_vu = instance.directional_costs[(v, u)]
                asym = abs(cost_uv - cost_vu) / max(cost_uv, cost_vu)
                asymmetries.append(asym)
        
        if asymmetries:
            avg_asym = sum(asymmetries) / len(asymmetries)
            print(f"   Average asymmetry (sample): {avg_asym:.1%}")


def demo_load_instance(generator):
    """Demo: Load saved instance"""
    print("\n" + "=" * 70)
    print("DEMO 3: Load Saved Instance")
    print("=" * 70)
    
    # Get list of available instances
    instance_ids = generator.get_instance_list()
    
    if not instance_ids:
        print("   No instances found!")
        return
    
    print(f"\n📂 Found {len(instance_ids)} saved instances")
    print(f"   First 5: {instance_ids[:5]}")
    
    # Load first instance
    instance_id = instance_ids[0]
    print(f"\n📥 Loading instance: {instance_id}")
    
    loaded_instance = generator.load_instance(instance_id)
    
    print(f"   ✓ Loaded successfully")
    print(f"   Graph: {loaded_instance.graph.number_of_nodes()} nodes, "
          f"{loaded_instance.graph.number_of_edges()} edges")
    print(f"   Has CPP-LC data: {loaded_instance.edge_demands is not None}")
    print(f"   Has CPP-TW data: {loaded_instance.time_windows is not None}")


def demo_filter_instances(generator):
    """Demo: Filter instances by family/size"""
    print("\n" + "=" * 70)
    print("DEMO 4: Filter Instances")
    print("=" * 70)
    
    # Filter by family
    print("\n🔍 Filtering by network family:")
    for family in [NetworkFamily.GRID, NetworkFamily.RANDOM_GEOMETRIC, NetworkFamily.CLUSTERED]:
        instances = generator.get_instance_list(family=family)
        print(f"   {family.value}: {len(instances)} instances")
    
    # Filter by size
    print("\n🔍 Filtering by size:")
    for size in GraphSize:
        instances = generator.get_instance_list(size=size)
        print(f"   {size.value}: {len(instances)} instances")
    
    # Filter by both
    print("\n🔍 Filtering by family AND size:")
    instances = generator.get_instance_list(
        family=NetworkFamily.GRID,
        size=GraphSize.SMALL
    )
    print(f"   Grid + Small: {len(instances)} instances")


def demo_visualize_instance(instance):
    """Demo: Visualize a graph instance"""
    print("\n" + "=" * 70)
    print("DEMO 5: Visualize Instance")
    print("=" * 70)
    
    try:
        import matplotlib.pyplot as plt
        
        G = instance.graph
        
        print(f"\n📊 Creating visualization for {instance.metadata.instance_id}")
        
        plt.figure(figsize=(10, 8))
        
        # Compute layout
        if instance.metadata.network_family == 'grid':
            # Use grid layout for grid graphs
            pos = nx.spring_layout(G, seed=42)  # Spring layout for better visualization
        else:
            pos = nx.spring_layout(G, seed=42, k=0.5)
        
        # Draw graph
        nx.draw_networkx_nodes(G, pos, node_color='lightblue', 
                              node_size=300, alpha=0.8)
        nx.draw_networkx_edges(G, pos, edge_color='gray', 
                              width=1.5, alpha=0.6)
        
        # Optionally show edge labels (weights)
        # edge_labels = nx.get_edge_attributes(G, 'weight')
        # edge_labels = {k: f"{v:.1f}" for k, v in edge_labels.items()}
        # nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=8)
        
        plt.title(f"{instance.metadata.network_family} - {instance.metadata.size}\n"
                 f"{G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        plt.axis('off')
        plt.tight_layout()
        
        # Save
        output_file = f"benchmark_viz_{instance.metadata.instance_id}.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"   ✓ Saved visualization: {output_file}")
        
        plt.close()
        
    except ImportError:
        print("   ⚠️  matplotlib not available, skipping visualization")


def demo_statistics_summary(instances):
    """Demo: Compute summary statistics"""
    print("\n" + "=" * 70)
    print("DEMO 6: Summary Statistics")
    print("=" * 70)
    
    from collections import defaultdict
    import numpy as np
    
    stats = defaultdict(lambda: defaultdict(list))
    
    # Collect statistics
    for inst in instances:
        family = inst.metadata.network_family
        stats[family]['nodes'].append(inst.metadata.num_nodes)
        stats[family]['edges'].append(inst.metadata.num_edges)
        stats[family]['density'].append(inst.metadata.density)
        stats[family]['clustering'].append(inst.metadata.clustering_coeff)
    
    # Print summary
    print("\n📊 Statistics by Network Family:\n")
    print(f"{'Family':<20} {'Avg Nodes':<12} {'Avg Edges':<12} {'Avg Density':<12} {'Avg Clustering':<15}")
    print("-" * 70)
    
    for family in sorted(stats.keys()):
        avg_nodes = np.mean(stats[family]['nodes'])
        avg_edges = np.mean(stats[family]['edges'])
        avg_density = np.mean(stats[family]['density'])
        avg_clustering = np.mean(stats[family]['clustering'])
        
        print(f"{family:<20} {avg_nodes:<12.1f} {avg_edges:<12.1f} "
              f"{avg_density:<12.3f} {avg_clustering:<15.3f}")


def main():
    """Run all demos"""
    print("\n" + "=" * 70)
    print("🧪 BENCHMARK SYSTEM TEST & DEMO")
    print("=" * 70)
    
    # Demo 1: Generate
    generator, instances = demo_basic_generation()
    
    # Demo 2: Inspect
    if instances:
        demo_inspect_instance(generator, instances)
    
    # Demo 3: Load
    demo_load_instance(generator)
    
    # Demo 4: Filter
    demo_filter_instances(generator)
    
    # Demo 5: Visualize
    if instances:
        demo_visualize_instance(instances[0])
    
    # Demo 6: Statistics
    if instances:
        demo_statistics_summary(instances)
    
    print("\n" + "=" * 70)
    print("✅ ALL DEMOS COMPLETE!")
    print("=" * 70)
    print("\n📁 Generated files:")
    print("   - benchmarks_test/ - Test benchmark dataset")
    print("   - benchmarks_test/BENCHMARK_SUMMARY.md - Summary report")
    print("   - benchmark_viz_*.png - Visualization (if matplotlib available)")
    
    print("\n🎯 Next steps:")
    print("   1. Review summary: cat benchmarks_test/BENCHMARK_SUMMARY.md")
    print("   2. Generate full dataset: python generate_benchmarks.py")
    print("   3. Run experiments: python src/run_experiments.py")


if __name__ == "__main__":
    main()
