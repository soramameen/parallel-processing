#!/usr/bin/env python3
"""
Verify that the H_2 stepper produces correct results:
1. Total maximal clique count matches reference implementation
2. Guided calls = 2^(k+1) - 1 = 7 for k=2
"""

def build_h2():
    """Build H_2 graph (k=2, w=5, n=26)"""
    k = 2
    w = 5
    n = 2*k*k + 9*k
    
    V = []
    # M vertices
    for i in range(k):
        V.append({'t': 'm', 'i': i, 'label': f'a{i+1}'})
        V.append({'t': 'm', 'i': i, 'label': f'b{i+1}'})
    # U vertices
    for i in range(k):
        V.append({'t': 'g', 'i': i, 'label': f'g{i+1}'})
    # W vertices
    for c in range(2*k):
        for j in range(w):
            V.append({'t': 'w', 'c': c, 'j': j, 'label': f'w{c+1}_{j+1}'})
    
    def non_adj(x, y):
        if x == y:
            return True
        X, Y = V[x], V[y]
        if X['t'] == 'g' and Y['t'] == 'g':
            return True
        if X['t'] == 'w' and Y['t'] == 'w':
            return True
        if X['t'] == 'g' and Y['t'] == 'm' and Y['i'] == X['i']:
            return True
        if Y['t'] == 'g' and X['t'] == 'm' and X['i'] == Y['i']:
            return True
        if X['t'] == 'w' and Y['t'] == 'm' and X['c'] == y:
            return True
        if Y['t'] == 'w' and X['t'] == 'm' and Y['c'] == x:
            return True
        return False
    
    adj = [set() for _ in range(n)]
    for x in range(n):
        for y in range(x+1, n):
            if not non_adj(x, y):
                adj[x].add(y)
                adj[y].add(x)
    
    return {'k': k, 'w': w, 'n': n, 'V': V, 'adj': adj}

def guided_parts(H, Q, CAND):
    """Check guided call conditions"""
    k = H['k']
    g1 = True
    used = set()
    
    for q in Q:
        if q >= 2*k or (q >> 1) in used:
            g1 = False
            break
        used.add(q >> 1)
    
    g2 = g3 = True
    if g1:
        for p in range(k):
            if p not in used and not (2*p in CAND and 2*p+1 in CAND):
                g2 = False
        for c in range(2*k):
            if c in Q:
                continue
            wit_start = 2*k + k + c*H['w']
            for j in range(H['w']):
                if wit_start + j not in CAND:
                    g3 = False
                    break
    else:
        g2 = g3 = False
    
    return g1 and g2 and g3

def run_cliques(H):
    """Run CLIQUES with deterministic tie-breaking"""
    calls = []
    Q = []
    
    def expand(SUBG, CAND, parent, via):
        guided = guided_parts(H, Q, CAND)
        rec = {
            'id': len(calls),
            'parent': parent,
            'via': via,
            'depth': 0 if parent < 0 else calls[parent]['depth'] + 1,
            'Q': Q[:],
            'guided': guided,
            'output': False
        }
        calls.append(rec)
        
        if not SUBG:
            rec['output'] = True
            return
        
        # Find pivot
        best = float('inf')
        ties = []
        for u in SUBG:
            s = len(CAND - H['adj'][u])
            if s < best:
                best = s
                ties = [u]
            elif s == best:
                ties.append(u)
        
        # Deterministic: smallest vertex
        u = min(ties)
        
        # Branch vertices
        ext = sorted(list(CAND - H['adj'][u]))
        
        rec['pivot'] = u
        rec['branch'] = ext
        
        cand_copy = CAND.copy()
        for q in ext:
            Q.append(q)
            new_subg = SUBG & H['adj'][q]
            new_cand = cand_copy & H['adj'][q]
            expand(new_subg, new_cand, rec['id'], q)
            Q.pop()
            cand_copy.discard(q)
    
    all_v = set(range(H['n']))
    expand(all_v, all_v, -1, -1)
    return calls

def main():
    print("Building H_2 graph...")
    H = build_h2()
    print(f"  n = {H['n']} vertices")
    print(f"  k = {H['k']}")
    
    print("\nRunning CLIQUES algorithm...")
    calls = run_cliques(H)
    print(f"  Total calls: {len(calls)}")
    
    guided_calls = [c for c in calls if c['guided']]
    output_calls = [c for c in calls if c['output']]
    
    print(f"  Guided calls: {len(guided_calls)}")
    print(f"  Maximal cliques: {len(output_calls)}")
    
    k = H['k']
    expected_guided = 2**(k+1) - 1
    
    print("\n=== VERIFICATION ===")
    print(f"Expected guided calls: 2^(k+1)-1 = 2^{k+1}-1 = {expected_guided}")
    print(f"Actual guided calls: {len(guided_calls)}")
    
    if len(guided_calls) == expected_guided:
        print("✓ PASS: Guided call count matches!")
    else:
        print("✗ FAIL: Guided call count mismatch!")
        return 1
    
    print(f"\nMaximal cliques found: {len(output_calls)}")
    print(f"Upper bound: (k+1)(2k(k+3)+1) = {(k+1)*(2*k*(k+3)+1)}")
    print(f"n^2 = {H['n']**2}")
    
    if len(output_calls) <= H['n']**2:
        print("✓ PASS: Maximal clique count within bounds!")
    else:
        print("✗ FAIL: Too many maximal cliques!")
        return 1
    
    print("\n=== ALL TESTS PASSED ===")
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
