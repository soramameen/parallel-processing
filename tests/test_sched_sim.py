"""Tests for the schedule simulator."""

from __future__ import annotations

import pytest

from parallel_processing import sched_sim


class TestSimulate:
    def test_single_core_is_sum_over_speed(self) -> None:
        r = sched_sim.simulate_dynamic([1.0, 2.0, 3.0], [0.5])
        assert r.makespan == pytest.approx(12.0)
        assert r.idle_pct == pytest.approx(0.0)

    def test_dynamic_greedy_on_unequal_cores(self) -> None:
        # fast core: 2 then 2 (t=4); slow core (0.5): task of 2 takes 4 -> t=4
        r = sched_sim.simulate_dynamic([2.0, 2.0, 2.0], [1.0, 0.5])
        assert r.makespan == pytest.approx(4.0)
        assert r.tasks == [2, 1]

    def test_static_lists_run_separately(self) -> None:
        r = sched_sim.simulate_static([[3.0], [1.0]], [1.0, 1.0])
        assert r.makespan == pytest.approx(3.0)
        assert r.idle_pct == pytest.approx(100 * (1 - 4 / 6))

    def test_overhead_is_per_task(self) -> None:
        r = sched_sim.simulate_dynamic([1.0, 1.0], [1.0], overhead=0.5)
        assert r.makespan == pytest.approx(3.0)

    def test_fast_scale_speeds_up_the_last_fast_core(self) -> None:
        # two fast cores at 0.5 each while both busy, 1.0 when alone
        scale = [1.0, 1.0, 0.5].__getitem__
        r = sched_sim.simulate_dynamic([1.0, 3.0], [1.0, 1.0], fast_scale=scale)
        # both run at 0.5 until t=2 (task 1 done, 2 left on the other); then 1.0
        assert r.makespan == pytest.approx(4.0)

    def test_slow_factor_caps_at_full_speed(self) -> None:
        r = sched_sim.simulate_dynamic([1.0], [0.5], slow_factor=[4.0])
        assert r.makespan == pytest.approx(1.0)

    def test_queues_poll_in_priority_order(self) -> None:
        # core 0 prefers queue 0 (heavy); core 1 serves only queue 1
        r = sched_sim.simulate([[5.0], [1.0, 1.0]], [1.0, 1.0], [[0, 1], [1]])
        assert r.makespan == pytest.approx(5.0)
        assert r.tasks == [1, 2]


class TestLpt:
    def test_speed_weighted_assignment(self) -> None:
        lists = sched_sim.lpt_assign([4.0, 2.0, 2.0], [1.0, 0.5])
        loads = [sum([4.0, 2.0, 2.0][t] for t in lst) for lst in lists]
        assert loads == [6.0, 2.0]

    def test_lower_bound(self) -> None:
        assert sched_sim.lower_bound([1.0, 1.0, 10.0], [1.0, 1.0]) == 10.0
        assert sched_sim.lower_bound([1.0] * 10, [1.0, 0.5, 0.5]) == 5.0
