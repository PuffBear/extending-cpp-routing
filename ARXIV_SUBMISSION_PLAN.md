# arXiv Submission Plan: Extending CPP Routing
**Goal**: Comprehensive, reproducible, publication-ready research

## 📊 Benchmark Design

### Network Families (4 types × 3 sizes × 10 instances = 120 base graphs)

#### 1. Grid Graphs (Structured)
- Small: 5×5 (25 nodes, 40 edges)
- Medium: 10×10 (100 nodes, 180 edges)  
- Large: 20×20 (400 nodes, 760 edges)
- **Why**: Regular structure, predictable behavior, worst-case analysis

#### 2. Random Geometric Graphs (Spatial)
- N={50, 100, 200}, radius r optimized for connectivity
- **Why**: Models wireless networks, drone routing, spatial logistics

#### 3. Clustered Graphs (Community Structure)
- 5/10/20 clusters, intra-cluster edge prob=0.7, inter-cluster=0.1
- **Why**: Models city districts, service zones, hierarchical routing

#### 4. OSM-Derived Real Networks
- Cities: NYC Manhattan, London Center, Mumbai, Tokyo, Paris
- Extract 1km², 5km², 10km² regions
- **Why**: Real-world validation, practical applicability

### Problem Variants (Full factorial design)

#### CPP-LC (Load-Dependent Costs)
**Parameters**:
- Capacity constraint: {Tight=0.3Q, Medium=0.5Q, Loose=0.8Q}
- Cost function: {Linear, Quadratic, Fuel-based}
- Demand distribution: {Uniform, Heavy-tail, Clustered}

**Total**: 4 networks × 3 sizes × 10 seeds × 3 capacities × 3 cost funcs = **1,080 instances**

#### CPP-TW (Time Windows)
**Parameters**:
- Tightness: {0.5, 1.0, 1.5, 2.0} (multiplier on minimum tour time)
- Window width: {Narrow, Medium, Wide}
- Service time distribution: {Fixed, Variable}

**Total**: 4 networks × 3 sizes × 10 seeds × 4 tightness × 3 widths = **1,440 instances**

#### Mixed CPP
**Parameters**:
- Directed fraction: {0.2, 0.4, 0.6, 0.8}
- Weight asymmetry: {Low, Medium, High}

**Total**: 4 networks × 3 sizes × 10 seeds × 4 fractions = **480 instances**

#### Windy Postman
**Parameters**:
- Asymmetry factor: {0.3, 0.5, 0.7}
- **Total**: 4 networks × 3 sizes × 10 seeds × 3 asymmetries = **360 instances**

### Learning-Augmented Framework
**Parameters**:
- GNN architecture: {GCN, GAT, GraphSAINT}
- Hidden dim: {32, 64, 128}
- Training size: {100, 500, 1000 instances}
- **Total ablations**: 3 × 3 × 3 = 27 configurations

---

## 🎯 Algorithms to Compare

### Baselines (Must-Have)
1. **Classical CPP** (Edmonds-Johnson) - Optimal for undirected
2. **Greedy Heuristic** - Fast, naive baseline
3. **2-opt Local Search** - Standard improvement heuristic
4. **Christofides for metric TSP** - Modified for CPP
5. **OR-Tools CVRP** - Industry-standard solver (for capacity variants)

### Your Contributions
6. **CPP-LC Greedy Insertion** (your implementation)
7. **CPP-TW Temporal Feasibility Checker** (your implementation)
8. **Mixed/Windy Heuristics** (your implementation)
9. **Hybrid Learning-Augmented Solver** (your novel contribution)
10. **GNN-based Solution Constructor** (your novel contribution)

---

## 📈 Metrics to Report

### Solution Quality
- **Absolute cost** (raw tour length)
- **Gap from optimal** (when known) or **gap from best-known**
- **Feasibility rate** (% of instances solved)
- **Constraint violations** (if any)

### Computational Performance
- **Runtime** (mean, median, std dev, 95th percentile)
- **Scaling behavior** (log-log plot: time vs. size)
- **Solution quality vs. time** (anytime performance)

