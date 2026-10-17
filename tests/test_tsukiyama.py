"""Tests for Tsukiyama et al.'s maximal clique enumeration.

Cross-checks the Tsukiyama implementation against the validated reference
algorithms (bron_kerbosch_pivot, cliques, eppstein_cliques) and verifies
correctness on the H_k instances from the thesis.
"""

import random
from pathlib import Path

from parallel_processing.bron_kerbosch import bron_kerbosch_pivot
from parallel_processing.cliques import cliques
from parallel_processing.eppstein import eppstein_cliques
from parallel_processing.graph_io import load_dimacs
from parallel_processing.tsukiyama import count_tsukiyama_cliques, tsukiyama_cliques

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


def test_tsukiyama_returns_expected_cliques() -> None:
    """Tsukiyama matches the hand-computed clique set."""
    assert tsukiyama_cliques(SAMPLE_GRAPH) == EXPECTED


def test_tsukiyama_matches_pivot_on_sample() -> None:
    """Tsukiyama agrees with bron_kerbosch_pivot on the sample graph."""
    assert tsukiyama_cliques(SAMPLE_GRAPH) == bron_kerbosch_pivot(SAMPLE_GRAPH)


def test_tsukiyama_matches_cliques_on_sample() -> None:
    """Tsukiyama agrees with Tomita CLIQUES on the sample graph."""
    assert tsukiyama_cliques(SAMPLE_GRAPH) == cliques(SAMPLE_GRAPH)


def test_tsukiyama_matches_eppstein_on_sample() -> None:
    """Tsukiyama agrees with Eppstein on the sample graph."""
    assert tsukiyama_cliques(SAMPLE_GRAPH) == eppstein_cliques(SAMPLE_GRAPH)


def test_tsukiyama_matches_pivot_on_random_graphs() -> None:
    """Tsukiyama and bron_kerbosch_pivot enumerate the same cliques."""
    rng = random.Random(42)
    for _ in range(20):  # Fewer iterations since Tsukiyama is slower
        n = rng.randint(2, 7)  # Smaller graphs since Tsukiyama is slow
        graph: dict[int, set[int]] = {i: set() for i in range(n)}
        for i in range(n):
            for j in range(i + 1, n):
                if rng.random() < 0.4:
                    graph[i].add(j)
                    graph[j].add(i)
        assert tsukiyama_cliques(graph) == bron_kerbosch_pivot(graph)


def test_isolated_vertex_is_a_clique() -> None:
    """A vertex with no edges is its own maximal clique."""
    assert tsukiyama_cliques({0: set()}) == [frozenset({0})]


def test_isolated_vertex_alongside_edge() -> None:
    """An isolated vertex coexists with cliques from the rest of the graph."""
    graph: dict[int, set[int]] = {0: set(), 1: {2}, 2: {1}}
    assert tsukiyama_cliques(graph) == [frozenset({0}), frozenset({1, 2})]
    assert tsukiyama_cliques(graph) == bron_kerbosch_pivot(graph)


def test_count_tsukiyama_matches_tsukiyama_on_random_graphs() -> None:
    """count_tsukiyama_cliques returns the same count and largest size."""
    rng = random.Random(42)
    for _ in range(20):
        n = rng.randint(2, 7)
        graph: dict[int, set[int]] = {i: set() for i in range(n)}
        for i in range(n):
            for j in range(i + 1, n):
                if rng.random() < 0.4:
                    graph[i].add(j)
                    graph[j].add(i)
        enumerated = tsukiyama_cliques(graph)
        count, largest, _ = count_tsukiyama_cliques(graph)
        assert count == len(enumerated)
        assert largest == max((len(c) for c in enumerated), default=0)


def test_generation_tree_is_at_most_linear_in_n_times_cliques() -> None:
    """Every UPDATE reaches an output, so nodes <= (n + 1) * #cliques."""
    rng = random.Random(7)
    for _ in range(20):
        n = rng.randint(1, 8)
        graph: dict[int, set[int]] = {i: set() for i in range(n)}
        for i in range(n):
            for j in range(i + 1, n):
                if rng.random() < 0.5:
                    graph[i].add(j)
                    graph[j].add(i)
        count, _, nodes = count_tsukiyama_cliques(graph)
        assert nodes <= (n + 1) * count


# README of data/instances: maximal-clique counts, and the core M has size 2k.
_H_INSTANCES = [
    ("H1_n11.clq", 1, 17),
    ("H3_n45.clq", 3, 145),
    ("H5_n95.clq", 5, 481),
    ("H7_n161.clq", 7, 1121),
]


def test_h_instances_match_existing_algorithms() -> None:
    """H1..H7: same clique set as Tomita, and the core has size 2k."""
    for name, k, expected in _H_INSTANCES:
        path = Path("data/instances") / name
        if not path.exists():
            continue
        graph = load_dimacs(path)
        found = tsukiyama_cliques(graph)
        assert len(found) == expected
        assert found == cliques(graph)
        assert found == eppstein_cliques(graph)
        count, largest, nodes = count_tsukiyama_cliques(graph)
        assert count == expected
        assert largest == 2 * k
        assert nodes <= (len(graph) + 1) * count
