# CPP Benchmark Dataset Generator

Comprehensive benchmark generation system for Chinese Postman Problem (CPP) research.

## 🎯 Overview

This system generates reproducible benchmark instances across 4 network families:

1. **Grid Graphs** - Regular structured networks
2. **Random Geometric Graphs (RGG)** - Spatial proximity networks
3. **Clustered Graphs** - Community structure networks
4. **OSM-Derived** - Real-world street networks

Each instance includes data for all CPP variants:
- CPP-LC: Load-Dependent Costs
- CPP-TW: Time Windows
- Mixed CPP: Directed/undirected edges
- Windy Postman: Directional costs

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# For OSM support (optional)
pip install osmnx geopandas
```

### Generate Benchmarks

```bash
# Generate default benchmark suite (90 instances)
python generate_benchmarks.py

# Generate with custom configuration
python generate_benchmarks.py --output my_benchmarks --instances-per-config 20 --seed 123

# Include OSM real-world networks
python generate_benchmarks.py --include-osm

# Full options
python generate_benchmarks.py --help
```

## 📊 What Gets Generated?

### Default Configuration
- **3 network families** × **3 sizes** × **10 instances** = **90 base graphs**
- **+5 OSM cities** (if `--include-osm`) = **95 total instances**

### File Structure
```
benchmarks/
├── grid/
│   ├── grid_small_0000_abc123.graphml        # NetworkX graph
│   ├── grid_small_0000_abc123.pkl            # Complete instance data
│   ├── grid_small_0000_abc123_metadata.json  # Human-readable metadata
│   └── ... (30 instances)
├── random_geometric/
│   └── ... (30 instances)
├── clustered/
│   └── ... (30 instances)
├── osm_derived/
│   └── ... (5 cities)
└── BENCHMARK_SUMMARY.md                       # Summary statistics
```

## 🔬 Instance Details

### Grid Graphs
| Size   | Dimensions | Nodes | Edges |
|--------|-----------|-------|-------|
| Small  | 5×5       | 25    | ~40   |
| Medium | 10×10     | 100   | ~180  |
| Large  | 20×20     | 400   | ~760  |

**Use case**: Regular structure, predictable behavior, algorithm testing

### Random Geometric Graphs (RGG)
| Size   | Nodes | Radius | Avg Degree |
|--------|-------|--------|------------|
| Small  | 50    | 0.25   | ~6         |
| Medium | 100   | 0.18   | ~6         |
| Large  | 200   | 0.13   | ~6         |

**Use case**: Spatial networks, wireless routing, drone paths

### Clustered Graphs
| Size   | Clusters | Nodes/Cluster | Total Nodes |
|--------|----------|---------------|-------------|
| Small  | 5        | 10            | 50          |
| Medium | 10       | 10            | 100         |
| Large  | 20       | 10            | 200         |

**Use case**: Community detection, hierarchical routing, city districts

### OSM-Derived (Real-World)
| City      | Region        | Approx. Nodes |
|-----------|---------------|---------------|
| Manhattan | NYC, USA      | ~300          |
| London    | City Center   | ~250          |
| Mumbai    | Maharashtra   | ~200          |
| Tokyo     | Shibuya       | ~280          |
| Paris     | Center        | ~260          |

**Use case**: Real-world validation, practical applicability

## 🎲 Reproducibility

All instances are generated with fixed random seeds:
- Base seed: 42 (configurable)
- Instance seed: `base_seed + offset`
- Metadata includes all generation parameters

To regenerate identical instances:
```bash
python generate_benchmarks.py --seed 42 --instances-per-config 10
```

## 📦 Loading Instances

### Python API

```python
from src.benchmark_generator import BenchmarkGenerator

# Initialize loader
generator = BenchmarkGenerator(output_dir="benchmarks")

# Load specific instance
instance = generator.load_instance("grid_small_0000_abc123")

# Access graph
G = instance.graph
print(f"Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")

# Access CPP-LC data
print(f"Edge demands: {instance.edge_demands}")
print(f"Vehicle capacity: {instance.vehicle_capacity}")

# Access CPP-TW data
print(f"Time windows: {instance.time_windows}")

# Access metadata
meta = instance.metadata
print(f"Family: {meta.network_family}, Size: {meta.size}")
print(f"Density: {meta.density:.3f}, Clustering: {meta.clustering_coeff:.3f}")

# List all instances
instances = generator.get_instance_list()
print(f"Total instances: {len(instances)}")

# Filter by family/size
grid_instances = generator.get_instance_list(
    family=NetworkFamily.GRID,
    size=GraphSize.SMALL
)
```

### Load GraphML Directly

```python
import networkx as nx

# Load just the graph
G = nx.read_graphml("benchmarks/grid/grid_small_0000_abc123.graphml")

# Load metadata
import json
with open("benchmarks/grid/grid_small_0000_abc123_metadata.json") as f:
    metadata = json.load(f)
```

## 🧪 Using in Experiments

```python
from src.benchmark_generator import BenchmarkGenerator

generator = BenchmarkGenerator(output_dir="benchmarks")

# Iterate over all instances
for instance_id in generator.get_instance_list():
    instance = generator.load_instance(instance_id)
    
    # Run your algorithm
    cost, tour = my_cpp_algorithm(instance.graph)
    
    # Use variant-specific data
    if instance.edge_demands:
        cost_lc = my_cpp_lc_algorithm(
            instance.graph,
            instance.edge_demands,
            instance.vehicle_capacity
        )
    
    # Collect results with metadata
    results.append({
        'instance_id': instance_id,
        'family': instance.metadata.network_family,
        'size': instance.metadata.size,
        'cost': cost,
        'nodes': instance.metadata.num_nodes
    })
