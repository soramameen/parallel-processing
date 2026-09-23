"""Makespan simulator for outer-loop schedules on cores of unequal speed.

Tasks are batches of outer vertices whose cost is the sum of the measured
per-vertex seconds on a full-speed core (``workload_profile`` CSV), plus a
fixed per-task overhead. A core of speed ``s`` burns ``s`` cost-seconds per
wall second. Three dispatch models match the executors in :mod:`hetero`:

- ``dynamic``: one shared queue in a fixed order; a core that goes idle
  takes the next task (``imap_unordered`` with chunksize 1, or the pull
  executor's shared list);
- ``static``: each core runs its own pre-assigned list;
- ``queues``: each core polls an ordered list of shared queues (e.g. fast
  cores take from a heavy queue first).

Speeds need not be constant. ``fast_scale(k)`` scales the fast cores when
``k`` of them are busy (the P-core clock dropping as more of them run), and
``slow_factor`` gives each task its own slow-core speed multiplier (memory
stalls that a lower clock does not stretch). Rates change only at task
boundaries, so the simulation is event driven over task starts and ends.
"""

from __future__ import annotations

import csv
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Workload:
    """Per-vertex costs (seconds at full speed) and candidate-set sizes."""

    seconds: list[float]
    p_size: list[int]

    @classmethod
    def from_csv(cls, path: str | Path) -> Workload:
        rows = sorted(csv.DictReader(open(path)), key=lambda r: int(r["pos"]))
        return cls(
            seconds=[float(r["seconds"]) for r in rows],
            p_size=[int(r["p_size"]) for r in rows],
        )

    @property
    def n(self) -> int:
        return len(self.seconds)

    def cost(self, batch: Sequence[int]) -> float:
        return sum(self.seconds[i] for i in batch)


@dataclass
class SimResult:
    makespan: float
    busy: list[float]
    tasks: list[int]
    speeds: list[float]

    @property
    def idle_pct(self) -> float:
        """Idle with every core counted as one unit (the M4 study's metric)."""
        return 100 * (1 - sum(self.busy) / (len(self.busy) * self.makespan))

    @property
    def idle_weighted_pct(self) -> float:
        capacity = sum(self.speeds) * self.makespan
        used = sum(b * s for b, s in zip(self.busy, self.speeds))
        return 100 * (1 - used / capacity)


def lower_bound(costs: Sequence[float], speeds: Sequence[float]) -> float:
    """No schedule beats total work over total speed, nor the biggest task
    on the fastest core."""
    return max(sum(costs) / sum(speeds), max(costs, default=0.0) / max(speeds))


def simulate(
    queues: Sequence[Sequence[float]],
    speeds: Sequence[float],
    poll: Sequence[Sequence[int]],
    overhead: float = 0.0,
    fast_scale: Callable[[int], float] | None = None,
    slow_factor: Sequence[Sequence[float]] | None = None,
) -> SimResult:
    """Run the pull model: core ``c`` takes the head of the first non-empty
    queue in ``poll[c]``. ``queues[q][t]`` is task ``t``'s cost; tasks on a
    core of speed 1 take ``cost + overhead`` seconds.

    ``fast_scale(k)`` multiplies the speed of speed-1 cores while ``k`` of
    them are busy. ``slow_factor[q][t]`` multiplies the speed of a slower
    core running that task (capped at speed 1).
    """
    cores = len(speeds)
    fast = [s >= 1 for s in speeds]
    heads = [0] * len(queues)
    busy = [0.0] * cores
    tasks = [0] * cores
    # what each core is running: (queue, task) or None, and its work left
    running: list[tuple[int, int] | None] = [None] * cores
    remaining = [0.0] * cores
    started = [0.0] * cores
    now = 0.0

    def take(c: int) -> None:
        running[c] = None
        for q in poll[c]:
            if heads[q] < len(queues[q]):
                t = heads[q]
                heads[q] += 1
                running[c] = (q, t)
                remaining[c] = queues[q][t] + overhead
                started[c] = now
                return

    def rate(c: int, busy_fast: int) -> float:
        s = speeds[c]
        if fast[c]:
            return s * (fast_scale(busy_fast) if fast_scale else 1.0)
        task = running[c]
        if slow_factor is not None and task is not None:
            return min(1.0, s * slow_factor[task[0]][task[1]])
        return s

    for c in range(cores):
        take(c)
    while True:
        active = [c for c in range(cores) if running[c] is not None]
        if not active:
            break
        busy_fast = sum(1 for c in active if fast[c])
        rates = {c: rate(c, busy_fast) for c in active}
        dt = min(remaining[c] / rates[c] for c in active)  # next completion
        now += dt
        for c in active:
            remaining[c] -= rates[c] * dt
        for c in active:
            if remaining[c] <= 1e-12:
                busy[c] += now - started[c]
                tasks[c] += 1
                take(c)
    return SimResult(makespan=now, busy=busy, tasks=tasks, speeds=list(speeds))


def simulate_dynamic(
    costs: Sequence[float],
    speeds: Sequence[float],
    overhead: float = 0.0,
    fast_scale: Callable[[int], float] | None = None,
    slow_factor: Sequence[float] | None = None,
) -> SimResult:
    """One shared queue in the given order (``imap_unordered``)."""
    return simulate(
        [costs],
        speeds,
        [[0]] * len(speeds),
        overhead,
        fast_scale,
        None if slow_factor is None else [slow_factor],
    )


def simulate_static(
    per_core: Sequence[Sequence[float]],
    speeds: Sequence[float],
    overhead: float = 0.0,
    fast_scale: Callable[[int], float] | None = None,
    slow_factor: Sequence[Sequence[float]] | None = None,
) -> SimResult:
    """Each core runs only its own list."""
    poll = [[c] for c in range(len(speeds))]
    return simulate(per_core, speeds, poll, overhead, fast_scale, slow_factor)


def lpt_assign(costs: Sequence[float], speeds: Sequence[float]) -> list[list[int]]:
    """Static LPT for uniform machines: heaviest task first, each to the core
    that would finish it earliest under the *assumed* ``speeds``.

    Returns task indices per core, heaviest first. Passing a wrong ``speeds``
    (a misestimated r) is how the robustness experiment perturbs it.
    """
    order = sorted(range(len(costs)), key=lambda t: -costs[t])
    load = [0.0] * len(speeds)
    lists: list[list[int]] = [[] for _ in speeds]
    for t in order:
        c = min(range(len(speeds)), key=lambda c: (load[c] + costs[t]) / speeds[c])
        load[c] += costs[t]
        lists[c].append(t)
    return lists
