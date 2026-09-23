"""CLI for the emulated asymmetric-core experiments (see :mod:`hetero`).

Two subcommands::

    python -m parallel_processing.benchmark_hetero calibrate \
        [--speeds 1,0.75,0.5,0.43,0.26] [--periods 4000,10000,100000] \
        [--repeat 3] [edge-list]

    python -m parallel_processing.benchmark_hetero run \
        --cores "F,F,F,F;F,F,S,S" [--r 0.43,0.26] \
        [--strategy block,interleave] [--batch 64] [--period 10000] \
        [--repeat 3] [--tag LABEL] edge-list ...

``calibrate`` checks that a core capped at speed s really runs at s: it
times a pure integer loop and three slices of the graph's outer loop (the
heaviest vertex, a mid-weight block, a light block) on one core at each
speed and period, and reports effective speed = t(1) / t(s).

``run`` executes every (cores, r, strategy) combination ``repeat`` times,
cycling through the combinations inside each repeat so that slow spells of
the host hit all of them alike. Every run is appended to
``artifacts/linux/hetero.csv`` (calibration to ``hetero-calibration.csv``),
with the host's steal time over the run so noisy runs can be excluded.
"""

from __future__ import annotations

import csv
import multiprocessing
import sys
import time
from pathlib import Path

from parallel_processing import hetero
from parallel_processing.eppstein import Graph, degeneracy_ordering
from parallel_processing.graph_io import load_edge_list

OUT_DIR = Path("artifacts/linux")
RUN_CSV = OUT_DIR / "hetero.csv"
CALIBRATION_CSV = OUT_DIR / "hetero-calibration.csv"

RUN_FIELDS = [
    "timestamp",
    "tag",
    "graph",
    "cores",
    "speeds",
    "r",
    "strategy",
    "batch",
    "period_us",
    "run",
    "ordering_s",
    "startup_s",
    "compute_s",
    "cliques",
    "batches",
    "busy",
    "vertices",
    "tasks",
    "idle_pct",
    "idle_weighted_pct",
    "steal_s",
]

CALIBRATION_FIELDS = [
    "timestamp",
    "graph",
    "task",
    "speed",
    "period_us",
    "run",
    "seconds",
    "steal_s",
]


def steal_seconds() -> float:
    """Host steal time summed over all CPUs, from /proc/stat."""
    with open("/proc/stat") as f:
        fields = f.readline().split()
    return int(fields[8]) / 100  # USER_HZ is 100 on Linux


def _calibration_slices(n: int, heaviest: int) -> dict[str, range | list[int]]:
    """Outer-loop slices of different weight, by position in the ordering.

    The heavy vertices cluster at the tail of the degeneracy ordering
    (artifacts/workload-*.csv). On soc-sign-epinions the head 91% is ~0.3 s
    of tiny subproblems (|P| <= 13) on the M4 and a 2,000-vertex block at
    95% is ~0.5 s of mid-size ones (|P| <= 48), so each slice runs long
    enough to span many quota periods.
    """
    return {
        "loop": [],
        "heavy": [heaviest],
        "mid": range(int(n * 0.95), min(n, int(n * 0.95) + 2000)),
        "light": range(0, int(n * 0.91)),
    }


def _heaviest_position(graph: Graph, ordering: list[int]) -> int:
    """Position whose subproblem has the largest candidate set |P|."""
    position = {v: i for i, v in enumerate(ordering)}
    return max(
        range(len(ordering)),
        key=lambda i: sum(1 for w in graph[ordering[i]] if position[w] > i),
    )


def calibrate(args: list[str]) -> None:
    speeds = [1.0, 0.75, 0.5, 0.43, 0.26]
    # 4 ms is the shortest period the kernel lets express speed 0.26.
    periods = [4_000, 10_000, 100_000]
    repeat = 3
    args = list(args)
    if "--speeds" in args:
        i = args.index("--speeds")
        speeds = [float(s) for s in args[i + 1].split(",")]
        del args[i : i + 2]
    if "--periods" in args:
        i = args.index("--periods")
        periods = [int(p) for p in args[i + 1].split(",")]
        del args[i : i + 2]
    if "--repeat" in args:
        i = args.index("--repeat")
        repeat = int(args[i + 1])
        del args[i : i + 2]
    path = Path(args[0]) if args else Path("data/soc-sign-epinions.txt.gz")

    graph = load_edge_list(path)
    ordering, _ = degeneracy_ordering(graph)
    slices = _calibration_slices(len(ordering), _heaviest_position(graph, ordering))
    print(f"calibration on {path.name}: slices {{k: len}} =",
          {k: len(v) for k, v in slices.items()}, flush=True)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    new_file = not CALIBRATION_CSV.exists()
    with CALIBRATION_CSV.open("a", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CALIBRATION_FIELDS)
        if new_file:
            writer.writeheader()
        ctx = multiprocessing.get_context("spawn")
        for period in periods:
            best: dict[tuple[str, float], float] = {}
            with hetero.CoreGroups([1.0], period) as groups:
                slots = ctx.Queue()
                slots.put(0)
                paths = [str(p) for p in groups.paths]
                with ctx.Pool(
                    1,
                    initializer=hetero._init_worker,
                    initargs=(graph, ordering, slots, paths),
                ) as pool:
                    groups.wait_populated()
                    for run_idx in range(repeat):
                        for speed in speeds:
                            groups.set_speed(groups.paths[0], speed)
                            for kind, batch in slices.items():
                                steal = steal_seconds()
                                seconds = pool.apply(
                                    hetero._calibration_task, (kind, batch)
                                )
                                writer.writerow(
                                    {
                                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                        "graph": path.name,
                                        "task": kind,
                                        "speed": speed,
                                        "period_us": period,
                                        "run": run_idx,
                                        "seconds": f"{seconds:.4f}",
                                        "steal_s": f"{steal_seconds() - steal:.2f}",
                                    }
                                )
                                csv_file.flush()
                                key = (kind, speed)
                                best[key] = min(best.get(key, float("inf")), seconds)
            for kind in slices:
                base = best[(kind, 1.0)] if (kind, 1.0) in best else None
                row = [f"period={period:>6}us {kind:5} t(1)={base or 0:6.3f}s"]
                for speed in speeds:
                    t = best[(kind, speed)]
                    eff = base / t if base else float("nan")
                    row.append(f"s={speed:<4} eff={eff:5.3f}")
                print("  ".join(row), flush=True)


