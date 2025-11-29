# Pipeline Results Summary - 2025-11-29

## SUCCESS: Fixed Matching Algorithm Works!

### Key Achievement
✅ **27/27 graphs achieved OPTIMAL baselines** (no approximation mode!)

### Graphs Tested (in order)
All showed `✓ OPTIMAL` status with proper minimum-weight matching:

1. clustered_medium_14 - cost=569.98
2. random_medium_10 - cost=3664.27
3. random_small_11 - cost=575.44
4. grid_medium_1 - cost=549.78
5. grid_medium_0 - cost=653.39
6. grid_medium_4 - cost=567.26
7. random_small_10 - cost=650.27
8. random_small_13 - cost=694.19
9. grid_medium_2 - cost=629.86
10. random_medium_5 - cost=3422.25
11. grid_medium_3 - cost=630.04
12. random_small_12 - cost=730.03
13. random_small_9 - cost=610.69
14. random_small_8 - cost=640.05
15. random_small_7 - cost=710.75
16. clustered_medium_12 - cost=609.64
17. random_medium_8 - cost=3704.78
18. random_medium_9 - cost=3467.81
19. grid_small_6 - cost=188.68
20. grid_small_4 - cost=169.11
21. grid_small_5 - cost=211.11
22. grid_small_1 - cost=214.48
23. grid_small_0 - cost=182.22
24. grid_small_2 - cost=220.24
25. grid_small_3 - cost=195.68
26. synthetic_urban_200 - cost=1338.30 (96 odd vertices, 1.06s)
27. synthetic_highway_100 - cost=500.49 (48 odd vertices, 0.10s)

**Graph 28** (likely northern_zones): 1614 odd vertices - TOO LARGE, user interrupted

### Statistics from Successful Graphs

**Odd Vertices Distribution**:
- Small graphs (20 nodes): 10-16 odd vertices
- Medium graphs (56 nodes): 22-26 odd vertices  
- Grid graphs: 10-22 odd vertices
- Clustered graphs: 24-26 odd vertices
- Large synthetic (200 nodes): 96 odd vertices
- Very large (northern_zones): 1614 odd vertices → SKIPPED

**Runtime Performance**:
- Grid small (10 odd vertices): 0.00s (instant)
- Grid medium (22 odd vertices): 0.01s
- Random medium (26-32 odd vertices): 0.04-0.05s
- Synthetic urban 200 (96 odd vertices): 1.06s
- Synthetic highway 100 (48 odd vertices): 0.10s

**Matching Success**: 100% (27/27)
**Approximation Mode**: 0% (0/27)

### Implications for Paper

1. **We can now honestly report**:
   - ALL 27 tested graphs have true optimal baselines
   - No approximation mode artifacts
   - Proper Edmonds' matching algorithm working correctly

2. **Expected gaps will NOW be positive**:
   - OLD (broken): Greedy -37.5%, ML -73.7% (negative = artifact)
   - NEW (fixed): Greedy ~10-15%, ML ~15-20% (positive = correct)

3. **We removed the scalability blocker**:
   - Successfully excluded northern_zones (1614 odd vertices)
   - Can run full pipeline on manageable 27-graph suite
   - Can add more real OSM networks in 100-300 node range

### Next Steps

1. **Re-run full pipeline** (without northern_zones):
   ```bash
   python3 FINAL_pipeline.py
   ```
   Expected runtime: 10-15 minutes for 27 graphs × 4 algorithms

2. **Analyze results CSV**:
   - All `baseline_type` should be `OPTIMAL`
   - Greedy and ML gaps should be POSITIVE
   - CPP-LC gaps should be POSITIVE (4-10% range)

3. **Update paper.tex**:
   - Remove "144.9 pp improvement" misleading claim
   - Update abstract with honest results
   - Revise Section 6 to reflect proper baselines
   - Add note about northern_zones being too large

### Paper Updates Needed

**Abstract** (lines 40-42):
- Remove: "144.9 percentage point improvement"
- Remove: References to approximation mode as normal
- Add: "27 diverse graphs with verified optimal baselines"
- Update: Actual gaps from re-run results

**Section 6.2** (lines 583-632):
- DELETE ENTIRELY: "Understanding Negative Gaps" section
- This explains approximation artifacts which NO LONGER EXIST

**Northern Zones** (lines 486-509):
- Add note: "Excluded from experiments due to 1614 odd vertices causing O(n³) matching to be intractable"
- Update table: Mark as "Extracted but excluded from benchmarks"

**Results Table** (lines 567-581):
- Will need complete rewrite with actual positive gaps from new run

### Technical Validation

The fix is validated by:
1. ✅ Proper matching algorithm (max_weight with negative weights)
2. ✅ Cross-platform timeout handling
3. ✅ Clear approximation mode tracking
4. ✅ 100% success rate on tested graphs
5. ✅ Reasonable runtimes (0.00s - 1.06s)
6. ✅ Gradual scaling (10 odd vertices → 96 odd vertices)

**Cutoff point identified**: ~100-200 odd vertices is manageable, 1600+ is not.

---

**Status**: Ready to complete full pipeline run and update paper! 🎯
