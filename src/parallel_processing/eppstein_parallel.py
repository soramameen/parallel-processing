"""Naive outer-loop parallelisation of the Eppstein-Löffler-Strash algorithm.

The outermost loop of *BronKerboschDegeneracy* visits each vertex of the
degeneracy ordering independently: the subproblem for ``v_i`` depends only
on the (fixed) graph and ordering, never on the other iterations. This
module exploits exactly that and nothing more — a :mod:`multiprocessing`
pool where each task counts the cliques rooted at a batch of consecutive
outer vertices.

Deliberately naive, for study purposes:

- The whole graph and ordering are shipped to every worker once at pool
  start-up (macOS uses the *spawn* start method, so they are pickled);
  no shared memory, no compact adjacency arrays.
- Load balancing is only what ``imap_unordered`` over fixed-size batches
  provides. A vertex with a huge subtree still serialises its batch.
- Only the counting variant is parallelised; materialising tens of
  millions of cliques across processes is a different problem.

Usage::

    python -m parallel_processing.benchmark_eppstein_parallel [path] [workers]
"""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass
from multiprocessing import Pool

from parallel_processing.eppstein import Graph, degeneracy_ordering

# Outer vertices per pool task. Small enough that imap_unordered can even
# out worker loads, large enough that task dispatch overhead stays trivial.
BATCH_SIZE = 512

# Worker-process state, set once by _init_worker. Module-level globals are
# the plain-multiprocessing way to avoid re-pickling the graph per task.
_graph: Graph = {}
_ordering: list[int] = []
_position: dict[int, int] = {}


def _init_worker(graph: Graph, ordering: list[int]) -> None:
    global _graph, _ordering, _position
    _graph = graph
    _ordering = ordering
    _position = {v: i for i, v in enumerate(ordering)}
    sys.setrecursionlimit(max(sys.getrecursionlimit(), len(graph) + 1000))


def _count_pivot(p: set[int], x: set[int], depth: int) -> tuple[int, int]:
    """Count cliques in one subtree; the pivot recursion of eppstein.py,
    restated here over the worker globals so no closure needs pickling."""
    if not p and not x:
        return 1, depth
    count = 0
    largest = 0
    pivot = max(p | x, key=lambda u: len(p & _graph[u]))
    for v in list(p - _graph[pivot]):
        neighbours = _graph[v]
        sub_count, sub_largest = _count_pivot(p & neighbours, x & neighbours, depth + 1)
        count += sub_count
        largest = max(largest, sub_largest)
        p.discard(v)
        x.add(v)
    return count, largest


def _count_batch(batch: range) -> tuple[int, int]:
    """Count cliques rooted at the outer vertices ``ordering[i]`` for i in batch."""
    count = 0
    largest = 0
    for i in batch:
        v = _ordering[i]
        p = {w for w in _graph[v] if _position[w] > i}
        x = {w for w in _graph[v] if _position[w] < i}
        sub_count, sub_largest = _count_pivot(p, x, 1)
        count += sub_count
        largest = max(largest, sub_largest)
    return count, largest


def _noop(_: int) -> None:
    return None


def _count_batch_timed(batch: range) -> tuple[int, float, int, int]:
    """Like _count_batch, but also report (pid, elapsed) for busy accounting."""
    start = time.perf_counter()
    count, largest = _count_batch(batch)
    return os.getpid(), time.perf_counter() - start, count, largest


@dataclass
class PhaseProfile:
    """Wall-clock seconds of each phase of one parallel run."""

    ordering_s: float
    startup_s: float
    compute_s: float
    cliques: int
    largest: int
    worker_busy: dict[int, float]
    batches: int


def profile_eppstein_parallel(
    graph: Graph, workers: int, batch_size: int = BATCH_SIZE
) -> PhaseProfile:
    """Run the parallel counter with per-phase timing; same result as
    :func:`count_eppstein_cliques_parallel`."""
    start = time.perf_counter()
    ordering, _ = degeneracy_ordering(graph)
    ordering_s = time.perf_counter() - start

    batches = [
        range(i, min(i + batch_size, len(ordering)))
        for i in range(0, len(ordering), batch_size)
    ]

    start = time.perf_counter()
    with Pool(workers, initializer=_init_worker, initargs=(graph, ordering)) as pool:
        # Pool() returns before the children finish unpickling the graph, so a
        # chunksize-1 noop sweep is the barrier; it only approximates full
        # startup because imap may still reach a worker that skipped the sweep.
        pool.map(_noop, range(workers * 4), chunksize=1)
        startup_s = time.perf_counter() - start

        start = time.perf_counter()
        count = 0
        largest = 0
        worker_busy: dict[int, float] = {}
        for pid, elapsed, sub_count, sub_largest in pool.imap_unordered(
            _count_batch_timed, batches
        ):
            count += sub_count
            largest = max(largest, sub_largest)
            worker_busy[pid] = worker_busy.get(pid, 0.0) + elapsed
        compute_s = time.perf_counter() - start

    return PhaseProfile(
        ordering_s=ordering_s,
        startup_s=startup_s,
        compute_s=compute_s,
        cliques=count,
        largest=largest,
        worker_busy=worker_busy,
        batches=len(batches),
    )


def count_eppstein_cliques_parallel(
    graph: Graph, workers: int
) -> tuple[int, int]:
    """Count maximal cliques with ``workers`` processes; return (count, largest).

    Same result as :func:`parallel_processing.eppstein.count_eppstein_cliques`;
    the degeneracy ordering is computed sequentially here and only the outer
    loop is fanned out.
    """
    ordering, _ = degeneracy_ordering(graph)
    batches = [
        range(start, min(start + BATCH_SIZE, len(ordering)))
        for start in range(0, len(ordering), BATCH_SIZE)
    ]
    count = 0
    largest = 0
    with Pool(workers, initializer=_init_worker, initargs=(graph, ordering)) as pool:
        for sub_count, sub_largest in pool.imap_unordered(_count_batch, batches):
            count += sub_count
            largest = max(largest, sub_largest)
    return count, largest
