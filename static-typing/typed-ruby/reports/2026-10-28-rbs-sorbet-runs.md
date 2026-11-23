# RBS and Sorbet variants: run data

Date: 2026-10-28. This file keeps the data of all RBS and Sorbet trials, so that the analysis can continue without `runs/`. The findings are in [2026-10-27-rbs-sorbet.md](2026-10-27-rbs-sorbet.md). The same data, with more columns, is in [2026-10-28-rbs-sorbet-runs.csv](2026-10-28-rbs-sorbet-runs.csv).

## Summary

| Variant | Trials scored | Solved (reward 1.0) | Mean credit |
|---|---|---|---|
| hist (older plain) | 48 | 29 | 0.44 |
| plain | 36 | 21 | 0.41 |
| rbs | 33 | 20 | 0.47 |
| sorbet | 35 | 20 | 0.44 |

- Types do not change the solve rate. All variants solve 57–61% of the trials.
- Types caught no real bug. The type errors are false nils, declarations missing after a migration, concern `self` types, gaps in the environment, and the agent's own slips.
- Types cost time for strong models and for deepseek with RBS. Sorbet costs weak models no extra time.
- After the worker fixes, no Steep or Tapioca process was killed.

## Per model, all four tasks

Time is the median, over tasks, of (median agent minutes of the variant) / (median agent minutes of plain).

| Model | Variant | Solved | Time vs plain | Median type min | Escape lines |
|---|---|---|---|---|---|
| sol | plain | 8/10 | 1.00 | – | – |
| sol | rbs | 6/6 | 1.25 | 4.2 | 1 |
| sol | sorbet | 7/8 | 1.23 | 5.0 | 9 |
| luna | plain | 5/10 | 1.00 | – | – |
| luna | rbs | 7/11 | 1.35 | 4.3 | 2 |
| luna | sorbet | 6/11 | 1.12 | 3.9 | 33 |
| glm | plain | 3/8 | 1.00 | – | – |
| glm | rbs | 3/8 | 0.88 | 3.8 | 6 |
| glm | sorbet | 3/8 | 0.79 | 2.3 | 16 |
| deepseek | plain | 5/8 | 1.00 | – | – |
| deepseek | rbs | 4/8 | 1.69 | 9.5 | 32 |
| deepseek | sorbet | 4/8 | 0.99 | 2.9 | 19 |

## Insights

1. **The solve rate stays the same.** No model solves clearly more tasks with types. The differences are 1–2 trials per model, which is noise at n=6–11.
2. **active-storage-tracking is the only task with a gap.** Typed trials solve it 5 times out of 18, plain trials 0 out of 9. The older plain trials solve it 2 out of 12, all by sol. The solves come from runtime check scripts and code reading, not from type errors.
3. **No type error pointed to a real bug.** The failures that cost points are logic bugs that type checks cannot see:
   - notification-bundle: notifications 5 hours apart go into one digest (deepseek in all 7 typed and older trials).
   - board-publish: images on a published card stay private for a signed-out visitor.
   - active-storage-tracking: the stored usage stays at 0 bytes (sol, 5/15), or a plain attachment recounts all blobs.
4. **Weak models with RBS lose the most time.** deepseek used 21–28 min on Steep errors in notification-bundle; its first check had 44–54 errors. It then wrote `untyped` signatures to pass the check.
5. **Sorbet is cheaper for weak models than RBS.** glm and deepseek finish Sorbet trials in the same time as plain or faster.
6. **Agents silence errors, they do not fix the design.** The usual answers are `#: as !nil`, `Current.user!`, `self #: as Model` (Sorbet concerns) and `untyped` (RBS). The escape count is highest for luna sorbet (33) and deepseek rbs (32).
7. **The RBS environment has a gap.** Steep says that `ActiveStorage::Attachment` and `ActionText::RichText` have no `record_id`, `record_type` or `account_id`. These columns exist; rbs_rails generates only app models. This gives false errors in active-storage-tracking. Sorbet does not have the gap.
8. **The checks do not show a type effect on quality.** The verifier checks behavior only. A type effect on code quality needs a different measure, such as review of the patches.

## Setup

| Item | Value |
|---|---|
| Tasks | `ft-card-reactions`, `ft-active-storage-tracking`, `ft-notification-bundle-window-overlap`, `ft-board-publish-unpublish-public-boundary` |
| Models | gpt-6.1-sol#xhigh, gpt-6-luna#max, glm-5.3-flash#max, deepseek-v4.1-flash#max (OpenRouter) |
| Agent | miniswen, from `../lemans/exe/lemans` (feat/variants) |
| Sandbox | Daytona, 4 CPUs, 4 GB memory (`bench.yml`) |
| RBS variant | `environment.rbs.patch`: rbs 4.2.0, Steep 2.1.0, rbs_rails 0.13.1, inline RBS, `TYPES.md` |
| Sorbet variant | `environment.sorbet.patch`: sorbet 0.6.13594, Tapioca 0.20.0, generated RBIs, `TYPES.md` |
| Plain | No patch. `hist` rows are older trials from `ai-evals/runs/2026-10-06-feature-tasks-revamped` |
| Attempts | 2 per model, task and variant; luna has more from earlier batches |

### Fixes and batches

The variants changed during the runs. The trial start time shows the version:

| Start (UTC, 2026-10-26) | Version | Effect |
|---|---|---|
| 16:54 | No worker limits | Steep and Tapioca start one worker per host CPU. luna card-reactions rbs `ZnOhVaj` had Steep killed (exit 137 and 124) and used 29 min on types. |
| 18:34 | Steep: 2 workers; `rbs:collection` works offline | luna as-tracking sorbet `PpVmG9H` had Tapioca killed (exit 137). |
| 19:50 and later | Tapioca: 1 worker | No type tool was killed. |

## Infrastructure failures

These trials are in the tables as `agent_error` and do not count in the aggregates.

| Cause | Trials | Status |
|---|---|---|
| OpenAI 502 (provider unavailable) | sol as-tracking plain `rOijwW5`, sorbet `OE5L7M7` | Restarted |
| OpenAI 502 | sol as-tracking rbs `4OIrm6u`, sol board-publish rbs `48IbDT8` | Not restarted |
| OpenRouter: no credits left | glm card-reactions rbs `PeqXm6A`, glm as-tracking rbs `ium1Ehf`, sol as-tracking rbs `hXRwNaP` | Restarted |

## Columns

| Column | Meaning |
|---|---|
| src | `ai-evals`: older plain trial; `here`: trial of this repo |
| min | Agent phase time, in minutes |
| steps, out k | Model calls; output tokens, in thousands |
| cost $ | Cost that the provider reports. Prices differ between the ai-evals runs and these runs, so compare cost only inside one source. |
| ann | Added lines in `app/` and `lib/` Ruby files with a type annotation (`#:`, `# @rbs`, `# @type`, `# typed:`) |
| esc | Added lines with an escape: `steep:ignore`, `untyped`, `T.untyped`, `T.unsafe`, `T.must`, `T.cast`, `T.let`, `#: as`. The count includes some valid uses, such as `Hash[Symbol, untyped]` and `T.let`. |
| tchk | Completed type checks (`steep check`, `srb tc`) |
| tfail | Type checks with errors |
| 1st err | Errors in the first completed type check |
| type min | Time in steps that run type tools. Steps that end after a gap of 30 min or more do not count. |
| clean | The last type check had no errors |
| failed | Failed checks, as IDs of the task's check list |

The CSV also has: the failure detail, the full names of failed checks, the added Ruby lines, the escape lines, edits after the last type check, killed type tools, whether the agent read `TYPES.md`, and the most frequent type errors.

## Trials

A scored trial with no checks (`passed` is `–`) broke an existing test. The verifier then gives reward 0 and runs no checks. Example: luna as-tracking plain `RxEagCM`.

### ft-card-reactions

Checks:

- C1: `a_card_takes_a_reaction_from_its_page_the_way_a_comment_does`
- C2: `a_fresh_boost_shows_on_a_preview_that_was_cached_without_it`
- C3: `only_the_person_who_reacted_can_take_it_back`
- C4: `preview_counts_do_not_cost_a_query_per_card`
- C5: `previews_show_the_boost_count,_and_nothing_when_there_are_none`
- C6: `reacting_makes_the_card_active,_and_reactions_keep_their_order`
- C7: `reactions_go_with_their_card_or_their_comment`

