# Resources

## 一次論文（最高信頼）

- **Tomita, Tanaka, Takahashi (2006)** — CLIQUES。ピボット版 Bron–Kerbosch の O(3^(n/3)) 証明。
  https://snap.stanford.edu/class/cs224w-readings/tomita06cliques.pdf
- **Eppstein, Löffler, Strash (2010)** — degeneracy ordering 版。O(d·n·3^(d/3)) と下界 (n−d)·3^(d/3)。
  https://arxiv.org/abs/1006.5440
- **Eppstein, Strash (2011/2013)** — 上記の実装・実験版（JEA 2013 が統合版）。
  https://arxiv.org/abs/1103.0318

## 参照実装

- quick-cliques (Strash 本人): https://github.com/darrenstrash/quick-cliques

## 社内資料

- `docs/artifacts/` — Bron–Kerbosch の可視化・ガイド HTML 群
- `html/` — 列挙の動機・PCAM 解説
- メモリ `parallel-bench-baseline` — 逐次ベースライン実測値
