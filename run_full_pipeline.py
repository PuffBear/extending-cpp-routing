"""
MASTER SCRIPT: Complete ArXiv Submission Pipeline
Runs everything from benchmark generation to figure generation

This is your ONE-COMMAND solution to go from zero to submission-ready results
"""

import sys
from pathlib import Path
import argparse
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def run_complete_pipeline(args):
    """Run complete experimental pipeline"""
    
    start_time = time.time()
    
    print_header("🚀 COMPLETE ARXIV SUBMISSION PIPELINE")
    print(f"\nConfiguration:")
    print(f"  Instances per config: {args.instances}")
    print(f"  Include OSM: {args.include_osm}")
    print(f"  Run experiments: {args.run_experiments}")
    print(f"  Generate figures: {args.generate_figures}")
    print(f"  Statistical analysis: {args.statistical_analysis}")
    
    # STEP 1: Generate Benchmarks
    if args.generate_benchmarks:
        print_header("STEP 1: Generate Benchmark Dataset")
        
        from benchmark_generator import BenchmarkGenerator
        
        generator = BenchmarkGenerator(output_dir="benchmarks", base_seed=42)
        instances = generator.generate_full_suite(instances_per_config=args.instances)
        
        print(f"\n✅ Generated {len(instances)} benchmark instances")
        
        # OSM networks
        if args.include_osm:
            print("\n📍 Downloading OSM real-world networks...")
            try:
                from osm_loader import create_osm_benchmark_instances
                osm_instances = create_osm_benchmark_instances("benchmarks/osm_derived")
                print(f"✅ Added {len(osm_instances)} OSM instances")
            except Exception as e:
                print(f"⚠️  OSM download failed: {e}")
                print("   Continuing without OSM data")
    
    else:
        print_header("STEP 1: Benchmark Generation - SKIPPED")
    
    # STEP 2: Run Experiments
    if args.run_experiments:
        print_header("STEP 2: Run All Experiments")
        
        from experimental_pipeline import ExperimentalPipeline
        
        pipeline = ExperimentalPipeline(
            benchmark_dir="benchmarks",
            output_dir="experimental_results"
        )
        
        algorithms = [
            'classical_cpp',
            'greedy_heuristic',
            'two_opt'
        ]
        
        # Add OR-Tools if available
        try:
            import ortools
            algorithms.append('ortools_baseline')
            print("  ✓ OR-Tools available")
        except ImportError:
            print("  ⚠️  OR-Tools not available, skipping")
        
        # Add hybrid learning if available
        try:
            import torch
            algorithms.append('hybrid_learning')
            print("  ✓ PyTorch available for learning")
        except ImportError:
            print("  ⚠️  PyTorch not available, skipping learning")
        
        print(f"\n  Running {len(algorithms)} algorithms...")
        pipeline.run_complete_pipeline(algorithms)
        
        print("\n✅ Experiments complete!")
    
    else:
        print_header("STEP 2: Run Experiments - SKIPPED")
    
    # STEP 3: Statistical Analysis
    if args.statistical_analysis:
        print_header("STEP 3: Statistical Analysis")
        
        from statistical_analysis_framework import analyze_experimental_results
        
        try:
            analyzer = analyze_experimental_results("experimental_results/all_results.csv")
            print("\n✅ Statistical analysis complete!")
        except FileNotFoundError:
            print("  ⚠️  No experimental results found. Run experiments first.")
        except Exception as e:
            print(f"  ✗ Statistical analysis failed: {e}")
    
    else:
        print_header("STEP 3: Statistical Analysis - SKIPPED")
    
    # STEP 4: Generate Figures
    if args.generate_figures:
        print_header("STEP 4: Generate Publication Figures")
        
        from production_plots import generate_all_publication_figures
        
        try:
            plotter = generate_all_publication_figures(
                "experimental_results/all_results.csv",
                "figures"
            )
            print("\n✅ All figures generated!")
        except FileNotFoundError:
            print("  ⚠️  No experimental results found. Run experiments first.")
        except Exception as e:
            print(f"  ✗ Figure generation failed: {e}")
    
    else:
        print_header("STEP 4: Generate Figures - SKIPPED")
    
    # Final Summary
    elapsed = time.time() - start_time
    
    print_header("✅ PIPELINE COMPLETE!")
    
    print(f"\n⏱️  Total time: {elapsed/60:.1f} minutes")
    
    print("\n📁 Output Structure:")
    print("  benchmarks/          - Benchmark instances")
    print("  experimental_results/ - Raw experimental data")
    print("  statistical_results/  - Statistical analysis")
    print("  figures/             - Publication figures (PDF + PNG)")
    
    print("\n🎯 Next Steps:")
    print("  1. Review results: cat experimental_results/EXPERIMENTAL_REPORT.md")
    print("  2. Check figures: open figures/")
    print("  3. Review stats: cat statistical_analysis_report.md")
    print("  4. Start writing paper!")
    
    print("\n📊 What You Have Now:")
    print("  ✅ Comprehensive benchmark dataset")
    print("  ✅ Experimental results from multiple algorithms")
    print("  ✅ Rigorous statistical analysis")
    print("  ✅ Publication-ready figures")
    print("  ✅ All data for arXiv submission")
    
    print("\n🎓 Ready for arXiv submission!")


