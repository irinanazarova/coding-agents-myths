"""Agent steps and cost per task by language, SWE-bench Multilingual February 2026 runs.

The public per-instance files record api_calls (agent steps) and cost, one attempt
per model per task. They do not record wall-clock time. Usage:
    .venv/bin/python -I scripts/steps_cost.py .
"""
import json,glob,sys
import pandas as pd, numpy as np, statsmodels.formula.api as smf
root=sys.argv[1]
t=pd.read_csv(f'{root}/results/tasks.csv')
rows=[]
for p in sorted(glob.glob(f'{root}/data/raw/experiments/202602*/per_instance_details.json')):
    m=p.split('/')[-2]
    for iid,r in json.load(open(p)).items():
        rows.append(dict(instance_id=iid,model=m,steps=r['api_calls'],cost=r['cost'],solved=int(bool(r['resolved']))))
d=pd.DataFrame(rows).merge(t,on='instance_id')
TYPED={'Rust','C','Java','C++','TypeScript','Go'}
d['dynamic']=(~d.lang.isin(TYPED)).astype(int)
d['ls']=np.log(d.steps.clip(lower=1)); d['lc']=np.log(d.cost.clip(lower=1e-4))
for c in ['lines','files','f2p','prob_len']: d['l_'+c]=np.log1p(d[c])
for y in ['ls','lc']:
  for f in [f'{y} ~ dynamic + C(model)', f'{y} ~ dynamic + C(model) + l_lines + l_files + l_f2p + l_prob_len + solved']:
    r=smf.ols(f,d).fit(cov_type='cluster',cov_kwds={'groups':d.repo})
    b=r.params['dynamic']; lo,hi=r.conf_int().loc['dynamic']
    print(f"{f[:60]:60} dynamic vs typed: {100*(np.exp(b)-1):+.0f}% ({100*(np.exp(lo)-1):+.0f} to {100*(np.exp(hi)-1):+.0f})")
# Ruby vs rest, adjusted
d['ruby']=(d.lang=='Ruby').astype(int)
r=smf.ols('ls ~ C(lang, Treatment("Java")) + C(model) + l_lines + l_files + l_f2p + l_prob_len + solved',d).fit(cov_type='cluster',cov_kwds={'groups':d.repo})
for k,v in r.params.items():
    if k.startswith('C(lang'):
        lo,hi=r.conf_int().loc[k]; print(k.split('[T.')[1][:-1], f"{100*(np.exp(v)-1):+.0f}% steps vs Java ({100*(np.exp(lo)-1):+.0f} to {100*(np.exp(hi)-1):+.0f})")
