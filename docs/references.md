# 参考文献

CLIQUES（Tomita）並列化の卒業研究に関する参考文献。Web 検索（WebSearch/WebFetch）で
実在を確認したもののみ掲載。要約は各文献の位置づけと、本研究での使いどころを示す。

## 新規性メモ

「Python の multiprocessing で Tomita CLIQUES をルート分割し、SNAP 実グラフ
（soc-sign-epinions 等）で 1/2/4/8 コアのスケーラビリティと負荷不均衡を測定・考察する」
という**全要素の組み合わせに一致する先行研究・公開物は見つからなかった**（論文・GitHub・
技術ブログ・CiNii いずれも）。ただしアルゴリズムとしては新規ではなく、以下が最も近い:

- **ルート分割（第1階層をタスク化）** → ssomers/Bron-Kerbosch と同じ発想
- **degeneracy-local な頂点ごと分割** → Das et al. の ParMCE と実質同型

学部卒論に求められるのは手法の新規性ではなく「既知手法を自分で実装・再現し、実測して
なぜその結果になるかを説明できること」なので問題ない。むしろ Das et al. という確立した
比較対象があることで「先行研究は C++ で N 倍、本研究は Python で M 倍、差の理由は…」と
書きやすい。学内リポジトリの日本語卒論は Web から見えないため、研究室内の類似テーマの
有無は指導教員に別途確認すること。

---

## A. 最大クリーク列挙（MCE）の並列化 — 本命の関連研究

### A1. Das, Sanei-Mehri, Tirthapura (2018 / 2020)
"Shared-Memory Parallel Maximal Clique Enumeration"
- 会議版: HiPC 2018（25th IEEE Int'l Conf. on High Performance Computing）
  arXiv: https://arxiv.org/abs/1807.09417
- ジャーナル拡張版: ACM Transactions on Parallel Computing (TOPC), 2020,
  DOI: 10.1145/3380936, arXiv: https://arxiv.org/abs/2001.11433
- **要約**: Tomita の CLIQUES（TTT）を並列化した **ParTTT** と、頂点ごとの誘導部分グラフに
  分割する **ParMCE**（亜種 ParMCEDegree / ParMCEDegen / ParMCETri）を提案。ParMCE は各頂点
  v の近傍で誘導される部分問題を独立に並列処理し、重複除去の工夫を持つ。
- **数値**: ParTTT は逐次 TTT に対し 12〜14 倍。ParMCE は 32 スレッドで 15〜31 倍。Wikipedia
  ネットワーク（約180万頂点・3650万辺・最大クリーク1.3億超）で ParTTT 16.5 倍、最適化版
  ParMCE 21.5 倍。既存手法が5時間で終わらない入力を 32 コアで1分未満に短縮。
- **本研究での使いどころ**: 最重要の直接比較対象。候補1（degeneracy-local 分割）は ParMCE と
  本質同型。「C++/共有メモリ 32 スレッドの ParMCE に対し、本研究は Python/multiprocessing で
  どこまで迫れるか」という対比で引用する。

### A2. Schmidt, Samatova, Thomas, Park (2009)
"A scalable, parallel algorithm for maximal clique enumeration"
- Journal of Parallel and Distributed Computing, 69(4), pp. 417-428
- DOI: https://doi.org/10.1016/j.jpdc.2009.01.003
- **要約**: 探索木の分解による並列深さ優先バックトラック探索。緩い同期のみとし、**on-demand
  work stealing と work stack splitting** を組み合わせてアイドル時間を最小化（stealer が他
  スレッドのスタック底部からノードをランダムに盗む）。
- **数値**: Cray XT 上で実世界の生物ネットワークに対し **2048 プロセッサまで線形スケーリング**。
- **本研究での使いどころ**: 負荷不均衡と work-stealing 考察の中心引用。「本研究の静的ルート
  分割では 8 コアで頭打ち、その原因は負荷不均衡。動的分散（work-stealing）で解決できることは
  Schmidt らが 2048 並列まで線形達成で示している」という論法に使う（＝候補3の裏付け）。

### A3. Almasri, Chang, El Hajj, Nagi, Xiong, Hwu (2023)
"Parallelizing Maximal Clique Enumeration on GPUs"
- PACT 2023, DOI: 10.1109/PACT58117.2023.00022, arXiv: https://arxiv.org/abs/2212.01473
- **要約**: Bron–Kerbosch の探索木を**深さ優先で独立部分木ごとに並列実行**（従来の GPU 研究は
  幅優先で深い階層で木が爆発する問題があった）。動的負荷分散用ワーカーリスト、部分誘導部分
  グラフ、除外頂点集合のコンパクト表現でメモリを抑制。
