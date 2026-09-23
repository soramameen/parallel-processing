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
    """Optimal preemptive makespan on uniform machines (Q|pmtn|Cmax), a lower
    bound for every schedule here: the k largest tasks cannot finish before
    their total over the k fastest speeds, for each k below the machine count,
    and all work cannot finish before the total over all speeds (Horvath, Lam
    and Sethi 1977; Gonzalez and Sahni 1978)."""
    tasks = sorted(costs, reverse=True)
    fast = sorted(speeds, reverse=True)
    bound = sum(tasks) / sum(fast)
    work = speed = 0.0
    for k in range(min(len(tasks), len(fast) - 1)):
        work += tasks[k]
        speed += fast[k]
        bound = max(bound, work / speed)
    return bound


def simulate(
    queues: Sequence[Sequence[float]],
    speeds: Sequence[float],
    poll: Sequence[Sequence[int]],
    overhead: float = 0.0,
    fast_scale: Callable[[int], float] | None = None,
    slow_factor: Sequence[Sequence[float]] | None = None,
    migrate: bool = False,
) -> SimResult:
    """Run the pull model: worker ``w`` takes the head of the first non-empty
    queue in ``poll[w]``. ``queues[q][t]`` is task ``t``'s cost; tasks on a
    core of speed 1 take ``cost + overhead`` seconds.

    ``speeds`` are the cores; there are ``len(poll)`` workers, and worker
    ``w`` starts on core ``w`` (so list fast cores first to mimic an OS that
    places the first threads on them). With ``migrate``, a worker that runs
    out of tasks frees its core, and the active worker on the slowest core
    moves to it when it is faster, carrying its unfinished task: the macOS
    behaviour of moving a runnable thread onto a P core that goes idle.
    Without it, workers stay pinned.

    ``fast_scale(k)`` multiplies the speed of speed-1 cores while ``k`` of
    them are busy. ``slow_factor[q][t]`` multiplies the speed of a slower
    core running that task (capped at speed 1).
    """
    workers = len(poll)
    if workers > len(speeds):
        raise ValueError(f"{workers} workers for {len(speeds)} cores")
    core = list(range(workers))  # worker -> core it runs on
    free = set(range(workers, len(speeds)))
    heads = [0] * len(queues)
    busy = [0.0] * workers
    tasks = [0] * workers
    # what each worker is running: (queue, task) or None, and its work left
    running: list[tuple[int, int] | None] = [None] * workers
    remaining = [0.0] * workers
    started = [0.0] * workers
    now = 0.0

    def take(w: int) -> None:
        running[w] = None
        for q in poll[w]:
            if heads[q] < len(queues[q]):
                t = heads[q]
                heads[q] += 1
                running[w] = (q, t)
                remaining[w] = queues[q][t] + overhead
                started[w] = now
                return

    def rate(w: int, busy_fast: int) -> float:
        s = speeds[core[w]]
        if s >= 1:
            return s * (fast_scale(busy_fast) if fast_scale else 1.0)
        task = running[w]
        if slow_factor is not None and task is not None:
            return min(1.0, s * slow_factor[task[0]][task[1]])
        return s

    def rebalance() -> None:
        while free:
            best = max(free, key=lambda c: speeds[c])
            active = [w for w in range(workers) if running[w] is not None]
            if not active:
                return
            slowest = min(active, key=lambda w: speeds[core[w]])
            if speeds[core[slowest]] >= speeds[best]:
                return
            free.remove(best)
            free.add(core[slowest])
            core[slowest] = best

    for w in range(workers):
        take(w)
    while True:
        active = [w for w in range(workers) if running[w] is not None]
        if not active:
            break
        busy_fast = sum(1 for w in active if speeds[core[w]] >= 1)
        rates = {w: rate(w, busy_fast) for w in active}
        dt = min(remaining[w] / rates[w] for w in active)  # next completion
        now += dt
        for w in active:
            remaining[w] -= rates[w] * dt
        for w in active:
            if remaining[w] <= 1e-12:
                busy[w] += now - started[w]
                tasks[w] += 1
                take(w)
                if running[w] is None:
                    free.add(core[w])
        if migrate:
            rebalance()
    return SimResult(
        makespan=now,
        busy=busy,
        tasks=tasks,
        speeds=[speeds[c] for c in range(workers)],
    )


def simulate_dynamic(
    costs: Sequence[float],
    speeds: Sequence[float],
    overhead: float = 0.0,
    fast_scale: Callable[[int], float] | None = None,
    slow_factor: Sequence[float] | None = None,
    migrate: bool = False,
    workers: int | None = None,
) -> SimResult:
    """One shared queue in the given order (``imap_unordered``), with
    ``workers`` workers (default: one per core)."""
    return simulate(
        [costs],
        speeds,
        [[0]] * (len(speeds) if workers is None else workers),
        overhead,
        fast_scale,
        None if slow_factor is None else [slow_factor],
        migrate,
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
