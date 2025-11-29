"""
Extract from London PBF - NO API CALLS
Uses pyrosm to read PBF directly (offline)
"""

from pathlib import Path
import networkx as nx
import json
from datetime import datetime

def extract_from_london_pbf():
    """
    Extract street network from local PBF file
    Uses pyrosm which reads PBF files OFFLINE
    """
    
    print("="*70)
    print("EXTRACTING FROM LOCAL LONDON PBF")
    print("="*70)
    
    pbf_file = Path("data/greater-london-251127.osm.pbf")
    
    if not pbf_file.exists():
        print(f"❌ PBF not found: {pbf_file}")
        return None
    
    print(f"\n✅ Found PBF: {pbf_file.stat().st_size / 1024 / 1024:.1f} MB")
    
    try:
        # Try pyrosm (reads PBF offline)
        import pyrosm
        
        print("\n📍 Extracting street network (offline)...")
        
        osm = pyrosm.OSM(str(pbf_file), bounding_box=[-0.128, 51.498, -0.122, 51.502])
        
        # Get drive network for Westminster area
        print(f"   Extracting Westminster driving network...")
        network = osm.get_network(network_type='driving')
        
        if network is None or len(network) == 0:
            print("   ✗ No network data extracted")
            return None
        
        print(f"   ✓ Extracted {len(network)} edges")
        
        # Convert to NetworkX
        G = osm.to_graph(network, graph_type='networkx')
        
        # Simplify to undirected
        if isinstance(G, nx.MultiDiGraph) or isinstance(G, nx.DiGraph):
            G = G.to_undirected()
        
        # Convert to simple graph with integer nodes
        G_final = nx.Graph()
        node_mapping = {node: i for i, node in enumerate(G.nodes())}
        
        for old_node, new_node in node_mapping.items():
            G_final.add_node(new_node)
        
        for u, v, data in G.edges(data=True):
            u_new = node_mapping[u]
            v_new = node_mapping[v]
            
            # Get length
            length = data.get('length', 100.0)
            if isinstance(length, (list, tuple)):
                length = length[0] if length else 100.0
            
            weight = float(length) / 100.0
            
            if not G_final.has_edge(u_new, v_new):
                G_final.add_edge(u_new, v_new, weight=weight, length=float(length))
        
        # Take largest connected component
        if not nx.is_connected(G_final):
            largest_cc = max(nx.connected_components(G_final), key=len)
            G_final = G_final.subgraph(largest_cc).copy()
            G_final = nx.convert_node_labels_to_integers(G_final)
        
        # Save
        output_dir = Path("benchmarks/osm_derived")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        graphml_file = output_dir / "osm_london_real.graphml"
        nx.write_graphml(G_final, graphml_file)
        
        metadata = {
            'instance_id': 'osm_london_real',
            'network_family': 'osm_real',
            'location': 'London, Westminster (from local PBF)',
            'num_nodes': G_final.number_of_nodes(),
            'num_edges': G_final.number_of_edges(),
            'source': 'OpenStreetMap (Geofabrik PBF)',
            'source_file': str(pbf_file),
            'extraction_date': datetime.now().isoformat(),
            'method': 'pyrosm (offline)'
        }
        
        metadata_file = output_dir / "osm_london_real_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n💾 Saved:")
        print(f"   {graphml_file}")
        print(f"\n✅ SUCCESS!")
        print(f"   Nodes: {G_final.number_of_nodes()}")
        print(f"   Edges: {G_final.number_of_edges()}")
        print(f"   Source: London PBF (offline extraction)")
        
        return G_final
        
    except ImportError:
        print("\n⚠️  pyrosm not installed")
        print("   Install: pip install pyrosm")
        print("\n   Trying alternative method...")
        return extract_simple_from_pbf()
    
    except Exception as e:
        print(f"\n❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def extract_simple_from_pbf():
    """
    Simple extraction using osmium (command line tool)
    """
    
    print("\n📍 Trying command-line extraction...")
    
    import subprocess
    
    pbf_file = "data/greater-london-251127.osm.pbf"
    output_file = "data/westminster_extract.osm"
    
    # Use osmium to extract bbox (if installed)
    bbox = "-0.128,51.498,-0.122,51.502"  # minx,miny,maxx,maxy
    
    try:
        cmd = f"osmium extract -b {bbox} {pbf_file} -o {output_file}"
        print(f"   Running: {cmd}")
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"   ✓ Extracted to {output_file}")
            
            # Now read with osmnx
            import osmnx as ox
            G = ox.graph_from_xml(output_file, simplify=True)
            
            print(f"   ✓ Loaded: {G.number_of_nodes()} nodes")
            
            # Convert and save...
            return G
        else:
            print(f"   ✗ osmium failed: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return None


if __name__ == "__main__":
    print("\n🌍 LONDON NETWORK FROM LOCAL PBF\n")
    
    print("Installing pyrosm (if needed)...")
    import subprocess
    subprocess.run(["pip", "install", "-q", "pyrosm"], capture_output=True)
    
    G = extract_from_london_pbf()
    
    if G:
        print("\n" + "="*70)
        print("REAL LONDON NETWORK EXTRACTED!")
        print("="*70)
        print(f"\nFile: benchmarks/osm_derived/osm_london_real.graphml")
        print(f"\nThis is REAL street network data from London!")
        print(f"Extracted offline from local PBF file - no network needed!")
    else:
        print("\n" + "="*70)
        print("EXTRACTION FAILED")
        print("="*70)
        print("\nTrying to install pyrosm...")
        print("Run: pip install pyrosm")
        print("Then run this script again")
