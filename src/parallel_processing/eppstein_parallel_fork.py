"""Fork-start-method variant of the parallel Eppstein counter.

Identical to :func:`parallel_processing.eppstein_parallel.profile_eppstein_parallel`
except for how workers are started: ``get_context("fork")`` instead of the
macOS default *spawn*. Forked children inherit the parent's memory
(copy-on-write), so the graph and ordering are never pickled and shipped —
the startup phase should collapse to the cost of fork itself.

macOS defaults to spawn because forking a process that already has threads
can deadlock in the child; this process is single-threaded pure Python at
fork time, so fork is safe here. Batch construction stays the contiguous
block of the base variant so that any difference against strategy "block"
is attributable to the start method alone.
"""

from __future__ import annotations

import time
from multiprocessing import get_context

from parallel_processing.eppstein import Graph, degeneracy_ordering
from parallel_processing.eppstein_parallel import (
    BATCH_SIZE,
    PhaseProfile,
    _count_batch_timed,
    _init_worker,
    _noop,
)


def profile_eppstein_parallel(
    graph: Graph, workers: int, batch_size: int = BATCH_SIZE
) -> PhaseProfile:
    start = time.perf_counter()
    ordering, _ = degeneracy_ordering(graph)
    ordering_s = time.perf_counter() - start

    batches = [
        range(i, min(i + batch_size, len(ordering)))
        for i in range(0, len(ordering), batch_size)
    ]

    start = time.perf_counter()
    ctx = get_context("fork")
    with ctx.Pool(workers, initializer=_init_worker, initargs=(graph, ordering)) as pool:
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
