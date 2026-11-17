# Coding agents myths

Claims about coding agents travel fast, and many are repeated without evidence. This repository checks them one at a time against data anyone can rerun: public benchmark results, and full run histories from our own agent experiments.

Each myth lives in its own folder with the claim, what the data says, and the scripts that produce every number.

## Myths checked so far

| Myth | Verdict | Folder |
| --- | --- | --- |
| Static typing makes coding agents better | No measurable effect on success, speed, or cost. At the same task difficulty, typed and dynamic languages tie on public benchmarks, and type errors cost Ruby agents under 1% of their time | [`static-typing/`](static-typing/) |

## How each myth is checked

Every folder follows the same rules, so a reader can audit one without learning a new setup:

- **Public inputs are pinned.** Downloads name an exact commit or dataset revision, and every file's SHA-256 is checked before it's read.
- **Our own runs are published in full.** Every agent step with its command and output, the final patches, and the verifier logs.
- **Hand judgments are data.** When a person or a model labeled something, the labels sit in a CSV with the reason, next to the script that checks they cover exactly the cases the rules found.
- **One command per analysis.** Each analysis folder has a `run.sh` or a short list of commands, and its README says what each output file holds.
- **Results are committed.** Generated tables sit in `results/`, so you can read them without running anything, and diff them after you do.
- **Comparisons are like for like.** Languages, stacks, or tools are compared on tasks of the same difficulty, and the README says how difficulty was measured.

To add a myth, copy [`TEMPLATE.md`](TEMPLATE.md) into a new folder as its `README.md`.

## Requirements

Ruby 3.4 or newer for the Ruby scripts. Python 3.12 or newer where a folder uses Python; its `run.sh` creates a virtualenv with pinned dependencies.

## Who's behind this

[Evil Martians](https://evilmartians.com) build developer tools and run agent evaluations on real Ruby on Rails apps. If you rerun something and get a different answer, open an issue.
