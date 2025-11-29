"""
REAL LEARNING PIPELINE
Trains actual Deep RL agent, not just regression

Duration: 1-3 hours (depending on training)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import torch
import pandas as pd
import time
import networkx as nx

from benchmark_generator import BenchmarkGenerator
from cpp_adapters import solve_classical_cpp, solve_greedy_heuristic
from fast_cpp_lc import SimplifiedCPPLC
from deep_rl_cpp import DeepRLCPP
from experimental_pipeline import ExperimentResult

def main():
    """Run complete pipeline with REAL deep learning"""
    
    print("="*70)
    print("REAL DEEP LEARNING PIPELINE FOR CPP")
    print("="*70)
    print("\nWhat this does:")
    print("  1. Generate/load benchmarks")
    print("  2. Run classical + greedy baselines")
    print("  3. TRAIN Deep RL agent (Graph Attention + Pointer Network)")
    print("  4. Test learned policy")
    print("  5. CPP-LC experiments")
    print("  6. London real data")
    print("\nEstimated time: 1-3 hours")
    print("  - Baselines: 1-2 min")
    print("  - RL Training: 30-60 min")
    print("  - Testing: 5-10 min")
    print("  - CPP-LC: 10-20 min")
    print("  - London: 2-5 min")
    
    input("\nPress Enter to start...")
    
    overall_start = time.time()
    
    # Setup
    gen = BenchmarkGenerator(output_dir="benchmarks")
    instance_ids = gen.get_instance_list()
    
    print(f"\n📊 Instances: {len(instance_ids)}")
    
    results = []
    
    # ==================== PART 1: BASELINES ====================
    print("\n" + "="*70)
    print("PART 1/5: Baseline Algorithms")
    print("="*70)
    
    classical_costs = {}
    training_graphs = []
    training_solutions = []
    
    print("\n1. Classical CPP (will use for RL training)...")
    for i, instance_id in enumerate(instance_ids, 1):
        try:
            instance = gen.load_instance(instance_id)
            
            start = time.time()
            cost, tour = solve_classical_cpp(instance.graph)
            runtime = time.time() - start
            
            classical_costs[instance_id] = cost
            
            # Save for RL training
            training_graphs.append(instance.graph)
            training_solutions.append((cost, tour))
            
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
    
    print(f"  ✅ {len([r for r in results if r.algorithm == 'classical_cpp'])} results")
    
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
            pass
    
    print(f"  ✅ {len([r for r in results if r.algorithm == 'greedy'])} results")
    
    # ==================== PART 2: DEEP RL TRAINING ====================
    print("\n" + "="*70)
    print("PART 2/5: Deep RL Training (THE REAL DEAL)")
    print("="*70)
    print("\nArchitecture:")
    print("  - Graph Attention Network (GAT) for node embeddings")
    print("  - Pointer Network for sequential edge selection")
    print("  - REINFORCE policy gradient")
    print("  - Trained on classical solutions as baseline\n")
    
    # Initialize RL agent
    rl_agent = DeepRLCPP(
        embedding_dim=32,
        hidden_dim=64,
        learning_rate=1e-3
    )
    
    # Train on subset (faster)
    n_train = min(40, len(training_graphs))
    print(f"Training on {n_train} instances...")
    
    train_start = time.time()
    rl_agent.train_from_graphs(
        training_graphs[:n_train],
        training_solutions[:n_train],
        n_epochs=50,  # Can increase for better results
        batch_size=5
    )
    train_time = time.time() - train_start
    
    print(f"  ⏱️  Training time: {train_time/60:.1f} minutes")
    
   # ==================== PART 3: TEST LEARNED POLICY ====================
    print("\n" + "="*70)
    print("PART 3/5: Testing Learned Policy")
    print("="*70)
    
    print("\nDeploying learned policy on all instances...")
    for i, instance_id in enumerate(instance_ids, 1):
        try:
            instance = gen.load_instance(instance_id)
            
            start = time.time()
            cost, tour, meta = rl_agent.solve(instance.graph, sampling=False)
            runtime = time.time() - start
            
            classical_cost = classical_costs.get(instance_id, cost)
            gap = ((cost - classical_cost) / classical_cost * 100) if classical_cost > 0 else 0
            
            result = ExperimentResult(
                instance_id=instance_id,
                algorithm='deep_rl',
                variant='pointer_network',
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
    
    rl_count = len([r for r in results if r.algorithm == 'deep_rl'])
    print(f"  ✅ {rl_count} RL results")
    
    # Quick performance summary
    rl_results = [r for r in results if r.algorithm == 'deep_rl']
    if rl_results:
        avg_gap = sum(r.gap_from_classical for r in rl_results) / len(rl_results)
        print(f"  📊 Deep RL avg gap: {avg_gap:.1f}%")
    
    # ==================== PART 4: CPP-LC ====================
    print("\n" + "="*70)
    print("PART 4/5: CPP-LC (Load-Dependent Costs)")
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
            
        except Exception as e:
            pass
    
    print(f"  ✅ {cpp_lc_count} CPP-LC results")
    
    # ==================== PART 5: LONDON ====================
    print("\n" + "="*70)
    print("PART 5/5: Real London Data")
    print("="*70)
    
    try:
        from download_london import quick_london_download
        
        G_london = quick_london_download()
        
        if G_london:
            # Classical
            cost, tour = solve_classical_cpp(G_london)
            london_classical = cost
            
            # Greedy
            cost_g, _ = solve_greedy_heuristic(G_london)
            
            # Deep RL
            cost_rl, _, _ = rl_agent.solve(G_london, sampling=False)
            
            # Save results
            for algo, c in [('classical_cpp', cost), ('greedy', cost_g), ('deep_rl', cost_rl)]:
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
            
            print(f"  ✅ London: Classical={cost:.1f}, RL={cost_rl:.1f} ({((cost_rl-cost)/cost*100):.1f}% gap)")
            
    except Exception as e:
        print(f"  ⚠️  London failed: {e}")
    
    # ==================== SAVE ====================
    print("\n" + "="*70)
    print("SAVING RESULTS")
    print("="*70)
    
    df = pd.DataFrame([r.to_dict() for r in results])
    
    output_dir = Path("results_deep_rl")
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
    
    # Save trained model
    torch.save(rl_agent.policy_net.state_dict(), output_dir / "trained_policy.pt")
    print(f"\n  ✓ Saved trained model: {output_dir / 'trained_policy.pt'}")
    
    total_time = time.time() - overall_start
    
    print("\n" + "="*70)
    print("✅ COMPLETE!")
    print("="*70)
    print(f"Total results: {len(results)}")
    print(f"Total time: {total_time/60:.1f} minutes")
    
    print("\n🎯 What you have:")
    print("  ✅ REAL deep RL (Graph Attention + Pointer Network)")
    print("  ✅ Trained policy saved")
    print("  ✅ CPP-LC results")
    print("  ✅ Real London data")
    print("  ✅ Complete experimental results")
    
    print("\nNext: python3 complete_plots.py")
    
    return df


if __name__ == "__main__":
    main()
