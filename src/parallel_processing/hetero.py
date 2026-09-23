"""Parallel Eppstein counter on emulated asymmetric cores (Linux only).

The M4 study found that balancing load across P and E cores barely helps,
but macOS cannot pin a process to a P core nor run an E core at a known
speed, so the core-speed ratio r was never measured directly. This module
builds cores whose speed is known by construction: each worker is pinned to
one CPU and placed in its own cgroup-v1 ``cpu`` group whose CFS quota caps
it at ``speed`` of that CPU.

Throttling is not a lower clock. A throttled core runs at full speed for
``speed * period`` and is then frozen for the rest of the period, so

- averaged over a task much longer than the period it looks like a core of
  speed ``speed`` (the property the scheduling question needs);
- it slows memory stalls by the same factor as compute, unlike a real
  low-clock core, where stalls do not stretch;
- while frozen it cannot pick up a new task at all.

Batch construction reuses the three strategies of the M4 study (block,
reversed, interleave); dispatch is ``imap_unordered`` as before, so the only
new variable is the core speeds. Busy time is wall-clock
(``perf_counter``), which includes the frozen part of each period: that is
the slowness being emulated. ``process_time`` would hide it.

Requires root and a cgroup-v1 ``cpu`` controller at :data:`CGROUP_ROOT`.
"""

from __future__ import annotations

import multiprocessing
import multiprocessing.synchronize
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from parallel_processing import eppstein_parallel
from parallel_processing.eppstein import Graph, degeneracy_ordering

CGROUP_ROOT = Path("/sys/fs/cgroup/cpu")
GROUP_PREFIX = "pp"

# 100 ms (the kernel default) makes a 0.43 core run 43 ms then freeze 57 ms,
# coarse enough to distort short batches. Calibration on soc-sign-epinions
# (artifacts/linux/calibration.log) put 4 ms as close to the set speed as
# 100 ms (graph tasks at 0.97-0.98 of it, 10 ms at 0.92-0.97), and 4 ms is
# the shortest period that still expresses speed 0.26 above the 1 ms quota
# floor, so frozen spells stay under 3 ms.
DEFAULT_PERIOD_US = 4_000
MIN_QUOTA_US = 1_000

STRATEGIES = ("block", "reversed", "interleave")


def cgroups_available() -> bool:
    """True when per-core CPU groups can be created here."""
    return (CGROUP_ROOT / "cpu.cfs_quota_us").exists() and os.access(
        CGROUP_ROOT, os.W_OK
    )


def parse_cores(spec: str, r: float) -> list[float]:
    """Turn ``"F,F,S,S"`` into per-core speeds ``[1, 1, r, r]``.

    A bare number is taken as that core's speed, so ``"1,0.43"`` also works.
    """
    speeds = []
    for token in spec.split(","):
        token = token.strip()
        if token == "F":
            speeds.append(1.0)
        elif token == "S":
            speeds.append(r)
        else:
            speeds.append(float(token))
    if not speeds or any(not 0 < s <= 1 for s in speeds):
        raise ValueError(f"core speeds must be in (0, 1]: {spec!r} (r={r})")
    cpus = os.cpu_count() or 1
    if len(speeds) > cpus:
        raise ValueError(f"{len(speeds)} cores requested, {cpus} CPUs")
    return speeds


