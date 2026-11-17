#!/bin/sh
# Reproduce everything: venv (outside data/), pinned deps, download, analysis.
set -eu
cd "$(dirname "$0")"
[ -x .venv/bin/python ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
.venv/bin/python -I scripts/fetch.py
.venv/bin/python -I scripts/analyze.py "$@"
.venv/bin/python -I scripts/steps_cost.py . > results/steps_cost.txt
