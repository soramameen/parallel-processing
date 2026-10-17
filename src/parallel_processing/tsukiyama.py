"""Tsukiyama et al.'s algorithm for enumerating all maximal cliques.

Clique formulation of the vertex-incremental generator of Tsukiyama, Ide,
Ariyoshi and Shirakawa, "A New Algorithm for Generating All the Maximal
Independent Sets", SIAM J. Comput. 6(3), 1977, pp. 505–517.

The 1977 paper generates maximal independent sets. This module implements
the equivalent clique recursion given by Chiba and Nishizeki, "Arboricity
and Subgraph Listing Algorithms", SIAM J. Comput. 14(1), 1985, pp. 210–223,
Section 6, procedure ``CLIQUE`` / ``UPDATE``. They state that the method is
the clique analogue of Tsukiyama et al.: from each maximal clique ``C`` of
``G_{i-1} = G[{v_1, ..., v_{i-1}}]`` one builds the maximal cliques of
``G_i`` by

1. keeping ``C`` when ``C \\ N(v_i)`` is nonempty (``v_i`` does not extend
   ``C``, so ``C`` stays maximal in ``G_i``);
2. emitting ``C' = (C ∩ N(v_i)) ∪ {v_i}`` only when ``C'`` is maximal in
   ``G_i`` (maximality test) and ``C`` is the lexicographically largest
   clique of ``G_{i-1}`` that contains ``C ∩ N(v_i)`` (lexicographic /
   parent-uniqueness test).

Every call of ``UPDATE`` has at least one child, the recursion has depth
``n``, and each output is produced by exactly one root-to-leaf path. The
number of generation-tree nodes is therefore at most ``(n + 1)`` times the
number of maximal cliques. Chiba and Nishizeki show that one step can be
implemented in ``O(m)`` time, hence ``O(nm)`` time per output; the tests
below are the direct checks of their Lemmas 4 and 5, not the arboricity
speedup.

Vertex order is increasing label. Any order is correct. Chiba and Nishizeki
sort by nondecreasing degree only to replace ``n`` by the arboricity in the
time bound.

Run as a module::

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


def _prepare(graph: Graph) -> tuple[list[int], list[int]]:
    """Return ``(vertices, adj_masks)`` with vertices in increasing label order.

    ``adj_masks[i]`` is a bitset of the neighbours of ``vertices[i]``, using
    the same index space. Bits are only a compact adjacency matrix; the
    search itself is the Chiba–Nishizeki recursion.
    """
    vertices = sorted(graph.keys())
    index = {v: i for i, v in enumerate(vertices)}
    adj_masks = [0] * len(vertices)
    for v, neighbours in graph.items():
        mask = 0
        iv = index[v]
        for u in neighbours:
            if u == v:
                continue
            mask |= 1 << index[u]
        adj_masks[iv] = mask
    return vertices, adj_masks


def _run(graph: Graph, *, collect: bool) -> list[frozenset[int]] | tuple[int, int, int]:
    """Run UPDATE. Collect cliques, or return ``(count, largest, nodes)``."""
    vertices, adj = _prepare(graph)
    n = len(vertices)
    sys.setrecursionlimit(max(sys.getrecursionlimit(), n + 50))

    nodes = 0
    count = 0
    largest = 0
    found: list[frozenset[int]] = []

    def mask_to_clique(mask: int) -> frozenset[int]:
        members: list[int] = []
        while mask:
            bit = mask & -mask
            members.append(vertices[bit.bit_length() - 1])
            mask ^= bit
        return frozenset(members)

    def extends(mask: int, limit: int) -> bool:
        """True iff some vertex of index ``< limit`` outside ``mask`` extends it."""
        candidates = ((1 << limit) - 1) & ~mask
        while candidates:
            bit = candidates & -candidates
            y = bit.bit_length() - 1
            candidates ^= bit
            if adj[y] & mask == mask:
                return True
        return False

    def lex_largest(c_mask: int, co_mask: int, i: int) -> bool:
        """True iff ``C`` is the lex-largest clique of ``G_{i-1}`` containing ``Co``.

        Lexicographic order prefers the larger vertex index, as in the proof
        of Chiba and Nishizeki's Lemma 5: ``C'`` is larger than ``C`` when
        the largest vertex of the symmetric difference lies in ``C'``. The
        proof says this happens exactly when some ``y ∉ C`` is adjacent to
        every vertex of ``Co ∪ {u ∈ C | u > y}``.
        """
        if c_mask == co_mask:
            # C itself is the unique clique of G_{i-1} that contains C.
            return True
        candidates = ((1 << i) - 1) & ~c_mask
        while candidates:
            bit = candidates & -candidates
            y = bit.bit_length() - 1
            candidates ^= bit
            higher = c_mask & ~((1 << (y + 1)) - 1)
            need = co_mask | higher
            if adj[y] & need == need:
                return False
        return True

    def update(i: int, c_mask: int) -> None:
        """Chiba–Nishizeki ``UPDATE(i, C)``; ``i`` is the next vertex index."""
        nonlocal nodes, count, largest
        nodes += 1
        if i == n:
            count += 1
            size = c_mask.bit_count()
            if size > largest:
                largest = size
            if collect:
                found.append(mask_to_clique(c_mask))
            return

        children = 0
        # (1) C stays maximal in G_i when v_i misses some vertex of C.
        if c_mask & ~adj[i]:
            children += 1
            update(i + 1, c_mask)

        # (2) C' = (C ∩ N(v_i)) ∪ {v_i}, kept only by the two tests.
        co_mask = c_mask & adj[i]
        cp_mask = co_mask | (1 << i)
        if not extends(cp_mask, i + 1) and lex_largest(c_mask, co_mask, i):
            children += 1
            update(i + 1, cp_mask)

        if children == 0:
            raise RuntimeError(
                "Tsukiyama generation tree has a dead-end; "
                "every UPDATE must reach an output"
            )

    update(0, 0)
    if collect:
        return _sort_cliques(found)
    return count, largest, nodes


def tsukiyama_cliques(graph: Graph) -> list[frozenset[int]]:
    """Enumerate all maximal cliques; sorted by size, then by members."""
    found = _run(graph, collect=True)
    assert isinstance(found, list)
    return found


def count_tsukiyama_cliques(graph: Graph) -> tuple[int, int, int]:
    """Return ``(count, largest, nodes)`` without storing the cliques.

    ``nodes`` is the number of calls of ``UPDATE``, including the leaves
    that output a clique. For this algorithm ``nodes <= (n + 1) * count``.
    """
    counted = _run(graph, collect=False)
    assert isinstance(counted, tuple)
    return counted


def main() -> None:
    """Run the algorithm on a sample graph and print the maximal cliques."""
    graph: Graph = {
        1: {2, 5},
        2: {1, 3, 5},
        3: {2, 4},
        4: {3, 5, 6},
        5: {1, 2, 4},
        6: {4},
    }

    found = tsukiyama_cliques(graph)
    count, largest, nodes = count_tsukiyama_cliques(graph)
    n = len(graph)
    print("graph: ", {k: sorted(v) for k, v in sorted(graph.items())})
    print(f"tsukiyama: {len(found)} maximal cliques")
    for clique in found:
        print("  ", sorted(clique))
    print(f"count: {count}, largest: {largest}, nodes: {nodes}")
    if count:
        print(f"nodes / (n * #cliques): {nodes / (n * count):.3f}")
        print(f"bound (n + 1) * #cliques: {(n + 1) * count}")


if __name__ == "__main__":
    main()
