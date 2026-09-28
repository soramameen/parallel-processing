## calibration

| period | task | s=0.75 | s=0.5 | s=0.43 | s=0.26 |
|---|---|---|---|---|---|
| 4 ms | loop | 0.786 | 0.523 | 0.446 | 0.267 |
| 4 ms | heavy | 0.748 | 0.493 | 0.420 | 0.244 |
| 4 ms | mid | 0.743 | 0.488 | 0.420 | 0.242 |
| 4 ms | light | 0.743 | 0.502 | 0.417 | 0.241 |
| 10 ms | loop | 0.753 | 0.498 | 0.429 | 0.255 |
| 10 ms | heavy | 0.742 | 0.480 | 0.416 | 0.246 |
| 10 ms | mid | 0.742 | 0.478 | 0.408 | 0.241 |
| 10 ms | light | 0.729 | 0.468 | 0.397 | 0.235 |
| 100 ms | loop | 0.783 | 0.534 | 0.449 | 0.271 |
| 100 ms | heavy | 0.755 | 0.502 | 0.442 | 0.258 |
| 100 ms | mid | 0.766 | 0.494 | 0.431 | 0.257 |
| 100 ms | light | 0.741 | 0.489 | 0.415 | 0.250 |

## phase1

| cores | r | strategy | compute | throughput | ideal | efficiency | idle | idle (weighted) | busy sum | runs | max/min |
|---|---|---|---|---|---|---|---|---|---|---|---|
| F | - | block | 198.8 s | 1.00 | 1.00 | 100% | 0.1% | 0.1% | 199 s | 3 | 1.00 |
| F,F,F,F | - | block | 64.9 s | 3.06 | 4.00 | 77% | 22.8% | 22.8% | 200 s | 3 | 1.09 |
| F,F,F,F | - | interleave | 51.1 s | 3.89 | 4.00 | 97% | 0.6% | 0.6% | 203 s | 3 | 1.15 |
| F,F,S,S | 0.26 | block | 143.1 s | 1.39 | 2.49 | 56% | 32.5% | 42.4% | 386 s | 3 | 1.29 |
| F,F,S,S | 0.26 | interleave | 81.5 s | 2.44 | 2.49 | 98% | 0.4% | 0.5% | 325 s | 3 | 1.01 |
| F,F,S,S | 0.43 | block | 83.6 s | 2.38 | 2.84 | 84% | 12.4% | 11.6% | 293 s | 3 | 1.14 |
| F,F,S,S | 0.43 | interleave | 72.2 s | 2.75 | 2.84 | 97% | 0.8% | 0.8% | 286 s | 3 | 1.04 |
| F,F,S,S | 0.75 | block | 66.0 s | 3.01 | 3.49 | 86% | 13.2% | 13.0% | 229 s | 3 | 1.26 |
| F,F,S,S | 0.75 | interleave | 58.9 s | 3.38 | 3.49 | 97% | 0.9% | 0.9% | 233 s | 3 | 1.09 |
| F,S,S,S | 0.26 | block | 158.2 s | 1.26 | 1.73 | 73% | 20.2% | 26.2% | 505 s | 3 | 1.18 |
| F,S,S,S | 0.26 | interleave | 119.3 s | 1.67 | 1.73 | 96% | 0.3% | 0.3% | 475 s | 3 | 1.01 |
| F,S,S,S | 0.43 | block | 99.0 s | 2.01 | 2.26 | 89% | 8.2% | 8.4% | 364 s | 3 | 1.42 |
| F,S,S,S | 0.43 | interleave | 91.6 s | 2.17 | 2.26 | 96% | 0.6% | 0.6% | 364 s | 3 | 1.04 |
| F,S,S,S | 0.75 | block | 66.9 s | 2.97 | 3.24 | 92% | 6.8% | 6.3% | 250 s | 3 | 1.32 |
| F,S,S,S | 0.75 | interleave | 64.4 s | 3.09 | 3.24 | 95% | 1.1% | 1.1% | 255 s | 3 | 1.10 |
| S,S,S,S | 0.43 | block | 161.0 s | 1.23 | 1.68 | 73% | 21.9% | 21.9% | 503 s | 3 | 1.06 |
| S,S,S,S | 0.43 | interleave | 127.8 s | 1.56 | 1.68 | 93% | 0.4% | 0.4% | 509 s | 3 | 1.06 |

