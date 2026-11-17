"""JavaScript vs TypeScript in SWE-bench Multilingual (13 February 2026 runs).

Reads data/raw/js_ts/ (written by js_ts/fetch_js_ts.py) as data only and writes
js_ts/results/. Every downloaded file is parsed as JSON, parquet or text;
Python-repr strings inside OpenAI-format trajectories are parsed with
ast.literal_eval, which evaluates literals only.

Usage: python -I js_ts/analyze_js_ts.py [--boot N] [--seed S]
"""

from __future__ import annotations

import argparse
import ast
import itertools
import json
import re
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RAW = ROOT / "data" / "raw" / "js_ts" / "multilingual"
OUT = HERE / "results"

REPO_LANG = {
    "axios/axios": "JS", "immutable-js/immutable-js": "JS", "mrdoob/three.js": "JS", "preactjs/preact": "JS",
    "babel/babel": "TS", "facebook/docusaurus": "TS", "vuejs/core": "TS",
}
NAMES = {
    "claude-4-5-haiku": "Claude 4.5 Haiku", "claude-4-5-opus": "Claude 4.5 Opus",
    "claude-4-5-sonnet": "Claude 4.5 Sonnet", "claude-4-6-opus": "Claude 4.6 Opus",
    "deepseek-3-2": "DeepSeek V3.2", "gemini-3-flash": "Gemini 3 Flash", "gemini-3-pro": "Gemini 3 Pro",
    "glm-5": "GLM 5", "gpt-5-2-high": "GPT 5.2 (high)", "gpt-5-mini": "GPT 5 mini",
    "kimi-k2-5": "Kimi K2.5", "minimax-2-5": "MiniMax M2.5", "gpt-5-2-codex": "GPT 5.2 Codex",
}

TSC_CMD = re.compile(r"\btsc\b|vue-tsc|type-?check|check-types|--noEmit")
TS_ERR = re.compile(r"error TS\d{4}")
TEST_CMD = re.compile(r"\b(jest|vitest|mocha|karma)\b|\b(npm|yarn|pnpm)\b[^|;&]*\btest\b")
RT_ERR = re.compile(r"\b(TypeError|ReferenceError|SyntaxError|RangeError): ")


def patch_files(patch: str) -> list[str]:
    return re.findall(r"^diff --git a/(\S+)", patch or "", re.M)


def changed_lines(patch: str) -> int:
    return sum(1 for ln in patch.splitlines()
               if ln[:1] in "+-" and not ln.startswith(("+++", "---")))


def n_tests(x) -> int:
    if isinstance(x, str):
        try:
            x = json.loads(x)
        except json.JSONDecodeError:
            try:
                x = ast.literal_eval(x)
            except Exception:
                return 1
    return len(x)


def as_obj(x):
    if isinstance(x, str):
        try:
            return ast.literal_eval(x)
        except Exception:
            return {}
    return x or {}


# ---------------------------------------------------------------- loading

def load():
    ds = pd.read_parquet(RAW / "test.parquet")
    assert len(ds) == 300
    ds["lines"] = ds.patch.map(changed_lines)
    ds["files"] = ds.patch.map(lambda p: len(patch_files(p)))
    ds["f2p"] = ds.FAIL_TO_PASS.map(n_tests)
    ds["prob_len"] = ds.problem_statement.str.len()
    ds["lang"] = ds.repo.map(REPO_LANG)
    runs = sorted((RAW / "runs").iterdir())
    rows = []
    for d in runs:
        pid = json.loads((d / "per_instance_details.json").read_text())
        key = d.name.split("_", 2)[2]
        for iid in ds.instance_id:
            rows.append({"run": d.name, "model": key, "instance_id": iid,
                         "solved": int(pid.get(iid, {}).get("resolved") is True)})
    long = pd.DataFrame(rows).merge(
        ds[["instance_id", "repo", "lang", "lines", "files", "f2p", "prob_len", "created_at"]], on="instance_id")
    return ds, long


