"""Tomita's CLIQUES algorithm for enumerating all maximal cliques.

Implements *Algorithm 1: CLIQUES* from Conte & Tomita, "On the overall and
delay complexity of the CLIQUES and Bron-Kerbosch algorithms" (TCS 2022),
faithfully to the paper's pseudocode. The pivot selection makes it
worst-case optimal (``O(3^{n/3})``).

Terminology follows the paper rather than the ``r/p/x`` naming used in
:mod:`parallel_processing.bron_kerbosch`:

- ``SUBG`` — the set of vertices to expand (initially ``V``).
- ``CAND`` — the not-yet-processed candidates (initially ``V``).
- ``FINI`` — the already-processed vertices, i.e. ``SUBG \\ CAND``.
- ``Q`` — the clique currently being built.

The result matches :func:`parallel_processing.bron_kerbosch.bron_kerbosch_pivot`
exactly (same clique set, same sort order), so the two can be cross-checked.

Run as a module to see it applied to a sample graph::

    python -m parallel_processing.cliques
"""

from __future__ import annotations

import sys

# A vertex to its set of neighbours. The graph is treated as undirected,
# so every edge ``{u, v}`` must appear as ``v in graph[u]`` and ``u in graph[v]``.
Graph = dict[int, set[int]]


def _sort_cliques(cliques: list[frozenset[int]]) -> list[frozenset[int]]:
    """Return cliques sorted by size then by members for deterministic output.

    Kept identical to :func:`parallel_processing.bron_kerbosch._sort_cliques`
    so the two implementations can be compared directly.
    """
    return sorted(cliques, key=lambda c: (len(c), sorted(c)))


def cliques(graph: Graph) -> list[frozenset[int]]:
    """Enumerate all maximal cliques with Tomita's CLIQUES algorithm.

    ``graph`` is an undirected graph as ``dict[int, set[int]]``. Returns the
    list of maximal cliques as ``frozenset``\\ s, sorted by size then members.

    The recursion depth is bounded by the size of the largest clique (shallow
    in practice), but ``sys.setrecursionlimit`` is raised as a safety margin.
    """
    result: list[frozenset[int]] = []
    q: list[int] = []

    # SUBG = ∅ implies Q is maximal; depth is bounded by the max clique size
    # (e.g. 57 for ca-AstroPh), so this limit is generous.
    sys.setrecursionlimit(max(sys.getrecursionlimit(), len(graph) + 1000))

    def expand(subg: set[int], cand: set[int]) -> None:
        if not subg:
            # SUBG is empty: Q is a maximal clique.
            result.append(frozenset(q))
            return
        # Pivot u ∈ SUBG maximising |CAND ∩ Γ(u)| (paper p.3); branching only
        # on CAND \ Γ(u) keeps the algorithm worst-case optimal.
        pivot = max(subg, key=lambda u: len(cand & graph.get(u, set())))
        ext = cand - graph.get(pivot, set())
        for p in list(ext):
            neighbours = graph.get(p, set())
            q.append(p)
            expand(subg & neighbours, cand & neighbours)
            q.pop()
            # Move p from CAND into FINI (SUBG \ CAND) for the next iterations.
            cand = cand - {p}

    expand(set(graph), set(graph))
    return _sort_cliques(result)


def main() -> None:
    """Run CLIQUES on a sample graph and print the maximal cliques."""
    # The same 6-vertex graph used by bron_kerbosch.main for a concrete example.
    graph: Graph = {
        1: {2, 5},
        2: {1, 3, 5},
        3: {2, 4},
        4: {3, 5, 6},
        5: {1, 2, 4},
        6: {4},
    }

    found = cliques(graph)
    print("graph: ", {k: sorted(v) for k, v in sorted(graph.items())})
    print(f"cliques: {len(found)} maximal cliques")
    for clique in found:
        print("  ", sorted(clique))


if __name__ == "__main__":
    main()
