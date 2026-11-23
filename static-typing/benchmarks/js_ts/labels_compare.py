"""Typed vs plain JavaScript/TypeScript tasks, by the code each fix edits.

Reads js_ts/results/task_labels.csv (from js_ts/labels.py) and each
benchmark's per-task results, and compares tasks whose gold patch edits only
typed code (TypeScript, or JavaScript the repo type-checks) with tasks whose
gold patch edits only unchecked JavaScript. Mixed and no-code tasks are left
out. Every comparison is at the same difficulty: solve rates within each level,
averaged with the pooled level mix of the two groups being compared.

  across repos   typed vs plain over all tasks (each side mixes projects)
  within repo    strata are repo x level, so typed and plain tasks are only
                 compared inside the same repository

Main comparison: TypeScript files (the fix edits only .ts/.tsx) vs plain
JavaScript (only unchecked JS; .d.ts edits allowed). Sign: positive = typed ahead. Points are percentage points.

Inputs, read as data only (all from js_ts/fetch_js_ts.py except PR #29):
  data/raw/js_ts/msb/, msb_pr28/, msb_pr29/          Multi-SWE-bench
  data/raw/js_ts/pb/                                  SWE-PolyBench Verified
  data/raw/js_ts/multilingual/                        SWE-bench Multilingual

Usage: python -I js_ts/labels_compare.py
"""
import csv
import glob
import json
import random
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "data" / "raw" / "js_ts"
LABELS = HERE / "results" / "task_labels.csv"
SEED, DRAWS = 20261120, 4000


# ---------------------------------------------------------------- setups
def msb():
    base = RAW / "msb" / "evaluation"
    level, ids = {}, set()
    for lang in ("javascript", "typescript"):
        idx = json.load(open(base / lang / "verified" / "index.json"))
        for lv in ("easy", "medium", "hard"):
            for i in idx[lv + "_ids"]:
                level[i] = lv
        ids |= set(idx["all_ids"])
    subs = {lang: {p.name for p in (base / lang / "verified").iterdir() if p.is_dir()} for lang in ("javascript", "typescript")}
    setups = []
    for s in sorted(subs["javascript"] & subs["typescript"]):
        res = set()
        for lang in ("javascript", "typescript"):
            res |= set(json.load(open(base / lang / "verified" / s / "results" / "results.json"))["resolved"])
        setups.append((s, "merged", res))
    for tag, paths in (("unmerged PR #28", [RAW / "msb_pr28" / l / "results" / "results.json" for l in ("javascript", "typescript")]),
                       ("unmerged PR #29", [RAW / "msb_pr29" / f"{l}.json" for l in ("javascript", "typescript")])):
        res = set()
        for p in paths:
            res |= set(json.load(open(p))["resolved"])
        name = {"unmerged PR #28": "20261026_AiWork-Code_Claude-Opus-5.5",
                "unmerged PR #29": "20261101_CodeArts-Agent_CodeArts-GLM-5.2"}[tag]
        setups.append((name, tag, res))
    for _, _, r in setups:
        assert r <= ids, "resolved ids outside the index"
    return level, setups


PB_SUBS = [
    ("Prometheus v1.2 + GPT-5", "merged", "merged/evaluation/PBVerified/20251130_prometheus_gpt-5"),
    ("Atlassian Rovo Dev", "merged", "merged/evaluation/PBVerified/20251208_atlassian-rovo-dev"),
    ("Kodah (gpt-5-mini)", "merged", "merged/evaluation/PBVerified/20260430_kodah_gpt-5-mini"),
    ("HMigBot (Claude Opus 4.8)", "merged", "merged/evaluation/PBVerified/20260623_migbot_claude-opus-4-8"),
    ("Mobile Coder + DeepSeek V4 Flash", "open PR #40", "pr40/evaluation/PBVerified/20260901_mobile-coder_deepseek-v4-flash"),
    ("Sapient Slingshot 3.4 + GPT-5.6-sol", "open PR #44", "pr44/evaluation/PBVerified/20261006_sapientslingshot_gpt-5.6-sol"),
    ("JamLabs Jitto Build (Opus 5.5)", "open PR #46", "pr46/evaluation/PBVerified/20261010_jitto-build_claude-opus-5-5"),
    ("AiWork.Code (Opus 5.5)", "open PR #47", "pr47/evaluation/PBVerified/20261021_aiwork-code_claude-opus-5-5"),
]