def traj_stats(run: str, iid: str) -> dict:
    p = RAW / "trajs" / run / f"{iid}.traj.json"
    t = json.loads(p.read_text())
    cmds, obs, in_tok, out_tok = [], [], 0, 0
    for m in t["messages"]:
        e = as_obj(m.get("extra"))
        if isinstance(e, dict):
            for a in e.get("actions", []) or []:
                cmds.append(str(a.get("command", "")))
        if m.get("role") == "tool" or m.get("type") == "function_call_output":
            obs.append(str(m.get("content") or m.get("output") or ""))
        u = m.get("usage")
        if u is None and isinstance(e, dict):
            resp = e.get("response")
            u = resp.get("usage") if isinstance(resp, dict) else None
        u = as_obj(u) if u else None
        if isinstance(u, dict):
            in_tok += int(u.get("prompt_tokens") or u.get("input_tokens") or 0)
            out_tok += int(u.get("completion_tokens") or u.get("output_tokens") or 0)
    ms = t["info"].get("model_stats", {})
    tserr_obs = [o for o in obs if TS_ERR.search(o)]
    rterr_obs = [o for o in obs if RT_ERR.search(o)]
    return {
        "steps": ms.get("api_calls"), "cost": ms.get("instance_cost"),
        "in_tokens": in_tok, "out_tokens": out_tok,
        "n_cmds": len(cmds),
        "tsc_cmds": sum(bool(TSC_CMD.search(c)) for c in cmds),
        "test_cmds": sum(bool(TEST_CMD.search(c)) for c in cmds),
        "tserr_obs": len(tserr_obs), "tserr_chars": sum(len(o) for o in tserr_obs),
        "rterr_obs": len(rterr_obs), "rterr_chars": sum(len(o) for o in rterr_obs),
        "obs_chars": sum(len(o) for o in obs),
        "exit_status": t["info"].get("exit_status"),
    }


def patch_stats(run: str, iid: str, gold_files: set[str]) -> dict:
    p = RAW / "logs" / run / iid / "patch.diff"
    if not p.exists():
        return {"patch_available": 0}
    files = [f for f in patch_files(p.read_text(errors="replace")) if not re.search(r"(^|/)(test|tests|__tests__)/|\.test\.|\.spec\.", f)]
    return {"patch_available": 1, "patch_empty": int(not files),
            "touches_gold_file": int(bool(set(files) & gold_files))}


# ---------------------------------------------------------------- statistics

def boot_ci(x, rng, B):
    x = np.asarray(x, float)
    d = np.array([x[rng.integers(0, len(x), len(x))].mean() for _ in range(B)])
    return np.percentile(d, [2.5, 97.5])


def gap_task_boot(js, ts, rng, B):
    js, ts = np.asarray(js), np.asarray(ts)
    d = np.array([js[rng.integers(0, len(js), len(js))].mean() - ts[rng.integers(0, len(ts), len(ts))].mean()
                  for _ in range(B)])
    return np.percentile(d, [2.5, 97.5])


def gap_repo_boot(tasks, rng, B):
    """Resample repositories within each language, then tasks within repo."""
    g = {L: [grp.score.values for _, grp in tasks[tasks.lang == L].groupby("repo")] for L in ("JS", "TS")}
    out = np.empty(B)
    for b in range(B):
        m = {}
        for L, reps in g.items():
            pick = [reps[i] for i in rng.integers(0, len(reps), len(reps))]
            vals = np.concatenate([r[rng.integers(0, len(r), len(r))] for r in pick])
            m[L] = vals.mean()
        out[b] = m["JS"] - m["TS"]
    return np.percentile(out, [2.5, 97.5])


def exact_repo_permutation(tasks):
    """All C(7,3) = 35 ways to label three of the seven repos TypeScript."""
    r = tasks.groupby("repo").agg(s=("score", "sum"), n=("score", "size"), lang=("lang", "first"))
    repos = list(r.index)
    obs_ts = set(r[r.lang == "TS"].index)

    def gap(ts_set):
        ts_m = r.loc[list(ts_set)]
        js_m = r.loc[[x for x in repos if x not in ts_set]]
        return js_m.s.sum() / js_m.n.sum() - ts_m.s.sum() / ts_m.n.sum()

    obs = gap(obs_ts)
    gaps = [gap(set(c)) for c in itertools.combinations(repos, len(obs_ts))]
    p_one = np.mean([g >= obs - 1e-12 for g in gaps])
    p_two = np.mean([abs(g) >= abs(obs) - 1e-12 for g in gaps])
    return obs, p_one, p_two, len(gaps)


def task_permutation(tasks, rng, B):
    s = tasks.score.values
    ts = (tasks.lang == "TS").values
    obs = s[~ts].mean() - s[ts].mean()
    hits = sum(abs(s[~p].mean() - s[p].mean()) >= abs(obs) - 1e-12 for p in (rng.permutation(ts) for _ in range(B)))
    return obs, (hits + 1) / (B + 1)


