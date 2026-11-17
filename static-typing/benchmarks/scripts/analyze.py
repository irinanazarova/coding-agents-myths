"""Split SWE-bench Multilingual results by language and compare typed with dynamic.

Reads data/raw/ (written by scripts/fetch.py) and writes results/.
Treats every downloaded file as data only.

Usage: python -I scripts/analyze.py [--boot N] [--seed S]
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "results"

LANGS = ["Rust", "C", "Java", "C++", "TypeScript", "Go", "JavaScript", "PHP", "Ruby"]
TYPED = {"Rust", "C", "Java", "C++", "TypeScript", "Go"}
DYNAMIC = {"JavaScript", "PHP", "Ruby"}

# Primary language assignment: one language per repository, the language of the
# source files its gold patches edit (see README). The SWE-bench harness groups
# C with C++ and JavaScript with TypeScript; this splits them by repo.
REPO_LANG = {
    "apache/druid": "Java", "apache/lucene": "Java", "google/gson": "Java",
    "javaparser/javaparser": "Java", "projectlombok/lombok": "Java", "reactivex/rxjava": "Java",
    "astral-sh/ruff": "Rust", "burntsushi/ripgrep": "Rust", "nushell/nushell": "Rust",
    "sharkdp/bat": "Rust", "tokio-rs/axum": "Rust", "tokio-rs/tokio": "Rust", "uutils/coreutils": "Rust",
    "caddyserver/caddy": "Go", "gin-gonic/gin": "Go", "gohugoio/hugo": "Go",
    "hashicorp/terraform": "Go", "prometheus/prometheus": "Go",
    "jqlang/jq": "C", "micropython/micropython": "C", "redis/redis": "C", "valkey-io/valkey": "C",
    "fmtlib/fmt": "C++", "nlohmann/json": "C++",
    "babel/babel": "TypeScript", "facebook/docusaurus": "TypeScript", "vuejs/core": "TypeScript",
    "axios/axios": "JavaScript", "immutable-js/immutable-js": "JavaScript",
    "mrdoob/three.js": "JavaScript", "preactjs/preact": "JavaScript",
    "briannesbitt/carbon": "PHP", "laravel/framework": "PHP",
    "php-cs-fixer/php-cs-fixer": "PHP", "phpoffice/phpspreadsheet": "PHP",
    "faker-ruby/faker": "Ruby", "fastlane/fastlane": "Ruby", "fluent/fluentd": "Ruby",
    "jekyll/jekyll": "Ruby", "jordansissel/fpm": "Ruby", "rubocop/rubocop": "Ruby",
}

# The six models on the Deccan Queen slide (2026-10-09).
DECK6 = ["claude-4-6-opus", "claude-4-5-opus", "gemini-3-pro",
         "claude-4-5-sonnet", "gpt-5-2-high", "gpt-5-2-codex"]

# Task-level assignment used for the slide: dominant source-file extension in
# the gold patch. Reimplemented from the slide's script for the sensitivity check.
PATCH_EXT = {"rs": "Rust", "java": "Java", "go": "Go", "c": "C", "h": "C", "cc": "C++",
             "cpp": "C++", "hpp": "C++", "hh": "C++", "ts": "TypeScript", "tsx": "TypeScript",
             "mts": "TypeScript", "js": "JavaScript", "jsx": "JavaScript", "cjs": "JavaScript",
             "mjs": "JavaScript", "php": "PHP", "rb": "Ruby", "rake": "Ruby"}


def patch_files(patch: str) -> list[str]:
    return re.findall(r"^diff --git a/(\S+)", patch, re.M)


def patch_lang(row) -> str:
    if row.repo in ("fmtlib/fmt", "nlohmann/json"):
        return "C++"
    files = [f for f in patch_files(row.patch) if not f.endswith(".d.ts")]
    c = collections.Counter(PATCH_EXT[f.rsplit(".", 1)[-1]] for f in files if f.rsplit(".", 1)[-1] in PATCH_EXT)
    return c.most_common(1)[0][0] if c else REPO_LANG[row.repo]


def changed_lines(patch: str) -> int:
    return sum(1 for ln in patch.splitlines()
               if (ln.startswith("+") or ln.startswith("-")) and not ln.startswith(("+++", "---")))


def n_tests(x) -> int:
    if isinstance(x, str):
        try:
            x = json.loads(x)
        except json.JSONDecodeError:
            return 1
    return len(x)


def load():
    ds = pd.read_parquet(RAW / "dataset" / "test.parquet")
    assert len(ds) == 300 and ds.instance_id.is_unique
    missing = set(ds.repo) - set(REPO_LANG)
    assert not missing, missing
    ds["lang"] = ds.repo.map(REPO_LANG)
    ds["lang_patch"] = [patch_lang(r) for r in ds.itertuples()]
    ds["lines"] = ds.patch.map(changed_lines)
    ds["files"] = ds.patch.map(lambda p: len(patch_files(p)))
    ds["f2p"] = ds.FAIL_TO_PASS.map(n_tests)
    ds["prob_len"] = ds.problem_statement.str.len()
    tasks = ds[["instance_id", "repo", "lang", "lang_patch", "lines", "files", "f2p", "prob_len"]].copy()

    subs, rows = [], []
    for d in sorted((RAW / "experiments").iterdir()):
        meta = yaml.safe_load((d / "metadata.yaml").read_text())
        pid = json.loads((d / "per_instance_details.json").read_text())
        key = d.name.split("_", 2)[2]
        resolved = {iid: bool(v.get("resolved") is True) for iid, v in pid.items()}
        n_ok = sum(resolved.get(i, False) for i in tasks.instance_id)
        subs.append({"folder": d.name, "model": key, "name": meta["info"]["name"],
                     "date": d.name[:8], "agent_version": meta["info"].get("mini-swe-agent_version"),
                     "official_resolved": meta["info"].get("resolved"),
                     "instances_reported": len(pid), "recomputed_resolved": round(100 * n_ok / 300, 2)})
        for iid in tasks.instance_id:
            rows.append({"model": key, "instance_id": iid, "solved": int(resolved.get(iid, False))})
    subs = pd.DataFrame(subs)
    long = pd.DataFrame(rows).merge(tasks, on="instance_id")
    return tasks, subs, long


# ---------------------------------------------------------------- statistics

def task_scores(long, models):
    s = long[long.model.isin(models)].groupby("instance_id").solved.mean()
    return s


def group_rate(scores, tasks, langcol, members):
    t = tasks[tasks[langcol].isin(members)]
    return scores.loc[t.instance_id].mean()


def cluster_boot(scores, tasks, langcol, rng, B):
    """Resample repositories with replacement inside each language; return
    bootstrap draws of each language rate, typed, dynamic and the difference."""
    t = tasks.assign(score=scores.loc[tasks.instance_id].values)
    by_repo = t.groupby("repo").agg(s=("score", "sum"), n=("score", "size"), lang=(langcol, "first"))
    # With the patch-level map a repo can span two languages, so split per (repo, lang).
    rl = t.groupby(["repo", langcol]).agg(s=("score", "sum"), n=("score", "size")).reset_index()
    out = {k: np.empty(B) for k in LANGS + ["Typed", "Dynamic", "Dynamic - Typed"]}
    strata = {L: rl[rl[langcol] == L] for L in LANGS}
    for b in range(B):
        S, N = {}, {}
        for L, g in strata.items():
            idx = rng.integers(0, len(g), len(g))
            S[L], N[L] = g.s.values[idx].sum(), g.n.values[idx].sum()
            out[L][b] = S[L] / N[L]
        ty = sum(S[L] for L in TYPED) / sum(N[L] for L in TYPED)
        dy = sum(S[L] for L in DYNAMIC) / sum(N[L] for L in DYNAMIC)
        out["Typed"][b], out["Dynamic"][b], out["Dynamic - Typed"][b] = ty, dy, dy - ty
    del by_repo
    return out


def repo_permutation(scores, tasks, rng, B):
    """Permute the typed/dynamic label across the 41 repositories (language is a
    repo property), keeping each repo's tasks together."""
    t = tasks.assign(score=scores.loc[tasks.instance_id].values)
    r = t.groupby("repo").agg(s=("score", "sum"), n=("score", "size"), lang=("lang", "first"))
    dyn = r.lang.isin(DYNAMIC).values
    s, n = r.s.values, r.n.values
    obs = s[dyn].sum() / n[dyn].sum() - s[~dyn].sum() / n[~dyn].sum()
    hits = 0
    for _ in range(B):
        p = rng.permutation(dyn)
        d = s[p].sum() / n[p].sum() - s[~p].sum() / n[~p].sum()
        hits += abs(d) >= abs(obs) - 1e-12
    return obs, (hits + 1) / (B + 1)