```

## 🌍 OSM Network Download

### Predefined Cities

```python
from src.osm_loader import OSMNetworkLoader

loader = OSMNetworkLoader()

# Download all benchmark cities
networks = loader.download_all_benchmark_cities()

# Download specific city
G_manhattan = loader.download_city_network('manhattan')
```

### Custom Locations

```python
# By place name
G = ox.graph_from_place("Cambridge, MA, USA", network_type='drive')

# By coordinates (lat, lon) + radius
G = loader.download_point_network(lat=40.7580, lon=-73.9855, dist=1000)

# By bounding box
G = loader.download_bbox_network(
    north=40.8, south=40.7, east=-73.9, west=-74.0
)
```

## 📈 Benchmark Statistics

After generation, view summary:

```bash
cat benchmarks/BENCHMARK_SUMMARY.md
```

Example output:
```
# Benchmark Dataset Summary Report
Generated: 2025-11-28T22:30:00

Total instances: 90

## Instance Breakdown
| Family           | Size   | Count | Avg Nodes | Avg Edges | Avg Density |
|------------------|--------|-------|-----------|-----------|-------------|
| clustered        | large  | 10    | 200.0     | 628.3     | 0.031       |
| clustered        | medium | 10    | 100.0     | 318.7     | 0.064       |
| clustered        | small  | 10    | 50.0      | 162.1     | 0.132       |
| grid             | large  | 10    | 400.0     | 760.0     | 0.010       |
| grid             | medium | 10    | 100.0     | 180.0     | 0.036       |
| grid             | small  | 10    | 25.0      | 40.0      | 0.133       |
| random_geometric | large  | 10    | 200.0     | 623.8     | 0.031       |
| random_geometric | medium | 10    | 100.0     | 337.2     | 0.068       |
| random_geometric | small  | 10    | 50.0      | 148.6     | 0.121       |
```

## 🔧 Advanced Usage

### Parameter Sweep Generation

For detailed sensitivity analysis:

```python
from src.benchmark_generator import generate_parameter_sweep_instances

# Generate instances with systematic parameter variation
instances = generate_parameter_sweep_instances(
    output_dir="benchmarks_sweep"
)
```

This creates instances varying:
- CPP-LC: Capacity ratios (0.3, 0.5, 0.8), cost functions (linear, quadratic, fuel)
- CPP-TW: Tightness values (0.5, 1.0, 1.5, 2.0)
- Mixed CPP: Directed fractions (0.2, 0.4, 0.6, 0.8)
- Windy: Asymmetry factors (0.3, 0.5, 0.7)

### Custom Network Generator

```python
from src.benchmark_generator import BenchmarkGenerator, CPPInstance, InstanceMetadata

generator = BenchmarkGenerator()

# Create your own graph
G = nx.karate_club_graph()

# Create CPP instance
metadata = InstanceMetadata(
    instance_id="custom_karate",
    network_family="custom",
    # ... fill other fields
)

instance = CPPInstance(graph=G, metadata=metadata)

# Add variant data
generator._add_cpp_lc_data(instance, seed=42)
generator._add_cpp_tw_data(instance, seed=42)

# Save
generator._save_instance(instance)
```

## 📋 Instance Metadata Fields

Each instance includes comprehensive metadata:

```json
{
  "instance_id": "grid_small_0000_abc123",
  "network_family": "grid",
  "size": "small",
  "num_nodes": 25,
  "num_edges": 40,
  "density": 0.133,
  "avg_degree": 3.2,
  "clustering_coeff": 0.0,
  "diameter": 8,
  "is_connected": true,
  "generation_timestamp": "2025-11-28T22:30:00",
  "random_seed": 42,
  "parameters": {
    "cpp_lc": {
      "total_demand": 245.6,
      "capacity": 98.24,
      "capacity_ratio": 0.4
    },
    "cpp_tw": {
      "tightness": 1.0,
      "num_windows": 40
    },
    "mixed_cpp": {
      "directed_fraction": 0.4,
      "num_directed": 16
    },
    "windy": {
      "asymmetry_factor": 0.6
    }
  }
}
```

## 🎓 Citation

If you use these benchmarks in your research, please cite:

```bibtex
@misc{cpp_benchmarks_2025,
  title={Comprehensive Benchmark Suite for Chinese Postman Problem Variants},
  author={Your Name},
  year={2025},
  url={https://github.com/yourusername/extending-cpp-routing}
}
```

## 📝 License

MIT License - see LICENSE file

## 🤝 Contributing

Contributions welcome! To add new network families or variants:

1. Add generator method to `BenchmarkGenerator`
2. Update `NetworkFamily` enum
3. Add tests
4. Submit PR

## 🐛 Troubleshooting

### OSM Download Fails

```bash
# Install osmnx if missing
pip install osmnx geopandas

# Check internet connection
# OSM servers may rate-limit - add delays between requests
```

### Graph Not Connected

The generator automatically ensures connectivity by:
- Taking largest connected component
- Adding bridging edges between components

### Memory Issues with Large Graphs

```python
# Generate in batches
for size in [GraphSize.SMALL, GraphSize.MEDIUM]:
    generator.generate_full_suite(instances_per_config=10)
```

## 📚 References

- [NetworkX Documentation](https://networkx.org/)
- [OSMnx: Python for Street Networks](https://github.com/gboeing/osmnx)
- Classical CPP: Edmonds & Johnson (1973)
