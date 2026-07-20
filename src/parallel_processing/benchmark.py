"""Measurement harness for Tomita's CLIQUES on a SNAP dataset.

Loads an edge list, enumerates all maximal cliques, and reports the load and
enumeration times, the vertex/edge counts, and the number of cliques found.

The default dataset is ca-AstroPh (SNAP co-authorship network). Table 1 of
Conte & Tomita (TCS 2022) reports **36,427** maximal cliques for it, so the
printed count can be eyeballed against that expected value.

Usage::

    python -m parallel_processing.benchmark [path-to-edge-list] [--workers N]

Passing ``--workers N`` switches enumeration to the naive root-split parallel
counter (:mod:`parallel_processing.cliques_parallel`) with ``N`` processes,
for comparing against the sequential run.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from parallel_processing.cliques import count_cliques
from parallel_processing.cliques_parallel import count_cliques_parallel_root
from parallel_processing.graph_io import edge_count, load_edge_list

DEFAULT_DATASET = "data/ca-AstroPh.txt.gz"

# Expected #cliques per dataset from Table 1 of Conte & Tomita (TCS 2022),
# keyed by filename prefix. Our counts differ by a handful because the SNAP
# files carry a few extra vertices vs. the paper's reported n.
EXPECTED_CLIQUES = {
    "ca-AstroPh": 36_427,
    "ca-HepPh": 14_937,
    "soc-sign-epinions": 22_226_172,
}


def run(path: str | Path, workers: int | None = None) -> None:
    """Load ``path``, enumerate maximal cliques, and print timing and counts.

    ``workers`` is ``None`` for the sequential counter, or a process count to
    use the root-split parallel counter instead.
    """
    path = Path(path)
    print(f"dataset: {path}")

    load_start = time.perf_counter()
    graph = load_edge_list(path)
    load_elapsed = time.perf_counter() - load_start
    print(f"vertices: {len(graph):,}")
    print(f"edges:    {edge_count(graph):,}")
    print(f"load time: {load_elapsed:.3f} s")

    enum_start = time.perf_counter()
    if workers is None:
        count, largest = count_cliques(graph)
        print("mode: sequential")
    else:
        count, largest = count_cliques_parallel_root(graph, workers=workers)
        print(f"mode: parallel (root-split, {workers} workers)")
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
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=DEFAULT_DATASET)
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="use the root-split parallel counter with N worker processes",
    )
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    run(args.path, workers=args.workers)


if __name__ == "__main__":
    main()
