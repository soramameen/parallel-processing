"""Tests for Tomita's CLIQUES implementation.

Cross-checks the new CLIQUES against the reference ``bron_kerbosch_pivot``,
which is itself validated against ``bron_kerbosch_simple`` in
``test_bron_kerbosch.py``.
"""

import random

from parallel_processing.bron_kerbosch import bron_kerbosch_pivot
from parallel_processing.cliques import cliques

SAMPLE_GRAPH: dict[int, set[int]] = {
    1: {2, 5},
    2: {1, 3, 5},
    3: {2, 4},
    4: {3, 5, 6},
    5: {1, 2, 4},
    6: {4},
}

# Same hand-computed maximal cliques as test_bron_kerbosch.py, in the order
# the implementation returns them: by size then by members.
EXPECTED = [
    frozenset({2, 3}),
    frozenset({3, 4}),
    frozenset({4, 5}),
    frozenset({4, 6}),
    frozenset({1, 2, 5}),
]


def test_cliques_returns_expected_cliques() -> None:
    """CLIQUES matches the hand-computed clique set."""
    assert cliques(SAMPLE_GRAPH) == EXPECTED


def test_cliques_matches_pivot_on_sample() -> None:
    """CLIQUES agrees with bron_kerbosch_pivot on the sample graph."""
    assert cliques(SAMPLE_GRAPH) == bron_kerbosch_pivot(SAMPLE_GRAPH)


def test_cliques_matches_pivot_on_random_graphs() -> None:
    """CLIQUES and bron_kerbosch_pivot enumerate the same cliques."""
    rng = random.Random(12345)
    for _ in range(50):
        n = rng.randint(2, 8)
        graph: dict[int, set[int]] = {i: set() for i in range(n)}
        for i in range(n):
            for j in range(i + 1, n):
                if rng.random() < 0.4:
                    graph[i].add(j)
                    graph[j].add(i)
        assert cliques(graph) == bron_kerbosch_pivot(graph)


def test_isolated_vertex_is_a_clique() -> None:
    """a vertex with no edges is its own maximal clique."""
    assert cliques({0: set()}) == [frozenset({0})]


def test_isolated_vertex_alongside_edge() -> None:
    """an isolated vertex coexists with cliques from the rest of the graph."""
    graph: dict[int, set[int]] = {0: set(), 1: {2}, 2: {1}}
    assert cliques(graph) == [frozenset({0}), frozenset({1, 2})]
    assert cliques(graph) == bron_kerbosch_pivot(graph)
