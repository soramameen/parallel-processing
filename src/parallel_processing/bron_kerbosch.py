"""Bron-Kerbosch algorithm for enumerating maximal cliques.

Two variants are provided:

- :func:`bron_kerbosch_simple`: the basic recursive formulation.
- :func:`bron_kerbosch_pivot`: the pivot-based variant that prunes the
  search tree by skipping neighbours of a chosen pivot vertex.

Both enumerate all *maximal cliques* of an undirected graph represented as
``dict[int, set[int]]`` (a vertex to its set of neighbours).

Run as a module to see both variants applied to a sample graph::

    python -m parallel_processing.bron_kerbosch
"""

from __future__ import annotations

# A vertex to its set of neighbours. The graph is treated as undirected,
# so every edge ``{u, v}`` must appear as ``v in graph[u]`` and ``u in graph[v]``.
Graph = dict[int, set[int]]


def _sort_cliques(cliques: list[frozenset[int]]) -> list[frozenset[int]]:
    """Return cliques sorted by size then by members for deterministic output."""
    return sorted(cliques, key=lambda c: (len(c), sorted(c)))


def bron_kerbosch_simple(graph: Graph) -> list[frozenset[int]]:
    """Enumerate all maximal cliques with the basic Bron-Kerbosch algorithm.

    Explores every branch of the search tree without pruning.
    """
    cliques: list[frozenset[int]] = []

    def recurse(r: set[int], p: set[int], x: set[int]) -> None:
        # r: current clique, p: candidates, x: already-processed exclusions
        if not p and not x:
            cliques.append(frozenset(r))
            return
        for v in list(p):
            neighbours = graph.get(v, set())
            recurse(r | {v}, p & neighbours, x & neighbours)
            p = p - {v}
            x = x | {v}

    recurse(set(), set(graph), set())
    return _sort_cliques(cliques)


def bron_kerbosch_pivot(graph: Graph) -> list[frozenset[int]]:
    """Enumerate all maximal cliques with the pivot-based Bron-Kerbosch algorithm.

    At each call a *pivot* ``u`` is chosen from ``p | x`` and only vertices in
    ``p`` that are **not** neighbours of ``u`` are branched on. This avoids
    recursing into branches that cannot produce new maximal cliques. The pivot
    is picked greedily as the vertex with the most neighbours in ``p``, which
    maximises pruning.
    """
    cliques: list[frozenset[int]] = []

    def recurse(r: set[int], p: set[int], x: set[int]) -> None:
        if not p and not x:
            cliques.append(frozenset(r))
            return
        # p | x is guaranteed non-empty here (otherwise we would have returned).
        pivot = max(p | x, key=lambda v: len(graph.get(v, set()) & p))
        # Only branch on candidates that are not neighbours of the pivot.
        for v in list(p - graph.get(pivot, set())):
            neighbours = graph.get(v, set())
            recurse(r | {v}, p & neighbours, x & neighbours)
            p = p - {v}
            x = x | {v}

    recurse(set(), set(graph), set())
    return _sort_cliques(cliques)


def main() -> None:
    """Run both variants on a sample graph and compare the results."""
    # A 6-vertex graph used for a concrete, hand-checkable example.
    graph: Graph = {
        1: {2, 5},
        2: {1, 3, 5},
        3: {2, 4},
        4: {3, 5, 6},
        5: {1, 2, 4},
        6: {4},
    }

    simple = bron_kerbosch_simple(graph)
    pivot = bron_kerbosch_pivot(graph)

    print("graph: ", {k: sorted(v) for k, v in sorted(graph.items())})
    print(f"simple: {len(simple)} maximal cliques")
    for clique in simple:
        print("  ", sorted(clique))
    print(f"pivot:  {len(pivot)} maximal cliques")
    for clique in pivot:
        print("  ", sorted(clique))
    print("match: ", simple == pivot)


if __name__ == "__main__":
    main()
