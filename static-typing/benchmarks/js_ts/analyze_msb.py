"""JavaScript vs TypeScript on Multi-SWE-bench (ByteDance) from per-instance resolved lists.

Reads data/raw/js_ts/msb/ and data/raw/js_ts/msb_pr28/ (written by
js_ts/fetch_js_ts.py) as JSON only and prints the tables. Ported from an
exploratory script; the standard library is enough.

Inputs:
  evaluation/{javascript,typescript}/verified/index.json  all_ids and easy/medium/hard ids
  evaluation/{javascript,typescript}/verified/<sub>/results/results.json  "resolved" ids
  evaluation/{mini,flash}/index.json and <sub>/results/results.json
Language for mini and flash tasks comes from the repository: every JS or TS
repository in mini and flash also appears in the full split, whose directory
gives its language (checked by assertion against the published counts).

Usage: python -I js_ts/analyze_msb.py
"""
import json, os, sys, random, statistics
from collections import Counter, defaultdict

from pathlib import Path
_RAW = Path(__file__).resolve().parent.parent / "data" / "raw" / "js_ts"
EXP = str(_RAW / "msb")
PR28 = str(_RAW / "msb_pr28")
LEVELS = ["easy", "medium", "hard"]


def load(p):
    with open(p) as f:
        return json.load(f)


def repo_of(iid):
    # instance_id format: org__repo-NUMBER
    org, rest = iid.split("__", 1)
    return org + "/" + rest.rsplit("-", 1)[0]


def index_labels(idx):
    lab = {}
    for lv in LEVELS:
        for i in idx[lv + "_ids"]:
            lab[i] = lv
    assert set(lab) == set(idx["all_ids"]), "difficulty lists do not partition all_ids"
    return lab


def rate(ids, resolved):
    ids = list(ids)
    return (sum(i in resolved for i in ids) / len(ids)) if ids else float("nan")


def std_rate(ids_by_level, resolved, w):
    return sum(w[lv] * rate(ids_by_level[lv], resolved) for lv in LEVELS)


def compare(js_lab, ts_lab, js_res, ts_res, w):
    """Return raw and difficulty-standardized TS minus JS."""
    js_by = {lv: [i for i, l in js_lab.items() if l == lv] for lv in LEVELS}
    ts_by = {lv: [i for i, l in ts_lab.items() if l == lv] for lv in LEVELS}
    out = {
        "js_raw": rate(js_lab, js_res),
        "ts_raw": rate(ts_lab, ts_res),
        "js_std": std_rate(js_by, js_res, w),
        "ts_std": std_rate(ts_by, ts_res, w),
    }
    for lv in LEVELS:
        out["js_" + lv] = rate(js_by[lv], js_res)
        out["ts_" + lv] = rate(ts_by[lv], ts_res)
    out["d_raw"] = out["ts_raw"] - out["js_raw"]
    out["d_std"] = out["ts_std"] - out["js_std"]
    return out


def pooled_weights(js_lab, ts_lab):
    c = Counter(list(js_lab.values()) + list(ts_lab.values()))
    n = sum(c.values())
    return {lv: c[lv] / n for lv in LEVELS}


def pct(x):
    return "  n/a" if x != x else f"{100 * x:5.1f}"


def describe(name, js_lab, ts_lab):
    print(f"\n### Task set: {name}")
    for lang, lab in (("JS", js_lab), ("TS", ts_lab)):
        c = Counter(lab.values())
        print(f"{lang}: n={len(lab)} easy={c['easy']} medium={c['medium']} hard={c['hard']}")
        byrepo = defaultdict(Counter)
        for i, l in lab.items():
            byrepo[repo_of(i)][l] += 1
        for r, cc in sorted(byrepo.items(), key=lambda kv: -sum(kv[1].values())):
            print(f"   {r:40s} n={sum(cc.values()):3d} easy={cc['easy']:3d} medium={cc['medium']:3d} hard={cc['hard']:3d}")


