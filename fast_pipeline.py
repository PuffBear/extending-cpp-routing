"""
MINIMAL FAST PIPELINE - For Immediate Results
Skips slow experiments, focuses on what works
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import pandas as pd
import time

from benchmark_generator import BenchmarkGenerator
from cpp_adapters import solve_classical_cpp, solve_greedy_heuristic, solve_two_opt
from experimental_pipeline import ExperimentResult

def run_fast_experiments():
    """Run only the fast experiments"""
    
    print("="*70)
    print("FAST EXPERIMENTAL PIPELINE - MINIMAL VERSION")
    print("="*70)
    
    # Get instances
    gen = BenchmarkGenerator(output_dir="benchmarks")
    instance_ids = gen.get_instance_list()
    
    print(f"\n📊 Found {len(instance_ids)} instances")
    print(f"🔬 Running 3 fast algorithms (skipping slow ones)")
    
    results = []
    
    # Algorithm 1: Classical CPP
    print("\n" + "="*70)
    print("1. Classical CPP (Baseline)")
    print("="*70)
    
    for i, instance_id in enumerate(instance_ids):
        print(f"  [{i+1}/{len(instance_ids)}] {instance_id}...", end=" ")
        
        try:
            instance = gen.load_instance(instance_id)
            
            start = time.time()
            cost, tour = solve_classical_cpp(instance.graph)
            runtime = time.time() - start
            
            result = ExperimentResult(
                instance_id=instance_id,
                algorithm='classical_cpp',
                variant='classical',
                cost=cost,
                tour_length=len(tour) if tour else 0,
                feasible=True,
                runtime_seconds=runtime,
                num_nodes=instance.metadata.num_nodes,
                num_edges=instance.metadata.num_edges,
                network_family=instance.metadata.network_family,
                size=instance.metadata.size,
                gap_from_classical=0.0
            )
            
            results.append(result)
            print(f"✓ Cost: {cost:.2f}, Time: {runtime:.3f}s")
            
        except Exception as e:
            print(f"✗ Error: {e}")
    
    # Algorithm 2: Greedy
    print("\n" + "="*70)
    print("2. Greedy Heuristic")
    print("="*70)
    
    # Get classical costs for comparison
    classical_costs = {r.instance_id: r.cost for r in results if r.algorithm == 'classical_cpp'}
    
    for i, instance_id in enumerate(instance_ids):
        print(f"  [{i+1}/{len(instance_ids)}] {instance_id}...", end=" ")
        
        try:
            instance = gen.load_instance(instance_id)
            
            start = time.time()
            cost, tour = solve_greedy_heuristic(instance.graph)
            runtime = time.time() - start
            
            classical_cost = classical_costs.get(instance_id, cost)
            gap = ((cost - classical_cost) / classical_cost * 100) if classical_cost > 0 else 0
            
            result = ExperimentResult(
                instance_id=instance_id,
                algorithm='greedy',
                variant='greedy',
                cost=cost,
                tour_length=len(tour) if tour else 0,
                feasible=True,
                runtime_seconds=runtime,
                num_nodes=instance.metadata.num_nodes,
                num_edges=instance.metadata.num_edges,
                network_family=instance.metadata.network_family,
                size=instance.metadata.size,
                gap_from_classical=gap
            )
            
            results.append(result)
            print(f"✓ Cost: {cost:.2f}, Gap: {gap:.1f}%, Time: {runtime:.3f}s")
            
        except Exception as e:
            print(f"✗ Error: {e}")
    
    # Algorithm 3: 2-opt
    print("\n" + "="*70)
    print("3. 2-Opt Local Search")
    print("="*70)
    
    for i, instance_id in enumerate(instance_ids):
        print(f"  [{i+1}/{len(instance_ids)}] {instance_id}...", end=" ")
        
        try:
            instance = gen.load_instance(instance_id)
            
            start = time.time()
            cost, tour = solve_two_opt(instance.graph, max_iterations=50)  # Limit iterations
            runtime = time.time() - start
            
            classical_cost = classical_costs.get(instance_id, cost)
            gap = ((cost - classical_cost) / classical_cost * 100) if classical_cost > 0 else 0
            
            result = ExperimentResult(
                instance_id=instance_id,
                algorithm='two_opt',
                variant='local_search',
                cost=cost,
                tour_length=len(tour) if tour else 0,
                feasible=True,
                runtime_seconds=runtime,
                num_nodes=instance.metadata.num_nodes,
                num_edges=instance.metadata.num_edges,
                network_family=instance.metadata.network_family,
                size=instance.metadata.size,
                gap_from_classical=gap
            )
            
            results.append(result)
            print(f"✓ Cost: {cost:.2f}, Gap: {gap:.1f}%, Time: {runtime:.3f}s")
            
        except Exception as e:
            print(f"✗ Error: {e}")
    
    # Save results
    print("\n" + "="*70)
    print("Saving Results")
    print("="*70)
    
    df = pd.DataFrame([r.to_dict() for r in results])
    
    output_dir = Path("experimental_results_fast")
    output_dir.mkdir(exist_ok=True)
    
    df.to_csv(output_dir / "all_results.csv", index=False)
    print(f"✓ Saved: {output_dir / 'all_results.csv'}")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    summary = df.groupby('algorithm').agg({
        'cost': ['count', 'mean', 'std'],
        'runtime_seconds': 'mean',
        'gap_from_classical': 'mean'
    }).round(3)
    
    print(summary)
    
    summary.to_csv(output_dir / "summary.csv")
    
    print(f"\n✅ COMPLETE!")
    print(f"   Total results: {len(results)}")
    print(f"   Saved to: {output_dir}/")
    
    return df


if __name__ == "__main__":
    start_time = time.time()
    
    df = run_fast_experiments()
    
    elapsed = time.time() - start_time
    print(f"\n⏱️  Total time: {elapsed/60:.1f} minutes")
    
    print("\n🎯 Next steps:")
    print("   1. Generate figures: python3 fast_plots.py")
    print("   2. Review results in: experimental_results_fast/")
