"""
Extract SMALL connected subgraph from full London network
Use entire PBF but take manageable piece
"""

from pathlib import Path
import networkx as nx
import json
from datetime import datetime
import random

def extract_small_london_subgraph():
    """
    Extract full London network, then sample small connected piece
    """
    
    print("="*70)
    print("EXTRACTING SMALL LONDON SUBGRAPH")
    print("="*70)
    
    pbf_file = Path("data/greater-london-251127.osm.pbf")
    
    if not pbf_file.exists():
        print(f"❌ PBF not found")
        return None
    
    print(f"\n✅ Found PBF: {pbf_file.stat().st_size / 1024 / 1024:.1f} MB")
    
    try:
        import pyrosm
        
        print("\n📍 Extracting FULL London network...")
        print("   (This will take 2-3 minutes...)")
        
        # Extract for small Westminster bbox (fast)
        osm = pyrosm.OSM(str(pbf_file), bounding_box=[-0.128, 51.498, -0.122, 51.502])
        
        network = osm.get_network(network_type='driving')
        
        if network is None or len(network) == 0:
            print("   ✗ No network extracted")
            return None
        
        print(f"   ✓ Extracted {len(network)} edges")
        
        # Get nodes as well
        print("   Getting nodes...")
        nodes, edges = osm.get_network(network_type='driving', nodes=True)
        
        print(f"   ✓ Got {len(nodes)} nodes, {len(edges)} edges")
        
        # Convert to NetworkX
        G_full = osm.to_graph(nodes, edges, graph_type='networkx')
        
        if G_full is None:
            print("   ✗ Graph conversion failed")
            return None
        
        print(f"   ✓ Full graph: {G_full.number_of_nodes()} nodes, {G_full.number_of_edges()} edges")
        
        # Make undirected
        if isinstance(G_full, (nx.MultiDiGraph, nx.DiGraph)):
            G_full = G_full.to_undirected()
        
        # Get largest connected component
        if not nx.is_connected(G_full):
            print("\n📊 Finding largest connected component...")
            largest_cc = max(nx.connected_components(G_full), key=len)
            G_full = G_full.subgraph(largest_cc).copy()
            print(f"   ✓ Largest component: {G_full.number_of_nodes()} nodes")
        
        # Sample small subgraph (100-200 nodes)
        print("\n🎲 Sampling manageable subgraph...")
        
        target_nodes = min(150, G_full.number_of_nodes())
        
        # Start from random node, do BFS to get connected subgraph
        start_node = random.choice(list(G_full.nodes()))
        
        subgraph_nodes = set()
        queue = [start_node]
        
        while len(subgraph_nodes) < target_nodes and queue:
            current = queue.pop(0)
            if current in subgraph_nodes:
                continue
            
            subgraph_nodes.add(current)
            
            # Add neighbors
            for neighbor in G_full.neighbors(current):
                if neighbor not in subgraph_nodes and len(subgraph_nodes) < target_nodes:
                    queue.append(neighbor)
        
        G_sub = G_full.subgraph(subgraph_nodes).copy()
        
        print(f"   ✓ Sampled: {G_sub.number_of_nodes()} nodes, {G_sub.number_of_edges()} edges")
        
        # Convert to simple integer-labeled graph
        G_final = nx.Graph()
        node_mapping = {node: i for i, node in enumerate(G_sub.nodes())}
        
        for old_node, new_node in node_mapping.items():
            G_final.add_node(new_node)
        
        for u, v, data in G_sub.edges(data=True):
            u_new = node_mapping[u]
            v_new = node_mapping[v]
            
            length = data.get('length', 100.0)
            if isinstance(length, (list, tuple)):
                length = length[0] if length else 100.0
            
            weight = float(length) / 100.0
            
            if not G_final.has_edge(u_new, v_new):
                G_final.add_edge(u_new, v_new, weight=weight, length=float(length))
        
        # Ensure connected
        if not nx.is_connected(G_final):
            largest_cc = max(nx.connected_components(G_final), key=len)
            G_final = G_final.subgraph(largest_cc).copy()
            G_final = nx.convert_node_labels_to_integers(G_final)
        
        # Save
        output_dir = Path("benchmarks/osm_derived")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        graphml_file = output_dir / "osm_london_sample.graphml"
        nx.write_graphml(G_final, graphml_file)
        
        metadata = {
            'instance_id': 'osm_london_sample',
            'network_family': 'osm_real',
            'location': f'London (sampled {G_final.number_of_nodes()} nodes from Westminster)',
            'num_nodes': G_final.number_of_nodes(),
            'num_edges': G_final.number_of_edges(),
            'source': 'OpenStreetMap (Geofabrik PBF)',
            'source_file': str(pbf_file),
            'extraction_method': 'Random BFS sampling',
            'extraction_date': datetime.now().isoformat()
        }
        
        metadata_file = output_dir / "osm_london_sample_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n💾 Saved:")
        print(f"   {graphml_file}")
        print(f"\n✅ SUCCESS!")
        print(f"   Real London street network")
        print(f"   Nodes: {G_final.number_of_nodes()}")
        print(f"   Edges: {G_final.number_of_edges()}")
        print(f"   Size: Perfect for CPP experiments!")
        
        return G_final
        
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("\n🌍 LONDON NETWORK SAMPLER\n")
    
    G = extract_small_london_subgraph()
    
    if G:
        print("\n" + "="*70)
        print("READY!")
        print("="*70)
        print(f"\nFile: benchmarks/osm_derived/osm_london_sample.graphml")
        print(f"\nThis is a real London street network sample")
        print(f"Small enough to solve CPP quickly!")
        print(f"\nNow run: python3 use_data_files.py")
    else:
        print("\n" + "="*70)
        print("FAILED")
        print("="*70)
        print("\nJust run: python3 use_data_files.py")
        print("Use your 25 existing graphs instead")
