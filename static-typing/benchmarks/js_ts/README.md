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
