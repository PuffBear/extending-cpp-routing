"""
Extract Northern Zone OSM data for ML training
Using pyrosm to handle PBF files
"""

from pyrosm import OSM, get_data
import networkx as nx
from pathlib import Path
import json
import random

print("="*70)
print("EXTRACTING NORTHERN ZONE NETWORK")
print("="*70)

pbf_file = Path("data/northern-zone-251127.osm.pbf")

print(f"\n📁 Input: {pbf_file}")
print(f"   Size: {pbf_file.stat().st_size / 1024 / 1024:.1f} MB")

print("\n🔄 Extracting street network with pyrosm...")

try:
    # Load OSM data
    print("   Loading PBF file...")
    osm = OSM(str(pbf_file))

    # Get driving network
    print("   Extracting drivable roads...")
    nodes, edges = osm.get_network(network_type="driving", nodes=True)

    print(f"   Extracted {len(edges)} edges, {len(nodes)} nodes")

    # Convert to NetworkX graph
    print("   Converting to NetworkX...")
    G = osm.to_graph(nodes, edges, graph_type="networkx")

    print(f"   Initial graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # Convert to undirected
    if G.is_directed():
        G = G.to_undirected()
        print(f"   Converted to undirected")

    # Sample if too large
    target_nodes = 200
    if G.number_of_nodes() > target_nodes:
        print(f"   Sampling {target_nodes} nodes...")

        # Get largest connected component first
        if not nx.is_connected(G):
            largest_cc = max(nx.connected_components(G), key=len)
            G = G.subgraph(largest_cc).copy()
            print(f"   Largest component: {G.number_of_nodes()} nodes")

        # BFS sampling
        random.seed(42)
        start_node = random.choice(list(G.nodes()))

        sampled_nodes = set()
        queue = [start_node]
        visited = {start_node}

        while len(sampled_nodes) < target_nodes and queue:
            current = queue.pop(0)
            sampled_nodes.add(current)

            # Add neighbors
            neighbors = list(G.neighbors(current))
            random.shuffle(neighbors)

            for neighbor in neighbors[:3]:
                if neighbor not in visited and len(sampled_nodes) < target_nodes:
                    visited.add(neighbor)
                    queue.append(neighbor)

        G = G.subgraph(sampled_nodes).copy()
        print(f"   Sampled: {G.number_of_nodes()} nodes")

    # Add weights
    for u, v, data in G.edges(data=True):
        if 'length' in data:
            # Convert to km
            G[u][v]['weight'] = data['length'] / 1000.0
        else:
            G[u][v]['weight'] = 1.0

    # Ensure connected
    if not nx.is_connected(G):
        largest = max(nx.connected_components(G), key=len)
        G = G.subgraph(largest).copy()

    # Convert node labels to integers
    G = nx.convert_node_labels_to_integers(G)

    print(f"\n✅ Final network:")
    print(f"   Nodes: {G.number_of_nodes()}")
    print(f"   Edges: {G.number_of_edges()}")
    print(f"   Connected: {nx.is_connected(G)}")

    # Save
    output_dir = Path("benchmarks/osm_derived")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "osm_northern_zone_sample.graphml"
    nx.write_graphml(G, str(output_file))
    print(f"\n💾 Saved: {output_file}")

    # Metadata
    from datetime import datetime
    metadata = {
        "instance_id": "osm_northern_zone_sample",
        "network_family": "osm_real",
        "location": "Northern Zone (sampled from OSM)",
        "num_nodes": G.number_of_nodes(),
        "num_edges": G.number_of_edges(),
        "source": "OpenStreetMap (Geofabrik PBF)",
        "source_file": str(pbf_file),
        "extraction_method": "pyrosm + BFS sampling",
        "extraction_date": datetime.now().isoformat()
    }

    metadata_file = output_dir / "osm_northern_zone_sample_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"💾 Saved: {metadata_file}")

    print("\n" + "="*70)
    print("✅ EXTRACTION COMPLETE!")
    print("="*70)
    print("\nNow you have 2 real-world networks for ML training:")
    print("  1. London (150 nodes)")
    print(f"  2. Northern Zone ({G.number_of_nodes()} nodes)")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
