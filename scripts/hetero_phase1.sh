#!/bin/sh
# Phase 1-3 reproduction on soc-sign-epinions (docs/plans/hetero-cores.md).
# Each repeat cycles through every combination, so slow spells of the host
# land on all of them alike; the F×1 run per repeat is the throughput unit.
set -eu
G=data/soc-sign-epinions.txt.gz
PERIOD=${PERIOD:-4000}
for rep in 1 2 3; do
  B="uv run python -m parallel_processing.benchmark_hetero run --batch 64 --period $PERIOD --repeat 1 --tag phase1-rep$rep"
  echo "=== repeat $rep $(date -u +%H:%M:%S)"
  $B --cores "F" --strategy block "$G"
  $B --cores "F,F,F,F" --strategy block,interleave "$G"
  $B --cores "F,F,S,S;F,S,S,S" --r 0.43,0.26,0.75 --strategy block,interleave "$G"
  $B --cores "S,S,S,S" --r 0.43 --strategy block,interleave "$G"
done
echo "=== done $(date -u +%H:%M:%S)"
