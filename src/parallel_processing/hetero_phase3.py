"""Phase 3 schedules on emulated asymmetric cores (docs/plans/hetero-cores.md).

Every schedule runs on the pull executor (:func:`hetero.profile_pull`), so
they differ only in how tasks are formed and which core may take them:

- ``block[K]`` / ``interleave``: the M4 batch shapes, one shared queue.
- ``lpt``: single vertices in descending *predicted* cost, packed into tasks
  of bounded predicted cost, one shared queue. Needs no core speeds.
- ``lpt-oracle``: the same ordered by *measured* cost (a best case for how
  good the cost ordering can be).
- ``static@R`` / ``static-oracle@R``: speed-weighted LPT assigns every vertex
  to one core up front, assuming slow cores run at ``R``. With the true r it
  is the textbook best static schedule; with a wrong ``R`` it measures what
  a misestimated core speed costs.
- ``giants``: like ``lpt``, but the few tasks predicted above 1/(8w) of all
  work sit in a queue only fast cores serve (first), so a giant cannot land
  on a slow core. Needs to know which cores are fast, not how fast.
- ``split``: like ``lpt``, but those giant vertices are cut into their
  first-level branches (:func:`hetero.split_root`) before ordering.
- ``split-giants``: both.

Costs: measured per-vertex seconds come from a ``workload_profile`` CSV of
the same graph on this host; the prediction is ``exp(a + b*|P|)`` fitted to
that CSV over ``|P| >= 5`` (a within-graph fit, so an optimistic predictor).

Usage::

    python -m parallel_processing.hetero_phase3 --graph G --workload CSV \
        --cores F,F,S,S --r 0.43 --schedules lpt,static-oracle@0.43 \
        [--fast-scale 1,1,0.8] [--period 4000] [--repeat 3] [--tag T]
"""

from __future__ import annotations

import csv
import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from parallel_processing import hetero, sched_sim
from parallel_processing.benchmark_hetero import OUT_DIR, steal_seconds
from parallel_processing.eppstein import Graph, degeneracy_ordering
from parallel_processing.graph_io import load_edge_list

CSV_PATH = OUT_DIR / "phase3.csv"
FIELDS = [
    "timestamp",
    "tag",
    "graph",
    "cores",
    "speeds",
    "r",
    "schedule",
    "period_us",
    "fast_scale",
    "run",
    "compute_s",
    "startup_s",
    "cliques",
    "tasks_total",
    "busy",
    "items",
    "tasks",
    "idle_pct",
    "idle_weighted_pct",
    "steal_s",
]

# Tasks are packed until their predicted cost reaches total / (TASKS_PER_CORE
# * workers); cheap vertices therefore travel in large groups, heavy ones
# alone. Capped so a task never holds more than MAX_ITEMS vertices.
TASKS_PER_CORE = 64
MAX_ITEMS = 2048
# A vertex predicted above total / (GIANT_SHARE * workers) is a "giant".
GIANT_SHARE = 8


@dataclass
class Costs:
    measured: list[float]
    predicted: list[float]
    p_size: list[int]


def fit_predictor(p_size: list[int], seconds: list[float]) -> tuple[float, float]:
    """Least-squares fit of log(seconds) = a + b*|P| over |P| >= 5."""
    pts = [(p, math.log(s)) for p, s in zip(p_size, seconds) if p >= 5 and s > 0]
    mx = sum(p for p, _ in pts) / len(pts)
    my = sum(y for _, y in pts) / len(pts)
    b = sum((p - mx) * (y - my) for p, y in pts) / sum((p - mx) ** 2 for p, _ in pts)
    return my - b * mx, b


def load_costs(workload_csv: str | Path) -> tuple[Costs, tuple[float, float]]:
    w = sched_sim.Workload.from_csv(workload_csv)
    a, b = fit_predictor(w.p_size, w.seconds)
    predicted = [math.exp(a + b * p) for p in w.p_size]
    return Costs(w.seconds, predicted, w.p_size), (a, b)


def pack(items: list[hetero.Item], cost: list[float], cap: float) -> list[hetero.Task]:
    """Group consecutive items into tasks of predicted cost up to ``cap``."""
    tasks: list[hetero.Task] = []
    current: hetero.Task = []
    acc = 0.0
    for item, c in zip(items, cost):
        if current and (acc + c > cap or len(current) >= MAX_ITEMS):
            tasks.append(current)
            current, acc = [], 0.0
        current.append(item)
        acc += c
    if current:
        tasks.append(current)
    return tasks


def branch_items(
    graph: Graph,
    ordering: list[int],
    position: dict[int, int],
    i: int,
    a: float,
    b: float,
) -> list[tuple[hetero.Item, float]]:
    """Vertex ``i`` as its first-level branches, each with a predicted cost
    from the branch's own candidate-set size."""
    root = hetero.split_root(graph, ordering, position, i)
    if root is None or not root[2]:
        return []
    p, _, branches = root
    out: list[tuple[hetero.Item, float]] = []
    for j, v in enumerate(branches):
        out.append(((i, j), math.exp(a + b * len(p & graph[v]))))
        p = p - {v}
    return out


