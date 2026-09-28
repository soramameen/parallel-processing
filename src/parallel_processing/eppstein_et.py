"""Eppstein-Löffler-Strash with clique early termination.

Identical to :mod:`parallel_processing.eppstein` except for one test at the
top of every recursive call: when the candidate set ``P`` is itself a
clique, the subtree holds at most one maximal clique, ``R ∪ P``, so it is
reported (or rejected) directly instead of being walked.

Why that is enough: ``R ∪ P`` is a clique, and any ``R ∪ S`` with ``S`` a
proper subset of ``P`` extends by a vertex of ``P \\ S``, so only ``S = P``
can be maximal. It is maximal exactly when no ``x`` in ``X`` is adjacent
to all of ``P`` (every ``x`` is already adjacent to all of ``R``).

Why it is cheap: ``P`` is a clique iff every ``u`` in ``P`` sees the other
``|P| - 1``, so the Tomita pivot (the vertex of ``P ∪ X`` seeing most of
``P``) must see at least ``|P| - 1`` of them. Checking that costs one set
intersection per call; the full test runs only when it passes. A first
version reused the pivot scores through a dict instead and was 10-17%
slower on graphs where the test never fires, because it built the dict at
every call.

Without it, a clique-shaped ``P`` is walked as a chain: the pivot excludes
all but one branch at every level, so a ``P`` of size k costs k levels of
set intersections. On ca-HepPh the vertex carrying 13% of the work has a
238-vertex clique as its ``P`` (docs/hetero-experiments.md, 3d). The idea
is the simplest case of the early termination in Wang, Yu and Long,
"Maximal Clique Enumeration with Hybrid Branching and Early Termination"
(ICDE 2025, arXiv:2412.08218).
"""

from __future__ import annotations

import sys
from collections.abc import Callable

from parallel_processing.eppstein import Graph, _sort_cliques, degeneracy_ordering


def eppstein_cliques_et(graph: Graph) -> list[frozenset[int]]:
    """All maximal cliques, sorted like :func:`eppstein.eppstein_cliques`."""
    result: list[frozenset[int]] = []

    def report(q: list[int]) -> None:
        result.append(frozenset(q))

    _bron_kerbosch_degeneracy_et(graph, report)
    return _sort_cliques(result)


def count_eppstein_cliques_et(graph: Graph, deep: bool = True) -> tuple[int, int]:
    """Count maximal cliques; return (count, largest). Same result as
    :func:`eppstein.count_eppstein_cliques`.

    With ``deep=False`` the clique test runs only on the outer vertices'
    subproblems (the roots), where ca-HepPh's heavy vertex sits, and the
    search below them is the plain one; that keeps the per-call gate off
    graphs where the test never fires."""
    count = 0
    largest = 0

    def report(q: list[int]) -> None:
        nonlocal count, largest
        count += 1
        if len(q) > largest:
            largest = len(q)

    _bron_kerbosch_degeneracy_et(graph, report, deep)
    return count, largest


def count_subproblem_et(graph: Graph, p: set[int], x: set[int]) -> int:
    """Maximal cliques in one outer vertex's subproblem, with early
    termination; the per-vertex unit a profiler or parallel worker times."""
    count = 0

    def report(_: list[int]) -> None:
        nonlocal count
        count += 1

    _search(graph, [0], p, x, report)
    return count


def _search(
    graph: Graph,
    r: list[int],
    p: set[int],
    x: set[int],
    report: Callable[[list[int]], None],
    test: bool = True,
    deep: bool = True,
) -> None:
    """The recursive search below one outer vertex (``r`` holds it).

    ``test`` says whether this call runs the clique test, ``deep`` whether
    the calls below it do."""
    if not p and not x:
        report(r)
        return
    pivot = max(p | x, key=lambda u: len(p & graph[u]))
    size = len(p)
    # P can only be a clique if the best pivot sees all of P but itself;
    # that pre-check is one intersection, so the full test (every u in P
    # scoring |P| - 1) runs only on the rare clique-shaped candidates.
    if (
        test
        and size > 1
        and len(p & graph[pivot]) == size - 1
        and all(len(p & graph[u]) == size - 1 for u in p)
    ):
        # P is a clique: R ∪ P is this subtree's only candidate.
        if not any(p <= graph[u] for u in x):
            r.extend(p)
            report(r)
            del r[-size:]
        return
    for v in list(p - graph[pivot]):
        neighbours = graph[v]
        r.append(v)
        _search(graph, r, p & neighbours, x & neighbours, report, deep, deep)
        r.pop()
        p.discard(v)
        x.add(v)


def _bron_kerbosch_degeneracy_et(
    graph: Graph, report: Callable[[list[int]], None], deep: bool = True
) -> None:
    sys.setrecursionlimit(max(sys.getrecursionlimit(), len(graph) + 1000))

    r: list[int] = []

    ordering, _ = degeneracy_ordering(graph)
    position = {v: i for i, v in enumerate(ordering)}
    for v in ordering:
        pos = position[v]
        p = {w for w in graph[v] if position[w] > pos}
        x = {w for w in graph[v] if position[w] < pos}
        r.append(v)
        _search(graph, r, p, x, report, True, deep)
        r.pop()
