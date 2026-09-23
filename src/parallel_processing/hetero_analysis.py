"""Summaries and simulator checks for the emulated asymmetric-core runs.

Reads ``artifacts/linux/{hetero-calibration,hetero,phase3}.csv`` and the
Linux per-vertex workload, and prints the Markdown tables used in
``docs/hetero-experiments.md``:

- ``calibration``: effective core speed per set speed;
- ``phase1``: throughput in F-core units, ideal throughput n_F + n_S * r_eff,
  efficiency, and both idle definitions, per (cores, r, strategy);
- ``sim``: the simulator's makespan for the same runs and its error;
- ``phase3``: the schedule comparison on emulated cores;
- ``sweep``: simulator-only r sweeps, misestimated r, and non-constant r;
- ``m4``: the M4 runs replayed in the simulator, pinned vs migrating;
- ``workers``: how many workers to run on the M4 shape.

Every table takes the minimum compute over repeats (the repo's protocol)
and drops runs whose host steal exceeds :data:`STEAL_LIMIT` of the CPU time
the run could have used, a limit fixed before any Phase 1 run.

Usage::

    python -m parallel_processing.hetero_analysis [section ...]
"""

from __future__ import annotations

import csv
import math
import sys
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from parallel_processing import hetero, hetero_phase3, sched_sim

ART = Path("artifacts/linux")
WORKLOAD = ART / "workload-soc-sign-epinions.csv"
STEAL_LIMIT = 0.03  # share of (cores x compute) lost to the hypervisor

# Calibration slices standing in for the soc outer loop, whose time is
# almost all heavy and mid-weight subproblems (top 1% of vertices: 94.5%).
GRAPH_TASKS = ("heavy", "mid")

Row = dict[str, str]


def _rows(name: str) -> list[Row]:
    path = ART / name
    if not path.exists():
        return []
    with path.open() as handle:
        return list(csv.DictReader(handle))


def _calibration_best() -> dict[tuple[int, str, float], float]:
    best: dict[tuple[int, str, float], float] = {}
    for r in _rows("hetero-calibration.csv"):
        key = (int(r["period_us"]), r["task"], float(r["speed"]))
        best[key] = min(best.get(key, math.inf), float(r["seconds"]))
    return best


def r_eff(period: int, speed: float) -> float:
    """Measured speed of a core set to ``speed``, averaged over GRAPH_TASKS;
    the set value itself when that combination was not calibrated."""
    if speed >= 1:
        return 1.0
    best = _calibration_best()
    try:
        effs = [best[(period, t, 1.0)] / best[(period, t, speed)] for t in GRAPH_TASKS]
    except KeyError:
        return speed
    return sum(effs) / len(effs)


def _ok(row: Row) -> bool:
    cores = len(row["speeds"].split(";"))
    return float(row["steal_s"]) <= STEAL_LIMIT * cores * float(row["compute_s"])


def _min_by(rows: Iterable[Row], key: Callable[[Row], tuple[str, ...]]
            ) -> dict[tuple[str, ...], tuple[Row, int, float]]:
    """Fastest row per key, with how many rows shared that key and the
    slowest of them over the fastest (the repeat-to-repeat spread)."""
    groups: dict[tuple[str, ...], list[Row]] = {}
    for row in rows:
        groups.setdefault(key(row), []).append(row)
    out = {}
    for k, group in groups.items():
        times = [float(r["compute_s"]) for r in group]
        best = group[times.index(min(times))]
        out[k] = (best, len(group), max(times) / min(times))
    return out


@dataclass
class Run:
    """The fastest repeat of one configuration, with derived metrics."""

    cores: str
    r: str
    strategy: str
    compute: float
    base: float  # F×1 compute on the same executor: the throughput unit
    speeds: list[float]  # effective (calibrated) speeds
    busy: list[float]
    idle: float
    idle_w: float
    runs: int
    spread: float  # slowest repeat / fastest repeat

    @property
    def throughput(self) -> float:
        return self.base / self.compute

    @property
    def ideal(self) -> float:
        return sum(self.speeds)

    @property
    def efficiency(self) -> float:
        return self.throughput / self.ideal


