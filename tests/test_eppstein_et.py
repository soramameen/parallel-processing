"""Tests for Eppstein with clique early termination."""

from __future__ import annotations

import pytest
from test_eppstein import complete_graph, random_graph

from parallel_processing.eppstein import (
    Graph,
    count_eppstein_cliques,
    eppstein_cliques,
)
from parallel_processing.eppstein_et import (
    count_eppstein_cliques_et,
    eppstein_cliques_et,
)
from parallel_processing.graph_gen import moon_moser


def clique_with_pendants(k: int, extra: int) -> Graph:
    """A k-clique whose last vertex also sees ``extra`` outside vertices, the
    shape of ca-HepPh's heavy vertex (P a clique, X not dominating it)."""
    graph = complete_graph(k)
    for j in range(extra):
        v = k + j
        graph[v] = {k - 1}
        graph[k - 1].add(v)
    return graph


class TestEarlyTermination:
    @pytest.mark.parametrize("seed", range(12))
    @pytest.mark.parametrize("p", [0.1, 0.3, 0.6, 0.9])
    def test_matches_plain_eppstein_on_random_graphs(self, seed: int, p: float) -> None:
        graph = random_graph(40, p, seed)
        assert eppstein_cliques_et(graph) == eppstein_cliques(graph)

    def test_complete_graph_is_one_clique(self) -> None:
        assert count_eppstein_cliques_et(complete_graph(30)) == (1, 30)

    def test_clique_with_pendants(self) -> None:
        graph = clique_with_pendants(20, 5)
        assert eppstein_cliques_et(graph) == eppstein_cliques(graph)

    def test_dominating_x_rejects_the_candidate(self) -> None:
        # Two triangles sharing an edge (a diamond): {0,1,2} and {1,2,3}.
        graph: Graph = {0: {1, 2}, 1: {0, 2, 3}, 2: {0, 1, 3}, 3: {1, 2}}
        assert eppstein_cliques_et(graph) == eppstein_cliques(graph)

    def test_moon_moser_counts(self) -> None:
        graph = moon_moser(7)
        assert count_eppstein_cliques_et(graph) == count_eppstein_cliques(graph)

    def test_isolated_and_empty(self) -> None:
        assert count_eppstein_cliques_et({}) == (0, 0)
        assert count_eppstein_cliques_et({0: set(), 1: set()}) == (2, 1)

    def test_subproblems_sum_to_the_total(self) -> None:
        from parallel_processing.eppstein import degeneracy_ordering
        from parallel_processing.eppstein_et import count_subproblem_et

        graph = clique_with_pendants(15, 4) | {
            v + 100: {w + 100 for w in nbrs}
            for v, nbrs in random_graph(30, 0.3, 2).items()
        }
        ordering, _ = degeneracy_ordering(graph)
        position = {v: i for i, v in enumerate(ordering)}
        total = sum(
            count_subproblem_et(
                graph,
                {w for w in graph[v] if position[w] > i},
                {w for w in graph[v] if position[w] < i},
            )
            for i, v in enumerate(ordering)
        )
        assert total == count_eppstein_cliques(graph)[0]

    @pytest.mark.parametrize("seed", range(6))
    def test_root_only_matches(self, seed: int) -> None:
        shifted = random_graph(40, 0.5, seed).items()
        graph = clique_with_pendants(12, 3) | {
            v + 100: {w + 100 for w in nbrs} for v, nbrs in shifted
        }
        expected = count_eppstein_cliques(graph)
        assert count_eppstein_cliques_et(graph, deep=False) == expected
