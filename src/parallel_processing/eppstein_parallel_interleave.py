"""Strided (interleaved) variant of the parallel Eppstein counter.

Identical to :func:`parallel_processing.eppstein_parallel.profile_eppstein_parallel`
except for batch construction: batch ``k`` takes indices ``k, k+K, k+2K, ...``
where ``K`` is the number of batches. Every batch therefore mixes vertices
from the cheap head and the heavy tail of the degeneracy ordering, so no
single batch concentrates the expensive subtrees the way a contiguous block
from the tail does.
"""

from __future__ import annotations

import time
from multiprocessing import Pool

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

    n = len(ordering)
    num_batches = -(-n // batch_size)
    batches = [range(k, n, num_batches) for k in range(num_batches)]

    start = time.perf_counter()
    with Pool(workers, initializer=_init_worker, initargs=(graph, ordering)) as pool:
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
