"""Tests for Phase 3 schedule construction."""

from __future__ import annotations

from collections import Counter

import pytest
from test_eppstein_parallel import random_graph

from parallel_processing import eppstein_parallel, hetero, hetero_phase3
from parallel_processing.eppstein import degeneracy_ordering

SCHEDULES = [
    "block", "block16", "interleave", "reversed", "lpt", "lpt-oracle", "static@0.43",
    "static-oracle@0.26", "giants", "split", "split-giants",
]


def _setup():  # type: ignore[no-untyped-def]
    graph = random_graph(120, 0.3, seed=21)
    ordering, _ = degeneracy_ordering(graph)
    eppstein_parallel._init_worker(graph, ordering)
    position = eppstein_parallel._position
    p_size = [
        sum(1 for w in graph[ordering[i]] if position[w] > i) for i in range(120)
    ]
    measured = [2.0 ** p / 1e4 for p in p_size]
    # one giant with branches (the last vertex has an empty P, nothing to split)
    measured[max(range(120), key=lambda i: p_size[i])] = sum(measured)
    fit = hetero_phase3.fit_predictor(p_size, measured)
    predicted = [measured[i] for i in range(120)]
    costs = hetero_phase3.Costs(measured, predicted, p_size)
    return graph, ordering, costs, fit


@pytest.mark.parametrize("name", SCHEDULES)
def test_every_vertex_covered_once(name: str) -> None:
    graph, ordering, costs, fit = _setup()
    speeds = [1.0, 1.0, 0.43, 0.43]
    queues, poll = hetero_phase3.build(name, speeds, costs, graph, ordering, fit)
    assert len(poll) == 4
    items = Counter(it for q in queues for task in q for it in task)
    assert all(n == 1 for n in items.values())
    whole = {it for it in items if isinstance(it, int)}
    split = {it[0] for it in items if isinstance(it, tuple)}
    assert whole | split == set(range(120)) and not whole & split
    position = eppstein_parallel._position
    for i in split:
        root = hetero.split_root(graph, ordering, position, i)
        assert root is not None
        branches = {it[1] for it in items if isinstance(it, tuple) and it[0] == i}
        assert branches == set(range(len(root[2])))


def test_split_actually_splits_the_giant() -> None:
    graph, ordering, costs, fit = _setup()
    queues, _ = hetero_phase3.build("split", [1.0, 0.5], costs, graph, ordering, fit)
    assert any(isinstance(it, tuple) for q in queues for t in q for it in t)


def test_giants_only_on_fast_cores() -> None:
    graph, ordering, costs, fit = _setup()
    queues, poll = hetero_phase3.build(
        "giants", [1.0, 0.5], costs, graph, ordering, fit
    )
    assert queues[0], "the planted giant should be in the fast-only queue"
    assert poll == [[0, 1], [1]]
