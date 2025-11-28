# 🎯 ArXiv Submission Checklist

## Phase 1: Benchmark Generation ✅ (This Week)

### Setup
- [ ] Install dependencies: `pip3 install networkx numpy pandas scipy matplotlib seaborn`
- [ ] Install OSM support: `pip3 install osmnx geopandas`
- [ ] Install OR-Tools: `pip3 install ortools`
- [ ] Test installation: `python3 -c "import networkx, numpy, pandas; print('✓ Ready')"`

### Generate Benchmarks
- [ ] Test system: `python3 test_benchmarks.py`
- [ ] Generate full dataset: `python3 generate_benchmarks.py --instances-per-config 20`
- [ ] Download OSM: `python3 generate_benchmarks.py --include-osm` (or run separately)
- [ ] Verify output: `cat benchmarks/BENCHMARK_SUMMARY.md`
- [ ] **Expected**: ~180 instances (20 per config × 9 configs)
- [ ] **Disk space**: ~100-200 MB

---

## Phase 2: Baseline Implementation (Week 2)

### Classical CPP
- [ ] Implement Edmonds-Johnson algorithm (or verify existing `cpp_solver.py`)
- [ ] Test on all instances
- [ ] Record: cost, runtime

### Greedy Heuristics
- [ ] Implement greedy edge addition
- [ ] Implement nearest neighbor heuristic
- [ ] Test on all instances

### OR-Tools Baseline (for CPP-LC)
- [ ] Integrate OR-Tools CVRP solver
- [ ] Map CPP-LC to CVRP formulation
- [ ] Test on capacity-constrained instances

### Local Search
- [ ] Implement 2-opt improvement
- [ ] Test on all instances

---

## Phase 3: Run All Experiments (Week 3-4)

### Experiment 1: CPP-LC Cost Increase
**Goal**: Validate 4x-14x cost increase claim

- [ ] Run classical CPP on all instances
- [ ] Run CPP-LC with different cost functions:
  - [ ] Linear cost function
  - [ ] Quadratic cost function
  - [ ] Fuel consumption model
- [ ] Run with different capacity constraints:
  - [ ] Tight (30% of demand)
  - [ ] Medium (50% of demand)
  - [ ] Loose (80% of demand)
- [ ] **Expected result**: 400-1400% cost increase validated
- [ ] **Data file**: `results/cpp_lc_cost_increase.csv`

### Experiment 2: Algorithm Comparison
**Goal**: Show your methods competitive with/better than baselines

- [ ] Run all algorithms × all instances (180+ instances × 6+ algorithms)
- [ ] Collect metrics:
  - [ ] Solution cost
  - [ ] Runtime
  - [ ] Optimality gap (vs. classical when applicable)
  - [ ] Feasibility rate
- [ ] Save results: `results/algorithm_comparison.csv`
- [ ] **Runtime estimate**: 2-6 hours on single machine

### Experiment 3: Scalability Analysis
**Goal**: Show computational tractability

- [ ] Group instances by size (small/medium/large)
- [ ] For each algorithm:
  - [ ] Plot runtime vs. graph size
  - [ ] Plot solution quality vs. graph size
- [ ] Fit scaling curves (linear, quadratic, cubic)
- [ ] **Data file**: `results/scalability_analysis.csv`

### Experiment 4: Learning Ablations
**Goal**: Show what components matter in hybrid approach

- [ ] Full model (GNN + heuristics)
- [ ] Ablation 1: GNN only
- [ ] Ablation 2: Heuristics only
- [ ] Ablation 3: MLP instead of GNN
- [ ] Ablation 4: Different GNN architectures (GCN, GAT, GraphSAINT)
- [ ] Ablation 5: Different hidden dimensions (32, 64, 128)
- [ ] **Data file**: `results/learning_ablations.csv`

### Experiment 5: OSM Real-World Validation
**Goal**: Show practical applicability

- [ ] Run all algorithms on 5 OSM cities
- [ ] Detailed analysis per city
- [ ] Pick 1 city for detailed case study
- [ ] Create visualization of tour on map
- [ ] **Data file**: `results/osm_validation.csv`

---

## Phase 4: Statistical Analysis (Week 5)

