# Mission

**Bron–Kerbosch（ピボット版 = Tomita/CLIQUES）の並列化を、学部卒業研究として発表できるレベルで完成させる。**

詳細は `docs/common/基本方針.md` が原本。要点:

- アルゴリズム（ピボット最適化含む）を自分の言葉で説明できる
- 逐次実装 → 大規模データ（soc-sign-epinions ほか）でベンチ → 並列化 → 定量評価
- 結果をグラフで視覚的に示し、なぜその結果になるかの考察を立てる

## 現在の学習フェーズ

Eppstein–Löffler–Strash (2010) の degeneracy ordering を理解中。
並列化の分割戦略（root-split）の理論的裏付けとして重要。

## しないこと

- C/OpenMP 実装、複数アルゴリズムの試食、1日で焦って進めること
