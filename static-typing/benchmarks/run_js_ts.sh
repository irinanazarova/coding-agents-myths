#!/bin/sh
# JavaScript vs TypeScript comparison: venv (outside data/), pinned deps,
# download into data/raw/js_ts/, check SHA-256 against js_ts/sources.lock.json,
# analyze into js_ts/results/. Set VENV to reuse an existing virtualenv.
set -eu
cd "$(dirname "$0")"
VENV="${VENV:-.venv}"
[ -x "$VENV/bin/python" ] || { python3 -m venv "$VENV" && "$VENV/bin/pip" install -q -r requirements.txt; }
"$VENV/bin/python" -I js_ts/fetch_js_ts.py
mkdir -p js_ts/results
"$VENV/bin/python" -I js_ts/analyze_js_ts.py "$@" > /dev/null
"$VENV/bin/python" -I js_ts/analyze_msb.py > js_ts/results/multi_swe_bench.txt
"$VENV/bin/python" -W ignore -I js_ts/analyze_pb.py > js_ts/results/swe_polybench.txt
echo "wrote js_ts/results/"