def _idle(p: hetero.HeteroProfile) -> tuple[float, float]:
    """Plain idle (cores as equals) and speed-weighted idle, in percent."""
    if p.compute_s <= 0:
        return 0.0, 0.0
    plain = 1 - sum(p.busy) / (len(p.busy) * p.compute_s)
    capacity = sum(p.speeds) * p.compute_s
    used = sum(b * s for b, s in zip(p.busy, p.speeds))
    return 100 * plain, 100 * (1 - used / capacity)


def run(args: list[str]) -> None:
    args = list(args)

    def take(flag: str, default: str) -> str:
        if flag in args:
            i = args.index(flag)
            value = args[i + 1]
            del args[i : i + 2]
            return value
        return default

    core_specs = take("--cores", "F,F,S,S").split(";")
    r_values = [float(r) for r in take("--r", "0.43").split(",")]
    strategies = take("--strategy", "block,interleave").split(",")
    batch = int(take("--batch", "64"))
    period = int(take("--period", str(hetero.DEFAULT_PERIOD_US)))
    repeat = int(take("--repeat", "3"))
    tag = take("--tag", "")
    if not args:
        sys.exit("give at least one edge list")
    for s in strategies:
        if s not in hetero.STRATEGIES:
            sys.exit(f"unknown strategy {s!r}; choose from {hetero.STRATEGIES}")

    # A spec with no S core does not depend on r: run it once per repeat.
    combos: list[tuple[str, float | None]] = []
    for spec in core_specs:
        if "S" in spec.split(","):
            combos.extend((spec, r) for r in r_values)
        else:
            combos.append((spec, None))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    new_file = not RUN_CSV.exists()
    with RUN_CSV.open("a", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=RUN_FIELDS)
        if new_file:
            writer.writeheader()
        for path in map(Path, args):
            graph = load_edge_list(path)
            expected: int | None = None
            for run_idx in range(repeat):
                for spec, r in combos:
                    speeds = hetero.parse_cores(spec, r if r is not None else 1.0)
                    for strategy in strategies:
                        steal = steal_seconds()
                        p = hetero.profile_hetero(
                            graph, speeds, strategy, batch, period
                        )
                        steal = steal_seconds() - steal
                        if expected is None:
                            expected = p.cliques
                        assert p.cliques == expected, f"{p.cliques} != {expected}"
                        idle, idle_w = _idle(p)
                        writer.writerow(
                            {
                                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                "tag": tag,
                                "graph": path.name,
                                "cores": spec,
                                "speeds": ";".join(f"{s:g}" for s in speeds),
                                "r": "" if r is None else r,
                                "strategy": strategy,
                                "batch": batch,
                                "period_us": period,
                                "run": run_idx,
                                "ordering_s": f"{p.ordering_s:.4f}",
                                "startup_s": f"{p.startup_s:.4f}",
                                "compute_s": f"{p.compute_s:.4f}",
                                "cliques": p.cliques,
                                "batches": p.batches,
                                "busy": ";".join(f"{b:.4f}" for b in p.busy),
                                "vertices": ";".join(map(str, p.vertices)),
                                "tasks": ";".join(map(str, p.tasks)),
                                "idle_pct": f"{idle:.2f}",
                                "idle_weighted_pct": f"{idle_w:.2f}",
                                "steal_s": f"{steal:.2f}",
                            }
                        )
                        csv_file.flush()
                        print(
                            f"{path.name:26} run={run_idx} cores={spec:9} "
                            f"r={'-' if r is None else r:<4} {strategy:10} "
                            f"compute={p.compute_s:8.3f}s idle={idle:5.1f}% "
                            f"idle_w={idle_w:5.1f}% "
                            f"busy={'/'.join(f'{b:.1f}' for b in p.busy)} "
                            f"steal={steal:.2f}s cliques={p.cliques:,}",
                            flush=True,
                        )


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    if not hetero.cgroups_available():
        sys.exit(f"cgroup-v1 cpu controller not writable at {hetero.CGROUP_ROOT}")
    if not args or args[0] not in ("calibrate", "run"):
        sys.exit("usage: benchmark_hetero {calibrate|run} ...")
    {"calibrate": calibrate, "run": run}[args[0]](args[1:])


if __name__ == "__main__":
    main()