def logit_fit(X, y, iters=50):
    """Plain Newton-Raphson logistic regression (used inside the bootstrap)."""
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


def design(df, models, with_dynamic):
    cols = [np.ones(len(df))]
    for m in models[1:]:
        cols.append((df.model == m).values.astype(float))
    for c in ("lines", "files", "f2p"):
        cols.append(np.log1p(df[c].values))
    cols.append(np.log(df.prob_len.values))
    if with_dynamic:
        cols.append(df.lang.isin(DYNAMIC).values.astype(float))
    return np.column_stack(cols)


def adjusted_residuals(long, tasks, models, rng, B):
    """Observed minus expected solve rate per language, where 'expected' comes
    from a logistic model with model dummies and difficulty proxies only
    (gold-patch size, files touched, failing tests to fix, issue length).
    Cluster bootstrap over repositories, refitting the model each time."""
    df = long[long.model.isin(models)].reset_index(drop=True)
    repos = tasks.repo.unique()
    by_repo = {r: np.flatnonzero(df.repo.values == r) for r in repos}

    def stat(d):
        X = design(d, models, False)
        y = d.solved.values.astype(float)
        p = 1 / (1 + np.exp(-X @ logit_fit(X, y)))
        res = y - p
        out = {L: res[d.lang.values == L].mean() for L in LANGS}
        out["Typed"] = res[d.lang.isin(TYPED).values].mean()
        out["Dynamic"] = res[d.lang.isin(DYNAMIC).values].mean()
        out["Dynamic - Typed"] = out["Dynamic"] - out["Typed"]
        return out

    point = stat(df)
    lang_repos = {L: [r for r in repos if REPO_LANG[r] == L] for L in LANGS}
    draws = collections.defaultdict(list)
    for _ in range(B):
        idx = []
        for L, rs in lang_repos.items():
            for r in rng.choice(rs, len(rs), replace=True):
                idx.append(by_repo[r])
        s = stat(df.iloc[np.concatenate(idx)])
        for k, v in s.items():
            draws[k].append(v)
    return point, {k: np.array(v) for k, v in draws.items()}


