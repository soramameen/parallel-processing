# CLAUDE.md

極大クリーク列挙（Bron–Kerbosch / Tomita / Eppstein）の並列化を扱う学部卒業研究のリポジトリ。
目標・方針の原本は `docs/common/基本方針.md`、要約は `MISSION.md`、教え方の方針は `NOTES.md`。

## やりとりの方針

- 回答・教材・ドキュメントはすべて日本語で書く。
- ユーザーは「ふわっと理解 → 質問攻め」のスタイルを好む。まず直感、数式は後。
- 圧縮された定義文は苦手。1文1主張にばらし、手を動かして確認できる形（具体例、インタラクティブな教材）にする。
- 数値・実験結果は創作しない。未測定のところは（未記入）と書く。
- しないこと: C/OpenMP 実装、複数アルゴリズムの試食、1日で焦って進めること。

## コマンド

環境は Nix + uv + direnv（`flake.nix`, `.envrc`）。Python 3.12、純 Python。

```sh
uv sync --all-groups          # 依存のインストール
uv run pytest                 # テスト
uv run ruff check .           # lint
uv run mypy .                 # 型チェック（strict）
cd thesis && make             # 卒論 PDF のビルド（latexmk + lualatex）
```

実験の再現手順は `REPRODUCE.md`。SNAP データセットは `data/` に置く（gitignore 済み）。

## 構成

- `src/parallel_processing/` — 実装
  - `bron_kerbosch.py`, `cliques.py`（Tomita CLIQUES）, `eppstein.py`, `eppstein_et.py`（早期終了版）
  - `eppstein_parallel*.py` — 並列版（spawn / fork / shm / interleave / reversed）
  - `benchmark*.py`, `phase_profile.py`, `workload_profile.py` — 測定
  - `hetero*.py`, `sched_sim.py` — 非対称コアのエミュレーションとシミュレーション
- `tests/` — pytest
- `artifacts/` — 生データ（`phase-profile.csv`, `workload-*.csv`, `linux/`）
- `thesis/` — 卒論（`main.tex`, `chapters/`）、ゼミ資料（`seminar-2026-10/`）
- `docs/` — 実験記録（`eppstein-experiments.md`, `hetero-experiments.md`）、計画（`plans/`）、図、スライド
- `lessons/`, `learning-records/`, `reference/` — 学習教材と論文
- `index.html`, `research.html` — GitHub Pages（`main` への push で `.github/workflows/deploy-pages.yml` が公開）

## 測定の注意

- 絶対値は再現しない（背景負荷や熱ドリフトで 26〜32% 動く）。比べるのは相対比較で、比較する条件は時間的に隣接させて測る。
- 各条件 3 回走らせて最小値を採る。全実験でクリーク数の一致を assert する。
- M4（P コア4 + E コア6）の結果と、Linux クラウド環境でのエミュレーション結果は区別して書く。

## 残件

`TODO.md` を参照。