## sim

F×1 compute 198.8 s vs summed per-vertex profile 197.7 s (costs rescaled by 1.006); per-core speed with four busy cores: 0.978

| cores | r | strategy | measured | sim | error | sim with contention | error | jittered p10-p90 | measured inside |
|---|---|---|---|---|---|---|---|---|---|
| F,F,F,F | - | block | 64.9 s | 65.1 s | +0.4% | 66.6 s | +2.6% | 63.7-69.2 s | yes |
| F,F,F,F | - | interleave | 51.1 s | 49.7 s | -2.8% | 50.8 s | -0.6% | 50.7-51.1 s | no |
| F,F,S,S | 0.26 | block | 143.1 s | 178.8 s | +24.9% | 182.7 s | +27.7% | 118.4-187.5 s | yes |
| F,F,S,S | 0.26 | interleave | 81.5 s | 80.0 s | -1.9% | 81.8 s | +0.3% | 81.7-82.2 s | no |
| F,F,S,S | 0.43 | block | 83.6 s | 100.3 s | +20.0% | 102.6 s | +22.7% | 83.3-112.3 s | yes |
| F,F,S,S | 0.43 | interleave | 72.2 s | 70.0 s | -3.0% | 71.6 s | -0.8% | 71.4-71.9 s | no |
| F,F,S,S | 0.75 | block | 66.0 s | 75.6 s | +14.5% | 77.3 s | +17.1% | 68.2-88.8 s | no |
| F,F,S,S | 0.75 | interleave | 58.9 s | 57.0 s | -3.2% | 58.2 s | -1.1% | 58.1-58.5 s | no |
| F,S,S,S | 0.26 | block | 158.2 s | 173.8 s | +9.9% | 177.7 s | +12.3% | 154.9-191.0 s | yes |
| F,S,S,S | 0.26 | interleave | 119.3 s | 115.0 s | -3.6% | 117.5 s | -1.5% | 117.3-118.2 s | no |
| F,S,S,S | 0.43 | block | 99.0 s | 102.4 s | +3.4% | 104.7 s | +5.8% | 103.7-136.3 s | no |
| F,S,S,S | 0.43 | interleave | 91.6 s | 88.0 s | -4.0% | 89.9 s | -1.8% | 89.8-90.4 s | no |
| F,S,S,S | 0.75 | block | 66.9 s | 77.3 s | +15.5% | 79.0 s | +18.1% | 69.6-89.8 s | no |
| F,S,S,S | 0.75 | interleave | 64.4 s | 61.4 s | -4.6% | 62.8 s | -2.4% | 62.7-63.1 s | no |
| S,S,S,S | 0.43 | block | 161.0 s | 155.0 s | -3.7% | 158.5 s | -1.6% | 151.7-164.8 s | yes |
| S,S,S,S | 0.43 | interleave | 127.8 s | 118.3 s | -7.4% | 121.0 s | -5.3% | 120.7-121.6 s | no |

## phase3

### 3a soc-sign-epinions.txt.gz period=4000 fast_scale=- migrate=0