def gee_typed(long, models):
    """Logistic GEE with an independence working correlation and repo-clustered
    (sandwich) standard errors: odds ratio for dynamic vs typed, with and without
    difficulty proxies."""
    import statsmodels.api as sm
    import statsmodels.formula.api as smf

    df = long[long.model.isin(models)].copy()
    df["dynamic"] = df.lang.isin(DYNAMIC).astype(int)
    df["l_lines"], df["l_files"] = np.log1p(df.lines), np.log1p(df.files)
    df["l_f2p"], df["l_prob"] = np.log1p(df.f2p), np.log(df.prob_len)
    res = {}
    for name, f in (("unadjusted", "solved ~ C(model) + dynamic"),
                    ("adjusted", "solved ~ C(model) + dynamic + l_lines + l_files + l_f2p + l_prob")):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            m = smf.gee(f, groups="repo", data=df, family=sm.families.Binomial(),
                        cov_struct=sm.cov_struct.Independence()).fit()
        b, se = m.params["dynamic"], m.bse["dynamic"]
        res[name] = {"OR": float(np.exp(b)), "lo": float(np.exp(b - 1.96 * se)),
                     "hi": float(np.exp(b + 1.96 * se)), "p": float(m.pvalues["dynamic"])}
    return res


def mixed_typed(long, tasks, models):
    """Linear mixed model on task-level scores (share of models that solved the
    task), random intercept per repository, fit by REML. The coefficient is in
    percentage points, dynamic minus typed."""
    import statsmodels.formula.api as smf

    sc = task_scores(long, models)
    df = tasks.assign(score=sc.loc[tasks.instance_id].values)
    df["dynamic"] = df.lang.isin(DYNAMIC).astype(int)
    df["l_lines"], df["l_files"] = np.log1p(df.lines), np.log1p(df.files)
    df["l_f2p"], df["l_prob"] = np.log1p(df.f2p), np.log(df.prob_len)
    out = {}
    for name, f in (("unadjusted", "score ~ dynamic"),
                    ("adjusted", "score ~ dynamic + l_lines + l_files + l_f2p + l_prob")):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = smf.mixedlm(f, df, groups=df["repo"]).fit(reml=True)
        b, se = r.params["dynamic"], r.bse["dynamic"]
        out[name] = {"b": float(b), "lo": float(b - 1.96 * se), "hi": float(b + 1.96 * se),
                     "p": float(r.pvalues["dynamic"]), "repo_sd": float(np.sqrt(r.cov_re.iloc[0, 0])),
                     "resid_sd": float(np.sqrt(r.scale))}
    return out


# ---------------------------------------------------------------- reporting

def pct(x):
    return f"{100 * x:.1f}"


def ci(a):
    lo, hi = np.percentile(a, [2.5, 97.5])
    return f"[{100 * lo:.0f}, {100 * hi:.0f}]"


