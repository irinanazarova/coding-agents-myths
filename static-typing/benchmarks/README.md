# Public benchmarks: typed vs dynamic languages, at the same difficulty

This folder reruns our analysis of three public agent benchmarks that publish per-task results: SWE-bench Multilingual, Multi-SWE-bench, and SWE-PolyBench. Run, in order:

```sh
./run.sh --boot 4000         # downloads SWE-bench Multilingual and Verified results, nine-language analysis
./run_js_ts.sh --boot 4000   # JavaScript vs TypeScript across the three benchmarks (js_ts/README.md)
ruby same_difficulty.rb      # typed vs dynamic and JS vs TS at the same mix of fix sizes
```

`same_difficulty.rb` writes `results/same_difficulty.md` and `.json`: each group's solve rate within each difficulty level, reweighted to the same mix of levels. SWE-bench Multilingual publishes no difficulty labels, so levels are terciles of the gold patch's changed lines. Multi-SWE-bench and SWE-PolyBench use their own human time-to-fix labels; those comparisons are in `js_ts/results/`.

The rest of this README documents the nine-language analysis in detail.

## SWE-bench Multilingual, split by language

## Question

Do coding agents solve more real-world bug-fix tasks in statically typed
languages than in dynamically typed ones?

SWE-bench Multilingual has 300 GitHub issues from 41 open-source repositories
in nine languages. A task counts as solved when the repository's own tests pass
after the agent's patch. The public leaderboard reports one number per model.
The per-task results are public, so this repository splits them by language.

## Short answer, typed vs dynamic

No measurable difference. Averaged over the 13 February 2026 submissions,
typed-language tasks were solved 64.6% of the time and dynamic-language tasks
67.1%. The gap, 2.5 points in favor of dynamic, has a 95% interval of roughly
minus 5 to plus 10 points under every method tried, including models that
adjust for task difficulty. The spread among typed languages is far wider than
the typed/dynamic gap: Rust 71% and Go 53%. The data cannot isolate the effect
of a type system, because each language comes from a different set of
projects and tasks.

## Python baseline, short answer

SWE-bench Multilingual has no Python by design. Python's counterpart is SWE-bench
Verified (500 tasks, 12 repos). The same 11 models were run on Verified in
February 2026 with the same agent (mini-SWE-agent, bash only, 250-step and $3
limits, identical model settings). On those runs Python scores 71.3%, against
64.4% for typed and 66.7% for dynamic Multilingual tasks. Python beats every
model's Multilingual total. The lead disappears once task difficulty is taken
into account (Python +0.6 points against expectation, typed -1.1, dynamic
-0.7). Verified's tasks were screened harder and are widely memorized, so the
Python row is a same-harness reference point. It does not test typing.

## Reproduce

```sh
./run.sh              # creates .venv, installs pinned deps, downloads, analyzes
./run.sh --boot 4000  # the setting used for the committed results
```

Requires Python 3.12 or newer and network access. `scripts/fetch.py` writes the
raw inputs to `data/raw/` (ignored by git) and checks every file's SHA-256
against `sources.lock.json`. `scripts/analyze.py` reads them as data and writes
`results/summary.md` (all tables), `results/tasks.csv` (each task's repo,
language and difficulty proxies), `results/submissions.csv` and
`results/headline.json`. Scripts run with `python -I`; the venv lives outside
the data directory.

## Data, pinned