class CoreGroups:
    """One cgroup per emulated core; a context manager that removes them.

    Core ``i`` is CPU ``i`` capped at ``speeds[i]`` of it. Speed 1 still gets
    a group (with no quota) so every worker goes through the same path.
    """

    def __init__(self, speeds: list[float], period_us: int = DEFAULT_PERIOD_US):
        self.speeds = speeds
        self.period_us = period_us
        # The owner's pid keeps concurrent runs (a test during an experiment)
        # from sharing, and then deleting, each other's groups.
        self.paths = [
            CGROUP_ROOT / f"{GROUP_PREFIX}{os.getpid()}_core{i}"
            for i in range(len(speeds))
        ]

    def __enter__(self) -> CoreGroups:
        try:
            for path, speed in zip(self.paths, self.speeds):
                path.mkdir(exist_ok=True)
                (path / "cpu.cfs_period_us").write_text(str(self.period_us))
                self.set_speed(path, speed)
        except BaseException:
            self.__exit__()
            raise
        return self

    def set_speed(self, path: Path, speed: float) -> None:
        if speed >= 1:
            quota = -1
        else:
            quota = round(speed * self.period_us)
            # The kernel rejects quotas under 1 ms, so a short period cannot
            # express a slow core; fail instead of silently running fast.
            if quota < MIN_QUOTA_US:
                raise ValueError(
                    f"speed {speed} needs period >= {MIN_QUOTA_US / speed:.0f}us, "
                    f"got {self.period_us}us"
                )
        (path / "cpu.cfs_quota_us").write_text(str(quota))

    def members(self, i: int) -> list[int]:
        text = (self.paths[i] / "cgroup.procs").read_text()
        return [int(pid) for pid in text.split()]

    def wait_populated(self, timeout: float = 60.0) -> None:
        """Block until every group holds exactly one worker."""
        deadline = time.monotonic() + timeout
        while any(len(self.members(i)) != 1 for i in range(len(self.paths))):
            if time.monotonic() > deadline:
                counts = [len(self.members(i)) for i in range(len(self.paths))]
                raise RuntimeError(f"workers did not attach to cores: {counts}")
            time.sleep(0.01)

    def __exit__(self, *exc: object) -> None:
        # Pool.__exit__ terminates workers asynchronously; rmdir fails while a
        # group still holds a pid, so retry briefly before giving up.
        for path in self.paths:
            for _ in range(200):
                try:
                    path.rmdir()
                    break
                except FileNotFoundError:
                    break
                except OSError:
                    time.sleep(0.01)


# Worker-process state, set once by _init_worker.
_slot = -1


def _init_worker(
    graph: Graph,
    ordering: list[int],
    slots: multiprocessing.Queue[int],
    paths: list[str],
) -> None:
    global _slot
    eppstein_parallel._init_worker(graph, ordering)
    _slot = slots.get()
    os.sched_setaffinity(0, {_slot})
    Path(paths[_slot], "cgroup.procs").write_text(str(os.getpid()))


def _count_batch_timed(batch: range | list[int]) -> tuple[int, float, int, int, int]:
    """Count one batch; report (slot, elapsed, vertices, count, largest)."""
    start = time.perf_counter()
    count, largest = eppstein_parallel._count_batch(batch)
    return _slot, time.perf_counter() - start, len(batch), count, largest


LOOP_ITERATIONS = 20_000_000


def _calibration_task(kind: str, batch: range | list[int]) -> float:
    """Time a pure integer loop (``kind == "loop"``) or one outer-loop batch."""
    start = time.perf_counter()
    if kind == "loop":
        x = 0
        for i in range(LOOP_ITERATIONS):
            x += i
    else:
        eppstein_parallel._count_batch(batch)
    return time.perf_counter() - start