def ci_pts(a):
    lo, hi = np.percentile(a, [2.5, 97.5])
    return f"[{100 * lo:+.1f}, {100 * hi:+.1f}]"


def per_model_table(long, subs, models, langcol):
    lines = ["| Model | All | " + " | ".join(LANGS) + " | Typed | Dynamic | Last language |",
             "|" + "---|" * (len(LANGS) + 5)]
    for m in models:
        d = long[long.model == m]
        r = {L: d[d[langcol] == L].solved.mean() for L in LANGS}
        ty = d[d[langcol].isin(TYPED)].solved.mean()
        dy = d[d[langcol].isin(DYNAMIC)].solved.mean()
        worst = min(LANGS, key=lambda L: r[L])
        name = subs.set_index("model").loc[m, "name"]
        lines.append(f"| {name} | {pct(d.solved.mean())} | " + " | ".join(pct(r[L]) for L in LANGS)
                     + f" | {pct(ty)} | {pct(dy)} | {worst} |")
    return "\n".join(lines)


def summary_block(long, tasks, models, langcol, rng, B, label):
    sc = task_scores(long, models)
    boot = cluster_boot(sc, tasks, langcol, rng, B)
    rows = ["| Group | Tasks | Repos | Solved (mean of models) | 95% CI, repo-clustered | 95% CI, task-level |",
            "|---|---|---|---|---|---|"]
    def tboot(ids):
        x = sc.loc[ids].values
        return np.array([x[rng.integers(0, len(x), len(x))].mean() for _ in range(B)])
    rec = {}
    for L in LANGS:
        t = tasks[tasks[langcol] == L]
        v = sc.loc[t.instance_id].mean()
        rec[L] = v
        flag = " *" if t.repo.nunique() < 5 else ""
        rows.append(f"| {L} ({'typed' if L in TYPED else 'dynamic'}) | {len(t)} | {t.repo.nunique()}{flag} | {pct(v)}% | {ci(boot[L])} | {ci(tboot(t.instance_id))} |")
    for g, mem in (("All typed", TYPED), ("All dynamic", DYNAMIC)):
        t = tasks[tasks[langcol].isin(mem)]
        v = sc.loc[t.instance_id].mean()
        rec[g] = v
        rows.append(f"| **{g}** | {len(t)} | {t.repo.nunique()} | **{pct(v)}%** | {ci(boot['Typed' if g == 'All typed' else 'Dynamic'])} | {ci(tboot(t.instance_id))} |")
    diff = rec["All dynamic"] - rec["All typed"]
    T = tasks[tasks[langcol].isin(TYPED)].instance_id
    D = tasks[tasks[langcol].isin(DYNAMIC)].instance_id
    td = np.array([sc.loc[D].values[rng.integers(0, len(D), len(D))].mean()
                   - sc.loc[T].values[rng.integers(0, len(T), len(T))].mean() for _ in range(B)])
    rows.append(f"| Dynamic minus typed | | | {100 * diff:+.1f} pts | {ci_pts(boot['Dynamic - Typed'])} | {ci_pts(td)} |")
    note = ("\n\n\\* Fewer than five repositories: the repo-clustered interval rests on two to four "
            "clusters and is unreliable; treat the language as a handful of projects.")
    return f"### {label}\n\n" + "\n".join(rows) + note, rec, boot


# ---------------------------------------------------------------- Python baseline

def load_verified():
    ds = pd.read_parquet(RAW / "dataset" / "verified.parquet")
    assert len(ds) == 500 and ds.instance_id.is_unique
    t = pd.DataFrame({"instance_id": ds.instance_id, "repo": ds.repo, "lang": "Python",
                      "lines": ds.patch.map(changed_lines), "files": ds.patch.map(lambda x: len(patch_files(x))),
                      "f2p": ds.FAIL_TO_PASS.map(lambda x: len(x) if not isinstance(x, str) else n_tests(x)),
                      "prob_len": ds.problem_statement.str.len(), "difficulty": ds.difficulty,
                      "patch": ds.patch, "base_commit": ds.base_commit, "created_at": ds.created_at})
    return t


def verified_resolved(folder):
    """Per-task results. Prefer the bucket's evaluation reports when fetched
    (Codex: no file in the repo; Gemini 3 Pro: the repo file marks every task
    unresolved, contradicting its official 69.6%)."""
    rep = RAW / "bucket_reports" / folder
    if not rep.exists():
        d = RAW / "experiments_verified" / folder / "per_instance_details.json"
        return {k: v.get("resolved") is True for k, v in json.loads(d.read_text()).items()}
    out = {}
    for f in rep.glob("*.json"):
        r = json.loads(f.read_text())
        out[f.stem] = r.get("resolved") is True
    return out