def _runs(rows: list[Row], strategy_key: str, base: float) -> list[Run]:
    out = []
    best = _min_by(rows, lambda r: (r["cores"], r["r"], r[strategy_key]))
    for (cores, r, strategy), (row, n, spread) in sorted(best.items()):
        period = int(row["period_us"])
        speeds = [r_eff(period, float(s)) for s in row["speeds"].split(";")]
        out.append(
            Run(
                cores=cores,
                r=r,
                strategy=strategy,
                compute=float(row["compute_s"]),
                base=base,
                speeds=speeds,
                busy=[float(b) for b in row["busy"].split(";")],
                idle=float(row["idle_pct"]),
                idle_w=float(row["idle_weighted_pct"]),
                runs=n,
                spread=spread,
            )
        )
    return out


def phase1_runs() -> list[Run]:
    rows = [r for r in _rows("hetero.csv") if r["tag"].startswith("phase1") and _ok(r)]
    base = min((float(r["compute_s"]) for r in rows if r["cores"] == "F"),
               default=math.nan)
    return _runs(rows, "strategy", base)


def _print_runs(runs: Sequence[Run], label: str) -> None:
    print(f"| cores | r | {label} | compute | throughput | ideal | efficiency "
          "| idle | idle (weighted) | busy sum | runs | max/min |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for t in runs:
        print(
            f"| {t.cores} | {t.r or '-'} | {t.strategy} | {t.compute:.1f} s "
            f"| {t.throughput:.2f} | {t.ideal:.2f} | {100 * t.efficiency:.0f}% "
            f"| {t.idle:.1f}% | {t.idle_w:.1f}% | {sum(t.busy):.0f} s | {t.runs} "
            f"| {t.spread:.2f} |"
        )
    print()


def print_calibration() -> None:
    best = _calibration_best()
    speeds = sorted({k[2] for k in best if k[2] < 1}, reverse=True)
    print("| period | task | " + " | ".join(f"s={s:g}" for s in speeds) + " |")
    print("|---|---|" + "---|" * len(speeds))
    for period in sorted({k[0] for k in best}):
        for task in ("loop", "heavy", "mid", "light"):
            base = best[(period, task, 1.0)]
            cells = [f"{base / best[(period, task, s)]:.3f}" for s in speeds]
            print(f"| {period / 1000:g} ms | {task} | " + " | ".join(cells) + " |")
    print()


def print_phase1() -> None:
    _print_runs(phase1_runs(), "strategy")


def contention_scale(runs: Sequence[Run]) -> float:
    """Per-core speed of four full-speed cores running together relative to
    one alone, from the F×4 interleave run (idle ~0) against F×1."""
    for t in runs:
        if (t.cores, t.strategy) == ("F,F,F,F", "interleave"):
            return t.throughput / (1 - t.idle / 100) / 4
    return 1.0


JITTER_SIGMA = 0.05  # per-batch lognormal noise for the spread columns
JITTER_TRIALS = 40


def _jittered(costs: list[float], seed: int) -> list[float]:
    import random

    rng = random.Random(seed)
    return [c * rng.lognormvariate(0.0, JITTER_SIGMA) for c in costs]


def print_sim() -> None:
    """Simulate every Phase 1 configuration and compare with the measurement.

    Which worker draws which heavy tail batch hinges on small timing
    differences, so besides the noiseless run the table gives the 10th-90th
    percentile over :data:`JITTER_TRIALS` runs with each batch's cost
    perturbed by lognormal noise of sigma :data:`JITTER_SIGMA`."""
    w = sched_sim.Workload.from_csv(WORKLOAD)
    runs = phase1_runs()
    base = runs[0].base if runs else math.nan
    scale = contention_scale(runs)
    unit = base / sum(w.seconds)
    print(f"F×1 compute {base:.1f} s vs summed per-vertex profile "
          f"{sum(w.seconds):.1f} s (costs rescaled by {unit:.3f}); per-core speed "
          f"with four busy cores: {scale:.3f}\n")
    print("| cores | r | strategy | measured | sim | error "
          "| sim with contention | error | jittered p10-p90 | measured inside |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for t in runs:
        if t.cores == "F":
            continue
        batches = hetero.make_batches(w.n, t.strategy, 64)
        costs = [unit * w.cost(b) for b in batches]
        plain = sched_sim.simulate_dynamic(costs, t.speeds).makespan
        cont = sched_sim.simulate_dynamic([c / scale for c in costs], t.speeds).makespan
        m = t.compute
        spread = sorted(
            sched_sim.simulate_dynamic(
                _jittered([c / scale for c in costs], k), t.speeds
            ).makespan
            for k in range(JITTER_TRIALS)
        )
        p10, p90 = spread[len(spread) // 10], spread[(9 * len(spread)) // 10]
        inside = "yes" if p10 <= m <= p90 else "no"
        print(
            f"| {t.cores} | {t.r or '-'} | {t.strategy} | {m:.1f} s "
            f"| {plain:.1f} s | {100 * (plain - m) / m:+.1f}% "
            f"| {cont:.1f} s | {100 * (cont - m) / m:+.1f}% "
            f"| {p10:.1f}-{p90:.1f} s | {inside} |"
        )
    print()


def print_phase3() -> None:
    rows = [r for r in _rows("phase3.csv") if _ok(r)]
    groups: dict[str, list[Row]] = {}
    for r in rows:
        tag = r["tag"].split("-rep")[0]
        key = (f"{tag} {r['graph']} period={r['period_us']} "
               f"fast_scale={r['fast_scale'] or '-'} migrate={r.get('migrate', '0')}")
        groups.setdefault(key, []).append(r)
    for key, group in groups.items():
        graph = group[0]["graph"]
        base_rows = [r for r in rows if r["graph"] == graph and r["cores"] == "F"]
        base = min((float(r["compute_s"]) for r in base_rows), default=math.nan)
        if math.isnan(base) and graph.startswith("soc"):
            base = phase1_runs()[0].base
        print(f"### {key}\n")
        _print_runs([t for t in _runs(group, "schedule", base) if t.cores != "F"],
                    "schedule")


def _sim_schedule(
    name: str,
    speeds: list[float],
    costs: hetero_phase3.Costs,
    fast_scale: Callable[[int], float] | None = None,
    slow_factor: Callable[[int], float] | None = None,
    cores: list[float] | None = None,
    migrate: bool = False,
) -> sched_sim.SimResult:
    """Simulate a Phase 3 schedule built exactly as the real driver builds it
    (split schedules excluded: they need branch costs).

    ``speeds`` are the workers' speeds as the schedule assumes them;
    ``cores``, when given, are the machine's cores (at least as many), on
    which the workers start in order and, with ``migrate``, move."""
    n = len(costs.measured)
    queues, poll = hetero_phase3.build(name, speeds, costs, {}, list(range(n)), (0, 0))
    m = costs.measured

    def cost(task: hetero.Task) -> float:
        return sum(m[i] for i in task if isinstance(i, int))

    q_costs = [[cost(t) for t in q] for q in queues]
    factors = None
    if slow_factor is not None:
        f = slow_factor

        def factor(task: hetero.Task) -> float:
            # time on a slow core is sum(c / (r * f)); express it as one factor
            slow = sum(m[i] / f(i) for i in task if isinstance(i, int))
            return cost(task) / slow if slow > 0 else 1.0

        factors = [[factor(t) for t in q] for q in queues]
    return sched_sim.simulate(
        q_costs, cores or speeds, poll, 0.0, fast_scale, factors, migrate
    )


SWEEP_SCHEDULES = ["block", "interleave", "lpt", "lpt-oracle", "static-oracle@TRUE"]
MIXES = {
    "F,F,S,S": ["F", "F", "S", "S"],
    "F,S,S,S": ["F", "S", "S", "S"],
    "4F+6S (M4 shape)": ["F"] * 4 + ["S"] * 6,
}


def print_sweep() -> None:
    """Simulator-only: r sweep per core mix, misestimated r, and H3/H4."""
    costs, _ = hetero_phase3.load_costs(WORKLOAD)

    print("### makespan / lower bound over r (1.000 = no schedule does better)\n")
    rs = [0.26, 0.43, 0.5, 0.75, 1.0]
    for label, mix in MIXES.items():
        print(f"{label}\n")
        print("| schedule | " + " | ".join(f"r={r:g}" for r in rs) + " |")
        print("|---|" + "---|" * len(rs))
        for sched in SWEEP_SCHEDULES:
            cells = []
            for r in rs:
                speeds = [1.0 if c == "F" else r for c in mix]
                res = _sim_schedule(sched.replace("TRUE", f"{r:g}"), speeds, costs)
                lb = sched_sim.lower_bound(costs.measured, speeds)
                cells.append(f"{res.makespan / lb:.3f}")
            print(f"| {sched} | " + " | ".join(cells) + " |")
        print()

    print("### misestimated r: static-oracle@r_hat makespan / lpt makespan\n")
    r_hats = [0.15, 0.26, 0.35, 0.43, 0.5, 0.6, 0.75, 1.0]
    for label, mix in MIXES.items():
        print(f"{label}\n")
        print("| true r | " + " | ".join(f"r_hat={h:g}" for h in r_hats) + " |")
        print("|---|" + "---|" * len(r_hats))
        for true_r in (0.26, 0.43, 0.6):
            speeds = [1.0 if c == "F" else true_r for c in mix]
            dyn = _sim_schedule("lpt", speeds, costs).makespan
            cells = []
            for h in r_hats:
                static = _sim_schedule(f"static-oracle@{h:g}", speeds, costs)
                cells.append(f"{static.makespan / dyn:.3f}")
            print(f"| {true_r:g} | " + " | ".join(cells) + " |")
        print()

    print("### non-constant r (M4 shape, nominal r = 0.43)\n")
    speeds = [1.0] * 4 + [0.43] * 6
    # H3: each extra busy fast core costs 7% (4 busy -> 0.79, the M4 P-only
    # efficiency), so while all run the ratio is 0.43 / 0.79 = 0.54.
    h3 = [1.0, 1.0, 0.93, 0.86, 0.79].__getitem__
    # H4: a task's slow-core speed is 1 / (alpha / r + 1 - alpha) for compute
    # share alpha; heavier subproblems assumed more memory-bound, alpha going
    # from 1.0 (cheapest) to 0.6 (costliest) with log cost.
    positive = [c for c in costs.measured if c > 0]
    lo, hi = math.log(min(positive)), math.log(max(positive))

    def h4(i: int) -> float:  # slow-core speed multiplier over r
        c = max(costs.measured[i], min(positive))
        alpha = 1.0 - 0.4 * (math.log(c) - lo) / (hi - lo)
        return (1 / (alpha / 0.43 + 1 - alpha)) / 0.43

    variants: list[tuple[str, Callable[[int], float] | None,
                         Callable[[int], float] | None]] = [
        ("constant r", None, None),
        ("H3", h3, None),
        ("H4", None, h4),
        ("H3 + H4", h3, h4),
    ]
    print("| schedule | " + " | ".join(v[0] for v in variants) + " |")
    print("|---|" + "---|" * len(variants))
    for sched in ["interleave", "lpt", "static-oracle@0.43", "static-oracle@0.54"]:
        cells = [
            f"{_sim_schedule(sched, speeds, costs, fs, sf).makespan:.2f} s"
            for _, fs, sf in variants
        ]
        print(f"| {sched} | " + " | ".join(cells) + " |")
    print(f"\n(total work {sum(costs.measured):.1f} s at full speed)\n")

    print("### migration (M4 shape: 8 workers on 4 fast + 6 slow cores, r = 0.43)\n")
    cores = [1.0] * 4 + [0.43] * 6
    assumed = [1.0] * 4 + [0.43] * 4  # where the workers start
    lb = sched_sim.lower_bound(costs.measured, assumed)
    print(f"lower bound with 4 fast + 4 slow workers busy: {lb:.1f} s\n")
    print("| schedule | pinned | migrating | pinned / LB | migrating / LB |")
    print("|---|---|---|---|---|")
    for sched in ["block", "reversed", "interleave", "lpt", "lpt-oracle",
                  "static-oracle@0.43"]:
        pin = _sim_schedule(sched, assumed, costs, cores=cores).makespan
        mig = _sim_schedule(sched, assumed, costs, cores=cores, migrate=True).makespan
        print(f"| {sched} | {pin:.1f} s | {mig:.1f} s "
              f"| {pin / lb:.3f} | {mig / lb:.3f} |")
    print()


# M4 strategy-comparison session (artifacts/phase-profile.csv, 2026-07-21,
# Chrome open): minimum compute over three runs and that run's busy sum.
M4_MEASURED = {
    (4, "block"): (33.27, 106.2),
    (4, "reversed"): (32.73, 130.8),
    (4, "interleave"): (36.69, 146.6),
    (8, "block"): (25.85, 139.3),
    (8, "reversed"): (28.54, 174.6),
    (8, "interleave"): (24.73, 197.7),
}
M4_CLEAN_INTERLEAVE_W8 = 18.24  # the Chrome-closed rerun


def print_m4() -> None:
    """Replay the M4 runs in the simulator with the M4 per-vertex costs:
    4 P + 6 E cores, workers placed on P first, pinned or migrating."""
    w = sched_sim.Workload.from_csv("artifacts/workload-soc-sign-epinions.csv")
    print(f"M4 per-vertex costs, total {sum(w.seconds):.1f} s on a P core; "
          "cores 4 P + 6 E, contention ignored\n")
    print("| workers | strategy | r | pinned | busy | migrating | busy "
          "| M4 measured | busy |")
    print("|---|---|---|---|---|---|---|---|---|")
    for workers in (4, 8):
        for strategy in ("block", "reversed", "interleave"):
            costs = [w.cost(b) for b in hetero.make_batches(w.n, strategy, 64)]
            for r in (0.26, 0.43):
                slots = [1.0] * 4 + [r] * 6
                pin = sched_sim.simulate_dynamic(costs, slots, workers=workers)
                mig = sched_sim.simulate_dynamic(
                    costs, slots, workers=workers, migrate=True
                )
                m, mb = M4_MEASURED[(workers, strategy)]
                print(
                    f"| {workers} | {strategy} | {r:g} | {pin.makespan:.1f} s "
                    f"| {sum(pin.busy):.0f} s | {mig.makespan:.1f} s "
                    f"| {sum(mig.busy):.0f} s | {m:.1f} s | {mb:.0f} s |"
                )
    print(f"\n(clean-session interleave w=8: {M4_CLEAN_INTERLEAVE_W8} s)\n")


def print_workers() -> None:
    """How many workers to run on the M4 shape (4 fast + 6 slow cores)."""
    w = sched_sim.Workload.from_csv(WORKLOAD)
    total = sum(w.seconds)
    print(f"this host's soc costs ({total:.1f} s at full speed); cores 4 fast + 6 "
          "slow; workers start on the fast cores\n")
    print("| r | workers | block pinned | block migrating | interleave pinned "
          "| interleave migrating | lower bound |")
    print("|---|---|---|---|---|---|---|")
    for r in (0.26, 0.43, 0.6):
        cores = [1.0] * 4 + [r] * 6
        for workers in (4, 6, 8, 10):
            cells = []
            for strategy in ("block", "interleave"):
                costs = [w.cost(b) for b in hetero.make_batches(w.n, strategy, 64)]
                for mig in (False, True):
                    res = sched_sim.simulate_dynamic(
                        costs, cores, workers=workers, migrate=mig
                    )
                    cells.append(f"{res.makespan:.1f} s")
            lb = sched_sim.lower_bound(w.seconds, cores[:workers])
            print(f"| {r:g} | {workers} | " + " | ".join(cells) + f" | {lb:.1f} s |")
    print()


SECTIONS: dict[str, Callable[[], None]] = {
    "calibration": print_calibration,
    "phase1": print_phase1,
    "sim": print_sim,
    "phase3": print_phase3,
    "sweep": print_sweep,
    "m4": print_m4,
    "workers": print_workers,
}


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    for name in args or list(SECTIONS):
        print(f"## {name}\n")
        SECTIONS[name]()


if __name__ == "__main__":
    main()
