"""Per-phase timing of the parallel Eppstein counter across graph shapes.

Breaks one parallel run into load / degeneracy ordering / pool startup /
compute, plus per-worker busy seconds, to show how much of the wall clock
the sequential preparation actually costs. Runs the synthetic suite of
:mod:`compare_cliques` plus any edge-list files given on the command line.

Usage::

    python -m parallel_processing.phase_profile \
        [--workers 1,2,4,8] [--batch 64] [--repeat 3] \
        [--strategy block|reversed|interleave] [--skip-suite] [edge-list ...]

Every run is appended to ``artifacts/phase-profile.csv``; stdout shows the
minimum-total run per (graph, workers), following the repeat-and-take-min
protocol of compare_cliques.
"""

from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

from parallel_processing import (
    eppstein_parallel,
    eppstein_parallel_interleave,
    eppstein_parallel_reversed,
)
from parallel_processing.compare_cliques import SUITE
from parallel_processing.eppstein_parallel import PhaseProfile
from parallel_processing.graph_io import edge_count, load_edge_list

CSV_PATH = Path("artifacts/phase-profile.csv")

# Each batch-distribution strategy lives in its own module (thin copies of
# eppstein_parallel) so the variants stay self-contained; here they are only
# looked up by name.
STRATEGIES = {
    "block": eppstein_parallel.profile_eppstein_parallel,
    "reversed": eppstein_parallel_reversed.profile_eppstein_parallel,
    "interleave": eppstein_parallel_interleave.profile_eppstein_parallel,
}

CSV_FIELDS = [
    "graph",
    "n",
    "m",
    "workers",
    "batch",
    "strategy",
    "run",
    "load_s",
    "ordering_s",
    "startup_s",
    "compute_s",
    "total_s",
    "cliques",
    "batches",
    "busy_max",
    "busy_min",
    "busy_sum",
]


def _total(p: PhaseProfile) -> float:
    return p.ordering_s + p.startup_s + p.compute_s


def _print_best(name: str, workers: int, load_s: float, best: PhaseProfile) -> None:
    busy = list(best.worker_busy.values())
    # Workers that never received a batch still count as capacity, so idle is
    # taken over `workers`, not over len(busy).
    idle = 1.0 - sum(busy) / (workers * best.compute_s) if best.compute_s > 0 else 0.0
    total = _total(best)
    print(
        f"{name:26} w={workers} "
        f"load={load_s:7.3f}s ord={best.ordering_s:7.3f}s "
        f"start={best.startup_s:6.3f}s compute={best.compute_s:8.3f}s "
        f"total={total:8.3f}s "
        f"ord%={100 * best.ordering_s / total:4.1f} "
        f"idle%={100 * idle:4.1f} "
        f"busy(max/min)={max(busy):7.3f}/{min(busy):7.3f}s "
        f"cliques={best.cliques:,}",
        flush=True,
    )


def run_graph(
    name: str,
    graph: dict[int, set[int]],
    load_s: float,
    workers_list: list[int],
    batch: int,
    strategy: str,
    repeat: int,
    writer: csv.DictWriter,
    csv_file,
) -> None:
    profile_fn = STRATEGIES[strategy]
    n, m = len(graph), edge_count(graph)
    expected: int | None = None
    for workers in workers_list:
        runs: list[PhaseProfile] = []
        for run_idx in range(repeat):
            p = profile_fn(graph, workers, batch)
            if expected is None:
                expected = p.cliques
            assert p.cliques == expected, (
                f"{name} w={workers}: {p.cliques} != {expected}"
            )
            runs.append(p)
            busy = list(p.worker_busy.values())
            writer.writerow(
                {
                    "graph": name,
                    "n": n,
                    "m": m,
                    "workers": workers,
                    "batch": batch,
                    "strategy": strategy,
                    "run": run_idx,
                    "load_s": f"{load_s:.4f}",
                    "ordering_s": f"{p.ordering_s:.4f}",
                    "startup_s": f"{p.startup_s:.4f}",
                    "compute_s": f"{p.compute_s:.4f}",
                    "total_s": f"{_total(p):.4f}",
                    "cliques": p.cliques,
                    "batches": p.batches,
                    "busy_max": f"{max(busy):.4f}",
                    "busy_min": f"{min(busy):.4f}",
                    "busy_sum": f"{sum(busy):.4f}",
                }
            )
            csv_file.flush()
        _print_best(name, workers, load_s, min(runs, key=_total))


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    workers_list = [1, 2, 4, 8]
    if "--workers" in args:
        i = args.index("--workers")
        workers_list = [int(w) for w in args[i + 1].split(",")]
        del args[i : i + 2]
    batch = 64
    if "--batch" in args:
        i = args.index("--batch")
        batch = int(args[i + 1])
        del args[i : i + 2]
    repeat = 1
    if "--repeat" in args:
        i = args.index("--repeat")
        repeat = int(args[i + 1])
        del args[i : i + 2]
    strategy = "block"
    if "--strategy" in args:
        i = args.index("--strategy")
        strategy = args[i + 1]
        if strategy not in STRATEGIES:
            sys.exit(f"unknown strategy {strategy!r}; choose from {sorted(STRATEGIES)}")
        del args[i : i + 2]
    skip_suite = False
    if "--skip-suite" in args:
        skip_suite = True
        args.remove("--skip-suite")

    CSV_PATH.parent.mkdir(exist_ok=True)
    new_file = not CSV_PATH.exists()
    with CSV_PATH.open("a", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
        if new_file:
            writer.writeheader()
        print(
            f"phase profile: batch={batch} strategy={strategy} repeat={repeat} "
            f"(stdout shows min-total run; all runs in {CSV_PATH})",
            flush=True,
        )
        if not skip_suite:
            for name, factory in SUITE:
                start = time.perf_counter()
                graph = factory()
                load_s = time.perf_counter() - start
                run_graph(
                    name,
                    graph,
                    load_s,
                    workers_list,
                    batch,
                    strategy,
                    repeat,
                    writer,
                    csv_file,
                )
        for path in args:
            start = time.perf_counter()
            graph = load_edge_list(path)
            load_s = time.perf_counter() - start
            run_graph(
                Path(path).name,
                graph,
                load_s,
                workers_list,
                batch,
                strategy,
                repeat,
                writer,
                csv_file,
            )


if __name__ == "__main__":
    main()