| model | var | src | trial | started (UTC) | outcome | reward | credit | passed | min | steps | out k | cost $ | ann | esc | tchk | tfail | 1st err | type min | clean | failed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sol | hist | ai-evals | `5tMbKAy` | 2026-10-08 05:39 | completed | 1.0 | 1.00 | 7/7 | 7.8 | 21 | 17 | 0.385 | 0 | 0 | – | – | – | – | – | – |
| sol | hist | ai-evals | `C0FSGds` | 2026-10-08 02:48 | completed | 1.0 | 1.00 | 7/7 | 10.0 | 31 | 18 | 0.493 | 0 | 0 | – | – | – | – | – | – |
| sol | hist | ai-evals | `GSX222M` | 2026-10-08 06:34 | completed | 1.0 | 1.00 | 7/7 | 19.1 | 27 | 16 | 0.420 | 0 | 0 | – | – | – | – | – | – |
| luna | hist | ai-evals | `Uz13hia` | 2026-10-08 03:31 | completed | 1.0 | 0.70 | 6/7 | 9.9 | 44 | 53 | 0.078 | 0 | 0 | – | – | – | – | – | C4 |
| luna | hist | ai-evals | `j6w8m7f` | 2026-10-08 08:06 | completed | 1.0 | 1.00 | 7/7 | 14.8 | 60 | 73 | 0.115 | 0 | 0 | – | – | – | – | – | – |
| luna | hist | ai-evals | `saBx119` | 2026-10-08 02:26 | completed | 1.0 | 1.00 | 7/7 | 13.3 | 38 | 70 | 0.093 | 0 | 0 | – | – | – | – | – | – |
| glm | hist | ai-evals | `OUTFrlH` | 2026-10-08 05:12 | completed | 1.0 | 0.70 | 6/7 | 22.5 | 133 | 51 | 0.327 | 0 | 0 | – | – | – | – | – | C4 |
| glm | hist | ai-evals | `YyX1th7` | 2026-10-08 04:00 | completed | 1.0 | 0.70 | 6/7 | 28.6 | 153 | 69 | 0.430 | 0 | 0 | – | – | – | – | – | C4 |
| glm | hist | ai-evals | `oY1IXWD` | 2026-10-08 03:51 | completed | 1.0 | 0.70 | 6/7 | 70.9 | 159 | 72 | 0.462 | 0 | 0 | – | – | – | – | – | C4 |
| deepseek | hist | ai-evals | `1XFgIa0` | 2026-10-08 03:40 | completed | 1.0 | 0.70 | 6/7 | 26.3 | 139 | 118 | 0.748 | 0 | 0 | – | – | – | – | – | C4 |
| deepseek | hist | ai-evals | `BVKkbPW` | 2026-10-08 05:33 | completed | 1.0 | 0.70 | 6/7 | 70.2 | 203 | 136 | 0.757 | 0 | 0 | – | – | – | – | – | C4 |
| deepseek | hist | ai-evals | `t6tYSP9` | 2026-10-08 02:10 | completed | 1.0 | 0.70 | 6/7 | 19.1 | 148 | 141 | 0.725 | 0 | 0 | – | – | – | – | – | C4 |
| sol | plain | here | `8jAqdCX` | 2026-10-26 20:50 | completed | 1.0 | 1.00 | 7/7 | 13.2 | 36 | 20 | 0.570 | 0 | 0 | – | – | – | – | – | – |
| sol | plain | here | `CnW7D01` | 2026-10-26 20:51 | completed | 1.0 | 0.70 | 6/7 | 10.3 | 21 | 16 | 0.408 | 0 | 0 | – | – | – | – | – | C4 |
| sol | rbs | here | `WwAr3zW` | 2026-10-26 21:56 | completed | 1.0 | 1.00 | 7/7 | 9.5 | 35 | 19 | 0.590 | 14 | 0 | 3 | 1 | 1 | 3.1 | yes | – |
| sol | rbs | here | `qEdwerf` | 2026-10-26 21:36 | completed | 1.0 | 1.00 | 7/7 | 13.5 | 33 | 21 | 0.591 | 14 | 0 | 3 | 1 | 1 | 4.5 | yes | – |
| sol | sorbet | here | `Q1bFlpU` | 2026-10-26 22:01 | completed | 1.0 | 1.00 | 7/7 | 10.2 | 31 | 20 | 0.526 | 16 | 2 | 7 | 0 | 0 | 4.9 | yes | – |
| sol | sorbet | here | `nDVFkzI` | 2026-10-26 21:53 | completed | 1.0 | 1.00 | 7/7 | 9.0 | 31 | 23 | 0.567 | 15 | 0 | 6 | 1 | 0 | 3.7 | yes | – |
| luna | plain | here | `EsW3PcY` | 2026-10-25 21:01 | completed | 1.0 | 0.70 | 6/7 | 12.0 | 46 | 62 | 0.089 | 0 | 0 | – | – | – | – | – | C4 |
| luna | plain | here | `N7OOroX` | 2026-10-26 20:50 | completed | 1.0 | 1.00 | 7/7 | 15.3 | 42 | 72 | 0.099 | 0 | 0 | – | – | – | – | – | – |
| luna | plain | here | `hCpJ71v` | 2026-10-26 20:50 | completed | 1.0 | 0.70 | 6/7 | 12.7 | 44 | 64 | 0.095 | 0 | 0 | – | – | – | – | – | C4 |
| luna | rbs | here | `L3qPiHK` | 2026-10-26 18:34 | completed | 1.0 | 0.70 | 6/7 | 15.8 | 48 | 62 | 0.090 | 7 | 0 | 3 | 1 | 1 | 2.9 | yes | C4 |
| luna | rbs | here | `ZnOhVaj` | 2026-10-26 16:54 | completed | 1.0 | 0.70 | 6/7 | 45.6 | 59 | 81 | 0.137 | 5 | 0 | 6 | 0 | 0 | 29.0 | yes | C4 |
| luna | rbs | here | `aMP4on6` | 2026-10-26 21:36 | completed | 1.0 | 1.00 | 7/7 | 13.3 | 50 | 68 | 0.105 | 11 | 0 | 3 | 0 | 0 | 3.1 | yes | – |
| luna | rbs | here | `gx7HlQo` | 2026-10-26 21:52 | completed | 1.0 | 1.00 | 7/7 | 18.7 | 67 | 92 | 0.148 | 2 | 0 | 2 | 0 | 0 | 2.7 | yes | – |
| luna | sorbet | here | `0Q7SOyQ` | 2026-10-26 18:34 | completed | 1.0 | 0.70 | 6/7 | 21.6 | 46 | 87 | 0.124 | 7 | 2 | 9 | 2 | 0 | 4.6 | yes | C4 |
| luna | sorbet | here | `RJd8WYa` | 2026-10-26 22:04 | completed | 1.0 | 1.00 | 7/7 | 14.3 | 58 | 71 | 0.113 | 2 | 0 | 5 | 1 | 4 | 2.5 | yes | – |
| luna | sorbet | here | `RovfXWk` | 2026-10-26 21:41 | completed | 1.0 | 1.00 | 7/7 | 12.3 | 49 | 66 | 0.101 | 4 | 2 | 4 | 1 | 2 | 1.6 | yes | – |
| glm | plain | here | `32gszlG` | 2026-10-26 20:46 | completed | 1.0 | 0.70 | 6/7 | 26.9 | 178 | 107 | 0.825 | 0 | 0 | – | – | – | – | – | C4 |
| glm | plain | here | `oRK6R8n` | 2026-10-26 20:46 | completed | 1.0 | 1.00 | 7/7 | 21.4 | 192 | 66 | 0.549 | 0 | 0 | – | – | – | – | – | – |
| glm | rbs | here | `Uyh6trh` | 2026-10-27 05:35 | completed | 1.0 | 0.70 | 6/7 | 15.1 | 192 | 79 | 0.706 | 1 | 0 | 3 | 0 | 0 | 1.5 | yes | C4 |
| glm | rbs | here | `hFMDVLh` | 2026-10-26 21:55 | completed | 1.0 | 0.70 | 6/7 | 22.8 | 205 | 73 | 0.622 | 0 | 0 | 4 | 0 | 0 | 3.9 | yes | C4 |
| glm | sorbet | here | `pVAgqxJ` | 2026-10-26 20:50 | completed | 1.0 | 0.70 | 6/7 | 19.0 | 127 | 57 | 0.403 | 8 | 0 | 4 | 2 | 1 | 1.4 | yes | C4 |
| glm | sorbet | here | `wAM5xPA` | 2026-10-26 22:00 | completed | 1.0 | 1.00 | 7/7 | 11.8 | 130 | 68 | 0.393 | 11 | 2 | 10 | 5 | 0 | 1.5 | yes | – |
| deepseek | plain | here | `7t26JXJ` | 2026-10-26 20:47 | completed | 1.0 | 0.70 | 6/7 | 21.0 | 186 | 144 | 0.062 | 0 | 0 | – | – | – | – | – | C4 |
| deepseek | plain | here | `SuyPJLv` | 2026-10-26 20:47 | completed | 1.0 | 0.70 | 6/7 | 13.2 | 189 | 121 | 0.048 | 0 | 0 | – | – | – | – | – | C4 |
| deepseek | rbs | here | `ApJPBY7` | 2026-10-26 22:20 | completed | 1.0 | 0.70 | 6/7 | 12.0 | 169 | 102 | 0.044 | 5 | 0 | 4 | 0 | 0 | 2.5 | yes | C4 |
| deepseek | rbs | here | `L7yxmTO` | 2026-10-26 21:12 | completed | 1.0 | 0.70 | 6/7 | 16.8 | 190 | 119 | 0.057 | 6 | 0 | 7 | 1 | 1 | 4.4 | yes | C4 |
| deepseek | sorbet | here | `MdwFEZa` | 2026-10-26 22:16 | completed | 1.0 | 0.70 | 6/7 | 11.1 | 194 | 99 | 0.046 | 14 | 1 | 13 | 2 | 2 | 1.9 | yes | C4 |
| deepseek | sorbet | here | `Nv7oCvP` | 2026-10-26 21:35 | completed | 1.0 | 0.70 | 6/7 | 16.6 | 184 | 120 | 0.058 | 14 | 0 | 7 | 2 | 5 | 1.4 | yes | C4 |

Scored trials only:

