# Ruby vs Rust: where coding agents spend their time

24 coding agent runs of two [Agents on Rails](https://github.com/rails/ai-evals) tasks, each done on Ruby on Rails and on Rust by the same model configuration:

- **Campfire** ([`ms-campfire-bots`](https://github.com/rails/ai-evals/tree/main/tasks/ms-campfire-bots)): add chat bots to [Campfire](https://github.com/basecamp/once-campfire) and to [its Rust port](https://github.com/basecamp/once-campfire-rust). Four models.
- **Quizzy** (`ms-greenfield-quizzy`): build a live quiz app from scratch, on Rails and on an empty Cargo project. Eight model configurations.

Each task is a chain of feature requests, and each request is a separate agent session. The runs date from October 2026. They were run with lemans, the harness described in [Enter LeMans](https://evilmartians.com/chronicles/the-agents-on-rails-files-enter-lemans-a-ruby-harness-for-fair-agent-races); the task design is in [Designing black-box evals](https://evilmartians.com/chronicles/the-agents-on-rails-files-designing-black-box-evals-for-coding-agents).

## Reproduce

```sh
./run.sh
```

That runs four scripts, all plain Ruby with no gems beyond the standard library:

| Script | Reads | Writes |
| --- | --- | --- |
| `analysis/find_ruby_errors.rb` | the Rails runs, `labels/ruby_error_steps.csv` | checks that the 101 steps whose output names a type-class error are exactly the labeled ones |
| `analysis/classify_steps.rb` | `runs.csv`, every `trajectory.*.json` | `results/steps.csv`: one row per agent step with its seconds and activity category |
| `analysis/summarize.rb` | `results/steps.csv` | `results/activity.csv`, `results/per_run.csv`, `results/summary.md` |
| `analysis/score_blind_check.rb` | `labels/blind_check/` | prints agreement between the rules and a blind labeler |

## Layout

```
ruby-vs-rust/
  runs.csv                     one row per run: task, model, stack, trial id, reward, minutes, cost, folder
  runs/<task>/<model>/<stack>/
    trajectory.<n>.json        every agent step in session n: the command, its output, timestamps, token use
    result.json                the run's outcome, per-session durations, usage and cost
    agent.patch, agent.<n>.patch   the code the agent left, overall and after session n
    checks*.json, verifier*.log    the hidden verifier's checks and logs
  labels/
    ruby_error_steps.csv       the 101 Ruby error steps, each labeled by hand with an excerpt
    blind_check/               60 time-weighted steps, the rules' labels, and a blind labeler's
  analysis/                    the scripts above, plus rules.rb with every classification rule
  results/                     generated tables, committed
```

Trajectories use the ATIF trajectory format: `steps[]` with `source`, `timestamp`, `tool_calls[].arguments.command`, and `observation.results[].content` holding the command's JSON output with its `returncode`.

## Method

**Time.** A step's time runs from its timestamp to the next step's: the command running, plus the agent reading the output and deciding what to do next. Gaps over 30 minutes are dropped as infrastructure stalls.

**Activities.** `analysis/rules.rb` assigns every step one category from its command, its output, and its exit code. The categories follow the taxonomy we use for all Agents on Rails runs, grouped into Understand, Build, Verify, Recover, and Plumbing, plus two Rust-only categories: `compile` (cargo build and check) and `fix_ownership` (borrow and lifetime errors). A step that writes a file and then runs tests counts as Verify. Under 2% of the time fits no category.

**Ruby type errors.** The rules flag 101 steps whose output names `NoMethodError`, `NameError`, `ArgumentError`, `TypeError`, a wrong argument count, or a failed implicit conversion. We read each one; the labels and an excerpt are in `labels/ruby_error_steps.csv`. Only 16 were type errors in code the project keeps (4 in the app, 12 in tests). The rest were throwaway scripts (55), tests written to fail before a feature existed (11), and matches for other reasons (19). Errors that never raise aren't counted.

**Rust compiler errors.** `rustc` diagnostics with an error code, like `E0308`, in the output of a `cargo` command. Borrow and lifetime errors are counted separately and included in the total. `cargo` tooling errors, like a missing `rustfmt`, don't count.

**Blind check.** 60 steps were drawn with probability proportional to their time. A separate model labeled them from the command and output alone, without seeing the rules' labels. It agreed on 63% of steps and on 75% at the group level. Most disagreements are commands that write a file and then run it, which the rules count as Verify and the labeler as Build. Read Build and Verify as accurate to several points, and the small categories as rough.

## Caveats

- **One trial per model and stack.** Success-rate differences are descriptive.
- **The stacks differ beyond types.** The Rust Campfire port was written by an AI and is about 12.7 times the code of the Rails app (about 50,800 lines against 4,000). The Rust sandbox had 4 CPUs and 8 GB, the Rails one 2 CPUs and 4 GB.
- **Gemini 3.8 Flash's Rust Campfire run has no valid result.** A baseline test the agent didn't touch failed on the old 5 GB sandbox disk. Its time data is included; its outcome isn't counted.
- **DeepSeek V4.1 Flash's Rust Quizzy run stopped after the first session**, so its time shares cover 7 minutes.
- **Agents piped `cargo` output through `tail`**, which hid most build timings, so compile time is measured as the time of `cargo build` and `cargo check` steps.