| cores | r | schedule | compute | throughput | ideal | efficiency | idle | idle (weighted) | busy sum | runs | max/min |
|---|---|---|---|---|---|---|---|---|---|---|---|
| F,F,S,S | 0.43 | block | 96.0 s | 2.07 | 2.84 | 73% | 20.1% | 21.0% | 307 s | 3 | 1.38 |
| F,F,S,S | 0.43 | block1 | 75.2 s | 2.64 | 2.84 | 93% | 1.3% | 1.3% | 297 s | 3 | 1.03 |
| F,F,S,S | 0.43 | block16 | 79.8 s | 2.49 | 2.84 | 88% | 6.6% | 6.2% | 298 s | 3 | 1.18 |
| F,F,S,S | 0.43 | interleave | 75.1 s | 2.65 | 2.84 | 93% | 0.1% | 0.1% | 300 s | 3 | 1.02 |
| F,F,S,S | 0.43 | lpt | 75.4 s | 2.64 | 2.84 | 93% | 1.2% | 1.3% | 298 s | 3 | 1.02 |
| F,F,S,S | 0.43 | lpt-oracle | 75.0 s | 2.65 | 2.84 | 93% | 0.0% | 0.0% | 300 s | 3 | 1.02 |
| F,F,S,S | 0.43 | static-oracle@0.26 | 83.6 s | 2.38 | 2.84 | 84% | 18.0% | 11.0% | 274 s | 3 | 1.01 |
| F,F,S,S | 0.43 | static-oracle@0.43 | 78.2 s | 2.54 | 2.84 | 90% | 3.0% | 4.0% | 303 s | 3 | 1.09 |
| F,F,S,S | 0.43 | static-oracle@0.6 | 97.7 s | 2.04 | 2.84 | 72% | 16.5% | 22.9% | 326 s | 3 | 1.02 |
| F,F,S,S | 0.43 | static-oracle@1.0 | 128.9 s | 1.54 | 2.84 | 54% | 29.9% | 41.6% | 362 s | 3 | 1.04 |
| F,F,S,S | 0.43 | static@0.43 | 76.2 s | 2.61 | 2.84 | 92% | 2.0% | 2.1% | 299 s | 3 | 1.02 |

### 3b soc-sign-epinions.txt.gz period=4000 fast_scale=1,1,0.8 migrate=0

| cores | r | schedule | compute | throughput | ideal | efficiency | idle | idle (weighted) | busy sum | runs | max/min |
|---|---|---|---|---|---|---|---|---|---|---|---|
| F,F,S,S | 0.43 | interleave | 90.0 s | 2.21 | 2.84 | 78% | 0.1% | 0.1% | 360 s | 3 | 1.01 |
| F,F,S,S | 0.43 | lpt | 88.9 s | 2.24 | 2.84 | 79% | 0.9% | 1.0% | 352 s | 3 | 1.04 |
| F,F,S,S | 0.43 | static-oracle@0.43 | 94.8 s | 2.10 | 2.84 | 74% | 7.6% | 4.8% | 350 s | 3 | 1.02 |
| F,F,S,S | 0.43 | static-oracle@0.53 | 91.4 s | 2.18 | 2.84 | 77% | 2.1% | 2.4% | 358 s | 3 | 1.02 |

### 3c soc-sign-epinions.txt.gz period=10000 fast_scale=- migrate=0

| cores | r | schedule | compute | throughput | ideal | efficiency | idle | idle (weighted) | busy sum | runs | max/min |
|---|---|---|---|---|---|---|---|---|---|---|---|
| F,F,S,S | 0.43 | block | 95.0 s | 2.09 | 2.82 | 74% | 20.5% | 21.2% | 302 s | 2 | 1.01 |
| F,F,S,S | 0.43 | lpt | 75.9 s | 2.62 | 2.82 | 93% | 1.8% | 2.2% | 298 s | 2 | 1.00 |
| F,F,S,S | 0.43 | static-oracle@0.43 | 77.3 s | 2.57 | 2.82 | 91% | 2.2% | 3.0% | 302 s | 2 | 1.03 |

### 3c soc-sign-epinions.txt.gz period=100000 fast_scale=- migrate=0

