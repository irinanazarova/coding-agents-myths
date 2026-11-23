// PreToolUse hook for the "edit-tools" conditions: reject Bash commands that
// write files outside /tmp, so every source change goes through Claude Code's
// Edit or Write tool. Only those tools tell the language server about a change,
// so without this the typescript-lsp plugin never sees the agent's edits.
//
// Claude Code passes the tool call as JSON on stdin. Exit code 2 blocks the
// call and shows stderr to the agent. The patterns are heuristics; anything
// they miss is counted afterwards from the transcript (edits_via_bash).

let input = "";
process.stdin.on("data", (c) => (input += c));
process.stdin.on("end", () => {
  const cmd = JSON.parse(input)?.tool_input?.command ?? "";
  const outsideTmp = (path) => path && !/^['"]?\/tmp\//.test(path) && path !== "/dev/null" && !path.startsWith("&");

  const reasons = [];
  if (/\bsed\b[^|;&]*\s-i/.test(cmd)) reasons.push("sed -i");
  if (/\bperl\b[^|;&]*\s-\w*i/.test(cmd)) reasons.push("perl -i");
  if (/\b(patch|git apply)\b/.test(cmd)) reasons.push("patch");
  if (/(write_text|writeFileSync|writeFile\(|\.write\(|open\([^)]*['"][wa]\+?['"])/.test(cmd)) reasons.push("script that writes a file");
  for (const m of cmd.matchAll(/(?<![0-9&])>>?\s*([^\s;|&)]+)/g)) if (outsideTmp(m[1])) reasons.push(`redirect to ${m[1]}`);
  for (const m of cmd.matchAll(/\btee\s+(?:-a\s+)?([^\s;|&]+)/g)) if (outsideTmp(m[1])) reasons.push(`tee ${m[1]}`);
  for (const m of cmd.matchAll(/\b(?:cp|mv)\s+(?:-\w+\s+)*\S+\s+([^\s;|&]+)/g)) if (outsideTmp(m[1])) reasons.push(`cp/mv to ${m[1]}`);

  if (reasons.length === 0) process.exit(0);
  process.stderr.write(
    `Blocked (${[...new Set(reasons)].join(", ")}): in this repository, change files only with the Edit or Write tool. ` +
      "Bash is for running commands such as tests; scratch files may go in /tmp.\n",
  );
  process.exit(2);
});
