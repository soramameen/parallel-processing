"""Eppstein-Löffler-Strash algorithm for enumerating all maximal cliques.

Implements *BronKerboschDegeneracy* from Eppstein, Löffler & Strash,
"Listing All Maximal Cliques in Sparse Graphs in Near-Optimal Time"
(ISAAC 2010, arXiv:1006.5440) and its experimental companion Eppstein &
Strash, "Listing All Maximal Cliques in Large Sparse Real-World Graphs"
(SEA 2011, arXiv:1103.0318), faithfully to the papers' pseudocode:

- The outermost level iterates over the vertices in a *degeneracy
  ordering*; each vertex ``v_i`` spawns an independent subproblem with
  ``P = Γ(v_i) ∩ {v_{i+1}, …}`` and ``X = Γ(v_i) ∩ {v_0, …, v_{i-1}}``.
- Inner levels are Bron-Kerbosch with the Tomita-style pivot chosen from
  ``P ∪ X`` maximising ``|P ∩ Γ(u)|``.

This bounds the running time by ``O(d·n·3^{d/3})`` where ``d`` is the
degeneracy of the graph, near-optimal by the papers' ``(n−d)·3^{d/3}``
bound on the number of maximal cliques.

The result matches :func:`parallel_processing.cliques.cliques` exactly
(same clique set, same sort order), so the two can be cross-checked.

Run as a module to see it applied to a sample graph::

    python -m parallel_processing.eppstein
"""

from __future__ import annotations

import sys
from collections.abc import Callable

# A vertex to its set of neighbours; matches parallel_processing.cliques.Graph.
Graph = dict[int, set[int]]


def degeneracy_ordering(graph: Graph) -> tuple[list[int], int]:
    """Return a degeneracy ordering of ``graph`` and its degeneracy ``d``.

    Repeatedly removes a minimum-degree vertex (Matula & Beck 1983, the
    procedure both papers cite); the removal order is the ordering, and the
    largest degree seen at removal time is the degeneracy. Every vertex has
    at most ``d`` neighbours *later* in the ordering.

    Uses bucket queues for the papers' O(n + m) bound; a heap would add a
    log factor and lazy-deletion bookkeeping for the same result.
    """
    degree = {v: len(neighbours) for v, neighbours in graph.items()}
    max_degree = max(degree.values(), default=0)
    buckets: list[set[int]] = [set() for _ in range(max_degree + 1)]
    for v, deg in degree.items():
        buckets[deg].add(v)

    ordering: list[int] = []
    removed: set[int] = set()
    degeneracy = 0
    # The minimum degree drops by at most 1 per removal, so restarting the
    # scan from one below the previous minimum keeps the total scan linear.
    scan_from = 0
    for _ in range(len(graph)):
        deg = scan_from
        while not buckets[deg]:
            deg += 1
        v = buckets[deg].pop()
        degeneracy = max(degeneracy, deg)
        ordering.append(v)
        removed.add(v)
        for w in graph[v]:
            if w in removed:
                continue
            buckets[degree[w]].discard(w)
            degree[w] -= 1
            buckets[degree[w]].add(w)
        scan_from = max(deg - 1, 0)
    return ordering, degeneracy


def _sort_cliques(cliques: list[frozenset[int]]) -> list[frozenset[int]]:
    """Return cliques sorted by size then by members for deterministic output.

    Kept identical to :func:`parallel_processing.cliques._sort_cliques`
    so the two implementations can be compared directly.
    """
    return sorted(cliques, key=lambda c: (len(c), sorted(c)))


def eppstein_cliques(graph: Graph) -> list[frozenset[int]]:
    """Enumerate all maximal cliques with the Eppstein-Löffler-Strash algorithm.

    ``graph`` is an undirected graph as ``dict[int, set[int]]``. Returns the
    list of maximal cliques as ``frozenset``\\ s, sorted by size then members.

    The recursion depth is bounded by the degeneracy ``d`` plus one (each
    inner ``P`` starts with at most ``d`` vertices), so the default limit is
    ample; it is still raised as a safety margin for consistency with
    :mod:`parallel_processing.cliques`.
    """
    result: list[frozenset[int]] = []

    def report(q: list[int]) -> None:
        result.append(frozenset(q))

    _bron_kerbosch_degeneracy(graph, report)
    return _sort_cliques(result)


def count_eppstein_cliques(graph: Graph) -> tuple[int, int]:
    """Count maximal cliques without materialising them; return (count, largest).

    Same search as :func:`eppstein_cliques` but never builds
    ``frozenset``\\ s nor a result list, so it stays O(1) in output memory —
    required for graphs with tens of millions of maximal cliques.
    """
    count = 0
    largest = 0

    def report(q: list[int]) -> None:
        nonlocal count, largest
        count += 1
        if len(q) > largest:
            largest = len(q)

    _bron_kerbosch_degeneracy(graph, report)
    return count, largest


def _bron_kerbosch_degeneracy(
    graph: Graph, report: Callable[[list[int]], None]
) -> None:
    """Run BronKerboschDegeneracy, calling ``report(R)`` per maximal clique.

    ``report`` receives the clique as the shared working list ``r``; it must
    copy the contents if it keeps them (both callers above do).
    """
    sys.setrecursionlimit(max(sys.getrecursionlimit(), len(graph) + 1000))

    r: list[int] = []

    def bron_kerbosch_pivot(p: set[int], x: set[int]) -> None:
        if not p and not x:
            # P ∪ X is empty: R is a maximal clique.
            report(r)
            return
        # Pivot u ∈ P ∪ X maximising |P ∩ Γ(u)| (Tomita-style; both papers
        # use this choice for the 3^{d/3} inner bound).
        pivot = max(p | x, key=lambda u: len(p & graph[u]))
        for v in list(p - graph[pivot]):
            neighbours = graph[v]
            r.append(v)
            bron_kerbosch_pivot(p & neighbours, x & neighbours)
            r.pop()
            # Move v from P to X for the remaining iterations.
            p.discard(v)
            x.add(v)

    ordering, _ = degeneracy_ordering(graph)
    # position[v] < position[w] iff v comes before w in the ordering; the
    # split below is the papers' "later neighbours into P, earlier into X".
    position = {v: i for i, v in enumerate(ordering)}
    for v in ordering:
        pos = position[v]
        p = {w for w in graph[v] if position[w] > pos}
        x = {w for w in graph[v] if position[w] < pos}
        r.append(v)
        bron_kerbosch_pivot(p, x)
        r.pop()


def main() -> None:
    """Run the algorithm on a sample graph and print the maximal cliques."""
    # The same 6-vertex graph used by cliques.main for a concrete example.
    graph: Graph = {
        1: {2, 5},
        2: {1, 3, 5},
        3: {2, 4},
        4: {3, 5, 6},
        5: {1, 2, 4},
        6: {4},
    }

    ordering, degeneracy = degeneracy_ordering(graph)
    found = eppstein_cliques(graph)
    print("graph: ", {k: sorted(v) for k, v in sorted(graph.items())})
    print(f"degeneracy: {degeneracy} (ordering: {ordering})")
    print(f"cliques: {len(found)} maximal cliques")
    for clique in found:
        print("  ", sorted(clique))


if __name__ == "__main__":
    main()