### Significance Testing
- [ ] Wilcoxon signed-rank test (pairwise algorithm comparison)
- [ ] Compute p-values for all pairs
- [ ] Apply Bonferroni correction for multiple testing
- [ ] **Output**: `results/statistical_tests.csv`

### Confidence Intervals
- [ ] 95% CI on mean cost for each algorithm
- [ ] 95% CI on mean runtime
- [ ] Bootstrap if needed (1000 samples)
- [ ] **Output**: Include in tables

### Effect Sizes
- [ ] Cohen's d for algorithm pairs
- [ ] Interpret: small (0.2), medium (0.5), large (0.8)
- [ ] **Output**: `results/effect_sizes.csv`

### Performance Profiles
- [ ] For each algorithm, compute % of instances solved within X% of optimal
- [ ] X = [0%, 5%, 10%, 20%, 50%]
- [ ] Plot cumulative curves
- [ ] **Output**: Figure 4 in paper

---

## Phase 5: Generate Figures (Week 6)

### Figure 1: Problem Taxonomy
- [ ] Venn diagram of CPP variants
- [ ] Show complexity classes
- [ ] **Tool**: PowerPoint/Illustrator → PDF
- [ ] **File**: `figures/fig1_taxonomy.pdf`

### Figure 2: CPP-LC Cost Increase (KEY RESULT!)
- [ ] Box plots by cost function
- [ ] Show 4x-14x range
- [ ] Annotate with statistics
- [ ] **Tool**: Python matplotlib/seaborn
- [ ] **File**: `figures/fig2_cpp_lc_increase.pdf`

### Figure 3: Algorithm Comparison
- [ ] Box plots of optimality gaps
- [ ] One per network family
- [ ] Statistical significance markers
- [ ] **File**: `figures/fig3_algorithm_comparison.pdf`

### Figure 4: Performance Profiles
- [ ] Cumulative curves (% instances vs. % gap)
- [ ] All algorithms on same plot
- [ ] **File**: `figures/fig4_performance_profiles.pdf`

### Figure 5: Scalability
- [ ] Log-log plot: runtime vs. graph size
- [ ] All algorithms, different colors
- [ ] Fit lines showing O(n²), O(n³)
- [ ] **File**: `figures/fig5_scalability.pdf`

### Figure 6: Learning Curves
- [ ] Training data size vs. solution quality
- [ ] Show sample efficiency
- [ ] **File**: `figures/fig6_learning_curves.pdf`

### Figure 7: Ablation Study
- [ ] Bar chart: performance drop when removing components
- [ ] Show contribution of each component
- [ ] **File**: `figures/fig7_ablations.pdf`

### Figure 8: OSM Case Study
- [ ] Map with computed tour overlay
- [ ] Pick Manhattan or London
- [ ] Show edge services, route
- [ ] **Tool**: OSMnx + matplotlib
- [ ] **File**: `figures/fig8_osm_case_study.pdf`

---

## Phase 6: Generate Tables (Week 6)

### Table 1: Complexity Hierarchy
- [ ] List all CPP variants
- [ ] Complexity class (P, NP-hard)
- [ ] Optimal algorithm (if P)
- [ ] Reference
- [ ] **File**: `tables/table1_complexity.tex`

### Table 2: Benchmark Statistics
- [ ] Network family characteristics
- [ ] Nodes, edges, density, clustering per family/size
- [ ] **File**: `tables/table2_benchmark_stats.tex`

### Table 3: Algorithm Comparison Summary
- [ ] Mean optimality gap ± std
- [ ] Median runtime
- [ ] Win rate (% instances where algorithm is best)
- [ ] **File**: `tables/table3_algorithm_summary.tex`

### Table 4: CPP-LC Analysis
- [ ] Cost increase by capacity constraint
- [ ] Cost increase by cost function
- [ ] Min/Mean/Median/Max
- [ ] **File**: `tables/table4_cpp_lc_detailed.tex`

### Table 5: Statistical Tests
- [ ] Pairwise comparisons
- [ ] p-values after correction
- [ ] Effect sizes
- [ ] **File**: `tables/table5_statistical_tests.tex`

### Table 6: OSM Validation
- [ ] Results per city
- [ ] Algorithm performance on real networks
- [ ] **File**: `tables/table6_osm_results.tex`

