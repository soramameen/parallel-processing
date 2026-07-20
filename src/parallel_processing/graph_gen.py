"""Seeded generators for graphs of contrasting shapes.

Each generator returns an undirected :data:`Graph` and is deterministic for
a given seed, so benchmark runs are reproducible. The families are chosen to
span the structural axes that matter for maximal clique enumeration:

- degeneracy: trees (1) and grids (2) at the bottom, dense random and
  Moon-Moser graphs near the top;
- degree distribution: Erdős-Rényi (concentrated) vs. Barabási-Albert
  (power-law hubs, like the SNAP social networks);
- output size: grids (one clique per edge) vs. Moon-Moser ``K_{3,3,…,3}``,
  the extremal graphs achieving the ``3^{n/3}`` maximal clique bound.
"""

from __future__ import annotations

import random

# A vertex to its set of neighbours; matches parallel_processing.cliques.Graph.
Graph = dict[int, set[int]]


def _empty(n: int) -> Graph:
    return {v: set() for v in range(n)}


def _add_edge(graph: Graph, u: int, v: int) -> None:
    graph[u].add(v)
    graph[v].add(u)


def random_tree(n: int, seed: int) -> Graph:
    """Random recursive tree: vertex i attaches to a uniform earlier vertex."""
    rng = random.Random(seed)
    graph = _empty(n)
    for v in range(1, n):
        _add_edge(graph, v, rng.randrange(v))
    return graph


def grid_2d(rows: int, cols: int) -> Graph:
    """4-neighbour grid; triangle-free, so every edge is a maximal clique."""
    graph = _empty(rows * cols)
    for r in range(rows):
        for c in range(cols):
            v = r * cols + c
            if c + 1 < cols:
                _add_edge(graph, v, v + 1)
            if r + 1 < rows:
                _add_edge(graph, v, v + cols)
    return graph


def erdos_renyi(n: int, avg_degree: float, seed: int) -> Graph:
    """G(n, m)-style sparse random graph with ``n * avg_degree / 2`` edges.

    Sampling a fixed edge count instead of per-pair coin flips keeps
    generation O(m) so large sparse instances stay cheap to build.
    """
    rng = random.Random(seed)
    graph = _empty(n)
    target = int(n * avg_degree / 2)
    edges = 0
    while edges < target:
        u = rng.randrange(n)
        v = rng.randrange(n)
        if u != v and v not in graph[u]:
            _add_edge(graph, u, v)
            edges += 1
    return graph


def dense_random(n: int, p: float, seed: int) -> Graph:
    """G(n, p) with per-pair coin flips; only sensible for small ``n``."""
    rng = random.Random(seed)
    graph = _empty(n)
    for u in range(n):
        for v in range(u + 1, n):
            if rng.random() < p:
                _add_edge(graph, u, v)
    return graph


def barabasi_albert(n: int, m: int, seed: int) -> Graph:
    """Preferential attachment: each new vertex links to ``m`` earlier ones.

    Attachment is degree-proportional via the classic repeated-endpoints
    list, yielding the power-law hubs of real social networks.
    """
    rng = random.Random(seed)
    graph = _empty(n)
    # Seed with a clique on the first m + 1 vertices so early attachment
    # targets have nonzero degree.
    for u in range(m + 1):
        for v in range(u + 1, m + 1):
            _add_edge(graph, u, v)
    endpoints = [v for v in range(m + 1) for _ in range(m)]
    for v in range(m + 1, n):
        targets: set[int] = set()
        while len(targets) < m:
            targets.add(endpoints[rng.randrange(len(endpoints))])
        for t in targets:
            _add_edge(graph, v, t)
            endpoints.append(t)
        endpoints.extend([v] * m)
    return graph


def moon_moser(k: int) -> Graph:
    """Complete multipartite ``K_{3,3,…,3}`` with ``k`` groups of 3.

    The extremal graphs of Moon & Moser (1965): ``3^k`` maximal cliques on
    ``3k`` vertices, the worst case both papers' bounds are tight against.
    """
    n = 3 * k
    return {
        v: {w for w in range(n) if w // 3 != v // 3} for v in range(n)
    }