| cores | r | schedule | compute | throughput | ideal | efficiency | idle | idle (weighted) | busy sum | runs | max/min |
|---|---|---|---|---|---|---|---|---|---|---|---|
| F,F,S,S | 0.43 | block | 91.6 s | 2.17 | 2.87 | 76% | 18.5% | 16.9% | 299 s | 2 | 1.00 |
| F,F,S,S | 0.43 | lpt | 76.7 s | 2.59 | 2.87 | 90% | 0.4% | 0.5% | 306 s | 2 | 1.01 |
| F,F,S,S | 0.43 | static-oracle@0.43 | 77.3 s | 2.57 | 2.87 | 90% | 1.6% | 1.9% | 304 s | 2 | 1.02 |

### 3d-base ca-HepPh.txt.gz period=4000 fast_scale=- migrate=0

| cores | r | schedule | compute | throughput | ideal | efficiency | idle | idle (weighted) | busy sum | runs | max/min |
|---|---|---|---|---|---|---|---|---|---|---|---|

### 3d ca-HepPh.txt.gz period=4000 fast_scale=- migrate=0

| cores | r | schedule | compute | throughput | ideal | efficiency | idle | idle (weighted) | busy sum | runs | max/min |
|---|---|---|---|---|---|---|---|---|---|---|---|
| F,F,F,F | 1.0 | block | 0.365 s | 3.34 | 4.00 | 84% | 15.6% | 15.6% | 1 s | 3 | 1.15 |
| F,F,F,F | 1.0 | lpt | 0.329 s | 3.71 | 4.00 | 93% | 0.4% | 0.4% | 1 s | 3 | 1.14 |
| F,F,F,F | 1.0 | split | 0.360 s | 3.39 | 4.00 | 85% | 0.7% | 0.7% | 1 s | 2 | 1.01 |
| F,F,S,S | 0.26 | block | 0.812 s | 1.50 | 2.49 | 60% | 26.8% | 36.5% | 2 s | 5 | 1.44 |
| F,F,S,S | 0.26 | giants | 0.655 s | 1.86 | 2.49 | 75% | 4.1% | 5.0% | 3 s | 5 | 1.42 |
| F,F,S,S | 0.26 | interleave | 0.608 s | 2.01 | 2.49 | 81% | 1.3% | 1.2% | 2 s | 4 | 1.66 |
| F,F,S,S | 0.26 | lpt | 0.661 s | 1.85 | 2.49 | 74% | 10.2% | 12.4% | 2 s | 4 | 1.30 |
| F,F,S,S | 0.26 | lpt-oracle | 0.586 s | 2.08 | 2.49 | 84% | 1.4% | 0.9% | 2 s | 5 | 1.12 |
| F,F,S,S | 0.26 | split | 0.660 s | 1.85 | 2.49 | 74% | 9.5% | 11.7% | 2 s | 5 | 1.36 |
| F,F,S,S | 0.26 | split-giants | 0.649 s | 1.88 | 2.49 | 76% | 10.1% | 12.8% | 2 s | 5 | 1.20 |
| F,F,S,S | 0.26 | static-oracle@0.26 | 0.660 s | 1.85 | 2.49 | 74% | 10.6% | 15.8% | 2 s | 4 | 1.27 |
| F,F,S,S | 0.43 | block | 0.536 s | 2.28 | 2.84 | 80% | 10.7% | 11.4% | 2 s | 5 | 1.27 |
| F,F,S,S | 0.43 | giants | 0.465 s | 2.63 | 2.84 | 92% | 1.4% | 1.6% | 2 s | 5 | 1.28 |
| F,F,S,S | 0.43 | interleave | 0.525 s | 2.33 | 2.84 | 82% | 2.3% | 2.3% | 2 s | 4 | 1.06 |
| F,F,S,S | 0.43 | lpt | 0.477 s | 2.56 | 2.84 | 90% | 1.4% | 1.5% | 2 s | 4 | 1.18 |
| F,F,S,S | 0.43 | lpt-oracle | 0.476 s | 2.56 | 2.84 | 90% | 2.3% | 2.5% | 2 s | 2 | 1.06 |
| F,F,S,S | 0.43 | split | 0.499 s | 2.44 | 2.84 | 86% | 3.3% | 3.6% | 2 s | 4 | 1.12 |
| F,F,S,S | 0.43 | split-giants | 0.466 s | 2.62 | 2.84 | 92% | 0.9% | 0.9% | 2 s | 5 | 1.36 |
| F,F,S,S | 0.43 | static-oracle@0.43 | 0.507 s | 2.41 | 2.84 | 85% | 6.0% | 7.6% | 2 s | 5 | 1.08 |

