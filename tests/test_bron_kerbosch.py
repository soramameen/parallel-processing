"""Tests for the Bron-Kerbosch implementations."""

import random

from parallel_processing.bron_kerbosch import (
    bron_kerbosch_pivot,
    bron_kerbosch_simple,
)

SAMPLE_GRAPH: dict[int, set[int]] = {
    1: {2, 5},
    2: {1, 3, 5},
    3: {2, 4},
    4: {3, 5, 6},
    5: {1, 2, 4},
    6: {4},
}

# Hand-computed maximal cliques of SAMPLE_GRAPH, ordered as the
# implementation returns them: by size then by members.
EXPECTED = [
    frozenset({2, 3}),
    frozenset({3, 4}),
    frozenset({4, 5}),
    frozenset({4, 6}),
    frozenset({1, 2, 5}),
]


def test_simple_returns_expected_cliques() -> None:
    """simple variant matches the hand-computed clique set."""
    assert bron_kerbosch_simple(SAMPLE_GRAPH) == EXPECTED


def test_pivot_returns_expected_cliques() -> None:
    """pivot variant matches the hand-computed clique set."""
    assert bron_kerbosch_pivot(SAMPLE_GRAPH) == EXPECTED


def test_simple_and_pivot_agree_on_random_graphs() -> None:
    """both variants enumerate the same cliques on random graphs."""
    rng = random.Random(12345)
    for _ in range(50):
        n = rng.randint(2, 8)
        graph: dict[int, set[int]] = {i: set() for i in range(n)}
        for i in range(n):
            for j in range(i + 1, n):
                if rng.random() < 0.4:
                    graph[i].add(j)
                    graph[j].add(i)
        assert bron_kerbosch_simple(graph) == bron_kerbosch_pivot(graph)


def test_isolated_vertex_is_a_clique() -> None:
    """a vertex with no edges is its own maximal clique."""
    assert bron_kerbosch_simple({0: set()}) == [frozenset({0})]
    assert bron_kerbosch_pivot({0: set()}) == [frozenset({0})]