| model | var | n | solved | mean reward | mean credit | median passed | median min | median cost $ | median steps |
|---|---|---|---|---|---|---|---|---|---|
| sol | hist | 3 | 3 | 1.00 | 1.00 | 7/7 | 10.0 | 0.420 | 27 |
| sol | plain | 2 | 2 | 1.00 | 0.85 | 6/7 | 11.7 | 0.489 | 28 |
| sol | rbs | 2 | 2 | 1.00 | 1.00 | 7/7 | 11.5 | 0.591 | 34 |
| sol | sorbet | 2 | 2 | 1.00 | 1.00 | 7/7 | 9.6 | 0.546 | 31 |
| luna | hist | 3 | 3 | 1.00 | 0.90 | 7/7 | 13.3 | 0.093 | 44 |
| luna | plain | 3 | 3 | 1.00 | 0.80 | 6/7 | 12.7 | 0.095 | 44 |
| luna | rbs | 4 | 4 | 1.00 | 0.85 | 6/7 | 17.2 | 0.121 | 54 |
| luna | sorbet | 3 | 3 | 1.00 | 0.90 | 7/7 | 14.3 | 0.113 | 49 |
| glm | hist | 3 | 3 | 1.00 | 0.70 | 6/7 | 28.6 | 0.430 | 153 |
| glm | plain | 2 | 2 | 1.00 | 0.85 | 6/7 | 24.1 | 0.687 | 185 |
| glm | rbs | 2 | 2 | 1.00 | 0.70 | 6/7 | 18.9 | 0.664 | 198 |
| glm | sorbet | 2 | 2 | 1.00 | 0.85 | 6/7 | 15.4 | 0.398 | 128 |
| deepseek | hist | 3 | 3 | 1.00 | 0.70 | 6/7 | 26.3 | 0.748 | 148 |
| deepseek | plain | 2 | 2 | 1.00 | 0.70 | 6/7 | 17.1 | 0.055 | 188 |
| deepseek | rbs | 2 | 2 | 1.00 | 0.70 | 6/7 | 14.4 | 0.050 | 180 |
| deepseek | sorbet | 2 | 2 | 1.00 | 0.70 | 6/7 | 13.9 | 0.052 | 189 |
| **all** | hist | 12 | 12 | 1.00 | 0.82 | – | 19.1 | 0.425 | 96 |
| **all** | plain | 9 | 9 | 1.00 | 0.80 | – | 13.2 | 0.099 | 46 |
| **all** | rbs | 10 | 10 | 1.00 | 0.82 | – | 15.4 | 0.142 | 63 |
| **all** | sorbet | 9 | 9 | 1.00 | 0.87 | – | 12.3 | 0.124 | 58 |

Most frequent type errors per typed trial:

- sol rbs `WwAr3zW`: `Type `singleton(::ApplicationRecord)` does not have method `order` ×1`
- sol rbs `qEdwerf`: `Type `singleton(::ApplicationRecord)` does not have method `order` ×1`
- sol sorbet `nDVFkzI`: `The instance variable `@reactable` must be declared inside `initialize` or declared nilable (5005) ×1`
- luna rbs `L3qPiHK`: `Type `(::Comment | nil)` does not have method `card` ×1`
- luna sorbet `0Q7SOyQ`: `Method `reactable` does not exist on `CardsHelper` (7003) ×4`; `Unexpected RBS assertion comment found after `method` end (3553) ×1`
- luna sorbet `RJd8WYa`: `Method `account` does not exist on `NilClass` component of `T.nilable(Card)` (7003) ×1`; `Method `account` does not exist on `NilClass` component of `T.nilable(Comment)` (7003) ×1`; `Method `touch_last_active_at` does not exist on `NilClass` component of `T.nilable(Card)` (7003) ×1`; `Method `card` does not exist on `NilClass` component of `T.nilable(Comment)` (7003) ×1`
- luna sorbet `RovfXWk`: `Method `account` does not exist on `NilClass` component of `T.nilable(Comment)` (7003) ×1`; `Method `card` does not exist on `NilClass` component of `T.nilable(Comment)` (7003) ×1`
- glm sorbet `pVAgqxJ`: `Method `reactable` does not exist on `Reaction` (7003) ×5`
- glm sorbet `wAM5xPA`: `This code is unreachable (7006) ×2`; `Method `touch_last_active_at` does not exist on `Comment` component of `T.any(Comment, Card)` (7003) ×2`; `Method `card` does not exist on `Reaction` (7003) ×1`; `Used `&.` operator on `T.any(Comment, Card)`, which can never be nil (7034) ×1`
- deepseek rbs `L7yxmTO`: `Type `(::Comment | nil)` does not have method `card` ×1`
- deepseek sorbet `MdwFEZa`: `This code is unreachable (7006) ×1`; `Method `card` does not exist on `Reaction` (7003) ×1`; `Can't make method alias from `boosts` to non existing method `reactions` (5037) ×1`; `Method `card` does not exist on `NilClass` component of `T.nilable(Comment)` (7003) ×1`
- deepseek sorbet `Nv7oCvP`: `Method `reactable` does not exist on `Reaction` (7003) ×3`; `Setter method `reactable=` does not exist on `Reaction` (7003) ×2`; `Assigning a value to `value` that does not match expected type `String` (7002) ×2`

### ft-active-storage-tracking

Checks:

- C1: `a_card_created_and_destroyed_before_the_background_work_runs_settles_at_zero`
- C2: `a_card_image_counts_once_the_background_work_has_run`
- C3: `a_draft_card_counts,_and_an_edit_that_touches_no_file_changes_nothing`
- C4: `a_job_delivered_twice_does_not_count_twice`
- C5: `a_rolled-back_change_leaves_the_usage_alone`
- C6: `accounts_do_not_see_each_other's_bytes`
- C7: `an_account_and_a_board_with_nothing_stored_use_zero_bytes`
- C8: `an_ordinary_attachment_does_not_recount_every_blob_in_the_account`
- C9: `destroying_a_comment,_a_card_and_a_board_subtracts_what_each_held`
- C10: `editing,_replacing_and_removing_embedded_files_settles_on_the_current_embeds`
- C11: `images_and_embedded_files_add_up_per_board_and_across_the_account`
- C12: `loose_files,_avatars_and_exports_do_not_count`
- C13: `moving_a_card_between_boards_moves_its_bytes,_and_deleting_it_takes_them_away`
- C14: `reading_the_usage_is_a_stored_value,_not_a_calculation`
- C15: `replacing_and_removing_a_card_image_settles_on_the_current_image`

