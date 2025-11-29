"""
Extract Northern Zone - Lightweight Approach
Process PBF in chunks with strict memory limits
"""

import subprocess
import networkx as nx
from pathlib import Path
import json
from datetime import datetime

print("="*70)
print("NORTHERN ZONE EXTRACTION - LIGHTWEIGHT")
print("="*70)

pbf_file = Path("data/northern-zone-251127.osm.pbf")
output_dir = Path("benchmarks/osm_derived")
output_dir.mkdir(parents=True, exist_ok=True)

print(f"\n📁 Input: {pbf_file}")
print(f"   Size: {pbf_file.stat().st_size / 1024 / 1024:.1f} MB")

# Strategy: Use osmium to extract a SMALL bbox first, then process
# This reduces memory usage dramatically

print("\n🔄 Strategy: Extract small bounding box first using osmium...")
print("   This will create a much smaller file to process")

# Check if osmium is available
try:
    result = subprocess.run(['osmium', '--version'],
                          capture_output=True,
                          text=True,
                          timeout=5)
    has_osmium = result.returncode == 0
except:
    has_osmium = False

if has_osmium:
    print("   ✓ osmium-tool found")

    # Extract a small bbox (0.1 degree square - roughly 10km x 10km)
    # This will be MUCH smaller than the full 206MB file

    # Northern Zone rough center coordinates
    lat_center = 51.6  # Approximate
    lon_center = -0.1

    bbox_size = 0.05  # degrees (about 5km)

    bbox = f"{lon_center - bbox_size},{lat_center - bbox_size},{lon_center + bbox_size},{lat_center + bbox_size}"

    small_pbf = Path("data/northern_zone_small_extract.osm.pbf")

    print(f"\n   Extracting bbox: {bbox}")
    print(f"   Output: {small_pbf}")

    cmd = [
        'osmium', 'extract',
        '--bbox', bbox,
        '--strategy', 'simple',
        '--overwrite',
        str(pbf_file),
        '-o', str(small_pbf)
    ]

    try:
        subprocess.run(cmd, check=True, timeout=120)
        print(f"   ✓ Small extract created: {small_pbf.stat().st_size / 1024 / 1024:.1f} MB")

        # Now process the SMALL file with pyrosm
        print("\n🔄 Processing small extract with pyrosm...")

        from pyrosm import OSM

        osm = OSM(str(small_pbf))
        nodes, edges = osm.get_network(network_type="driving", nodes=True)
        G = osm.to_graph(nodes, edges, graph_type="networkx")

        print(f"   Extracted {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        # Convert to undirected
        if G.is_directed():
            G = G.to_undirected()

        # Get largest component
        if not nx.is_connected(G):
            largest = max(nx.connected_components(G), key=len)
            G = G.subgraph(largest).copy()
            print(f"   Largest component: {G.number_of_nodes()} nodes")

        # Add weights
        for u, v, data in G.edges(data=True):
            if 'length' in data:
                G[u][v]['weight'] = data['length'] / 1000.0  # Convert to km
            else:
                G[u][v]['weight'] = 1.0

        # Convert to integers
        G = nx.convert_node_labels_to_integers(G)

        print(f"\n✅ Final network:")
        print(f"   Nodes: {G.number_of_nodes()}")
        print(f"   Edges: {G.number_of_edges()}")
        print(f"   Connected: {nx.is_connected(G)}")

        # Save
        output_file = output_dir / "osm_northern_zone_sample.graphml"
        nx.write_graphml(G, str(output_file))
        print(f"\n💾 Saved: {output_file}")

        # Metadata
        metadata = {
            'instance_id': 'osm_northern_zone_sample',
            'network_family': 'osm_real',
            'location': 'Northern Zone, London (OSM extract)',
            'num_nodes': G.number_of_nodes(),
            'num_edges': G.number_of_edges(),
            'source': 'OpenStreetMap via osmium extract + pyrosm',
            'extraction_method': 'osmium bbox extract + pyrosm',
            'extraction_date': datetime.now().isoformat()
        }

        metadata_file = output_dir / "osm_northern_zone_sample_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"💾 Saved: {metadata_file}")

        print("\n" + "="*70)
        print("✅ NORTHERN ZONE EXTRACTION COMPLETE!")
        print("="*70)

        # Clean up small extract
        small_pbf.unlink()
        print(f"\n🧹 Cleaned up temporary file: {small_pbf}")

    except subprocess.TimeoutExpired:
        print("   ✗ osmium extract timed out (file too large)")
        has_osmium = False
    except Exception as e:
        print(f"   ✗ osmium extract failed: {e}")
        has_osmium = False

else:
    print("   ✗ osmium-tool not found")

if not has_osmium:
    print("\n" + "="*70)
    print("FALLBACK: Using OSMnx with strict limits")
    print("="*70)

    try:
        import osmnx as ox

        # Use a VERY small area
        # North London rough center
        center_point = (51.6, -0.1)

        print(f"\nExtracting street network around {center_point}")
        print("   Radius: 2000m (2km)")

        # Small radius to avoid memory issues
        G = ox.graph_from_point(center_point, dist=2000, network_type='drive')

        print(f"   Extracted {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        # Convert to undirected simple graph (not multi)
        G_simple = nx.Graph()

        # Add all nodes
        G_simple.add_nodes_from(G.nodes(data=True))

        # Add edges with weights
        for u, v, key, data in G.edges(data=True, keys=True):
            if not G_simple.has_edge(u, v):
                # First edge between u-v
                weight = data.get('length', 1000.0) / 1000.0  # Convert to km
                G_simple.add_edge(u, v, weight=weight)
            else:
                # Multiple edges - take minimum length
                existing_weight = G_simple[u][v].get('weight', float('inf'))
                new_weight = data.get('length', 1000.0) / 1000.0
                G_simple[u][v]['weight'] = min(existing_weight, new_weight)

        G = G_simple
        print(f"   Converted to simple graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        # Convert to integers
        G = nx.convert_node_labels_to_integers(G)

        print(f"\n✅ Final network:")
        print(f"   Nodes: {G.number_of_nodes()}")
        print(f"   Edges: {G.number_of_edges()}")

        # Save
        output_file = output_dir / "osm_northern_zone_sample.graphml"
        nx.write_graphml(G, str(output_file))
        print(f"\n💾 Saved: {output_file}")

        metadata = {
            'instance_id': 'osm_northern_zone_sample',
            'network_family': 'osm_real',
            'location': 'Northern Zone, London (OSMnx 2km radius)',
            'num_nodes': G.number_of_nodes(),
            'num_edges': G.number_of_edges(),
            'source': 'OpenStreetMap via OSMnx',
            'extraction_method': 'OSMnx point query (2km radius)',
            'extraction_date': datetime.now().isoformat()
        }

        metadata_file = output_dir / "osm_northern_zone_sample_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"💾 Saved: {metadata_file}")

        print("\n" + "="*70)
        print("✅ EXTRACTION COMPLETE (OSMnx fallback)!")
        print("="*70)

    except Exception as e:
        print(f"\n❌ OSMnx fallback failed: {e}")
        import traceback
        traceback.print_exc()

        print("\n" + "="*70)
        print("⚠️  UNABLE TO EXTRACT NORTHERN ZONE")
        print("="*70)
        print("\nThe 206MB PBF file is too large for available memory.")
        print("\nOptions:")
        print("1. Use smaller OSM extract (download smaller area)")
        print("2. Use synthetic networks (already generated)")
        print("3. Install osmium-tool: brew install osmium-tool")
