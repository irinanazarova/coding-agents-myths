# RBS and Sorbet variants: results

Date: 2026-10-27. Trials: `runs/` (2026-10-26, restarts on 2026-10-27), with older plain runs from
`ai-evals/runs/2026-10-06-feature-tasks-revamped` for comparison.
The data of all trials is in [2026-10-28-rbs-sorbet-runs.md](2026-10-28-rbs-sorbet-runs.md).

## Highlights

- Types do not help agents on these tasks. They caught no real bug, and typed trials score the same as plain trials.
- Types cost time, most for weak models with RBS: deepseek spends 21–28 min on Steep errors on one task.
- The agents find the type tools without help. `AGENTS.md` is enough; the instruction does not need a hint.

Hypotheses from the discussions (2026-10-26 to 2026-10-28):

| Date | Hypothesis | Verdict | Evidence |
|---|---|---|---|
| 10-26 | The variants need no extra instruction; `AGENTS.md` is enough. | Confirmed | Agents read `AGENTS.md` unasked in 93% of 2,160 older `ft-*` trials, usually as the second command. Every typed trial on notification-bundle and board-publish ended with a clean type check. |
| 10-26 | Tasks with much app and lib Ruby (notification-bundle, board-publish) gain the most from types. | Not confirmed | No type error was a real bug. The deepseek window bug and the luna design failure are invisible to types. |
| 10-26 | card-reactions and active-storage-tracking show a difference on more models. | Not shown | card-reactions has no headroom: every scored trial gets reward 1.0. active-storage-tracking: typed 5 solves, plain 0, with n = 8–10 per variant. Too few trials to show a cause. |

## Summary

- Types caught no real bug in any trial.
- Typed trials score the same as plain trials, or slightly better. The better scores come from runtime checks and code reading, not from types.
- Types cost time. Strong models (sol, luna) lose 0–2 min on easy tasks and about 12 min on active-storage-tracking. Weak models (glm, deepseek) lose up to 25 min with RBS.
- Sorbet costs weak models less time than RBS.
- The worker limits for Steep and Tapioca work. No type tool was killed after the fixes.

## Setup

- Tasks: `ft-card-reactions`, `ft-active-storage-tracking`, `ft-notification-bundle-window-overlap`, `ft-board-publish-unpublish-public-boundary`.
- Variants: `plain`, `#rbs` (RBS inline + Steep), `#sorbet` (Sorbet + Tapioca).
- Models: gpt-6.1-sol-xhigh, gpt-6-luna-max, glm-5.3-flash-max, deepseek-v4.1-flash-max.
- Attempts: 2 per model, task and variant. The Daytona sandbox has 4 CPUs and 4 GB of memory (`bench.yml`).

## Results

