import networkx as nx

G = nx.cycle_graph(4)
for u,v in G.edges():
    G[u][v]['weight'] = 1.0
    
circuit = list(nx.eulerian_circuit(G))
print(f'Circuit type: {type(circuit[0])}')
print(f'Circuit: {circuit[:5]}')
print(f'Length: {len(circuit)}')