### 3e soc-sign-epinions.txt.gz period=4000 fast_scale=- migrate=1

| cores | r | schedule | compute | throughput | ideal | efficiency | idle | idle (weighted) | busy sum | runs | max/min |
|---|---|---|---|---|---|---|---|---|---|---|---|
| F,F,S,S | 0.26 | block | 98.4 s | 2.02 | 2.49 | 81% | 19.7% | 16.5% | 316 s | 2 | 1.01 |
| F,F,S,S | 0.26 | interleave | 85.5 s | 2.32 | 2.49 | 93% | 0.3% | 0.3% | 341 s | 2 | 1.01 |
| F,F,S,S | 0.26 | lpt | 86.1 s | 2.31 | 2.49 | 93% | 2.1% | 2.7% | 337 s | 2 | 1.02 |
| F,F,S,S | 0.26 | reversed | 91.0 s | 2.19 | 2.49 | 88% | 9.9% | 13.6% | 328 s | 2 | 1.06 |
| F,F,S,S | 0.26 | static-oracle@0.26 | 85.4 s | 2.33 | 2.49 | 94% | 1.3% | 1.8% | 337 s | 2 | 1.02 |
| F,F,S,S | 0.43 | block | 88.9 s | 2.24 | 2.84 | 79% | 20.5% | 19.0% | 283 s | 2 | 1.00 |
| F,F,S,S | 0.43 | interleave | 75.5 s | 2.63 | 2.84 | 93% | 0.0% | 0.0% | 302 s | 2 | 1.05 |
| F,F,S,S | 0.43 | lpt | 74.7 s | 2.66 | 2.84 | 94% | 0.4% | 0.5% | 297 s | 2 | 1.00 |
| F,F,S,S | 0.43 | reversed | 79.6 s | 2.50 | 2.84 | 88% | 8.2% | 10.3% | 292 s | 2 | 1.00 |
| F,F,S,S | 0.43 | static-oracle@0.43 | 76.9 s | 2.59 | 2.84 | 91% | 2.1% | 2.8% | 301 s | 2 | 1.02 |

### 3e soc-sign-epinions.txt.gz period=4000 fast_scale=- migrate=0

| cores | r | schedule | compute | throughput | ideal | efficiency | idle | idle (weighted) | busy sum | runs | max/min |
|---|---|---|---|---|---|---|---|---|---|---|---|
| F,F,S,S | 0.26 | block | 211.4 s | 0.94 | 2.49 | 38% | 45.1% | 59.5% | 464 s | 2 | 1.02 |
| F,F,S,S | 0.26 | interleave | 85.9 s | 2.31 | 2.49 | 93% | 0.8% | 0.9% | 341 s | 2 | 1.00 |
| F,F,S,S | 0.26 | lpt | 94.3 s | 2.11 | 2.49 | 85% | 8.3% | 10.5% | 346 s | 2 | 1.02 |
| F,F,S,S | 0.26 | reversed | 161.3 s | 1.23 | 2.49 | 50% | 37.1% | 46.0% | 406 s | 2 | 1.00 |
| F,F,S,S | 0.26 | static-oracle@0.26 | 91.3 s | 2.18 | 2.49 | 88% | 5.2% | 7.7% | 346 s | 2 | 1.01 |
| F,F,S,S | 0.43 | block | 108.2 s | 1.84 | 2.84 | 65% | 28.3% | 30.4% | 311 s | 2 | 1.24 |
| F,F,S,S | 0.43 | interleave | 75.4 s | 2.64 | 2.84 | 93% | 0.1% | 0.1% | 302 s | 2 | 1.01 |
| F,F,S,S | 0.43 | lpt | 75.0 s | 2.65 | 2.84 | 93% | 1.6% | 1.8% | 295 s | 2 | 1.03 |
| F,F,S,S | 0.43 | reversed | 84.7 s | 2.35 | 2.84 | 83% | 8.5% | 11.6% | 310 s | 2 | 1.11 |
| F,F,S,S | 0.43 | static-oracle@0.43 | 77.9 s | 2.55 | 2.84 | 90% | 2.6% | 3.5% | 304 s | 2 | 1.03 |

