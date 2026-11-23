# Typed Ruby: the same Rails app with and without a type checker

The cleanest test of static typing we have: one app, the same tasks, the same models, and three variants that differ only in typing.

- **App:** [Fizzy](https://github.com/basecamp/fizzy), 37signals' kanban tool (O'Saasy license).
- **Tasks:** four feature requests from the [Agents on Rails](https://github.com/rails/ai-evals) evals: `ft-card-reactions`, `ft-active-storage-tracking`, `ft-notification-bundle-window-overlap`, and `ft-board-publish-unpublish-public-boundary`.
- **Variants:** plain Ruby, inline [RBS](https://github.com/ruby/rbs) checked by Steep (rbs 4.2, Steep 2.1, rbs_rails 0.13), and [Sorbet](https://sorbet.org) with Tapioca (Sorbet 0.6, Tapioca 0.20). The app's `AGENTS.md` names the type checker; the task instruction is the same in all three.
- **Models:** GPT-6.1 Sol (xhigh), GPT-6 Luna, GLM-5.3 Flash, and DeepSeek V4.1 Flash, two attempts per task and variant, run October 25 to 28, 2026, in a 4-CPU, 4 GB sandbox.

[Vladimir Dementyev](https://evilmartians.com/martians/vladimir-dementyev) ran it for his SF Ruby Conference 2026 talk, in his own evals repository, and it's published here with his permission. Everything below is copied from that repository at commit `1887750`, except `summarize.rb` and `results/`, which we added to recompute the numbers in the blog post.

## Results

```sh
ruby summarize.rb   # Ruby 3.4+, standard library only; writes results/summary.md
```

| | Plain Ruby | RBS and Steep | Sorbet and Tapioca |
| --- | --- | --- | --- |
| Trials | 36 | 33 | 35 |
| Solved | 58% | 61% | 57% |
| Share of agent time in steps that ran type tools | none | 28% | 20% |
| Trials that ended with a clean type check | n/a | 33 of 33 | 35 of 35 |
| Agent time against plain, by model | 1× | 0.88 to 1.69× | 0.79 to 1.23× |

No type error caught a bug the tests didn't. Vladimir's full write-up, with per-task results, every class of type error the checkers reported, and the trials lost to provider outages, is [`reports/2026-10-27-rbs-sorbet.md`](reports/2026-10-27-rbs-sorbet.md).

## Definitions

- **A solve** is a trial that got the verifier's full reward.
- **Share of agent time in type tools** is the time in steps running Steep, Sorbet, or Tapioca, over all agent time in that variant. Each step is timed from launching its command to the agent's next action.
- **Agent time against plain** is, for each model, the median over the four tasks of its median agent time in the variant divided by its median in plain Ruby.
- **`hist` rows** in the CSV are older plain trials of the same tasks from the Agents on Rails runs. They're context for the write-up and aren't counted in the table.

## Layout

```
reports/
  2026-10-27-rbs-sorbet.md         Vladimir's write-up
  2026-10-28-rbs-sorbet-runs.csv   one row per trial: outcome, checks passed, time, cost, type-check statistics
  2026-10-28-rbs-sorbet-runs.md    the same data as tables, with each trial's top type errors
tasks/<task>/
  instruction.md                   what the agent was asked to do
  environment.patch                the plain Ruby starting point, applied to Fizzy
  environment+rbs.patch            the RBS variant: signatures, Steepfile, AGENTS.md
  environment+sorbet.patch.gz      the Sorbet variant, gzipped: Tapioca's generated RBIs make it 24 MB
  solution.patch                   a reference solution
  verification_test.rb             the hidden checks
  RATIONALE.md                     why the task is in the suite
docker/fizzy/Dockerfile            the sandbox image
bench.yml                          harness settings: resources, time limits, verifier command
scripts/                           the scripts that built the CSV and the tables from the trial logs
summarize.rb                       recomputes the blog post's numbers from the CSV
results/summary.md                 its output
```

## What's not here

The per-step trial logs. The source repository doesn't keep them, so `scripts/variants.rb` and `scripts/variants_report.rb`, which read them, can't be rerun from this folder; they're included to show how the CSV was built. The CSV and `summarize.rb` are enough to check every number in the post.

The task files carry the Agents on Rails canary string. Please keep them out of training data.
