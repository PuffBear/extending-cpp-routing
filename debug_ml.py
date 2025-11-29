"""
ML Training Debugger - Find out why it's failing
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import networkx as nx
from simple_ml_cpp import SimpleMLCPP
from cpp_adapters import solve_classical_cpp

print("="*70)
print("ML TRAINING DEBUGGER")
print("="*70)

# Load some graphs
print("\n1. Loading graphs...")
graphs = []
data_dir = Path("data")
for i, gml_file in enumerate(list(data_dir.glob("*.gml"))[:10]):
    try:
        G = nx.read_gml(str(gml_file))
        graphs.append(G)
        print(f"  ✓ Loaded {gml_file.name}")
    except Exception as e:
        print(f"  ✗ Failed {gml_file.name}: {e}")

print(f"\nLoaded {len(graphs)} graphs")

# Generate training data
print("\n2. Generating training data...")
training_data = []

for i, G in enumerate(graphs):
    try:
        cost, tour = solve_classical_cpp(G)
        training_data.append((G, tour))
        print(f"  ✓ Graph {i+1}: {G.number_of_nodes()} nodes, tour length {len(tour)}")
    except Exception as e:
        print(f"  ✗ Graph {i+1} failed: {e}")

print(f"\nGenerated {len(training_data)} training examples")

# Try to train
print("\n3. Training ML model...")
ml_solver = SimpleMLCPP()

try:
    success = ml_solver.train_from_solutions(training_data)
    
    if success:
        print("  ✅ Training succeeded!")
        print(f"  Model trained: {ml_solver.trained}")
    else:
        print("  ❌ Training returned False")
        print("  This means no training data was extracted")
        
except Exception as e:
    print(f"  ❌ Training crashed: {e}")
    import traceback
    traceback.print_exc()

# Test inference
if ml_solver.trained:
    print("\n4. Testing inference...")
    
    test_graph = graphs[0]
    try:
        cost, tour, meta = ml_solver.solve_with_learning(test_graph)
        print(f"  ✓ Inference worked!")
        print(f"  Cost: {cost}")
        print(f"  Tour length: {len(tour)}")
        print(f"  Method: {meta.get('method', 'unknown')}")
    except Exception as e:
        print(f"  ✗ Inference failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\n4. Skipping inference (model not trained)")

print("\n" + "="*70)
print("DIAGNOSIS")
print("="*70)

if ml_solver.trained:
    print("✅ ML is working! Integration issue in main pipeline.")
else:
    print("❌ ML training is broken. Check simple_ml_cpp.py")
    print("\nLikely issues:")
    print("  - Feature extraction failing")
    print("  - Tour format incompatible")
    print("  - No valid training pairs generated")
