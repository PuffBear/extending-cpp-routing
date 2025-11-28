"""
Test OSM Connectivity and Download Real Street Networks
"""

import sys

def test_basic_connectivity():
    """Test if we can reach the internet"""
    print("Testing basic internet connectivity...")
    
    try:
        import requests
        response = requests.get("https://www.google.com", timeout=5)
        print("✅ Internet connectivity: OK")
        return True
    except Exception as e:
        print(f"❌ Internet connectivity failed: {e}")
        return False


def test_osm_connectivity():
    """Test if we can reach OpenStreetMap servers"""
    print("\nTesting OSM server connectivity...")
    
    try:
        import requests
        
        # Test Nominatim (geocoding)
        print("  Testing nominatim.openstreetmap.org...")
        response = requests.get(
            "https://nominatim.openstreetmap.org/search?format=json&q=New+York",
            timeout=10,
            headers={'User-Agent': 'CPP-Research/1.0'}
        )
        if response.status_code == 200:
            print("  ✅ Nominatim server: OK")
            return True
        else:
            print(f"  ⚠️  Nominatim server returned: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ OSM server failed: {e}")
        return False


def test_osmnx_simple():
    """Test osmnx with simple query"""
    print("\nTesting osmnx library...")
    
    try:
        import osmnx as ox
        print("  ✅ osmnx imported successfully")
        print(f"  Version: {ox.__version__}")
        
        # Try downloading a very small network using coordinates
        print("  Attempting small download (coordinates)...")
        
        # Manhattan coordinates (bbox format for osmnx 2.0)
        bbox = (40.7589, 40.7489, -73.9851, -73.9951)  # north, south, east, west
        
        # osmnx 2.0 uses 'bbox' parameter
        G = ox.graph_from_bbox(
            bbox=bbox,
            network_type='drive',
            simplify=True
        )
        
        print(f"  ✅ Successfully downloaded graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        return True, G
        
    except Exception as e:
        print(f"  ❌ osmnx test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def download_osm_by_coordinates():
    """
    Alternative: Download OSM using coordinates instead of place names
    More reliable than place name geocoding
    """
    print("\n" + "="*70)
    print("ALTERNATIVE: Downloading OSM via Coordinates")
    print("="*70)
    
    try:
        import osmnx as ox
        import networkx as nx
        
        # City coordinates (bbox: north, south, east, west)
        cities = {
            'manhattan_small': {
                'name': 'Manhattan (Times Square area)',
                'bbox': (40.7614, 40.7514, -73.9776, -73.9876)
            },
            'london_piccadilly': {
                'name': 'London (Piccadilly Circus area)',
                'bbox': (51.5114, 51.5014, -0.1276, -0.1376)
            },
            'paris_louvre': {
                'name': 'Paris (Louvre area)',
                'bbox': (48.8656, 48.8556, 2.3422, 2.3322)
            },
            'tokyo_shibuya': {
                'name': 'Tokyo (Shibuya Crossing area)',
                'bbox': (35.6645, 35.6545, 139.7025, 139.6925)
            },
            'mumbai_gateway': {
                'name': 'Mumbai (Gateway of India area)',
                'bbox': (18.9300, 18.9200, 72.8356, 72.8256)
            }
        }
        
        downloaded_networks = {}
        
        for city_key, city_info in cities.items():
            print(f"\n📍 Downloading {city_info['name']}...")
            
            try:
                bbox = city_info['bbox']  # (north, south, east, west)
                
                # osmnx 2.0 uses bbox parameter
                G = ox.graph_from_bbox(
                    bbox=bbox,
                    network_type='drive',
                    simplify=True
                )
                
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
        
    except Exception as e:
        print(f"❌ Overall download failed: {e}")
        import traceback
        traceback.print_exc()
        return {}


def save_osm_networks(networks, output_dir="benchmarks/osm_derived"):
    """Save downloaded OSM networks"""
    from pathlib import Path
    import networkx as nx
    import json
    from datetime import datetime
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n💾 Saving {len(networks)} OSM networks to {output_dir}/")
    
    for city_key, G in networks.items():
        # Save as GraphML
        graphml_file = output_path / f"osm_{city_key}.graphml"
        nx.write_graphml(G, graphml_file)
        
        # Save metadata
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
        
        print(f"  ✅ Saved {city_key}: {graphml_file}")
    
    print(f"\n✅ All OSM networks saved!")


def main():
    print("="*70)
    print("OSM CONNECTIVITY TEST & DOWNLOAD")
    print("="*70)
    
    # Step 1: Test basic connectivity
    if not test_basic_connectivity():
        print("\n❌ Cannot reach internet. Check your network connection.")
        return
    
    # Step 2: Test OSM servers
    osm_ok = test_osm_connectivity()
    
    # Step 3: Test osmnx
    osmnx_ok, test_graph = test_osmnx_simple()
    
    if not osmnx_ok:
        print("\n❌ osmnx not working. This might be a firewall or DNS issue.")
        print("\nTroubleshooting:")
        print("  1. Check if you're behind a firewall/proxy")
        print("  2. Try: ping nominatim.openstreetmap.org")
        print("  3. Try: curl https://nominatim.openstreetmap.org")
        return
    
    # Step 4: Download networks using coordinates
    print("\n" + "="*70)
    print("Downloading Real OSM Street Networks")
    print("="*70)
    
    networks = download_osm_by_coordinates()
    
    if networks:
        print(f"\n✅ Successfully downloaded {len(networks)} city networks!")
        
        # Save them
        save_osm_networks(networks)
        
        print("\n" + "="*70)
        print("SUCCESS!")
        print("="*70)
        print(f"Downloaded {len(networks)} real-world street networks")
        print("Saved to: benchmarks/osm_derived/")
        print("\nYou can now run experiments with real OSM data!")
        
    else:
        print("\n❌ Could not download any networks")
        print("Check your internet connection and firewall settings")


if __name__ == "__main__":
    main()
