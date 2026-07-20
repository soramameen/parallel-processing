"""Tests for the naive root-split parallel CLIQUES counter.

Cross-checks against the sequential ``count_cliques`` on the same graphs used
in ``test_cliques.py``, across a few worker counts, to make sure the root
split reproduces the sequential ``cand -= {p}`` sibling order exactly.
"""

import random

from parallel_processing.cliques import count_cliques
from parallel_processing.cliques_parallel import count_cliques_parallel_root

SAMPLE_GRAPH: dict[int, set[int]] = {
    1: {2, 5},
    2: {1, 3, 5},
    3: {2, 4},
    4: {3, 5, 6},
    5: {1, 2, 4},
    6: {4},
}


def test_parallel_matches_sequential_on_sample() -> None:
    """The root-split parallel counter agrees with the sequential one."""
    assert count_cliques_parallel_root(SAMPLE_GRAPH, workers=2) == count_cliques(
        SAMPLE_GRAPH
    )


def test_parallel_matches_sequential_on_random_graphs() -> None:
    """Parallel and sequential counters agree across random graphs and worker counts."""
    rng = random.Random(54321)
    for i in range(20):
        n = rng.randint(2, 10)
        graph: dict[int, set[int]] = {v: set() for v in range(n)}
        for a in range(n):
            for b in range(a + 1, n):
                if rng.random() < 0.4:
                    graph[a].add(b)
                    graph[b].add(a)
        workers = [1, 2, 4][i % 3]
        assert count_cliques_parallel_root(graph, workers=workers) == count_cliques(
            graph
        )


def test_isolated_vertex_is_a_clique() -> None:
    """A single isolated vertex is its own maximal clique."""
    assert count_cliques_parallel_root({0: set()}, workers=2) == (1, 1)


def test_empty_graph() -> None:
    """An empty graph has exactly one (empty) maximal clique."""
    assert count_cliques_parallel_root({}, workers=2) == (1, 0)