def analyze(name, js_lab, ts_lab, subs):
    """subs: list of (setup_name, js_resolved_set, ts_resolved_set)."""
    describe(name, js_lab, ts_lab)
    w = pooled_weights(js_lab, ts_lab)
    w_js = {lv: Counter(js_lab.values())[lv] / len(js_lab) for lv in LEVELS}
    w_ts = {lv: Counter(ts_lab.values())[lv] / len(ts_lab) for lv in LEVELS}
    print("pooled difficulty weights:", {k: round(v, 3) for k, v in w.items()})
    print("\nsetup | JS raw | TS raw | TS-JS raw | JS e/m/h | TS e/m/h | JS std | TS std | TS-JS std(pooled) | std(JS mix) | std(TS mix)")
    rows = []
    for s, jr, tr in subs:
        o = compare(js_lab, ts_lab, jr, tr, w)
        o_js = compare(js_lab, ts_lab, jr, tr, w_js)["d_std"]
        o_ts = compare(js_lab, ts_lab, jr, tr, w_ts)["d_std"]
        rows.append((s, o, o_js, o_ts))
        print(f"{s:48s} {pct(o['js_raw'])} {pct(o['ts_raw'])} {pct(o['d_raw'])} | "
              f"{pct(o['js_easy'])}/{pct(o['js_medium'])}/{pct(o['js_hard'])} | "
              f"{pct(o['ts_easy'])}/{pct(o['ts_medium'])}/{pct(o['ts_hard'])} | "
              f"{pct(o['js_std'])} {pct(o['ts_std'])} {pct(o['d_std'])} | {pct(o_js)} | {pct(o_ts)}")
    n = len(rows)
    print(f"\nsetups={n}  TS>JS raw: {sum(r[1]['d_raw'] > 0 for r in rows)}  ties raw: {sum(r[1]['d_raw'] == 0 for r in rows)}"
          f"  TS>JS std(pooled): {sum(r[1]['d_std'] > 0 for r in rows)}"
          f"  std(JS mix): {sum(r[2] > 0 for r in rows)}  std(TS mix): {sum(r[3] > 0 for r in rows)}")
    print(f"mean over setups: TS-JS raw {pct(statistics.mean(r[1]['d_raw'] for r in rows))}, "
          f"std {pct(statistics.mean(r[1]['d_std'] for r in rows))}; median std {pct(statistics.median(r[1]['d_std'] for r in rows))}")
    for lv in LEVELS:
        ds = [r[1]['ts_' + lv] - r[1]['js_' + lv] for r in rows]
        print(f"  within {lv:6s}: TS>JS in {sum(d > 0 for d in ds)}/{n} setups, mean TS-JS {pct(statistics.mean(ds))}")

    # Per-repo solve rate, averaged across setups
    print("\nPer-repo solve rate (mean across setups), and within-repo difficulty mix:")
    for lang, lab, k in (("JS", js_lab, 1), ("TS", ts_lab, 2)):
        repos = sorted(set(map(repo_of, lab)))
        for r in repos:
            ids = [i for i in lab if repo_of(i) == r]
            rates = [rate(ids, s[k]) for s in subs]
            by = {lv: [i for i in ids if lab[i] == lv] for lv in LEVELS}
            lvr = {lv: (statistics.mean(rate(by[lv], s[k]) for s in subs) if by[lv] else float('nan')) for lv in LEVELS}
            print(f"  {lang} {r:40s} n={len(ids):3d} mean={pct(statistics.mean(rates))} "
                  f"min={pct(min(rates))} max={pct(max(rates))} | easy {pct(lvr['easy'])} med {pct(lvr['medium'])} hard {pct(lvr['hard'])}")

    # Leave-one-repo-out
    print("\nLeave-one-repo-out (pooled-mix difficulty standardization, weights recomputed):")
    for lang in ("JS", "TS"):
        lab = js_lab if lang == "JS" else ts_lab
        for r in sorted(set(map(repo_of, lab))):
            jl = {i: l for i, l in js_lab.items() if not (lang == "JS" and repo_of(i) == r)}
            tl = {i: l for i, l in ts_lab.items() if not (lang == "TS" and repo_of(i) == r)}
            if any(Counter(jl.values())[lv] == 0 or Counter(tl.values())[lv] == 0 for lv in LEVELS):
                # drop empty levels from weighting
                lv_ok = [lv for lv in LEVELS if Counter(jl.values())[lv] and Counter(tl.values())[lv]]
            else:
                lv_ok = LEVELS
            c = Counter(v for v in list(jl.values()) + list(tl.values()) if v in lv_ok)
            ww = {lv: (c[lv] / sum(c.values()) if lv in lv_ok else 0.0) for lv in LEVELS}
            ds, dr = [], []
            for s, jr, tr in subs:
                o = compare(jl, tl, jr, tr, ww)
                ds.append(sum(ww[lv] * (o['ts_' + lv] - o['js_' + lv]) for lv in lv_ok))
                dr.append(o['d_raw'])
            print(f"  drop {lang} {r:40s} (JS n={len(jl)}, TS n={len(tl)}) raw TS>JS {sum(d > 0 for d in dr)}/{n} mean {pct(statistics.mean(dr))} | "
                  f"std TS>JS {sum(d > 0 for d in ds)}/{n} mean {pct(statistics.mean(ds))}")

    # Instance bootstrap (stratified by language x difficulty) of mean-over-setups standardized diff
    rnd = random.Random(20261030)
    js_by = {lv: [i for i, l in js_lab.items() if l == lv] for lv in LEVELS}
    ts_by = {lv: [i for i, l in ts_lab.items() if l == lv] for lv in LEVELS}
    # precompute per-instance mean solve rate across setups
    js_m = {i: statistics.mean(i in s[1] for s in subs) for i in js_lab}
    ts_m = {i: statistics.mean(i in s[2] for s in subs) for i in ts_lab}
    boots = []
    for _ in range(4000):
        d = 0.0
        for lv in LEVELS:
            jb = [js_m[rnd.choice(js_by[lv])] for _ in js_by[lv]]
            tb = [ts_m[rnd.choice(ts_by[lv])] for _ in ts_by[lv]]
            d += w[lv] * (statistics.mean(tb) - statistics.mean(jb))
        boots.append(d)
    boots.sort()
    point = sum(w[lv] * (statistics.mean(ts_m[i] for i in ts_by[lv]) - statistics.mean(js_m[i] for i in js_by[lv])) for lv in LEVELS)
    print(f"\nMean-over-setups std TS-JS = {pct(point)} pts, instance bootstrap 95% CI [{pct(boots[100])}, {pct(boots[3899])}] "
          "(resamples tasks within language x difficulty; ignores repo clustering)")
    # Repo-cluster bootstrap: resample repos within language
    js_repos = sorted(set(map(repo_of, js_lab)))
    ts_repos = sorted(set(map(repo_of, ts_lab)))
    cb = []
    for _ in range(4000):
        jl = [i for r in (rnd.choice(js_repos) for _ in js_repos) for i in js_lab if repo_of(i) == r]
        tl = [i for r in (rnd.choice(ts_repos) for _ in ts_repos) for i in ts_lab if repo_of(i) == r]
        d = 0.0
        ok = True
        for lv in LEVELS:
            a = [ts_m[i] for i in tl if ts_lab[i] == lv]
            b = [js_m[i] for i in jl if js_lab[i] == lv]
            if not a or not b:
                ok = False
                break
            d += w[lv] * (statistics.mean(a) - statistics.mean(b))
        if ok:
            cb.append(d)
    cb.sort()
    k = len(cb)
    print(f"Repo-cluster bootstrap 95% CI [{pct(cb[int(0.025 * k)])}, {pct(cb[int(0.975 * k) - 1])}] from {k} valid draws")
    return rows


