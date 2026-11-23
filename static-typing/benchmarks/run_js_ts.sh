#!/bin/sh
# JavaScript vs TypeScript comparison: venv (outside data/), pinned deps,
# download into data/raw/js_ts/, check SHA-256 against js_ts/sources.lock.json,
# analyze into js_ts/results/. Set VENV to reuse an existing virtualenv.
# LABELS=1 also relabels every task by the files its fix edits (js_ts/labels.py):
# needs the 1.3 GB Multi-SWE-bench task files and `gh auth token`; otherwise the
# committed js_ts/results/task_labels.csv is used.
set -eu
cd "$(dirname "$0")"
VENV="${VENV:-.venv}"
[ -x "$VENV/bin/python" ] || { python3 -m venv "$VENV" && "$VENV/bin/pip" install -q -r requirements.txt; }
"$VENV/bin/python" -I js_ts/fetch_js_ts.py
mkdir -p js_ts/results
"$VENV/bin/python" -I js_ts/analyze_js_ts.py "$@" > /dev/null
"$VENV/bin/python" -I js_ts/analyze_msb.py > js_ts/results/multi_swe_bench.txt
"$VENV/bin/python" -W ignore -I js_ts/analyze_pb.py > js_ts/results/swe_polybench.txt
if [ "${LABELS:-0}" = 1 ]; then
  "$VENV/bin/python" -I js_ts/labels.py > js_ts/results/task_labels.txt
fi
"$VENV/bin/python" -I js_ts/labels_compare.py > js_ts/results/typed_vs_plain.txt
echo "wrote js_ts/results/"
