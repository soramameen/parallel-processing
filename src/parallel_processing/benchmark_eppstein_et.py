"""Eppstein with and without clique early termination, side by side.

Runs :func:`eppstein.count_eppstein_cliques` and
:func:`eppstein_et.count_eppstein_cliques_et` (the test at every call, and
at the outer vertices only) alternately in one process,
``repeat`` times each, and reports the minimum of each (the repo's
protocol against slow spells of the host). Both must agree on the clique
count and the largest clique. Covers the synthetic suite of
:mod:`compare_cliques` plus any edge lists given.

Usage::

    python -m parallel_processing.benchmark_eppstein_et [--repeat 3] \
        [--skip-suite] [edge-list ...]
"""

from __future__ import annotations

import sys
import time
from collections.abc import Callable
from pathlib import Path

from parallel_processing.compare_cliques import SUITE
from parallel_processing.eppstein import Graph, count_eppstein_cliques
from parallel_processing.eppstein_et import count_eppstein_cliques_et
from parallel_processing.graph_io import load_edge_list


def _time(
    fn: Callable[[Graph], tuple[int, int]], graph: Graph
) -> tuple[float, int, int]:
    start = time.perf_counter()
    count, largest = fn(graph)
    return time.perf_counter() - start, count, largest


def _root_only(graph: Graph) -> tuple[int, int]:
    return count_eppstein_cliques_et(graph, deep=False)


def run(name: str, graph: Graph, repeat: int) -> None:
    plain: list[float] = []
    early: list[float] = []
    root: list[float] = []
    result = None
    for _ in range(repeat):
        for fn, times in (
            (count_eppstein_cliques, plain),
            (count_eppstein_cliques_et, early),
            (_root_only, root),
        ):
            t, count, largest = _time(fn, graph)
            if result is None:
                result = (count, largest)
            assert (count, largest) == result, f"{name}: {(count, largest)} != {result}"
            times.append(t)
    assert result is not None
    print(
        f"{name:26} cliques={result[0]:>11,} largest={result[1]:>3} "
        f"eppstein={min(plain):8.3f}s every-call={min(early):8.3f}s "
        f"({min(plain) / min(early):4.2f}x) root-only={min(root):8.3f}s "
        f"({min(plain) / min(root):4.2f}x)",
        flush=True,
    )


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    repeat = 3
    if "--repeat" in args:
        i = args.index("--repeat")
        repeat = int(args[i + 1])
        del args[i : i + 2]
    skip_suite = "--skip-suite" in args
    if skip_suite:
        args.remove("--skip-suite")
    print(f"min of {repeat} alternating runs each", flush=True)
    if not skip_suite:
        for name, factory in SUITE:
            run(name, factory(), repeat)
    for path in args:
        run(Path(path).name, load_edge_list(path), repeat)


if __name__ == "__main__":
    main()
