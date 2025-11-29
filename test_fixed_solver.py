"""
Quick Test Script - Verify Fixed CPP Solver
Tests the fixed solver on a few sample graphs before running full pipeline
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import networkx as nx
from cpp_adapters import solve_classical_cpp

print("="*70)
print("QUICK TEST: Fixed CPP Solver")
print("="*70)

# Test 1: Simple graph
print("\n[Test 1] Simple 4-node graph")
G1 = nx.Graph()
G1.add_edge(0, 1, weight=1.0)
G1.add_edge(1, 2, weight=1.5)
G1.add_edge(2, 3, weight=2.0)
G1.add_edge(3, 0, weight=1.2)
G1.add_edge(0, 2, weight=1.8)

print(f"  Nodes: {len(G1.nodes())}, Edges: {len(G1.edges())}")
result1 = solve_classical_cpp(G1, timeout_seconds=30)
print(f"  Cost: {result1['cost']:.2f}")
print(f"  Mode: {'✓ OPTIMAL' if not result1['approximation_mode'] else '⚠️ APPROX'}")
print(f"  Time: {result1['computation_time']:.3f}s")

# Test 2: Eulerian graph (already balanced)
print("\n[Test 2] Eulerian graph (5-cycle)")
G2 = nx.cycle_graph(5)
for u, v in G2.edges():
    G2[u][v]['weight'] = 1.0

print(f"  Nodes: {len(G2.nodes())}, Edges: {len(G2.edges())}")
result2 = solve_classical_cpp(G2, timeout_seconds=30)
print(f"  Cost: {result2['cost']:.2f}")
print(f"  Mode: {'✓ OPTIMAL' if not result2['approximation_mode'] else '⚠️ APPROX'}")
print(f"  Odd vertices: {result2['num_odd_vertices']}")
print(f"  Time: {result2['computation_time']:.3f}s")

# Test 3: Load a real graph from benchmarks (if available)
print("\n[Test 3] Real benchmark graph")
data_dir = Path("data")
gml_files = list(data_dir.glob("*.gml"))

if gml_files:
    test_file = gml_files[0]
    try:
        G3 = nx.read_gml(str(test_file))
        G3 = nx.convert_node_labels_to_integers(G3)
        
        print(f"  File: {test_file.name}")
        print(f"  Nodes: {len(G3.nodes())}, Edges: {len(G3.edges())}")
        
        result3 = solve_classical_cpp(G3, timeout_seconds=60)
        print(f"  Cost: {result3['cost']:.2f}")
        print(f"  Mode: {'✓ OPTIMAL' if not result3['approximation_mode'] else '⚠️ APPROX'}")
        print(f"  Time: {result3['computation_time']:.3f}s")
        
    except Exception as e:
        print(f"  ✗ Failed to load: {e}")
else:
    print("  No GML files found in data/")

# Test 4: OSM London (if available)
print("\n[Test 4] London OSM network (if available)")
london_path = Path("benchmarks/osm_derived/london_network.graphml")

if london_path.exists():
    try:
        G4 = nx.read_graphml(str(london_path))
        G4 = nx.convert_node_labels_to_integers(G4)
        
        print(f"  Nodes: {len(G4.nodes())}, Edges: {len(G4.edges())}")
        
        result4 = solve_classical_cpp(G4, timeout_seconds=300)  # 5 minute timeout
        print(f"  Cost: {result4['cost']:.2f}")
        print(f"  Mode: {'✓ OPTIMAL' if not result4['approximation_mode'] else '⚠️ APPROX'}")
        print(f"  Time: {result4['computation_time']:.3f}s")
        
        if result4['approximation_mode']:
            print(f"  Reason: {result4.get('failure_reason', 'Unknown')}")
            
    except Exception as e:
        print(f"  ✗ Failed: {e}")
else:
    print("  London network not found")

# Summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)

total_tests = 2  # Simple + Eulerian
optimal_count = 2 if (not result1['approximation_mode'] and not result2['approximation_mode']) else 0

if gml_files:
    total_tests += 1
    if 'result3' in locals() and not result3['approximation_mode']:
        optimal_count += 1

if london_path.exists():
    total_tests += 1
    if 'result4' in locals() and not result4['approximation_mode']:
        optimal_count += 1

print(f"Tests run: {total_tests}")
print(f"Optimal baselines: {optimal_count}/{total_tests}")
print(f"Success rate: {optimal_count/total_tests*100:.0f}%")

if optimal_count == total_tests:
    print("\n✅ ALL TESTS PASSED - Ready to run full pipeline!")
    print("\nNext step:")
    print("  python3 FINAL_pipeline.py")
elif optimal_count > 0:
    print("\n⚠️ PARTIAL SUCCESS - Some graphs in approximation mode")
    print("  This is OK if large graphs timed out")
    print("\nNext step:")
    print("  python3 FINAL_pipeline.py")
else:
    print("\n❌ ALL TESTS FAILED - Something is wrong")
    print("\nDebug steps:")
    print("  1. Check if NetworkX is installed correctly")
    print("  2. Verify graph files have 'weight' attributes")
    print("  3. Try increasing timeout")