### Statistical Analysis
- **Wilcoxon signed-rank test** (pairwise algorithm comparison)
- **Effect size** (Cohen's d)
- **Win-tie-loss records** (A vs B on all instances)
- **Performance profiles** (% of instances solved within X% of optimal)

### Learning-Specific
- **Sample efficiency** (performance vs. training data size)
- **Generalization** (train on small, test on large)
- **Ablation impact** (% contribution of each component)

---

## 📊 Key Figures for Paper

### Figure 1: Problem Taxonomy
- Venn diagram showing CPP variants and complexity classes

### Figure 2: Benchmark Instance Gallery
- 4×4 grid showing example from each network family

### Figure 3: Cost Increase Analysis (CPP-LC)
- Box plots: cost increase vs. classical by capacity/cost function
- **This validates your 4x-14x claim!**

### Figure 4: Algorithm Comparison (Main Result)
- Performance profile: % instances vs. optimality gap
- Shows your methods vs. baselines across ALL instances

### Figure 5: Scalability
- Log-log plot: runtime vs. graph size for all algorithms
- Shows computational tractability

### Figure 6: Learning Curves
- Training data size vs. solution quality
- Shows sample efficiency of learned approach

### Figure 7: Ablation Study
- Bar chart: performance drop when removing each component
- Shows what matters in your hybrid approach

### Figure 8: Real-World Case Study
- OSM map with computed tour overlaid
- Shows practical applicability

---

## 📋 Key Tables for Paper

### Table 1: Complexity Hierarchy
| Variant | Complexity | Optimal? | Reference |
|---------|-----------|----------|-----------|
| CPP | O(|V|³) | ✓ | Edmonds-Johnson |
| CPP-LC | NP-hard | ✗ | Your work |
| CPP-TW | NP-hard | ✗ | Your work |
| Mixed CPP | NP-hard | ✗ | Literature |
| Windy | NP-hard | ✗ | Literature |

### Table 2: Benchmark Statistics
- Network family characteristics (nodes, edges, density, clustering)

### Table 3: Algorithm Comparison (Summary)
| Algorithm | Mean Gap | Median Time | Win Rate | Feasibility |
|-----------|----------|-------------|----------|-------------|
| Classical | 0% | 0.1s | Baseline | 100% |
| Greedy | +45% | 0.01s | 12% | 98% |
| OR-Tools | +15% | 2.3s | 34% | 95% |
| **Your Method** | **+8%** | **0.5s** | **54%** | **100%** |

### Table 4: CPP-LC Analysis
- Cost increase by capacity constraint and cost function
- Shows 4x-14x validation

### Table 5: Ablation Study Results
- Component removal impact on performance

### Table 6: Real-World Results
- City-by-city performance on OSM networks

---

## 🔬 Statistical Rigor Checklist

- [ ] **30+ runs** per configuration (different random seeds)
- [ ] **Fixed random seeds** documented for reproducibility
- [ ] **Wilcoxon signed-rank tests** for pairwise comparisons
- [ ] **95% confidence intervals** on all reported metrics
- [ ] **Effect sizes** (Cohen's d) reported alongside p-values
- [ ] **Multiple testing correction** (Bonferroni/Holm) if needed
- [ ] **Performance profiles** showing distribution of results

---

## 💻 Code & Reproducibility

### GitHub Repository Structure
```
extending-cpp-routing/
├── src/                    # All implementations
│   ├── algorithms/         # CPP variants
│   ├── baselines/          # Comparison methods
│   ├── learning/           # GNN models
│   └── utils/              # Helpers
├── benchmarks/             # Instance generators
│   ├── grid.py
│   ├── random_geometric.py
│   ├── clustered.py
│   └── osm_loader.py
├── experiments/            # Experiment scripts
│   ├── run_all.py
│   ├── ablations.py
│   └── statistical_analysis.py
├── results/                # Raw data (CSV)
├── figures/                # Publication figures (PDF)
├── tables/                 # LaTeX tables
├── data/                   # Benchmark instances
├── requirements.txt        # Dependencies
├── README.md               # How to reproduce
└── LICENSE
```

### Reproducibility Requirements
- **README** with exact setup instructions
- **requirements.txt** with pinned versions
- **Makefile** to run all experiments with one command
- **Data DOI** (Zenodo/Figshare) for benchmark instances
- **Seeds documented** in all experiment scripts
- **Docker container** (optional but impressive)

---

## ✍️ Writing Strategy

### Abstract (250 words)
- **Problem**: CPP variants with real-world constraints
- **Gap**: No unified framework, limited empirical analysis
- **Contribution**: Comprehensive study + learning-augmented solver
- **Results**: X% better than baselines, validated on real OSM networks

### Introduction
- Motivation: Real-world routing problems
- Limitations of classical CPP
- Your contributions (3-4 bullet points)
- Paper organization

### Section 2: Background & Related Work
- Classical CPP (Edmonds-Johnson)
- Complexity hierarchy (your Table 1)
- Existing variants (literature review)
- Learning for combinatorial optimization

### Section 3: Problem Formulations
- CPP-LC (load-dependent costs)
- CPP-TW (time windows)
- Mixed/Windy variants
- Unified notation

### Section 4: Algorithms
- Classical baselines
- Your heuristics for each variant
- Learning-augmented framework
- Complexity analysis

### Section 5: Experimental Setup
- Benchmark design (4 network families)
- Metrics and statistical methodology
- Implementation details

### Section 6: Results
- 6.1: CPP-LC analysis (validates 4x-14x)
- 6.2: Algorithm comparison (main result)
- 6.3: Scalability analysis
- 6.4: Learning ablations
- 6.5: Real-world validation (OSM)

### Section 7: Discussion
- Insights from experiments
- When to use which method
- Limitations

### Section 8: Conclusion
- Summary of contributions
- Future work (dynamic routing, online algorithms)

---

## ⏱️ Timeline (8 weeks)

### Week 1-2: Infrastructure
- [ ] Implement 4 network generators
- [ ] Create parameter sweep framework
- [ ] Generate all 3,360 benchmark instances
- [ ] Set up experiment tracking (WandB/MLflow)

### Week 3-4: Experiments
- [ ] Integrate OR-Tools baseline
- [ ] Run all algorithms on all instances (may take 24-48hrs)
- [ ] Collect all metrics in structured format
- [ ] Checkpoint: Have complete results CSV

### Week 5: Analysis
- [ ] Statistical significance testing
- [ ] Generate all figures (8 main + supplementary)
- [ ] Generate all tables (6 main + supplementary)
- [ ] Ablation studies
- [ ] Checkpoint: All figures/tables ready

### Week 6: Real-World
- [ ] Download OSM data for 5 cities
- [ ] Run experiments on real networks
- [ ] Create case study visualizations
- [ ] Checkpoint: Real-world validation complete

### Week 7: Writing
- [ ] Draft all sections based on results
- [ ] Integrate figures/tables
- [ ] Write discussion and related work
- [ ] Internal review/revision

### Week 8: Finalization
- [ ] Polish writing (grammar, clarity)
- [ ] Prepare code repository for release
- [ ] Create reproducibility README
- [ ] arXiv submission
- [ ] Optional: Conference submission (NeurIPS, ICML, AAAI)

---

## 🎓 Target Venues (Post-arXiv)

### Top-Tier Conferences
1. **NeurIPS** (ML for combinatorial optimization)
2. **ICML** (learning-augmented algorithms)
3. **AAAI** (AI planning and optimization)
4. **IJCAI** (multi-disciplinary AI)

### Operations Research
1. **INFORMS Annual Meeting**
2. **EURO** (European OR conference)

### Journals (if going that route)
1. **Operations Research** (top-tier OR journal)
2. **Computers & Operations Research**
3. **European Journal of Operational Research**
4. **Transportation Science** (if focusing on routing)

---

## 🚀 Success Criteria

### Minimum Viable Submission
- [ ] 200+ benchmark instances across 4 network families
- [ ] 5+ baseline comparisons
- [ ] Statistical significance on all claims
- [ ] 1 real-world OSM case study
- [ ] Reproducible code on GitHub

### Strong Submission (Target)
- [ ] 1,000+ benchmark instances
- [ ] 8+ algorithm comparisons
- [ ] Rigorous statistical analysis
- [ ] 5+ OSM cities validated
- [ ] Ablation studies for learning approach
- [ ] Performance profiles and scaling analysis
- [ ] Public benchmark suite for community

### Exceptional Submission (Stretch Goal)
- [ ] All of above +
- [ ] Novel theoretical contribution (approximation bound?)
- [ ] Comparison with commercial solvers (Gurobi)
- [ ] Interactive visualization tool
- [ ] Kaggle/benchmark challenge launched

---

## 📝 Notes & Ideas

### Potential Novel Contributions
1. **First comprehensive empirical study** of CPP variants
2. **Learning-augmented CPP** (first use of GNNs for CPP?)
3. **Unified benchmark suite** (released for community)
4. **Real-world validation** on OSM networks
5. **Characterization of hardness** (when is learning better than heuristics?)

### Potential Theoretical Contributions
- Approximation bound for CPP-LC greedy insertion?
- Hardness of approximation for CPP-TW?
- Competitive ratio for learning-augmented approach?

### Story to Tell
"Classical CPP is well-solved, but real-world routing has constraints (capacity, time windows) that make it NP-hard. We provide the first comprehensive study of these variants, develop both heuristic and learning-based solvers, and validate on real street networks."

---

## 🎯 Implementation Priorities

### P0 (Critical - Must Have)
1. 4 network generators (grid, RGG, clustered, OSM)
2. CPP-LC experiments (validates main claim)
3. Baseline comparisons (greedy, OR-Tools)
4. Statistical analysis framework
5. Core figures (cost increase, algorithm comparison, scalability)

### P1 (High Priority - Should Have)
1. CPP-TW experiments
2. Mixed/Windy experiments
3. Learning ablation studies
4. OSM real-world validation
5. All 8 main figures + 6 tables

### P2 (Nice to Have - Could Have)
1. Interactive visualizations
2. Theoretical analysis
3. Comparison with commercial solvers
4. Docker containerization
5. Extensive supplementary material

---

**Let's build a paper that gets accepted to NeurIPS! 🚀**