def pb():
    ann = pd.read_json(RAW / "pb" / "gh" / "annotations.jsonl", lines=True)
    med = ann.groupby("instance_id").task_difficulty_choice.median()
    level = {i: ["<15m", "15m-1h", ">=1h"][int(min(2, max(0, round(m))))] for i, m in med.items()}
    setups = []
    for name, tier, path in PB_SUBS:
        res = set()
        for f in glob.glob(str(RAW / "pb" / path / "logs" / "*_result.json")):
            j = json.load(open(f))
            if j["resolved"]:
                res.add(j["instance_id"])
        setups.append((name, tier, res))  # a missing result file counts as unresolved
    return level, setups


def changed_lines(patch):
    return sum(1 for ln in (patch or "").splitlines() if ln[:1] in "+-" and not ln.startswith(("+++", "---")))


def ml():
    ds = pd.read_parquet(RAW / "multilingual" / "test.parquet")
    assert len(ds) == 300
    lines = dict(zip(ds.instance_id, ds.patch.map(changed_lines)))
    s = sorted(lines.values())
    cuts = (s[len(s) // 3], s[2 * len(s) // 3])  # terciles over all 300 tasks, as in same_difficulty.rb
    level = {i: "small" if n <= cuts[0] else "medium" if n <= cuts[1] else "large" for i, n in lines.items()}
    setups = []
    for d in sorted((RAW / "multilingual" / "runs").iterdir()):
        pid = json.loads((d / "per_instance_details.json").read_text())
        setups.append((d.name.split("_", 2)[2], "Feb 2026", {i for i, v in pid.items() if v.get("resolved") is True}))
    assert len(setups) == 13
    return level, setups


# ---------------------------------------------------------------- statistics
def strat_diff(a_ids, b_ids, stratum, score):
    """Same-difficulty A minus B: per-stratum rate difference, weighted by the
    stratum's share of A+B tasks, over strata where both sides have tasks."""
    sa, sb = defaultdict(list), defaultdict(list)
    for i in a_ids:
        sa[stratum(i)].append(score(i))
    for i in b_ids:
        sb[stratum(i)].append(score(i))
    both = [k for k in sa if k in sb]
    n = sum(len(sa[k]) + len(sb[k]) for k in both)
    if not n:
        return float("nan"), 0
    d = sum((len(sa[k]) + len(sb[k])) / n * (statistics.mean(sa[k]) - statistics.mean(sb[k])) for k in both)
    return d, n


def compare(title, a_ids, b_ids, level, setups, repo_of, within_repo, rng):
    a_ids, b_ids = sorted(a_ids), sorted(b_ids)
    # each comparison gets its own seed, so adding or reordering checks leaves the others unchanged
    rng = random.Random(f"{SEED}|{title}|{','.join(a_ids)}|{','.join(b_ids)}")
    stratum = (lambda i: (repo_of[i], level[i])) if within_repo else (lambda i: level[i])
    per = []
    for name, tier, res in setups:
        d, n = strat_diff(a_ids, b_ids, stratum, lambda i: float(i in res))
        per.append((name, tier, d))
    mean_score = {i: statistics.mean(i in r for _, _, r in setups) for i in a_ids + b_ids}
    point, n_used = strat_diff(a_ids, b_ids, stratum, mean_score.get)
    # task bootstrap within stratum x side
    sa, sb = defaultdict(list), defaultdict(list)
    for i in a_ids:
        sa[stratum(i)].append(i)
    for i in b_ids:
        sb[stratum(i)].append(i)
    draws = []
    for _ in range(DRAWS):
        ra = [rng.choice(v) for v in sa.values() for _ in v]
        rb = [rng.choice(v) for v in sb.values() for _ in v]
        draws.append(strat_diff(ra, rb, stratum, mean_score.get)[0])
    draws.sort()
    lo, hi = draws[int(0.025 * DRAWS)], draws[int(0.975 * DRAWS) - 1]
    ahead = sum(d > 0 for _, _, d in per)
    loo = []
    if not within_repo:
        for r in sorted({repo_of[i] for i in a_ids + b_ids}):
            a2 = [i for i in a_ids if repo_of[i] != r]
            b2 = [i for i in b_ids if repo_of[i] != r]
            if a2 and b2:
                loo.append((r, strat_diff(a2, b2, stratum, mean_score.get)[0]))
    print(f"\n### {title}")
    print(f"typed n={len(a_ids)} ({len({repo_of[i] for i in a_ids})} repos), plain n={len(b_ids)} "
          f"({len({repo_of[i] for i in b_ids})} repos); tasks in compared strata: {n_used}")
    print(f"typed minus plain, mean of setups: {100 * point:+.1f} pts, task bootstrap 95% [{100 * lo:+.1f}, {100 * hi:+.1f}]; "
          f"typed ahead in {ahead} of {len(per)} setups")
    if loo:
        print("leave one repo out: " + ", ".join(f"{r.split('/')[1]} {100 * d:+.1f}" for r, d in loo))
    for name, tier, d in per:
        if tier != "merged" or len(per) <= 13:
            print(f"   {name:48s} {tier:16s} {100 * d:+6.1f}")
    return point, lo, hi, ahead, len(per)


def group_rates(groups, ref, level, setups, repo_of):
    """Each group's solve rate at one level mix: the pooled mix of the two
    `ref` groups (the main comparison), over levels both of them have. The
    rates of the two `ref` groups then subtract to exactly the main gap."""
    a, b = (groups[g] for g in ref)
    la, lb = Counter(level[i] for i in a), Counter(level[i] for i in b)
    w = {k: la[k] + lb[k] for k in la if k in lb}

    def std(ids, res):
        by = defaultdict(list)
        for i in ids:
            by[level[i]].append(i in res)
        lv = [k for k in w if k in by]
        tot = sum(w[k] for k in lv)
        return sum(w[k] / tot * statistics.mean(by[k]) for k in lv)

    shown = [(nm, t, r) for nm, t, r in setups if t != "merged" or len(setups) <= 13]
    merged = [r for _, t, r in setups if t == "merged"]
    print(f"\n### Solve rate by what the fix edits, at the level mix of {ref[0]} + {ref[1]} "
          f"(levels {', '.join(str(k) for k in sorted(w))})")
    print(f"{'group':34s} {'tasks':>5s} {'repos':>5s} {'all setups':>10s}  " + "  ".join(f"{nm[:22]:>22s}" for nm, _, _ in shown))
    for g, ids in groups.items():
        if not ids:
            continue
        repos = Counter(repo_of[i] for i in ids)
        missing = sorted(str(k) for k in w if k not in {level[i] for i in ids})
        allm = statistics.mean(std(ids, r) for _, _, r in setups)
        label = g
        if 0 < len(merged) < len(setups) and len(setups) > 13:
            label = f"{g} (merged {100 * statistics.mean(std(ids, r) for r in merged):.1f})"
        cols = "  ".join(f"{100 * std(ids, r):22.1f}" for _, _, r in shown)
        print(f"{label:34s} {len(ids):5d} {len(repos):5d} {100 * allm:10.1f}  {cols}")
        print("    " + ", ".join(f"{r} {c}" for r, c in repos.most_common())
              + (f"  [no tasks at level {', '.join(missing)}; rate renormalized over the rest]" if missing else ""))


AUDIT = RAW / "pb" / "pr47_audit" / "memorization_audit.json"
AUDIT_SHA = "91e3fba1d9df5a322faebd182413aa4e3d5e3ae46dc2725ad3e4ffd703b83066"


def memorization(ts_only, plain, bl_ts, bl_js, level, setups):
    """AiWork.Code (Opus 5.5) ships memorization_audit.json in PR #47
    (x4vierli/SWE-PolyBench@828dadd0): resolved instances whose patch carries a
    verbatim trace of the upstream fix. Recompute that run with them unsolved."""
    import hashlib
    if not AUDIT.exists():
        print("\n(memorization audit not downloaded; see js_ts/README.md)")
        return
    assert hashlib.sha256(AUDIT.read_bytes()).hexdigest() == AUDIT_SHA, "audit sha256 mismatch"
    mem = {x["instance_id"] for x in json.load(open(AUDIT))["instances"] if x.get("counted") and x.get("resolved")}
    res = next(r for n, _, r in setups if n == "AiWork.Code (Opus 5.5)")
    jt = mem & set(ts_only + plain + bl_ts + bl_js)
    print(f"\n### Memorization sensitivity, AiWork.Code (Opus 5.5): {len(mem)} counted memorized solves, "
          f"{len(jt)} in JS/TS tasks ({len(mem & set(ts_only))} TypeScript-files, {len(mem & set(plain))} plain-JS)")
    lv = lambda i: level[i]
    for tag, r in (("as submitted", res), ("memorized solves counted unsolved", res - mem)):
        a = strat_diff(bl_ts, bl_js, lv, lambda i: float(i in r))[0]
        b = strat_diff(ts_only, plain, lv, lambda i: float(i in r))[0]
        print(f"  {tag:36s} benchmark labels TS-JS {100 * a:+.1f}   TS files - plain JS {100 * b:+.1f}")
    a = [i for i in ts_only if i not in mem]
    b = [i for i in plain if i not in mem]
    print(f"  {'memorized tasks dropped':36s} TS files - plain JS {100 * strat_diff(a, b, lv, lambda i: float(i in res))[0]:+.1f} (n {len(a)}/{len(b)})")


def main():
    rows = list(csv.DictReader(open(LABELS)))
    benches = {"SWE-bench Multilingual": ml(), "Multi-SWE-bench": msb(), "SWE-PolyBench": pb()}
    rng = random.Random(SEED)
    for bench, (level, setups) in benches.items():
        rs = [r for r in rows if r["benchmark"] == bench]
        repo_of = {r["instance_id"]: r["repo"] for r in rs}
        assert all(r["instance_id"] in level for r in rs), f"{bench}: task without a difficulty level"
        print(f"\n\n================ {bench}: {len(rs)} tasks, {len(setups)} setups ================")

        # where each benchmark label's tasks fall
        print("\nBenchmark label -> edit label:")
        for lang in ("JS", "TS"):
            c = Counter(r["label"] for r in rs if r["bench_lang"] == lang)
            sub = Counter("ts" if r["n_checked_js"] == "0" else "checked JS" for r in rs if r["bench_lang"] == lang and r["label"] == "typed")
            print(f"  {lang}: {sum(c.values())} tasks: typed {c['typed']} (TS files {sub['ts']}, checked JS {sub['checked JS']}), "
                  f"plain {c['plain']}, mixed {c['mixed']}, none {c['none']}")

        bl_js = [r["instance_id"] for r in rs if r["bench_lang"] == "JS"]
        bl_ts = [r["instance_id"] for r in rs if r["bench_lang"] == "TS"]
        typed = [r["instance_id"] for r in rs if r["label"] == "typed"]
        plain = [r["instance_id"] for r in rs if r["label"] == "plain"]
        ts_only = [r["instance_id"] for r in rs if r["label"] == "typed" and r["n_checked_js"] == "0"]
        plain_nodts = [r["instance_id"] for r in rs if r["label"] == "plain" and r["n_dts"] == "0"]

        group_rates({
            "TypeScript files": ts_only,
            "type-checked JavaScript": [r["instance_id"] for r in rs if r["label"] == "typed" and r["n_checked_js"] != "0"],
            "plain JavaScript": plain,
        }, ("TypeScript files", "plain JavaScript"), level, setups, repo_of)
        compare("Benchmark labels: TS minus JS (reproduces the published comparison)", bl_ts, bl_js, level, setups, repo_of, False, rng)
        compare("Edit labels, across repos: TypeScript files minus plain JavaScript (main comparison)", ts_only, plain, level, setups, repo_of, False, rng)
        compare("Sensitivity: typed (TS files or type-checked JS) minus plain", typed, plain, level, setups, repo_of, False, rng)
        compare("Sensitivity: TS files minus plain JS whose fix edits no .d.ts", ts_only, plain_nodts, level, setups, repo_of, False, rng)
        mixed = [r["instance_id"] for r in rs if r["label"] == "mixed"]
        if mixed:
            compare("Sensitivity: TS files or mixed (TS + plain JS) minus plain", ts_only + mixed, plain, level, setups, repo_of, False, rng)
        code_n = {r["instance_id"]: int(r["n_ts"]) + int(r["n_checked_js"]) + int(r["n_plain_js"]) for r in rs}
        t2, p2 = [i for i in ts_only if code_n[i] >= 2], [i for i in plain if code_n[i] >= 2]
        if len(t2) >= 10 and len(p2) >= 10:
            compare("Sensitivity: fixes that edit two or more code files, TS files minus plain", t2, p2, level, setups, repo_of, False, rng)
        merged = [s for s in setups if s[1] == "merged"]
        if 0 < len(merged) < len(setups):
            compare(f"Main comparison, {len(merged)} merged setups only", ts_only, plain, level, merged, repo_of, False, rng)
        if bench == "SWE-PolyBench":
            memorization(ts_only, plain, bl_ts, bl_js, level, setups)
        both = {repo_of[i] for i in ts_only} & {repo_of[i] for i in plain}
        if both:
            print("\nRepos with both TypeScript-files and plain-JS tasks: " + ", ".join(
                f"{r} ({sum(repo_of[i] == r for i in ts_only)} TS / {sum(repo_of[i] == r for i in plain)} plain)" for r in sorted(both)))
            compare("Within repo: TypeScript files minus plain JavaScript", [i for i in ts_only if repo_of[i] in both],
                    [i for i in plain if repo_of[i] in both], level, setups, repo_of, True, rng)
            for r in sorted(both):
                t = [i for i in ts_only if repo_of[i] == r]
                p = [i for i in plain if repo_of[i] == r]
                if len(t) >= 5 and len(p) >= 5:
                    compare(f"Within {r}: TypeScript files minus plain JavaScript", t, p, level, setups, repo_of, True, rng)


if __name__ == "__main__":
    main()
