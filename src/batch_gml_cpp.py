
import argparse, time, glob, os
import networkx as nx
import pandas as pd

def load_gml(path):
    # Robust read for GML; networkx returns Graph or DiGraph.
    G = nx.read_gml(path)
    # ensure weights exist
    for u, v, data in G.edges(data=True):
        if "weight" not in data:
            data["weight"] = 1.0
    return G

def cpp_cost(G):
    # Classical undirected CPP via matching; convert to undirected MultiGraph
    if G.is_directed():
        G = G.to_undirected()
    MG = nx.MultiGraph(G)
    # metric closure
    length = dict(nx.all_pairs_dijkstra_path_length(MG, weight="weight"))
    path = dict(nx.all_pairs_dijkstra_path(MG, weight="weight"))
    # odd set
    odd = [v for v,deg in MG.degree() if deg % 2 == 1]
    if odd:
        K = nx.Graph()
        K.add_nodes_from(odd)
        for i,u in enumerate(odd):
            for v in odd[i+1:]:
                K.add_edge(u, v, weight=length[u][v])
        matching = nx.algorithms.matching.min_weight_matching(K, maxcardinality=True, weight="weight")
        for u,v in matching:
            sp = path[u][v]
            for a,b in zip(sp, sp[1:]):
                w = MG[a][b][0].get("weight",1.0) if isinstance(MG, nx.MultiGraph) else MG[a][b].get("weight",1.0)
                MG.add_edge(a,b,weight=w)
    # euler cost
    total = 0.0
    for (u,v,key) in nx.eulerian_circuit(MG):
        total += MG[u][v][key]["weight"]
    return total, MG.number_of_nodes(), MG.number_of_edges()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_glob", default="data/*.gml", help="Pattern for GML files")
    ap.add_argument("--out_csv", default="results/gml_cpp_results.csv")
    args = ap.parse_args()

    rows = []
    for fp in glob.glob(args.data_glob):
        t0 = time.time()
        try:
            G = load_gml(fp)
            cost, n, m = cpp_cost(G)
            dt = time.time() - t0
            rows.append({
                "instance": os.path.basename(fp),
                "algorithm": "Classical_CPP",
                "variant": "CPP",
                "cost": cost,
                "time": dt,
                "nodes": n,
                "edges": m
            })
            print(f"[OK] {fp}  cost={cost:.3f}  time={dt:.4f}s  n={n} m={m}")
        except Exception as e:
            print(f"[FAIL] {fp}  err={e}")

    if rows:
        os.makedirs(os.path.dirname(args.out_csv), exist_ok=True)
        pd.DataFrame(rows).to_csv(args.out_csv, index=False)
        print("Saved:", args.out_csv)

if __name__ == "__main__":
    main()
