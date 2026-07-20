# CLIQUES 並列化：5候補（Codex xhigh との議論・実測を統合）

Tomita の CLIQUES（Bron–Kerbosch pivot 版、`src/parallel_processing/cliques.py`）を Python で
並列化するための設計メモ。Claude と Codex（reasoning: xhigh）が独立に検討し、実グラフ計測を
挟んで一往復議論した結果の統合版。ベンチ対象は SNAP `soc-sign-epinions`。

## 議論で確定した事実（Codex が実グラフで計測）

`soc-sign-epinions` は 131,828 頂点・711,210 辺・最大次数 3,558・degeneracy 121。
**並列化の前に効く発見が2つ**出た。

| カーネル | 実行時間 | 対元 175秒 |
|---|---:|---:|
| 元の global Tomita（set 版） | 約175秒 | 1.00× |
| degeneracy 順＋`set[int]` | 110.7秒 | 1.58× |
| **degeneracy 順＋`int` ビットセット** | **41.2秒** | **4.25×** |

count は 3 つとも 22,226,173、largest 94 で一致（正しさ検証済み）。**並列化に入る前に、
逐次のまま 4.25 倍が取れる**のが最大の収穫。並列8コアはこの上に乗る。

### 負荷偏りの実測

degeneracy 分割で最重の1タスクは 0.894 秒（全タスク時間 110 秒の 0.81%）、8コアの理想
一人当たり 13.8 秒に対し 6.5%。**「ハブ頂点1個が支配して speedup が頭打ち」という懸念は
否定された**。上位1,000タスクで時間の 91.5% を占めるので、その1,000個を個別・降順投入し、
残り13万頂点をバッチ化すれば動的分散で足りる。

forward-neighbourhood 内辺数（＝その頂点が最小になる三角形数）の分布:

| 集合 | 全三角形に占める割合 |
|---|---:|
| 最上位1頂点 | 0.144% |
| 上位10頂点 | 1.415% |
| 上位100頂点 | 12.693% |
| 上位1,000頂点 | 50.272% |
| 上位1%（1,318頂点） | 57.629% |

実際の探索時間ベース:

| 集合 | 全タスク時間に占める割合 |
|---|---:|
| 最重1タスク | 0.811% |
| 上位10タスク | 6.267% |
| 上位100タスク | 36.306% |
| 上位1,000タスク | 91.529% |

## 共通する正しさの条件

現在の探索は兄弟を処理するたび `cand` から `p` を除去している
（`cliques.py` の `expand`）。したがって並列タスクは単純な `(p, initial_cand)` ではなく
`(subg, cand_at_this_branch, depth)` を持つ必要があり、子タスク生成時も逐次版と同じ順序で
`cand` を更新する。各 worker は `(local_count, local_largest)` を返し、親で `sum`/`max`。
約2,200万葉で共有カウンタを更新するとロック競合が支配するため、**共有カウンタは使わない**。

---

## 候補1：degeneracy-local ビットセット × ProcessPool（本命）

**アイデア。** degeneracy（smallest-last）順序で各頂点 `v` を独立タスクにする。各クリークは
順序最小の頂点のタスクにだけ現れるので重複なし。さらに `v` のタスク内では、近傍 `N(v)` を
0 始まりに再番号付けし、`SUBG`/`CAND`/各頂点の局所隣接を Python の任意精度 `int` で表現。
intersection は `&`、`|CAND∩Γ(u)|` は `bit_count()`、頂点取り出しは最下位ビット抽出。
set 版の 2.69 倍速いカーネルがそのまま各ワーカーで走る。これは degeneracy による探索量削減
（1.58×）とビット演算の定数倍（1.70×）の**掛け算**。

**実装。**
- degeneracy 順序と `rank` を一度計算。タスク引数は**頂点番号 `v` だけ**。局所ビット行列は
  worker 内で構築（`N(v)` 全体＝幅は最大次数 3,558、最大でも raw 1.6MB、アクティブな
  worker 内だけなら現実的）。全頂点分の局所行列を事前保持しない。