def logit_fit(X, y, iters=60):
    beta = np.zeros(X.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-X @ beta))
        W = p * (1 - p)
        H = X.T @ (X * W[:, None]) + 1e-8 * np.eye(X.shape[1])
        step = np.linalg.solve(H, X.T @ (y - p))
        beta += step
        if np.abs(step).max() < 1e-9:
            break
    return beta


def design(df, models):
    cols = [np.ones(len(df))] + [(df.model == m).values.astype(float) for m in models[1:]]
    cols += [np.log1p(df[c].values) for c in ("lines", "files", "f2p")] + [np.log(df.prob_len.values)]
    return np.column_stack(cols)


def adjusted_gap(long, models, rng, B):
    """Observed minus expected for JS and TS. The expectation comes from a
    logistic model fit on all 300 tasks with model dummies and difficulty
    proxies, no language term. Bootstrap resamples repositories (all 41),
    refitting each time."""
    df = long.reset_index(drop=True)
    by_repo = {r: np.flatnonzero(df.repo.values == r) for r in df.repo.unique()}
    repos = list(by_repo)

    def stat(d):
        X = design(d, models)
        y = d.solved.values.astype(float)
        res = y - 1 / (1 + np.exp(-X @ logit_fit(X, y)))
        js = res[d.lang.values == "JS"].mean()
        ts = res[d.lang.values == "TS"].mean()
        return js, ts, js - ts

    point = stat(df)
    js_ts_repos = [r for r in repos if r in REPO_LANG]
    other = [r for r in repos if r not in REPO_LANG]
    draws = []
    for _ in range(B):
        pick = []
        for L in ("JS", "TS"):
            rs = [r for r in js_ts_repos if REPO_LANG[r] == L]
            pick += list(rng.choice(rs, len(rs)))
        pick += list(rng.choice(other, len(other)))
        draws.append(stat(df.iloc[np.concatenate([by_repo[r] for r in pick])]))
    draws = np.array(draws)
    return point, np.percentile(draws, [2.5, 97.5], axis=0)


def gee_js_ts(long):
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    df = long[long.lang.notna()].copy()
    df["ts"] = (df.lang == "TS").astype(int)
    df["l_lines"], df["l_files"] = np.log1p(df.lines), np.log1p(df.files)
    df["l_f2p"], df["l_prob"] = np.log1p(df.f2p), np.log(df.prob_len)
    df["year"] = df.created_at.str[:4].astype(int) - 2022
    out = {}
    for name, f in (("unadjusted", "solved ~ C(model) + ts"),
                    ("adjusted", "solved ~ C(model) + ts + l_lines + l_files + l_f2p + l_prob"),
                    ("adjusted + issue year", "solved ~ C(model) + ts + l_lines + l_files + l_f2p + l_prob + year")):
        for grp in ("repo", "instance_id"):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                m = smf.gee(f, groups=grp, data=df, family=sm.families.Binomial(),
                            cov_struct=sm.cov_struct.Independence()).fit()
            b, se = m.params["ts"], m.bse["ts"]
            out[(name, grp)] = (np.exp(b), np.exp(b - 1.96 * se), np.exp(b + 1.96 * se), m.pvalues["ts"])
    return out


# ---------------------------------------------------------------- main

