"""Measurement harness for the parallel Eppstein enumeration on SNAP data.

Same report format as :mod:`parallel_processing.benchmark_eppstein` plus the
worker count, so sequential and parallel runs compare line-for-line.

Usage::

    python -m parallel_processing.benchmark_eppstein_parallel [path] [workers]

``workers`` defaults to the CPU count.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from parallel_processing.benchmark_eppstein import DEFAULT_DATASET, EXPECTED_CLIQUES
from parallel_processing.eppstein_parallel import count_eppstein_cliques_parallel
from parallel_processing.graph_io import edge_count, load_edge_list


def run(path: str | Path, workers: int) -> None:
    """Load ``path``, enumerate maximal cliques in parallel, and print timings."""
    path = Path(path)
    print(f"dataset: {path}")
    print(f"workers: {workers}")

    load_start = time.perf_counter()
    graph = load_edge_list(path)
    load_elapsed = time.perf_counter() - load_start
    print(f"vertices: {len(graph):,}")
    print(f"edges:    {edge_count(graph):,}")
    print(f"load time: {load_elapsed:.3f} s")

    enum_start = time.perf_counter()
    count, largest = count_eppstein_cliques_parallel(graph, workers)
    enum_elapsed = time.perf_counter() - enum_start
    print(f"maximal cliques: {count:,}")
    print(f"largest clique:  {largest}")
    print(f"enumeration time: {enum_elapsed:.3f} s")

    for prefix, expected in EXPECTED_CLIQUES.items():
        if path.name.startswith(prefix):
            print(f"expected (Table 1): {expected:,} (diff {count - expected:+,})")
            break


def main(argv: list[str] | None = None) -> None:
    """CLI entry point; ``argv`` defaults to ``sys.argv[1:]``."""
    args = sys.argv[1:] if argv is None else argv
    path = args[0] if args else DEFAULT_DATASET
    workers = int(args[1]) if len(args) > 1 else os.cpu_count() or 1
    run(path, workers)


if __name__ == "__main__":
    main()