---

## Phase 7: Write Paper (Week 7)

### Sections
- [ ] **Abstract** (250 words)
  - [ ] Problem statement
  - [ ] Gap in literature
  - [ ] Your contributions (3-4 bullets)
  - [ ] Key results (4x-14x, algorithm performance)

- [ ] **Introduction** (2-3 pages)
  - [ ] Motivation: real-world routing
  - [ ] Limitations of classical CPP
  - [ ] Your contributions
  - [ ] Paper organization

- [ ] **Related Work** (2 pages)
  - [ ] Classical CPP (Edmonds-Johnson)
  - [ ] CPP variants (literature review)
  - [ ] Learning for combinatorial optimization
  - [ ] Position your work

- [ ] **Problem Formulations** (2-3 pages)
  - [ ] CPP-LC definition
  - [ ] CPP-TW definition
  - [ ] Mixed/Windy definitions
  - [ ] Unified notation

- [ ] **Algorithms** (3-4 pages)
  - [ ] Classical baselines
  - [ ] Your heuristics (CPP-LC, CPP-TW)
  - [ ] Learning-augmented framework
  - [ ] Complexity analysis

- [ ] **Experimental Setup** (2 pages)
  - [ ] Benchmark design (4 families)
  - [ ] Metrics
  - [ ] Statistical methodology
  - [ ] Implementation details

- [ ] **Results** (4-5 pages)
  - [ ] 6.1: CPP-LC analysis (validates 4x-14x)
  - [ ] 6.2: Algorithm comparison
  - [ ] 6.3: Scalability
  - [ ] 6.4: Learning ablations
  - [ ] 6.5: OSM validation

- [ ] **Discussion** (1-2 pages)
  - [ ] Key insights
  - [ ] When to use which method
  - [ ] Limitations
  - [ ] Future work

- [ ] **Conclusion** (0.5-1 page)
  - [ ] Summary
  - [ ] Contributions
  - [ ] Impact

### Supplementary Material
- [ ] Additional figures
- [ ] Full statistical test results
- [ ] Algorithm pseudocode
- [ ] Hyperparameter details
- [ ] Extended OSM analysis

---

## Phase 8: Code Release (Week 7-8)

### Clean Repository
- [ ] Remove debugging code
- [ ] Add docstrings to all functions
- [ ] Add type hints
- [ ] Format code (black, autopep8)

### Documentation
- [ ] README.md with setup instructions
- [ ] requirements.txt with pinned versions
- [ ] INSTALL.md for detailed setup
- [ ] REPRODUCE.md for exact reproduction

### Reproducibility
- [ ] Makefile to run all experiments: `make all`
- [ ] Script to download data: `./download_data.sh`
- [ ] Script to generate figures: `python generate_figures.py`
- [ ] Script to generate tables: `python generate_tables.py`
- [ ] **Test**: Fresh clone + run = reproduce all results

### Optional but Impressive
- [ ] Docker container for reproducibility
- [ ] Jupyter notebooks with examples
- [ ] Interactive visualization tool
- [ ] CI/CD for tests

---

## Phase 9: Data Release (Week 8)

### Prepare Data Package
- [ ] Benchmark instances (all .graphml files)
- [ ] Metadata (all .json files)
- [ ] README for dataset
- [ ] LICENSE (CC BY 4.0 or MIT)

### Upload to Repository
- [ ] Zenodo (preferred for academic data)
- [ ] Figshare
- [ ] IEEE DataPort
- [ ] Get DOI

### Dataset Description
- [ ] Number of instances
- [ ] Network families
- [ ] File formats
- [ ] How to use
- [ ] Citation information

---

## Phase 10: arXiv Submission (Week 8)

### Pre-submission Checklist
- [ ] Paper written (LaTeX source)
- [ ] All figures included (PDF format, 300 DPI)
- [ ] All tables formatted (LaTeX)
- [ ] References complete (BibTeX)
- [ ] Supplementary material prepared
- [ ] Code repository public
- [ ] Data repository public with DOI
- [ ] Author information correct

