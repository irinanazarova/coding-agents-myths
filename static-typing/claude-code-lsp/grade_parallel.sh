#!/bin/sh
# Grade every condition of a run at once: one SWE-bench harness per condition.
# Usage: ./grade_parallel.sh RUN [WORKERS_PER_CONDITION]
set -eu
cd "$(dirname "$0")"
RUN=$1; W=${2:-2}
for c in runs/"$RUN"/*/; do
  c=$(basename "$c")
  [ -f "runs/$RUN/$c/predictions.jsonl" ] || continue
  .venv/bin/python -m swebench.harness.run_evaluation -d SWE-bench/SWE-bench_Multilingual \
    -p "runs/$RUN/$c/predictions.jsonl" -id "$RUN-$c" --max_workers "$W" -t 600 \
    --report_dir logs/reports > "runs/$RUN/$c/harness.log" 2>&1 &
done
wait