| model | var | src | trial | started (UTC) | outcome | reward | credit | passed | min | steps | out k | cost $ | ann | esc | tchk | tfail | 1st err | type min | clean | failed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sol | hist | ai-evals | `AkwcPgx` | 2026-10-08 07:24 | completed | 1.0 | 1.00 | 15/15 | 25.1 | 44 | 38 | 0.888 | 0 | 0 | – | – | – | – | – | – |
| sol | hist | ai-evals | `KV6kHsx` | 2026-10-08 07:54 | completed | 0.0 | 0.00 | 5/15 | 13.9 | 19 | 32 | 0.559 | 0 | 0 | – | – | – | – | – | C2 C3 C4 C6 C8 C9 C10 C11 C13 C15 |
| sol | hist | ai-evals | `SIusPMq` | 2026-10-08 09:05 | completed | 1.0 | 1.00 | 15/15 | 18.0 | 29 | 37 | 0.727 | 0 | 0 | – | – | – | – | – | – |
| luna | hist | ai-evals | `3VYBmH3` | 2026-10-08 02:25 | completed | 0.0 | 0.00 | 14/15 | 24.0 | 70 | 120 | 0.172 | 0 | 0 | – | – | – | – | – | C8 |
| luna | hist | ai-evals | `XU8iYNg` | 2026-10-08 07:40 | completed | 0.0 | 0.00 | 5/15 | 22.9 | 56 | 123 | 0.164 | 0 | 0 | – | – | – | – | – | C2 C3 C4 C6 C8 C9 C10 C11 C13 C15 |
| luna | hist | ai-evals | `vsTKVTH` | 2026-10-08 02:56 | completed | 0.0 | 0.00 | 14/15 | 35.6 | 113 | 158 | 0.316 | 0 | 0 | – | – | – | – | – | C8 |
| glm | hist | ai-evals | `hRO8afK` | 2026-10-08 05:53 | completed | 0.0 | 0.00 | 14/15 | 52.7 | 164 | 117 | 0.640 | 0 | 0 | – | – | – | – | – | C8 |
| glm | hist | ai-evals | `sC3FJCA` | 2026-10-08 09:34 | agent_timeout | 0.0 | 0.00 | 11/15 | 92.2 | 148 | 130 | 0.596 | 0 | 0 | – | – | – | – | – | C2 C8 C9 C14 |
| glm | hist | ai-evals | `y4NVQNJ` | 2026-10-08 09:19 | completed | 0.0 | 0.00 | 12/15 | 88.1 | 215 | 204 | 1.172 | 0 | 0 | – | – | – | – | – | C2 C8 C14 |
| deepseek | hist | ai-evals | `NNzSdLQ` | 2026-10-08 05:06 | completed | 0.0 | 0.00 | 13/15 | 53.1 | 242 | 208 | 1.751 | 0 | 0 | – | – | – | – | – | C2 C14 |
| deepseek | hist | ai-evals | `dsjUIOo` | 2026-10-08 08:29 | completed | 0.0 | 0.00 | 12/15 | 46.4 | 195 | 219 | 1.030 | 0 | 0 | – | – | – | – | – | C2 C8 C14 |
| deepseek | hist | ai-evals | `sK5BYzx` | 2026-10-08 07:45 | agent_timeout | 0.0 | 0.00 | 14/15 | 90.8 | 210 | 200 | 1.173 | 0 | 0 | – | – | – | – | – | C8 |
| sol | plain | here | `AsViDMv` | 2026-10-26 20:50 | completed | 0.0 | 0.00 | 14/15 | 15.3 | 23 | 24 | 0.462 | 0 | 0 | – | – | – | – | – | C8 |
| sol | plain | here | `y0F21wD` | 2026-10-27 05:35 | completed | 0.0 | 0.00 | 5/15 | 16.2 | 23 | 31 | 0.672 | 0 | 0 | – | – | – | – | – | C2 C3 C4 C6 C8 C9 C10 C11 C13 C15 |
| sol | rbs | here | `l4RSlmt` | 2026-10-27 05:35 | completed | 1.0 | 1.00 | 15/15 | 19.8 | 35 | 33 | 0.841 | 25 | 0 | 7 | 2 | 12 | 6.1 | yes | – |
| sol | sorbet | here | `1BpXAuf` | 2026-10-27 05:40 | completed | 1.0 | 1.00 | 15/15 | 19.1 | 38 | 37 | 0.816 | 29 | 0 | 10 | 3 | 3 | 5.1 | yes | – |
| sol | sorbet | here | `wCnEtWA` | 2026-10-26 21:38 | completed | 0.0 | 0.00 | 5/15 | 19.1 | 33 | 43 | 0.832 | 23 | 0 | 10 | 2 | 5 | 9.0 | yes | C2 C3 C4 C6 C8 C9 C10 C11 C13 C15 |
| luna | plain | here | `QsyNFz9` | 2026-10-25 21:01 | completed | 0.0 | 0.00 | 6/15 | 27.2 | 70 | 139 | 0.205 | 0 | 0 | – | – | – | – | – | C3 C4 C6 C8 C9 C10 C11 C13 C15 |
| luna | plain | here | `RxEagCM` | 2026-10-26 20:50 | completed | 0.0 | 0.00 | – | 40.0 | 114 | 173 | 0.317 | 0 | 0 | – | – | – | – | – | – |
| luna | plain | here | `x3Xd1tO` | 2026-10-26 20:49 | completed | 0.0 | 0.00 | 14/15 | 34.2 | 98 | 149 | 0.256 | 0 | 0 | – | – | – | – | – | C8 |
| luna | rbs | here | `8Ju8sYz` | 2026-10-26 18:34 | completed | 0.0 | 0.00 | 14/15 | 45.6 | 122 | 193 | 0.349 | 32 | 1 | 7 | 2 | 13 | 7.6 | yes | C8 |
| luna | rbs | here | `EAicl9y` | 2026-10-26 20:51 | completed | 0.0 | 0.00 | 13/15 | 40.6 | 89 | 154 | 0.253 | 28 | 0 | 7 | 1 | 25 | 8.8 | yes | C8 C15 |
| luna | rbs | here | `yZ5Usv0` | 2026-10-26 20:51 | completed | 1.0 | 1.00 | 15/15 | 46.6 | 116 | 182 | 0.362 | 47 | 1 | 17 | 3 | 17 | 12.6 | yes | – |
| luna | sorbet | here | `Be0qXze` | 2026-10-26 20:51 | completed | 0.0 | 0.00 | 13/15 | 43.1 | 125 | 179 | 0.358 | 29 | 5 | 11 | 2 | 4 | 6.3 | yes | C8 C15 |
| luna | sorbet | here | `PpVmG9H` | 2026-10-26 18:34 | completed | 1.0 | 1.00 | 15/15 | 50.5 | 166 | 200 | 0.454 | 67 | 9 | 16 | 3 | 19 | 8.7 | yes | – |
| luna | sorbet | here | `n4TbLBK` | 2026-10-26 16:54 | completed | 0.0 | 0.00 | 13/15 | 52.1 | 109 | 195 | 0.332 | 39 | 4 | 15 | 1 | 0 | 10.4 | yes | C8 C9 |
| luna | sorbet | here | `xhB040f` | 2026-10-26 21:04 | completed | 0.0 | 0.00 | 13/15 | 27.9 | 81 | 134 | 0.213 | 38 | 5 | 13 | 4 | 7 | 3.9 | yes | C8 C15 |
| glm | plain | here | `CLMUDEt` | 2026-10-26 20:45 | completed | 0.0 | 0.00 | 12/15 | 43.8 | 171 | 210 | 1.081 | 0 | 0 | – | – | – | – | – | C2 C8 C13 |
| glm | plain | here | `J5FGOqr` | 2026-10-26 20:46 | completed | 0.0 | 0.00 | 12/15 | 41.4 | 190 | 168 | 1.119 | 0 | 0 | – | – | – | – | – | C2 C8 C14 |
| glm | rbs | here | `6R366Oo` | 2026-10-27 05:08 | completed | 0.0 | 0.00 | 12/15 | 35.8 | 274 | 258 | 1.975 | 17 | 4 | 9 | 3 | 2 | 5.4 | yes | C8 C14 C15 |
| glm | rbs | here | `DseNrWT` | 2026-10-26 20:50 | completed | 0.0 | 0.00 | 12/15 | 40.2 | 187 | 211 | 1.232 | 39 | 0 | 8 | 2 | 0 | 6.2 | yes | C4 C13 C14 |
| glm | sorbet | here | `52VDvHl` | 2026-10-26 21:53 | completed | 0.0 | 0.00 | 13/15 | 24.2 | 216 | 174 | 1.229 | 23 | 3 | 18 | 8 | 0 | 3.5 | yes | C8 C14 |
| glm | sorbet | here | `kxuahvD` | 2026-10-26 21:31 | completed | 0.0 | 0.00 | 12/15 | 25.7 | 172 | 162 | 0.905 | 16 | 4 | 9 | 2 | 0 | 3.3 | yes | C8 C13 C14 |
| deepseek | plain | here | `ULAgC6n` | 2026-10-26 20:46 | completed | 0.0 | 0.00 | 12/15 | 25.6 | 219 | 213 | 0.091 | 0 | 0 | – | – | – | – | – | C2 C8 C14 |
| deepseek | plain | here | `oveEu6D` | 2026-10-26 20:46 | completed | 0.0 | 0.00 | 13/15 | 33.1 | 249 | 250 | 0.110 | 0 | 0 | – | – | – | – | – | C2 C8 |
| deepseek | rbs | here | `Xx1UuJf` | 2026-10-26 20:50 | completed | 0.0 | 0.00 | 12/15 | 40.7 | 284 | 225 | 0.118 | 20 | 1 | 15 | 8 | 22 | 8.9 | yes | C2 C8 C14 |
| deepseek | rbs | here | `yKutYiE` | 2026-10-26 20:50 | completed | 1.0 | 0.70 | 14/15 | 34.1 | 244 | 213 | 0.108 | 30 | 1 | 20 | 2 | 19 | 10.1 | yes | C4 |
| deepseek | sorbet | here | `Wz09nO9` | 2026-10-26 21:31 | completed | 0.0 | 0.00 | 13/15 | 18.4 | 192 | 182 | 0.076 | 38 | 3 | 28 | 8 | 10 | 3.6 | yes | C2 C8 |
| deepseek | sorbet | here | `rmfAsr3` | 2026-10-26 21:34 | completed | 0.0 | 0.00 | 13/15 | 15.3 | 139 | 115 | 0.048 | 4 | 0 | 6 | 0 | 0 | 0.9 | yes | C2 C14 |

Scored trials only:

| model | var | n | solved | mean reward | mean credit | median passed | median min | median cost $ | median steps |
|---|---|---|---|---|---|---|---|---|---|
| sol | hist | 3 | 2 | 0.67 | 0.67 | 15/15 | 18.0 | 0.727 | 29 |
| sol | plain | 2 | 0 | 0.00 | 0.00 | 10/15 | 15.8 | 0.567 | 23 |
| sol | rbs | 1 | 1 | 1.00 | 1.00 | 15/15 | 19.8 | 0.841 | 35 |
| sol | sorbet | 2 | 1 | 0.50 | 0.50 | 10/15 | 19.1 | 0.824 | 36 |
| luna | hist | 3 | 0 | 0.00 | 0.00 | 14/15 | 24.0 | 0.172 | 70 |
| luna | plain | 3 | 0 | 0.00 | 0.00 | 6/15 | 34.2 | 0.256 | 98 |
| luna | rbs | 3 | 1 | 0.33 | 0.33 | 14/15 | 45.6 | 0.349 | 116 |
| luna | sorbet | 4 | 1 | 0.25 | 0.25 | 13/15 | 46.8 | 0.345 | 117 |
| glm | hist | 3 | 0 | 0.00 | 0.00 | 12/15 | 88.1 | 0.640 | 164 |
| glm | plain | 2 | 0 | 0.00 | 0.00 | 12/15 | 42.6 | 1.100 | 180 |
| glm | rbs | 2 | 0 | 0.00 | 0.00 | 12/15 | 38.0 | 1.604 | 230 |
| glm | sorbet | 2 | 0 | 0.00 | 0.00 | 12/15 | 24.9 | 1.067 | 194 |
| deepseek | hist | 3 | 0 | 0.00 | 0.00 | 13/15 | 53.1 | 1.173 | 210 |
| deepseek | plain | 2 | 0 | 0.00 | 0.00 | 12/15 | 29.4 | 0.100 | 234 |
| deepseek | rbs | 2 | 1 | 0.50 | 0.35 | 13/15 | 37.4 | 0.113 | 264 |
| deepseek | sorbet | 2 | 0 | 0.00 | 0.00 | 13/15 | 16.8 | 0.062 | 166 |
| **all** | hist | 12 | 2 | 0.17 | 0.17 | – | 41.0 | 0.683 | 130 |
| **all** | plain | 9 | 0 | 0.00 | 0.00 | – | 33.1 | 0.317 | 114 |
| **all** | rbs | 8 | 3 | 0.38 | 0.34 | – | 40.4 | 0.355 | 154 |
| **all** | sorbet | 10 | 2 | 0.20 | 0.20 | – | 24.9 | 0.406 | 132 |

Most frequent type errors per typed trial:

