"""
ULTRA FAST PIPELINE - 2 Algorithms Only
For emergency deadline situations
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import pandas as pd
import time

from benchmark_generator import BenchmarkGenerator
from cpp_adapters import solve_classical_cpp, solve_greedy_heuristic
from experimental_pipeline import ExperimentResult

def run_ultra_fast():
    """Run ONLY the 2 fastest algorithms"""
    
    print("="*70)
    print("ULTRA FAST PIPELINE - 2 ALGORITHMS ONLY")
    print("="*70)
    
    # Get instances
    gen = BenchmarkGenerator(output_dir="benchmarks")
    instance_ids = gen.get_instance_list()
    
    print(f"\n📊 Instances: {len(instance_ids)}")
    print(f"🔬 Algorithms: 2 (Classical CPP + Greedy)")
    print(f"⏱️  Estimated time: 15-30 minutes\n")
    
    results = []
    
    # Algorithm 1: Classical CPP
    print("="*70)
    print("1/2: Classical CPP (Baseline)")
    print("="*70)
    
    for i, instance_id in enumerate(instance_ids, 1):
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
            
            if i % 10 == 0:
                print(f"  Progress: {i}/{len(instance_ids)} ({i/len(instance_ids)*100:.0f}%)")
            
        except Exception as e:
            print(f"  ✗ Error on {instance_id}: {e}")
    
    print(f"  ✅ Complete: {len([r for r in results if r.algorithm == 'classical_cpp'])} results\n")
    
    # Get classical costs for comparison
    classical_costs = {r.instance_id: r.cost for r in results if r.algorithm == 'classical_cpp'}
    
    # Algorithm 2: Greedy
    print("="*70)
    print("2/2: Greedy Heuristic")
    print("="*70)
    
    for i, instance_id in enumerate(instance_ids, 1):
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
            
            if i % 10 == 0:
                print(f"  Progress: {i}/{len(instance_ids)} ({i/len(instance_ids)*100:.0f}%)")
            
        except Exception as e:
            print(f"  ✗ Error on {instance_id}: {e}")
    
    print(f"  ✅ Complete: {len([r for r in results if r.algorithm == 'greedy'])} results\n")
    
    # Save results
    print("="*70)
    print("Saving Results")
    print("="*70)
    
    df = pd.DataFrame([r.to_dict() for r in results])
    
    output_dir = Path("results_ultrafast")
    output_dir.mkdir(exist_ok=True)
    
    df.to_csv(output_dir / "all_results.csv", index=False)
    print(f"  ✓ CSV: {output_dir / 'all_results.csv'}")
    
    # Summary statistics
    summary = df.groupby('algorithm').agg({
        'cost': ['count', 'mean', 'std', 'min', 'max'],
        'runtime_seconds': ['mean', 'max'],
        'gap_from_classical': ['mean', 'std']
    }).round(3)
    
    print("\n" + "="*70)
    print("SUMMARY STATISTICS")
    print("="*70)
    print(summary)
    print()
    
    summary.to_csv(output_dir / "summary.csv")
    
    # Quick analysis
    greedy_results = df[df['algorithm'] == 'greedy']
    avg_gap = greedy_results['gap_from_classical'].mean()
    
    print("="*70)
    print("KEY FINDING")
    print("="*70)
    print(f"Greedy heuristic has {avg_gap:.1f}% average gap from optimal")
    print(f"  (This is your main result to report!)")
    
    print("\n" + "="*70)
    print("✅ COMPLETE!")
    print("="*70)
    print(f"Total results: {len(results)}")
    print(f"Saved to: {output_dir}/")
    
    return df


if __name__ == "__main__":
    print("\n🚀 Starting ultra-fast pipeline...")
    print("   Estimated time: 15-30 minutes\n")
    
    start_time = time.time()
    
    df = run_ultra_fast()
    
    elapsed = time.time() - start_time
    
    print(f"\n⏱️  Total time: {elapsed/60:.1f} minutes")
    print(f"\n✅ You now have experimental results!")
    print(f"\n🎯 Next: Generate figures")
    print(f"   python3 ultrafast_plots.py")
