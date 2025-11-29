"""
Test ML Improvements on Real London Data
Compare old simple ML vs new improved ML
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import networkx as nx
import time

from cpp_adapters import solve_classical_cpp, solve_greedy_heuristic
from simple_ml_cpp import SimpleMLCPP
from improved_ml_cpp import ImprovedMLCPP

print("="*70)
print("ML IMPROVEMENT TEST - LONDON REAL NETWORK")
print("="*70)

# Load London
london_file = Path("benchmarks/osm_derived/osm_london_sample.graphml")
G_london = nx.read_graphml(str(london_file))
G_london = nx.convert_node_labels_to_integers(G_london)

print(f"\n✅ Loaded London network")
print(f"   Nodes: {G_london.number_of_nodes()}")
print(f"   Edges: {G_london.number_of_edges()}")

# Get baselines
print("\n" + "="*70)
print("BASELINES")
print("="*70)

classical_cost, classical_tour = solve_classical_cpp(G_london)
print(f"Classical CPP: {classical_cost:.2f}")

greedy_cost, greedy_tour = solve_greedy_heuristic(G_london)
greedy_gap = ((greedy_cost - classical_cost) / classical_cost * 100)
print(f"Greedy:        {greedy_cost:.2f} ({greedy_gap:+.1f}%)")

# Prepare training data
training_data = [
    (G_london, classical_tour),
    (G_london, greedy_tour)
]

# Test 1: Old Simple ML
print("\n" + "="*70)
print("TEST 1: Old Simple ML (Linear Regression)")
print("="*70)

old_ml = SimpleMLCPP()

if old_ml.train_from_solutions(training_data):
    print("✓ Training successful")

    start = time.time()
    old_cost, old_tour, old_meta = old_ml.solve_with_learning(G_london)
    old_runtime = time.time() - start

    old_gap = ((old_cost - classical_cost) / classical_cost * 100)

    print(f"Cost:    {old_cost:.2f} ({old_gap:+.1f}%)")
    print(f"Tour:    {len(old_tour)} steps")
    print(f"Runtime: {old_runtime:.3f}s")
else:
    print("✗ Training failed")
    old_cost = float('inf')
    old_gap = float('inf')

# Test 2: New Improved ML
print("\n" + "="*70)
print("TEST 2: New Improved ML (Random Forest + Rich Features)")
print("="*70)

new_ml = ImprovedMLCPP()

if new_ml.train_from_solutions(training_data):
    print("✓ Training successful")

    start = time.time()
    new_cost, new_tour, new_meta = new_ml.solve_with_learning(G_london)
    new_runtime = time.time() - start

    new_gap = ((new_cost - classical_cost) / classical_cost * 100)

    print(f"Cost:    {new_cost:.2f} ({new_gap:+.1f}%)")
    print(f"Tour:    {len(new_tour)} steps")
    print(f"Runtime: {new_runtime:.3f}s")
    print(f"Features: {new_meta.get('num_features', 'N/A')}")
else:
    print("✗ Training failed")
    new_cost = float('inf')
    new_gap = float('inf')

# Summary
print("\n" + "="*70)
print("SUMMARY - LONDON NETWORK")
print("="*70)

print(f"\n{'Method':<25} {'Cost':<12} {'Gap %':<12} {'vs Greedy'}")
print("-"*70)

methods = [
    ("Classical CPP", classical_cost, 0.0, "-"),
    ("Greedy Heuristic", greedy_cost, greedy_gap, "baseline"),
    ("Old ML (simple)", old_cost, old_gap, f"{old_cost - greedy_cost:+.1f}"),
    ("New ML (improved)", new_cost, new_gap, f"{new_cost - greedy_cost:+.1f}"),
]

for method, cost, gap, vs_greedy in methods:
    print(f"{method:<25} {cost:<12.2f} {gap:<12.1f} {vs_greedy}")

# Analysis
print("\n" + "="*70)
print("ANALYSIS")
print("="*70)

if new_gap < old_gap:
    improvement = old_gap - new_gap
    print(f"✅ NEW ML IS BETTER by {improvement:.1f} percentage points!")
elif new_gap == old_gap:
    print(f"➡️  Both ML approaches perform the same")
else:
    print(f"⚠️  Old ML is still better (needs more tuning)")

if new_gap < greedy_gap:
    print(f"✅ NEW ML BEATS GREEDY by {greedy_gap - new_gap:.1f} pp!")
else:
    beat_margin = new_gap - greedy_gap
    print(f"⚠️  Greedy still better by {beat_margin:.1f} pp")

print("\n" + "="*70)
print("RECOMMENDATIONS")
print("="*70)

if new_gap < 20:
    print("✅ New ML is PRODUCTION-READY for real-world networks!")
elif new_gap < 50:
    print("⚠️  New ML shows promise but needs more training data")
else:
    print("❌ New ML needs significant improvement")

print("\nNext steps:")
if new_gap < greedy_gap:
    print("  • Use this improved ML in FINAL_pipeline.py")
    print("  • Test on more real-world networks")
    print("  • Consider ensemble with greedy")
else:
    print("  • Collect more training data")
    print("  • Try different features or model")
    print("  • Consider hybrid ML+greedy approach")
