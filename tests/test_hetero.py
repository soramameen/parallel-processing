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
