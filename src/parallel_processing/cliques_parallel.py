"""Naive root-split parallel version of Tomita's CLIQUES (candidate 2 in
``docs/plans/cliques-parallelization-ideas.md``).

The sequential kernel in :mod:`parallel_processing.cliques` is used
unchanged; only the top-level branching is distributed across processes.
Each branch of the root's ``CAND \\ Γ(pivot)`` becomes one independent task,
since every maximal clique containing vertex ``p`` at the root is confined to
that branch's subtree. Workers return ``(local_count, local_largest)`` and
the parent reduces with ``sum``/``max`` — no shared counter, per the
correctness notes in the design doc (an int counter would serialise ~22M
leaves through lock contention).

Run as a module to compare against the sequential count on a sample graph::

    python -m parallel_processing.cliques_parallel
"""

from __future__ import annotations

import os
import sys
from concurrent.futures import ProcessPoolExecutor

from parallel_processing.cliques import Graph

# Set once per worker process by _init_worker; avoids re-pickling the graph
# for every task (ProcessPoolExecutor.map would otherwise send it per-call).
_GRAPH: Graph | None = None


def _init_worker(graph: Graph) -> None:
    global _GRAPH
    _GRAPH = graph
    sys.setrecursionlimit(max(sys.getrecursionlimit(), len(graph) + 1000))


def _branch_task(subg: set[int], cand: set[int]) -> tuple[int, int]:
    """Count maximal cliques within one root branch; depth starts at 1
    because the branch's root vertex is already implicitly in ``Q``."""
    graph = _GRAPH
    assert graph is not None
    count = 0
    largest = 0

    def expand(subg: set[int], cand: set[int], depth: int) -> None:
        nonlocal count, largest
        if not subg:
            count += 1
            if depth > largest:
                largest = depth
            return
        pivot = max(subg, key=lambda u: len(cand & graph.get(u, set())))
        ext = cand - graph.get(pivot, set())
        for p in list(ext):
            neighbours = graph.get(p, set())
            expand(subg & neighbours, cand & neighbours, depth + 1)
            cand = cand - {p}

    expand(subg, cand, 1)
    return count, largest


def _root_branches(graph: Graph) -> list[tuple[set[int], set[int]]]:
    """Split the root level exactly as the sequential ``expand`` would,
    reproducing the same ``cand -= {p}`` sibling order (design doc, "共通する
    正しさの条件")."""
    subg = set(graph)
    cand = set(graph)
    pivot = max(subg, key=lambda u: len(cand & graph.get(u, set())))
    ext = cand - graph.get(pivot, set())
    branches: list[tuple[set[int], set[int]]] = []
    for p in ext:
        neighbours = graph.get(p, set())
        branches.append((subg & neighbours, cand & neighbours))
        cand = cand - {p}
    return branches


def count_cliques_parallel_root(
    graph: Graph, workers: int | None = None
) -> tuple[int, int]:
    """Count maximal cliques, parallelising over the root-level branches.

    Returns ``(count, largest)`` exactly like
    :func:`parallel_processing.cliques.count_cliques`. ``workers`` defaults to
    :func:`os.cpu_count`.
    """
    if not graph:
        return 1, 0

    branches = _root_branches(graph)
    workers = workers or os.cpu_count() or 1
    subgs, cands = zip(*branches, strict=True)

    with ProcessPoolExecutor(
        max_workers=workers, initializer=_init_worker, initargs=(graph,)
    ) as executor:
        results = list(executor.map(_branch_task, subgs, cands))

    count = sum(c for c, _ in results)
    largest = max((size for _, size in results), default=0)
    return count, largest


def main() -> None:
    """Run the parallel counter on the same sample graph as ``cliques.main``."""
    from parallel_processing.cliques import count_cliques

    graph: Graph = {
        1: {2, 5},
        2: {1, 3, 5},
        3: {2, 4},
        4: {3, 5, 6},
        5: {1, 2, 4},
        6: {4},
    }

    seq = count_cliques(graph)
    par = count_cliques_parallel_root(graph, workers=2)
    print(f"sequential: {seq}")
    print(f"parallel:   {par}")
    print("MATCH" if seq == par else "MISMATCH")


if __name__ == "__main__":
    main()