## inrun

| schedule | period | run | compute | fast-core speed | slow-core speed | slow / fast |
|---|---|---|---|---|---|---|
| static-oracle@0.26 | 4 ms | 3a-rep1 | 83.7 s | 0.940 | 0.380 | 0.404 |
| static-oracle@0.26 | 4 ms | 3a-rep2 | 83.6 s | 0.941 | 0.380 | 0.403 |
| static-oracle@0.26 | 4 ms | 3a-rep3 | 84.4 s | 0.934 | 0.380 | 0.406 |
| static-oracle@0.26 | 4 ms | 3e-rep1 | 92.5 s | 0.936 | 0.224 | 0.239 |
| static-oracle@0.26 | 4 ms | 3e-rep2 | 91.3 s | 0.950 | 0.225 | 0.237 |
| static-oracle@0.43 | 4 ms | 3a-rep1 | 84.9 s | 0.933 | 0.363 | 0.389 |
| static-oracle@0.43 | 4 ms | 3a-rep2 | 80.6 s | 0.932 | 0.371 | 0.399 |
| static-oracle@0.43 | 4 ms | 3a-rep3 | 78.2 s | 0.936 | 0.382 | 0.408 |
| static-oracle@0.43 | 4 ms | 3e-rep1 | 80.6 s | 0.928 | 0.371 | 0.400 |
| static-oracle@0.43 | 4 ms | 3e-rep2 | 77.9 s | 0.934 | 0.382 | 0.409 |
| static-oracle@0.6 | 4 ms | 3a-rep1 | 99.7 s | 0.933 | 0.378 | 0.406 |
| static-oracle@0.6 | 4 ms | 3a-rep2 | 97.8 s | 0.938 | 0.379 | 0.404 |
| static-oracle@0.6 | 4 ms | 3a-rep3 | 97.7 s | 0.937 | 0.381 | 0.407 |
| static-oracle@1.0 | 4 ms | 3a-rep1 | 128.9 s | 0.942 | 0.385 | 0.408 |
| static-oracle@1.0 | 4 ms | 3a-rep2 | 133.7 s | 0.922 | 0.375 | 0.407 |
| static-oracle@1.0 | 4 ms | 3a-rep3 | 130.8 s | 0.939 | 0.380 | 0.404 |
| static@0.43 | 4 ms | 3a-rep1 | 77.6 s | 0.940 | 0.376 | 0.400 |
| static@0.43 | 4 ms | 3a-rep2 | 76.2 s | 0.941 | 0.382 | 0.406 |
| static@0.43 | 4 ms | 3a-rep3 | 76.4 s | 0.945 | 0.384 | 0.406 |
| static-oracle@0.43 | 10 ms | 3c-rep1 | 77.3 s | 0.933 | 0.385 | 0.413 |
| static-oracle@0.43 | 10 ms | 3c-rep2 | 79.3 s | 0.934 | 0.375 | 0.401 |
| static-oracle@0.43 | 100 ms | 3c-rep1 | 77.3 s | 0.915 | 0.388 | 0.424 |
| static-oracle@0.43 | 100 ms | 3c-rep2 | 78.9 s | 0.920 | 0.381 | 0.414 |

