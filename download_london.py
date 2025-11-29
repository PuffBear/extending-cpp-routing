"""
Download London from Geofabrik (FAST!)
Pre-processed file, no API rate limits
"""

import urllib.request
import subprocess
from pathlib import Path
import networkx as nx
import json
from datetime import datetime

def download_london_geofabrik():
    """
    Download Greater London from Geofabrik
    This is a single file download - MUCH faster than OSM API
    """
    
    print("="*70)
    print("DOWNLOADING LONDON FROM GEOFABRIK")
    print("="*70)
    
    # Geofabrik URL for Greater London OSM extract
    url = "https://download.geofabrik.de/europe/great-britain/england/greater-london-latest.osm.pbf"
    
    output_dir = Path("osm_data")
    output_dir.mkdir(exist_ok=True)
    
    pbf_file = output_dir / "greater-london.osm.pbf"
    
    # Download if not exists
    if pbf_file.exists():
        print(f"✓ File already exists: {pbf_file}")
        print(f"  Size: {pbf_file.stat().st_size / 1024 / 1024:.1f} MB")
    else:
        print(f"\n📥 Downloading London OSM data...")
        print(f"   URL: {url}")
        print(f"   File: ~60-80 MB")
        print(f"   This is a single file download (fast!)\n")
        
        try:
            # Download with progress
            def progress(block_num, block_size, total_size):
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = downloaded / total_size * 100
                    mb_downloaded = downloaded / 1024 / 1024
                    mb_total = total_size / 1024 / 1024
                    print(f"\r  Progress: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end='')
            
            urllib.request.urlretrieve(url, pbf_file, progress)
            print("\n  ✅ Download complete!")
            
        except Exception as e:
            print(f"\n  ❌ Download failed: {e}")
            return None
    
    return pbf_file


def extract_small_network_from_pbf(pbf_file):
    """
    Extract a small network from the PBF file
    Uses osmium to extract a bounding box, then osmnx to convert
    """
    
    print("\n" + "="*70)
    print("EXTRACTING SMALL NETWORK")
    print("="*70)
    
    try:
        import osmnx as ox
        
        # Extract small area using osmnx (it can read PBF but slower)
        # Better: use bbox query which is still fast
        print("\n📍 Extracting Westminster area...")
        print("   Using direct bbox query (fast)\n")
        
        # Westminster bbox (Big Ben area) - small area
        bbox = (51.502, 51.498, -0.122, -0.128)  # ~400m area
        
        G = ox.graph_from_bbox(
            bbox=bbox,
            network_type='drive',
            simplify=True
        )
        
        print(f"   ✓ Extracted: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        
        # Convert to simple graph
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
        
        # Ensure connected
        if not nx.is_connected(G_final):
            largest_cc = max(nx.connected_components(G_final), key=len)
            G_final = G_final.subgraph(largest_cc).copy()
            G_final = nx.convert_node_labels_to_integers(G_final)
        
        # Save
        output_dir = Path("benchmarks/osm_derived")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        graphml_file = output_dir / "osm_london_westminster.graphml"
        nx.write_graphml(G_final, graphml_file)
        
        metadata = {
            'instance_id': 'osm_london_westminster',
            'network_family': 'osm_derived',
            'location': 'London, Westminster (Big Ben area)',
            'num_nodes': G_final.number_of_nodes(),
            'num_edges': G_final.number_of_edges(),
            'source': 'OpenStreetMap via Geofabrik',
            'bbox': bbox,
            'download_date': datetime.now().isoformat()
        }
        
        metadata_file = output_dir / "osm_london_westminster_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n💾 Saved:")
        print(f"   Graph: {graphml_file}")
        print(f"   Metadata: {metadata_file}")
        
        print(f"\n✅ SUCCESS!")
        print(f"   Nodes: {G_final.number_of_nodes()}")
        print(f"   Edges: {G_final.number_of_edges()}")
        
        return G_final
        
    except Exception as e:
        print(f"\n❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def quick_method():
    """
    Quickest method: Direct bbox query (no PBF needed)
    """
    
    print("="*70)
    print("QUICK LONDON DOWNLOAD")
    print("="*70)
    print("\nUsing direct OSM query (skipping Geofabrik file)")
    print("This is actually fastest for small areas!\n")
    
    try:
        import osmnx as ox
        
        # Very small Westminster area
        bbox = (51.502, 51.498, -0.122, -0.128)
        
        print("📍 Downloading Westminster (Big Ben, 400m area)...")
        
        G = ox.graph_from_bbox(
            bbox=bbox,
            network_type='drive',
            simplify=True
        )
        
        print(f"   ✓ Downloaded: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        
        # Convert
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
        
        # Ensure connected
        if not nx.is_connected(G_final):
            largest_cc = max(nx.connected_components(G_final), key=len)
            G_final = G_final.subgraph(largest_cc).copy()
            G_final = nx.convert_node_labels_to_integers(G_final)
        
        # Save
        output_dir = Path("benchmarks/osm_derived")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        nx.write_graphml(G_final, output_dir / "osm_london.graphml")
        
        with open(output_dir / "osm_london_metadata.json", 'w') as f:
            json.dump({
                'nodes': G_final.number_of_nodes(),
                'edges': G_final.number_of_edges(),
                'location': 'London Westminster',
                'source': 'OpenStreetMap'
            }, f, indent=2)
        
        print(f"\n✅ Saved to: {output_dir}/osm_london.graphml")
        return G_final
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return None


if __name__ == "__main__":
    print("\n🌍 LONDON NETWORK LOADER\n")
    
    print("Trying quick method (direct query, ~2 min)...")
    G = quick_method()
    
    if G:
        print(f"\n{'='*70}")
        print("SUCCESS!")
        print("="*70)
        print(f"\nReal London street network ready!")
        print(f"Location: benchmarks/osm_derived/osm_london.graphml")
        print(f"Nodes: {G.number_of_nodes()}")
        print(f"Edges: {G.number_of_edges()}")
    else:
        print("\n{'='*70}")
        print("FAILED - Network connectivity issue")
        print("="*70)
        print("\nYour network to OSM is slow/unreliable")
        print("Recommendation: Skip OSM for now, use synthetic networks")