- `ProcessPoolExecutor`（または `Pool.imap_unordered(chunksize=1)`）。graph は worker
  initializer で一度だけ渡す。worker 関数はモジュールトップレベル。
- 上位1,000〜2,000頂点（forward-neighbourhood 内辺数の降順）を個別・先頭投入、残りをバッチ化。
- 各 worker は `(local_count, local_largest)` を返し親で集約。共有カウンタは使わない。
- macOS の spawn 既定に注意（Python 3.14 は forkserver 既定）。Linux なら graph ロード後
  fork で Copy-on-Write が使える。

**期待と落とし穴。** カーネルで 4.25× ×並列 5〜7× を狙うが、両者が完全な掛け算になる保証は
ない。タスクが短くなるぶん scheduler overhead の比率が上がり、局所ビット構築コストとメモリ
帯域が並列効率を削りうる。

## 候補2：ルート分割 × ProcessPool（安全な基準線）

**アイデア。** 既存の探索木をそのまま使い、最初の `ext` の各枝を独立部分木としてプロセスへ
渡す。アルゴリズムを一切変えないので**重複・欠落のリスクが最小**。最初にこれで「並列が正しく
動く基準」を作る価値がある。

**実装。** 兄弟処理ごとに `cand` から `p` を除く逐次版の順序を再現する必要がある。`ext_order`
と `rank` を作り、枝 `p` の初期状態を `subg=graph[p]`, `cand={u∈graph[p] | rank[u]≥rank[p]}`
として構成。128,270 枝を個別 Future にせず、推定コストの近い枝を `workers×16〜64` のバッチに。

**期待と落とし穴。** 元 set カーネルのままなので絶対性能は候補1に劣る（対元 3〜6×）。枝の
計算量の偏り、spawn での graph 複製が主な問題。**位置づけは「候補1の正しさ・性能の対照実験」**。

## 候補3：適応的 frontier 分割 × work donation（保険）

**アイデア。** ルートだけでなく探索木を「タスク数が十分になるまで」浅く展開し、重い worker が
未処理の兄弟部分木を queue に戻す。不規則な最大クリーク探索では静的分割より
stack splitting/work stealing が有効という既存研究（Schmidt et al.）がある。

**実装。** 第一段階は真の work stealing を避け、親で
`while len(frontier) < workers*32: frontier.extend(split_once(heavy))` と frontier を作る
だけ。偏りが残る場合のみ `multiprocessing.Queue` で枯渇時に兄弟を寄付。`Manager().dict()` は
inner loop で使わない。

**期待と落とし穴。** 負荷分散は最良だが、状態 pickle・queue lock・終了判定が複雑。**ただし
実測で最重タスクが理想の 6.5% しかない以上、初期実装には不要**。実際の並列実行で「最後の
worker だけ長く残る」tail が出た場合、あるいは32コア以上／別データセットでのみ投入する。

## 候補4：free-threaded CPython × ThreadPoolExecutor

**アイデア。** 通常 CPython は GIL でこの pure-Python 再帰を thread 並列化できない。3.13t/3.14t
の free-threaded ビルドなら graph を**同一プロセスで共有したまま**複数コアを使える。pickle も
graph 複製も不要で、これが最大の利点。候補1のタスクをそのまま `ThreadPoolExecutor` に載せられる。

**実装。** graph は完全 read-only、`subg`/`cand`/count は thread-local。`sys._is_gil_enabled()`
で環境確認し、通常ビルド／1t／4t／8t を比較。

**期待と落とし穴。** free-threaded の単スレッド性能低下、dict/set 内部ロック、allocator/GC、
メモリ帯域競合で対プロセス 2〜5×。**graph 複製メモリが問題になったときの選択肢**として位置づけ、
3.14t で評価。

## 候補5：ビットセットのさらなる圧縮 — bitset の共有・SIMD 化（研究枠）

> 議論で最も動いた点。当初 Codex の第5候補は subinterpreter + `InterpreterPoolExecutor`
> だったが、Claude が「3.14限定・graph複製orCSR書き直しで multiprocessing への優位が薄い、
> 代わりにビットセットにすべき」と反論。Codex は実測（2.69×）で **subinterpreter を落とし、
> ビットセットを候補1に格上げ**することに同意した。第5枠にはビットセット路線をさらに押す
> 研究テーマを置く。

