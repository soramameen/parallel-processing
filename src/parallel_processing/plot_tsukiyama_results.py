"""Plot Tsukiyama benchmark results.

Creates visualizations comparing Tsukiyama et al.'s algorithm with modern
pivot-based algorithms (Bron-Kerbosch, Tomita CLIQUES, Eppstein).

Usage::

    python -m parallel_processing.plot_tsukiyama_results
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def load_results(csv_path: Path) -> list[dict]:
    """Load benchmark results from CSV."""
    results = []
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            for key in ["vertices", "edges", "degeneracy", "expected_cliques", "runs"]:
                if row[key]:
                    row[key] = int(row[key])
            for key in ["time_s"]:
                if row[key]:
                    row[key] = float(row[key])
            if row["work_counter"]:
                row["work_counter"] = int(row["work_counter"])
            row["timeout"] = row["timeout"] == "True"
            results.append(row)
    return results


def plot_runtime_comparison(results: list[dict], output_path: Path) -> None:
    """Plot runtime comparison across instances and algorithms."""
    # Group by instance
    instances = {}
    for r in results:
        inst = r["instance"]
        if inst not in instances:
            instances[inst] = {}
        instances[inst][r["algorithm"]] = r

    # Prepare data
    instance_names = [r.split("_")[0] for r in sorted(instances.keys())]
    algorithms = ["bron_kerbosch_pivot", "tomita_cliques", "eppstein_cliques", "tsukiyama_cliques"]
    algo_labels = ["Bron-Kerbosch\n(pivot)", "Tomita\nCLIQUES", "Eppstein et al.\n(2010)", "Tsukiyama et al.\n(1977)"]
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]

    fig, ax = plt.subplots(figsize=(12, 6))

    x_pos = range(len(instance_names))
    width = 0.2

    for i, (algo, label, color) in enumerate(zip(algorithms, algo_labels, colors)):
        times = []
        for inst in sorted(instances.keys()):
            r = instances[inst].get(algo, {})
            if r.get("timeout", False):
                times.append(300)  # Plot timeout at 300s
            elif r.get("time_s") is not None:
                times.append(r["time_s"])
            else:
                times.append(None)

        # Plot bars, handling None values
        for j, (x, t) in enumerate(zip(x_pos, times)):
            if t is not None:
                if instances[sorted(instances.keys())[j]][algo].get("timeout", False):
                    # Timeout: use hatched bar
                    ax.bar(x + i * width, t, width, label=label if j == 0 else "",
                           color=color, alpha=0.7, hatch="//", edgecolor="black")
                else:
                    ax.bar(x + i * width, t, width, label=label if j == 0 else "", color=color)

    ax.set_ylabel("Time (seconds)", fontsize=12)
    ax.set_xlabel("Instance", fontsize=12)
    ax.set_title("Runtime Comparison: Tsukiyama vs. Modern Algorithms", fontsize=14, fontweight="bold")
    ax.set_xticks([x + width * 1.5 for x in x_pos])
    ax.set_xticklabels(instance_names)
    ax.set_yscale("log")
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.legend(loc="upper left", fontsize=10)

    # Add timeout annotation
    timeout_patch = mpatches.Patch(facecolor="white", edgecolor="black", hatch="//", label="Timeout (≥300s)")
    handles, labels = ax.get_legend_handles_labels()
    handles.append(timeout_patch)
    ax.legend(handles=handles, loc="upper left", fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Saved runtime plot to {output_path}")


def plot_speedup(results: list[dict], output_path: Path) -> None:
    """Plot speedup of modern algorithms relative to Tsukiyama."""
    # Group by instance
    instances = {}
    for r in results:
        inst = r["instance"]
        if inst not in instances:
            instances[inst] = {}
        instances[inst][r["algorithm"]] = r

    # Filter instances where Tsukiyama completed
    completed_instances = []
    for inst in sorted(instances.keys()):
        tsuk = instances[inst].get("tsukiyama_cliques", {})
        if not tsuk.get("timeout", False) and tsuk.get("time_s") is not None:
            completed_instances.append(inst)

    if not completed_instances:
        print("No instances where Tsukiyama completed; skipping speedup plot.")
        return

    instance_names = [r.split("_")[0] for r in completed_instances]
    algorithms = ["bron_kerbosch_pivot", "tomita_cliques", "eppstein_cliques"]
    algo_labels = ["Bron-Kerbosch (pivot)", "Tomita CLIQUES", "Eppstein et al. (2010)"]
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

    fig, ax = plt.subplots(figsize=(10, 6))

    x_pos = range(len(instance_names))
    width = 0.25

    for i, (algo, label, color) in enumerate(zip(algorithms, algo_labels, colors)):
        speedups = []
        for inst in completed_instances:
            tsuk_time = instances[inst]["tsukiyama_cliques"]["time_s"]
            algo_time = instances[inst][algo]["time_s"]
            speedup = tsuk_time / algo_time if algo_time > 0 else 0
            speedups.append(speedup)

        ax.bar([x + i * width for x in x_pos], speedups, width, label=label, color=color)

    ax.set_ylabel("Speedup (×)", fontsize=12)
    ax.set_xlabel("Instance", fontsize=12)
    ax.set_title("Speedup of Modern Algorithms vs. Tsukiyama (1977)", fontsize=14, fontweight="bold")
    ax.set_xticks([x + width for x in x_pos])
    ax.set_xticklabels(instance_names)
    ax.set_yscale("log")
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.legend(loc="upper left", fontsize=10)
    ax.axhline(y=1, color="red", linestyle="--", linewidth=1, alpha=0.5)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Saved speedup plot to {output_path}")


def main() -> None:
    """Generate all plots from benchmark results."""
    csv_path = Path("artifacts/tsukiyama_benchmark.csv")
    if not csv_path.exists():
        print(f"Error: {csv_path} not found. Run benchmark_tsukiyama.py first.")
        return

    results = load_results(csv_path)

    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)

    plot_runtime_comparison(results, artifacts_dir / "tsukiyama_runtime_comparison.png")
    plot_speedup(results, artifacts_dir / "tsukiyama_speedup.png")

    print("\nPlots generated successfully!")


if __name__ == "__main__":
    main()
