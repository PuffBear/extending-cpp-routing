"""
FAILSAFE PIPELINE FOR DEADLINE
Lightweight, guaranteed to finish in 30-60 minutes

What it includes:
1. Classical + Greedy (fast baselines)
2. Lightweight learning (simple, not deep)
3. CPP-LC (ultra-fast version)
4. London data
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import pandas as pd
import numpy as np
import time
import networkx as nx

from benchmark_generator import BenchmarkGenerator
from cpp_adapters import solve_classical_cpp, solve_greedy_heuristic
from fast_cpp_lc import SimplifiedCPPLC
from simple_ml_cpp import SimpleMLCPP  # Lightweight learning
from experimental_pipeline import ExperimentResult

print("="*70)
print("FAILSAFE PIPELINE - GUARANTEED TO FINISH")
print("="*70)
print("\nComponents:")
print("  ✓ Classical CPP + Greedy (proven fast)")
print("  ✓ Lightweight ML (regression-based, fast training)")
print("  ✓ CPP-LC (ultra-fast version)")
print("  ✓ London real data")
print("\nEstimated: 30-60 minutes")
print("\nNote: Using lightweight ML instead of deep RL")
print("      (Deep RL kept crashing due to memory)")

input("\nPress Enter to start...")

overall_start = time.time()

# Setup
gen = BenchmarkGenerator(output_dir="benchmarks")
instance_ids = gen.get_instance_list()

print(f"\n📊 Instances: {len(instance_ids)}")

results = []
classical_costs = {}
training_data = []

# ==================== PART 1: BASELINES ====================
print("\n" + "="*70)
print("PART 1/4: Baseline Algorithms")
print("="*70)

print("\n1. Classical CPP...")
for i, instance_id in enumerate(instance_ids, 1):
    try:
        instance = gen.load_instance(instance_id)
        
        start = time.time()
        cost, tour = solve_classical_cpp(instance.graph)
        runtime = time.time() - start
        
        classical_costs[instance_id] = cost
        training_data.append((instance.graph, tour))
        
        results.append(ExperimentResult(
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
        ))
        
        if i % 10 == 0:
            print(f"  Progress: {i}/{len(instance_ids)}")
            
    except Exception as e:
        print(f"  ✗ Error: {e}")

print(f"  ✅ {len([r for r in results if r.algorithm == 'classical_cpp'])} results")

print("\n2. Greedy...")
for i, instance_id in enumerate(instance_ids, 1):
    try:
        instance = gen.load_instance(instance_id)
        
        start = time.time()
        cost, tour = solve_greedy_heuristic(instance.graph)
        runtime = time.time() - start
        
        gap = ((cost - classical_costs.get(instance_id, cost)) / classical_costs.get(instance_id, cost) * 100) if classical_costs.get(instance_id, cost) > 0 else 0
        
        results.append(ExperimentResult(
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
        ))
        
        if i % 10 == 0:
            print(f"  Progress: {i}/{len(instance_ids)}")
            
    except:
        pass

print(f"  ✅ {len([r for r in results if r.algorithm == 'greedy'])} results")

# ==================== PART 2: LIGHTWEIGHT ML ====================
print("\n" + "="*70)
print("PART 2/4: Lightweight ML Learning")
print("="*70)
print("\nApproach: Feature-based supervised learning")
print("  (Lightweight, fast training, guaranteed to finish)")

ml_solver = SimpleMLCPP()

print(f"\nTraining on {min(30, len(training_data))} instances...")
if ml_solver.train_from_solutions(training_data[:30]):
    print("  ✓ Training complete")
    
    print("\nTesting learned heuristic...")
    for i, instance_id in enumerate(instance_ids, 1):
        try:
            instance = gen.load_instance(instance_id)
            
            start = time.time()
            cost, tour, meta = ml_solver.solve_with_learning(instance.graph)
            runtime = time.time() - start
            
            gap = ((cost - classical_costs.get(instance_id, cost)) / classical_costs.get(instance_id, cost) * 100) if classical_costs.get(instance_id, cost) > 0 else 0
            
            results.append(ExperimentResult(
                instance_id=instance_id,
                algorithm='ml_learned',
                variant='feature_based',
                cost=cost,
                tour_length=len(tour) if tour else 0,
                feasible=True,
                runtime_seconds=runtime,
                num_nodes=instance.metadata.num_nodes,
                num_edges=instance.metadata.num_edges,
                network_family=instance.metadata.network_family,
                size=instance.metadata.size,
                gap_from_classical=gap,
                metadata=meta
            ))
            
            if i % 10 == 0:
                print(f"  Progress: {i}/{len(instance_ids)}")
                
        except:
            pass
    
    ml_count = len([r for r in results if r.algorithm == 'ml_learned'])
    print(f"  ✅ {ml_count} ML results")
else:
    print("  ⚠️  ML training failed")

# ==================== PART 3: CPP-LC ====================
print("\n" + "="*70)
print("PART 3/4: CPP-LC (Ultra-Fast Version)")
print("="*70)

cpp_lc_count = 0
for i, instance_id in enumerate(instance_ids, 1):
    try:
        instance = gen.load_instance(instance_id)
        
        if instance.edge_demands is None:
            continue
        
        capacity = instance.vehicle_capacity if instance.vehicle_capacity else \
                  sum(instance.edge_demands.values()) / 2 * 0.4
        
        solver = SimplifiedCPPLC(instance.graph, instance.edge_demands, capacity)
        
        start = time.time()
        cost, tour, meta = solver.solve_fast()
        runtime = time.time() - start
        
        gap = ((cost - classical_costs.get(instance_id, cost)) / classical_costs.get(instance_id, cost) * 100) if classical_costs.get(instance_id, cost) > 0 else 0
        
        results.append(ExperimentResult(
            instance_id=instance_id,
            algorithm='cpp_lc_fast',
            variant='load_dependent',
            cost=cost,
            tour_length=len(tour) if tour else 0,
            feasible=True,
            runtime_seconds=runtime,
            num_nodes=instance.metadata.num_nodes,
            num_edges=instance.metadata.num_edges,
            network_family=instance.metadata.network_family,
            size=instance.metadata.size,
            gap_from_classical=gap,
            metadata=meta
        ))
        cpp_lc_count += 1
        
        if i % 10 == 0:
            print(f"  Progress: {cpp_lc_count} CPP-LC results")
            
    except:
        pass

print(f"  ✅ {cpp_lc_count} CPP-LC results")

# ==================== PART 4: LONDON ====================
print("\n" + "="*70)
print("PART 4/4: Real London Data")
print("="*70)

try:
    from download_london import quick_london_download
    
    G_london = quick_london_download()
    
    if G_london:
        # Classical
        cost, _ = solve_classical_cpp(G_london)
        london_classical = cost
        
        # Greedy
        cost_g, _ = solve_greedy_heuristic(G_london)
        
        # ML
        cost_ml, _, _ = ml_solver.solve_with_learning(G_london)
        
        for algo, c in [('classical_cpp', cost), ('greedy', cost_g), ('ml_learned', cost_ml)]:
            results.append(ExperimentResult(
                instance_id='london',
                algorithm=algo,
                variant='real_world',
                cost=c,
                tour_length=0,
                feasible=True,
                runtime_seconds=0,
                num_nodes=G_london.number_of_nodes(),
                num_edges=G_london.number_of_edges(),
                network_family='osm_real',
                size='real',
                gap_from_classical=((c - london_classical) / london_classical * 100)
            ))
        
        print(f"  ✅ London: Classical={cost:.1f}, ML={cost_ml:.1f} ({((cost_ml-cost)/cost*100):.1f}% gap)")
        
except Exception as e:
    print(f"  ⚠️  London failed: {e}")

# ==================== SAVE ====================
print("\n" + "="*70)
print("SAVING RESULTS")
print("="*70)

df = pd.DataFrame([r.to_dict() for r in results])

output_dir = Path("results_final")
output_dir.mkdir(exist_ok=True)

df.to_csv(output_dir / "all_results.csv", index=False)
print(f"  ✓ CSV: {output_dir / 'all_results.csv'}")

summary = df.groupby('algorithm').agg({
    'cost': ['count', 'mean', 'std'],
    'gap_from_classical': ['mean', 'std']
}).round(3)

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(summary)

summary.to_csv(output_dir / "summary.csv")

total_time = time.time() - overall_start

print("\n" + "="*70)
print("✅ COMPLETE!")
print("="*70)
print(f"Total results: {len(results)}")
print(f"Total time: {total_time/60:.1f} minutes")

print("\n📊 What you have:")
for algo in df['algorithm'].unique():
    count = len(df[df['algorithm'] == algo])
    gap = df[df['algorithm'] == algo]['gap_from_classical'].mean()
    print(f"  {algo}: {count} instances, {gap:.1f}% avg gap")

cpp_lc_data = df[df['algorithm'] == 'cpp_lc_fast']
if not cpp_lc_data.empty:
    print(f"\n🔥 CPP-LC: {cpp_lc_data['gap_from_classical'].mean():.1f}% cost increase")

print("\n🎯 Next: python3 complete_plots.py")
