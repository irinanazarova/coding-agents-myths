"""Write data/tasks.jsonl: the 43 SWE-bench Multilingual JavaScript and TypeScript tasks.

Each line carries the issue text and image the harness uses, plus the group the
post compares: "ts" (fix edits only TypeScript files), "plain" (only JavaScript
the repo doesn't type-check), "checked" (only type-checked JavaScript), or
"mixed". Groups come from ../benchmarks/js_ts/results/task_labels.csv, the same
labels behind the post's JavaScript vs TypeScript table.
"""

import csv
import json
from pathlib import Path

from swebench.harness.run_evaluation import load_instances
from swebench.harness.utils import make_test_spec

HERE = Path(__file__).parent
LABELS = HERE.parent / "benchmarks" / "js_ts" / "results" / "task_labels.csv"


def group(row):
    ts, checked, plain = (int(row[k]) for k in ("n_ts", "n_checked_js", "n_plain_js"))
    if ts and not checked and not plain:
        return "ts"
    if plain and not ts and not checked:
        return "plain"
    if checked and not ts and not plain:
        return "checked"
    return "mixed"


labels = {
    r["instance_id"]: r
    for r in csv.DictReader(LABELS.open())
    if r["benchmark"].startswith("SWE-bench")
}
instances = {
    i["instance_id"]: i
    for i in load_instances("SWE-bench/SWE-bench_Multilingual", "test", None, None)
}

out = HERE / "data" / "tasks.jsonl"
out.parent.mkdir(exist_ok=True)
counts = {}
with out.open("w") as f:
    for iid, row in sorted(labels.items()):
        inst = instances[iid]
        g = group(row)
        counts[g] = counts.get(g, 0) + 1
        f.write(json.dumps({
            "instance_id": iid,
            "repo": inst["repo"],
            "bench_lang": row["bench_lang"],
            "group": g,
            "base_commit": inst["base_commit"],
            "image": make_test_spec(inst).image,
            "problem_statement": inst["problem_statement"],
        }) + "\n")
print(out, counts)
