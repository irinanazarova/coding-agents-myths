"""SWE-PolyBench Verified (Amazon): JavaScript vs TypeScript, per-instance re-analysis.

Reads data/raw/js_ts/pb/ (written by js_ts/fetch_js_ts.py) as CSV, JSON and
JSONL only and prints the tables. Only the 200 JS/TS result files of each
submission are downloaded; a missing result file counts as unresolved.
Ported from an exploratory script.

Usage: python -I js_ts/analyze_pb.py
"""
import sys, json, glob, os, re
import numpy as np, pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
pd.set_option('display.width', 220); pd.set_option('display.max_columns', 30); pd.set_option('display.max_rows', 200)
from pathlib import Path
R = str(Path(__file__).resolve().parent.parent / 'data' / 'raw' / 'js_ts' / 'pb')

# ---------- task metadata ----------
def patch_stats(p):
    files = len(re.findall(r'^diff --git ', p, flags=re.M))
    add = rem = 0
    for line in p.splitlines():
        if line.startswith('+++') or line.startswith('---'): continue
        if line.startswith('+'): add += 1
        elif line.startswith('-'): rem += 1
    return files, add + rem

def load_split(name):
    d = pd.read_csv(f'{R}/hf/{name}_test.csv')
    fs = d['patch'].map(patch_stats)
    d['gold_files'] = [f for f, _ in fs]; d['gold_lines'] = [l for _, l in fs]
    d['node_class'] = np.select([d.is_no_nodes, d.is_func_only, d.is_class_only, d.is_mixed],
                                ['no_nodes', 'func_only', 'class_only', 'mixed'], 'other')
    d['category'] = d.task_category
    return d

ann = pd.read_json(f'{R}/gh/annotations.jsonl', lines=True)
# 3 annotators per instance; difficulty 0..3 (0: <15 min, 1: 15 min-1 h, 2: 1-4 h, 3: >4 h)
diff = ann.groupby('instance_id').task_difficulty_choice.agg(['median', 'mean', 'count']).rename(
    columns={'median': 'diff_median', 'mean': 'diff_mean', 'count': 'n_annot'})

pbv = load_split('PBv').merge(diff, left_on='instance_id', right_index=True, how='left')
pbv['difficulty'] = pbv.diff_median.round().clip(0, 2).astype(int).map({0: '<15m', 1: '15m-1h', 2: '>=1h'})
pbv['lang'] = pbv.language.map({'JavaScript': 'JS', 'TypeScript': 'TS', 'Python': 'Py', 'Java': 'Java'})
jt = pbv[pbv.lang.isin(['JS', 'TS'])].copy()
jt['ts'] = (jt.lang == 'TS').astype(int)
# class_only has 2 TS / 0 JS tasks (perfect separation in the GLM): merge with mixed for modelling and strata
jt['node_class'] = jt.node_class.replace({'class_only': 'class_or_mixed', 'mixed': 'class_or_mixed'})
jt['cat2'] = np.where(jt.category == 'Bug Fix', 'bug', 'feature_or_refactor')
q = jt.gold_lines.quantile([.25, .5, .75]).values
jt['lines_bin'] = pd.cut(jt.gold_lines, [-1, q[0], q[1], q[2], 1e9], labels=['Q1', 'Q2', 'Q3', 'Q4'])
jt['files_bin'] = np.where(jt.gold_files <= 1, '1 file', '2+ files')
jt['log_lines'] = np.log1p(jt.gold_lines); jt['log_files'] = np.log1p(jt.gold_files)

print('== PBv JS/TS task profile')
print(jt.groupby('lang').agg(n=('instance_id', 'size'), median_lines=('gold_lines', 'median'), mean_lines=('gold_lines', 'mean'),
      median_files=('gold_files', 'median'), multi_file=('gold_files', lambda s: (s > 1).mean()),
      mean_nodes=('num_nodes', 'mean'), diff_mean=('diff_mean', 'mean')).round(2))
for c in ['category', 'node_class', 'difficulty', 'lines_bin', 'files_bin']:
    print(pd.crosstab(jt[c], jt.lang))
print('gold_lines quartile cuts', q)

