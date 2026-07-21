"""Tests for the per-vertex workload profiler."""

from __future__ import annotations

import random

from parallel_processing.eppstein import Graph, count_eppstein_cliques
from parallel_processing.workload_profile import profile


def random_graph(n: int, p: float, seed: int) -> Graph:
    rng = random.Random(seed)
    graph: Graph = {v: set() for v in range(n)}
    for u in range(n):
        for v in range(u + 1, n):
            if rng.random() < p:
                graph[u].add(v)
                graph[v].add(u)
    return graph


class TestProfile:
    def test_per_vertex_cliques_sum_to_total(self) -> None:
        graph = random_graph(60, 0.3, seed=8)
        rows = profile(graph)
        count, _ = count_eppstein_cliques(graph)
        assert sum(r[4] for r in rows) == count
        assert len(rows) == len(graph)

    def test_rows_cover_every_vertex_once(self) -> None:
        graph = random_graph(40, 0.2, seed=2)
        rows = profile(graph)
        assert sorted(r[1] for r in rows) == sorted(graph)
