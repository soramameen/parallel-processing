"""Tests for the naive parallel Eppstein enumeration."""

from __future__ import annotations

import random

from parallel_processing.eppstein import Graph, count_eppstein_cliques
from parallel_processing.eppstein_parallel import count_eppstein_cliques_parallel


def random_graph(n: int, p: float, seed: int) -> Graph:
    rng = random.Random(seed)
    graph: Graph = {v: set() for v in range(n)}
    for u in range(n):
        for v in range(u + 1, n):
            if rng.random() < p:
                graph[u].add(v)
                graph[v].add(u)
    return graph


class TestCountEppsteinCliquesParallel:
    def test_matches_sequential_on_random_graph(self) -> None:
        graph = random_graph(60, 0.3, seed=5)
        assert count_eppstein_cliques_parallel(graph, workers=2) == (
            count_eppstein_cliques(graph)
        )

    def test_isolated_vertices_and_small_graph(self) -> None:
        graph: Graph = {0: set(), 1: {2}, 2: {1}}
        assert count_eppstein_cliques_parallel(graph, workers=2) == (2, 2)