- **数値**: 単一 GPU で最先端の並列 CPU 実装に対し幾何平均 4.9 倍（最大 16.7 倍）。
- **本研究での使いどころ**: GPU という別アーキテクチャの関連研究。「探索木を独立部分木に分けて
  並列化する」着想が本研究のルート分割と共通することを示す。

### A4. Wei, Chen, Tsai (2021)
"Accelerating the Bron-Kerbosch Algorithm for Maximal Clique Enumeration Using GPUs"
- IEEE Transactions on Parallel and Distributed Systems, 32(9), pp. 2352-2366
- DOI: 10.1109/TPDS.2021.3067053
- **要約**: Bron–Kerbosch の探索木トラバーサルを GPU 上で実行する先行研究。A3 が「従来の GPU
  研究は幅優先」と批判する対象の一つ。
- **本研究での使いどころ**: GPU 系関連研究の補足。

### A5. Svendsen, Mukherjee, Tirthapura — PECO
"Parallel Enumeration of Cliques using Ordering" (Journal of Parallel and Distributed Computing)
- 同著者グループの関連: "Mining Maximal Cliques from a Large Graph using MapReduce"
- **要約**: MapReduce 向け。頂点の全順序（total ordering）で負荷分散されたワーク分割を実現し、
  重複クリークの発生と後処理での重複除去を不要にする。100万頂点・数千万辺級で 64 プロセッサ
  までスケール。
- **本研究での使いどころ**: 「順序を使って重複なく分割する」着想（degeneracy 順による一意割当）
  の先行例。分散環境（MapReduce）版の関連研究。
- 注: 具体的スピードアップ数値は検索範囲では未確認。

### A6. Lu, Gu, Grossman — dMaximalCliques
"A Distributed Algorithm for Enumerating All Maximal Cliques and Maximal Clique Distribution"
- IEEE ICDM Workshops 2010, DOI: 10.1109/ICDMW.2010.100
- **要約**: shared-nothing 分散環境（クラスタ）向け。80 ノードのクラスタで数百万頂点級グラフ
  のクリーク情報を数分で取得。
- **本研究での使いどころ**: 分散メモリ版の代表例。詳細スピードアップは未確認。

---

## B. 逐次アルゴリズムの土台 — 理論背景

### B1. Conte, Tomita (2021)
"On the overall and delay complexity of the CLIQUES and Bron-Kerbosch algorithms"
- Theoretical Computer Science (Elsevier), ScienceDirect: S0304397521006538
- 会議版: WALCOM 2021, LNCS 12635, DOI: 10.1007/978-3-030-68211-8_16
- **要約**: 本研究が実装した論文そのもの。CLIQUES / Bron–Kerbosch の delay 複雑度を解析し、
  CLIQUES は Ω(3^(n/6)) の delay を持ち、いかなる pivot 戦略でも P≠NP の限り多項式 delay 版は
  作れないことを証明。130 超のグラフで実験し、実性能は最悪ケースよりずっと良いと報告
  （＝ output-sensitive に振る舞う）。
- **本研究での使いどころ**: アルゴリズムの出典。Table 1 のデータセット（ca-AstroPh, ca-HepPh,
  soc-sign-epinions 等）と #cliques の期待値照合に使用。逐次の理論的限界を示す。

### B2. Tomita, Tanaka, Takahashi (2006)
"The worst-case time complexity for generating all maximal cliques and computational experiments"
- Theoretical Computer Science, 363(1), pp. 28-42
- **要約**: CLIQUES アルゴリズムの原論文。pivot を |CAND∩Γ(u)| 最大で選ぶことで最悪計算量
  O(3^(n/3)) を達成（これは n 頂点グラフが持ちうる極大クリークの最大数と同オーダー＝worst-case
  optimal）。
- **本研究での使いどころ**: 実装したアルゴリズムの一次出典。pivot 選択の正当性の根拠。

### B3. Eppstein, Löffler, Strash (2010)
"Listing All Maximal Cliques in Sparse Graphs in Near-Optimal Time"
- ISAAC 2010。拡張版 "Listing All Maximal Cliques in Large Sparse Real-World Graphs"
  arXiv:1103.0318
- **要約**: degeneracy ordering に基づき、外側ループを degeneracy 順に固定して再帰する変種を
  提示。疎グラフで近最適な最悪計算量 O(d·n·3^(d/3))（d は degeneracy）を達成。
- **本研究での使いどころ**: 候補1（degeneracy-local 分割）の理論的根拠。degeneracy 順による
  探索量削減と、各クリークを「順序最小の頂点」に一意割当（並列分割で重複なし）する仕組みの出典。

### B4. Bron, Kerbosch (1973)
"Algorithm 457: Finding All Cliques of an Undirected Graph"
- Communications of the ACM, 16(9), pp. 575-577, DOI: 10.1145/362342.362367
- **要約**: 極大クリーク列挙の古典。pivot による枝刈りの原型を提示。Tomita の CLIQUES はこの
  pivot 選択規則を最悪計算量最適化したもの。
