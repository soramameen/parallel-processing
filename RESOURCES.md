# Bron–Kerbosch / Tomita CLIQUES 並列化 Resources

`docs/references.md` に既存のより網羅的な参考文献リストがある（すべて実在確認済み）。ここでは
教材作成に直接使う一次資料だけを抜粋・整理する。

## Knowledge

- [Tomita, Tanaka, Takahashi (2006) "The worst-case time complexity for generating all maximal
  cliques and computational experiments"](https://doi.org/10.1016/j.tcs.2006.06.015) — CLIQUES
  アルゴリズムの原論文。pivot を `|CAND∩Γ(u)|` 最大で選ぶことで最悪計算量 `O(3^{n/3})` を達成する
  根拠。Use for: 逐次アルゴリズムそのもの・pivot 選択の正当性の説明。
- [Conte, Tomita (2021) "On the overall and delay complexity of the CLIQUES and Bron-Kerbosch
  algorithms"](https://doi.org/10.1016/j.tcs.2021.11.008) — 本リポジトリの `cliques.py` が実装
  している論文。Table 1 のデータセット（ca-AstroPh 等）と #cliques 期待値の出典。Use for: 実装が
  何に忠実かを説明するとき、期待値照合の根拠を示すとき。
- [ssomers/Bron-Kerbosch (GitHub)](https://github.com/ssomers/Bron-Kerbosch) — 「degeneracy 順序
  生成 → 最初の反復 → N 個の並列ネスト反復」という第1階層タスク分割方式。本リポジトリの
  `cliques_parallel.py`（root-split）と設計思想が最も近い公開実装。Use for: 「自分の実装は先行例
  とどう同じでどう違うか」を説明する対照。
- `docs/plans/cliques-parallelization-ideas.md`（本リポジトリ内） — Claude と Codex が実測を挟んで
  詰めた5つの並列化候補の設計メモ。候補2（root-split × ProcessPool）が現在の実装そのもの。
  Use for: なぜこの分割方式を選んだか、正しさの条件（`cand -= {p}` の兄弟順序再現）を確認すると
  き。
- [Gustafson (1988) "Reevaluating Amdahl's Law"](https://doi.org/10.1145/42411.42415) — 固定問題
  サイズでの strong scaling 上限（Amdahl）と、問題サイズを増やす weak scaling（Gustafson）の対比。
  Use for: 「8 コアで線形にスケールしない」現象を理論的に位置づけるとき。
- [Rao, Kumar (1987) "Parallel depth-first search"](https://doi.org/10.1007/BF01379244) — 並列
  深さ優先探索における作業分配方式が性能を強く左右することを示した古典。Use for: root-split の
  ような静的分割がなぜ負荷偏りに弱いかを説明するとき。

## Wisdom (Communities)

- 現時点で未選定（gap）。この題材は学部卒論という性質上、リアルタイムのコミュニティより指導教員
  との議論が主な検証の場になる想定。もし外部コミュニティで壁打ちしたくなった場合は
  r/algorithms や r/compsci が候補だが、まだ実際に使う判断はしていない。

## Gaps

- 並列版の性能実測を裏付ける一次資料（本リポジトリ自身の計測ログ）は `docs/plans/` や
  auto-memory 側にあり、まだこの Resources には明示リンクしていない。計測が進むごとに追記する。
