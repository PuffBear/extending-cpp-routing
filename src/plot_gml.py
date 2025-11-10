#!/usr/bin/env python3
# plot_gml.py
import argparse
from pathlib import Path
import math

import networkx as nx
import matplotlib.pyplot as plt

def load_graph(path: Path):
    # networkx auto-detects directedness from the file if stored that way
    G = nx.read_gml(path, destringizer=None, label='id')  # 'id' keeps numeric names if present
    return G

def pick_layout(G):
    # Use 'pos' if embedded; else spring for general, or kamada_kawai for smaller graphs
    pos_attr = nx.get_node_attributes(G, 'pos')
    if pos_attr:
        # ensure tuple(float,float)
        pos = {n: (float(x), float(y)) for n,(x,y) in pos_attr.items()}
    else:
        if len(G) <= 400:
            pos = nx.kamada_kawai_layout(G)
        else:
            pos = nx.spring_layout(G, k=1.2/math.sqrt(len(G)), iterations=200)
    return pos

def is_windy(G):
    # If edge has 'cost_fwd'/'cost_rev' or if directed with asymmetric weights
    if G.is_directed():
        return True
    for u, v, d in G.edges(data=True):
        if 'cost_fwd' in d or 'cost_rev' in d:
            return True
    return False

def edge_weight(u, v, d):
    # Choose a representative label; prefer 'weight', else 'cost', else length
    for key in ('weight','cost','w','c'):
        if key in d:
            return d[key]
    # fallback: 1.0 (or Euclidean length if coordinates exist)
    return 1.0

def draw_graph(G, out_path: Path, dpi=300, show_labels=False, max_edge_labels=250):
    pos = pick_layout(G)
    plt.figure(figsize=(10, 10), dpi=dpi)

    # Node styling
    nx.draw_networkx_nodes(G, pos, node_size=80, node_color="#BCD4E6", edgecolors="#2E4057", linewidths=0.6)
    nx.draw_networkx_labels(G, pos, font_size=6, font_color="#1b1b1b")

    # Edge styling
    directed = G.is_directed()
    alpha = 0.9
    width = 0.8 if len(G) < 1000 else 0.4
    arrows = directed
    arrowstyle = "-|>" if directed else "-"

    # Draw edges
    nx.draw_networkx_edges(
        G, pos,
        width=width,
        alpha=alpha,
        arrows=arrows,
        arrowstyle=arrowstyle,
        arrowsize=10 if len(G) < 600 else 6,
        connectionstyle="arc3,rad=0.02" if directed else "arc3,rad=0.0"
    )

    # Edge labels (sample if graph is large)
    if show_labels:
        edges = list(G.edges(data=True))
        if len(edges) > max_edge_labels:
            # sample evenly
            step = max(1, len(edges) // max_edge_labels)
            edges = edges[::step]
        e_labels = {(u, v): f"{edge_weight(u,v,d):.2f}" for u, v, d in edges}
        nx.draw_networkx_edge_labels(G, pos, e_labels, font_size=5, label_pos=0.5, rotate=False)

    plt.axis('off')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path)
    # Also produce an SVG for magnification
    plt.savefig(out_path.with_suffix(".svg"))
    plt.close()
    print(f"[OK] Saved figure: {out_path} and {out_path.with_suffix('.svg')}")

def main():
    ap = argparse.ArgumentParser(description="Render a GML graph to PNG/SVG.")
    ap.add_argument("gml", type=Path, help="Input .gml file")
    ap.add_argument("-o", "--out", type=Path, default=None, help="Output image (default: same name with .png)")
    ap.add_argument("--labels", action="store_true", help="Draw sampled edge labels (weights)")
    ap.add_argument("--dpi", type=int, default=300, help="Figure DPI (default 300)")
    args = ap.parse_args()

    G = load_graph(args.gml)
    out = args.out if args.out else args.gml.with_suffix(".png")
    draw_graph(G, out, dpi=args.dpi, show_labels=args.labels)

if __name__ == "__main__":
    main()
