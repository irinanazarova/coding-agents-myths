# Claude Code with a TypeScript language server

The public benchmarks run agents with a bash shell and nothing else, so a type error reaches them only if they run `tsc`. Teams usually work in Claude Code or Cursor, where type errors can show up after every edit. This experiment checks whether that loop helps.

- **Tasks:** the 25 SWE-bench Multilingual tasks whose reference fix edits only TypeScript files (13) or only JavaScript the repository doesn't type-check (12), as labeled in [`../benchmarks/js_ts`](../benchmarks/js_ts).
- **Agent:** Claude Code 2.1.330, headless (`claude -p`), with Claude Opus 5.5 and three attempts per task and condition (runs `full`, `full-a2`, `full-a3`), run November 23, 2026.
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

Each cell is the median of the three attempts' solve rates, ± its standard error ([`results/combined.md`](results/combined.md), from `aggregate.rb`).

| | No plugin | Plugin | Hook | Plugin and hook |
| --- | --- | --- | --- | --- |
| TypeScript solved (13 tasks) | 92% ± 0 | 85% ± 3 | 92% ± 0 | 77% ± 3 |
| Plain JavaScript solved (12 tasks) | 75% ± 3 | 75% ± 3 | 75% ± 3 | 75% ± 0 |
| TypeScript runs shown type errors | 0 of 39 | 0 of 39 | 0 of 39 | 23 of 39 |
| Runs that edited with Edit or Write | 5 of 75 | 5 of 75 | 75 of 75 | 75 of 75 |

- **The loop ran only with the hook.** With the plugin alone, the agent edited through the shell in 70 runs of 75, so the plugin never reported an error. This is [anthropics/claude-code#80267](https://github.com/anthropics/claude-code/issues/80267), reproduced by a maintainer and closed without a fix.
- **Seeing type errors didn't help, and installing the plugin hurt.** Without the plugin, every run solved the same 12 TypeScript tasks. With it, runs lost `babel__babel-15445` (5 of 6 plugin runs) and `vuejs__core-11899` (4 of 6), which no run without the plugin failed. None of those 9 failed runs was shown a type error or called the LSP tool: the Babel fixes return `null` where the test expects the value to stay missing, and the Vue fixes leave CSS comments behind in a nested rule. The plugin's only footprint in those sessions is the extra tool in the agent's context.
- **How errors reach the agent.** In the plugin-and-hook runs, the language server reported 234 times. Claude Code attaches only new errors, and only the latest report per file, to the agent's next step: 66 reports were shown, 117 were replaced by a newer report first, and 51 arrived after the agent's last step.
- **TypeScript tasks did better than plain JavaScript ones in every condition**, 92% against 75% without any plugin, though the 13 models in the public SWE-bench Multilingual results solved these TypeScript tasks less often (56% on average against 71%). With 25 tasks from 7 repositories, this can't separate types from projects.

Per-attempt results: [`results/full.md`](results/full.md), [`results/full-a2.md`](results/full-a2.md), [`results/full-a3.md`](results/full-a3.md).

## Reproduce

Needs Docker, Ruby 3.4+, Python 3.12+, and a Claude Code token from `claude setup-token`, saved to `~/.config/claude-bench/token`. The runner reads it from there and passes it to the containers through the environment.

```sh
python3 -m venv .venv && .venv/bin/pip install swebench   # the official grading harness
.venv/bin/python -I export_tasks.py                        # writes data/tasks.jsonl
ruby run_agent.rb --run full --conditions nolsp,lsp,nolsp-edit,lsp-edit --groups ts,plain --jobs 6
./grade_parallel.sh full                                   # one harness per condition
ruby evaluate.rb --run full --no-grade                     # results/full.md and full.json
# attempts 2 and 3: the same two commands with --run full-a2 and --run full-a3
ruby aggregate.rb                                          # results/combined.md
```

`run_agent.rb` expects `cache/claude` (the Claude Code 2.1.330 Linux x64 binary) and `cache/lsp.tar.gz` (Node 22.21.1 with `typescript-language-server` 5.3.0 and TypeScript 5.9.3 under `/opt/lsp`, plus a wrapper in `/opt/lsp/wrap` that runs the server on that Node). Both are built outside the task images so the agent's tools don't depend on each repository's Node version.

`evaluate.rb --no-grade` summarizes from the `report.json` files committed next to each run, so it works without rerunning anything.

## Layout

```
runs/<full|full-a2|full-a3>/<condition>/<instance_id>/
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

- One model, three attempts per task and condition. The plugin effect rests on two tasks of 13; it held in every attempt, and the mechanism is not fully explained.
- The images run under x86 emulation, which slows everything, including the language server's first check of a project (about 9 seconds in the smoke test).
- `typescript-language-server` checks TypeScript files and JavaScript the repository opts into checking; plain JavaScript gets few errors by design.