# ---------- submissions ----------
SUBS = [  # (label, tier, date, path)
    ('Prometheus v1.2 + GPT-5', 'merged', '2025-11-30', 'merged/evaluation/PBVerified/20251130_prometheus_gpt-5'),
    ('Atlassian Rovo Dev', 'merged', '2025-12-08', 'merged/evaluation/PBVerified/20251208_atlassian-rovo-dev'),
    ('Kodah (gpt-5-mini)', 'merged', '2026-04-30', 'merged/evaluation/PBVerified/20260430_kodah_gpt-5-mini'),
    ('HMigBot (Claude Opus 4.8)', 'merged', '2026-06-23', 'merged/evaluation/PBVerified/20260623_migbot_claude-opus-4-8'),
    ('Mobile Coder + DeepSeek V4 Flash', 'open PR #40', '2026-09-01', 'pr40/evaluation/PBVerified/20260901_mobile-coder_deepseek-v4-flash'),
    ('Sapient Slingshot 3.4 + GPT-5.6-sol', 'open PR #44', '2026-10-06', 'pr44/evaluation/PBVerified/20261006_sapientslingshot_gpt-5.6-sol'),
    ('JamLabs Jitto Build (Opus 5.5)', 'open PR #46', '2026-10-10', 'pr46/evaluation/PBVerified/20261010_jitto-build_claude-opus-5-5'),
    ('AiWork.Code (Opus 5.5)', 'open PR #47', '2026-10-21', 'pr47/evaluation/PBVerified/20261021_aiwork-code_claude-opus-5-5'),
]
rows = []
for label, tier, date, path in SUBS:
    res = {}
    for f in glob.glob(f'{R}/{path}/logs/*_result.json'):
        j = json.load(open(f)); res[j['instance_id']] = bool(j['resolved'])
    for iid in pbv.instance_id:  # a missing result file counts as unresolved (evaluator convention)
        rows.append((label, tier, date, iid, res.get(iid, False), iid in res))
long = pd.DataFrame(rows, columns=['sub', 'tier', 'date', 'instance_id', 'resolved', 'has_result']).merge(pbv, on='instance_id')
print('\n== Overall and per-language resolved (all 382), sanity check vs claimed pass rates')
t = long.pivot_table(index=['date', 'sub', 'tier'], columns='lang', values='resolved', aggfunc='sum')
t['all'] = t.sum(axis=1); t['missing_files'] = long.groupby(['date', 'sub', 'tier']).has_result.apply(lambda s: (~s).sum())
print(t)

L = long[long.lang.isin(['JS', 'TS'])].drop(columns=['node_class']).merge(jt[['instance_id', 'ts', 'node_class', 'cat2', 'lines_bin', 'files_bin', 'log_lines', 'log_files']], on='instance_id')
L['y'] = L.resolved.astype(int)

def wilson_diff_ci(k1, n1, k2, n2):  # Newcombe hybrid score interval for p1 - p2
    from statsmodels.stats.proportion import proportion_confint
    l1, u1 = proportion_confint(k1, n1, method='wilson'); l2, u2 = proportion_confint(k2, n2, method='wilson')
    p1, p2 = k1 / n1, k2 / n2; d = p1 - p2
    return d - np.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), d + np.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)

def standardized(df, strata):
    """Direct standardization: TS and JS rates within strata, weighted by pooled JS+TS stratum share.
    Strata lacking one language are dropped (share of tasks dropped is reported)."""
    g = df.groupby(strata + ['lang'], observed=True).y.agg(['mean', 'size']).unstack('lang')
    ok = g['size'].notna().all(axis=1)
    g = g[ok]; w = g['size'].sum(axis=1); w = w / w.sum()
    ts = (g['mean']['TS'] * w).sum(); js = (g['mean']['JS'] * w).sum()
    kept = g['size'].sum().sum() / len(df)
    return ts, js, ts - js, kept

def gcomp(df, formula):
    """Logistic regression, then g-computation: average predicted P(resolve) with ts=1 minus ts=0 over the pooled mix."""
    m = smf.glm(formula, df, family=sm.families.Binomial()).fit()
    a = df.copy(); a['ts'] = 1; b = df.copy(); b['ts'] = 0
    return m.predict(a).mean() - m.predict(b).mean(), m.params['ts'], m.bse['ts']

FORM = 'y ~ ts + C(cat2) + C(node_class) + diff_mean + log_lines + log_files'
print('\n== Per submission: raw and adjusted TS minus JS (percentage points). PBv: 100 JS, 100 TS tasks.')
out = []
for (date, sub, tier), df in L.groupby(['date', 'sub', 'tier']):
    kj, kt = df[df.lang == 'JS'].y.sum(), df[df.lang == 'TS'].y.sum()
    lo, hi = wilson_diff_ci(kt, 100, kj, 100)
    r = dict(date=date, sub=sub, tier=tier, JS=kj, TS=kt, raw=(kt - kj), raw_ci=f'[{lo*100:.0f},{hi*100:.0f}]')
    for nm, st in [('std_cat', ['cat2']), ('std_nodes', ['node_class']), ('std_diff', ['difficulty']),
                   ('std_size', ['lines_bin', 'files_bin']), ('std_size_cat', ['lines_bin', 'cat2'])]:
        r[nm] = standardized(df, st)[2] * 100
    try:
        r['glm_ame'] = gcomp(df, FORM)[0] * 100
    except Exception as e:
        r['glm_ame'] = np.nan
    out.append(r)