def run_config(bucket, folder):
    f = RAW / "trajs" / bucket / f"{folder}.traj.json"
    if not f.exists():
        return None
    d = json.loads(f.read_text())
    c = d["info"]["config"]
    kw = {k: v for k, v in (c["model"].get("model_kwargs") or {}).items() if k not in ("drop_params", "extra_headers")}
    a = c["agent"]
    return {"mini": d["info"].get("mini_version"), "model": c["model"].get("model_name"), "kwargs": json.dumps(kw, sort_keys=True),
            "step_limit": a.get("step_limit"), "cost_limit": a.get("cost_limit"),
            "template": a.get("system_template", "") + a.get("instance_template", "")}


def boot_mean(x, rng, B):
    x = np.asarray(x)
    return np.array([x[rng.integers(0, len(x), len(x))].mean() for _ in range(B)])


def strat_cluster(df, group_of_repo, rng, B):
    """df: instance_id, repo, score. Resample repos within each group; return
    draws of each group's task-weighted mean."""
    r = df.groupby("repo").agg(s=("score", "sum"), n=("score", "size")).reset_index()
    r["g"] = r.repo.map(group_of_repo)
    out = collections.defaultdict(list)
    strata = {g: x for g, x in r.groupby("g")}
    for _ in range(B):
        S, N = {}, {}
        for g, x in strata.items():
            i = rng.integers(0, len(x), len(x))
            S[g], N[g] = x.s.values[i].sum(), x.n.values[i].sum()
            out[g].append(S[g] / N[g])
        for name, mem in (("Typed", TYPED), ("Dynamic", DYNAMIC)):
            out[name].append(sum(S[g] for g in mem) / sum(N[g] for g in mem))
    return {k: np.array(v) for k, v in out.items()}


