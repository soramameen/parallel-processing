# 思い出しロードマップ（最小限・約5日・7ステップ）

1日1時間ほどで約5日。各ステップは「まず可視化・教材で感覚をつかむ → コードを読む → 卒論の該当節を読む → 問いに答える」の順で進める。パスはリポジトリ soramameen/parallel-processing のもの。

## Step0 全体像（15分・1日目）
- 読む: `MISSION.md`、`docs/common/基本方針.md`、`thesis/chapters/01-introduction.tex` の「本研究のアプローチ」と「本研究の貢献」
- 問い: この研究を一言で言うと？何を速くしようとした？

## Step1 極大クリーク列挙とは（30分・1日目）
- 読む: `docs/slides/enumeration-motivation.html`、2章「グラフとクリーク」
- 問い: 「極大」と「最大」の違いは？5頂点くらいの小さなグラフで、極大クリークを手で全部書き出せる？

## Step2 Bron–Kerbosch とピボット（1時間・2日目）
- 触る: `docs/artifacts/bron-kerbosch-visualizer.html` → `docs/artifacts/bron-kerbosch-pivot-visualizer.html`（迷ったら `docs/artifacts/bron-kerbosch-guide.html`）
- コード: `src/parallel_processing/bron_kerbosch.py` の `bron_kerbosch_simple`（L29）と `bron_kerbosch_pivot`（L51）、`cliques.py` の `cliques`（L42、Tomita CLIQUES）
- 問い: R・P・X はそれぞれ何の集合？X がないと何が困る？ピボットを選ぶと、どの枝を探さずに済む？

## Step3 縮退順序と Eppstein（1時間・2〜3日目）
- 触る: `lessons/0001-degeneracy-peeling.html`、`learning-records/0001-degeneracy-definition-confusion.md`
- コード: `eppstein.py` の `degeneracy_ordering`（L36）、`eppstein_cliques`（L86）、`_bron_kerbosch_degeneracy`（L126）
- 卒論: 2章「縮退数と縮退順序」「Eppstein アルゴリズム」、5章「逐次版の比較：CLIQUES 対 Eppstein」
- 問い: 縮退数とは（頂点を剥がしていく操作で説明できる？）。外側ループで頂点 v ごとに P と X をどう作る？soc-sign-epinions の逐次実行（約95秒）で Eppstein のほうが速いのはなぜ？

## Step4 並列化の基本形（1時間・3日目）
- 触る: `lessons/0002-outermost-layer.html`、`learning-records/0002-outermost-layer.md`
- コード: `eppstein_parallel.py` の `BATCH_SIZE`（L37）、`_init_worker`（L46）、`_count_batch`（L72）、`count_eppstein_cliques_parallel`（L155）
- 卒論: 4章「最外層の独立性とカウント版への限定」「プロセスプールによる基本実装」
- 問い: 最外層の頂点ごとの仕事はなぜ互いに独立？なぜ列挙ではなく「数えるだけ」の版にした？worker を起動するとき何を渡している？

## Step5 並列化の工夫（1.5時間・4日目）
- 触る: `lessons/0003-batch-strategies.html`、`reference/batch-strategies.html`、`learning-records/0003-batch-strategies-and-pe-cores.md`
- コード: `eppstein_parallel_interleave.py`、`eppstein_parallel_reversed.py`（配分戦略）、`eppstein_parallel_fork.py`、`eppstein_parallel_shm.py` の `_pack`（L36）（グラフの届け方）
- 卒論: 4章「バッチ配分の三つの戦略」「グラフを worker へ届ける二つの方式」、5章「負荷分布の測定」
- 問い: 仕事量が一部の頂点に偏るのはなぜ（上位1%に94.7%）？interleave はそれをどう和らげる？spawn・fork・shm はそれぞれグラフをどうやって worker に届けていて、何が遅くなる原因？

## Step6 ベンチ結果の読み方（1.5時間・4〜5日目）
- 読む: `REPRODUCE.md`（測定プロトコル）、`docs/eppstein-experiments.md`、`artifacts/phase-profile.csv` と `phase_profile.py`
- 卒論: 5章「フェーズ別時間の分解」から最後の節まで
- 問い: startup と compute は何を測っている？9グラフのうち6グラフで並列化が損になるのはなぜ？E コアの速度比 0.26 が「下限の実測値」で、0.43 が「推定値」なのはなぜ？4.9倍（クリーン環境での interleave）と約3.6倍（shm）は条件がどう違う？

## Step7 卒論で説明できる状態にする（1時間・5日目）
- 読む: `06-conclusion.tex` の「本研究のまとめ」と「得られた知見」、`thesis/slides.pptx`
- ゴール: 4つの知見（起動の固定費、負荷の偏り、P/E コアの非対称性、メモリ共有方式）をそれぞれ一文で言えて、全体を5分で口頭説明できること。