- **本研究での使いどころ**: アルゴリズムの系譜の起点。「Tomita = BK pivot + pivot 選択規則」の
  説明で参照。
- 注: 書誌は一般に知られた古典のもの。今回の検索対象外だったため、引用時は原典を確認すること。

---

## C. 並列化の一般理論 — 考察の裏付け

### C1. Rao, Kumar (1987)
"Parallel depth-first search. Part I: Implementation / Part II: Analysis"
- International Journal of Parallel Programming, 16(6), pp. 479-499 / 501-519
- **要約**: 並列深さ優先探索の古典。作業分配方式（work distribution scheme）が性能を強く左右
  することを示し、負荷分散方式の効果を分析（MIMD 上で15パズルを題材に検証）。
- **本研究での使いどころ**: 「探索木の枝ごとに仕事量が不均衡」という問題を論じる根拠。

### C2. Gustafson (1988)
"Reevaluating Amdahl's Law"
- Communications of the ACM, 31(5), DOI: 10.1145/42411.42415
- **要約**: Amdahl の法則（固定問題サイズでの strong scaling 上限）に対し、問題サイズを
  プロセッサ数に応じて拡大する weak scaling の視点（Gustafson の法則）を提示。
- **本研究での使いどころ**: 「8 コアで線形にスケールしない」を理論的に位置づける標準的引用。

### C3. Gendron, Crainic (1994)
"Parallel Branch-and-Bound Algorithms: Survey and Synthesis"
- Operations Research, 42(6), pp. 1042-1066, DOI: 10.1287/opre.42.6.1042
- **要約**: 並列分枝限定法の体系的サーベイと分類。負荷分散戦略の分類軸を提供。
- **本研究での使いどころ**: 負荷分散手法の分類を参照する総説として。

### C4. Grama, Kumar (1999)
"State of the Art in Parallel Search Techniques for Discrete Optimization Problems"
- IEEE Transactions on Knowledge and Data Engineering, 11(1), pp. 28-35
- DOI: 10.1109/69.755612
- **要約**: 離散最適化問題（分枝限定法含む）の並列探索手法のサーベイ。負荷分散手法の分類を提供。
- **本研究での使いどころ**: B&B 文脈での負荷分散議論の補強。

---

## D. 近い公開実装（差分を明示すべき相手）

### D1. ssomers/Bron-Kerbosch (GitHub)
- https://github.com/ssomers/Bron-Kerbosch
- **要約**: Rust/C#/C++/Python/F#/Java/Kotlin/Go の多言語で Bron–Kerbosch の性能比較。並列版は
  「degeneracy 順序生成 → 最初の反復 → N 個の並列ネスト反復」という**第1階層をタスク分割する
  方式**で、本研究のルート分割（候補2）と設計思想が最も近い。
- **本研究との違い**: 並列化は主にスレッドベース（Python 版はマルチプロセスでない可能性）、
  ベンチは人為的ランダムグラフのみで SNAP 実グラフ未使用、コア数ごとのスピードアップ・負荷
  不均衡の学術的考察ではなく言語間性能比較が主眼。
- **使いどころ**: 卒論の「先行研究との違い」で最も近い比較対象として明示する。

### D2. ryanrossi/pmc — Parallel Maximum Clique Library
- https://github.com/ryanrossi/pmc （WWW'14 論文あり）
- **要約**: SNAP 系実世界グラフで並列最大クリーク探索をベンチマーク。branch-and-bound の並列分割。
- **本研究との違い**: C++（OpenMP）実装。最大クリーク「1つ」を高速に見つけるのが目的で、全極大
  クリークを列挙する CLIQUES/Tomita 型の全列挙ではない。
- **使いどころ**: 「最大クリーク発見」と「極大クリーク全列挙」の違いを説明する対比。

### D3. NetworkX `find_cliques`
- **要約**: Tomita, Tanaka, Takahashi のアルゴリズムを実装しているが**逐次実行のみ**、並列化機能
  は無い。
- **使いどころ**: 「標準ライブラリにも並列版が無い」＝本研究の動機づけに使える。

---

## 未確認・要追加調査

- **PbitMCE** — Eppstein 系アルゴリズムのビットベース・マルチコア並列実装として言及はあるが、
  著者名・会議名・スピードアップ数値を Web 検索で特定できず。候補1/bitset（候補5）を進める場合は
  PDF 直接取得での追加調査を推奨。
- **MPI の現代的（2015 年以降）MCE 実装**、**Spark 固有実装** は今回のクエリでは発見できず。
- 学内リポジトリの**日本語卒論・修論**は Web から見えないため、研究室内の類似テーマの有無は
  指導教員に確認すること。
