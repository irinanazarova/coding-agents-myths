"""Python on SWE-bench Verified, at the same fix-size mix as SWE-bench Multilingual.

SWE-bench Multilingual leaves Python out. Its Python counterpart, SWE-bench
Verified, was run in the same month by 11 of the same 13 models with the same
agent (scripts/pairs.json). This puts Python on the same footing as the
per-language bars in the blog post: the gold patch's changed lines give each
task a level, with the same cut points as same_difficulty.rb (terciles of the
300 Multilingual tasks), and each group's per-level solve rate is weighted to
the level mix of those 300 tasks.

Typed and dynamic are recomputed here with the same 11 models, so all three
numbers in the output come from one set of models.

Needs the downloads from ./run.sh (data/raw). Usage, from static-typing/benchmarks:
  .venv/bin/python -I scripts/python_same_mix.py
Writes results/python_same_mix.json and prints a summary.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import analyze  # noqa: E402  (reuses the loaders, so Python is read exactly like the post's other numbers)

ROOT = Path(__file__).resolve().parent.parent
TYPED = ["Rust", "C", "Java", "C++", "TypeScript", "Go"]
DYNAMIC = ["JavaScript", "PHP", "Ruby"]
LEVELS = ["small", "medium", "large"]


def main():
    tasks, subs, long = analyze.load()
    by_folder = subs.set_index("folder")
    pairs = [p for p in json.loads((ROOT / "scripts" / "pairs.json").read_text()) if p["use"]]
    models = [by_folder.loc[p["multilingual"], "model"] for p in pairs]

    # Same cut points as same_difficulty.rb: sorted[n/3] and sorted[2n/3] of the 300 tasks.
    s = sorted(tasks.lines)
    cuts = (s[len(s) // 3], s[2 * len(s) // 3])
    level = lambda n: "small" if n <= cuts[0] else "medium" if n <= cuts[1] else "large"
    weights = tasks.lines.map(level).value_counts(normalize=True).to_dict()

    # Multilingual scores for the 11 matched models: share of those models that solved each task.
    ml = long[long.model.isin(models)].groupby("instance_id").solved.mean()
    ml_tasks = tasks.assign(score=ml.loc[tasks.instance_id].values, level=tasks.lines.map(level))

    vt = analyze.load_verified()
    solved = {i: 0 for i in vt.instance_id}
    for p in pairs:
        res = analyze.verified_resolved(p["verified"])
        for i in solved:
            solved[i] += int(res.get(i, False))
    py = vt.assign(score=vt.instance_id.map(lambda i: solved[i] / len(pairs)), level=vt.lines.map(level))

    def same_mix(df):
        rates = df.groupby("level").score.mean().to_dict()
        covered = {k: w for k, w in weights.items() if k in rates}
        total = sum(covered.values())
        return 100 * sum(w / total * rates[k] for k, w in covered.items())

    groups = {
        "Python (SWE-bench Verified)": py,
        "Typed (Multilingual)": ml_tasks[ml_tasks.lang.isin(TYPED)],
        "Dynamic (Multilingual)": ml_tasks[ml_tasks.lang.isin(DYNAMIC)],
    }
    out = {
        "models": models,
        "cuts": {"small_max_lines": cuts[0], "medium_max_lines": cuts[1]},
        "groups": {
            name: {
                "tasks": len(df),
                "tasks_per_level": [int((df.level == lv).sum()) for lv in LEVELS],
                "raw": round(100 * df.score.mean(), 1),
                "same_mix": round(same_mix(df), 1),
                "by_level": {lv: round(100 * df[df.level == lv].score.mean(), 1) for lv in LEVELS},
            }
            for name, df in groups.items()
        },
    }
    (ROOT / "results" / "python_same_mix.json").write_text(json.dumps(out, indent=2) + "\n")
    print(f"{len(models)} matched models; levels: small <= {cuts[0]} lines, medium <= {cuts[1]}")
    for name, g in out["groups"].items():
        print(f"{name:30} tasks {g['tasks']:3}  per level {g['tasks_per_level']}  raw {g['raw']}%  same mix {g['same_mix']}%  by level {g['by_level']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
