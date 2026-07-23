# 実験の再現手順

卒論・Notion「研究Note」に載せた数字を出し直すための手順。
清書された結果と考察は Notion（研究Note）、生データは `artifacts/phase-profile.csv` と `artifacts/workload-*.csv` が正。

## 前提と注意

- 測定環境: Apple M4 MacBook（P コア4 + E コア6、16GB）、macOS、Python 3.12（uv 管理）、純 Python。
- **絶対値はそのままは再現しない**。実測で Chrome の開閉だけで 26%、約1.5時間の連続ベンチ後の熱ドリフトで 32% 動いた。再現できるのは相対比較（手法間の比、worker スケーリング、フェーズの内訳）である。
- 測定プロトコル（全実験共通）:
  - 各条件 3 回走らせ最小値を採用する（CSV には全 run が残る）。
  - 測定前に `ps aux -r | head` で背景プロセスを確認し、スナップショットを記録する（例: `artifacts/env-snapshot-shm-bench.txt`）。前セッションの負荷生成ループ等の残骸がいれば止めてから測る。
  - 比較したい条件は時間的に隣接させて測る（別の日・別セッションの値と絶対値比較をしない）。
  - 重い測定は冷えたマシンで行う。

## セットアップ

```sh
uv sync
mkdir -p data
# SNAP データセット（gitignore 済み）を data/ に置く
curl -o data/ca-AstroPh.txt.gz        https://snap.stanford.edu/data/ca-AstroPh.txt.gz
curl -o data/ca-HepPh.txt.gz          https://snap.stanford.edu/data/ca-HepPh.txt.gz
curl -o data/soc-sign-epinions.txt.gz https://snap.stanford.edu/data/soc-sign-epinions.txt.gz
# E コア測定の CSV 行をタグで区別するための別名リンク（コードは無変更で済ませるため）
ln -s soc-sign-epinions.txt.gz data/soc-sign-epinions-ecore.txt.gz
```

合成グラフ 7 種は `graph_gen.py` が seed 固定で生成するので、ダウンロード不要かつ毎回同一。
全実験でクリーク数の一致が assert されるため、どの run も結果の正しさの相互チェックを兼ねる。

## 実験一覧（Notion の節 → コマンド）

### 1. 逐次比較: Tomita CLIQUES 対 Eppstein（「逐次版の測定結果」）

```sh
uv run python -m parallel_processing.compare_cliques --repeat 3 \
  data/ca-AstroPh.txt.gz data/ca-HepPh.txt.gz data/soc-sign-epinions.txt.gz
```

倍率（Tomita 時間 ÷ Eppstein 時間）の表がここから出る。両者を同一プロセス内で交互に反復するのが単発計測の振れ対策。

### 2. 素朴な並列化とバッチサイズ（「並列版の実装」）

```sh
uv run python -m parallel_processing.benchmark_eppstein data/soc-sign-epinions.txt.gz          # 逐次基準
uv run python -m parallel_processing.benchmark_eppstein_parallel data/soc-sign-epinions.txt.gz 8  # バッチ512（既定）
```

バッチ 512 は `eppstein_parallel.py` の `BATCH_SIZE`。バッチ 64 の測定は次の phase_profile（`--batch 64` が既定）で行った。

### 3. 負荷分布（「負荷分布の測定」: 上位1%が94.7% など）

```sh
uv run python -m parallel_processing.workload_profile data/soc-sign-epinions.txt.gz
```

→ `artifacts/workload-<dataset>.csv` と `artifacts/workload-summary.json`。ca-AstroPh、ca-HepPh も同様。

### 4. フェーズ分解（「フェーズ別時間の分解」: 9グラフ × w=1,2,4,8、block/spawn）

```sh
uv run python -m parallel_processing.phase_profile --workers 1,2,4,8 --repeat 3 \
  data/ca-AstroPh.txt.gz data/ca-HepPh.txt.gz data/soc-sign-epinions.txt.gz
```

→ `artifacts/phase-profile.csv` に追記（`strategy=block`）。合成 6 種は suite として自動で回る。

### 5. 配分戦略の比較（「配分戦略の比較」: reversed / interleave）

```sh
uv run python -m parallel_processing.phase_profile --strategy reversed   --workers 4,8 --repeat 3 --skip-suite data/soc-sign-epinions.txt.gz
uv run python -m parallel_processing.phase_profile --strategy interleave --workers 4,8 --repeat 3 --skip-suite data/soc-sign-epinions.txt.gz
```

基準の block も同一セッションで再測定して比較する（プロトコル参照）。

### 6. P/E コアの切り分け（「P/E コアの切り分け実験」「E コアの速度の正体」）

```sh
# E コア固定（background QoS）。ecore 別名を渡すと CSV 上で行が区別できる
taskpolicy -b uv run python -m parallel_processing.phase_profile \
  --strategy interleave --workers 1,4 --repeat 3 --skip-suite data/soc-sign-epinions-ecore.txt.gz

# 純計算ループ（クロック制限の切り分け。通常と taskpolicy -b の両方で3回ずつ）
python3 -c 'import time; s=0; t=time.perf_counter()
for i in range(100_000_000): s+=i
print(time.perf_counter()-t)'
```

純計算ループの回数は当時の記録に残っていない。再現するのは絶対秒数（P で 0.64 秒）ではなく P 対 E の速度比（約 5.75 倍）である。

注意: taskpolicy -b は優先度も下げるため、得られる E コア速度比（0.26）は下限値。全力 E コアの r≈0.43 は第三者の powermetrics 測定（クロック値）と自前の IPC 係数からの推定であり、確定には sudo で powermetrics を回して実クロックを観測する（未実施）。

### 7. 共有メモリアプローチ（「共有メモリアプローチ」: fork / shm、9グラフ × w=1,4,8）

```sh
for s in fork shm; do
  uv run python -m parallel_processing.phase_profile --strategy $s --workers 1,4,8 --repeat 3 \
    data/ca-AstroPh.txt.gz data/ca-HepPh.txt.gz data/soc-sign-epinions.txt.gz
done
```

2 手法は同一セッションで連続実行する。2026-07-21 実行時の環境記録は `artifacts/env-snapshot-shm-bench.txt`。

## phase-profile.csv の読み方

- 1 行 = 1 run。`strategy` 列が block / reversed / interleave / fork / shm を区別する（fork・shm はグラフ配布方式の変種で、バッチ配分は block と同一）。
- 論文・Notion の表の値は `(graph, strategy, workers)` ごとに `total_s` 最小の行。
- `graph=soc-sign-epinions-ecore.txt.gz` の行は taskpolicy -b（E コア固定）の測定。データは soc-sign-epinions と同一。
- `busy_max/busy_min/busy_sum` は worker 別稼働秒。idle% = 1 − busy_sum / (workers × compute_s)。
- 古い行（strategy 列追加前）は block でバックフィルされている。
