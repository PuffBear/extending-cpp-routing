# ML Improvements for Real-World CPP

## Problem

Original simple ML achieved **658.9% gap** on London network (terrible!)

## Root Causes

1. **Poor Features**: Only 5 basic features (weight, degree, simple centrality)
2. **Wrong Model**: Linear regression doesn't capture complex edge selection patterns
3. **Limited Training**: Training on approximations (empty tours)

## Improvements Made

### 1. Rich Graph Features (10 total)

**Old (5 features):**
- Edge weight
- Source degree
- Target degree
- Average degree
- Distance from depot (arbitrary)

**New (10 features):**
- Edge weight
- Source/Target **betweenness centrality** (captures importance in shortest paths)
- Source/Target **closeness centrality** (how central nodes are)
- Source/Target **clustering coefficient** (local connectivity)
- Source/Target **degree centrality** (normalized)
- **Relative weight** (edge weight / graph average)

### 2. Better Model

**Old:** `LinearRegression()` - assumes linear relationships

**New:** `RandomForestRegressor()` with:
- 50 trees
- Max depth 10
- Handles non-linear patterns
- Feature importance ranking
- Better generalization

### 3. Smarter Training Strategy

**Old:**
```python
# Only used tour order if available
# Otherwise: no training data!
```

**New:**
```python
# Strategy 1: Use tour order if available
# Strategy 2: Learn from edge characteristics
#   - Shorter edges traversed earlier
#   - High centrality edges prioritized
# Strategy 3: Train on ALL 26 graphs (not just one)
```

### 4. Improved Edge Selection

**Old:** Pick edges by predicted priority only

**New:** Trade-off between:
- Learned priority (from model)
- Travel cost (distance to edge)
- Formula: `score = priority - 0.5 * travel_cost`

## Results

| Method | Cost | Gap from Classical |
|--------|------|-------------------|
| Classical CPP | 25.91 | 0% (baseline) |
| Greedy | 28.63 | +10.5% |
| **Old ML** | 196.67 | **+658.9%** ❌ |
| **New ML** | 71.95 | **+177.7%** ⚠️ |

**Improvement:** 481 percentage points better!

## Next Steps to Further Improve

### Option 1: Ensemble Approach
```python
def ensemble_ml_greedy(G):
    ml_cost, ml_tour = ml_solver.solve(G)
    greedy_cost, greedy_tour = greedy_solver.solve(G)

    # Pick better one
    return min((ml_cost, ml_tour), (greedy_cost, greedy_tour))
```

### Option 2: More Training Data
- Add more real-world networks (not just London)
- Use data augmentation (graph perturbations)
- Transfer learning from similar networks

### Option 3: Deep Learning
- Graph Neural Networks (GNN)
- Attention mechanisms
- Learn tour construction directly

### Option 4: Hybrid ML + Local Search
```python
# Use ML for initial solution
initial_tour = ml_solver.solve(G)

# Improve with 2-opt
optimized_tour = two_opt(G, initial_tour)
```

## Current Status

✅ **ML is production-ready for COMPARISON** (shows learning is possible)
⚠️ **Not yet competitive with greedy** (needs more work)
✅ **Massive improvement over baseline** (658% → 177%)

## For Your Paper

**What you CAN claim:**
- "Demonstrated learning-augmented approach using Random Forest with 10 graph features"
- "ML approach achieves 177% gap on real London network, showing promise"
- "481 percentage point improvement over naive ML baseline"

**What you SHOULD NOT claim:**
- "ML beats classical approaches" (it doesn't yet)
- "Production-ready ML solver" (still experimental)

**Honest Positioning:**
- "Preliminary ML results show potential for future work"
- "Hybrid ML+greedy ensemble recommended for practice"
- "Deep learning (GNNs) identified as promising direction"

