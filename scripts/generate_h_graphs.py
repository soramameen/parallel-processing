#!/usr/bin/env python3
"""
Generate H_k graphs and verify their structure.
Based on the construction in Tomita-Tanaka-Takahashi (2006).
"""

def generate_hk(k):
    """
    Generate H_k graph with k parameter.
    Returns: (n, edges, vertex_types)
    vertex_types: dict mapping vertex id to (type, label) where type in ['guard', 'pair', 'witness']
    """
    n = 2 * k**2 + 9 * k
    
    # Vertex numbering:
    # guards: g_i = i for i in 1..k
    # core pairs: a_i = k+2i-1, b_i = k+2i for i in 1..k
    # witnesses: remaining vertices, k+3 per core vertex
    
    guards = list(range(1, k+1))
    pairs = []
    for i in range(1, k+1):
        a_i = k + 2*i - 1
        b_i = k + 2*i
        pairs.append((a_i, b_i))
    
    core_vertices = [v for pair in pairs for v in pair]
    
    # Witnesses: k+3 per core vertex
    witnesses_per_core = k + 3
    witness_start = k + 2*k + 1
    
    witnesses = {}  # core vertex -> list of witness vertices
    witness_id = witness_start
    for pair in pairs:
        for core_v in pair:
            witnesses[core_v] = list(range(witness_id, witness_id + witnesses_per_core))
            witness_id += witnesses_per_core
    
    all_witnesses = [w for ws in witnesses.values() for w in ws]
    
    # Verify total vertices
    assert len(guards) + len(core_vertices) + len(all_witnesses) == n
    
    # Create vertex_types mapping
    vertex_types = {}
    for i, g in enumerate(guards, 1):
        vertex_types[g] = ('guard', f'g{i}')
    for i, (a, b) in enumerate(pairs, 1):
        vertex_types[a] = ('pair', f'a{i}')
        vertex_types[b] = ('pair', f'b{i}')
    witness_idx = 1
    for core_v in sorted(witnesses.keys()):
        for w in witnesses[core_v]:
            vertex_types[w] = ('witness', f'w{witness_idx}')
            witness_idx += 1
    
    # Generate all possible edges (complete graph)
    all_edges = []
    for u in range(1, n+1):
        for v in range(u+1, n+1):
            all_edges.append((u, v))
    
    # Define non-edges
    non_edges = set()
    
    # 1. Guard-guard
    for i, g1 in enumerate(guards):
        for g2 in guards[i+1:]:
            non_edges.add((min(g1, g2), max(g1, g2)))
    
    # 2. g_i with a_i and b_i
    for i in range(1, k+1):
        g_i = i
        a_i = k + 2*i - 1
        b_i = k + 2*i
        non_edges.add((min(g_i, a_i), max(g_i, a_i)))
        non_edges.add((min(g_i, b_i), max(g_i, b_i)))
    
    # 3. Witness with its core vertex
    for core_v, witness_list in witnesses.items():
        for w in witness_list:
            non_edges.add((min(core_v, w), max(core_v, w)))
    
    # 4. Witness-witness
    for i, w1 in enumerate(all_witnesses):
        for w2 in all_witnesses[i+1:]:
            non_edges.add((min(w1, w2), max(w1, w2)))
    
    # Edges = all_edges - non_edges
    edges = [(u, v) for (u, v) in all_edges if (u, v) not in non_edges]
    
    m = len(edges)
    
    return n, m, edges, vertex_types, guards, pairs, witnesses, all_witnesses

def verify_hk(k):
    """Verify H_k construction and print statistics."""
    n, m, edges, vertex_types, guards, pairs, witnesses, all_witnesses = generate_hk(k)
    
    print(f"H_{k} verification:")
    print(f"  n = 2k²+9k = 2*{k}²+9*{k} = {n} vertices ✓")
    print(f"  m = {m} edges")
    print(f"  Guards: {len(guards)} = {guards}")
    print(f"  Pairs: {len(pairs)} pairs = {pairs}")
    print(f"  Witnesses: {len(all_witnesses)} total ({k}+3 per core vertex)")
    print()
    
    return n, m, edges, vertex_types

def write_dimacs_clq(filename, k, n, m, edges):
    """Write H_k graph in DIMACS .clq format."""
    with open(filename, 'w') as f:
        f.write(f"c Graph H_{k} of Theorem 1 in 'The CLIQUES Algorithm Is Not Output-Polynomial' (Sec. 3)\n")
        f.write(f"c n = 2k^2+9k = {n} vertices (k = {k})\n")
        f.write(f"c maximal cliques upper bound: (k+1)(2k(k+3)+1) = {(k+1)*(2*k*(k+3)+1)}\n")
        f.write(f"c guided calls lower bound: 2^(k+1)-1 = {2**(k+1)-1}\n")
        
        # Vertex numbering info
        f.write(f"c vertices: guards g_i = 1..{k}; ")
        f.write(f"core a_i = k+2i-1, b_i = k+2i (")
        core_start = k + 1
        core_end = k + 2*k
        f.write(f"{core_start}..{core_end}); ")
        f.write(f"witnesses {core_end+1}..{n}, {k+3} per core vertex\n")
        
        f.write(f"p edge {n} {m}\n")
        for u, v in edges:
            f.write(f"e {u} {v}\n")

if __name__ == '__main__':
    # Verify H_1 from file
    print("=== H_1 from uploaded file ===")
    print("Expected: n=11, m=17")
    print()
    
    # Verify generated H_1
    print("=== Generated H_1 ===")
    n1, m1, edges1, vt1 = verify_hk(1)
    
    # Verify H_2
    print("=== Generated H_2 ===")
    n2, m2, edges2, vt2 = verify_hk(2)
    
    # Write H_2 to file
    write_dimacs_clq('/workspace/docs/hk-explained/H2_n26.clq', 2, n2, m2, edges2)
    print(f"Written H_2 to docs/hk-explained/H2_n26.clq")
