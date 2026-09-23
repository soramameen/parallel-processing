"""Tests for the emulated asymmetric-core counter."""

from __future__ import annotations

import os

import pytest
from test_eppstein_parallel import random_graph

from parallel_processing import hetero
from parallel_processing.eppstein import count_eppstein_cliques


class TestParseCores:
    def test_letters_map_to_full_and_slow(self) -> None:
        assert hetero.parse_cores("F,F,S,S", 0.43) == [1.0, 1.0, 0.43, 0.43]

    def test_bare_numbers_are_speeds(self) -> None:
        assert hetero.parse_cores("1,0.5", 0.43) == [1.0, 0.5]

    def test_rejects_out_of_range_speed(self) -> None:
        with pytest.raises(ValueError):
            hetero.parse_cores("F,S", 0.0)

    def test_rejects_more_cores_than_cpus(self) -> None:
        with pytest.raises(ValueError):
            hetero.parse_cores(",".join(["F"] * ((os.cpu_count() or 1) + 1)), 1.0)


class TestMakeBatches:
    @pytest.mark.parametrize("strategy", hetero.STRATEGIES)
    def test_every_index_exactly_once(self, strategy: str) -> None:
        batches = hetero.make_batches(1000, strategy, 64)
        indices = [i for batch in batches for i in batch]
        assert sorted(indices) == list(range(1000))
        assert len(batches) == 16

    def test_interleave_mixes_head_and_tail(self) -> None:
        batch = list(hetero.make_batches(1000, "interleave", 64)[0])
        assert batch[0] == 0 and batch[-1] >= 900


@pytest.mark.skipif(not hetero.cgroups_available(), reason="needs cgroup-v1 cpu, root")
class TestProfileHetero:
    def test_matches_sequential_on_asymmetric_cores(self) -> None:
        graph = random_graph(80, 0.3, seed=7)
        expected = count_eppstein_cliques(graph)
        for strategy in hetero.STRATEGIES:
            p = hetero.profile_hetero(graph, [1.0, 0.5], strategy, batch_size=8)
            assert (p.cliques, p.largest) == expected
            assert sum(p.vertices) == len(graph)

    def test_groups_are_removed(self) -> None:
        graph = random_graph(20, 0.3, seed=1)
        hetero.profile_hetero(graph, [1.0, 0.5], "block", batch_size=4)
        leftovers = [
            p for p in hetero.CGROUP_ROOT.iterdir()
            if p.name.startswith(f"{hetero.GROUP_PREFIX}{os.getpid()}_")
        ]
        assert leftovers == []

    def test_period_too_short_for_speed_is_rejected(self) -> None:
        graph = random_graph(10, 0.3, seed=1)
        with pytest.raises(ValueError):
            hetero.profile_hetero(graph, [0.26], "block", period_us=1_000)
        assert not any(
            p.name.startswith(f"{hetero.GROUP_PREFIX}{os.getpid()}_")
            for p in hetero.CGROUP_ROOT.iterdir()
        )


class TestSplitRoot:
    def test_branches_partition_the_vertex_count(self) -> None:
        from parallel_processing import eppstein_parallel
        from parallel_processing.eppstein import degeneracy_ordering

        graph = random_graph(60, 0.4, seed=3)
        ordering, _ = degeneracy_ordering(graph)
        eppstein_parallel._init_worker(graph, ordering)
        position = eppstein_parallel._position
        for i in range(len(ordering)):
            whole = hetero._count_item(i)
            root = hetero.split_root(graph, ordering, position, i)
            if root is None:
                assert whole == (1, 1)
                continue
            parts = [hetero._count_item((i, j)) for j in range(len(root[2]))]
            assert sum(c for c, _ in parts) == whole[0]
            assert max((m for _, m in parts), default=0) == whole[1]


@pytest.mark.skipif(not hetero.cgroups_available(), reason="needs cgroup-v1 cpu, root")
class TestProfilePull:
    def _graph_and_items(self):  # type: ignore[no-untyped-def]
        from parallel_processing.eppstein import degeneracy_ordering

        graph = random_graph(80, 0.3, seed=11)
        ordering, _ = degeneracy_ordering(graph)
        return graph, ordering, list(range(len(ordering)))

    def test_shared_queue_matches_sequential(self) -> None:
        graph, ordering, items = self._graph_and_items()
        tasks: list[hetero.Task] = [list(items[i : i + 8]) for i in range(0, 80, 8)]
        p = hetero.profile_pull(graph, [1.0, 0.5], [tasks], [[0], [0]])
        assert (p.cliques, p.largest) == count_eppstein_cliques(graph)
        assert sum(p.vertices) == 80

    def test_static_lists_and_split_items(self) -> None:
        from parallel_processing import eppstein_parallel

        graph, ordering, items = self._graph_and_items()
        eppstein_parallel._init_worker(graph, ordering)
        heavy = max(items, key=lambda i: len(hetero.split_root(
            graph, ordering, eppstein_parallel._position, i) or ((), (), [])[2]))
        root = hetero.split_root(graph, ordering, eppstein_parallel._position, heavy)
        assert root is not None
        split: list[hetero.Item] = [(heavy, j) for j in range(len(root[2]))]
        rest: list[hetero.Item] = [i for i in items if i != heavy]
        queues = [[[it] for it in split + rest[::2]], [[it] for it in rest[1::2]]]
        p = hetero.profile_pull(graph, [1.0, 0.5], queues, [[0], [1]])
        assert (p.cliques, p.largest) == count_eppstein_cliques(graph)

    def test_fast_scale_controller_runs(self) -> None:
        graph, ordering, items = self._graph_and_items()
        tasks: list[hetero.Task] = [[i] for i in items]
        p = hetero.profile_pull(
            graph, [1.0, 1.0, 0.5], [tasks], [[0]] * 3, fast_scale=[1.0, 1.0, 0.8]
        )
        assert (p.cliques, p.largest) == count_eppstein_cliques(graph)
