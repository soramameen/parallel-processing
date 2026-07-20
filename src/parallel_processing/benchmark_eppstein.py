"""Measurement harness for the Eppstein-Löffler-Strash algorithm on SNAP data.

Loads an edge list, computes the degeneracy ordering, enumerates all maximal
cliques, and reports the load / ordering / enumeration times, the vertex and
edge counts, the degeneracy, and the number of cliques found.

The expected clique counts mirror :mod:`parallel_processing.benchmark`, so a
run here can be compared line-for-line against the Tomita CLIQUES baseline.

Usage::

    python -m parallel_processing.benchmark_eppstein [path-to-edge-list]
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from parallel_processing.eppstein import count_eppstein_cliques, degeneracy_ordering
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

    # The ordering is recomputed inside the enumeration; timing it separately
    # here shows how cheap it is relative to the search itself.
    order_start = time.perf_counter()
    _, degeneracy = degeneracy_ordering(graph)
    order_elapsed = time.perf_counter() - order_start
    print(f"degeneracy: {degeneracy}")
    print(f"ordering time: {order_elapsed:.3f} s")

    enum_start = time.perf_counter()
    count, largest = count_eppstein_cliques(graph)
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
    run(path)


if __name__ == "__main__":
    main()
