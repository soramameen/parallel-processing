"""Per-vertex workload profiler for the Eppstein outer loop.

Root-split parallelisation treats each vertex of the degeneracy ordering as
one task, so its achievable speed-up is bounded by how evenly the work is
spread over those tasks. This profiler times every outer vertex's subproblem
separately and reports how concentrated the work is ("the top 1% of vertices
carry X% of the time"), turning the straggler hypothesis from an anecdote
into data. The per-vertex CSV also records ``|P|`` as a candidate cheap
predictor for cost-model scheduling experiments.

Usage::

    python -m parallel_processing.workload_profile [--out-dir DIR] [path-to-edge-list]
    python -m parallel_processing.workload_profile --branches K [--out-dir DIR] [path]
    python -m parallel_processing.workload_profile --early-termination [...] [path]

Writes ``<DIR>/workload-<dataset>.csv`` (``DIR`` defaults to ``artifacts``,
where the M4 profiles live) and prints a summary.
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


def profile(graph: Graph, early_termination: bool = False) -> list[Row]:
    """Time each outer vertex's subproblem; return one row per vertex.

    Runs the same per-vertex search as the parallel workers (via
    ``eppstein_parallel._count_pivot`` on its module globals), so the
    measured times are the task costs a scheduler would actually see.
    With ``early_termination`` the search is
    :func:`parallel_processing.eppstein_et.count_subproblem_et` instead.
    """
    from parallel_processing.eppstein_et import count_subproblem_et

    ordering, _ = degeneracy_ordering(graph)
    _init_worker(graph, ordering)
    position = eppstein_parallel._position
    rows: list[Row] = []
    for pos, v in enumerate(ordering):
        p = {w for w in graph[v] if position[w] > pos}
        x = {w for w in graph[v] if position[w] < pos}
        p_size = len(p)
        start = time.perf_counter()
        if early_termination:
            cliques = count_subproblem_et(graph, p, x)
        else:
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


def run(
    path: str | Path, out_dir: str | Path = "artifacts", early_termination: bool = False
) -> None:
    """Profile ``path`` per outer vertex, write the CSV, print the summary."""
    path = Path(path)
    print(f"dataset: {path}")
    graph = load_edge_list(path)

    wall_start = time.perf_counter()
    rows = profile(graph, early_termination)
    wall = time.perf_counter() - wall_start

    suffix = "-et" if early_termination else ""
    out = Path(out_dir) / f"workload-{path.name.split('.')[0]}{suffix}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
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


def profile_branches(graph: Graph, top: int) -> list[tuple[int, int, int, float]]:
    """Time each first-level branch of the ``top`` costliest outer vertices.

    The branches are the ones :func:`parallel_processing.hetero.split_root`
    defines, timed through the same code path the pull executor runs, so a
    simulator can price a split schedule. Rows are (pos, branch, |P| of the
    branch, seconds).
    """
    from parallel_processing import hetero

    rows = profile(graph)
    ordering, _ = degeneracy_ordering(graph)
    _init_worker(graph, ordering)
    position = eppstein_parallel._position
    heavy = sorted(rows, key=lambda r: -r[5])[:top]
    out = []
    for pos, *_ in heavy:
        root = hetero.split_root(graph, ordering, position, pos)
        if root is None:
            continue
        p, _, branches = root
        for j, v in enumerate(branches):
            size = len(p & graph[v])
            p = p - {v}
            start = time.perf_counter()
            hetero._count_item((pos, j))
            out.append((pos, j, size, time.perf_counter() - start))
    return out


def main(argv: list[str] | None = None) -> None:
    """CLI entry point; ``argv`` defaults to ``sys.argv[1:]``."""
    args = list(sys.argv[1:] if argv is None else argv)
    out_dir = "artifacts"
    if "--out-dir" in args:
        i = args.index("--out-dir")
        out_dir = args[i + 1]
        del args[i : i + 2]
    if "--branches" in args:
        i = args.index("--branches")
        top = int(args[i + 1])
        del args[i : i + 2]
        path = Path(args[0] if args else DEFAULT_DATASET)
        out = Path(out_dir) / f"branches-{path.name.split('.')[0]}.csv"
        branch_rows = profile_branches(load_edge_list(path), top)
        with out.open("w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["pos", "branch", "p_size", "seconds"])
            writer.writerows(branch_rows)
        print(f"{len(branch_rows)} branches of the {top} costliest vertices: {out}")
        return
    early = "--early-termination" in args
    if early:
        args.remove("--early-termination")
    run(args[0] if args else DEFAULT_DATASET, out_dir, early)


if __name__ == "__main__":
    main()