**アイデア。** 候補1のローカル `int` ビットセットは Python int 演算のオーバーヘッドが残る。密
再番号後の隣接行列を numpy `uint64` 配列や C 拡張／Cython、あるいは Roaring bitmap にして
intersection と popcount を SIMD 化すれば、カーネルにもう一段の定数倍が乗りうる。並列化と
直交するので掛け算になる。

**実装。** 局所 `adj` を `uint64` の CSR 的レイアウトに置き、intersection を numpy ベクトル
演算 or 小さな Cython カーネルに。worker 間で共有するなら `SharedMemory` に置くが、局所 adj を
別プロセスへ送ると利点が薄れる（Codex 指摘）。

**期待と落とし穴。** カーネル律速なら効くが、探索の分岐が予測不能で SIMD 化が効きにくい部分も
多い。**実装コスト高・優先度低の研究枠**。

---

## 比較表

| 候補 | 実装難度 | 負荷分散 | graphメモリ | 8コア推定（対元175秒） |
|---|---:|---:|---:|---:|
| 1. degeneracy-local bitset × ProcessPool | 中 | 中〜高 | fork有利/spawn複製 | 本命（4.25×カーネル ×並列） |
| 2. ルート ProcessPool | 低 | 中 | fork有利/spawn複製 | 3〜6× |
| 3. 適応 frontier × work donation | 高 | 高 | 候補1と同じ | 4〜7×（tail 時のみ） |
| 4. free-threading | 中 | 高 | 1コピー | 2〜5× |
| 5. bitset SIMD 化 | 高 | — | 複製 or SharedMemory | 研究枠 |

## まず試すべき順（両者合意）

1. **degeneracy＋ローカル `int` ビットセットの逐次版**を作り、正しさ（count 22,226,173／
   largest 94 一致）と ~41秒 を再現する。← ここで並列前に 4.25×
2. それを **ProcessPool 化**。重い頂点（上位1,000〜2,000）は個別・降順投入、軽量頂点は
   バッチ＋`imap_unordered(chunksize=1)` で動的配分。
3. **対照として** 元 set カーネルのルート ProcessPool 版（候補2）を測り、カーネル差と並列
   効率を切り分ける。
4. graph 複製メモリが問題なら **free-threaded 3.14t 版**（候補4）を比較。
5. 実測で**長い tail が出た場合だけ** 適応的 frontier 分割（候補3）を追加。

**性能本命は候補1。** 検証では毎回、逐次版との `(count, largest)` 一致・1/2/4/8 worker の
wall time・peak RSS・最長タスク時間を記録すると、カーネル効果／並列効果／負荷偏りを分離できる。

## 議論の決着（3論点）

- **論点1（ビットセット差し替え）**: 実測 2.69× で採用。subinterpreter は候補から除外。
- **論点2（ハブ偏り懸念）**: 最重タスクが理想の 6.5% にとどまり棄却。work donation は初期不要。
- **論点3（候補間 speedup 差）**: 「tail の違い」という当初説明を撤回。主因は degeneracy に
  よる 1.58× の探索量削減（`CAND` が最大次数 3,558 でなく degeneracy 121 で頭打ちになるため）。

## 補足：degeneracy とは

グラフ $G$ の degeneracy $d$ は「どの部分グラフを取り出しても必ず次数 $d$ 以下の頂点が存在する」
最小の $d$。smallest-last ordering（毎回最小次数頂点を末尾へ抜く貪欲法）で得た並びでは、各頂点の
forward neighbours 数が必ず $d$ 以下になる。これにより各頂点タスクの `CAND` を $d$ 個に閉じ込め
（探索量削減）、かつ各クリークを「順序最小の頂点」に一意に割り当てられる（並列分割で重複なし）。
Eppstein–Löffler–Strash の疎グラフ向け限界 $O(d \cdot n \cdot 3^{d/3})$ の実装版。