## m4

M4 per-vertex costs, total 98.0 s on a P core; cores 4 P + 6 E, contention ignored

| workers | strategy | r | pinned | busy | migrating | busy | M4 measured | busy |
|---|---|---|---|---|---|---|---|---|
| 4 | block | 0.26 | 32.5 s | 98 s | 32.5 s | 98 s | 33.3 s | 106 s |
| 4 | block | 0.43 | 32.5 s | 98 s | 32.5 s | 98 s | 33.3 s | 106 s |
| 4 | reversed | 0.26 | 24.5 s | 98 s | 24.5 s | 98 s | 32.7 s | 131 s |
| 4 | reversed | 0.43 | 24.5 s | 98 s | 24.5 s | 98 s | 32.7 s | 131 s |
| 4 | interleave | 0.26 | 24.5 s | 98 s | 24.5 s | 98 s | 36.7 s | 147 s |
| 4 | interleave | 0.43 | 24.5 s | 98 s | 24.5 s | 98 s | 36.7 s | 147 s |
| 8 | block | 0.26 | 69.6 s | 275 s | 25.7 s | 125 s | 25.9 s | 139 s |
| 8 | block | 0.43 | 33.9 s | 150 s | 21.1 s | 121 s | 25.9 s | 139 s |
| 8 | reversed | 0.26 | 67.3 s | 233 s | 26.0 s | 132 s | 28.5 s | 175 s |
| 8 | reversed | 0.43 | 40.7 s | 163 s | 23.8 s | 123 s | 28.5 s | 175 s |
| 8 | interleave | 0.26 | 20.4 s | 156 s | 19.6 s | 155 s | 24.7 s | 198 s |
| 8 | interleave | 0.43 | 17.6 s | 137 s | 17.3 s | 137 s | 24.7 s | 198 s |

(clean-session interleave w=8: 18.24 s)

## sweep

### makespan / lower bound over r (1.000 = no schedule does better)

F,F,S,S

| schedule | r=0.26 | r=0.43 | r=0.5 | r=0.75 | r=1 |
|---|---|---|---|---|---|
| block | 1.608 | 1.163 | 1.210 | 1.508 | 1.310 |
| interleave | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| lpt | 1.019 | 1.016 | 1.029 | 1.003 | 1.006 |
| lpt-oracle | 1.023 | 1.006 | 1.001 | 1.002 | 1.000 |
| static-oracle@TRUE | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

F,S,S,S

| schedule | r=0.26 | r=0.43 | r=0.5 | r=0.75 | r=1 |
|---|---|---|---|---|---|
| block | 1.456 | 1.497 | 1.434 | 1.257 | 1.310 |
| interleave | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| lpt | 1.018 | 1.008 | 1.001 | 1.003 | 1.006 |
| lpt-oracle | 1.007 | 1.004 | 1.000 | 1.001 | 1.000 |
| static-oracle@TRUE | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

4F+6S (M4 shape)

| schedule | r=0.26 | r=0.43 | r=0.5 | r=0.75 | r=1 |
|---|---|---|---|---|---|
| block | 3.940 | 2.848 | 2.647 | 2.152 | 1.909 |
| interleave | 1.066 | 1.004 | 1.005 | 1.003 | 1.001 |
| lpt | 1.150 | 1.061 | 1.030 | 1.010 | 1.009 |
| lpt-oracle | 1.016 | 1.013 | 1.008 | 1.000 | 1.003 |
| static-oracle@TRUE | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

### misestimated r: static-oracle@r_hat makespan / lpt makespan

F,F,S,S

