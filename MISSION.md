# Mission: Bron–Kerbosch / Tomita CLIQUES の並列化（学部卒業研究）

## Why
学部の卒業研究として、最大クリーク列挙アルゴリズム（Bron–Kerbosch、特に pivot 最適化を使った
Tomita の CLIQUES）を自分で理解し、Python で並列化した上で定量的に性能評価する。結果をグラフ
などで視覚的に説明し、なぜその結果になるのかを考察できる状態にして発表する。

## Success looks like
- pivot 最適化を使った Tomita の CLIQUES アルゴリズムの動作原理を、自分の言葉で説明できる。
- 単体（逐次）実装を動かし、その性能を計測できる。
- 現状実装済みの並列版（root-split × ProcessPoolExecutor、`cliques_parallel.py`）の並列化戦略
  を説明できる：どこを分割しているか、なぜ重複・欠落なく正しいか、共有カウンタを使わない理由。
- 並列版の性能（1/2/4/8 worker のスピードアップ）を計測し、逐次版との違いをグラフで説明できる。
- 「なぜ理想的な線形スピードアップにならないのか」（プロセス生成コスト・グラフ複製・枝ごとの
  負荷偏り・spawn のオーバーヘッドなど）を考察として言語化できる。

## Constraints
- 研究は焦らず進める（1日で詰め込みすぎない）。
- 実装は Python 並列処理に絞る（C/OpenMP 実装はしない）。
- 実データは SNAP のデータセット（`data/` 配下：ca-AstroPh, ca-HepPh, soc-sign-epinions）を使う。

## Out of scope
- C 言語・OpenMP による実装。
- 多数のアルゴリズムを網羅的に比較すること（今は Tomita CLIQUES の並列化に集中。他アルゴリズム
  との比較は余裕があれば後で）。
- 理論的な計算量解析の深追い（論文の結果を引用する程度に留め、自前で証明はしない）。