def make_batches(n: int, strategy: str, batch_size: int) -> list[range | list[int]]:
    """Outer-vertex index batches, built exactly as in the M4 variants."""
    if strategy == "block":
        return [range(i, min(i + batch_size, n)) for i in range(0, n, batch_size)]
    if strategy == "reversed":
        indices = list(range(n))[::-1]
        return [indices[i : i + batch_size] for i in range(0, n, batch_size)]
    if strategy == "interleave":
        num_batches = -(-n // batch_size)
        return [range(k, n, num_batches) for k in range(num_batches)]
    raise ValueError(f"unknown strategy {strategy!r}; choose from {STRATEGIES}")


@dataclass
class HeteroProfile:
    """One run on emulated cores; per-slot lists are indexed by core."""

    speeds: list[float]
    ordering_s: float
    startup_s: float
    compute_s: float
    cliques: int
    largest: int
    batches: int
    busy: list[float]
    vertices: list[int]
    tasks: list[int]


def profile_hetero(
    graph: Graph,
    speeds: list[float],
    strategy: str = "block",
    batch_size: int = 64,
    period_us: int = DEFAULT_PERIOD_US,
) -> HeteroProfile:
    """Count maximal cliques with one worker per emulated core."""
    start = time.perf_counter()
    ordering, _ = degeneracy_ordering(graph)
    ordering_s = time.perf_counter() - start
    batches = make_batches(len(ordering), strategy, batch_size)

    workers = len(speeds)
    ctx = multiprocessing.get_context("spawn")  # same start method as the M4 runs
    slots = ctx.Queue()
    for i in range(workers):
        slots.put(i)

    busy = [0.0] * workers
    vertices = [0] * workers
    tasks = [0] * workers
    with CoreGroups(speeds, period_us) as groups:
        start = time.perf_counter()
        paths = [str(p) for p in groups.paths]
        with ctx.Pool(
            workers, initializer=_init_worker, initargs=(graph, ordering, slots, paths)
        ) as pool:
            groups.wait_populated()
            startup_s = time.perf_counter() - start

            start = time.perf_counter()
            count = 0
            largest = 0
            results = pool.imap_unordered(_count_batch_timed, batches)
            for slot, elapsed, n_vertices, sub_count, sub_largest in results:
                count += sub_count
                largest = max(largest, sub_largest)
                busy[slot] += elapsed
                vertices[slot] += n_vertices
                tasks[slot] += 1
            compute_s = time.perf_counter() - start

    return HeteroProfile(
        speeds=speeds,
        ordering_s=ordering_s,
        startup_s=startup_s,
        compute_s=compute_s,
        cliques=count,
        largest=largest,
        batches=len(batches),
        busy=busy,
        vertices=vertices,
        tasks=tasks,
    )


# --- Pull executor -----------------------------------------------------------
#
# Pool/imap_unordered can only express "one shared queue in a fixed order".
# The schedules compared in Phase 3 also need per-core lists (static LPT),
# queues that only some cores serve (heavy tasks to fast cores first), and
# tasks that are one first-level branch of a heavy vertex. The pull executor
# gives each worker an ordered list of shared task lists; a worker takes the
# head of the first non-empty one through a shared cursor, so no parent
# dispatch sits between tasks.

# A task item is an outer-vertex position, or (position, j): the j-th
# first-level branch of that vertex's subproblem.
Item = int | tuple[int, int]
Task = list[Item]


def split_root(
    graph: Graph, ordering: list[int], position: dict[int, int], i: int
) -> tuple[set[int], set[int], list[int]] | None:
    """(P, X, branches) of outer vertex ``i``'s root call, or None when the
    vertex is itself a maximal clique (P and X both empty).

    The pivot and branch order are made deterministic (sorted, ties to the
    smallest vertex) so every process agrees on what branch ``j`` is.
    """
    v = ordering[i]
    p = {w for w in graph[v] if position[w] > i}
    x = {w for w in graph[v] if position[w] < i}
    if not p and not x:
        return None
    pivot = max(sorted(p | x), key=lambda u: len(p & graph[u]))
    return p, x, sorted(p - graph[pivot])


def _count_item(item: Item) -> tuple[int, int]:
    if isinstance(item, int):
        return eppstein_parallel._count_batch([item])
    i, j = item
    graph = eppstein_parallel._graph
    ordering, position = eppstein_parallel._ordering, eppstein_parallel._position
    root = split_root(graph, ordering, position, i)
    assert root is not None, f"vertex {i} has no branches"
    p, x, branches = root
    for v in branches[:j]:  # the root loop moves earlier branches from P to X
        p.discard(v)
        x.add(v)
    v = branches[j]
    return eppstein_parallel._count_pivot(p & graph[v], x & graph[v], 2)


def _pull_worker(
    slot: int,
    graph: Graph,
    ordering: list[int],
    queues: list[list[Task]],
    poll: list[int],
    cursors: Any,  # ctx.Array("i"): one cursor per queue, with a lock
    active: Any,  # ctx.Array("b", lock=False): 1 while that worker still runs
    group: str,
    ready: multiprocessing.Queue[int],
    go: multiprocessing.synchronize.Event,
    results: multiprocessing.Queue[tuple[int, float, int, int, int, int]],
) -> None:
    eppstein_parallel._init_worker(graph, ordering)
    os.sched_setaffinity(0, {slot})
    Path(group, "cgroup.procs").write_text(str(os.getpid()))
    ready.put(slot)
    go.wait()
    busy = 0.0
    items = tasks = count = largest = 0
    active[slot] = 1
    while True:
        task = None
        with cursors.get_lock():
            for q in poll:
                k = cursors[q]
                if k < len(queues[q]):
                    cursors[q] = k + 1
                    task = queues[q][k]
                    break
        if task is None:
            break
        start = time.perf_counter()
        for item in task:
            sub_count, sub_largest = _count_item(item)
            count += sub_count
            largest = max(largest, sub_largest)
        busy += time.perf_counter() - start
        items += len(task)
        tasks += 1
    active[slot] = 0
    results.put((slot, busy, items, tasks, count, largest))


def profile_pull(
    graph: Graph,
    speeds: list[float],
    queues: list[list[Task]],
    poll: list[list[int]],
    period_us: int = DEFAULT_PERIOD_US,
    fast_scale: list[float] | None = None,
    control_interval: float = 0.005,
    ordering: list[int] | None = None,
) -> HeteroProfile:
    """Count maximal cliques with the pull executor on emulated cores.

    ``poll[c]`` lists, in priority order, the queues core ``c`` serves.
    ``fast_scale[k]``, when given, is the speed of every speed-1 core while
    ``k`` of them are still working; a control thread rewrites their quota
    as that count changes (the P-core clock dropping with load).
    """
    start = time.perf_counter()
    if ordering is None:
        ordering, _ = degeneracy_ordering(graph)
    ordering_s = time.perf_counter() - start

    workers = len(speeds)
    fast = [i for i, s in enumerate(speeds) if s >= 1]
    ctx = multiprocessing.get_context("spawn")
    cursors = ctx.Array("i", len(queues))
    active = ctx.Array("b", workers, lock=False)
    ready: multiprocessing.Queue[int] = ctx.Queue()
    results: multiprocessing.Queue[tuple[int, float, int, int, int, int]] = ctx.Queue()
    go = ctx.Event()

    busy = [0.0] * workers
    vertices = [0] * workers
    tasks = [0] * workers
    count = largest = 0
    with CoreGroups(speeds, period_us) as groups:
        start = time.perf_counter()
        procs = [
            ctx.Process(
                target=_pull_worker,
                args=(
                    c, graph, ordering, queues, poll[c], cursors, active,
                    str(groups.paths[c]), ready, go, results,
                ),
            )
            for c in range(workers)
        ]
        for proc in procs:
            proc.start()
        try:
            for _ in range(workers):
                ready.get(timeout=120)
            groups.wait_populated()
            startup_s = time.perf_counter() - start

            stop = False
            if fast_scale is not None:
                # All workers are active from the start signal on.
                for c in fast:
                    groups.set_speed(groups.paths[c], fast_scale[len(fast)])

                def control() -> None:
                    current = len(fast)
                    while not stop:
                        k = sum(active[c] for c in fast)
                        if k != current and k > 0:
                            for c in fast:
                                groups.set_speed(groups.paths[c], fast_scale[k])
                            current = k
                        time.sleep(control_interval)

                controller = threading.Thread(target=control, daemon=True)

            start = time.perf_counter()
            go.set()
            if fast_scale is not None:
                controller.start()
            for _ in range(workers):
                slot, b, n_items, n_tasks, sub_count, sub_largest = results.get()
                busy[slot] = b
                vertices[slot] = n_items
                tasks[slot] = n_tasks
                count += sub_count
                largest = max(largest, sub_largest)
            compute_s = time.perf_counter() - start
            stop = True
        finally:
            for proc in procs:
                proc.join(timeout=10)
                if proc.is_alive():
                    proc.terminate()
                    proc.join()

    return HeteroProfile(
        speeds=speeds,
        ordering_s=ordering_s,
        startup_s=startup_s,
        compute_s=compute_s,
        cliques=count,
        largest=largest,
        batches=sum(len(q) for q in queues),
        busy=busy,
        vertices=vertices,
        tasks=tasks,
    )
