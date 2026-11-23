# JavaScript vs TypeScript

Same question as the main analysis, narrowed to the cleanest pair: one
ecosystem, with static types (TypeScript) or without (JavaScript). Three
benchmarks publish per-task results for both languages.

```sh
./run_js_ts.sh --boot 4000              # creates .venv if needed
VENV=/path/to/venv ./run_js_ts.sh       # reuse an existing virtualenv
```

`js_ts/fetch_js_ts.py` downloads into `data/raw/js_ts/` (git-ignored, about
450 MB, mostly agent trajectories) and checks every file's SHA-256 against
`js_ts/sources.lock.json`. All scripts run with `python -I` and read the
downloads as data only.

| Script | Benchmark | Output |
|---|---|---|
| `analyze_js_ts.py` | SWE-bench Multilingual, 43 JS/TS tasks x 13 February 2026 runs, plus all 559 trajectories and submitted patches | `results/summary.md`, `tasks.csv`, `trajectories.csv` |
| `analyze_msb.py` | Multi-SWE-bench (ByteDance) full, mini and flash splits; experiments repo at `6a7d556`, plus unmerged PR #28 (Claude Opus 5.5) | `results/multi_swe_bench.txt` |
| `analyze_pb.py` | SWE-PolyBench Verified (Amazon), 4 merged and 4 open-PR submissions | `results/swe_polybench.txt` |
| `svelte_jsdoc.py` | One-off check on the 503 MB Multi-SWE-bench svelte task file (download command inside) | stdout |
| `labels.py` | Relabels all 823 JS/TS tasks by the files each gold patch edits, read at the task's base commit: TypeScript, type-checked JavaScript (`// @ts-check`, or `checkJs` in the nearest tsconfig/jsconfig that includes the file), or plain JavaScript. Optional, see below | `results/task_labels.csv` |
| `labels_compare.py` | TypeScript files vs plain JavaScript at the same difficulty, across repos and within Material UI, for every setup; sensitivity checks for mixed tasks, `.d.ts` edits, multi-file fixes and merged setups only; plus the memorization check on AiWork.Code's SWE-PolyBench run | `results/typed_vs_plain.txt` |

`task_notes.csv` holds hand-read notes on the hardest tasks in SWE-bench
Multilingual: what the hidden test checks beyond the issue, and how the
submitted patches failed.

Pinned sources:

- SWE-bench Multilingual: same pins as `scripts/fetch.py`; trajectories and
  logs from the public `swe-bench-submissions` S3 bucket.
- Multi-SWE-bench: `multi-swe-bench/experiments@6a7d5566f62fa76f4192302cf763051b98e4facc`
  (file list in `msb_files.txt`), PR #28 at
  `x4vierli/multi-swe-bench-experiments@1c043915c4c36d0893c4dcce892bbdc4892f7e02`.
- SWE-PolyBench: HF `AmazonScience/SWE-PolyBench_Verified@b3fca77b`,
  annotations at `amazon-science/SWE-PolyBench@9c836c5d`, submissions at the
  `submission` branch `e7062f4a` and the fork heads listed in `fetch_js_ts.py`.
  Only JS and TS result files are downloaded, so the all-language table in
  `swe_polybench.txt` shows zeros for Java and Python.

In every benchmark each repository has a single language, so language and
project are confounded. Difficulty adjustments use what each benchmark
publishes: patch size, files, failing tests and issue length (Multilingual),
human time-to-fix labels (Multi-SWE-bench, SWE-PolyBench), task category and
AST node class (SWE-PolyBench).

## Relabeling tasks by edited files

A benchmark files each task under its repository's language, which often
misses what the fix changes: most Multi-SWE-bench "JavaScript" is Svelte,
whose JSDoc types the TypeScript compiler checks, and most SWE-PolyBench
"TypeScript" is Material UI tasks that edit only `.js` files.
`results/task_labels.csv` is committed, so `labels_compare.py` runs without
any of this. To rebuild it, download the Multi-SWE-bench task files (about
1.3 GB, pinned to `ByteDance-Seed/Multi-SWE-bench@56ff018c`; `labels.py`
checks every SHA-256):

```sh
B=https://huggingface.co/datasets/ByteDance-Seed/Multi-SWE-bench/resolve/56ff018c04a38e27ada1e9d0a6d5839a51f88f0d
mkdir -p data/raw/js_ts/msb_tasks
for f in ts/mui__material-ui ts/vuejs__core ts/darkreader__darkreader js/Kong__insomnia \
         js/anuraghazra__github-readme-stats js/axios__axios js/expressjs__express js/iamkun__dayjs; do
  curl -L -o "data/raw/js_ts/msb_tasks/${f#*/}.jsonl" "$B/${f}_dataset.jsonl"
done
curl -L -o data/raw/js_ts/msb_svelte.jsonl "$B/js/sveltejs__svelte_dataset.jsonl"
LABELS=1 ./run_js_ts.sh
```

`labels.py` reads each edited file, `package.json`, and every
`tsconfig.json`/`jsconfig.json` above it at the task's base commit through
GitHub GraphQL (it needs `gh auth token`), about 14,000 files, cached in
`data/raw/js_ts/gh_cache/` so a second run is offline.

Unmerged submissions included: Multi-SWE-bench PR #28 (AiWork.Code + Claude
Opus 5.5, `x4vierli/multi-swe-bench-experiments@1c043915`) and PR #29
(CodeArts Agent + CodeArts-GLM-5.2, `cakeliang-cc/experiments@d8b79c05`);
SWE-PolyBench PRs #40, #44, #46 and #47. AiWork.Code's SWE-PolyBench
submission ships `memorization_audit.json`; its Multi-SWE-bench submission
ships no audit, logs or trajectories.
