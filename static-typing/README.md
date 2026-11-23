# Myth: static typing makes coding agents better

## The claim

Static types give a coding agent a fast feedback loop: the compiler flags a wrong method name in seconds, before any test runs. So agents should solve more tasks, faster and cheaper, in statically typed languages. Search engines' AI summaries now state this as settled.

If it held, we'd expect typed-language tasks to be solved more often at the same difficulty, and agents in dynamic languages to lose real time to errors a type checker would have caught.

## Verdict

No measurable effect. At the same task difficulty, typed and dynamic languages tie on public benchmarks, tasks that edit only TypeScript files don't beat tasks that edit only plain JavaScript, and in our Ruby vs Rust runs, type errors cost Ruby agents under 1% of their time. Not as of November 2026, at least.

## Evidence

**Public benchmarks** ([`benchmarks/`](benchmarks/)), compared at the same difficulty:

| Benchmark | Comparison | Raw | At the same difficulty |
| --- | --- | --- | --- |
| SWE-bench Multilingual, 13 models, 300 tasks | Typed vs dynamic languages | Dynamic ahead by 2.5 points | Tie: 65.5% vs 65.1%, 95% interval −7.6 to +5.8 |
| SWE-bench Multilingual | JavaScript vs TypeScript | JavaScript ahead by 16.5 | JavaScript ahead by 8.6; −0.7 without the 5 tasks no model solved |
| Multi-SWE-bench, 36 setups | JavaScript vs TypeScript | TypeScript ahead in 24 of 36 | JavaScript ahead in 28 of 36, by 2.1 points on average |
| SWE-PolyBench Verified, 8 submissions | JavaScript vs TypeScript | TypeScript ahead in 6 of 8 | TypeScript ahead in 6 of 8; leave out Material UI and JavaScript leads by 13 |

Those rows use each benchmark's repository labels, which often miss the code a fix edits: most Multi-SWE-bench "JavaScript" is Svelte, whose JSDoc types the TypeScript compiler checks, and most SWE-PolyBench "TypeScript" is Material UI tasks that edit only `.js` files. Relabeled by edited files ([`benchmarks/js_ts/labels.py`](benchmarks/js_ts/labels.py)), at the same difficulty:

| Benchmark | TypeScript files | Type-checked JavaScript | Plain JavaScript | TypeScript files minus plain JavaScript (95% interval) | TypeScript files ahead in |
| --- | --- | --- | --- | --- | --- |
| SWE-bench Multilingual, 13 models | 60.4% of 13 | 72.3% of 18 (Preact) | 62.2% of 12 | −1.9 (−21.2 to +18.8) | 5 of 13 models |
| Multi-SWE-bench, 36 merged setups | 4.6% of 79 | 4.2% of 271 (Svelte) | 8.4% of 152 | −3.8 (−6.7 to −1.0) | 3 of 36 |
| Multi-SWE-bench, Opus 5.5 and GLM-5.2 (unmerged) | 51.3%, 54.7% | 76.9%, 74.3% | 61.3%, 62.4% | −10.1 and −7.7 | 0 of 2 |
| SWE-PolyBench, 8 submissions | 48.1% of 72 | 71.9% of 4 (Prettier) | 54.2% of 110 | −6.1 (−14.5 to +2.8) | 4 of 8 |

Rates are weighted by the difficulty mix of the TypeScript-file and plain JavaScript tasks combined, so those two columns subtract to the gap (up to rounding). Counting the tasks that edit both on the TypeScript side leaves plain JavaScript ahead by 4.4 points on Multi-SWE-bench and 3.6 on SWE-PolyBench. On fixes that edit two or more code files, the two tie: +0.7 points on Multi-SWE-bench (−1.8 to +3.3) and −0.4 on SWE-PolyBench (−14.7 to +14.1).

Inside Material UI on Multi-SWE-bench, the one repository with more than five tasks on each side (28 TypeScript, 78 plain JavaScript), the two tie across 38 setups: TypeScript trails by 0.7 points (95% interval −5.5 to +4.6) and leads in 16.

**Our Ruby vs Rust runs** ([`ruby-vs-rust/`](ruby-vs-rust/)), 24 runs of two Agents on Rails tasks:

| | Quizzy, Rails | Quizzy, Rust | Campfire, Rails | Campfire, Rust |
| --- | --- | --- | --- | --- |
| Type errors (Ruby) or compiler errors (Rust), share of agent time | 0.5% | 0.8% | 0.6% | 3.2% |
| Reading project code | 14.3% | 24.2% | 33.2% | 43.6% |
| Running tests | 16.0% | 10.7% | 22.8% | 20.5% |
| Compiling and type-checking | | 11.5% | | 3.6% |
| Runs that passed every required check | 6 of 8 | 4 of 8 | 2 of 3 valid pairs | 2 of 3 valid pairs |

## What would change our mind

On SWE-PolyBench, two unmerged October 2026 runs of Claude Opus 5.5 favor TypeScript files over plain JavaScript by 10 and 13 points at the same difficulty, and by 25 once AiWork.Code's own memorization audit is applied (21 of its 29 flagged JS/TS solves are plain JavaScript). The same AiWork.Code agent and model favor plain JavaScript by 10 points on Multi-SWE-bench, and by 16.5 inside Material UI. If newer models start to pull ahead on typed code across benchmarks, the per-model splits in `benchmarks/js_ts/results/` are where it'll show first.

## Reproduce

```sh
# Public benchmarks: about 1.5 GB of downloads, Python 3.12+ and Ruby 3.4+
cd benchmarks
./run.sh --boot 4000         # nine languages, typed vs dynamic
./run_js_ts.sh --boot 4000   # JavaScript vs TypeScript, three benchmarks
ruby same_difficulty.rb      # the same-difficulty tables
cd ..

# Ruby vs Rust runs: Ruby 3.4+, no downloads
cd ruby-vs-rust && ./run.sh && cd ..

# Charts
ruby charts/charts.rb
```

## Layout

```
static-typing/
  benchmarks/     public benchmark analysis: SWE-bench Multilingual, Multi-SWE-bench, SWE-PolyBench
  ruby-vs-rust/   our 24 Agents on Rails runs, the step classifier, hand labels, and results
  charts/         the published charts and the script that draws them from the results
```

## Caveats

- **No benchmark has the same task in two languages.** Every comparison between languages is also a comparison between projects; matching on difficulty narrows that gap and doesn't close it.
- **Difficulty is measured differently per benchmark.** Multi-SWE-bench and SWE-PolyBench use human time-to-fix labels. SWE-bench Multilingual has none, so we use the size of the human fix, which explains only about a tenth of why some tasks are harder.
- **The Ruby vs Rust runs are small.** One trial per model and stack; the Rust Campfire port was written by an AI and is about 12.7 times the code, and the Rust sandbox had twice the CPU and memory.
- **Type errors that never raise aren't counted.** A silently wrong `nil` that no test catches is invisible to this method on both stacks.