def python_baseline(tasks, subs, long, rng, B):
    pairs = json.loads((ROOT / "scripts" / "pairs.json").read_text())
    vt = load_verified()
    by_folder = subs.set_index("folder")
    md = ["", "## Python baseline: SWE-bench Verified runs of the same models", ""]

    # pair checks from the recorded trajectories
    md += ["Matching checks, read from one recorded trajectory per run:", "",
           "| Model | Multilingual run | Verified run | Model id (ML / Verified) | Model settings equal | Step / cost limit | mini version (ML / V) | Prompt templates | Used |",
           "|---|---|---|---|---|---|---|---|---|"]
    prow = []
    for p in pairs:
        a, b = run_config("multilingual", p["multilingual"]), run_config("bash-only", p["verified"])
        name = by_folder.loc[p["multilingual"], "name"]
        if a and b:
            tmpl = "same" if a["template"] == b["template"] else "one sentence differs" if abs(len(a["template"]) - len(b["template"])) < 120 else "differ"
            md.append(f"| {name} | {p['multilingual']} | {p['verified']} | {a['model']} / {b['model']} | "
                      f"{'yes' if a['kwargs'] == b['kwargs'] else 'no'} | {a['step_limit']}, {a['cost_limit']} / {b['step_limit']}, {b['cost_limit']} | "
                      f"{a['mini']} / {b['mini']} | {tmpl} | {'yes' if p['use'] else 'no'} |")
        else:
            md.append(f"| {name} | {p['multilingual']} | {p['verified']} | trajectory missing | | | | | {'yes' if p['use'] else 'no'} |")
        prow.append((name, p))
    md.append("")
    for name, p in prow:
        if not p["use"]:
            md.append(f"- Not used, {name}: {p['reason']}")

    # Codex duplicate check
    cod = verified_resolved("20260219_mini-v2.0.0_gpt-5-2-codex")
    g52 = verified_resolved("20260217_mini-v2.0.0_gpt-5-2-high")
    common = [i for i in vt.instance_id if i in cod and i in g52]
    agree = sum(cod[i] == g52[i] for i in common)
    md.append(f"- The Verified 'GPT 5.2 Codex' reports (from the submissions bucket) cover {len(cod)} tasks, "
              f"{sum(cod.values())} solved ({100 * sum(cod.values()) / 500:.1f}%); they agree with the Verified GPT 5.2 (high) "
              f"run on {agree} of {len(common)} tasks.")
    gp = verified_resolved("20260226_mini-v2.0.0_gemini-3-pro-high")
    md.append(f"- Gemini 3 Pro's per_instance_details.json in the experiments repo marks all 500 tasks unresolved, "
              f"against an official 69.6%. Its {len(gp)} evaluation reports in the submissions bucket give "
              f"{sum(gp.values())} solved ({100 * sum(gp.values()) / 500:.1f}%); those are used.")
    md.append("- Multilingual runs without a Verified twin at mini-SWE-agent 2.x: Gemini 3.5 Flash (Multilingual 2.4.6, "
              "Verified 2.4.2, 36 Multilingual tasks missing) is outside the February set and not paired.")

    used = [p for p in pairs if p["use"]]
    models = [by_folder.loc[p["multilingual"], "model"] for p in used]
    # Python long table, keyed by the Multilingual model key so models line up
    rows = []
    for p in used:
        res = verified_resolved(p["verified"])
        key = by_folder.loc[p["multilingual"], "model"]
        rows += [{"model": key, "instance_id": i, "solved": int(res.get(i, False))} for i in vt.instance_id]
    py_long = pd.DataFrame(rows).merge(vt.drop(columns=["patch", "base_commit", "created_at"]), on="instance_id")
    meta = {p["verified"]: yaml.safe_load((RAW / "experiments_verified" / p["verified"] / "metadata.yaml").read_text())
            for p in used}

    ml = long[long.model.isin(models)]
    ml_sc = ml.groupby("instance_id").solved.mean()
    py_sc = py_long.groupby("instance_id").solved.mean()
    ml_df = tasks[["instance_id", "repo", "lang"]].assign(score=ml_sc.loc[tasks.instance_id].values)
    py_df = vt[["instance_id", "repo", "lang"]].assign(score=py_sc.loc[vt.instance_id].values)
    both = pd.concat([ml_df, py_df])
    group_of_repo = {**REPO_LANG, **{r: "Python" for r in vt.repo.unique()}}
    draws = strat_cluster(both, group_of_repo, rng, B)

    md += ["", f"### {len(models)} matched models: nine Multilingual languages plus Python (Verified)", "",
           "| Language | Tasks | Repos | Solved (mean of models) | 95% CI, repo-clustered | 95% CI, task-level |",
           "|---|---|---|---|---|---|"]
    rec = {}
    for L in LANGS + ["Python"]:
        d = both[both.lang == L]
        rec[L] = d.score.mean()
        flag = " *" if d.repo.nunique() < 5 else ""
        kind = "typed" if L in TYPED else "dynamic"
        md.append(f"| {L} ({kind}) | {len(d)} | {d.repo.nunique()}{flag} | {pct(rec[L])}% | {ci(draws[L])} | {ci(boot_mean(d.score, rng, B))} |")
    for g, mem in (("Typed", TYPED), ("Dynamic", DYNAMIC)):
        d = both[both.lang.isin(mem)]
        rec[g] = d.score.mean()
        md.append(f"| **All {g.lower()} (Multilingual)** | {len(d)} | {d.repo.nunique()} | **{pct(rec[g])}%** | {ci(draws[g])} | {ci(boot_mean(d.score, rng, B))} |")
    d = both[both.lang == "Python"]
    md.append(f"| **Python (Verified)** | {len(d)} | {d.repo.nunique()} | **{pct(rec['Python'])}%** | {ci(draws['Python'])} | |")
    T = both[both.lang.isin(TYPED)].score.values
    D = both[both.lang.isin(DYNAMIC)].score.values
    P = d.score.values
    for g, X in (("Typed", T), ("Dynamic", D)):
        td = np.array([P[rng.integers(0, len(P), len(P))].mean() - X[rng.integers(0, len(X), len(X))].mean() for _ in range(B)])
        md.append(f"| Python minus {g.lower()} | | | {100 * (rec['Python'] - rec[g]):+.1f} pts | "
                  f"{ci_pts(draws['Python'] - draws[g])} | {ci_pts(td)} |")
    md += ["", f"Python's 12 repos are dominated by django ({(vt.repo == 'django/django').sum()} of 500 tasks) and sympy "
           f"({(vt.repo == 'sympy/sympy').sum()}); seaborn has 2 tasks and flask 1. The repo-clustered interval for Python rests on "
           "an effective two or three clusters and understates the uncertainty."]

    # per-model
    md += ["", "Per model (Multilingual typed / dynamic from the February runs; Python from the matched Verified run):", "",
           "| Model | Verified run | Python (Verified) | Official Verified % | Multilingual all | Typed | Dynamic | Ruby |",
           "|---|---|---|---|---|---|---|---|"]
    for p in used:
        key = by_folder.loc[p["multilingual"], "model"]
        a = py_long[py_long.model == key].solved.mean()
        m = ml[ml.model == key]
        md.append(f"| {by_folder.loc[p['multilingual'], 'name']} | {p['verified']} | {pct(a)} | {meta[p['verified']]['info']['resolved']} | "
                  f"{pct(m.solved.mean())} | {pct(m[m.lang.isin(TYPED)].solved.mean())} | {pct(m[m.lang.isin(DYNAMIC)].solved.mean())} | "
                  f"{pct(m[m.lang == 'Ruby'].solved.mean())} |")
    n_hi = sum(py_long[py_long.model == k].solved.mean() > ml[ml.model == k].solved.mean() for k in models)
    md.append(f"\nPython (Verified) is above the model's Multilingual total for {n_hi} of {len(models)} models.")

    # difficulty proxies
    allt = pd.concat([tasks.assign(group=tasks.lang)[["lang", "lines", "files", "f2p", "prob_len"]],
                      vt[["lang", "lines", "files", "f2p", "prob_len"]]])
    md += ["", "Difficulty proxies by language (medians):", "",
           "| Language | Gold-patch lines changed | Files touched | Failing tests to fix | Issue length (chars) |", "|---|---|---|---|---|"]
    for L in LANGS + ["Python"]:
        x = allt[allt.lang == L]
        md.append(f"| {L} | {x.lines.median():.0f} | {x.files.median():.0f} | {x.f2p.median():.0f} | {x.prob_len.median():.0f} |")
    vd = vt.difficulty.value_counts()
    md.append("\nVerified's annotator time estimates: " + ", ".join(f"{k}: {v}" for k, v in vd.items()) + ".")

    # difficulty-adjusted, Python included
    comb = pd.concat([ml[["model", "instance_id", "solved", "repo", "lang", "lines", "files", "f2p", "prob_len"]],
                      py_long[["model", "instance_id", "solved", "repo", "lang", "lines", "files", "f2p", "prob_len"]]]).reset_index(drop=True)
    groups = LANGS + ["Python"]
    repo_rows = {r: np.flatnonzero(comb.repo.values == r) for r in comb.repo.unique()}
    grp_repos = collections.defaultdict(list)
    for r in comb.repo.unique():
        grp_repos[group_of_repo[r]].append(r)

    def stat(d):
        X = design(d, models, False)
        y = d.solved.values.astype(float)
        res = y - 1 / (1 + np.exp(-X @ logit_fit(X, y)))
        out = {g: res[d.lang.values == g].mean() for g in groups}
        out["Typed"] = res[d.lang.isin(TYPED).values].mean()
        out["Dynamic"] = res[d.lang.isin(DYNAMIC).values].mean()
        return out

    point = stat(comb)
    dr = collections.defaultdict(list)
    for _ in range(max(300, B // 8)):
        idx = [repo_rows[r] for g, rs in grp_repos.items() for r in rng.choice(rs, len(rs), replace=True)]
        s_ = stat(comb.iloc[np.concatenate(idx)])
        for k, v in s_.items():
            dr[k].append(v)
    md += ["", "Difficulty-adjusted, Python included (observed minus expected; expectation from model and the four proxies, "
           "fit on Multilingual and Verified together, refit per repo-clustered draw):", "",
           "| Group | Observed minus expected | 95% CI |", "|---|---|---|"]
    for k in ["Python", "Typed", "Dynamic", "Ruby", "Go", "TypeScript", "Rust"]:
        md.append(f"| {k} | {100 * point[k]:+.1f} pts | {ci_pts(np.array(dr[k]))} |")

    # Python typing in the Verified repos
    md += ["", "Static typing in the Verified repos (config files at each repo's newest task's base commit; "
           "share of `def` lines added by gold patches that carry a return annotation):", "",
           "| Repo | Tasks | mypy named in config files | Annotated new defs |", "|---|---|---|---|"]
    for repo, g in vt.groupby("repo"):
        d_ = RAW / "typing_check" / repo.replace("/", "__")
        txt = " ".join(f.read_text(errors="ignore") for f in d_.glob("*")) if d_.exists() else ""
        defs = [ln for pt in g.patch for ln in pt.splitlines() if ln.startswith("+") and re.match(r"\+\s*(async\s+)?def ", ln)]
        ann = sum("->" in ln for ln in defs)
        md.append(f"| {repo} | {len(g)} | {'yes' if 'mypy' in txt else 'no'} | {ann}/{len(defs)} |")

    json.dump({"python_rec": {k: round(100 * v, 2) for k, v in rec.items()}, "models": models},
              open(OUT / "python_baseline.json", "w"), indent=2)
    return md


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=20261030)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    OUT.mkdir(exist_ok=True)

    tasks, subs, long = load()
    all_models = list(subs.model)
    feb = list(subs[subs.date < "20260301"].model)
    tasks.to_csv(OUT / "tasks.csv", index=False)
    subs.to_csv(OUT / "submissions.csv", index=False)

    md = ["# Results", "",
          f"Generated by `scripts/analyze.py --boot {args.boot} --seed {args.seed}`.", "",
          "## Submissions at the pinned commit", "",
          "| Folder | Model | Agent version | Instances in file | Official % | Recomputed % (unreported = unsolved) |",
          "|---|---|---|---|---|---|"]
    for s in subs.itertuples():
        md.append(f"| {s.folder} | {s.name} | {s.agent_version} | {s.instances_reported} | {s.official_resolved} | {s.recomputed_resolved} |")

    md += ["", "## Task counts by language", "",
           "| Language | Tasks (repo map) | Repos | Tasks (slide's patch map) |", "|---|---|---|---|"]
    for L in LANGS:
        md.append(f"| {L} | {(tasks.lang == L).sum()} | {tasks[tasks.lang == L].repo.nunique()} | {(tasks.lang_patch == L).sum()} |")
    moved = tasks[tasks.lang != tasks.lang_patch]
    md.append("")
    md.append("Tasks where the two maps disagree: " + ", ".join(
        f"{r.instance_id} ({r.lang} by repo, {r.lang_patch} by patch)" for r in moved.itertuples()))

    blocks = {}
    for key, models, label in (("feb", feb, f"Primary: all {len(feb)} February 2026 submissions (mini-SWE-agent 2.0)"),
                               ("deck6", DECK6, "The six models on the slide (February 2026)"),
                               ("all", all_models, f"All {len(all_models)} submissions, including Gemini 3.5 Flash "
                                "(September 2026; 36 tasks unattempted, counted unsolved)")):
        md += ["", f"## {label}", ""]
        for langcol, mlabel in (("lang", "Repo-level language map (primary)"),
                                ("lang_patch", "Task-level patch map (the slide's method)")):
            block, rec, boot = summary_block(long, tasks, models, langcol, rng, args.boot, mlabel)
            blocks[(key, langcol)] = rec
            md += [block, ""]
        sc = task_scores(long, models)
        obs, p = repo_permutation(sc, tasks, rng, 20000)
        md.append(f"Repo-level permutation test (typed/dynamic label shuffled across the 41 repos): "
                  f"dynamic minus typed = {100 * obs:+.1f} pts, two-sided p = {p:.2f}.")
        md += ["", "Per model, repo-level map:", "", per_model_table(long, subs, models, "lang"), ""]
        md += ["Per model, the slide's patch map:", "", per_model_table(long, subs, models, "lang_patch"), ""]

        point, draws = adjusted_residuals(long, tasks, models, rng, max(500, args.boot // 4))
        md += ["Difficulty-adjusted: observed minus expected solve rate, where the expectation uses "
               "model, gold-patch lines, files touched, failing tests to fix and issue length "
               "(logistic model refit in each repo-clustered bootstrap draw).", "",
               "| Group | Observed minus expected | 95% CI |", "|---|---|---|"]
        for k in LANGS + ["Typed", "Dynamic", "Dynamic - Typed"]:
            md.append(f"| {k} | {100 * point[k]:+.1f} pts | {ci_pts(draws[k])} |")
        g = gee_typed(long, models)
        md += ["", "Logistic GEE clustered by repository, odds ratio for a dynamic-language task "
               "vs a typed one (above 1 favors dynamic):", ""]
        for k, v in g.items():
            md.append(f"- {k}: OR {v['OR']:.2f}, 95% CI [{v['lo']:.2f}, {v['hi']:.2f}], p = {v['p']:.2f}")
        mm = mixed_typed(long, tasks, models)
        md += ["", "Linear mixed model on task scores with a random intercept per repository (REML), "
               "dynamic minus typed in points:", ""]
        for k, v in mm.items():
            md.append(f"- {k}: {100 * v['b']:+.1f} pts, 95% CI [{100 * v['lo']:+.1f}, {100 * v['hi']:+.1f}], "
                      f"p = {v['p']:.2f}; repo SD {100 * v['repo_sd']:.1f} pts, task SD {100 * v['resid_sd']:.1f} pts")

    md += python_baseline(tasks, subs, long, rng, args.boot)
    (OUT / "summary.md").write_text("\n".join(md) + "\n")
    json.dump({f"{k}|{c}": {g: round(100 * v, 2) for g, v in rec.items()} for (k, c), rec in blocks.items()},
              open(OUT / "headline.json", "w"), indent=2)
    print((OUT / "summary.md").read_text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
