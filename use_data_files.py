"""
USE EXISTING DATA/ FILES - NO NETWORK DOWNLOAD NEEDED!
These are already complete benchmark instances!
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import pandas as pd
import networkx as nx
import time
from typing import List, Tuple, Dict

from cpp_adapters import solve_classical_cpp, solve_greedy_heuristic
from fast_cpp_lc import SimplifiedCPPLC
from simple_ml_cpp import SimpleMLCPP
from experimental_pipeline import ExperimentResult

def load_gml_files():
    """Load all GML files from data/ directory"""
    
    data_dir = Path("data")
    gml_files = list(data_dir.glob("*.gml"))
    
    print(f"Found {len(gml_files)} GML files in data/")
    
    graphs = {}
    for gml_file in gml_files:
        try:
            G = nx.read_gml(str(gml_file))
            instance_id = gml_file.stem
            graphs[instance_id] = G
        except Exception as e:
            print(f"  ✗ Failed to load {gml_file.name}: {e}")
    
    return graphs

def main():
    """Run experiments on existing data/ files"""
    
    print("="*70)
    print("EXPERIMENTS ON EXISTING DATA")
    print("="*70)
    print("\nUsing graph files from data/ directory")
    print("These already have complete CPP instance data!\n")
    
    # Load graphs
    graphs = load_gml_files()
    print(f"\n✅ Loaded {len(graphs)} graphs")
    
    results = []
    classical_costs = {}
    training_data = []
    
    # ==================== PART 1: BASELINES ====================
    print("\n" + "="*70)
    print("PART 1/4: Baseline Algorithms")
    print("="*70)
    
    print("\n1. Classical CPP...")
    for i, (instance_id, G) in enumerate(graphs.items(), 1):
        try:
            start = time.time()
            cost, tour = solve_classical_cpp(G)
            runtime = time.time() - start
            
            classical_costs[instance_id] = cost
            training_data.append((G, tour))
            
            results.append(ExperimentResult(
                instance_id=instance_id,
                algorithm='classical_cpp',
                variant='classical',
                cost=cost,
                tour_length=len(tour) if tour else 0,
                feasible=True,
                runtime_seconds=runtime,
                num_nodes=G.number_of_nodes(),
                num_edges=G.number_of_edges(),
                network_family='from_data_dir',
                size='various',
                gap_from_classical=0.0
            ))
            
            if i % 5 == 0:
                print(f"  Progress: {i}/{len(graphs)}")
                
        except Exception as e:
            print(f"  ✗ Error on {instance_id}: {e}")
    
    print(f"  ✅ {len([r for r in results if r.algorithm == 'classical_cpp'])} results")
    
    print("\n2. Greedy...")
    for i, (instance_id, G) in enumerate(graphs.items(), 1):
        try:
            start = time.time()
            cost, tour = solve_greedy_heuristic(G)
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
                num_nodes=G.number_of_nodes(),
                num_edges=G.number_of_edges(),
                network_family='from_data_dir',
                size='various',
                gap_from_classical=gap
            ))
            
            if i % 5 == 0:
                print(f"  Progress: {i}/{len(graphs)}")
                
        except:
            pass
    
    print(f"  ✅ {len([r for r in results if r.algorithm == 'greedy'])} results")
    
    # ==================== PART 2: ML ====================
    print("\n" + "="*70)
    print("PART 2/4: ML Learning")
    print("="*70)
    
    ml_solver = SimpleMLCPP()
    
    if ml_solver.train_from_solutions(training_data):
        print("  ✓ ML training complete")
        
        for i, (instance_id, G) in enumerate(graphs.items(), 1):
            try:
                start = time.time()
                cost, tour, meta = ml_solver.solve_with_learning(G)
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
                    num_nodes=G.number_of_nodes(),
                    num_edges=G.number_of_edges(),
                    network_family='from_data_dir',
                    size='various',
                    gap_from_classical=gap
                ))
                
                if i % 5 == 0:
                    print(f"  Progress: {i}/{len(graphs)}")
                    
            except:
                pass
        
        print(f"  ✅ {len([r for r in results if r.algorithm == 'ml_learned'])} ML results")
    
    # ==================== PART 3: CPP-LC ====================
    print("\n" + "="*70)
    print("PART 3/4: CPP-LC (Load-Dependent)")
    print("="*70)
    
    cpp_lc_count = 0
    for i, (instance_id, G) in enumerate(graphs.items(), 1):
        try:
            # Extract demands from graph edges
            edge_demands = {}
            for u, v, data in G.edges(data=True):
                demand = data.get('demand', 1.0)
                edge_demands[(u, v)] = demand
                edge_demands[(v, u)] = demand
            
            if not edge_demands:
                continue
            
            total_demand = sum(edge_demands.values()) / 2
            capacity = total_demand * 0.4
            
            solver = SimplifiedCPPLC(G, edge_demands, capacity)
            
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
                num_nodes=G.number_of_nodes(),
                num_edges=G.number_of_edges(),
                network_family='from_data_dir',
                size='various',
                gap_from_classical=gap,
                metadata=meta
            ))
            cpp_lc_count += 1
            
            if cpp_lc_count % 5 == 0:
                print(f"  Progress: {cpp_lc_count} CPP-LC results")
                
        except Exception as e:
            pass
    
    print(f"  ✅ {cpp_lc_count} CPP-LC results")
    
    # ==================== SAVE ====================
    print("\n" + "="*70)
    print("SAVING RESULTS")
    print("="*70)
    
    df = pd.DataFrame([r.to_dict() for r in results])
    
    output_dir = Path("results_data_dir")
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
    
    print("\n" + "="*70)
    print("✅ COMPLETE!")
    print("="*70)
    print(f"\nTotal results: {len(results)}")
    print(f"Instances: {len(graphs)}")
    
    for algo in df['algorithm'].unique():
        count = len(df[df['algorithm'] == algo])
        gap = df[df['algorithm'] == algo]['gap_from_classical'].mean()
        print(f"  {algo}: {count} results, {gap:.1f}% avg gap")
    
    cpp_lc_data = df[df['algorithm'] == 'cpp_lc_fast']
    if not cpp_lc_data.empty:
        print(f"\n🔥 CPP-LC: {cpp_lc_data['gap_from_classical'].mean():.1f}% cost increase")
    
    print("\n🎯 Next: python3 complete_plots.py")

if __name__ == "__main__":
    main()