Cells show the passed checks per trial and the median agent time. `err` is an infrastructure error (see [Lost trials](#lost-trials)). Restarted trials replace their failed runs.

### notification-bundle-window-overlap (7 checks)

| Model | Plain | RBS | Sorbet |
|---|---|---|---|
| sol | 6, 6 · 9 min | 6, 6 · 10 min | 6, 6 · 10 min |
| luna | 4, 4 · 18 min | 4, 1 · 26 min | 4, 4 · 20 min |
| glm | 4, 6 · 23 min | 6, 4 · 20 min | 4, 6 · 28 min |
| deepseek | 6, 6 · 22 min | 4, 4 · 46 min | 4, 4 · 26 min |

- deepseek failed all 4 typed trials. The cause is a window logic bug: two notifications 5 hours apart go into one digest. All 3 older plain trials have the same bug. Types cannot find it.
- deepseek used 21–28 min on RBS errors. Its first `steep check` gave 44–54 errors. It added `untyped` signatures to make the check pass.
- luna RBS got 1/7 because it built a new `EmailDigestWindow` model and did not use `Notification::Bundle`. This is a design choice, not a type effect.

### board-publish-unpublish-public-boundary (12 checks)

| Model | Plain | RBS | Sorbet |
|---|---|---|---|
| sol | 11, 11 · 9 min | err, 12 · 11 min | 12, 11 · 12 min |
| luna | 12, 11 · 11 min | 11, 11 · 13 min | 11, 11 · 12 min |
| glm | 9, 10 · 22 min | 11, 10 · 25 min | 10, 10 · 21 min |
| deepseek | 10, 11 · 15 min | 11, 10 · 32 min | 11, 11 · 19 min |

- sol got 12/12 in 2 typed trials. All 5 of its plain trials got 11/12. In both 12/12 trials, sol found `Card::Accessible` by reading the code and edited it, which fixed the image check. Type tools played no part.

### card-reactions (7 checks)

| Model | Plain | RBS | Sorbet |
|---|---|---|---|
| sol | 7, 6 · 12 min | 7, 7 · 11 min | 7, 7 · 10 min |
| luna | 6, 7, 6 · 13 min | 6, 6, 7, 7 · 17 min | 6, 7, 7 · 14 min |
| glm | 6, 7 · 24 min | 6, 6 · 19 min | 6, 7 · 15 min |
| deepseek | 6, 6 · 17 min | 6, 6 · 14 min | 6, 6 · 14 min |

- All scored trials get reward 1.0. The task has no headroom.
- Types add no time.
- The luna RBS column includes 2 trials from before the Steep fix.

### active-storage-tracking (15 checks)

| Model | Plain | RBS | Sorbet |
|---|---|---|---|
| sol | 14, 5 · 16 min | **15**, err · 20 min | **15**, 5 · 19 min |
| luna | 6, 0\*, 14 · 34 min | 14, 13, **15** · 46 min | 13, **15**, 13, 13 · 47 min |
| glm | 12, 12 · 43 min | 12, 12 · 38 min | 13, 12 · 25 min |
| deepseek | 12, 13 · 29 min | 12, **14** · 37 min | 13, 13 · 17 min |

\* The agent broke an existing test, so the verifier gave no checks.

- Mean reward: plain 0.00 (n=9), RBS 0.38 (n=8), Sorbet 0.20 (n=10). Typed trials solve the task 5 times, plain trials 0 times. The samples are too small to show a cause.
- sol solved it in 2 of 3 typed trials and in 0 of 2 plain trials. Its older plain trials solved it 2 of 3 times, so sol solves it often without types.
- sol got 5/15 once in plain and once in Sorbet: the usage stays at 0 bytes. One older plain trial has the same result. This is a design failure, not a type effect.
- deepseek RBS solved the task once (14/15, reward 1.0). No earlier deepseek trial solved it. Its type errors were all false (see [RBS gap](#rbs-gap-in-gem-models)).
- luna solved it in 2 of 7 typed trials and in 0 of 6 plain trials. The solves come from runtime check scripts, not from types.
- luna typed trials are slower: 46–47 min against 34 min.

## What the type checks found

| Error class | Example | Real bug? |
|---|---|---|
| Impossible nil | `(::User::Settings \| nil)` has no `update` | No |
| Missing declaration after a migration or concern | `bundle_email_frequency` does not exist on `User::Settings` | No |
| Concern `self` type (Sorbet) | Expected `Notification`, found `Notification::Bundleable` | No |
| The agent's own slip | Wrong arity, a method declared twice, unreachable code | No, the check found it before the tests did |
| Gaps in the environment | `ActiveStorage::Attachment` has no `record_id` | No, a false error |

Agents fix nil errors with `#: as !nil` and `Current.user!`. They fix concern errors with `self #: as Model`.

## RBS gap in gem models

Steep reports that `ActiveStorage::Attachment` and `ActionText::RichText` have no `record_id`, `record_type` or `account_id`. These columns exist. rbs_rails generates signatures only for app models.

- Effect: glm and deepseek lost time on active-storage-tracking and added `untyped` to stop the errors.
- Fix: generate rbs_rails signatures for `ActiveStorage::Attachment`, `ActiveStorage::Blob` and `ActionText::RichText` in all RBS patches.
- Sorbet does not have this gap: the Tapioca DSL compilers cover these models.

## Lost trials

| Cause | Time (UTC, 2026-10-26) | Trials | Status |
|---|---|---|---|
| OpenAI 502 | 20:50–21:00 | sol as-tracking plain, Sorbet | Restarted |
| OpenAI 502 | 20:51 | sol as-tracking RBS (`4OIrm6u`) | Not restarted |
| OpenAI 502 | — | sol board-publish RBS (`48IbDT8`) | Not restarted |
| OpenRouter: no credits left | 21:54–22:21 | glm card-reactions RBS, glm as-tracking RBS, sol as-tracking RBS | Restarted |

The analysis ignores the failed runs of restarted trials.

## Fixes in the variants

- `bin/steep` uses 2 workers. Steep otherwise starts one worker for each host CPU and runs out of memory.
- `sorbet/tapioca/config.yml` sets `workers: 1` for `gem` and `dsl`, for the same reason.
- `rbs:collection` keeps the installed `.gem_rbs_collection` when it has no network access.

## Best variant for top models

No `#sorbet` trial of Opus 5.5 or Astra (both medium) is run yet (2026-11-05). Sorbet is the better of the two type
variants: it costs weak models less time than RBS. One trial per model is planned, because the trials are slow and
expensive.

## Next steps

1. Fix the RBS gap in gem models.
2. Restart the 2 sol RBS trials that are still lost.
3. To reduce the RBS time cost for weak models, try shorter type guidance in `TYPES.md`.
