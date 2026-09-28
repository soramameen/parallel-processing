#!/bin/sh
# Phase 3 schedule comparison (docs/plans/hetero-cores.md).
# 3a: schedules and misestimated r on soc, F,F,S,S at r=0.43.
# 3b: the same with fast cores slowing as more of them run (H3).
# 3c: quota period sensitivity of the dynamic schedules.
# 3d: ca-HepPh, where one vertex carries 13% of the work (giants, splitting).
# 3e: OS-style migration (a slow worker takes over a fast core that a
#     finished worker frees) against pinned workers (hypothesis H5).
set -eu
SOC=data/soc-sign-epinions.txt.gz
HEP=data/ca-HepPh.txt.gz
P3="uv run python -m parallel_processing.hetero_phase3"
W=artifacts/linux

echo "=== 3a $(date -u +%H:%M:%S)"
for rep in 1 2 3; do
  $P3 --graph $SOC --workload $W/workload-soc-sign-epinions.csv --cores F,F,S,S --r 0.43 \
    --schedules block,interleave,block16,block1,lpt,lpt-oracle,static@0.43,static-oracle@0.26,static-oracle@0.43,static-oracle@0.6,static-oracle@1.0 \
    --repeat 1 --tag 3a-rep$rep
done

echo "=== 3b $(date -u +%H:%M:%S)"
for rep in 1 2 3; do
  $P3 --graph $SOC --workload $W/workload-soc-sign-epinions.csv --cores F,F,S,S --r 0.43 \
    --fast-scale 1,1,0.8 \
    --schedules interleave,lpt,static-oracle@0.43,static-oracle@0.53 \
    --repeat 1 --tag 3b-rep$rep
done

echo "=== 3c $(date -u +%H:%M:%S)"
for rep in 1 2; do
  for period in 10000 100000; do
    $P3 --graph $SOC --workload $W/workload-soc-sign-epinions.csv --cores F,F,S,S --r 0.43 \
      --period $period --schedules block,lpt,static-oracle@0.43 --repeat 1 --tag 3c-rep$rep
  done
done

echo "=== 3d $(date -u +%H:%M:%S)"
$P3 --graph $HEP --workload $W/workload-ca-HepPh.csv --cores F --r 1 \
  --schedules block --repeat 5 --tag 3d-base
for r in 0.26 0.43; do
  $P3 --graph $HEP --workload $W/workload-ca-HepPh.csv --cores F,F,S,S --r $r \
    --schedules block,interleave,lpt,lpt-oracle,giants,split,split-giants,static-oracle@$r \
    --repeat 5 --tag 3d
done
$P3 --graph $HEP --workload $W/workload-ca-HepPh.csv --cores F,F,F,F --r 1 \
  --schedules block,lpt,split --repeat 5 --tag 3d
echo "=== 3e $(date -u +%H:%M:%S)"
for rep in 1 2; do
  for r in 0.43 0.26; do
    $P3 --graph $SOC --workload $W/workload-soc-sign-epinions.csv --cores F,F,S,S --r $r \
      --migrate --schedules block,reversed,interleave,lpt,static-oracle@$r \
      --repeat 1 --tag 3e-rep$rep
    $P3 --graph $SOC --workload $W/workload-soc-sign-epinions.csv --cores F,F,S,S --r $r \
      --schedules block,reversed,interleave,lpt,static-oracle@$r \
      --repeat 1 --tag 3e-rep$rep
  done
done
echo "=== done $(date -u +%H:%M:%S)"
