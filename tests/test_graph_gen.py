"""Tests for the synthetic graph generators."""

from __future__ import annotations

from parallel_processing.cliques import count_cliques
from parallel_processing.eppstein import (
    Graph,
    count_eppstein_cliques,
    degeneracy_ordering,
)
from parallel_processing.graph_gen import (
    barabasi_albert,
    dense_random,
    erdos_renyi,
    grid_2d,
    moon_moser,
    random_tree,
)


def assert_undirected(graph: Graph) -> None:
    for v, neighbours in graph.items():
        assert v not in neighbours
        for w in neighbours:
            assert v in graph[w]


class TestGenerators:
    def test_random_tree(self) -> None:
        graph = random_tree(50, seed=1)
        assert_undirected(graph)
        assert sum(len(nb) for nb in graph.values()) // 2 == 49
        _, d = degeneracy_ordering(graph)
        assert d == 1

    def test_grid_is_triangle_free(self) -> None:
        graph = grid_2d(5, 7)
        assert_undirected(graph)
        # Every maximal clique of a triangle-free graph with edges is an edge.
        count, largest = count_eppstein_cliques(graph)
        assert largest == 2
        assert count == sum(len(nb) for nb in graph.values()) // 2

    def test_erdos_renyi_edge_count(self) -> None:
        graph = erdos_renyi(200, 6, seed=2)
        assert_undirected(graph)
        assert sum(len(nb) for nb in graph.values()) // 2 == 600

    def test_dense_random(self) -> None:
        assert_undirected(dense_random(40, 0.5, seed=3))

    def test_barabasi_albert_degrees(self) -> None:
        graph = barabasi_albert(300, 4, seed=4)
        assert_undirected(graph)
        assert all(len(graph[v]) >= 4 for v in graph)

    def test_moon_moser_clique_count(self) -> None:
        graph = moon_moser(4)
        assert_undirected(graph)
        count, largest = count_eppstein_cliques(graph)
        assert (count, largest) == (81, 4)

    def test_generators_are_deterministic(self) -> None:
        assert erdos_renyi(100, 5, seed=9) == erdos_renyi(100, 5, seed=9)
        assert barabasi_albert(100, 3, seed=9) == barabasi_albert(100, 3, seed=9)

    def test_tomita_and_eppstein_agree_on_each_family(self) -> None:
        for graph in [
            random_tree(60, seed=5),
            grid_2d(6, 6),
            erdos_renyi(80, 6, seed=5),
            dense_random(30, 0.5, seed=5),
            barabasi_albert(80, 3, seed=5),
            moon_moser(3),
        ]:
            assert count_eppstein_cliques(graph) == count_cliques(graph)