- sol rbs `l4RSlmt`: `Type `::ActionText::RichText` does not have method `record_id` ×3`; `Type `::ActiveStorage::Attachment` does not have method `record_type` ×2`; `Type `::ActiveStorage::Attachment` does not have method `record_id` ×2`; `Type `::ActiveStorage::Attachment` does not have method `track_storage_later` ×2`
- sol sorbet `1BpXAuf`: `Method `name` does not exist on `NilClass` component of `T.nilable(ActiveStorage::Attachment)` (7003 ×1`; `Method `record_id` does not exist on `NilClass` component of `T.nilable(ActiveStorage::Attachment)`  ×1`; `Method `current_transaction` does not exist on `T::Class[Storage::TrackedAttachment]` (7003) ×1`; `Method `board_id` does not exist on `Storage::AttachmentUsage` (7003) ×1`
- sol sorbet `wCnEtWA`: `Expected `Integer` but found `T.any(Integer, Float, BigDecimal)` for method result type (7005) ×1`; `Method `transaction` does not exist on `T::Class[Storage::Accounting]` (7003) ×1`; `Method `lock` does not exist on `T::Class[Storage::Accounting]` (7003) ×1`; `Method `where` does not exist on `T::Class[Storage::Accounting]` (7003) ×1`
- luna rbs `8Ju8sYz`: `Type `void` does not have method `key?` ×2`; `Type `::ActiveStorage::Attachment` does not have method `refresh_storage_usage_later` ×2`; `Type `::ActiveStorage::Attachment` does not have method `record_type` ×2`; `Type `::ActiveStorage::Attachment` does not have method `refresh_storage_usage_for_rich_text` ×2`
- luna rbs `EAicl9y`: `Type `::ActiveStorage::Attachment` does not have method `record_type` ×5`; `Type `::ActiveStorage::Attachment` does not have method `record_id` ×5`; `Type `::ActiveStorage::Attachment` does not have method `storage_usage_board_id` ×4`; `Type `::ActionText::RichText` does not have method `record_type` ×3`
- luna rbs `yZ5Usv0`: `Type `::ActionText::RichText` does not have method `attachment_sgids` ×4`; `Type `::ActiveStorage::Attachment` does not have method `account_id` ×3`; `Type `::ActionText::RichText` does not have method `record_id` ×3`; `Type `::ActiveStorage::Attachment` does not have method `record_type` ×2`
- luna sorbet `Be0qXze`: `Expected `Integer` but found `T.any(Integer, Float, BigDecimal)` for method result type (7005) ×2`; `Expected `ApplicationRecord` but found `StorageUsage::Refreshable` for argument `` (7002) ×1`; `Method `where` does not exist on `T::Class[StorageUsage::Refreshable]` (7003) ×1`; `Expected `ApplicationRecord` but found `StorageUsage::Refreshable` for argument `record` (7002) ×1`
- luna sorbet `PpVmG9H`: `This code is unreachable (7006) ×8`; `The instance variable `@storage_usage_account_id` must be declared inside `initialize` or declared n ×7`; `Argument does not have asserted type `T::Array[String]` (7007) ×6`; `Expected `T::Array[String]` but found `NilClass` for field (7013) ×6`
- luna sorbet `n4TbLBK`: `Argument does not have asserted type `String` (7007) ×2`; `Argument kind mismatch for `board_id`, method declares `optional positional`, but RBS signature decl ×1`
- luna sorbet `xhB040f`: `Method `StorageUsage::Trackable#with_bytes_used_recalculation` does not take a block (7035) ×5`; `Use `T.let` to specify the type of instance variables (5013) ×4`; `The instance variable `@previous_board_id_for_bytes_used` must be declared inside `initialize` or de ×3`; `Unused type annotation. No method def before next annotation (5040) ×3`
- glm rbs `6R366Oo`: `Type `::Board` does not have method `calculated_bytes_used` ×1`; `Type `::Object` does not have method `include` ×1`; `Type `(::ActiveStorage::UsageTracking & ::ActiveStorage::Attachment)` does not have method `account` ×1`; `Type `(::ActiveStorage::UsageTracking & ::ActiveStorage::Attachment)` does not have method `record_t ×1`
- glm rbs `DseNrWT`: `Cannot pass a value of type `nil` as an argument of type `::ActiveStorage::Attachment` ×2`; `Type `::ActiveStorage::Attachment` does not have method `record_type` ×2`; `Type `::ActiveStorage::Attachment` does not have method `record_id` ×2`; `Type `nil` does not have method `counted_usage=` ×1`
- glm sorbet `52VDvHl`: `Method `counted_comment_ids` does not exist on `Board::StorageUsage` (7003) ×5`; `Unable to resolve constant `ActiveRecord_Relation` (5002) ×4`; `Expected `Integer` but found `Numeric` for method result type (7005) ×3`; `Expected `Integer` but found `T.any(Integer, Float, BigDecimal)` for method result type (7005) ×3`
- glm sorbet `kxuahvD`: `Expected `Integer` but found `T.any(Integer, Float, BigDecimal)` for method result type (7005) ×1`; `Expected `Board` but found `Board::Usage` for argument `board` (7002) ×1`
- deepseek rbs `Xx1UuJf`: `Unused inline rbs annotation ×9`; `Type `(::BytesUsed::Trackable & ::BytesUsed::Trackable::_Includer & ::ApplicationRecord)` does not h ×4`; `Type `::ActionText::RichText` does not have method `record_id` ×3`; `Type `singleton(::StorageUsage)` does not have method `sum_blob_bytes` ×2`
- deepseek rbs `yKutYiE`: `Type `::ActionText::RichText` does not have method `record_id` ×6`; `Type `::ActiveStorage::Attachment` does not have method `account_id` ×5`; `Type `::ActiveStorage::Attachment` does not have method `record_id` ×4`; `Type `::ActiveStorage::Attachment` does not have method `storage_usage_board_id` ×2`
- deepseek sorbet `Wz09nO9`: `Method `account_id` does not exist on `StorageUsage::Attachable` (7003) ×3`; `Method `blob` does not exist on `StorageUsage::Attachable` (7003) ×2`; `Method `name` does not exist on `StorageUsage::Attachable` (7003) ×2`; `Method `record_id` does not exist on `StorageUsage::Attachable` (7003) ×2`

### ft-notification-bundle-window-overlap

Checks:

- C1: `a_daily_person_and_a_four-hourly_person_are_windowed_differently`
- C2: `a_late_notification_between_two_windows_lands_in_one_of_them`
- C3: `a_notification_that_arrives_late_does_not_open_a_second_window_over_the_same_period`
- C4: `a_notification_three_hours_later_joins_the_open_four-hour_window`
- C5: `changing_the_frequency_takes_effect_on_the_notifications_that_follow_it`
- C6: `nothing_is_emailed_while_the_window_is_still_open`
- C7: `someone_with_digests_off_is_never_emailed`

| model | var | src | trial | started (UTC) | outcome | reward | credit | passed | min | steps | out k | cost $ | ann | esc | tchk | tfail | 1st err | type min | clean | failed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sol | hist | ai-evals | `OOAphhM` | 2026-10-08 03:44 | completed | 1.0 | 0.70 | 6/7 | 17.1 | 21 | 24 | 0.440 | 0 | 0 | – | – | – | – | – | C5 |
| sol | hist | ai-evals | `ROhUTDw` | 2026-10-08 06:18 | completed | 1.0 | 0.70 | 6/7 | 16.2 | 28 | 23 | 0.491 | 0 | 0 | – | – | – | – | – | C5 |
| sol | hist | ai-evals | `cEcqYFs` | 2026-10-08 04:57 | completed | 1.0 | 0.70 | 6/7 | 10.0 | 21 | 19 | 0.366 | 0 | 0 | – | – | – | – | – | C5 |
| luna | hist | ai-evals | `SUYQt1j` | 2026-10-08 02:45 | completed | 0.0 | 0.00 | 4/7 | 15.1 | 41 | 72 | 0.087 | 0 | 0 | – | – | – | – | – | C1 C2 C5 |
| luna | hist | ai-evals | `dau9iFL` | 2026-10-08 05:09 | completed | 1.0 | 0.70 | 6/7 | 15.5 | 53 | 91 | 0.121 | 0 | 0 | – | – | – | – | – | C5 |
| luna | hist | ai-evals | `gOI71WP` | 2026-10-08 02:50 | completed | 0.0 | 0.00 | 4/7 | 23.6 | 57 | 102 | 0.134 | 0 | 0 | – | – | – | – | – | C1 C2 C5 |
| glm | hist | ai-evals | `UliRTRS` | 2026-10-08 06:05 | completed | 0.0 | 0.00 | 4/7 | 38.7 | 117 | 88 | 0.366 | 0 | 0 | – | – | – | – | – | C1 C2 C5 |
| glm | hist | ai-evals | `WAHvAGZ` | 2026-10-08 05:13 | completed | 1.0 | 0.70 | 6/7 | 29.9 | 137 | 75 | 0.409 | 0 | 0 | – | – | – | – | – | C5 |
| glm | hist | ai-evals | `ciid1oo` | 2026-10-08 04:50 | completed | 1.0 | 0.70 | 6/7 | 34.9 | 111 | 87 | 0.352 | 0 | 0 | – | – | – | – | – | C5 |
| deepseek | hist | ai-evals | `bq9RYcz` | 2026-10-08 02:53 | completed | 0.0 | 0.00 | 5/7 | 51.0 | 283 | 233 | 1.681 | 0 | 0 | – | – | – | – | – | C1 C2 |
| deepseek | hist | ai-evals | `dr7cyvo` | 2026-10-08 03:22 | completed | 0.0 | 0.00 | 4/7 | 58.7 | 299 | 253 | 1.909 | 0 | 0 | – | – | – | – | – | C1 C2 C5 |
| deepseek | hist | ai-evals | `tX8mC0Z` | 2026-10-08 01:41 | completed | 0.0 | 0.00 | 4/7 | 46.4 | 277 | 252 | 1.790 | 0 | 0 | – | – | – | – | – | C1 C2 C5 |
| sol | plain | here | `E2k1txy` | 2026-10-26 19:51 | completed | 1.0 | 0.70 | 6/7 | 8.3 | 27 | 24 | 0.494 | 0 | 0 | – | – | – | – | – | C5 |
| sol | plain | here | `VIRVr5f` | 2026-10-26 19:51 | completed | 1.0 | 0.70 | 6/7 | 9.3 | 21 | 22 | 0.409 | 0 | 0 | – | – | – | – | – | C5 |
| sol | plain | here | `uh4pk4E` | 2026-10-28 06:08 | completed | 1.0 | 0.70 | 6/7 | 7.3 | 20 | 17 | 0.335 | 0 | 0 | – | – | – | – | – | C5 |
| sol | rbs | here | `9CrNujr` | 2026-10-26 20:03 | completed | 1.0 | 0.70 | 6/7 | 9.2 | 19 | 19 | 0.372 | 12 | 0 | 3 | 1 | 3 | 3.9 | yes | C5 |
| sol | rbs | here | `vV6jVfS` | 2026-10-26 20:15 | completed | 1.0 | 0.70 | 6/7 | 11.4 | 20 | 20 | 0.419 | 13 | 0 | 4 | 1 | 2 | 5.9 | yes | C5 |
| sol | sorbet | here | `3Y92Pv4` | 2026-10-26 20:29 | completed | 1.0 | 0.70 | 6/7 | 9.1 | 22 | 22 | 0.425 | 23 | 3 | 6 | 2 | 3 | 3.4 | yes | C5 |
| sol | sorbet | here | `CPFyyFO` | 2026-10-26 20:21 | completed | 1.0 | 0.70 | 6/7 | 11.6 | 23 | 23 | 0.443 | 25 | 3 | 6 | 1 | 2 | 5.0 | yes | C5 |
| luna | plain | here | `WCH5qCA` | 2026-10-26 19:51 | completed | 0.0 | 0.00 | 4/7 | 19.5 | 53 | 97 | 0.119 | 0 | 0 | – | – | – | – | – | C1 C2 C5 |
| luna | plain | here | `oPUC4cv` | 2026-10-26 19:51 | completed | 0.0 | 0.00 | 4/7 | 15.8 | 45 | 77 | 0.095 | 0 | 0 | – | – | – | – | – | C1 C2 C5 |
| luna | rbs | here | `HUsJyBG` | 2026-10-26 20:18 | completed | 0.0 | 0.00 | 4/7 | 15.4 | 47 | 75 | 0.101 | 13 | 0 | 4 | 0 | 0 | 4.3 | yes | C1 C2 C5 |
| luna | rbs | here | `OrzHFhB` | 2026-10-26 20:36 | completed | 0.0 | 0.00 | 1/7 | 35.9 | 86 | 153 | 0.251 | 28 | 0 | 8 | 2 | 1 | 7.6 | yes | C1 C2 C3 C4 C5 C6 |
| luna | sorbet | here | `XFwV6hO` | 2026-10-26 20:26 | completed | 0.0 | 0.00 | 4/7 | 19.1 | 64 | 99 | 0.146 | 25 | 3 | 10 | 2 | 18 | 4.3 | yes | C1 C2 C5 |
| luna | sorbet | here | `uGEqNmv` | 2026-10-26 20:03 | completed | 0.0 | 0.00 | 4/7 | 20.0 | 64 | 104 | 0.157 | 26 | 3 | 8 | 1 | 0 | 3.4 | yes | C1 C2 C5 |
| glm | plain | here | `1c4ISXT` | 2026-10-26 20:00 | completed | 0.0 | 0.00 | 4/7 | 26.5 | 196 | 128 | 0.846 | 0 | 0 | – | – | – | – | – | C1 C2 C5 |
| glm | plain | here | `cJPj4cQ` | 2026-10-26 20:00 | completed | 1.0 | 0.70 | 6/7 | 20.4 | 164 | 108 | 0.652 | 0 | 0 | – | – | – | – | – | C5 |
| glm | rbs | here | `43Ip3NH` | 2026-10-26 20:33 | completed | 1.0 | 0.70 | 6/7 | 26.5 | 201 | 115 | 0.880 | 26 | 0 | 7 | 1 | 2 | 3.6 | yes | C5 |
| glm | rbs | here | `iwO0oK7` | 2026-10-26 21:46 | completed | 0.0 | 0.00 | 4/7 | 14.3 | 130 | 96 | 0.463 | 14 | 0 | 3 | 0 | 0 | 1.4 | yes | C1 C2 C5 |
| glm | sorbet | here | `M9jmjuj` | 2026-10-26 20:31 | completed | 0.0 | 0.00 | 4/7 | 29.1 | 209 | 123 | 0.912 | 25 | 3 | 6 | 2 | 2 | 2.0 | yes | C1 C2 C5 |
| glm | sorbet | here | `PW3dQwv` | 2026-10-26 20:47 | completed | 1.0 | 0.70 | 6/7 | 26.0 | 145 | 116 | 0.723 | 33 | 4 | 10 | 4 | 1 | 3.5 | yes | C5 |
| deepseek | plain | here | `KOAnCGj` | 2026-10-26 19:54 | completed | 1.0 | 0.70 | 6/7 | 22.5 | 246 | 223 | 0.099 | 0 | 0 | – | – | – | – | – | C5 |
| deepseek | plain | here | `NNwvLTs` | 2026-10-26 19:54 | completed | 1.0 | 0.70 | 6/7 | 21.2 | 212 | 191 | 0.087 | 0 | 0 | – | – | – | – | – | C5 |
| deepseek | rbs | here | `AygS1fu` | 2026-10-26 20:58 | completed | 0.0 | 0.00 | 4/7 | 49.5 | 289 | 218 | 0.116 | 61 | 5 | 54 | 7 | 8 | 27.8 | yes | C1 C2 C5 |
| deepseek | rbs | here | `lYq7ZXf` | 2026-10-26 20:02 | completed | 0.0 | 0.00 | 4/7 | 42.1 | 318 | 206 | 0.127 | 73 | 22 | 44 | 5 | 1 | 20.9 | yes | C1 C2 C5 |
| deepseek | sorbet | here | `CfVa67y` | 2026-10-26 20:02 | completed | 0.0 | 0.00 | 4/7 | 26.8 | 250 | 202 | 0.090 | 80 | 3 | 47 | 7 | 8 | 9.8 | yes | C1 C2 C5 |
| deepseek | sorbet | here | `nvFJ7PW` | 2026-10-26 20:29 | completed | 0.0 | 0.00 | 4/7 | 24.4 | 286 | 201 | 0.105 | 100 | 6 | 44 | 7 | 6 | 5.8 | yes | C1 C2 C5 |

Scored trials only:

| model | var | n | solved | mean reward | mean credit | median passed | median min | median cost $ | median steps |
|---|---|---|---|---|---|---|---|---|---|
| sol | hist | 3 | 3 | 1.00 | 0.70 | 6/7 | 16.2 | 0.440 | 21 |
| sol | plain | 3 | 3 | 1.00 | 0.70 | 6/7 | 8.3 | 0.409 | 21 |
| sol | rbs | 2 | 2 | 1.00 | 0.70 | 6/7 | 10.3 | 0.396 | 20 |
| sol | sorbet | 2 | 2 | 1.00 | 0.70 | 6/7 | 10.4 | 0.434 | 22 |
| luna | hist | 3 | 1 | 0.33 | 0.23 | 4/7 | 15.5 | 0.121 | 53 |
| luna | plain | 2 | 0 | 0.00 | 0.00 | 4/7 | 17.7 | 0.107 | 49 |
| luna | rbs | 2 | 0 | 0.00 | 0.00 | 2/7 | 25.6 | 0.176 | 66 |
| luna | sorbet | 2 | 0 | 0.00 | 0.00 | 4/7 | 19.5 | 0.152 | 64 |
| glm | hist | 3 | 2 | 0.67 | 0.47 | 6/7 | 34.9 | 0.366 | 117 |
| glm | plain | 2 | 1 | 0.50 | 0.35 | 5/7 | 23.5 | 0.749 | 180 |
| glm | rbs | 2 | 1 | 0.50 | 0.35 | 5/7 | 20.4 | 0.672 | 166 |
| glm | sorbet | 2 | 1 | 0.50 | 0.35 | 5/7 | 27.6 | 0.818 | 177 |
| deepseek | hist | 3 | 0 | 0.00 | 0.00 | 4/7 | 51.0 | 1.790 | 283 |
| deepseek | plain | 2 | 2 | 1.00 | 0.70 | 6/7 | 21.8 | 0.093 | 229 |
| deepseek | rbs | 2 | 0 | 0.00 | 0.00 | 4/7 | 45.8 | 0.122 | 304 |
| deepseek | sorbet | 2 | 0 | 0.00 | 0.00 | 4/7 | 25.6 | 0.098 | 268 |
| **all** | hist | 12 | 6 | 0.50 | 0.35 | – | 26.8 | 0.388 | 84 |
| **all** | plain | 9 | 6 | 0.67 | 0.47 | – | 19.5 | 0.335 | 53 |
| **all** | rbs | 8 | 3 | 0.38 | 0.26 | – | 21.0 | 0.312 | 108 |
| **all** | sorbet | 8 | 3 | 0.38 | 0.26 | – | 22.2 | 0.291 | 104 |

Most frequent type errors per typed trial:

- sol rbs `9CrNujr`: `Type `(::User::Settings | nil)` does not have method `bundle_email_interval` ×2`; `Type `(::User::Settings | nil)` does not have method `update` ×1`
- sol rbs `vV6jVfS`: `Type `(::User::Settings | nil)` does not have method `update` ×1`; `Type `(::Identity | nil)` does not have method `email_address` ×1`
- sol sorbet `3Y92Pv4`: `Left side of `&&` condition was always `truthy` (7006) ×2`; `Expected `Notification` but found `Notification::Bundleable` for argument `notification` (7002) ×1`; `Method `update!` does not exist on `NilClass` component of `T.nilable(User::Settings)` (7003) ×1`
- sol sorbet `CPFyyFO`: `Method `update` does not exist on `NilClass` component of `T.nilable(User::Settings)` (7003) ×1`; `Expected `Notification` but found `Notification::Bundleable` for argument `notification` (7002) ×1`
- luna rbs `OrzHFhB`: `Type `::EmailDigestWindow::ActiveRecord_Associations_CollectionProxy` does not have method `open` ×3`; `Cannot allow method body have type `(::ActiveSupport::TimeZone | nil)` because declared as type `::A ×1`
- luna sorbet `XFwV6hO`: `Method `bundle_email_frequency` does not exist on `User::Settings` (7003) ×5`; `Method `account_id` does not exist on `Notification::Bundle` (7003) ×2`; `Method `user` does not exist on `Notification::Bundle` (7003) ×2`; `The instance variable `@notifications` must be declared inside `initialize` or declared nilable (500 ×2`
- luna sorbet `uGEqNmv`: `This code is unreachable (7006) ×1`
- glm rbs `43Ip3NH`: `Unexpected positional argument ×1`; `The method parameter is incompatible with the declaration `(::Notification) -> ::Notification::Bundl ×1`
- glm sorbet `M9jmjuj`: `Method `user` does not exist on `Notification::EmailBundle` (7003) ×1`; `Method `notifications` does not exist on `Notification::EmailBundle` (7003) ×1`; `Method `email_address` does not exist on `NilClass` component of `T.nilable(Identity)` (7003) ×1`
- glm sorbet `PW3dQwv`: `Unused RBS signature comment. No method definition found after it (3554) ×2`; `Expected `Notification` but found `Notification::Emailable` for argument `` (7002) ×2`; `Method `bundle_email_window_started_at` does not exist on `User::Settings` (7003) ×1`; `Method `update!` does not exist on `NilClass` component of `T.nilable(User::Settings)` (7003) ×1`
- deepseek rbs `AygS1fu`: `Type `(::ActiveSupport::TimeWithZone | nil)` does not have method `+` ×4`; `Type `(::User::Settings | nil)` does not have method `update!` ×3`; `Type `(::ActiveSupport::TimeWithZone | nil)` does not have method `<` ×2`; `Type `::Notification::Bundle` does not have method `deliver_after` ×2`
- deepseek rbs `lYq7ZXf`: `Type `(::User::Settings | nil)` does not have method `bundle_email_frequency` ×2`; `Type `::User` does not have method `notification_bundles` ×2`; `Type `(::ActiveSupport::TimeWithZone | nil)` does not have method `<=` ×2`; `Non-overloading method definition of `add` in `::Notification::Bundle` cannot be duplicated ×1`
- deepseek sorbet `CfVa67y`: `Used `&.` operator on `User`, which can never be nil (7034) ×5`; `This code is unreachable (7006) ×5`; `Method `starts_at` does not exist on `Notification::Bundle` (7003) ×3`; `Expected `T::Boolean` but found `T.nilable(T::Boolean)` for method result type (7005) ×3`
- deepseek sorbet `nvFJ7PW`: `This code is unreachable (7006) ×8`; `Left side of `&&` condition was always `truthy` (7006) ×4`; `Unable to resolve constant `PrivateCollectionProxy` (5002) ×1`; `Method `notification_bundles` does not exist on `User` (7003) ×1`

### ft-board-publish-unpublish-public-boundary

Checks:

- C1: `a_board_member_who_is_not_an_admin_can_neither_publish_nor_unpublish`
- C2: `a_card_that_was_never_published_has_no_public_page_of_its_own`
- C3: `a_column's_page_lists_its_own_cards,_not_the_whole_board`
- C4: `a_column_and_a_card_have_pages_of_their_own_under_the_public_board`
- C5: `a_picture_on_a_card_that_was_never_published_stays_private`
- C6: `a_picture_on_a_published_card_loads_for_a_signed-out_visitor`
- C7: `a_public_key_unlocks_its_own_board_and_nothing_else`
- C8: `only_published_cards_show_on_the_public_board,_in_every_column`
- C9: `publishing_gives_the_board_a_full_public_url_under_/public/boards/:key_that_a_signed-out_visitor_can_open`
- C10: `the_in-app_board_stays_behind_sign-in_after_publishing`
- C11: `the_public_key_is_not_the_board's_id,_a_number_or_its_name,_and_differs_per_board`
- C12: `unpublishing_revokes_every_public_page_at_once`

