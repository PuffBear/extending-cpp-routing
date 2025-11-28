"""
Quick Start: Generate Complete Benchmark Dataset
Run this script to create all benchmark instances
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from benchmark_generator import BenchmarkGenerator, NetworkFamily, GraphSize
import argparse


def main():
    parser = argparse.ArgumentParser(description='Generate CPP benchmark dataset')
    parser.add_argument('--output', default='benchmarks', help='Output directory')
    parser.add_argument('--instances-per-config', type=int, default=10,
                       help='Number of instances per configuration')
    parser.add_argument('--seed', type=int, default=42, help='Base random seed')
    parser.add_argument('--include-osm', action='store_true',
                       help='Include OSM real-world networks (requires osmnx)')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🚀 CPP BENCHMARK DATASET GENERATOR")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Output directory: {args.output}")
    print(f"  Instances per config: {args.instances_per_config}")
    print(f"  Base seed: {args.seed}")
    print(f"  Include OSM: {args.include_osm}")
    
    # Generate main benchmark suite
    generator = BenchmarkGenerator(output_dir=args.output, base_seed=args.seed)
    instances = generator.generate_full_suite(instances_per_config=args.instances_per_config)
    
    # Calculate expected total
    num_families = 3  # grid, random_geometric, clustered (OSM separate)
    num_sizes = 3     # small, medium, large
    expected_total = num_families * num_sizes * args.instances_per_config
    
    print(f"\n✅ Generated {len(instances)}/{expected_total} instances")
    
    # OSM networks (optional)
    if args.include_osm:
        print("\n" + "=" * 70)
        print("Downloading OSM Networks")
        print("=" * 70)
        
        try:
            from osm_loader import create_osm_benchmark_instances
            osm_instances = create_osm_benchmark_instances(
                output_dir=f"{args.output}/osm_derived"
            )
            print(f"✅ Added {len(osm_instances)} OSM instances")
            instances.extend(osm_instances)
        except ImportError as e:
            print(f"⚠️  Could not load OSM: {e}")
            print("    Install with: pip install osmnx")
        except Exception as e:
            print(f"⚠️  Error downloading OSM: {e}")
    
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"Total instances: {len(instances)}")
    print(f"Output directory: {args.output}")
    print(f"\nFiles generated:")
    print(f"  - {len(instances)} × .graphml (NetworkX graphs)")
    print(f"  - {len(instances)} × .pkl (Complete instances)")
    print(f"  - {len(instances)} × _metadata.json (Metadata)")
    print(f"  - 1 × BENCHMARK_SUMMARY.md (Summary report)")
    
    print("\n🎯 Next steps:")
    print("  1. Review: cat benchmarks/BENCHMARK_SUMMARY.md")
    print("  2. List instances: ls benchmarks/*/*.graphml")
    print("  3. Run experiments: python src/run_experiments.py")
    
    return instances


if __name__ == "__main__":
    main()
