"""Benchmark Tsukiyama et al. against the algorithms already in this repo.

This script benchmarks the Tsukiyama algorithm (1977) against the repository's
existing algorithms:
- Bron-Kerbosch with pivot (bron_kerbosch_pivot)
- Tomita's CLIQUES (cliques)
- Eppstein-Löffler-Strash (eppstein_cliques)

For each algorithm and instance:
- Measures wall time (median of multiple runs)
- Counts maximal cliques
- Records work metrics (recursive calls where available)
- Enforces per-run timeout

Results are saved to artifacts/tsukiyama_benchmark.csv and a summary table
is printed to stdout.

Usage::

    python -m parallel_processing.benchmark_tsukiyama
"""

from __future__ import annotations

import csv
import json
import platform
import signal
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from parallel_processing.bron_kerbosch import bron_kerbosch_pivot
from parallel_processing.cliques import count_cliques
from parallel_processing.eppstein import count_eppstein_cliques, degeneracy_ordering
from parallel_processing.graph_io import edge_count, load_dimacs
from parallel_processing.tsukiyama import count_tsukiyama_cliques

# Instances to benchmark
INSTANCES = [
    ("H1_n11.clq", 17),
    ("H3_n45.clq", 145),
    ("H5_n95.clq", 481),
    ("H7_n161.clq", 1121),
    ("H8_n200.clq", 1585),
    ("H9_n243.clq", 2161),
    ("H10_n290.clq", 2861),
]


# Algorithms to benchmark
# name, function, has_work_counter
def _bk_count(graph):
    cliques = bron_kerbosch_pivot(graph)
    count = len(cliques)
    largest = max((len(c) for c in cliques), default=0)
    return count, largest, None


ALGORITHMS = [
    ("bron_kerbosch_pivot", _bk_count, False),
    ("tomita_cliques", lambda g: (*count_cliques(g), None), False),
    ("eppstein_cliques", lambda g: (*count_eppstein_cliques(g), None), False),
    ("tsukiyama_cliques", count_tsukiyama_cliques, True),
]

# Benchmark configuration
REPEAT = 3  # Number of runs per configuration
TIMEOUT_SECONDS = 300  # 5 minutes per run


class BenchmarkTimeoutError(Exception):
    """Raised when a benchmark run exceeds the timeout."""


@contextmanager
def time_limit(seconds: int):
    """Context manager that raises TimeoutException after seconds."""

    def signal_handler(signum, frame):
        raise BenchmarkTimeoutError("Timed out!")

    # Set up signal handler for timeout
    old_handler = signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def benchmark_algorithm(
    algorithm_name: str,
    algorithm_fn: Any,
    graph: dict[int, set[int]],
    timeout: int,
) -> dict[str, Any]:
    """Benchmark one algorithm on one graph.

    Returns:
        time_s, clique_count, largest_clique, work_counter, and timeout.
    """
    try:
        with time_limit(timeout):
            start = time.perf_counter()
            count, largest, work = algorithm_fn(graph)
            elapsed = time.perf_counter() - start
            return {
                "time_s": elapsed,
                "clique_count": count,
                "largest_clique": largest,
                "work_counter": work,
                "timeout": False,
            }
    except BenchmarkTimeoutError:
        return {
            "time_s": None,
            "clique_count": None,
            "largest_clique": None,
            "work_counter": None,
            "timeout": True,
        }
    except Exception as e:
        print(f"    ERROR: {algorithm_name} failed with {e}", file=sys.stderr)
        return {
            "time_s": None,
            "clique_count": None,
            "largest_clique": None,
            "work_counter": None,
            "timeout": False,
        }