| Source | Revision | What it gives |
|---|---|---|
| [SWE-bench/experiments](https://github.com/SWE-bench/experiments/tree/40f164d5b8f1d249bf95a6df8b74b577fd8e519d/evaluation/multilingual) `evaluation/multilingual/*/per_instance_details.json`, `metadata.yaml` | `40f164d5b8f1d249bf95a6df8b74b577fd8e519d` (main, 2026-09-03) | solved or not, per model, per task |
| [SWE-bench/SWE-bench_Multilingual](https://huggingface.co/datasets/SWE-bench/SWE-bench_Multilingual/tree/846e647b9f33c0b51b739d005d13d85493c9af09) test split | `846e647b9f33c0b51b739d005d13d85493c9af09` (2026-08-17) | task to repo, gold patch, failing tests |

The experiments repo holds 14 Multilingual submissions, all run with
mini-SWE-agent: 13 from February 2026 (agent 2.0) and Gemini 3.5 Flash from
2 September 2026 (agent 2.4.6, PR #476). That September run is the newest
per-task Multilingual data in the repo as of 2026-10-30; no other Multilingual
submission was open or merged after it. Its README says 40 tasks produced no
patch and 2 errored; 36 tasks are missing from its results file, concentrated
in Rust, TypeScript and C repos, so its per-language split is skewed. It is
kept out of the primary set and reported separately. Each submission's
recomputed total matches its official score when unreported tasks count as
unsolved, with one exception: MiniMax M2.5's file lists 203 solved tasks
(67.7%) against an official 68.3% (205). Its file lacks three three.js tasks
and holds one malformed id, `mrdoob__three`. The analysis uses the file as
published.

### Python baseline sources

| Source | Revision | What it gives |
|---|---|---|
| SWE-bench/experiments `evaluation/verified/<run>/` for the 13 runs in `scripts/pairs.json` | same commit `40f164d` | per-task results and metadata |
| [SWE-bench/SWE-bench_Verified](https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified/tree/78f471bf655a3137b2e8a75af1501690ec009ec3) | `78f471bf655a3137b2e8a75af1501690ec009ec3` (2026-08-16) | task to repo, gold patch, failing tests, annotator time estimate |
| `s3://swe-bench-submissions` (public HTTPS), `bash-only/<run>/logs/<task>/report.json` | object hashes in `sources.lock.json` | per-task results for GPT-5.2 Codex and Gemini 3 Pro on Verified |
| same bucket, one `*.traj.json` per run, both benchmarks | object hashes in `sources.lock.json` | the agent and model config each run recorded |
| GitHub raw config files of each Verified repo at its newest task's base commit | hashes in `sources.lock.json` | whether mypy is named in setup.cfg, pyproject.toml, tox.ini, mypy.ini or .pre-commit-config.yaml |

## Method

**Language of a task.** Primary: the language of its repository, read from the
files the gold patches edit (`REPO_LANG` in `scripts/analyze.py`). The SWE-bench
harness groups C with C++ and JavaScript with TypeScript; here fmt and
nlohmann/json count as C++, and babel, docusaurus and vuejs/core as
TypeScript. Sensitivity check: the method of our first, conference-talk version, the dominant
source-file extension in each task's gold patch. The two maps disagree on two
tasks (one babel task is JavaScript by patch, one prometheus task is
TypeScript by patch), and results barely move.

**Typed:** Rust, C, Java, C++, TypeScript, Go. **Dynamic:** JavaScript, PHP,
Ruby. PHP has optional type declarations and TypeScript is gradually typed;
the split follows common usage.

**Solve rate.** For each task, the share of models that solved it. A language's
rate is the mean over its tasks, which equals the average of the per-model
rates.

**Uncertainty.** Tasks cluster in 41 repositories, and tasks from one repo
tend to succeed or fail together, so the main interval resamples whole
repositories within each language (4,000 draws). A task-level bootstrap is
shown next to it. With two to four repos in a language (C, C++, TypeScript,
JavaScript, PHP) the clustered interval is unreliable; the table marks those.
A permutation test shuffles the typed/dynamic label across the 41 repos.

**Difficulty.** Three models adjust for observable task difficulty: gold-patch
lines changed, files touched, number of failing tests to fix, and issue
length. (1) A logistic GEE over every model-task attempt with cluster-robust
errors by repo. (2) A linear mixed model on task scores with a random
intercept per repo. (3) Observed minus expected solve rate per language, where
the expectation comes from a logistic model with no language term, refit in
every repo-clustered bootstrap draw. Repo fixed effects cannot be used for the
typed/dynamic question, because every repo has exactly one language and the
repo dummies absorb it.

## Results

### Primary: 13 February 2026 submissions, repo-level language map

| Language | Tasks | Repos | Solved | 95% CI, repo-clustered | 95% CI, task-level |
|---|---|---|---|---|---|
| Rust (typed) | 43 | 7 | 70.7% | 59 to 82 | 61 to 80 |
| C (typed) | 30 | 4 * | 68.7% | 63 to 82 | 57 to 80 |
| Java (typed) | 43 | 6 | 69.8% | 58 to 81 | 61 to 78 |
| C++ (typed) | 12 | 2 * | 67.3% | 64 to 100 | 46 to 87 |
| TypeScript (typed) | 15 | 3 * | 54.4% | 52 to 55 | 34 to 74 |
| Go (typed) | 42 | 5 | 52.9% | 48 to 63 | 41 to 65 |
| JavaScript (dynamic) | 28 | 4 * | 70.9% | 63 to 78 | 59 to 81 |
| PHP (dynamic) | 43 | 4 * | 69.6% | 58 to 80 | 58 to 80 |
| Ruby (dynamic) | 44 | 6 | 62.2% | 48 to 67 | 51 to 73 |
| **All typed** | 185 | 27 | **64.6%** | 60 to 69 | 60 to 69 |
| **All dynamic** | 115 | 14 | **67.1%** | 61 to 72 | 61 to 73 |
| Dynamic minus typed | | | +2.5 pts | -4.8 to +9.0 | -6.2 to +10.9 |

\* Two to four repositories; read the clustered interval as unreliable.

Dynamic minus typed under the other tests, same 13 models:

| Method | Estimate | 95% interval |
|---|---|---|
| Repo-level permutation test | +2.5 pts | p = 0.57 |
| Logistic GEE, clustered by repo | OR 1.12 | 0.79 to 1.59 |
| Logistic GEE, adjusted for difficulty proxies | OR 1.12 | 0.80 to 1.57 |
| Linear mixed model, repo random intercept | +2.5 pts | -5.9 to +10.9 |
| Linear mixed model, adjusted | +2.2 pts | -6.4 to +10.8 |
| Observed minus expected, adjusted | +2.2 pts | -3.8 to +7.7 |

Per model: 10 of 13 models solve dynamic-language tasks at least as often as
typed ones; Gemini 3 Flash, GLM 5 and MiniMax M2.5 lean typed. Go or
TypeScript is the worst language for 12 of 13 models.

After the difficulty adjustment, two languages fall clearly below
expectation: TypeScript (minus 11 points) and Go (minus 12 points). Both are
typed. Ruby sits at minus 1 point, interval minus 15 to plus 5.

### The six models from our conference talk

Opus 4.6, Opus 4.5, Gemini 3 Pro, Sonnet 4.5, GPT-5.2 (high), GPT-5.2 Codex.
With the patch-level map, every number from the talk's slide reproduces after
rounding: Rust 75.6, C 75.0, Java 70.9, C++ 63.9, TypeScript 58.9, Go 52.0,
JavaScript 81.0, PHP 71.7, Ruby 63.6, all typed 67.0, all dynamic 71.0. The gap
is +3.9 points (repo-clustered 95% interval -4.0 to +10.3). With the repo-level
map: Go 53.2, JavaScript 80.4, typed 67.2, dynamic 70.7, gap +3.5 (-4.6 to
+10.8), permutation p = 0.51. Go is the worst language for all six models
under both maps.

The six exclude Gemini 3 Flash, the top February entry at 72.7%, which leans
typed (74.6 vs 69.6). Including all 13 February models shrinks the gap from
about 4 points to about 2.5. All 14 submissions: +3.3 points (-4.0 to +10.2).

Full tables, per-model splits and the September run are in
`results/summary.md`.

## Python baseline

### Matching the runs

The 13 February Multilingual runs have 13 Verified runs of the same models on
the bash-only leaderboard, dated 2026-02-17 to 2026-02-26. The recorded config
in one trajectory per run agrees on all 13 pairs for agent class, 250-step
limit, $3 cost limit and Docker environment. The Multilingual trajectories
record mini-SWE-agent 2.0.0 and the Verified ones 2.1.0. (The metadata says
2.0.0a0 and 2.0.0.) The prompt templates are identical, except that four
Multilingual runs carry one extra sentence encouraging parallel tool calls.
The "(high)" in Verified names matches the Multilingual runs, which recorded
the same reasoning settings.

| Multilingual run | Verified run | Used | Why |
|---|---|---|---|
| claude-4-5-haiku | 20260217 claude-4-5-haiku-high | yes | same model id and settings |
| claude-4-5-opus | 20260217 claude-4-5-opus-high | yes | same |
| claude-4-5-sonnet | 20260217 claude-4-5-sonnet-high | yes | same |
| claude-4-6-opus | 20260217 claude-4-6-opus | yes | same |
| deepseek-3-2 | 20260217 deepseek-3-2-high | yes | same |
| gemini-3-flash | 20260217 gemini-3-flash-high | yes | same |
| gemini-3-pro | 20260226 gemini-3-pro-high | yes | same. The repo's per-task file marks all 500 tasks unresolved, so the bucket's evaluation reports are used: 353 solved (70.6%) against an official 69.6% |
| glm-5 | 20260217 glm-5-high | yes | same |
| gpt-5-2-high | 20260217 gpt-5-2-high | yes | same |
| gpt-5-mini | 20260217 gpt-5-mini | yes | same |
| minimax-2-5 | 20260217 minimax-2-5-high | yes | same |
| kimi-k2-5 | 20260217 kimi-k2-5-high | no | different settings: OpenRouter at temperature 0 vs Moonshot API with reasoning effort high |
| gpt-5-2-codex | 20260219 gpt-5-2-codex | no | the Verified run's trajectories record `openai/gpt-5.2-2025-12-11`, plain GPT-5.2. Its total (72.8%) equals GPT-5.2 (high) and the two agree on 456 of 500 tasks. The repo has no per-task file for it |

Gemini 3.5 Flash (Multilingual September, agent 2.4.6) has a Verified run at
2.4.2. It is left unpaired because its Multilingual run is incomplete.

### Results, 11 matched models

| Language | Tasks | Repos | Solved | 95% CI, repo-clustered | 95% CI, task-level |
|---|---|---|---|---|---|
| Rust | 43 | 7 | 70.6% | 59 to 81 | 60 to 80 |
| C | 30 | 4 * | 67.3% | 61 to 81 | 55 to 79 |
| Java | 43 | 6 | 70.0% | 62 to 80 | 62 to 78 |
| C++ | 12 | 2 * | 67.4% | 64 to 100 | 48 to 86 |
| TypeScript | 15 | 3 * | 55.2% | 53 to 56 | 35 to 75 |
| Go | 42 | 5 | 52.8% | 48 to 64 | 41 to 65 |
| JavaScript | 28 | 4 * | 70.5% | 64 to 79 | 58 to 81 |
| PHP | 43 | 4 * | 69.3% | 57 to 80 | 58 to 80 |
| Ruby | 44 | 6 | 61.8% | 47 to 67 | 51 to 73 |
| **Python (Verified)** | 500 | 12 | **71.3%** | 63 to 75 | 68 to 74 |
| **All typed** | 185 | 27 | **64.4%** | 60 to 69 | 59 to 69 |
| **All dynamic (no Python)** | 115 | 14 | **66.7%** | 61 to 72 | 60 to 73 |
| Python minus typed | | | +6.9 pts | -2.2 to +12.4 | +0.8 to +12.8 |
| Python minus dynamic | | | +4.6 pts | -5.4 to +11.5 | -2.5 to +12.3 |

**The Python interval rests on few effective clusters.** Django has 231 of
the 500 tasks and sympy 75, while seaborn has 2 and flask 1. The
repo-clustered interval is therefore too narrow and should be read as
indicative.

**Python (Verified) beats the model's Multilingual total for all 11 models,
by 1.9 to 16.5 points.** GPT-5 mini is the extreme: 56.2% on Verified against
39.7% on Multilingual.

**The difficulty proxies favor Python.** Python's median gold patch changes 7
lines; for Multilingual languages the median is 6 to 18 lines. Its median issue
text is the third shortest, after C++ and C. A logistic model fit on both benchmarks
uses model plus the four proxies (patch lines, files touched, failing tests,
issue length). Relative to its prediction, with 95% repo-clustered intervals:

| Group | Observed minus expected | 95% CI |
|---|---|---|
| Python | +0.6 pts | -2.9 to +3.0 |
| Typed | -1.1 pts | -5.1 to +3.7 |
| Dynamic | -0.7 pts | -5.8 to +4.9 |

**Python typing in Verified is optional and mostly absent where the tasks are.**
mypy is named in the config files of 9 of the 12 repos. Django, with 231 of
the 500 tasks, does not use it. The `def` lines added by gold patches carry
return annotations in xarray (15 of 21), sphinx (11 of 18) and pylint (4 of
6), and almost nowhere else: django 0 of 82, sympy 0 of 35.

### How comparable the Python baseline is

- Same: models, agent, prompt, step and cost limits, Docker evaluation, one
  attempt per task, the same month.
- Different tasks and projects. Language, project and task are as confounded
  here as between the Multilingual languages, and more so: one project
  (django) is 46% of Python's tasks.
- **Different screening.** Verified was screened by 93 Python developers, 3
  annotators per task, keeping the strictest label. The screen dropped 68% of
  candidates for underspecified issues or unfair tests and added time
  estimates. Multilingual was "manually curated" by its authors, who rejected
  vague issues, mismatched PRs and over-strict tests. It reports no annotator
  count, no inter-annotator protocol and no difficulty labels. A stricter
  screen removes impossible tasks, which raises scores.
- **Contamination.** Verified dates from 2024, and its source tasks from 2023
  and earlier. In February 2026 OpenAI reported that every frontier model it
  probed (GPT-5.2, Claude Opus 4.5, Gemini 3 Flash) could reproduce gold
  patches or issue details for some Verified tasks, and it stopped reporting
  Verified. Liang et al. ("The SWE-Bench Illusion", arXiv 2506.12286) found
  models naming the buggy file from the issue alone 76% of the time on
  Verified, against 53% elsewhere. No comparable study exists for
  Multilingual.
- **Agent version** 2.0.0 vs 2.1.0, and one prompt sentence in four pairs.

## Caveats

- **Language is confounded with project and task.** Each language comes from
  two to seven repositories with their own test suites, issue styles, build
  systems and difficulty. A gap between languages may reflect those projects.
  Nothing here can say what the same task would score in another language.
- **The difficulty proxies are weak.** Patch size, files, tests and issue
  length explain about 10% of the variation in task scores. Unmeasured
  difficulty remains.
- **Small samples.** 12 to 44 tasks per language. C++ is effectively two
  projects (one of them with a single task) and TypeScript three.
- **One agent.** Every run uses mini-SWE-agent, a minimal bash-only agent with
  no language server or type checker wired in. An agent that runs the compiler
  or type checker as a tool might behave differently.
- **Contamination.** The tasks come from public repositories and issues from
  before most models' training cutoffs; leakage could differ by repo.
- **Typed vs dynamic is a coarse label.** C's type system is weak; PHP and
  modern JavaScript projects can carry type information (PHPDoc, JSDoc).
- **Newer frontier models publish totals only.** Anthropic's system cards
  report Opus 5 at 89.5% and Opus 5.5 at 93.9% (five-trial averages), and the
  Mercor leaderboard lists entries above 95%, all under different harnesses
  and without per-task files. Per-language gaps among those systems are
  unknown and would have less room to show.

## Agent steps and cost by language

The per-instance files record agent steps (`api_calls`) and dollar cost for
each task, one attempt per model. They hold no wall-clock time, so "speed" here
means steps. `scripts/steps_cost.py` fits log steps and log cost on a
dynamic-language indicator with model fixed effects, with and without the
difficulty proxies, errors clustered by repo (`results/steps_cost.txt`).

With all 13 February runs, dynamic-language tasks took about 9% fewer steps
(95% interval −20% to +3%) and cost about 10% less (−25% to +9%) after the
difficulty adjustment. Ruby took the fewest steps of the nine languages: 13%
fewer than Java (−35% to +16%). Every interval crosses zero except the
unadjusted step gap, which only just does not.

## How many runs?

Each model attempted each task once. Run-to-run variance for a model cannot be
measured from this data. The intervals elsewhere in this README resample tasks
and repos. Across the 13 models, the solve rate on typed tasks has a standard
deviation of 9 points (range 39% to 75%) and on dynamic tasks 8 points (41% to
77%).
