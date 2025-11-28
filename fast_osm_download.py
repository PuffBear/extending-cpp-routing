"""
Fast OSM Download - Smaller Areas
Downloads very small city areas quickly for testing
"""

import osmnx as ox
import networkx as nx
from pathlib import Path
import json
from datetime import datetime


def download_osm_fast():
    """Download small OSM areas quickly"""
    
    print("="*70)
    print("FAST OSM DOWNLOAD - Small Areas")
    print("="*70)
    
    # Much smaller areas (0.01 degree × 0.01 degree ≈ 1km × 1km)
    cities = {
        'manhattan_tiny': {
            'name': 'Manhattan (Times Square - 1km)',
            'bbox': (40.760, 40.750, -73.980, -73.990)  # ~1km area
        },
        'london_tiny': {
            'name': 'London (Piccadilly - 1km)', 
            'bbox': (51.510, 51.500, -0.130, -0.140)
        },
        'paris_tiny': {
            'name': 'Paris (Louvre - 1km)',
            'bbox': (48.865, 48.855, 2.335, 2.325)
        }
    }
    
    downloaded_networks = {}
    
    for city_key, city_info in cities.items():
        print(f"\n📍 Downloading {city_info['name']}...")
        print(f"   bbox: {city_info['bbox']}")
        
        try:
            bbox = city_info['bbox']
            
            print(f"   Requesting from OSM...")
            G = ox.graph_from_bbox(
                bbox=bbox,
                network_type='drive',
                simplify=True
            )
            
            print(f"   Converting to simple graph...")
            # Convert to simple undirected graph
            G_simple = G.to_undirected()
            G_final = nx.Graph()
            
            node_mapping = {node: i for i, node in enumerate(G_simple.nodes())}
            G_final.add_nodes_from(range(len(node_mapping)))
            
            for u, v, data in G_simple.edges(data=True):
                u_idx = node_mapping[u]
                v_idx = node_mapping[v]
                length = data.get('length', 100.0)
                weight = length / 100.0
                
                if not G_final.has_edge(u_idx, v_idx):
                    G_final.add_edge(u_idx, v_idx, weight=weight, length=length)
            
            # Take largest connected component
            if not nx.is_connected(G_final):
                largest_cc = max(nx.connected_components(G_final), key=len)
                G_final = G_final.subgraph(largest_cc).copy()
                G_final = nx.convert_node_labels_to_integers(G_final)
            
            downloaded_networks[city_key] = G_final
            
            print(f"   ✅ Success: {G_final.number_of_nodes()} nodes, {G_final.number_of_edges()} edges")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            import traceback
            traceback.print_exc()
    
    return downloaded_networks


def save_networks(networks, output_dir="benchmarks/osm_derived"):
    """Save downloaded networks"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n💾 Saving {len(networks)} networks...")
    
    for city_key, G in networks.items():
        # GraphML
        graphml_file = output_path / f"osm_{city_key}.graphml"
        nx.write_graphml(G, graphml_file)
        
        # Metadata
        metadata = {
            'instance_id': f'osm_{city_key}',
            'network_family': 'osm_derived',
            'city': city_key,
            'num_nodes': G.number_of_nodes(),
            'num_edges': G.number_of_edges(),
            'source': 'OpenStreetMap',
            'download_date': datetime.now().isoformat()
        }
        
        metadata_file = output_path / f"osm_{city_key}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"  ✅ {city_key}: {graphml_file}")
    
    print(f"\n✅ All networks saved to: {output_dir}/")


if __name__ == "__main__":
    print("Starting fast OSM download...\n")
    
    networks = download_osm_fast()
    
    if networks:
        save_networks(networks)
        
        print("\n" + "="*70)
        print("SUCCESS!")
        print("="*70)
        print(f"Downloaded {len(networks)} real-world street networks")
        print("\nNetworks:")
        for city, G in networks.items():
            print(f"  - {city}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        
        print("\n🎉 You now have real OSM data!")
        print("\nNext: Run experiments")
        print("  python3 run_full_pipeline.py --run-experiments")
    
    else:
        print("\n❌ No networks downloaded")