def resolved_set(p, universe):
    r = set(load(p)["resolved"])
    extra = r - set(universe)
    assert not extra, f"{p}: resolved ids outside index: {sorted(extra)[:5]}"
    return r


# ---- Full "verified" splits ----
base = os.path.join(EXP, "evaluation")
js_idx = load(os.path.join(base, "javascript/verified/index.json"))
ts_idx = load(os.path.join(base, "typescript/verified/index.json"))
js_lab, ts_lab = index_labels(js_idx), index_labels(ts_idx)


def subdirs(lang):
    d = os.path.join(base, lang, "verified")
    return sorted(x for x in os.listdir(d) if os.path.isdir(os.path.join(d, x)))


js_subs, ts_subs = set(subdirs("javascript")), set(subdirs("typescript"))
print("Submissions only in JS:", sorted(js_subs - ts_subs), " only in TS:", sorted(ts_subs - js_subs))
paired = []
for s in sorted(js_subs & ts_subs):
    jr = resolved_set(os.path.join(base, "javascript/verified", s, "results/results.json"), js_lab)
    tr = resolved_set(os.path.join(base, "typescript/verified", s, "results/results.json"), ts_lab)
    paired.append((s, jr, tr))
if PR28:
    jr = resolved_set(os.path.join(PR28, "javascript/results/results.json"), js_lab)
    tr = resolved_set(os.path.join(PR28, "typescript/results/results.json"), ts_lab)
    paired_plus = paired + [("UNMERGED_PR28_20261026_AiWork-Code_Claude-Opus-5.5", jr, tr)]
else:
    paired_plus = paired
print("\n================ FULL (merged submissions) ================")
analyze("Multi-SWE-bench JS/TS (experiments index.json)", js_lab, ts_lab, paired)
if PR28:
    print("\n================ FULL incl. unmerged PR #28 ================")
    analyze("Multi-SWE-bench JS/TS + PR28", js_lab, ts_lab, paired_plus)

# ---- mini and flash ----
REPO_LANG = {repo_of(i): "JS" for i in js_lab}
REPO_LANG.update({repo_of(i): "TS" for i in ts_lab})
EXPECTED = {"mini": (50, 50), "flash": (45, 45)}
for split in ("mini", "flash"):
    idx = load(os.path.join(base, split, "index.json"))
    lab = index_labels(idx)
    jl = {i: lab[i] for i in lab if REPO_LANG.get(repo_of(i)) == "JS"}
    tl = {i: lab[i] for i in lab if REPO_LANG.get(repo_of(i)) == "TS"}
    assert (len(jl), len(tl)) == EXPECTED[split], (split, len(jl), len(tl))
    subs = []
    d = os.path.join(base, split)
    for s in sorted(x for x in os.listdir(d) if os.path.isdir(os.path.join(d, x))):
        r = resolved_set(os.path.join(d, s, "results/results.json"), lab)
        subs.append((s, r & set(jl), r & set(tl)))
    print(f"\n================ {split.upper()} ================")
    analyze(f"Multi-SWE-bench {split}", jl, tl, subs)
