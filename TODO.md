# 卒論 TODO

目標: 2026-07-28 頃までに提出できる形に固める。
ドラフトは `thesis/`（`latexmk -lualatex main.tex` でビルド）。本文中の残件は `[TODO: ...]` でマーク済み。

## 前半（1〜3日目）: 中身の確定

- [ ] 先行研究の本文読み込みと3章の加筆（最大の穴）
  - [ ] Eppstein 2010（arXiv:1006.5440）
  - [ ] Eppstein-Strash 2011/2013（arXiv:1103.0318）
  - [ ] ParMCE（arXiv:1807.09417）
  - [ ] 余裕があれば Schmidt 2009
- [ ] 全章の通読検証（数値の転記ミス、章間の用語の揺れ、論理の飛び。Notion の記録と突き合わせ）
- [ ] 安い実験の穴埋め
  - [ ] powermetrics 10分（冷えた朝、sudo、`!` プレフィックスで実行）: E コアの実クロックを観測し r≈0.43 を推定から実測に格上げ
  - [ ] gc.freeze で fork を再測定: CoW 遅延コスト説の切り分け（shm の compute が fork より速い件）

## 中盤（4〜5日目）: 提出物の形

- [ ] 図の作成（phase-profile.csv から生成）
  - [ ] speedup 曲線（soc: spawn/fork/shm × workers）
  - [ ] フェーズ分解の積み上げ棒
  - [ ] 合成グラフの外観図（Notion の画像を figure 化、2章の TODO）
- [ ] 付録: 9グラフ × 2手法の全数表（5章の TODO）
- [ ] 概要（背景・手法・結果・結論の4段落、本文確定後）
- [ ] 序論の応用例に一次資料を付ける（1章の TODO）
- [ ] 研究室テンプレートの入手と差し替え（documentclass、表紙、文献スタイル、分量規定、締切の確認）

## 後半（6〜7日目）: レビューと修正

- [ ] 指導教員に仮完成版を投げる（**3日目頃に前倒しで一度見せるのが安全**）
- [ ] レビュー反映、最終ビルド確認

## 論文以外

- [ ] `thesis/` をコミットする
- [ ] worktree `feat/eppstein` の push（頼まれたら conventional-commit-push）
- [ ] docs/eppstein-experiments.md と Artifact「実験記録」の Notion 同期（必要になったら）