### Submission Package
- [ ] main.tex (paper source)
- [ ] references.bib
- [ ] figures/*.pdf (all figures)
- [ ] tables/*.tex (optional, can inline)
- [ ] supplementary.pdf (if applicable)

### arXiv Categories
- [ ] Primary: cs.DS (Data Structures and Algorithms)
- [ ] Secondary: cs.LG (Machine Learning)
- [ ] Secondary: cs.AI (Artificial Intelligence)

### Submit
- [ ] Create arXiv account (if needed)
- [ ] Upload LaTeX source
- [ ] Compile check
- [ ] Preview PDF
- [ ] Add abstract
- [ ] Add authors
- [ ] Select categories
- [ ] Add comments (code/data links)
- [ ] **Submit!**

### Post-submission
- [ ] Share arXiv link on Twitter/LinkedIn
- [ ] Post to Reddit (r/MachineLearning, r/compsci)
- [ ] Email to relevant mailing lists
- [ ] Add to your website/CV

---

## Optional: Conference Submission

### Target Conferences (with deadlines)

**Machine Learning:**
- [ ] NeurIPS (May deadline) - Top tier
- [ ] ICML (January deadline) - Top tier
- [ ] AAAI (August deadline) - Top tier
- [ ] IJCAI (January deadline) - Top tier

**Operations Research:**
- [ ] INFORMS Annual Meeting (rolling)
- [ ] EURO Conference (varies)

**Algorithms:**
- [ ] SODA (July deadline)
- [ ] ESA (April deadline)

### Conference Preparation
- [ ] Check page limits (typically 8-10 pages)
- [ ] Adapt paper to page limit (move details to appendix)
- [ ] Follow formatting guidelines
- [ ] Prepare rebuttal for reviews
- [ ] Submit to 2-3 conferences (staggered deadlines)

---

## Success Metrics

### Minimum Viable Paper
- ✅ 100+ benchmark instances
- ✅ 4+ baseline comparisons
- ✅ Statistical significance tests
- ✅ 1 real-world case study (OSM)
- ✅ Reproducible code
- **Outcome**: arXiv submission, workshop paper

### Strong Paper
- ✅ 150+ benchmark instances
- ✅ 6+ algorithm comparisons
- ✅ Rigorous statistical analysis
- ✅ 3+ OSM cities
- ✅ Ablation studies
- ✅ Performance profiles
- **Outcome**: Conference submission (AAAI, IJCAI)

### Exceptional Paper
- ✅ 200+ benchmark instances
- ✅ 8+ algorithms including commercial solvers
- ✅ Novel theoretical contribution
- ✅ 5+ OSM cities
- ✅ Complete ablations
- ✅ Public benchmark challenge
- ✅ Interactive demo
- **Outcome**: Top-tier conference (NeurIPS, ICML)

---

## Timeline Summary

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1 | Benchmark Generation | 180 instances, summary report |
| 2 | Baseline Implementation | 5 baseline algorithms working |
| 3 | Run Experiments (Part 1) | CPP-LC, algorithm comparison data |
| 4 | Run Experiments (Part 2) | Scalability, ablations, OSM data |
| 5 | Statistical Analysis | Significance tests, CIs, effect sizes |
| 6 | Generate Assets | 8 figures, 6 tables (publication-ready) |
| 7 | Write Paper | Complete draft (15-20 pages) |
| 8 | Finalize & Submit | Code release, data release, arXiv! |

---

## Current Status

✅ **DONE: Benchmark Generation System**
- Complete generator implemented
- OSM loader ready
- Test suite created
- Documentation complete

⏳ **NEXT: Install & Generate**
- Install dependencies
- Test system
- Generate full dataset
- Verify benchmarks

---

## Quick Commands Reference

```bash
# Install dependencies
pip3 install networkx numpy pandas scipy matplotlib seaborn osmnx ortools

# Test system
python3 test_benchmarks.py

# Generate benchmarks
python3 generate_benchmarks.py --instances-per-config 20 --include-osm

# Verify
cat benchmarks/BENCHMARK_SUMMARY.md

# List instances
ls benchmarks/*/*.graphml | wc -l

# Run experiments (later)
python3 src/run_experiments.py

# Generate figures (later)
python3 src/generate_all_figures.py

# Generate tables (later)
python3 src/generate_all_tables.py
```

---

**Remember**: Start small, test often, iterate quickly. You've got this! 🚀
