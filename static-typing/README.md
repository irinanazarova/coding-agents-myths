# Myth: static typing makes coding agents better

## The claim

Static types give a coding agent a fast feedback loop: the compiler flags a wrong method name in seconds, before any test runs. So agents should solve more tasks, faster and cheaper, in statically typed languages. Search engines' AI summaries now state this as settled.

If it held, we'd expect typed-language tasks to be solved more often at the same difficulty, and agents in dynamic languages to lose real time to errors a type checker would have caught.

## Verdict

No measurable effect. At the same task difficulty, typed and dynamic languages tie on public benchmarks, JavaScript vs TypeScript has no consistent winner, and in our Ruby vs Rust runs, type errors cost Ruby agents under 1% of their time. Not as of November 2026, at least.

## Evidence

**Public benchmarks** ([`benchmarks/`](benchmarks/)), compared at the same difficulty:

| Benchmark | Comparison | Raw | At the same difficulty |
| --- | --- | --- | --- |
| SWE-bench Multilingual, 13 models, 300 tasks | Typed vs dynamic languages | Dynamic ahead by 2.5 points | Tie: 65.5% vs 65.1%, 95% interval −7.6 to +5.8 |
| SWE-bench Multilingual | JavaScript vs TypeScript | JavaScript ahead by 16.5 | JavaScript ahead by 8.6; −0.7 without the 5 tasks no model solved |
| Multi-SWE-bench, 36 setups | JavaScript vs TypeScript | TypeScript ahead in 24 of 36 | JavaScript ahead in 28 of 36, by 2.1 points on average |
| SWE-PolyBench Verified, 8 submissions | JavaScript vs TypeScript, by edited file | TypeScript ahead in 6 of 8 by repo label | TypeScript ahead in 4 of 8; pooled, JavaScript ahead by 5.2 (p = 0.24) |

**Our Ruby vs Rust runs** ([`ruby-vs-rust/`](ruby-vs-rust/)), 24 runs of two Agents on Rails tasks:

| | Quizzy, Rails | Quizzy, Rust | Campfire, Rails | Campfire, Rust |
| --- | --- | --- | --- | --- |
| Type errors (Ruby) or compiler errors (Rust), share of agent time | 0.5% | 0.8% | 0.6% | 3.2% |
| Reading project code | 14.3% | 24.2% | 33.2% | 43.6% |
| Running tests | 16.0% | 10.7% | 22.8% | 20.5% |
| Compiling and type-checking | | 11.5% | | 3.6% |
| Runs that passed every required check | 6 of 8 | 4 of 8 | 2 of 3 valid pairs | 2 of 3 valid pairs |

## What would change our mind

On SWE-PolyBench, two unmerged October 2026 runs of Claude Opus 5.5 favor TypeScript by 12 and 14 points at the same difficulty. The same model favors JavaScript by 15 on Multi-SWE-bench. If newer models start to pull ahead on typed code across benchmarks, the per-model splits in `benchmarks/js_ts/results/` are where it'll show first.

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