| model | var | src | trial | started (UTC) | outcome | reward | credit | passed | min | steps | out k | cost $ | ann | esc | tchk | tfail | 1st err | type min | clean | failed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sol | hist | ai-evals | `7fwmkKN` | 2026-10-08 01:18 | completed | 1.0 | 0.50 | 11/12 | 12.1 | 20 | 23 | 0.486 | 0 | 0 | – | – | – | – | – | C6 |
| sol | hist | ai-evals | `IiO61G5` | 2026-10-08 02:10 | completed | 1.0 | 0.50 | 11/12 | 11.6 | 27 | 20 | 0.488 | 0 | 0 | – | – | – | – | – | C6 |
| sol | hist | ai-evals | `UfipjVn` | 2026-10-08 02:45 | completed | 1.0 | 0.50 | 11/12 | 11.2 | 34 | 21 | 0.587 | 0 | 0 | – | – | – | – | – | C6 |
| luna | hist | ai-evals | `8m4QysX` | 2026-10-08 02:10 | completed | 1.0 | 0.50 | 11/12 | 13.2 | 39 | 70 | 0.092 | 0 | 0 | – | – | – | – | – | C6 |
| luna | hist | ai-evals | `apu1AeY` | 2026-10-08 05:00 | completed | 1.0 | 0.50 | 11/12 | 12.8 | 50 | 62 | 0.101 | 0 | 0 | – | – | – | – | – | C6 |
| luna | hist | ai-evals | `mV4cwp8` | 2026-10-08 02:41 | completed | 1.0 | 0.50 | 11/12 | 13.2 | 51 | 59 | 0.093 | 0 | 0 | – | – | – | – | – | C6 |
| glm | hist | ai-evals | `AftYRiv` | 2026-10-08 04:18 | completed | 0.0 | 0.00 | 10/12 | 36.5 | 153 | 78 | 0.488 | 0 | 0 | – | – | – | – | – | C6 C8 |
| glm | hist | ai-evals | `GUwVOi3` | 2026-10-08 09:42 | completed | 0.0 | 0.00 | 11/12 | 53.7 | 133 | 118 | 0.565 | 0 | 0 | – | – | – | – | – | C8 |
| glm | hist | ai-evals | `lQI9xYw` | 2026-10-08 09:39 | completed | 0.0 | 0.00 | 9/12 | 62.6 | 182 | 130 | 0.790 | 0 | 0 | – | – | – | – | – | C6 C8 C11 |
| deepseek | hist | ai-evals | `LDjX4X6` | 2026-10-08 07:52 | completed | 1.0 | 1.00 | 12/12 | 51.9 | 250 | 208 | 1.367 | 0 | 0 | – | – | – | – | – | – |
| deepseek | hist | ai-evals | `NvIRgjR` | 2026-10-08 11:03 | completed | 1.0 | 0.50 | 11/12 | 46.2 | 196 | 179 | 1.103 | 0 | 0 | – | – | – | – | – | C6 |
| deepseek | hist | ai-evals | `X0RGxSo` | 2026-10-08 02:10 | completed | 1.0 | 0.50 | 11/12 | 35.9 | 237 | 213 | 1.204 | 0 | 0 | – | – | – | – | – | C6 |
| sol | plain | here | `IIECBdZ` | 2026-10-28 07:20 | completed | 1.0 | 0.50 | 11/12 | 8.0 | 27 | 20 | 0.504 | 0 | 0 | – | – | – | – | – | C6 |
| sol | plain | here | `gGLJOoP` | 2026-10-26 19:50 | completed | 1.0 | 0.50 | 11/12 | 10.8 | 34 | 26 | 0.665 | 0 | 0 | – | – | – | – | – | C6 |
| sol | plain | here | `jFYubbz` | 2026-10-26 19:50 | completed | 1.0 | 0.50 | 11/12 | 7.2 | 24 | 19 | 0.470 | 0 | 0 | – | – | – | – | – | C6 |
| sol | rbs | here | `IysTWaz` | 2026-10-26 21:03 | completed | 1.0 | 1.00 | 12/12 | 11.2 | 32 | 22 | 0.602 | 18 | 1 | 3 | 0 | 0 | 3.2 | yes | – |
| sol | sorbet | here | `EZzZOV8` | 2026-10-26 20:37 | completed | 1.0 | 1.00 | 12/12 | 9.4 | 37 | 22 | 0.608 | 21 | 1 | 6 | 0 | 0 | 4.2 | yes | – |
| sol | sorbet | here | `HXCd4ki` | 2026-10-26 20:57 | completed | 1.0 | 0.50 | 11/12 | 15.6 | 26 | 21 | 0.517 | 18 | 0 | 8 | 1 | 2 | 6.4 | yes | C6 |
| luna | plain | here | `2d3IwF1` | 2026-10-26 19:49 | completed | 1.0 | 1.00 | 12/12 | 11.2 | 51 | 48 | 0.079 | 0 | 0 | – | – | – | – | – | – |
| luna | plain | here | `mYQi6yJ` | 2026-10-26 19:50 | completed | 1.0 | 0.50 | 11/12 | 11.6 | 37 | 45 | 0.064 | 0 | 0 | – | – | – | – | – | C6 |
| luna | rbs | here | `PbmXPOW` | 2026-10-26 20:42 | completed | 1.0 | 0.50 | 11/12 | 12.0 | 46 | 56 | 0.082 | 2 | 0 | 2 | 0 | 0 | 2.0 | yes | C6 |
| luna | rbs | here | `VT4ekVo` | 2026-10-26 20:03 | completed | 1.0 | 0.50 | 11/12 | 14.6 | 47 | 67 | 0.097 | 20 | 0 | 3 | 0 | 0 | 2.0 | yes | C6 |
| luna | sorbet | here | `IHryc5n` | 2026-10-26 20:48 | completed | 1.0 | 0.50 | 11/12 | 11.4 | 36 | 51 | 0.075 | 8 | 0 | 3 | 0 | 0 | 2.1 | yes | C6 |
| luna | sorbet | here | `qbOutXL` | 2026-10-26 20:03 | completed | 1.0 | 0.50 | 11/12 | 12.4 | 47 | 59 | 0.093 | 19 | 0 | 5 | 1 | 3 | 2.3 | yes | C6 |
| glm | plain | here | `EhtTl1s` | 2026-10-26 19:59 | completed | 0.0 | 0.00 | 9/12 | 22.8 | 195 | 106 | 0.841 | 0 | 0 | – | – | – | – | – | C5 C8 C11 |
| glm | plain | here | `jbsw0V1` | 2026-10-26 20:00 | completed | 0.0 | 0.00 | 10/12 | 21.6 | 194 | 106 | 0.826 | 0 | 0 | – | – | – | – | – | C5 C8 |
| glm | rbs | here | `KXmc1qw` | 2026-10-26 20:02 | completed | 0.0 | 0.00 | 11/12 | 24.2 | 160 | 83 | 0.684 | 11 | 0 | 8 | 3 | 1 | 5.7 | yes | C5 |
| glm | rbs | here | `WDEv58E` | 2026-10-26 20:02 | completed | 0.0 | 0.00 | 10/12 | 25.0 | 177 | 95 | 0.641 | 10 | 2 | 3 | 0 | 0 | 2.1 | yes | C6 C8 |
| glm | sorbet | here | `hxEcj6p` | 2026-10-26 21:16 | completed | 0.0 | 0.00 | 10/12 | 23.2 | 234 | 106 | 0.986 | 18 | 0 | 11 | 5 | 2 | 2.6 | yes | C5 C8 |
| glm | sorbet | here | `pvWTEMU` | 2026-10-26 21:02 | completed | 0.0 | 0.00 | 10/12 | 18.4 | 122 | 105 | 0.476 | 14 | 0 | 4 | 1 | 1 | 1.9 | yes | C6 C8 |
| deepseek | plain | here | `PdMEEfw` | 2026-10-26 19:53 | completed | 0.0 | 0.00 | 10/12 | 16.3 | 219 | 196 | 0.084 | 0 | 0 | – | – | – | – | – | C6 C8 |
| deepseek | plain | here | `pGwYv5h` | 2026-10-26 19:53 | completed | 1.0 | 0.50 | 11/12 | 13.8 | 253 | 143 | 0.072 | 0 | 0 | – | – | – | – | – | C6 |
| deepseek | rbs | here | `8tdxJHu` | 2026-10-26 21:46 | completed | 1.0 | 0.50 | 11/12 | 24.6 | 203 | 150 | 0.068 | 15 | 0 | 14 | 1 | 0 | 7.6 | yes | C6 |
| deepseek | rbs | here | `mmWzClh` | 2026-10-26 21:04 | completed | 0.0 | 0.00 | 10/12 | 38.8 | 229 | 183 | 0.078 | 22 | 3 | 20 | 5 | 1 | 14.4 | yes | C6 C11 |
| deepseek | sorbet | here | `0BS2atZ` | 2026-10-26 21:24 | completed | 1.0 | 0.50 | 11/12 | 19.2 | 237 | 151 | 0.069 | 24 | 5 | 20 | 2 | 4 | 2.2 | yes | C6 |
| deepseek | sorbet | here | `tBSa8Gz` | 2026-10-26 21:42 | completed | 1.0 | 0.50 | 11/12 | 18.1 | 263 | 175 | 0.084 | 24 | 1 | 23 | 2 | 4 | 4.4 | yes | C6 |