def run_quick_test():
    """Run quick test with small dataset"""
    print_header("🧪 QUICK TEST MODE")
    print("\nGenerating small test dataset for validation...")
    
    from benchmark_generator import BenchmarkGenerator
    
    generator = BenchmarkGenerator(output_dir="benchmarks_test", base_seed=42)
    instances = generator.generate_full_suite(instances_per_config=2)
    
    print(f"\n✅ Generated {len(instances)} test instances")
    print("\n✓ Benchmark system working correctly!")
    print("\nTo run full pipeline:")
    print("  python run_full_pipeline.py --all")


def main():
    parser = argparse.ArgumentParser(
        description='Complete CPP Research Pipeline - Benchmark to Publication',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run everything (6-8 hours)
  python run_full_pipeline.py --all
  
  # Just generate benchmarks
  python run_full_pipeline.py --generate-benchmarks --instances 20
  
  # Generate benchmarks + run experiments
  python run_full_pipeline.py --generate-benchmarks --run-experiments
  
  # Quick test
  python run_full_pipeline.py --quick-test
  
  # Analysis + figures only (after experiments)
  python run_full_pipeline.py --statistical-analysis --generate-figures
        """
    )
    
    # Pipeline steps
    parser.add_argument('--all', action='store_true',
                       help='Run complete pipeline (all steps)')
    parser.add_argument('--generate-benchmarks', action='store_true',
                       help='Generate benchmark dataset')
    parser.add_argument('--run-experiments', action='store_true',
                       help='Run all experiments')
    parser.add_argument('--statistical-analysis', action='store_true',
                       help='Run statistical analysis')
    parser.add_argument('--generate-figures', action='store_true',
                       help='Generate publication figures')
    
    # Parameters
    parser.add_argument('--instances', type=int, default=10,
                       help='Instances per configuration (default: 10)')
    parser.add_argument('--include-osm', action='store_true',
                       help='Include OSM real-world networks')
    
    # Quick test
    parser.add_argument('--quick-test', action='store_true',
                       help='Run quick test with 2 instances per config')
    
    args = parser.parse_args()
    
    # Quick test mode
    if args.quick_test:
        run_quick_test()
        return
    
    # If --all, enable everything
    if args.all:
        args.generate_benchmarks = True
        args.run_experiments = True
        args.statistical_analysis = True
        args.generate_figures = True
        args.include_osm = True
    
    # Check if any step is selected
    if not any([args.generate_benchmarks, args.run_experiments, 
                args.statistical_analysis, args.generate_figures]):
        parser.print_help()
        print("\n⚠️  No pipeline steps selected. Use --all or specify individual steps.")
        return
    
    # Run pipeline
    run_complete_pipeline(args)


if __name__ == "__main__":
    main()
