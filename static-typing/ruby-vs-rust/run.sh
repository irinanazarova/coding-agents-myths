#!/bin/sh
# Reproduce every Ruby vs Rust number: labels check, step classification,
# summary tables, blind-check agreement. Plain Ruby, no downloads.
set -eu
cd "$(dirname "$0")"
ruby analysis/find_ruby_errors.rb
ruby analysis/classify_steps.rb
ruby analysis/summarize.rb > /dev/null
echo "wrote results/activity.csv, results/per_run.csv, results/summary.md"
ruby analysis/score_blind_check.rb | head -4
