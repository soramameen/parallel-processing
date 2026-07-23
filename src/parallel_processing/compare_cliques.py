"""Head-to-head timing of Tomita CLIQUES vs. Eppstein on varied graph shapes.

Runs both sequential counters (and optionally the parallel Eppstein) on a
suite of synthetic graphs spanning low to high degeneracy, plus any edge-list
files given on the command line. Clique counts are asserted equal across the
implementations, so every run doubles as a cross-check.

Usage::

    python -m parallel_processing.compare_cliques [--parallel N] [edge-list ...]
"""

from __future__ import annotations

import sys
import time
from collections.abc import Callable
from pathlib import Path

from parallel_processing.cliques import count_cliques
from parallel_processing.eppstein import (
    Graph,
    count_eppstein_cliques,
    degeneracy_ordering,
)
from parallel_processing.eppstein_parallel import count_eppstein_cliques_parallel
from parallel_processing.graph_gen import (
    barabasi_albert,
    dense_random,
    erdos_renyi,
    grid_2d,
    moon_moser,
    random_tree,
)
from parallel_processing.graph_io import edge_count, load_edge_list

# Sizes are tuned so the slower algorithm stays in the tens of seconds on a
# laptop; the shapes, not the absolute times, are the point.
SUITE: list[tuple[str, Callable[[], Graph]]] = [
    ("tree n=20k", lambda: random_tree(20_000, seed=1)),
    ("grid 100x100", lambda: grid_2d(100, 100)),
    ("er-sparse n=20k deg=10", lambda: erdos_renyi(20_000, 10, seed=1)),
    ("ba-hubs n=20k m=5", lambda: barabasi_albert(20_000, 5, seed=1)),
    ("er-dense n=120 p=0.5", lambda: dense_random(120, 0.5, seed=1)),
    ("moon-moser k=11 (n=33)", lambda: moon_moser(11)),
]


def _time(fn: Callable[[], tuple[int, int]]) -> tuple[float, int, int]:
    start = time.perf_counter()
    count, largest = fn()
    return time.perf_counter() - start, count, largest


def run_one(
    name: str, graph: Graph, parallel_workers: int | None, repeat: int = 1
) -> None:
    """Time each implementation on ``graph`` and print one aligned block.

    With ``repeat`` > 1 the two algorithms are timed alternately per round,
    so slow machine phases hit both equally; the headline number is the
    minimum, the standard noise-resistant statistic for benchmarks.
    """
    _, d = degeneracy_ordering(graph)
    tomita_runs: list[float] = []
    eppstein_runs: list[float] = []
    for _ in range(repeat):
        tomita_s, count, largest = _time(lambda: count_cliques(graph))
        eppstein_s, e_count, _ = _time(lambda: count_eppstein_cliques(graph))
        assert e_count == count, f"{name}: eppstein {e_count} != tomita {count}"
        tomita_runs.append(tomita_s)
        eppstein_runs.append(eppstein_s)
    tomita_s, eppstein_s = min(tomita_runs), min(eppstein_runs)

    reps = ""
    if repeat > 1:
        reps = (
            f"  [tomita {'/'.join(f'{t:.2f}' for t in tomita_runs)}"
            f" | eppstein {'/'.join(f'{t:.2f}' for t in eppstein_runs)}]"
        )
    line = (
        f"{name:26} n={len(graph):>7,} m={edge_count(graph):>9,} d={d:>3} "
        f"cliques={count:>11,} q={largest:>3} "
        f"tomita={tomita_s:>8.3f}s eppstein={eppstein_s:>8.3f}s "
        f"ratio={tomita_s / eppstein_s:>5.2f}x{reps}"
    )
    if parallel_workers is not None:
        par_s, p_count, _ = _time(
            lambda: count_eppstein_cliques_parallel(graph, parallel_workers)
        )
        assert p_count == count, f"{name}: parallel {p_count} != tomita {count}"
        line += f" par{parallel_workers}={par_s:>8.3f}s"
    print(line, flush=True)


def main(argv: list[str] | None = None) -> None:
    """CLI entry point; ``argv`` defaults to ``sys.argv[1:]``."""
    args = list(sys.argv[1:] if argv is None else argv)
    parallel_workers: int | None = None
    if "--parallel" in args:
        i = args.index("--parallel")
        parallel_workers = int(args[i + 1])
        del args[i : i + 2]
    repeat = 1
    if "--repeat" in args:
        i = args.index("--repeat")
        repeat = int(args[i + 1])
        del args[i : i + 2]

    print(
        f"ratio = tomita / eppstein (min of {repeat}); >1 means eppstein is faster",
        flush=True,
    )
    for name, factory in SUITE:
        run_one(name, factory(), parallel_workers, repeat)
    for path in args:
        run_one(Path(path).name, load_edge_list(path), parallel_workers, repeat)


if __name__ == "__main__":
    main()
