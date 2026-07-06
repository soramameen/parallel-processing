# CLIQUES (Tomita) 論文準拠実装 + ca-AstroPh 測定

## Context

卒論の第一歩として、論文 *"On the overall and delay complexity of the CLIQUES and
Bron-Kerbosch algorithms"* (Conte & Tomita, TCS 2022) の **Algorithm 1: CLIQUES**
を論文の擬似コードに忠実に実装し、論文の実験（Table 1）で使われた実データ
**ca-AstroPh**（SNAP, 共著ネットワーク）に対して最大クリーク列挙を実行し、
クリーク数と実行時間を測定する。

これは `docs/plan.md` のマイルストーン「pivot 最適化を使った Tomita のアルゴリズムを
説明・実装・測定できるようになる」に対応する。この後の並列化・性能評価の
ベースラインとなる。

既存の `src/parallel_processing/bron_kerbosch.py` に `bron_kerbosch_pivot` があり
本質的には同じロジックだが、命名（r/p/x）と出力が BK 流。論文と対応づけて
説明できるよう、SUBG/CAND/FINI 命名で **新規に** CLIQUES を実装する。既存の
`bron_kerbosch_simple` / `bron_kerbosch_pivot` は正解照合用に残す。

## 検証可能な成功基準

1. 新規 CLIQUES が、既存テストの `SAMPLE_GRAPH` および 50 本のランダムグラフで
   `bron_kerbosch_pivot` と**同一のクリーク集合**を返す。
2. ca-AstroPh に対して実行し、**列挙されたクリーク数が 36,427**（Table 1 の
   #cliques）と一致する。
3. 実行時間（読み込みと列挙を分けて）とクリーク数がコンソールに出力される。

## 実装

### 1. 論文準拠 CLIQUES — `src/parallel_processing/cliques.py`（新規）

論文 Algorithm 1 に忠実に実装する。用語を擬似コードに合わせる:

- `SUBG` = 展開対象の頂点集合（初期は V）、`CAND` = 未処理候補（初期は V）、
  `FINI` = 処理済み (`SUBG \ CAND`)。
- ピボット `u` は `SUBG` の中で `|CAND ∩ Γ(u)|` を最大化する頂点（論文 p.3、
  worst-case optimal に効く選択）。
- 分岐は `CAND \ Γ(u)` の各頂点 `p` について。`Q ← Q ∪ {p}`、
  `SUBG_p = SUBG ∩ Γ(p)`、`CAND_p = CAND ∩ Γ(p)` で再帰。戻ったら
  `CAND ← CAND \ {p}`、`FINI ← FINI ∪ {p}`。
- `SUBG = ∅` で `Q` を極大クリークとして記録。

インターフェースは既存に合わせる:
- グラフ型 `Graph = dict[int, set[int]]`（無向、`bron_kerbosch.py` と同じ）。
- 返り値 `list[frozenset[int]]`、`bron_kerbosch.py` の `_sort_cliques` と同じ順序
  でソート（照合を単純にするため）。`_sort_cliques` を再利用するか同等関数を置く。
- Python の再帰で回すため冒頭で `sys.setrecursionlimit` を引き上げる（最大クリーク
  57 なので深さ自体は浅いが安全側に）。

計算量メモ: ピボット選択は毎ノードで `O(|SUBG|)` 回の集合積。ca-AstroPh 程度なら
純 Python でも現実的な時間で終わる想定（論文も「実装は最適化していない」）。

### 2. SNAP エッジリストのローダ — `src/parallel_processing/graph_io.py`（新規）

- `load_edge_list(path) -> Graph`: SNAP 形式（`#` で始まるコメント行、タブ/空白
  区切りの `u v`、無向グラフは両方向が別行で記載されうる）を読む。
- gzip (`*.txt.gz`) をそのまま読めるよう `gzip` 判定を入れる。
- 自己ループ (`u == v`) は除外、重複エッジは `set` で自然に吸収。頂点 ID は
  `int` に変換。孤立頂点も `graph` のキーとして必ず登録する（極大クリークとして
  効くため）。

### 3. 測定ハーネス — `src/parallel_processing/benchmark.py`（新規、`__main__` で実行）

- 引数でエッジリストのパスを受け取り（デフォルトで `data/ca-AstroPh.txt.gz`）、
  読み込み時間・頂点数/辺数、列挙時間、クリーク数を出力。
- `time.perf_counter` で読み込みと列挙を別々に計測。
- クリーク数を出力し、期待値 36,427 と目視照合できるようにする。

### 4. データ取得 — `data/`（gitignore 追加）

- ca-AstroPh を SNAP から取得: `https://snap.stanford.edu/data/ca-AstroPh.txt.gz`
  を `data/ca-AstroPh.txt.gz` に保存（`curl` で取得）。
- `.gitignore` に `data/` を追加し、生データはコミットしない。

### 5. テスト — `tests/test_cliques.py`（新規）

- `SAMPLE_GRAPH` で `EXPECTED`（既存テストと同じ手計算値）と一致。
- ランダムグラフ 50 本で `cliques()` == `bron_kerbosch_pivot()`（既存テストの
  パターンを流用）。
- 孤立頂点ケース。

## 変更ファイル一覧

- 新規 `src/parallel_processing/cliques.py`
- 新規 `src/parallel_processing/graph_io.py`
- 新規 `src/parallel_processing/benchmark.py`
- 新規 `tests/test_cliques.py`
- 編集 `.gitignore`（`data/` を追加）

既存の `bron_kerbosch.py` は変更しない（照合の基準として温存）。

## 検証手順（end-to-end）

1. `uv run pytest tests/test_cliques.py` — 正解照合・ランダム一致・孤立頂点が
   すべて green。
2. データ取得: `curl -L -o data/ca-AstroPh.txt.gz https://snap.stanford.edu/data/ca-AstroPh.txt.gz`
3. `uv run python -m parallel_processing.benchmark data/ca-AstroPh.txt.gz`
   → 頂点数 18,771 前後、**クリーク数 36,427**、読み込み時間・列挙時間が出力される
   ことを確認。クリーク数が 36,427 に一致すれば実装の正しさが裏づけられる。
4. `uv run ruff check` / `uv run mypy src` が通ること。
