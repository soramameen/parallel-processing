# Instances: the graphs H_k of Theorem 1

DIMACS files (`p edge n m`, then `e u v`, 1-based) of the graph H_k from Sec. 3 of `paper/tomita_lb.tex`
(and of `paper/cliques_short.tex`). H_k has n = 2k²+9k vertices, so for each target n in 10, 50, 100, …, 300 the
nearest H_k is used and the actual n is in the file name. Regenerate with `python3 code/gen_instances.py`.

| target n | file | k | n | m | maximal cliques | lower bound 2^(k+1)−1 on calls | calls in one run* |
|---:|---|---:|---:|---:|---:|---:|---:|
| 10 | `H1_n11.clq` | 1 | 11 | 17 | 17 | 3 | 21 |
| 50 | `H3_n45.clq` | 3 | 45 | 315 | 145 | 15 | 363 |
| 100 | `H5_n95.clq` | 5 | 95 | 1205 | 481 | 63 | 2161 |
| 150 | `H7_n161.clq` | 7 | 161 | 2975 | 1121 | 255 | 7923 |
| 200 | `H8_n200.clq` | 8 | 200 | 4280 | 1585 | 511 | 13872 |
| 250 | `H9_n243.clq` | 9 | 243 | 5913 | 2161 | 1023 | 23625 |
| 300 | `H10_n290.clq` | 10 | 290 | 7910 | 2861 | 2047 | 39921 |

\* `code/cliques.py` with the smallest-label pivot among ties and increasing-label processing order; it counts every
call of Expand, including the leaves through witnesses. The theorem guarantees 2^(k+1)−1 calls whose current clique
lies in the core M, for every run.

Vertex numbering: guards g_i = 1..k; core a_i = k+2i−1, b_i = k+2i; then the k+3 witnesses of each core vertex in the
order a_1, b_1, a_2, b_2, …. Non-edges: guard–guard, g_i with a_i and b_i, each witness with its core vertex, and
witness–witness. Each file's comment lines repeat these numbers.

For these small k, the number of calls is still dominated by polynomial terms; the exponential term 2^(k+1)−1 only
dominates for larger k.