P = pd.DataFrame(out).sort_values('date'); print(P.round(1).to_string(index=False))
adjcols = ['std_cat', 'std_nodes', 'std_diff', 'std_size', 'std_size_cat', 'glm_ame']
for tierset, nm in [(['merged'], 'merged only'), (None, 'all 8')]:
    S = P if tierset is None else P[P.tier.isin(tierset)]
    print(f'{nm}: TS>JS raw in {(S.raw > 0).sum()}/{len(S)} (ties {(S.raw == 0).sum()});',
          ' '.join(f'{c}:{(S[c] > 0).sum()}/{len(S)}' for c in adjcols))

# ---------- pooled models (submission fixed effects, SE clustered by instance) ----------
def pooled(df, label):
    m = smf.glm('y ~ ts + C(sub) + C(cat2) + C(node_class) + diff_mean + log_lines + log_files', df,
                family=sm.families.Binomial()).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(df.instance_id)[0]})
    m0 = smf.glm('y ~ ts + C(sub)', df, family=sm.families.Binomial()).fit(
        cov_type='cluster', cov_kwds={'groups': pd.factorize(df.instance_id)[0]})
    a = df.copy(); a['ts'] = 1; b = df.copy(); b['ts'] = 0
    ame = (m.predict(a) - m.predict(b)).mean()
    print(f'{label}: raw OR={np.exp(m0.params.ts):.2f} (p={m0.pvalues.ts:.3f}); adjusted OR={np.exp(m.params.ts):.2f} '
          f'[{np.exp(m.conf_int().loc["ts",0]):.2f},{np.exp(m.conf_int().loc["ts",1]):.2f}] p={m.pvalues.ts:.3f}; adjusted AME={ame*100:+.1f} pp')
    return m
print('\n== Pooled logistic, submission fixed effects, cluster-robust by instance')
pooled(L[L.tier == 'merged'], 'merged 4')
mfull = pooled(L, 'all 8')
print(mfull.summary().tables[1])

# ---------- breakdowns, pooled over submissions ----------
def brk(df, col):
    g = df.groupby([col, 'lang'], observed=True).agg(rate=('y', 'mean'), tasks=('instance_id', 'nunique')).unstack('lang')
    g[('rate', 'TS-JS')] = g[('rate', 'TS')] - g[('rate', 'JS')]
    g[('rate', 'JS')] *= 100; g[('rate', 'TS')] *= 100; g[('rate', 'TS-JS')] *= 100
    return g.round(1)
for tierset, nm in [(['merged'], 'MERGED 4'), (None, 'ALL 8')]:
    S = L if tierset is None else L[L.tier.isin(tierset)]
    print(f'\n######## Breakdowns pooled over {nm} submissions (rate = mean resolve rate over submission x task)')
    for c in ['category', 'node_class', 'difficulty', 'lines_bin', 'files_bin']:
        print(brk(S, c))
    r = S.groupby(['repo', 'lang']).agg(rate=('y', 'mean'), tasks=('instance_id', 'nunique')).round(3)
    r['rate'] *= 100; print(r)

print('\n== Per submission x repo resolve rate (%)')
print((L.pivot_table(index='repo', columns='sub', values='y', aggfunc='mean') * 100).round(0))
print('\n== Per submission x category, TS-JS (pp)')
for c in ['category', 'node_class', 'difficulty']:
    x = L.pivot_table(index=[c, 'sub'], columns='lang', values='y', aggfunc='mean')
    x['TS-JS'] = (x.TS - x.JS) * 100
    print(x['TS-JS'].unstack(c).round(0))

# ---------- leave-one-repo-out ----------
print('\n== Leave-one-repo-out: TS minus JS (pp) per submission; raw / standardized by size bins x category')
lo = []
for rep in sorted(jt.repo.unique()):
    for (date, sub, tier), df in L[L.repo != rep].groupby(['date', 'sub', 'tier']):
        raw = (df[df.lang == 'TS'].y.mean() - df[df.lang == 'JS'].y.mean()) * 100
        adj = standardized(df, ['lines_bin', 'cat2'])[2] * 100
        lo.append(dict(dropped=rep, sub=sub, tier=tier, raw=raw, adj=adj))
