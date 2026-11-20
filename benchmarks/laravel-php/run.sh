#!/bin/bash
# Interleaved benchmark: ROUNDS rounds; each round runs every workload on every PHP version in a shuffled order.
ROUNDS=${ROUNDS:-8}; OUT=${OUT:-results.jsonl}; CPUS=${CPUS:-2-3}
: > "$OUT"
for r in $(seq 1 $ROUNDS); do
  for w in request eloquent blade collections; do
    for v in $(printf '8.3\n8.4\n8.5\n' | shuf); do
      line=$(docker run --rm --cpuset-cpus="$CPUS" lbench:$v php bench.php $w 5) || { echo "FAIL $v $w"; continue; }
      echo "{\"round\":$r,${line#\{}" >> "$OUT"
    done
  done
  echo "round $r done $(date +%T)"
done
