"""One-off check: how many Multi-SWE-bench sveltejs/svelte gold patches edit
TypeScript files, and how many add JSDoc type tags. The task file is 503 MB, so
it is fetched only on request:

  curl -L -o data/raw/js_ts/msb_svelte.jsonl \
    https://huggingface.co/datasets/ByteDance-Seed/Multi-SWE-bench/resolve/56ff018c04a38e27ada1e9d0a6d5839a51f88f0d/js/sveltejs__svelte_dataset.jsonl
  # sha256 bd58d8e5348afcee93c1e9cb79398888c73b92b336ab09e1825068eb5fda1b09
  python -I js_ts/svelte_jsdoc.py

Reads the file as JSON lines only.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "data" / "raw" / "js_ts" / "msb_svelte.jsonl"
SHA = "bd58d8e5348afcee93c1e9cb79398888c73b92b336ab09e1825068eb5fda1b09"
if not P.exists():
    sys.exit(f"missing {P}; see the docstring for the download command")
assert hashlib.sha256(P.read_bytes()).hexdigest() == SHA, "sha256 mismatch"
n = ts = jsdoc = 0
for line in P.open():
    d = json.loads(line)
    n += 1
    files = re.findall(r"^diff --git a/(\S+)", d["fix_patch"], re.M)
    ts += any(f.endswith((".ts", ".tsx")) and not f.endswith(".d.ts") for f in files)
    jsdoc += bool(re.search(r"^\+.*@(param|type|returns?|typedef)\s*\{", d["fix_patch"], re.M))
print(f"svelte tasks: {n}; gold patch edits .ts/.tsx source: {ts}; gold patch adds JSDoc type tags: {jsdoc}")