LO = pd.DataFrame(lo)
print(LO.pivot_table(index='sub', columns='dropped', values='raw').round(0))
print(LO.pivot_table(index='sub', columns='dropped', values='adj').round(0))
s = LO.groupby('dropped').agg(raw_mean=('raw', 'mean'), raw_TSwins=('raw', lambda v: (v > 0).sum()),
                              adj_mean=('adj', 'mean'), adj_TSwins=('adj', lambda v: (v > 0).sum()), n=('raw', 'size'))
print(s.round(1))
sm_ = LO[LO.tier == 'merged'].groupby('dropped').agg(raw_mean=('raw', 'mean'), raw_TSwins=('raw', lambda v: (v > 0).sum()),
                              adj_mean=('adj', 'mean'), adj_TSwins=('adj', lambda v: (v > 0).sum()), n=('raw', 'size'))
print('merged only'); print(sm_.round(1))
# drop mui alone: share of TS tasks
print('mui share of TS tasks:', (jt[jt.lang == 'TS'].repo == 'mui/material-ui').mean())

# ---------- sensitivity 1: drop Mobile Coder (22/23 vscode runs produced no test logs = evaluation infra failure) ----------
print('\n== Sensitivity: pooled models without Mobile Coder')
pooled(L[L['sub'] != 'Mobile Coder + DeepSeek V4 Flash'], 'all 8 minus Mobile Coder (7)')

# ---------- sensitivity 2: file-level language of the gold patch ----------
# The dataset 'language' is a repo-level label. Re-label each task by the files its gold patch edits:
# 'TSsrc' = edits at least one .ts/.tsx file that is not a .d.ts; 'JSonly' = otherwise.
def edits_ts_src(p):
    fs = re.findall(r'^diff --git a/(\S+)', p, flags=re.M)
    return any((f.endswith('.ts') or f.endswith('.tsx')) and not f.endswith('.d.ts') for f in fs)
jt['file_lang'] = np.where(jt.patch.map(edits_ts_src), 'TS', 'JS')
print('\n== Repo-level label vs gold-patch file language'); print(pd.crosstab([jt.lang, jt.repo], jt.file_lang))
L2 = L.drop(columns=['lang', 'ts']).merge(jt[['instance_id', 'file_lang']], on='instance_id').rename(columns={'file_lang': 'lang'})
L2['ts'] = (L2.lang == 'TS').astype(int)
out = []
for (date, sub, tier), df in L2.groupby(['date', 'sub', 'tier']):
    nj, nt = (df.lang == 'JS').sum(), (df.lang == 'TS').sum()
    kj, kt = df[df.lang == 'JS'].y.sum(), df[df.lang == 'TS'].y.sum()
    lo, hi = wilson_diff_ci(kt, nt, kj, nj)
    out.append(dict(date=date, sub=sub, tier=tier, JS=f'{kj}/{nj}', TS=f'{kt}/{nt}', raw=(kt / nt - kj / nj) * 100,
                    raw_ci=f'[{lo*100:.0f},{hi*100:.0f}]',
                    std_size_cat=standardized(df, ['lines_bin', 'cat2'])[2] * 100,
                    std_diff=standardized(df, ['difficulty'])[2] * 100, glm_ame=gcomp(df, FORM)[0] * 100))
P2 = pd.DataFrame(out).sort_values('date'); print(P2.round(1).to_string(index=False))
for tierset, nm in [(['merged'], 'merged only'), (None, 'all 8')]:
    S = P2 if tierset is None else P2[P2.tier.isin(tierset)]
    print(f'{nm}: TS>JS raw {(S.raw > 0).sum()}/{len(S)}; std_size_cat {(S.std_size_cat > 0).sum()}/{len(S)}; '
          f'std_diff {(S.std_diff > 0).sum()}/{len(S)}; glm {(S.glm_ame > 0).sum()}/{len(S)}')
pooled(L2[L2.tier == 'merged'], 'file-level, merged 4')
pooled(L2, 'file-level, all 8')
pooled(L2[L2['sub'] != 'Mobile Coder + DeepSeek V4 Flash'], 'file-level, all 8 minus Mobile Coder')
# within the two mixed repos: svelte (labelled JS) and mui (labelled TS) split by file language
print('\n== Within-repo split by gold-patch file language, pooled over all 8 (rate %, tasks)')
for rep in ['sveltejs/svelte', 'mui/material-ui']:
    s = L2[L2.repo == rep].groupby('lang').agg(rate=('y', 'mean'), tasks=('instance_id', 'nunique'))
    s['rate'] *= 100; print(rep); print(s.round(1))
