"""Shared-memory variant of the parallel Eppstein counter.

Identical to :func:`parallel_processing.eppstein_parallel.profile_eppstein_parallel`
except for how the graph reaches the workers: instead of pickling the
dict-of-sets through the spawn pipe, the parent packs it once into CSR-style
int64 arrays inside :class:`multiprocessing.shared_memory.SharedMemory`
blocks, and each worker attaches to those blocks by name.

The recursion kernel needs Python set operations, and sets cannot live in
shared memory, so each worker still rebuilds its own dict-of-sets from the
shared arrays at start-up. What this variant removes is only the pickle
serialisation and pipe transfer; the per-worker structure build remains.
Comparing its startup against spawn (transfer + build) and fork (neither)
therefore splits the spawn startup cost into its two parts.

The start method stays *spawn* (the macOS default) on purpose: the only
difference against strategy "block" is how the graph is delivered.
"""

from __future__ import annotations

import time
from array import array
from multiprocessing import get_context, shared_memory

from parallel_processing.eppstein import Graph, degeneracy_ordering
from parallel_processing.eppstein_parallel import (
    BATCH_SIZE,
    PhaseProfile,
    _count_batch_timed,
    _init_worker,
    _noop,
)


def _pack(graph: Graph, ordering: list[int]) -> tuple[list[shared_memory.SharedMemory], tuple]:
    """Lay the graph out as CSR arrays in shared memory.

    Returns the blocks (caller owns close/unlink) and the initargs for
    :func:`_init_worker_shm`: block names plus element counts, because macOS
    rounds block sizes up to a page so the buffer length alone is ambiguous.
    """
    ids = list(graph)
    index = {v: i for i, v in enumerate(ids)}
    indptr = array("q", [0])
    indices = array("q")
    for v in ids:
        indices.extend(index[w] for w in graph[v])
        indptr.append(len(indices))
    arrays = {
        "ids": array("q", ids),
        "indptr": indptr,
        "indices": indices,
        "order": array("q", (index[v] for v in ordering)),
    }
    blocks = []
    meta = []
    for arr in arrays.values():
        shm = shared_memory.SharedMemory(create=True, size=max(len(arr) * 8, 8))
        shm.buf[: len(arr) * 8] = arr.tobytes()
        blocks.append(shm)
        meta.append((shm.name, len(arr)))
    return blocks, tuple(meta)


def _init_worker_shm(meta: tuple) -> None:
    views = []
    shms = []
    try:
        for name, count in meta:
            shm = shared_memory.SharedMemory(name=name)
            shms.append(shm)
            mv = shm.buf.cast("q")
            views.append(mv[:count].tolist())
            mv.release()
        ids, indptr, indices, order = views
    finally:
        for shm in shms:
            shm.close()
    graph = {
        ids[i]: {ids[j] for j in indices[indptr[i] : indptr[i + 1]]}
        for i in range(len(ids))
    }
    ordering = [ids[j] for j in order]
    _init_worker(graph, ordering)


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
    blocks, meta = _pack(graph, ordering)
    try:
        ctx = get_context("spawn")
        with ctx.Pool(workers, initializer=_init_worker_shm, initargs=(meta,)) as pool:
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
    finally:
        for shm in blocks:
            shm.close()
            shm.unlink()

    return PhaseProfile(
        ordering_s=ordering_s,
        startup_s=startup_s,
        compute_s=compute_s,
        cliques=count,
        largest=largest,
        worker_busy=worker_busy,
        batches=len(batches),
    )
