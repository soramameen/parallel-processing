"""SVG figures for docs/hetero-experiments.md.

Plain SVG with its own light/dark tokens, so the files render the same on
GitHub, in a browser, and when pulled into the thesis. Colours follow the
validated default categorical order (series 1 blue, 2 orange, 3 aqua) and
text always wears ink tokens, never a series colour. Each figure has a
table in the write-up carrying the same numbers.

Usage::

    python -m parallel_processing.hetero_figures [outdir]
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from parallel_processing import hetero, hetero_phase3, sched_sim
from parallel_processing import hetero_analysis as ha

STYLE = """<style>
  .s { --surface:#fcfcfb; --ink:#0b0b0b; --ink2:#52514e; --muted:#898781;
       --grid:#e1e0d9; --axis:#c3c2b7; --c1:#2a78d6; --c2:#eb6834; --c3:#1baf7a; }
  @media (prefers-color-scheme: dark) {
    .s { --surface:#1a1a19; --ink:#ffffff; --ink2:#c3c2b7; --muted:#898781;
         --grid:#2c2c2a; --axis:#383835; --c1:#3987e5; --c2:#d95926; --c3:#199e70; }
  }
  .s text { font-family: system-ui, -apple-system, "Segoe UI", "Hiragino Sans",
            "Noto Sans JP", sans-serif; fill: var(--ink2); font-size: 12px; }
  .s .title { fill: var(--ink); font-size: 14px; font-weight: 600; }
  .s .tick { fill: var(--muted); font-size: 11px; font-variant-numeric: tabular-nums; }
  .s .grid { stroke: var(--grid); stroke-width: 1; }
  .s .axis { stroke: var(--axis); stroke-width: 1; }
</style>"""

SERIES = ["var(--c1)", "var(--c2)", "var(--c3)"]


@dataclass
class Svg:
    width: int
    height: int
    parts: list[str]

    def add(self, s: str) -> None:
        self.parts.append(s)

    def text(
        self,
        x: float,
        y: float,
        s: str,
        cls: str = "",
        anchor: str = "start",
    ) -> None:
        c = f' class="{cls}"' if cls else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}"{c} text-anchor="{anchor}">{s}</text>')

    def render(self) -> str:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" class="s" '
            f'viewBox="0 0 {self.width} {self.height}" width="{self.width}" '
            f'height="{self.height}" role="img">{STYLE}'
            f'<rect width="100%" height="100%" fill="var(--surface)"/>'
            + "".join(self.parts)
            + "</svg>"
        )


def _hbar(
    svg: Svg, x0: float, y: float, length: float, h: float, color: str, title: str
) -> None:
    """Horizontal bar anchored at x0 with a 4px rounded data end."""
    r = min(4.0, h / 2, length / 2) if length > 0 else 0
    x1 = x0 + length
    path = (
        f"M{x0:.1f},{y:.1f} H{x1 - r:.1f} Q{x1:.1f},{y:.1f} {x1:.1f},{y + r:.1f} "
        f"V{y + h - r:.1f} Q{x1:.1f},{y + h:.1f} {x1 - r:.1f},{y + h:.1f} "
        f"H{x0:.1f} Z"
    )
    svg.add(f'<path d="{path}" fill="{color}"><title>{title}</title></path>')


def _legend(svg: Svg, x: float, y: float, labels: Sequence[str]) -> None:
    for i, label in enumerate(labels):
        svg.add(
            f'<rect x="{x:.1f}" y="{y - 9:.1f}" width="10" height="10" rx="2" '
            f'fill="{SERIES[i]}"/>'
        )
        svg.text(x + 15, y, label)
        x += 15 + 13 * len(label) + 18


def _x_axis(
    svg: Svg,
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    vmax: float,
    step: float,
    unit: str,
) -> None:
    v = 0.0
    while v <= vmax + 1e-9:
        x = x0 + (x1 - x0) * v / vmax
        svg.add(
            f'<line class="grid" x1="{x:.1f}" y1="{y0:.1f}" x2="{x:.1f}" '
            f'y2="{y1:.1f}"/>'
        )
        svg.text(x, y1 + 14, f"{v:g}{unit}", "tick", "middle")
        v += step
    svg.add(
        f'<line class="axis" x1="{x0:.1f}" y1="{y0:.1f}" x2="{x0:.1f}" y2="{y1:.1f}"/>'
    )


def fig_phase1() -> str:
    """Throughput of block vs interleave per pinned core mix, with the ideal
    n_F + n_S * r_eff as a tick."""
    runs = {(t.cores, t.r, t.strategy): t for t in ha.phase1_runs()}
    configs = [
        ("F,F,F,F", ""),
        ("F,F,S,S", "0.75"),
        ("F,F,S,S", "0.43"),
        ("F,F,S,S", "0.26"),
        ("F,S,S,S", "0.75"),
        ("F,S,S,S", "0.43"),
        ("F,S,S,S", "0.26"),
        ("S,S,S,S", "0.43"),
    ]
    configs = [c for c in configs if (c[0], c[1], "block") in runs]
    left, right, top, row = 150, 600, 64, 40
    svg = Svg(640, top + row * len(configs) + 40, [])
    svg.text(16, 24, "コアを固定したとき: block と interleave のスループット", "title")
    _legend(svg, 16, 46, ["block", "interleave"])
    vmax = 4.0
    y1 = top + row * len(configs)
    _x_axis(svg, left, right, top - 6, y1, vmax, 1.0, "")
    svg.text(right, y1 + 30, "スループット（速いコア1個 = 1）", "tick", "end")
    for i, (cores, r) in enumerate(configs):
        y = top + i * row
        label = cores.replace(",", "") + (f"  r={r}" if r else "")
        svg.text(left - 10, y + 17, label, anchor="end")
        for j, strategy in enumerate(("block", "interleave")):
            t = runs[(cores, r, strategy)]
            length = (right - left) * t.throughput / vmax
            _hbar(
                svg,
                left,
                y + 3 + j * 14,
                length,
                12,
                SERIES[j],
                f"{label} {strategy}: {t.throughput:.2f}（idle {t.idle:.1f}%）",
            )
        ideal = left + (right - left) * runs[(cores, r, "block")].ideal / vmax
        svg.add(
            f'<line x1="{ideal:.1f}" y1="{y:.1f}" x2="{ideal:.1f}" y2="{y + 32:.1f}" '
            f'stroke="var(--ink)" stroke-width="2"><title>理想</title></line>'
        )
    svg.text(right, 46, "縦線 = 理想（速いコア数 + 遅いコア数 × r）", "tick", "end")
    return svg.render()


def fig_m4() -> str:
    """M4 w=8 replayed: pinned sim, migrating sim, and the measurement."""
    w = sched_sim.Workload.from_csv("artifacts/workload-soc-sign-epinions.csv")
    left, right, top, row = 120, 600, 64, 52
    strategies = ["block", "reversed", "interleave"]
    svg = Svg(640, top + row * len(strategies) + 40, [])
    svg.text(16, 24, "M4 の w=8 を再現: worker 固定と移動（r = 0.43）", "title")
    _legend(svg, 16, 46, ["固定（シミュ）", "移動あり（シミュ）", "M4 実測"])
    vmax = 45.0
    y1 = top + row * len(strategies)
    _x_axis(svg, left, right, top - 6, y1, vmax, 10.0, " 秒")
    slots = [1.0] * 4 + [0.43] * 6
    for i, strategy in enumerate(strategies):
        y = top + i * row
        svg.text(left - 10, y + 24, strategy, anchor="end")
        costs = [w.cost(b) for b in hetero.make_batches(w.n, strategy, 64)]
        values = [
            sched_sim.simulate_dynamic(costs, slots, workers=8).makespan,
            sched_sim.simulate_dynamic(costs, slots, workers=8, migrate=True).makespan,
            ha.M4_MEASURED[(8, strategy)][0],
        ]
        for j, v in enumerate(values):
            _hbar(
                svg,
                left,
                y + 3 + j * 14,
                (right - left) * min(v, vmax) / vmax,
                12,
                SERIES[j],
                f"{strategy}: {v:.1f} 秒",
            )
            svg.text(
                left + (right - left) * min(v, vmax) / vmax + 6,
                y + 14 + j * 14,
                f"{v:.1f}",
                "tick",
            )
    return svg.render()


def fig_misestimate() -> str:
    """Static LPT with exact costs but an assumed r, as makespan over the
    lower bound, for the M4 shape (4 fast + 6 slow); interleave, which needs
    neither r nor costs, is marked per true r."""
    costs, _ = hetero_phase3.load_costs(ha.WORKLOAD)
    r_hats = [0.15, 0.2, 0.26, 0.3, 0.35, 0.43, 0.5, 0.6, 0.75, 0.9, 1.0]
    truths = [0.26, 0.43, 0.6]
    left, right, top, bottom = 64, 600, 92, 332
    svg = Svg(640, 384, [])
    svg.text(
        16, 24, "遅いコアの速さを見誤った静的配分（4 速い + 6 遅い、シミュ）", "title"
    )
    _legend(svg, 16, 46, [f"真の r = {t:g}" for t in truths])
    svg.text(
        16,
        68,
        "縦軸: 完了時間 ÷ 下限（1.0 = これ以上速くできない）。"
        "コストは実測値を与えた最良ケース",
        "tick",
    )
    ymin, ymax = 0.9, 2.0
    for k in range(12):
        v = ymin + 0.1 * k
        y = bottom - (bottom - top) * (v - ymin) / (ymax - ymin)
        svg.add(
            f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}"/>'
        )
        svg.text(left - 8, y + 4, f"{v:.1f}", "tick", "end")
    for h in (0.2, 0.4, 0.6, 0.8, 1.0):
        x = left + (right - left) * (h - 0.1) / 0.9
        svg.text(x, bottom + 16, f"{h:g}", "tick", "middle")
    svg.text(right, bottom + 34, "静的配分に入れた r", "tick", "end")
    svg.text(left, bottom + 34, "2.0 を超える点は上端に描いた", "tick")

    def yof(v: float) -> float:
        return bottom - (bottom - top) * (min(v, ymax) - ymin) / (ymax - ymin)

    for j, truth in enumerate(truths):
        speeds = [1.0] * 4 + [truth] * 6
        lb = sched_sim.lower_bound(costs.measured, speeds)
        inter = ha._sim_schedule("interleave", speeds, costs).makespan / lb
        y = yof(inter)
        svg.add(
            f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" '
            f'stroke="{SERIES[j]}" stroke-width="1.5" stroke-dasharray="4 3">'
            f"<title>interleave（真の r={truth:g}）: {inter:.3f}</title></line>"
        )
        pts = []
        for h in r_hats:
            name = f"static-oracle@{h:g}"
            ratio = ha._sim_schedule(name, speeds, costs).makespan / lb
            x = left + (right - left) * (h - 0.1) / 0.9
            pts.append((x, yof(ratio), h, ratio))
        d = " ".join(
            f"{'M' if k == 0 else 'L'}{x:.1f},{y:.1f}"
            for k, (x, y, _, _) in enumerate(pts)
        )
        svg.add(f'<path d="{d}" fill="none" stroke="{SERIES[j]}" stroke-width="2"/>')
        for x, y, h, ratio in pts:
            svg.add(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{SERIES[j]}" '
                f'stroke="var(--surface)" stroke-width="2"><title>真の r={truth:g}, '
                f"入れた r={h:g}: {ratio:.3f}</title></circle>"
            )
    svg.text(right, top - 6, "破線 = interleave（r もコストも使わない）", "tick", "end")
    return svg.render()


def fig_migration() -> str:
    """3e: the same schedules with pinned and migrating workers (F,F,S,S)."""
    rows = [
        r for r in ha._rows("phase3.csv") if r["tag"].startswith("3e") and ha._ok(r)
    ]
    best: dict[tuple[str, str, str], float] = {}
    for row_ in rows:
        key = (row_["r"], row_["schedule"].split("@")[0], row_["migrate"])
        best[key] = min(best.get(key, float("inf")), float(row_["compute_s"]))
    order = ["block", "reversed", "interleave", "lpt", "static-oracle"]
    configs = [(r, sched) for r in ("0.43", "0.26") for sched in order]
    left, right, top, row = 170, 600, 64, 36
    svg = Svg(640, top + row * len(configs) + 44, [])
    svg.text(16, 24, "worker を固定したときと移動させたとき（F,F,S,S、実測）", "title")
    _legend(svg, 16, 46, ["固定", "移動あり"])
    vmax = 220.0
    y1 = top + row * len(configs)
    _x_axis(svg, left, right, top - 6, y1, vmax, 50.0, " 秒")
    for i, (r, sched) in enumerate(configs):
        y = top + i * row
        label = f"r={r}  {sched.replace('static-oracle', 'static')}"
        svg.text(left - 10, y + 15, label, anchor="end")
        for j, mig in enumerate(("0", "1")):
            v = best[(r, sched, mig)]
            length = (right - left) * v / vmax
            _hbar(
                svg,
                left,
                y + 2 + j * 13,
                length,
                11,
                SERIES[j],
                f"{label} {'移動あり' if mig == '1' else '固定'}: {v:.1f} 秒",
            )
            svg.text(left + length + 6, y + 12 + j * 13, f"{v:.1f}", "tick")
    return svg.render()


FIGURES = {
    "hetero-phase1.svg": fig_phase1,
    "hetero-m4-replay.svg": fig_m4,
    "hetero-misestimate.svg": fig_misestimate,
    "hetero-migration.svg": fig_migration,
}


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    out = Path(args[0] if args else "docs/figures")
    out.mkdir(parents=True, exist_ok=True)
    for name, fn in FIGURES.items():
        (out / name).write_text(fn())
        print(out / name)


if __name__ == "__main__":
    main()
