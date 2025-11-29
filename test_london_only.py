"""
Test ALL algorithms on the REAL London data
Verify everything works before running full pipeline
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import networkx as nx
import random
import time

from cpp_adapters import solve_classical_cpp, solve_greedy_heuristic
from cpp_lc_corrected import solve_cpp_lc_corrected
from simple_ml_cpp import SimpleMLCPP

print("="*70)
print("TESTING ALL ALGORITHMS ON REAL LONDON DATA")
print("="*70)

# Load London graph
london_file = Path("benchmarks/osm_derived/osm_london_sample.graphml")
G_london = nx.read_graphml(str(london_file))

print(f"\n✅ Loaded London network")
print(f"   Nodes: {G_london.number_of_nodes()}")
print(f"   Edges: {G_london.number_of_edges()}")

# Check node types (GraphML sometimes loads as strings)
first_node = list(G_london.nodes())[0]
print(f"   Node type: {type(first_node)}")
if isinstance(first_node, str):
    print("   ⚠️  Nodes are strings, converting to integers...")
    G_london = nx.convert_node_labels_to_integers(G_london)
    print("   ✓ Converted to integers")

results = {}

# TEST 1: Classical CPP
print("\n" + "="*70)
print("TEST 1: Classical CPP")
print("="*70)
try:
    start = time.time()
    cost, tour = solve_classical_cpp(G_london)
    runtime = time.time() - start

    print(f"✅ Classical CPP:")
    print(f"   Cost: {cost:.2f}")
    print(f"   Tour length: {len(tour)} steps")
    print(f"   Runtime: {runtime:.3f}s")

    results['classical_cpp'] = {
        'cost': cost,
        'tour_length': len(tour),
        'runtime': runtime,
        'status': 'SUCCESS'
    }
except Exception as e:
    print(f"❌ Classical CPP FAILED: {e}")
    results['classical_cpp'] = {'status': 'FAILED', 'error': str(e)}

# TEST 2: Greedy Heuristic
print("\n" + "="*70)
print("TEST 2: Greedy Heuristic")
print("="*70)
try:
    start = time.time()
    cost, tour = solve_greedy_heuristic(G_london)
    runtime = time.time() - start

    classical_cost = results.get('classical_cpp', {}).get('cost', cost)
    gap = ((cost - classical_cost) / classical_cost * 100) if classical_cost > 0 else 0

    print(f"✅ Greedy Heuristic:")
    print(f"   Cost: {cost:.2f}")
    print(f"   Tour length: {len(tour)} steps")
    print(f"   Runtime: {runtime:.3f}s")
    print(f"   Gap from classical: {gap:.1f}%")

    results['greedy'] = {
        'cost': cost,
        'tour_length': len(tour),
        'runtime': runtime,
        'gap': gap,
        'status': 'SUCCESS'
    }
except Exception as e:
    print(f"❌ Greedy FAILED: {e}")
    results['greedy'] = {'status': 'FAILED', 'error': str(e)}

# TEST 3: ML Learning
print("\n" + "="*70)
print("TEST 3: ML Learning")
print("="*70)
try:
    ml_solver = SimpleMLCPP()

    # Train on London itself (self-supervised)
    classical_tour = results.get('classical_cpp', {}).get('cost')
    if 'classical_cpp' in results and results['classical_cpp']['status'] == 'SUCCESS':
        _, classical_tour_path = solve_classical_cpp(G_london)
        training_data = [(G_london, classical_tour_path)]

        if ml_solver.train_from_solutions(training_data):
            print("   ✓ Training complete")

            start = time.time()
            cost, tour, meta = ml_solver.solve_with_learning(G_london)
            runtime = time.time() - start

            classical_cost = results.get('classical_cpp', {}).get('cost', cost)
            gap = ((cost - classical_cost) / classical_cost * 100) if classical_cost > 0 else 0

            print(f"✅ ML Learning:")
            print(f"   Cost: {cost:.2f}")
            print(f"   Tour length: {len(tour)} steps")
            print(f"   Runtime: {runtime:.3f}s")
            print(f"   Gap from classical: {gap:.1f}%")

            results['ml_learned'] = {
                'cost': cost,
                'tour_length': len(tour),
                'runtime': runtime,
                'gap': gap,
                'status': 'SUCCESS'
            }
        else:
            print("❌ ML training failed")
            results['ml_learned'] = {'status': 'FAILED', 'error': 'Training failed'}
    else:
        print("⚠️  Skipping ML (classical CPP failed)")
        results['ml_learned'] = {'status': 'SKIPPED', 'reason': 'No training data'}

except Exception as e:
    print(f"❌ ML FAILED: {e}")
    results['ml_learned'] = {'status': 'FAILED', 'error': str(e)}

# TEST 4: CPP-LC (Load-Dependent Costs)
print("\n" + "="*70)
print("TEST 4: CPP-LC (Load-Dependent Costs)")
print("="*70)
try:
    # Generate realistic demands for London
    random.seed(42)
    edge_demands = {}
    for u, v in G_london.edges():
        # Demand based on road length/weight
        base_demand = G_london[u][v].get('weight', 1.0) * random.uniform(0.5, 2.0)
        edge_demands[(u, v)] = base_demand
        edge_demands[(v, u)] = base_demand

    total_demand = sum(edge_demands.values()) / 2
    capacity = total_demand * 0.4  # Tight 40% capacity

    print(f"   Total demand: {total_demand:.2f}")
    print(f"   Vehicle capacity: {capacity:.2f} (40% of total)")

    start = time.time()
    cost, tour, meta = solve_cpp_lc_corrected(G_london, edge_demands, capacity)
    runtime = time.time() - start

    classical_cost = results.get('classical_cpp', {}).get('cost', cost)
    gap = ((cost - classical_cost) / classical_cost * 100) if classical_cost > 0 else 0

    print(f"✅ CPP-LC:")
    print(f"   Classical cost: {classical_cost:.2f}")
    print(f"   Load-dependent cost: {cost:.2f}")
    print(f"   Cost increase: {gap:.1f}%")
    print(f"   Depot trips: {meta.get('trips_to_depot', 'N/A')}")
    print(f"   Runtime: {runtime:.3f}s")

    if gap > 0:
        print(f"   ✅ POSITIVE increase (as expected!)")
    else:
        print(f"   ⚠️  WARNING: Should be positive!")

    results['cpp_lc'] = {
        'cost': cost,
        'classical_cost': classical_cost,
        'gap': gap,
        'depot_trips': meta.get('trips_to_depot', 0),
        'runtime': runtime,
        'status': 'SUCCESS'
    }
except Exception as e:
    print(f"❌ CPP-LC FAILED: {e}")
    import traceback
    traceback.print_exc()
    results['cpp_lc'] = {'status': 'FAILED', 'error': str(e)}

# SUMMARY
print("\n" + "="*70)
print("SUMMARY - LONDON REAL NETWORK RESULTS")
print("="*70)

print(f"\n{'Algorithm':<20} {'Status':<10} {'Cost':<15} {'Gap %':<10}")
print("-"*70)

for algo, data in results.items():
    status = data.get('status', 'UNKNOWN')
    cost = data.get('cost', '-')
    gap = data.get('gap', '-')

    if isinstance(cost, (int, float)):
        cost = f"{cost:.2f}"
    if isinstance(gap, (int, float)):
        gap = f"{gap:.1f}"

    print(f"{algo:<20} {status:<10} {cost:<15} {gap:<10}")

# Success check
successes = sum(1 for r in results.values() if r.get('status') == 'SUCCESS')
total = len(results)

print("\n" + "="*70)
if successes == total:
    print(f"✅ ALL {total}/{total} ALGORITHMS WORKING ON LONDON DATA!")
    print("\nYou can now run: python3 FINAL_pipeline.py")
else:
    print(f"⚠️  {successes}/{total} algorithms working")
    print("\nFix the failed algorithms before running full pipeline")
print("="*70)
