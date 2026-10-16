"""Tsukiyama et al.'s algorithm for enumerating all maximal cliques.

Implements the algorithm from Tsukiyama, Ide, Ariyoshi & Shirakawa,
"A New Algorithm for Generating All the Maximal Independent Sets"
(SIAM J. Comput., Vol. 6, No. 3, 1977).

The original paper describes an algorithm for maximal independent sets.
To enumerate maximal cliques, we apply it to the complement graph:
a maximal independent set in the complement is a maximal clique in the original.

This algorithm is expected to be significantly slower than modern pivot-based
algorithms (Tomita/CLIQUES, Eppstein-Löffler-Strash) because it lacks the
sophisticated pruning strategies introduced later.

Run as a module to see it applied to a sample graph::

    python -m parallel_processing.tsukiyama
"""

from __future__ import annotations

import sys

# A vertex to its set of neighbours; matches parallel_processing.cliques.Graph.
Graph = dict[int, set[int]]


def _sort_cliques(cliques: list[frozenset[int]]) -> list[frozenset[int]]:
    """Return cliques sorted by size then by members for deterministic output.

    Kept identical to :func:`parallel_processing.cliques._sort_cliques`
    so the implementations can be compared directly.
    """
    return sorted(cliques, key=lambda c: (len(c), sorted(c)))


def _complement_graph(graph: Graph) -> Graph:
    """Return the complement of ``graph``.

    In the complement, vertices are connected if and only if they are **not**
    connected in the original graph (excluding self-loops).
    """
    vertices = set(graph.keys())
    complement: Graph = {v: set() for v in vertices}
    for v in vertices:
        # Neighbours in complement = all vertices except v and its original neighbours
        complement[v] = vertices - {v} - graph.get(v, set())
    return complement


def tsukiyama_cliques(graph: Graph) -> list[frozenset[int]]:
    """Enumerate all maximal cliques with Tsukiyama et al.'s algorithm.

    ``graph`` is an undirected graph as ``dict[int, set[int]]``. Returns the
    list of maximal cliques as ``frozenset``\\s, sorted by size then members.

    The algorithm works by finding maximal independent sets in the complement
    graph, since a maximal independent set in complement(G) corresponds to a
    maximal clique in G.

    Implementation note (未確認): The original paper's algorithm for maximal
    independent sets is described in terms of a "family generation tree" with
    specific ordering and pruning rules. This implementation follows a simpler
    recursive backtracking approach that enumerates maximal independent sets
    without the specific optimizations of the original paper. It is expected
    to be significantly slower than modern pivot-based algorithms.
    """
    # Work on the complement graph to find maximal independent sets
    comp = _complement_graph(graph)
    vertices = sorted(graph.keys())

    result: list[frozenset[int]] = []
    sys.setrecursionlimit(max(sys.getrecursionlimit(), len(graph) + 1000))

    def generate(
        current: list[int], candidates: list[int], position: int
    ) -> None:
        """Recursively generate maximal independent sets in the complement graph.

        current: vertices in the current independent set
        candidates: ordered list of vertices to consider
        position: current position in the candidates list
        """
        # Try to extend current with remaining candidates
        extendable = False
        for i in range(position, len(candidates)):
            v = candidates[i]
            # Check if v is independent from all vertices in current
            # (no edge in complement means v is not adjacent to any vertex in current)
            v_neighbours_comp = comp.get(v, set())
            if all(u not in v_neighbours_comp for u in current):
                # v can be added to current
                extendable = True
                current.append(v)
                generate(current, candidates, i + 1)
                current.pop()

        # If current cannot be extended with remaining candidates,
        # check if it's truly maximal (cannot be extended with ANY vertex)
        if not extendable and current:  # Don't output empty set
            # Check all candidates (not just remaining) to ensure maximality
            is_maximal = True
            for v in vertices:
                if v not in current:
                    v_neighbours_comp = comp.get(v, set())
                    if all(u not in v_neighbours_comp for u in current):
                        is_maximal = False
                        break
            if is_maximal:
                result.append(frozenset(current))

    generate([], vertices, 0)
    return _sort_cliques(result)


def count_tsukiyama_cliques(graph: Graph) -> tuple[int, int, int]:
    """Count maximal cliques without materialising them; return (count, largest, calls).

    Same search as :func:`tsukiyama_cliques` but counts recursive calls
    for performance analysis.
    """
    comp = _complement_graph(graph)
    vertices = sorted(graph.keys())

    count = 0
    largest = 0
    recursive_calls = 0

    sys.setrecursionlimit(max(sys.getrecursionlimit(), len(graph) + 1000))

    def generate(
        current: list[int], candidates: list[int], position: int
    ) -> None:
        nonlocal count, largest, recursive_calls
        recursive_calls += 1

        extendable = False
        for i in range(position, len(candidates)):
            v = candidates[i]
            v_neighbours_comp = comp.get(v, set())
            if all(u not in v_neighbours_comp for u in current):
                extendable = True
                current.append(v)
                generate(current, candidates, i + 1)
                current.pop()

        if not extendable and current:
            is_maximal = True
            for v in vertices:
                if v not in current:
                    v_neighbours_comp = comp.get(v, set())
                    if all(u not in v_neighbours_comp for u in current):
                        is_maximal = False
                        break
            if is_maximal:
                count += 1
                if len(current) > largest:
                    largest = len(current)

    generate([], vertices, 0)
    return count, largest, recursive_calls


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

    found = tsukiyama_cliques(graph)
    print("graph: ", {k: sorted(v) for k, v in sorted(graph.items())})
    print(f"tsukiyama: {len(found)} maximal cliques")
    for clique in found:
        print("  ", sorted(clique))


if __name__ == "__main__":
    main()