| true r | r_hat=0.15 | r_hat=0.26 | r_hat=0.35 | r_hat=0.43 | r_hat=0.5 | r_hat=0.6 | r_hat=0.75 | r_hat=1 |
|---|---|---|---|---|---|---|---|---|
| 0.26 | 1.076 | 0.982 | 1.233 | 1.430 | 1.586 | 1.784 | 2.039 | 2.379 |
| 0.43 | 1.223 | 1.117 | 1.042 | 0.984 | 1.091 | 1.227 | 1.402 | 1.636 |
| 0.6 | 1.378 | 1.258 | 1.174 | 1.108 | 1.057 | 0.991 | 1.132 | 1.321 |

F,S,S,S

| true r | r_hat=0.15 | r_hat=0.26 | r_hat=0.35 | r_hat=0.43 | r_hat=0.5 | r_hat=0.6 | r_hat=0.75 | r_hat=1 |
|---|---|---|---|---|---|---|---|---|
| 0.26 | 1.206 | 0.983 | 1.149 | 1.263 | 1.346 | 1.442 | 1.553 | 1.682 |
| 0.43 | 1.567 | 1.276 | 1.108 | 0.992 | 1.057 | 1.132 | 1.219 | 1.321 |
| 0.6 | 1.927 | 1.570 | 1.363 | 1.220 | 1.118 | 0.998 | 1.075 | 1.164 |

4F+6S (M4 shape)

| true r | r_hat=0.15 | r_hat=0.26 | r_hat=0.35 | r_hat=0.43 | r_hat=0.5 | r_hat=0.6 | r_hat=0.75 | r_hat=1 |
|---|---|---|---|---|---|---|---|---|
| 0.26 | 0.987 | 0.869 | 1.067 | 1.215 | 1.328 | 1.468 | 1.640 | 1.859 |
| 0.43 | 1.266 | 1.116 | 1.017 | 0.943 | 1.031 | 1.139 | 1.273 | 1.443 |
| 0.6 | 1.469 | 1.295 | 1.180 | 1.094 | 1.029 | 0.947 | 1.059 | 1.200 |

### non-constant r (M4 shape, nominal r = 0.43)

| schedule | constant r | H3 | H4 | H3 + H4 |
|---|---|---|---|---|
| interleave | 30.16 s | 34.50 s | 27.80 s | 31.18 s |
| lpt | 31.86 s | 35.01 s | 29.24 s | 31.11 s |
## workers

this host's soc costs (197.7 s at full speed); cores 4 fast + 6 slow; workers start on the fast cores

| r | workers | block pinned | block migrating | interleave pinned | interleave migrating | lower bound |
|---|---|---|---|---|---|---|
| 0.26 | 4 | 64.7 s | 64.7 s | 49.4 s | 49.4 s | 49.4 s |
| 0.26 | 6 | 132.6 s | 55.2 s | 45.3 s | 44.1 s | 43.7 s |
| 0.26 | 8 | 102.7 s | 44.4 s | 41.1 s | 39.6 s | 39.2 s |
| 0.26 | 10 | 140.1 s | 53.6 s | 37.9 s | 36.0 s | 35.5 s |
| 0.43 | 4 | 64.7 s | 64.7 s | 49.4 s | 49.4 s | 49.4 s |
| 0.43 | 6 | 64.6 s | 46.0 s | 40.7 s | 40.7 s | 40.7 s |
| 0.43 | 8 | 79.8 s | 45.0 s | 34.6 s | 34.6 s | 34.6 s |
| 0.43 | 10 | 85.6 s | 49.7 s | 30.2 s | 30.1 s | 30.0 s |
| 0.6 | 4 | 64.7 s | 64.7 s | 49.4 s | 49.4 s | 49.4 s |
| 0.6 | 6 | 65.0 s | 51.3 s | 38.1 s | 38.0 s | 38.0 s |
| 0.6 | 8 | 59.0 s | 41.2 s | 31.1 s | 31.0 s | 30.9 s |
| 0.6 | 10 | 62.3 s | 41.2 s | 26.3 s | 26.2 s | 26.0 s |

