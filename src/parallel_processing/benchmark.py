"""Measurement harness for Tomita's CLIQUES on a SNAP dataset.

Loads an edge list, enumerates all maximal cliques, and reports the load and
enumeration times, the vertex/edge counts, and the number of cliques found.

The default dataset is ca-AstroPh (SNAP co-authorship network). Table 1 of
Conte & Tomita (TCS 2022) reports **36,427** maximal cliques for it, so the
printed count can be eyeballed against that expected value.

Usage::

    python -m parallel_processing.benchmark [path-to-edge-list]
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from parallel_processing.cliques import cliques
from parallel_processing.graph_io import edge_count, load_edge_list

DEFAULT_DATASET = "data/ca-AstroPh.txt.gz"

# Expected #cliques for ca-AstroPh from Table 1 of Conte & Tomita (TCS 2022).
CA_ASTROPH_EXPECTED_CLIQUES = 36_427


def run(path: str | Path) -> None:
    """Load ``path``, enumerate maximal cliques, and print timing and counts."""
    path = Path(path)
    print(f"dataset: {path}")

    load_start = time.perf_counter()
    graph = load_edge_list(path)
    load_elapsed = time.perf_counter() - load_start
    print(f"vertices: {len(graph):,}")
    print(f"edges:    {edge_count(graph):,}")
    print(f"load time: {load_elapsed:.3f} s")

    enum_start = time.perf_counter()
    found = cliques(graph)
    enum_elapsed = time.perf_counter() - enum_start
    largest = max((len(c) for c in found), default=0)
    print(f"maximal cliques: {len(found):,}")
    print(f"largest clique:  {largest}")
    print(f"enumeration time: {enum_elapsed:.3f} s")

    if path.name.startswith("ca-AstroPh"):
        match = len(found) == CA_ASTROPH_EXPECTED_CLIQUES
        print(
            f"expected (Table 1): {CA_ASTROPH_EXPECTED_CLIQUES:,} "
            f"-> {'MATCH' if match else 'MISMATCH'}"
        )


def main(argv: list[str] | None = None) -> None:
    """CLI entry point; ``argv`` defaults to ``sys.argv[1:]``."""
    args = sys.argv[1:] if argv is None else argv
    path = args[0] if args else DEFAULT_DATASET
    run(path)


if __name__ == "__main__":
    main()