def build(
    name: str,
    speeds: list[float],
    costs: Costs,
    graph: Graph,
    ordering: list[int],
    fit: tuple[float, float],
) -> tuple[list[list[hetero.Task]], list[list[int]]]:
    """(queues, poll) for schedule ``name`` on cores ``speeds``."""
    n = len(ordering)
    w = len(speeds)
    shared = [[0]] * w
    fast = [c for c, s in enumerate(speeds) if s >= 1]

    if name.startswith("block"):
        size = int(name[len("block"):] or 64)
        return [[list(b) for b in hetero.make_batches(n, "block", size)]], shared
    if name == "interleave":
        return [[list(b) for b in hetero.make_batches(n, "interleave", 64)]], shared

    if name.startswith("static"):
        base, r_hat = name.split("@")
        c = costs.measured if base == "static-oracle" else costs.predicted
        assumed = [1.0 if s >= 1 else float(r_hat) for s in speeds]
        lists = sched_sim.lpt_assign(c, assumed)
        queues: list[list[hetero.Task]] = [
            [list[hetero.Item](lst[k : k + 64]) for k in range(0, len(lst), 64)]
            for lst in lists
        ]
        return queues, [[q] for q in range(w)]

    c = costs.measured if name == "lpt-oracle" else costs.predicted
    total = sum(c)
    giant = total / (GIANT_SHARE * w)
    entries: list[tuple[hetero.Item, float]] = [(i, c[i]) for i in range(n)]
    if name in ("split", "split-giants"):
        position = {v: i for i, v in enumerate(ordering)}
        entries = []
        for i in range(n):
            parts = []
            if c[i] > giant:
                parts = branch_items(graph, ordering, position, i, *fit)
            entries.extend(parts or [(i, c[i])])
    entries.sort(key=lambda e: -e[1])
    cap = total / (TASKS_PER_CORE * w)

    if name in ("giants", "split-giants"):
        heavy = [e for e in entries if e[1] > giant]
        light = [e for e in entries if e[1] <= giant]
        q_heavy = [[item] for item, _ in heavy]
        q_light = pack([i for i, _ in light], [x for _, x in light], cap)
        poll = [[0, 1] if c_ in fast else [1] for c_ in range(w)]
        return [q_heavy, q_light], poll
    if name in ("lpt", "lpt-oracle", "split"):
        return [pack([i for i, _ in entries], [x for _, x in entries], cap)], shared
    raise ValueError(f"unknown schedule {name!r}")


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)

    def take(flag: str, default: str | None = None) -> str:
        if flag in args:
            i = args.index(flag)
            value = args[i + 1]
            del args[i : i + 2]
            return value
        if default is None:
            sys.exit(f"missing {flag}")
        return default

    graph_path = Path(take("--graph"))
    workload = take("--workload")
    spec = take("--cores", "F,F,S,S")
    r = float(take("--r", "0.43"))
    schedules = take("--schedules").split(",")
    fs = take("--fast-scale", "")
    fast_scale = [float(x) for x in fs.split(",")] if fs else None
    period = int(take("--period", str(hetero.DEFAULT_PERIOD_US)))
    repeat = int(take("--repeat", "3"))
    tag = take("--tag", "")
    if not hetero.cgroups_available():
        sys.exit(f"cgroup-v1 cpu controller not writable at {hetero.CGROUP_ROOT}")

    graph = load_edge_list(graph_path)
    ordering, _ = degeneracy_ordering(graph)
    costs, fit = load_costs(workload)
    assert len(costs.measured) == len(ordering), "workload CSV is for another graph"
    speeds = hetero.parse_cores(spec, r)
    plans = {s: build(s, speeds, costs, graph, ordering, fit) for s in schedules}
    print(f"predictor: log t = {fit[0]:.3f} + {fit[1]:.4f}*|P|", flush=True)

    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    new_file = not CSV_PATH.exists()
    expected: int | None = None
    with CSV_PATH.open("a", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        for run_idx in range(repeat):
            for name in schedules:
                queues, poll = plans[name]
                steal = steal_seconds()
                p = hetero.profile_pull(
                    graph, speeds, queues, poll, period, fast_scale, ordering=ordering
                )
                steal = steal_seconds() - steal
                if expected is None:
                    expected = p.cliques
                assert p.cliques == expected, f"{name}: {p.cliques} != {expected}"
                plain = 100 * (1 - sum(p.busy) / (len(p.busy) * p.compute_s))
                cap = sum(speeds) * p.compute_s
                weighted = 100 * (1 - sum(b * s for b, s in zip(p.busy, speeds)) / cap)
                writer.writerow(
                    {
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                        "tag": tag,
                        "graph": graph_path.name,
                        "cores": spec,
                        "speeds": ";".join(f"{s:g}" for s in speeds),
                        "r": r,
                        "schedule": name,
                        "period_us": period,
                        "fast_scale": fs,
                        "run": run_idx,
                        "compute_s": f"{p.compute_s:.4f}",
                        "startup_s": f"{p.startup_s:.4f}",
                        "cliques": p.cliques,
                        "tasks_total": p.batches,
                        "busy": ";".join(f"{b:.4f}" for b in p.busy),
                        "items": ";".join(map(str, p.vertices)),
                        "tasks": ";".join(map(str, p.tasks)),
                        "idle_pct": f"{plain:.2f}",
                        "idle_weighted_pct": f"{weighted:.2f}",
                        "steal_s": f"{steal:.2f}",
                    }
                )
                handle.flush()
                print(
                    f"{graph_path.name:24} run={run_idx} {spec} r={r} {name:18} "
                    f"compute={p.compute_s:8.3f}s idle={plain:5.1f}% "
                    f"idle_w={weighted:5.1f}% busy="
                    f"{'/'.join(f'{b:.1f}' for b in p.busy)} "
                    f"tasks={p.batches} steal={steal:.2f}s",
                    flush=True,
                )


if __name__ == "__main__":
    main()