Scored trials only:

| model | var | n | solved | mean reward | mean credit | median passed | median min | median cost $ | median steps |
|---|---|---|---|---|---|---|---|---|---|
| sol | hist | 3 | 3 | 1.00 | 0.50 | 11/12 | 11.6 | 0.488 | 27 |
| sol | plain | 3 | 3 | 1.00 | 0.50 | 11/12 | 8.0 | 0.504 | 27 |
| sol | rbs | 1 | 1 | 1.00 | 1.00 | 12/12 | 11.2 | 0.602 | 32 |
| sol | sorbet | 2 | 2 | 1.00 | 0.75 | 12/12 | 12.5 | 0.563 | 32 |
| luna | hist | 3 | 3 | 1.00 | 0.50 | 11/12 | 13.2 | 0.093 | 50 |
| luna | plain | 2 | 2 | 1.00 | 0.75 | 12/12 | 11.4 | 0.071 | 44 |
| luna | rbs | 2 | 2 | 1.00 | 0.50 | 11/12 | 13.3 | 0.090 | 46 |
| luna | sorbet | 2 | 2 | 1.00 | 0.50 | 11/12 | 11.9 | 0.084 | 42 |
| glm | hist | 3 | 0 | 0.00 | 0.00 | 10/12 | 53.7 | 0.565 | 153 |
| glm | plain | 2 | 0 | 0.00 | 0.00 | 10/12 | 22.2 | 0.834 | 194 |
| glm | rbs | 2 | 0 | 0.00 | 0.00 | 10/12 | 24.6 | 0.663 | 168 |
| glm | sorbet | 2 | 0 | 0.00 | 0.00 | 10/12 | 20.8 | 0.731 | 178 |
| deepseek | hist | 3 | 3 | 1.00 | 0.67 | 11/12 | 46.2 | 1.204 | 237 |
| deepseek | plain | 2 | 1 | 0.50 | 0.25 | 10/12 | 15.0 | 0.078 | 236 |
| deepseek | rbs | 2 | 1 | 0.50 | 0.25 | 10/12 | 31.7 | 0.073 | 216 |
| deepseek | sorbet | 2 | 2 | 1.00 | 0.50 | 11/12 | 18.7 | 0.076 | 250 |
| **all** | hist | 12 | 9 | 0.75 | 0.42 | – | 24.5 | 0.526 | 92 |
| **all** | plain | 9 | 6 | 0.67 | 0.39 | – | 11.6 | 0.470 | 51 |
| **all** | rbs | 7 | 4 | 0.57 | 0.36 | – | 24.2 | 0.097 | 160 |
| **all** | sorbet | 8 | 6 | 0.75 | 0.44 | – | 16.8 | 0.285 | 84 |

