"""Tests for the Eppstein-Löffler-Strash maximal clique enumeration."""

from __future__ import annotations

import random

from parallel_processing.cliques import cliques
from parallel_processing.eppstein import (
    Graph,
    count_eppstein_cliques,
    degeneracy_ordering,
    eppstein_cliques,
)


def complete_graph(n: int) -> Graph:
    return {v: {w for w in range(n) if w != v} for v in range(n)}


def random_graph(n: int, p: float, seed: int) -> Graph:
    rng = random.Random(seed)
    graph: Graph = {v: set() for v in range(n)}
    for u in range(n):
        for v in range(u + 1, n):
            if rng.random() < p:
                graph[u].add(v)
                graph[v].add(u)
    return graph


class TestDegeneracyOrdering:
    def test_complete_graph_has_degeneracy_n_minus_1(self) -> None:
        _, d = degeneracy_ordering(complete_graph(5))
        assert d == 4

    def test_tree_has_degeneracy_1(self) -> None:
        # A path on 5 vertices.
        graph: Graph = {0: {1}, 1: {0, 2}, 2: {1, 3}, 3: {2, 4}, 4: {3}}
        _, d = degeneracy_ordering(graph)
        assert d == 1

    def test_cycle_has_degeneracy_2(self) -> None:
        graph: Graph = {v: {(v - 1) % 6, (v + 1) % 6} for v in range(6)}
        _, d = degeneracy_ordering(graph)
        assert d == 2

    def test_every_vertex_has_at_most_d_later_neighbours(self) -> None:
        graph = random_graph(40, 0.3, seed=7)
        ordering, d = degeneracy_ordering(graph)
        position = {v: i for i, v in enumerate(ordering)}
        for v in graph:
            later = sum(1 for w in graph[v] if position[w] > position[v])
            assert later <= d

    def test_ordering_is_a_permutation_of_the_vertices(self) -> None:
        graph = random_graph(30, 0.2, seed=3)
        ordering, _ = degeneracy_ordering(graph)
        assert sorted(ordering) == sorted(graph)

    def test_empty_graph(self) -> None:
        ordering, d = degeneracy_ordering({})
        assert ordering == []
        assert d == 0


class TestEppsteinCliques:
    def test_sample_graph_matches_known_cliques(self) -> None:
        graph: Graph = {
            1: {2, 5},
            2: {1, 3, 5},
            3: {2, 4},
            4: {3, 5, 6},
            5: {1, 2, 4},
            6: {4},
        }
        assert eppstein_cliques(graph) == [
            frozenset({2, 3}),
            frozenset({3, 4}),
            frozenset({4, 5}),
            frozenset({4, 6}),
            frozenset({1, 2, 5}),
        ]

    def test_isolated_vertex_is_its_own_maximal_clique(self) -> None:
        graph: Graph = {0: set(), 1: {2}, 2: {1}}
        assert eppstein_cliques(graph) == [frozenset({0}), frozenset({1, 2})]

    def test_complete_graph_is_a_single_clique(self) -> None:
        assert eppstein_cliques(complete_graph(6)) == [frozenset(range(6))]

    def test_matches_tomita_cliques_on_random_graphs(self) -> None:
        for seed in range(10):
            graph = random_graph(30, 0.4, seed=seed)
            assert eppstein_cliques(graph) == cliques(graph)


class TestCountEppsteinCliques:
    def test_count_matches_materialised_result(self) -> None:
        graph = random_graph(40, 0.3, seed=1)
        found = eppstein_cliques(graph)
        count, largest = count_eppstein_cliques(graph)
        assert count == len(found)
        assert largest == max(len(c) for c in found)

    def test_empty_graph(self) -> None:
        assert count_eppstein_cliques({}) == (0, 0)
