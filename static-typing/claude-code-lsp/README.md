# Claude Code with a TypeScript language server

The public benchmarks run agents with a bash shell and nothing else, so a type error reaches them only if they run `tsc`. Teams usually work in Claude Code or Cursor, where type errors can show up after every edit. This experiment checks whether that loop helps.

- **Tasks:** the 25 SWE-bench Multilingual tasks whose reference fix edits only TypeScript files (13) or only JavaScript the repository doesn't type-check (12), as labeled in [`../benchmarks/js_ts`](../benchmarks/js_ts).
- **Agent:** Claude Code 2.1.330, headless (`claude -p`), with Claude Opus 5.5 and one attempt per task and condition, run November 23, 2026.
- **Sandbox:** each task's official SWE-bench image (x86, run under emulation on an Apple Silicon Mac). The harness grades each patch with the task's hidden tests.

## Conditions

| Condition | Language server plugin | Hook |
| --- | --- | --- |
| `nolsp` | no | no |
| `lsp` | Anthropic's [`typescript-lsp`](https://code.claude.com/docs/en/plugins/code-intelligence), running `typescript-language-server` 5.3.0 | no |
| `nolsp-edit` | no | yes |
| `lsp-edit` | yes | yes |

The plugin reports type errors only for edits made with Claude Code's Edit and Write tools. In the first runs, the agent edited through the shell instead (`sed -i`, inline Python), so the `-edit` conditions add a `PreToolUse` hook ([`hook/block-shell-edits.mjs`](hook/block-shell-edits.mjs)) that rejects Bash commands writing files outside `/tmp`. Everything else is identical: the image, the Claude Code binary, the prompt ([`run_agent.rb`](run_agent.rb)), and the language server binary on `PATH`.

## Results

| Condition | TypeScript solved | Plain JavaScript solved | Runs that edited with Edit or Write | Runs shown type errors |
| --- | --- | --- | --- | --- |
| No plugin | 12 of 13 | 9 of 12 | 1 of 25 | 0 |
| Plugin | 11 of 13 | 9 of 12 | 2 of 25 | 0 |
| Hook | 12 of 13 | 9 of 12 | 25 of 25 | 0 |
| Plugin and hook | 10 of 13 | 9 of 12 | 25 of 25 | 10 (8 TypeScript), 113 errors |

- **The loop ran only with the hook.** Without it, the plugin saw an edit in 2 runs of 25 and never reported an error.
- **Seeing type errors didn't change the outcome.** The 8 TypeScript runs shown type errors solved all 8 tasks, and so did the same tasks with the hook alone. The two TypeScript tasks the plugin-and-hook runs lost, `babel__babel-15445` and `vuejs__core-11899`, were never shown a type error.
- **How errors reach the agent.** The language server reported 104 times in the plugin-and-hook runs, and Claude Code attached 30 of those reports, with 157 errors, to the agent's next step. Most of the rest were replaced by a newer report for the same file before that step, and Claude Code dropped 2,650 repeats of errors the agent had already seen. Every report arrived before its session ended.
- **TypeScript tasks did better than plain JavaScript ones in every condition**, 12 of 13 against 9 of 12 without any plugin, though the 13 models in the public SWE-bench Multilingual results solved these TypeScript tasks less often (56% on average against 71%). The plain JavaScript failures are three axios tasks. With 25 tasks from 7 repositories and one attempt each, this can't separate types from projects.

Full per-task results: [`results/full.md`](results/full.md) and [`results/full.json`](results/full.json).

## Reproduce

Needs Docker, Ruby 3.4+, Python 3.12+, and a Claude Code token from `claude setup-token`, saved to `~/.config/claude-bench/token`. The runner reads it from there and passes it to the containers through the environment.

```sh
python3 -m venv .venv && .venv/bin/pip install swebench   # the official grading harness
.venv/bin/python -I export_tasks.py                        # writes data/tasks.jsonl
ruby run_agent.rb --run full --conditions nolsp,lsp,nolsp-edit,lsp-edit --groups ts,plain --jobs 6
./grade_parallel.sh full                                   # one harness per condition
ruby evaluate.rb --run full --no-grade                     # results/full.md and full.json
```

`run_agent.rb` expects `cache/claude` (the Claude Code 2.1.330 Linux x64 binary) and `cache/lsp.tar.gz` (Node 22.21.1 with `typescript-language-server` 5.3.0 and TypeScript 5.9.3 under `/opt/lsp`, plus a wrapper in `/opt/lsp/wrap` that runs the server on that Node). Both are built outside the task images so the agent's tools don't depend on each repository's Node version.

`evaluate.rb --no-grade` summarizes from the `report.json` files committed next to each run, so it works without rerunning anything.

## Layout

```
runs/full/<condition>/<instance_id>/
  prompt.md        the prompt: the issue text plus the same short instruction for every task
  stream.jsonl     the headless session (--output-format stream-json)
  projects/        Claude Code's own session transcript
  debug/           Claude Code's --debug log, including every language server message
  patch.diff       the agent's changes
  report.json      the SWE-bench harness verdict
  meta.json        exit status, time, cost, versions
runs/smoke/        the probe sessions that checked the plugin delivers errors headlessly
hook/              the PreToolUse hook for the -edit conditions
data/tasks.jsonl   the 25 tasks with their group and image
```

## Caveats

- One model, one attempt per task and condition. A difference of one or two tasks is within run-to-run noise.
- The images run under x86 emulation, which slows everything, including the language server's first check of a project (about 9 seconds in the smoke test).
- `typescript-language-server` checks TypeScript files and JavaScript the repository opts into checking; plain JavaScript gets few errors by design.
