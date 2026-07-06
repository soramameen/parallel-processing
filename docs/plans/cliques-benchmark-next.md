# CLIQUES ベンチマーク — 次にやること

`docs/plans/cliques-benchmark.md` の実装（CLIQUES 本体・SNAP ローダ・測定
ハーネス・テスト）は完了済み。ここでは「その次」を記録する。全体ロードマップは
`docs/common/基本方針.md`（bron-kerbosch の並列化を卒業研究として仕上げる）を参照。

## 現在の状態（2026-07-06）

- ✅ `src/parallel_processing/cliques.py` — 論文 Algorithm 1 (Tomita CLIQUES) を
  SUBG/CAND/FINI 命名で実装。`bron_kerbosch_pivot` と出力一致。
- ✅ `src/parallel_processing/graph_io.py` — SNAP エッジリストローダ（gzip・自己
  ループ除外・孤立頂点登録）。
- ✅ `src/parallel_processing/benchmark.py` — 読み込み/列挙時間・頂点/辺数・
  クリーク数を出力。ca-AstroPh は期待値 36,427 と自動照合。
- ✅ `tests/test_cliques.py` — サンプル・ランダム50本・孤立頂点で pivot と一致。
- ✅ `ruff` / `mypy` 通過、`pytest` 全 green。
- ⏳ **未実施**: ca-AstroPh 実データでの 36,427 照合（成功基準 #2）。

## 1. ca-AstroPh 実測を完了させる（最優先・ブロッカー）

計画の成功基準 #2（クリーク数 36,427 の一致）が唯一残っている。実装側は完成済みで、
**データ取得だけが未達**。

### ブロッカー

Claude Code on the web のサンドボックスのネットワークポリシーが
`snap.stanford.edu` への接続を **403（policy denial）** で拒否するため、
`curl` でのダウンロードができなかった。

### 解決策（いずれか）

- **A. ローカル/許可された環境で実行する（推奨）**

  ```bash
  curl -L -o data/ca-AstroPh.txt.gz https://snap.stanford.edu/data/ca-AstroPh.txt.gz
  uv run python -m parallel_processing.benchmark data/ca-AstroPh.txt.gz
  ```

  期待出力: 頂点数 18,771 前後、**maximal cliques: 36,427**、`MATCH` 表示、
  読み込み時間・列挙時間。

- **B. Web セッションを続ける場合**は、環境のネットワークポリシーで
  `snap.stanford.edu`（または SNAP のミラー）を許可リストに追加してから
  上記を実行する。設定は
  https://code.claude.com/docs/en/claude-code-on-the-web を参照。

- **C.** データを手元で取得し、`data/ca-AstroPh.txt.gz` に配置してから
  ベンチマークを回す。`data/` は `.gitignore` 済みなのでコミットされない。

### 完了の定義

- クリーク数が 36,427 と一致（`MATCH` 表示）。
- 読み込み時間・列挙時間を記録し、以降の並列化の**ベースライン数値**として
  この doc か学習ログ（`docs/learnigs/`）に残す。
- 最大クリークサイズが 57 であること（論文 Table 1）も確認できると尚良い。

## 2. ベースライン測定の整理（並列化の前準備）

並列化の効果を語るには単体実装の数値を固めておく必要がある。

- 純 Python の列挙時間を複数回計測して中央値を取る（GC・キャッシュのブレ対策）。
- ボトルネックの当たりを付ける: `python -m cProfile -m parallel_processing.benchmark …`
  でピボット選択（`cand & graph[u]` の集合積）と分岐の再帰コストを確認。
- 頂点集合の表現を `set[int]` からビットセット（`int` のビット演算）に替えると
  集合積が速くなる余地がある。まずは計測してから判断する（早すぎる最適化は避ける）。
- 中規模データ（例: `email-Enron`, `ca-CondMat`）でもスケールを確認しておくと、
  並列化の効き方を比較しやすい。

## 3. 並列化の設計・実装（研究の本題）

`基本方針.md` のマイルストーン「並列処理を動かす／説明する／性能評価する」に対応。

- **並列化の粒度**: CLIQUES の探索木の**トップレベル分岐**（初回の
  `CAND \ Γ(pivot)` の各頂点）を独立タスクとして分配するのが素直。各枝は
  独立に部分クリークを列挙できる。
- **手法の候補**（1つ選んで深掘りする方針）:
  - `concurrent.futures.ProcessPoolExecutor`（GIL 回避、プロセス間はグラフを
    共有 or 各プロセスに複製）。
  - `multiprocessing` + 明示的なワークキュー（枝ごとの負荷が偏るので動的分配が要る）。
  - 参考として、真の性能は C/OpenMP 実装が要るが、`基本方針.md` の「一旦しないこと」
    に沿って今回は Python 並列に絞る。
- **負荷分散**: クリーク分布は枝ごとに大きく偏る（べき則的）。静的分割だと遅い枝で
  律速するので、動的スケジューリング（細かめのタスク + work stealing 的な分配）を検討。
- **正しさの担保**: 並列版も `cliques()`（単体版）と**同一集合**を返すことを
  `tests/` で検証する（既存の照合テストのパターンを流用）。

## 4. 性能評価と可視化

- 単体版 vs 並列版の**実行時間・スピードアップ・並列化効率**をワーカー数を変えて測定。
- グラフ化（matplotlib 等）してスケーラビリティを図示。`基本方針.md` の
  「単体実装との違いをグラフで視覚的に説明する」に対応。
- 「なぜこの結果になるか」の考察: Amdahl 則、負荷の偏り、プロセス間通信/複製の
  オーバーヘッド、データサイズ依存性など。

## 変更ファイルの見通し（今後）

- 新規 `src/parallel_processing/cliques_parallel.py`（並列版 CLIQUES）
- 新規 `tests/test_cliques_parallel.py`（単体版との一致 + ワーカー数不変性）
- 編集 `src/parallel_processing/benchmark.py`（単体/並列の切替と比較出力）
- 追記 `docs/learnigs/`（各回の測定値と考察のログ）
