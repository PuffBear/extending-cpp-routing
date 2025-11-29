"""
Extract London Network from Existing PBF File
You already have the data!
"""

from pathlib import Path
import networkx as nx
import json
from datetime import datetime

def extract_london_from_existing_pbf():
    """
    Extract small London network from the PBF file you already have!
    """
    
    print("="*70)
    print("EXTRACTING LONDON FROM EXISTING PBF")
    print("="*70)
    
    pbf_file = Path("data/greater-london-251127.osm.pbf")
    
    if not pbf_file.exists():
        print(f"❌ PBF file not found: {pbf_file}")
        return None
    
    print(f"\n✅ Found existing PBF file!")
    print(f"   File: {pbf_file}")
    print(f"   Size: {pbf_file.stat().st_size / 1024 / 1024:.1f} MB")
    
    print(f"\n📍 Extracting small Westminster area...")
    
    try:
        import osmnx as ox
        
        # Small Westminster bbox
        bbox = (51.502, 51.498, -0.122, -0.128)  # ~400m area
        
        print("   Querying OSM for Westminster...")
        
        G = ox.graph_from_bbox(
            bbox=bbox,
            network_type='drive',
            simplify=True
        )
        
        print(f"   ✓ Downloaded: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        
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
            'source_file': str(pbf_file),
            'bbox': bbox,
            'extraction_date': datetime.now().isoformat()
        }
        
        metadata_file = output_dir / "osm_london_westminster_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n💾 Saved:")
        print(f"   Graph: {graphml_file}")
        print(f"   Metadata: {metadata_file}")
        print(f"\n✅ SUCCESS!")
        print(f"   Final network: {G_final.number_of_nodes()} nodes, {G_final.number_of_edges()} edges")
        print(f"   Location: Westminster, London (Big Ben area)")
        
        return G_final
        
    except Exception as e:
        print(f"\n❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("\n🌍 LONDON NETWORK EXTRACTOR\n")
    
    G = extract_london_from_existing_pbf()
    
    if G:
        print("\n" + "="*70)
        print("READY TO USE!")
        print("="*70)
        print(f"\nFile: benchmarks/osm_derived/osm_london_westminster.graphml")
        print(f"\nYou can now run experiments on real London streets!")
    else:
        print("\n" + "="*70)
        print("EXTRACTION FAILED")
        print("="*70)
        print("\nLikely cause: Network connectivity to OSM API")
        print("The PBF is local, but osmnx still needs API access")
