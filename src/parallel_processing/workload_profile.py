"""Per-vertex workload profiler for the Eppstein outer loop.

Root-split parallelisation treats each vertex of the degeneracy ordering as
one task, so its achievable speed-up is bounded by how evenly the work is
spread over those tasks. This profiler times every outer vertex's subproblem
separately and reports how concentrated the work is ("the top 1% of vertices
carry X% of the time"), turning the straggler hypothesis from an anecdote
into data. The per-vertex CSV also records ``|P|`` as a candidate cheap
predictor for cost-model scheduling experiments.

Usage::

    python -m parallel_processing.workload_profile [path-to-edge-list]

Writes ``artifacts/workload-<dataset>.csv`` and prints a summary.
"""

from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

from parallel_processing import eppstein_parallel
from parallel_processing.benchmark_eppstein import DEFAULT_DATASET
from parallel_processing.eppstein import Graph, degeneracy_ordering
from parallel_processing.eppstein_parallel import _count_pivot, _init_worker
from parallel_processing.graph_io import load_edge_list

# One profile row per outer vertex: (pos, vertex, degree, |P|, cliques, seconds).
Row = tuple[int, int, int, int, int, float]


def profile(graph: Graph) -> list[Row]:
    """Time each outer vertex's subproblem; return one row per vertex.

    Runs the same per-vertex search as the parallel workers (via
    ``eppstein_parallel._count_pivot`` on its module globals), so the
    measured times are the task costs a scheduler would actually see.
    """
    ordering, _ = degeneracy_ordering(graph)
    _init_worker(graph, ordering)
    position = eppstein_parallel._position
    rows: list[Row] = []
    for pos, v in enumerate(ordering):
        p = {w for w in graph[v] if position[w] > pos}
        x = {w for w in graph[v] if position[w] < pos}
        p_size = len(p)
        start = time.perf_counter()
        cliques, _ = _count_pivot(p, x, 1)
        elapsed = time.perf_counter() - start
        rows.append((pos, v, len(graph[v]), p_size, cliques, elapsed))
    return rows


def _share_summary(label: str, weights: list[float]) -> None:
    """Print what share of ``sum(weights)`` the heaviest vertices carry."""
    total = sum(weights)
    if total <= 0:
        print(f"{label}: total is zero, no concentration to report")
        return
    ordered = sorted(weights, reverse=True)
    n = len(ordered)
    print(f"{label} concentration (n={n:,}, total={total:,.3f}):")
    print(f"  heaviest vertex : {ordered[0] / total:7.2%}")
    for pct in (0.001, 0.01, 0.10):
        k = max(1, int(n * pct))
        share = sum(ordered[:k]) / total
        print(f"  top {pct:6.1%} ({k:>7,} vertices): {share:7.2%}")


def _time_histogram(times: list[float]) -> None:
    """Print a log-binned histogram of per-vertex times (decades of seconds)."""
    bins: dict[int, int] = {}
    for t in times:
        # Everything below 1 µs is one "trivial" bin; -21 marks exact zeros.
        decade = -21
        if t >= 1e-6:
            decade = 0
            while t < 1:
                t *= 10
                decade -= 1
        bins[decade] = bins.get(decade, 0) + 1
    print("per-vertex time histogram (log bins):")
    width = max(bins.values())
    for decade in sorted(bins):
        label = "< 1 µs" if decade == -21 else f"1e{decade} - 1e{decade + 1} s"
        count = bins[decade]
        bar = "#" * max(1, round(count / width * 50))
        print(f"  {label:>15}: {count:>8,} {bar}")


def run(path: str | Path) -> None:
    """Profile ``path`` per outer vertex, write the CSV, print the summary."""
    path = Path(path)
    print(f"dataset: {path}")
    graph = load_edge_list(path)

    wall_start = time.perf_counter()
    rows = profile(graph)
    wall = time.perf_counter() - wall_start

    out = Path("artifacts") / f"workload-{path.name.split('.')[0]}.csv"
    out.parent.mkdir(exist_ok=True)
    with out.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["pos", "vertex", "degree", "p_size", "cliques", "seconds"])
        writer.writerows(rows)

    total_cliques = sum(r[4] for r in rows)
    total_time = sum(r[5] for r in rows)
    print(f"vertices: {len(rows):,}")
    print(f"total cliques (sum over vertices): {total_cliques:,}")
    print(f"summed subproblem time: {total_time:.3f} s (wall {wall:.3f} s)")
    _share_summary("time", [r[5] for r in rows])
    _share_summary("cliques", [float(r[4]) for r in rows])
    _time_histogram([r[5] for r in rows])
    print(f"csv: {out}")


def main(argv: list[str] | None = None) -> None:
    """CLI entry point; ``argv`` defaults to ``sys.argv[1:]``."""
    args = sys.argv[1:] if argv is None else argv
    run(args[0] if args else DEFAULT_DATASET)


if __name__ == "__main__":
    main()