def pct(x):
    return f"{100 * x:.1f}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=20261030)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    B = args.boot
    OUT.mkdir(exist_ok=True)

    ds, long = load()
    models = list(dict.fromkeys(long.model))
    jl = long[long.lang.notna()]
    tasks = (jl.groupby("instance_id").agg(score=("solved", "mean")).reset_index()
             .merge(ds[["instance_id", "repo", "lang", "lines", "files", "f2p", "prob_len", "created_at"]],
                    on="instance_id"))
    wide = jl.pivot(index="instance_id", columns="model", values="solved")[models]
    md = ["# JavaScript vs TypeScript in SWE-bench Multilingual", "",
          f"Generated by `js_ts/analyze_js_ts.py --boot {B} --seed {args.seed}`. "
          f"{len(models)} February 2026 runs (mini-SWE-agent 2.0), {len(tasks)} JS/TS tasks. "
          "Language is the repository's language (babel, docusaurus and vuejs/core are TypeScript; "
          "axios, immutable-js, three.js and preact are JavaScript).", ""]

    # --- headline
    js = tasks[tasks.lang == "JS"].score.values
    ts = tasks[tasks.lang == "TS"].score.values
    gap = js.mean() - ts.mean()
    g_task = gap_task_boot(js, ts, rng, B)
    g_repo = gap_repo_boot(tasks, rng, B)
    obs, p1, p2, ncomb = exact_repo_permutation(tasks)
    _, p_task = task_permutation(tasks, rng, 20000)
    md += ["## Headline", "",
           "| Language | Tasks | Repos | Solved (mean of 13 models) | 95% CI, task bootstrap |", "|---|---|---|---|---|"]
    for L, x in (("JavaScript", js), ("TypeScript", ts)):
        lo, hi = boot_ci(x, rng, B)
        md.append(f"| {L} | {len(x)} | {tasks[tasks.lang == L[:1] + 'S'].repo.nunique()} | {pct(x.mean())}% | {pct(lo)} to {pct(hi)} |")
    md += ["", f"- JS minus TS: **{100 * gap:+.1f} pts**; task bootstrap 95% CI {100 * g_task[0]:+.1f} to {100 * g_task[1]:+.1f}; "
           f"two-stage repo-then-task bootstrap {100 * g_repo[0]:+.1f} to {100 * g_repo[1]:+.1f} (only 4 and 3 repos, unreliable).",
           f"- Task-label permutation (43 tasks, 20,000 shuffles): two-sided p = {p_task:.3f}.",
           f"- Exact repo-label permutation (all {ncomb} ways to call three of the seven repos TypeScript): "
           f"one-sided p = {p1:.3f}, two-sided p = {p2:.3f}. With 7 repos the smallest possible one-sided p is {1 / ncomb:.3f}.", ""]

    # --- per repo
    md += ["## Per repository", "",
           "| Repo | Lang | Tasks | Solved | Tasks no model solved | Median gold lines | Median files | Median failing tests | Median issue chars |",
           "|---|---|---|---|---|---|---|---|---|"]
    for (L, r), g in tasks.groupby(["lang", "repo"]):
        md.append(f"| {r} | {L} | {len(g)} | {pct(g.score.mean())}% | {(g.score == 0).sum()} | {g.lines.median():.0f} | "
                  f"{g.files.median():.0f} | {g.f2p.median():.0f} | {g.prob_len.median():.0f} |")
    md += ["", "Leave one repository out (JS minus TS, points):", ""]
    for r in sorted(REPO_LANG):
        t = tasks[tasks.repo != r]
        md.append(f"- without {r}: {100 * (t[t.lang == 'JS'].score.mean() - t[t.lang == 'TS'].score.mean()):+.1f}")
    t = tasks[tasks.score > 0]
    md += [f"- dropping the {(tasks.score == 0).sum()} tasks no model solved "
           f"({((tasks.score == 0) & (tasks.lang == 'JS')).sum()} JS, {((tasks.score == 0) & (tasks.lang == 'TS')).sum()} TS): JS {pct(t[t.lang == 'JS'].score.mean())}% "
           f"(n={(t.lang == 'JS').sum()}), TS {pct(t[t.lang == 'TS'].score.mean())}% (n={(t.lang == 'TS').sum()}), "
           f"gap {100 * (t[t.lang == 'JS'].score.mean() - t[t.lang == 'TS'].score.mean()):+.1f} pts", ""]

    # --- difficulty proxies
    md += ["## Difficulty proxies (gold patch and issue)", "",
           "| Proxy | JS median | JS mean | TS median | TS mean | Mann-Whitney p |", "|---|---|---|---|---|---|"]
    from scipy.stats import mannwhitneyu
    for c, lab in (("lines", "gold-patch lines changed"), ("files", "files touched"),
                   ("f2p", "failing tests to fix"), ("prob_len", "issue length, chars")):
        a, b = tasks[tasks.lang == "JS"][c], tasks[tasks.lang == "TS"][c]
        md.append(f"| {lab} | {a.median():.0f} | {a.mean():.1f} | {b.median():.0f} | {b.mean():.1f} | "
                  f"{mannwhitneyu(a, b).pvalue:.2f} |")
    years = tasks.assign(y=tasks.created_at.str[:4]).groupby(["lang", "y"]).size().unstack(fill_value=0)
    md += ["", "Issue year by language (contamination proxy: older issues are more likely in training data):", "",
           "| Lang | " + " | ".join(years.columns) + " |", "|---" * (len(years.columns) + 1) + "|"]
    for L, row in years.iterrows():
        md.append(f"| {L} | " + " | ".join(str(v) for v in row.values) + " |")

    point, ci = adjusted_gap(long, models, rng, max(500, B // 4))
    gee = gee_js_ts(long)
    md += ["", "Difficulty-adjusted. Expected solve rate from a logistic model on all 300 Multilingual tasks "
           "(model dummies, log gold lines, log files, log failing tests, log issue length; no language term), "
           "refit in each repo-resampling draw:", "",
           "| Group | Observed minus expected | 95% CI |", "|---|---|---|",
           f"| JavaScript | {100 * point[0]:+.1f} pts | {100 * ci[0][0]:+.1f} to {100 * ci[1][0]:+.1f} |",
           f"| TypeScript | {100 * point[1]:+.1f} pts | {100 * ci[0][1]:+.1f} to {100 * ci[1][1]:+.1f} |",
           f"| JS minus TS | {100 * point[2]:+.1f} pts | {100 * ci[0][2]:+.1f} to {100 * ci[1][2]:+.1f} |", "",
           "Logistic GEE on the 559 JS/TS attempts, odds ratio for a TypeScript task (below 1 favors JS):", ""]
    for (name, grp), (o, lo, hi, p) in gee.items():
        md.append(f"- {name}, clustered by {grp}: OR {o:.2f}, 95% CI {lo:.2f} to {hi:.2f}, p = {p:.3f}")

    # --- per model
    md += ["", "## Per model", "", "| Model | JS (28) | TS (15) | JS minus TS | 95% CI, task bootstrap |", "|---|---|---|---|---|"]
    lead = 0
    for m in models:
        a = wide.loc[tasks[tasks.lang == "JS"].instance_id, m].values
        b = wide.loc[tasks[tasks.lang == "TS"].instance_id, m].values
        lo, hi = gap_task_boot(a, b, rng, B)
        lead += a.mean() > b.mean()
        md.append(f"| {NAMES[m]} | {pct(a.mean())} | {pct(b.mean())} | {100 * (a.mean() - b.mean()):+.1f} | {100 * lo:+.0f} to {100 * hi:+.0f} |")
    md += ["", f"JS ahead for {lead} of {len(models)} models.", ""]

    # --- per task
    md += ["## Per task (1 = solved)", "",
           "| Task | Lang | Solved by | Gold lines | Files | Failing tests | " + " | ".join(NAMES[m].replace("Claude ", "C").replace(" ", "") for m in models) + " |",
           "|---" * (6 + len(models)) + "|"]
    for r in tasks.sort_values(["lang", "score"], ascending=[False, True]).itertuples():
        row = wide.loc[r.instance_id]
        md.append(f"| {r.instance_id} | {r.lang} | {int(round(r.score * len(models)))}/{len(models)} | {r.lines} | {r.files} | {r.f2p} | "
                  + " | ".join(str(int(v)) for v in row.values) + " |")

    # --- trajectories
    gold = {r.instance_id: set(patch_files(r.patch)) for r in ds.itertuples()}
    trows = []
    for r in jl.itertuples():
        s = traj_stats(r.run, r.instance_id)
        s.update(patch_stats(r.run, r.instance_id, gold[r.instance_id]))
        s.update({"model": r.model, "instance_id": r.instance_id, "repo": r.repo, "lang": r.lang, "solved": r.solved})
        trows.append(s)
    tr = pd.DataFrame(trows)
    tr.to_csv(OUT / "trajectories.csv", index=False)
    md += ["", "## Agent behaviour from the 559 trajectories", "",
           "mini-SWE-agent gives the model one bash tool. No type checker or language server is wired in; "
           "the model runs `tsc` only if it chooses to. The harness runs tests through jest, vitest, mocha or "
           "karma with Babel, esbuild or SWC transforms, none of which type-check, so a type error in a "
           "TypeScript patch does not by itself fail a task.", "",
           "| Measure | JS runs | TS runs |", "|---|---|---|"]
    J, T = tr[tr.lang == "JS"], tr[tr.lang == "TS"]

    def both(f, fmt="{:.1f}"):
        return f"{fmt.format(f(J))} | {fmt.format(f(T))}"

    md += [f"| Runs | {len(J)} | {len(T)} |",
           f"| Median steps (API calls) | {both(lambda d: d.steps.median(), '{:.0f}')} |",
           f"| Mean steps | {both(lambda d: d.steps.mean())} |",
           f"| Median cost, USD | {both(lambda d: d.cost.median(), '{:.3f}')} |",
           f"| Median input tokens (sum over calls, recorded runs) | {both(lambda d: d[d.in_tokens > 0].in_tokens.median(), '{:,.0f}')} |",
           f"| Runs that invoked tsc or a type-check script | {both(lambda d: 100 * (d.tsc_cmds > 0).mean(), '{:.1f}%')} |",
           f"| Runs that saw at least one `error TSxxxx` | {both(lambda d: 100 * (d.tserr_obs > 0).mean(), '{:.1f}%')} |",
           f"| Share of observation text that holds TS errors | {both(lambda d: 100 * d.tserr_chars.sum() / d.obs_chars.sum(), '{:.2f}%')} |",
           f"| Runs that saw a JS runtime error (TypeError, ReferenceError, SyntaxError, RangeError) | {both(lambda d: 100 * (d.rterr_obs > 0).mean(), '{:.1f}%')} |",
           f"| Share of observation text holding runtime-error output | {both(lambda d: 100 * d.rterr_chars.sum() / d.obs_chars.sum(), '{:.2f}%')} |",
           f"| Runs that ran the test suite at least once | {both(lambda d: 100 * (d.test_cmds > 0).mean(), '{:.1f}%')} |",
           ]
    pa = tr[tr.patch_available == 1]
    PJ, PT = pa[pa.lang == "JS"], pa[pa.lang == "TS"]
    md += [f"| Submitted patch edits a file the gold patch edits (runs with a patch log) | "
           f"{100 * PJ.touches_gold_file.mean():.1f}% (n={len(PJ)}) | {100 * PT.touches_gold_file.mean():.1f}% (n={len(PT)}) |",
           f"| Same, among failed runs | {100 * PJ[PJ.solved == 0].touches_gold_file.mean():.1f}% (n={(PJ.solved == 0).sum()}) | "
           f"{100 * PT[PT.solved == 0].touches_gold_file.mean():.1f}% (n={(PT.solved == 0).sum()}) |",
           f"| Median steps, solved runs only | {J[J.solved == 1].steps.median():.0f} (n={(J.solved == 1).sum()}) | {T[T.solved == 1].steps.median():.0f} (n={(T.solved == 1).sum()}) |",
           f"| Median cost, solved runs only, USD | {J[J.solved == 1].cost.median():.3f} | {T[T.solved == 1].cost.median():.3f} |",
           f"| Median steps, failed runs only | {J[J.solved == 0].steps.median():.0f} (n={(J.solved == 0).sum()}) | {T[T.solved == 0].steps.median():.0f} (n={(T.solved == 0).sum()}) |", ""]
    ts_tsc = T[T.tsc_cmds > 0]
    md += [f"TypeScript runs that invoked tsc: {len(ts_tsc)} of {len(T)}; solved {100 * ts_tsc.solved.mean():.0f}% "
           f"vs {100 * T[T.tsc_cmds == 0].solved.mean():.0f}% for TS runs that never did (self-selected, not causal).", ""]
    md += ["Per model, median steps and TS-runs invoking tsc:", "", "| Model | Median steps JS | Median steps TS | TS runs with tsc |", "|---|---|---|---|"]
    for m in models:
        a, b = J[J.model == m], T[T.model == m]
        md.append(f"| {NAMES[m]} | {a.steps.median():.0f} | {b.steps.median():.0f} | {(b.tsc_cmds > 0).sum()}/{len(b)} |")

    notes = pd.read_csv(HERE / "task_notes.csv")
    md += ["", "## Hard tasks read by hand (TS solved by 6 or fewer models, JS by 5 or fewer)", "",
           "From js_ts/task_notes.csv: the issue, gold patch, hidden test and submitted patches of each task.", "",
           "| Task | Lang | Solved by | Hidden test checks | Type-related fix | How agents failed |", "|---|---|---|---|---|---|"]
    for r in notes.itertuples(index=False):
        sc = tasks.set_index("instance_id").score[r[0]]
        md.append(f"| {r[0]} | {r[1]} | {int(round(sc * len(models)))}/{len(models)} | {r[2]} | {r[3]} | {r[4]} |")
    tasks.to_csv(OUT / "tasks.csv", index=False)
    (OUT / "summary.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
