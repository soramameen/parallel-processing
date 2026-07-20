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

import sys
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