def run_benchmarks() -> list[dict[str, Any]]:
    """Run all benchmarks and return results."""
    results: list[dict[str, Any]] = []
    instances_dir = Path("data/instances")

    for instance_file, expected_cliques in INSTANCES:
        instance_path = instances_dir / instance_file
        if not instance_path.exists():
            print(f"Skipping {instance_file}: file not found")
            continue

        print(f"\n=== {instance_file} (expected {expected_cliques} cliques) ===")

        # Load graph
        try:
            graph = load_dimacs(instance_path)
            n = len(graph)
            m = edge_count(graph)
            print(f"Loaded: {n} vertices, {m} edges")

            # Compute degeneracy for context
            _, degeneracy = degeneracy_ordering(graph)
            print(f"Degeneracy: {degeneracy}")
        except Exception as e:
            print(f"Failed to load {instance_file}: {e}")
            continue

        for algo_name, algo_fn, has_work in ALGORITHMS:
            print(f"  {algo_name}:", end=" ", flush=True)

            # Run multiple times
            run_times = []
            run_results = []

            for run_idx in range(REPEAT):
                result = benchmark_algorithm(algo_name, algo_fn, graph, TIMEOUT_SECONDS)
                run_results.append(result)

                if result["timeout"]:
                    print("TIMEOUT", end=" ", flush=True)
                elif result["time_s"] is not None:
                    run_times.append(result["time_s"])
                    print(f"{result['time_s']:.3f}s", end=" ", flush=True)
                else:
                    print("ERROR", end=" ", flush=True)

            print()  # newline after all runs

            # Compute median time. 0.0 is a successful measurement.
            median_time = sorted(run_times)[len(run_times) // 2] if run_times else None

            # Use the result from the median run for clique count/work.
            best_result = (
                run_results[run_times.index(median_time)]
                if median_time is not None
                else run_results[0]
            )

            # Verify clique count
            got = best_result["clique_count"]
            if got is not None and got != expected_cliques:
                print(f"    WARNING: expected {expected_cliques}, got {got}")

            # Record result
            results.append(
                {
                    "instance": instance_file,
                    "vertices": n,
                    "edges": m,
                    "degeneracy": degeneracy,
                    "expected_cliques": expected_cliques,
                    "algorithm": algo_name,
                    "time_s": median_time,
                    "clique_count": best_result["clique_count"],
                    "largest_clique": best_result["largest_clique"],
                    "work_counter": best_result["work_counter"],
                    "timeout": best_result["timeout"],
                    "runs": REPEAT,
                }
            )

    return results


def save_results(results: list[dict[str, Any]], output_path: Path) -> None:
    """Save results to CSV."""
    if not results:
        print("No results to save")
        return

    fieldnames = [
        "instance",
        "vertices",
        "edges",
        "degeneracy",
        "expected_cliques",
        "algorithm",
        "time_s",
        "clique_count",
        "largest_clique",
        "work_counter",
        "timeout",
        "runs",
    ]

    with output_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nResults saved to {output_path}")


def print_summary(results: list[dict[str, Any]]) -> None:
    """Print a summary table of results."""
    print("\n" + "=" * 80)
    print("SUMMARY TABLE")
    print("=" * 80)

    # Group by instance
    instances = {}
    for r in results:
        inst = r["instance"]
        if inst not in instances:
            instances[inst] = {}
        instances[inst][r["algorithm"]] = r

    # Print header
    header = (
        f"{'Instance':<15} {'Algorithm':<20} {'Time (s)':>12} "
        f"{'Cliques':>10} {'Largest':>8} {'Nodes':>12}"
    )
    print(header)
    print("-" * len(header))

    for inst_name in [f for f, _ in INSTANCES]:
        if inst_name not in instances:
            continue

        inst_results = instances[inst_name]
        for i, (algo_name, _, _) in enumerate(ALGORITHMS):
            if algo_name not in inst_results:
                continue

            r = inst_results[algo_name]
            inst_display = inst_name if i == 0 else ""

            time_str = (
                "TIMEOUT"
                if r["timeout"]
                else (f"{r['time_s']:.3f}" if r["time_s"] is not None else "ERROR")
            )
            clique_str = (
                str(r["clique_count"]) if r["clique_count"] is not None else "-"
            )
            largest_str = (
                str(r["largest_clique"]) if r["largest_clique"] is not None else "-"
            )
            if r["work_counter"] is None or not r["clique_count"]:
                work_str = "-"
            else:
                ratio = r["work_counter"] / (r["vertices"] * r["clique_count"])
                work_str = f"{r['work_counter']} ({ratio:.3f} nμ)"

            print(
                f"{inst_display:<15} {algo_name:<20} {time_str:>12} "
                f"{clique_str:>10} {largest_str:>8} {work_str:>12}"
            )

        if inst_name != INSTANCES[-1][0]:
            print()


def save_machine_info(output_path: Path) -> None:
    """Save machine information for reproducibility."""
    info = {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "machine": platform.machine(),
    }

    with output_path.open("w") as f:
        json.dump(info, f, indent=2)

    print(f"Machine info saved to {output_path}")


def main() -> None:
    """Run all benchmarks and save results."""
    print("Tsukiyama et al. Algorithm Benchmark")
    print("=" * 80)
    print("Configuration:")
    print(f"  Repetitions: {REPEAT}")
    print(f"  Timeout: {TIMEOUT_SECONDS}s per run")
    print()

    # Create output directory
    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)

    # Run benchmarks
    results = run_benchmarks()

    # Save results
    save_results(results, artifacts_dir / "tsukiyama_benchmark.csv")
    save_machine_info(artifacts_dir / "tsukiyama_machine_info.json")

    # Print summary
    print_summary(results)


if __name__ == "__main__":
    main()