Most frequent type errors per typed trial:

- sol sorbet `HXCd4ki`: `Method `published` does not exist on `T.class_of(Board)` (7003) ×1`; `Method `public_key` does not exist on `Board::Publishable` (7003) ×1`
- luna sorbet `qbOutXL`: `Method `public_key` does not exist on `Board::Publishable` (7003) ×2`; `Method `public_board_url` does not exist on `Boards::PublicationsController` (7003) ×1`
- glm rbs `KXmc1qw`: `Type `::ApplicationController` does not have method `board_key` ×2`; `Type `::ApplicationController` does not have method `two` ×1`
- glm sorbet `hxEcj6p`: `Method `record` does not exist on `Object` (7003) ×4`; `Expected `Board` but found `Board::Publishable` for method result type (7005) ×2`; `Method `attachments` does not exist on `Object` (7003) ×1`; `Method `record` does not exist on `ActionText::RichText::PubliclyAccessible` (7003) ×1`
- glm sorbet `pvWTEMU`: `Method `published` does not exist on `T.class_of(Column)` (7003) ×1`
- deepseek rbs `8tdxJHu`: `Cannot allow method body have type `(bool | nil)` because declared as type `(::Board::Publication |  ×1`
- deepseek rbs `mmWzClh`: `Type `singleton(::Board)` does not have method `find_by_public_key!` ×3`; `Type `::Board` does not have method `find_by` ×2`; `Cannot allow method body have type `(::String | nil)` because declared as type `::String` ×2`; `Cannot pass a value of type `(self | nil)` as an argument of type `(::Board | nil)` ×1`
- deepseek sorbet `0BS2atZ`: `Method `key` does not exist on `Board::Publication` (7003) ×2`; `Method `key` does not exist on `NilClass` component of `T.nilable(Board::Publication)` (7003) ×2`; `Method `publication` does not exist on `Board::Publishable` (7003) ×1`; `Method `board` does not exist on `Board::Publication` (7003) ×1`
- deepseek sorbet `tBSa8Gz`: `Method `publication` does not exist on `Board` (7003) ×1`; `Method `key` does not exist on ancestors of `Board` (7048) ×1`; `Method `url_options` does not exist on `T.class_of(Current)` (7003) ×1`; `Setter method `url_options=` does not exist on `T.class_of(Current)` (7003) ×1`
