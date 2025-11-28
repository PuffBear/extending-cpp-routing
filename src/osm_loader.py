"""
OSM (OpenStreetMap) Network Loader
Downloads and processes real street networks for CPP benchmarking
"""

import networkx as nx
import numpy as np
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass
import json
from pathlib import Path

try:
    import osmnx as ox
    OSMNX_AVAILABLE = True
except ImportError:
    OSMNX_AVAILABLE = False
    print("⚠️  osmnx not installed. Install with: pip install osmnx")


@dataclass
class CityConfig:
    """Configuration for downloading city network"""
    name: str
    location: str  # City name or (lat, lon)
    network_type: str = "drive"  # 'drive', 'walk', 'bike'
    area_km2: float = 1.0  # Area to extract in km²
    simplify: bool = True


class OSMNetworkLoader:
    """
    Loads real street networks from OpenStreetMap
    """
    
    # Predefined cities for benchmarking
    BENCHMARK_CITIES = {
        'manhattan': CityConfig(
            name='Manhattan_NYC',
            location='Manhattan, New York City, New York, USA',
            network_type='drive',
            area_km2=5.0
        ),
        'london': CityConfig(
            name='London_Center',
            location='City of London, London, UK',
            network_type='drive',
            area_km2=5.0
        ),
        'mumbai': CityConfig(
            name='Mumbai_Center',
            location='Mumbai, Maharashtra, India',
            network_type='drive',
            area_km2=5.0
        ),
        'tokyo': CityConfig(
            name='Tokyo_Center',
            location='Shibuya, Tokyo, Japan',
            network_type='drive',
            area_km2=5.0
        ),
        'paris': CityConfig(
            name='Paris_Center',
            location='Paris, France',
            network_type='drive',
            area_km2=5.0
        )
    }
    
    def __init__(self, cache_dir: str = "osm_cache"):
        if not OSMNX_AVAILABLE:
            raise ImportError("osmnx required for OSM loading. Install: pip install osmnx")
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure osmnx
        ox.settings.use_cache = True
        ox.settings.cache_folder = str(self.cache_dir)
    
    def download_city_network(self, city_key: str) -> nx.Graph:
        """
        Download street network for a predefined city
        
        Args:
            city_key: Key from BENCHMARK_CITIES
            
        Returns:
            NetworkX graph of street network
        """
        if city_key not in self.BENCHMARK_CITIES:
            raise ValueError(f"Unknown city: {city_key}. Available: {list(self.BENCHMARK_CITIES.keys())}")
        
        config = self.BENCHMARK_CITIES[city_key]
        
        print(f"📍 Downloading {config.name}...")
        print(f"   Location: {config.location}")
        print(f"   Network type: {config.network_type}")
        
        try:
            # Download network
            G = ox.graph_from_place(
                config.location,
                network_type=config.network_type,
                simplify=config.simplify
            )
            
            # Convert to undirected and simplify
            G = self._process_osm_graph(G)
            
            print(f"   ✓ Downloaded: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
            
            # Save to cache
            self._save_graph(G, config.name)
            
            return G
        
        except Exception as e:
            print(f"   ✗ Error downloading {config.name}: {e}")
            raise
    
    def download_bbox_network(self, north: float, south: float, 
                              east: float, west: float, 
                              network_type: str = 'drive') -> nx.Graph:
        """
        Download network within bounding box
        
        Args:
            north, south, east, west: Bounding box coordinates
            network_type: Type of network ('drive', 'walk', 'bike')
            
        Returns:
            NetworkX graph
        """
        print(f"📍 Downloading network in bbox ({north}, {south}, {east}, {west})...")
        
        G = ox.graph_from_bbox(
            north=north,
            south=south,
            east=east,
            west=west,
            network_type=network_type
        )
        
        G = self._process_osm_graph(G)
        
        print(f"   ✓ Downloaded: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        
        return G
    
    def download_point_network(self, lat: float, lon: float, 
                               dist: int = 1000,
                               network_type: str = 'drive') -> nx.Graph:
        """
        Download network around a point
        
        Args:
            lat, lon: Center point coordinates
            dist: Distance in meters
            network_type: Type of network
            
        Returns:
            NetworkX graph
        """
        print(f"📍 Downloading network around ({lat}, {lon}), radius={dist}m...")
        
        G = ox.graph_from_point(
            center_point=(lat, lon),
            dist=dist,
            network_type=network_type
        )
        
        G = self._process_osm_graph(G)
        
        print(f"   ✓ Downloaded: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        
        return G
    
    def _process_osm_graph(self, G_osm: nx.MultiDiGraph) -> nx.Graph:
        """
        Process OSM graph for CPP use:
        - Convert to undirected
        - Simplify to single edges
        - Add weights based on length
        - Ensure connectivity
        """
        # Convert to undirected
        G = G_osm.to_undirected()
        
        # Create simple graph (remove multi-edges)
        H = nx.Graph()
        
        # Re-index nodes to integers
        node_mapping = {node: i for i, node in enumerate(G.nodes())}
        H.add_nodes_from(range(len(node_mapping)))
        
        # Add edges with length-based weights
        for u, v, data in G.edges(data=True):
            u_idx = node_mapping[u]
            v_idx = node_mapping[v]
            
            # Get edge length (in meters)
            length = data.get('length', 100.0)
            
            # Convert to weight (you can normalize or scale as needed)
            weight = length / 100.0  # Scale to reasonable range
            
            if H.has_edge(u_idx, v_idx):
                # Keep shorter edge if duplicate
                if weight < H[u_idx][v_idx]['weight']:
                    H[u_idx][v_idx]['weight'] = weight
            else:
                H.add_edge(u_idx, v_idx, weight=weight, length=length)
        
        # Ensure connectivity (take largest component)
        if not nx.is_connected(H):
            print("   ⚠️  Graph not connected, taking largest component")
            largest_cc = max(nx.connected_components(H), key=len)
            H = H.subgraph(largest_cc).copy()
            
            # Re-index after taking subgraph
            H = nx.convert_node_labels_to_integers(H)
        
        return H
    
    def _save_graph(self, G: nx.Graph, name: str):
        """Save graph to cache"""
        cache_file = self.cache_dir / f"{name}.graphml"
        nx.write_graphml(G, cache_file)
        print(f"   💾 Cached to: {cache_file}")
    
    def load_cached_graph(self, name: str) -> Optional[nx.Graph]:
        """Load graph from cache if available"""
        cache_file = self.cache_dir / f"{name}.graphml"
        if cache_file.exists():
            print(f"   📂 Loading from cache: {cache_file}")
            return nx.read_graphml(cache_file)
        return None
    
    def download_all_benchmark_cities(self) -> Dict[str, nx.Graph]:
        """Download all predefined benchmark cities"""
        print("=" * 70)
        print("DOWNLOADING ALL BENCHMARK CITIES")
        print("=" * 70)
        
        networks = {}
        
        for city_key in self.BENCHMARK_CITIES:
            try:
                # Check cache first
                config = self.BENCHMARK_CITIES[city_key]
                cached = self.load_cached_graph(config.name)
                
                if cached is not None:
                    networks[city_key] = cached
                    print(f"✓ {city_key}: loaded from cache")
                else:
                    networks[city_key] = self.download_city_network(city_key)
                    print(f"✓ {city_key}: downloaded")
            
            except Exception as e:
                print(f"✗ {city_key}: failed - {e}")
        
        print(f"\n✅ Downloaded {len(networks)}/{len(self.BENCHMARK_CITIES)} cities")
        
        return networks


def create_osm_benchmark_instances(output_dir: str = "benchmarks/osm_derived"):
    """
    Create benchmark instances from OSM networks
    Integrates with main benchmark generator
    """
    from benchmark_generator import CPPInstance, InstanceMetadata, NetworkFamily, GraphSize
    from datetime import datetime
    
    loader = OSMNetworkLoader()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Download all cities
    networks = loader.download_all_benchmark_cities()
    
    instances = []
    
    for city_key, G in networks.items():
        print(f"\n📊 Creating benchmark instance for {city_key}...")
        
        # Determine size based on number of nodes
        n = G.number_of_nodes()
        if n < 100:
            size = GraphSize.SMALL
        elif n < 300:
            size = GraphSize.MEDIUM
        else:
            size = GraphSize.LARGE
        
        # Create metadata
        m = G.number_of_edges()
        density = (2 * m) / (n * (n - 1)) if n > 1 else 0
        avg_degree = sum(dict(G.degree()).values()) / n
        clustering = nx.average_clustering(G)
        
        try:
            diameter = nx.diameter(G)
        except:
            diameter = -1
        
        metadata = InstanceMetadata(
            instance_id=f"osm_{city_key}_{n}nodes",
            network_family=NetworkFamily.OSM_DERIVED.value,
            size=size.value,
            num_nodes=n,
            num_edges=m,
            density=density,
            avg_degree=avg_degree,
            clustering_coeff=clustering,
            diameter=diameter,
            is_connected=nx.is_connected(G),
            generation_timestamp=datetime.now().isoformat(),
            random_seed=0,  # OSM data is deterministic
            parameters={'city': city_key}
        )
        
        instance = CPPInstance(graph=G, metadata=metadata)
        
        # Save
        instance_file = output_path / f"{metadata.instance_id}.graphml"
        nx.write_graphml(G, instance_file)
        
        metadata_file = output_path / f"{metadata.instance_id}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata.to_dict(), f, indent=2)
        
        instances.append(instance)
        print(f"   ✓ Saved: {instance_file}")
    
    print(f"\n✅ Created {len(instances)} OSM benchmark instances")
    
    return instances


if __name__ == "__main__":
    # Example: Download benchmark cities
    loader = OSMNetworkLoader()
    
    try:
        # Download all predefined cities
        networks = loader.download_all_benchmark_cities()
        
        # Or download specific city
        # G = loader.download_city_network('manhattan')
        
        # Or download custom location
        # G = loader.download_point_network(lat=40.7580, lon=-73.9855, dist=500)
        
        # Create benchmark instances
        # instances = create_osm_benchmark_instances()
        
    except ImportError as e:
        print(f"\n⚠️  {e}")
        print("\nTo use OSM features, install:")
        print("  pip install osmnx")
