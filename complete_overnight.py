"""
COMPLETE OVERNIGHT PIPELINE
Everything you need by morning: CPP-LC, ML/RL, Real data

Total time: 30-60 minutes
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
from simple_ml_cpp import SimpleMLCPP
from experimental_pipeline import ExperimentResult

def run_complete_overnight():
    """Run all experiments overnight"""
    
    print("="*70)
    print("COMPLETE OVERNIGHT PIPELINE")
    print("="*70)
    print("\nWhat will run:")
    print("  1. Classical CPP (baseline)")
    print("  2. Greedy Heuristic")
    print("  3. CPP-LC (simplified, fast)")
    print("  4. ML/RL Learning (simple baseline)")
    print("  5. Real London data")
    print("\nEstimated time: 30-60 minutes\n")
    
    input("Press Enter to start...")
    
    overall_start = time.time()
    
    #Get instances
    gen = BenchmarkGenerator(output_dir="benchmarks")
    instance_ids = gen.get_instance_list()
    
    print(f"\n📊 Instances: {len(instance_ids)}")
    
    results = []
    
    # ==================== PART 1: Classical + Greedy ====================
    print("\n" + "="*70)
    print("PART 1/4: Classical CPP + Greedy (FAST)")
    print("="*70)
    
    classical_costs = {}
    
    # Classical CPP
    print("\n1. Classical CPP...")
    for i, instance_id in enumerate(instance_ids, 1):
        try:
            instance = gen.load_instance(instance_id)
            
            start = time.time()
            cost, tour = solve_classical_cpp(instance.graph)
            runtime = time.time() - start
            
            classical_costs[instance_id] = cost
            
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
                print(f"  Progress: {i}/{len(instance_ids)}")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print(f"  ✅ Complete: {len([r for r in results if r.algorithm == 'classical_cpp'])} results")
    
    # Greedy
    print("\n2. Greedy Heuristic...")
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
                print(f"  Progress: {i}/{len(instance_ids)}")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print(f"  ✅ Complete: {len([r for r in results if r.algorithm == 'greedy'])} results")
    
    # ==================== PART 2: CPP-LC ====================
    print("\n" + "="*70)
    print("PART 2/4: CPP-LC (Load-Dependent Costs)")
    print("="*70)
    print("\nAssumptions:")
    print("  - Linear load-dependent costs")
    print("  - Greedy edge selection")
    print("  - Single vehicle")
    print("  - Simplified for speed (see paper)\n")
    
    cpp_lc_count = 0
    
    for i, instance_id in enumerate(instance_ids, 1):
        try:
            instance = gen.load_instance(instance_id)
            
            if instance.edge_demands is None:
                continue
            
            # Use existing demands
            capacity = instance.vehicle_capacity if instance.vehicle_capacity else \
                      sum(instance.edge_demands.values()) / 2 * 0.4
            
            solver = SimplifiedCPPLC(
                instance.graph,
                instance.edge_demands,
                capacity
            )
            
            start = time.time()
            cost, tour, meta = solver.solve_fast()
            runtime = time.time() - start
            
            classical_cost = classical_costs.get(instance_id, cost)
            gap = ((cost - classical_cost) / classical_cost * 100) if classical_cost > 0 else 0
            
            result = ExperimentResult(
                instance_id=instance_id,
                algorithm='cpp_lc_fast',
                variant='cpp_lc_simplified',
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
            )
            
            results.append(result)
            cpp_lc_count += 1
            
            if i % 10 == 0:
                print(f"  Progress: {cpp_lc_count} CPP-LC results")
                
        except Exception as e:
            pass
    
    print(f"  ✅ Complete: {cpp_lc_count} CPP-LC results")
    
    # ==================== PART 3: ML/RL Baseline ====================
    print("\n" + "="*70)
    print("PART 3/4: ML/RL Baseline")
    print("="*70)
    print("\nApproach:")
    print("  - Learn from classical solutions")
    print("  - Linear regression model")
    print("  - Feature-based edge selection\n")
    
    # Train ML model
    print("Training ML model...")
    ml_solver = SimpleMLCPP()
    
    # Get training data from classical results
    training_data = []
    for instance_id in instance_ids[:20]:  # Train on first 20
        try:
            instance = gen.load_instance(instance_id)
            _, tour = solve_classical_cpp(instance.graph)
            training_data.append((instance.graph, tour))
        except:
            pass
    
    if ml_solver.train_from_solutions(training_data):
        print(f"  ✓ Trained on {len(training_data)} instances")
        
        # Test ML solver
        print("\nTesting ML solver...")
        for i, instance_id in enumerate(instance_ids, 1):
            try:
                instance = gen.load_instance(instance_id)
                
                start = time.time()
                cost, tour, meta = ml_solver.solve_with_learning(instance.graph)
                runtime = time.time() - start
                
                classical_cost = classical_costs.get(instance_id, cost)
                gap = ((cost - classical_cost) / classical_cost * 100) if classical_cost > 0 else 0
                
                result = ExperimentResult(
                    instance_id=instance_id,
                    algorithm='ml_learning',
                    variant='ml_baseline',
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
                )
                
                results.append(result)
                
                if i % 10 == 0:
                    print(f"  Progress: {i}/{len(instance_ids)}")
                    
            except Exception as e:
                pass
        
        ml_count = len([r for r in results if r.algorithm == 'ml_learning'])
        print(f"  ✅ Complete: {ml_count} ML results")
    else:
        print("  ⚠️  ML training failed, skipping")
    
    # ==================== PART 4: London Real Data ====================
    print("\n" + "="*70)
    print("PART 4/4: Real London Street Network")
    print("="*70)
    
    try:
        print("\nDownloading London street network...")
        from download_london import quick_london_download
        
        G_london = quick_london_download()
        
        if G_london:
            print("\n✅ London data downloaded!")
            print(f"   Nodes: {G_london.number_of_nodes()}")
            print(f"   Edges: {G_london.number_of_edges()}")
            
            # Run all algorithms on London
            print("\nRunning experiments on London network...")
            
            # Classical
            cost, tour = solve_classical_cpp(G_london)
            london_classical = cost
            
            results.append(ExperimentResult(
                instance_id='london_westminster',
                algorithm='classical_cpp',
                variant='classical',
                cost=cost,
                tour_length=len(tour),
                feasible=True,
                runtime_seconds=0,
                num_nodes=G_london.number_of_nodes(),
                num_edges=G_london.number_of_edges(),
                network_family='osm_real',
                size='real_world',
                gap_from_classical=0.0
            ))
            
            # Greedy
            cost, tour = solve_greedy_heuristic(G_london)
            results.append(ExperimentResult(
                instance_id='london_westminster',
                algorithm='greedy',
                variant='greedy',
                cost=cost,
                tour_length=len(tour),
                feasible=True,
                runtime_seconds=0,
                num_nodes=G_london.number_of_nodes(),
                num_edges=G_london.number_of_edges(),
                network_family='osm_real',
                size='real_world',
                gap_from_classical=((cost - london_classical) / london_classical * 100)
            ))
            
            # ML
            cost, tour, _ = ml_solver.solve_with_learning(G_london)
            results.append(ExperimentResult(
                instance_id='london_westminster',
                algorithm='ml_learning',
                variant='ml_baseline',
                cost=cost,
                tour_length=len(tour),
                feasible=True,
                runtime_seconds=0,
                num_nodes=G_london.number_of_nodes(),
                num_edges=G_london.number_of_edges(),
                network_family='osm_real',
                size='real_world',
                gap_from_classical=((cost - london_classical) / london_classical * 100)
            ))
            
            print("  ✅ London experiments complete")
            
    except Exception as e:
        print(f"  ⚠️  London download failed: {e}")
        print("  Continuing without real data...")
    
    # ==================== SAVE RESULTS ====================
    print("\n" + "="*70)
    print("SAVING RESULTS")
    print("="*70)
    
    df = pd.DataFrame([r.to_dict() for r in results])
    
    output_dir = Path("results_complete")
    output_dir.mkdir(exist_ok=True)
    
    df.to_csv(output_dir / "all_results.csv", index=False)
    print(f"  ✓ CSV: {output_dir / 'all_results.csv'}")
    
    # Summary
    summary = df.groupby('algorithm').agg({
        'cost': ['count', 'mean', 'std'],
        'runtime_seconds': 'mean',
        'gap_from_classical': ['mean', 'std']
    }).round(3)
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(summary)
    
    summary.to_csv(output_dir / "summary.csv")
    
    # Key findings
    print("\n" + "="*70)
    print("KEY FINDINGS")
    print("="*70)
    
    for algo in df['algorithm'].unique():
        algo_data = df[df['algorithm'] == algo]
        avg_gap = algo_data['gap_from_classical'].mean()
        count = len(algo_data)
        print(f"  {algo}: {count} instances, {avg_gap:.1f}% avg gap")
    
    # CPP-LC specific
    cpp_lc_data = df[df['algorithm'] == 'cpp_lc_fast']
    if not cpp_lc_data.empty:
        avg_increase = cpp_lc_data['gap_from_classical'].mean()
        print(f"\n  🔥 CPP-LC cost increase: {avg_increase:.1f}%")
    
    # Total time
    total_time = time.time() - overall_start
    
    print("\n" + "="*70)
    print("✅ COMPLETE!")
    print("="*70)
    print(f"Total results: {len(results)}")
    print(f"Total time: {total_time/60:.1f} minutes")
    print(f"\nResults saved to: {output_dir}/")
    
    print("\n🎯 Next: Generate figures")
    print("   python3 complete_plots.py")
    
    return df


if __name__ == "__main__":
    run_complete_overnight()
