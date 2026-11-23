# Grade the patches in runs/<run>/ with the official SWE-bench harness, then
# summarize solve rate, time, cost, and diagnostics seen, by condition and group.
#
#   ruby evaluate.rb --run pilot
#
# Writes runs/<run>/<condition>/predictions.jsonl, harness logs under logs/,
# and results/<run>.json and results/<run>.md.

require "json"
require "optparse"
require "open3"
require "fileutils"

HERE = __dir__
DATASET = "SWE-bench/SWE-bench_Multilingual"

opts = { run: nil, workers: 3, grade: true, timeout: 600 }
OptionParser.new do |o|
  o.on("--run NAME") { |v| opts[:run] = v }
  o.on("--workers N", Integer) { |v| opts[:workers] = v }
  o.on("--timeout SECONDS", Integer, "per-task test timeout") { |v| opts[:timeout] = v }
  o.on("--no-grade", "summarize existing reports only") { opts[:grade] = false }
end.parse!
abort "--run is required" unless opts[:run]

run_dir = File.join(HERE, "runs", opts[:run])
tasks = File.readlines(File.join(HERE, "data", "tasks.jsonl")).to_h { |l| t = JSON.parse(l); [t["instance_id"], t] }

# Diagnostics Claude Code actually showed the agent. The language server's
# results are queued and attached to the agent's next turn; each delivery is a
# transcript entry {"type":"attachment","attachment":{"type":"diagnostics",
# "files":[{"uri":…,"diagnostics":[{"severity":"Error",…}]}]}}, rendered to the
# model as <new-diagnostics>. Results that arrive after the session ends are
# never delivered, so a server reply alone doesn't count.
def diagnostics_seen(dir)
  deliveries = 0
  errors = 0
  codes = Hash.new(0)
  Dir.glob(File.join(dir, "projects", "**", "*.jsonl")).each do |f|
    File.foreach(f) do |line|
      next unless line.include?('"type":"diagnostics"')
      e = JSON.parse(line) rescue next
      next unless e["type"] == "attachment" && e.dig("attachment", "type") == "diagnostics"
      deliveries += 1
      Array(e.dig("attachment", "files")).each do |file|
        Array(file["diagnostics"]).each do |d|
          next unless d["severity"] == "Error"
          errors += 1
          codes["#{d['source']}#{d['code']}"] += 1
        end
      end
    end
  end
  { diagnostic_blocks: deliveries, diagnostic_errors: errors, diagnostic_codes: codes }
end

# What the agent did with its tools: edits through Edit/Write (the only edits
# Claude Code reports to the language server), Bash calls, and Bash commands the
# shell-edit hook blocked.
def tool_use(dir)
  counts = Hash.new(0)
  File.foreach(File.join(dir, "stream.jsonl")) do |line|
    e = JSON.parse(line) rescue next
    Array(e.dig("message", "content")).each do |c|
      next unless c.is_a?(Hash)
      counts[c["name"]] += 1 if c["type"] == "tool_use"
      counts["hook_blocks"] += 1 if c["type"] == "tool_result" && c["content"].to_s.include?("Blocked (")
    end
  end
  { "edit_tool_calls" => counts["Edit"] + counts["Write"] + counts["MultiEdit"], "bash_calls" => counts["Bash"],
    "hook_blocks" => counts["hook_blocks"] }
end

# From Claude Code's --debug log: how many diagnostic sets the language server
# reported, and how many Claude Code attached to a turn. Reported but never
# delivered means the session moved on or ended first.
def lsp_debug(dir)
  reported = delivered = 0
  Dir.glob(File.join(dir, "debug", "*.txt")).each do |f|
    File.foreach(f) do |line|
      reported += $1.to_i if line =~ /LSP Diagnostics: Registering (\d+) diagnostic file/
      delivered += $1.to_i if line =~ /LSP Diagnostics: Returning (\d+) diagnostic attachment/
    end
  end
  { "lsp_sets_reported" => reported, "lsp_sets_delivered" => delivered }
end

def tsc_runs(dir)
  n = 0
  File.foreach(File.join(dir, "stream.jsonl")) do |line|
    next unless line.include?("tool_use")
    e = JSON.parse(line) rescue next
    Array(e.dig("message", "content")).each do |c|
      next unless c["type"] == "tool_use" && c["name"] == "Bash"
      n += 1 if c.dig("input", "command").to_s.match?(/\btsc\b|type-?check|vue-tsc/)
    end
  end
  n
end

rows = []
Dir.children(run_dir).sort.each do |condition|
  cdir = File.join(run_dir, condition)
  next unless File.directory?(cdir)
  model_name = "claude-code-#{condition}"
  preds = Dir.children(cdir).sort.filter_map do |iid|
    d = File.join(cdir, iid)
    next unless File.exist?(File.join(d, "meta.json"))
    { instance_id: iid, model_name_or_path: model_name, model_patch: File.read(File.join(d, "patch.diff")) }
  end
  next if preds.empty?
  pred_path = File.join(cdir, "predictions.jsonl")
  File.write(pred_path, preds.map(&:to_json).join("\n") + "\n")

  run_id = "#{opts[:run]}-#{condition}"
  if opts[:grade]
    cmd = [File.join(HERE, ".venv", "bin", "python"), "-m", "swebench.harness.run_evaluation",
           "-d", DATASET, "-p", pred_path, "-id", run_id, "--max_workers", opts[:workers].to_s, "-t", opts[:timeout].to_s,
           "--report_dir", File.join(HERE, "logs", "reports"), "-i", *preds.map { _1[:instance_id] }]
    puts "grading #{condition}: #{preds.size} patches"
    out, status = Open3.capture2e(*cmd, chdir: HERE)
    File.write(File.join(cdir, "harness.log"), out)
    abort "harness failed for #{condition}; see #{cdir}/harness.log" unless status.success?
  end

  preds.each do |p|
    iid = p[:instance_id]
    d = File.join(cdir, iid)
    meta = JSON.parse(File.read(File.join(d, "meta.json")))
    # The harness writes reports under logs/ (not published); a copy sits next to each run.
    report = File.join(HERE, "logs", "run_evaluation", run_id, model_name, iid, "report.json")
    report = File.join(d, "report.json") unless File.exist?(report)
    resolved = File.exist?(report) && JSON.parse(File.read(report)).dig(iid, "resolved") == true
    rows << meta.slice("instance_id", "condition", "duration_s", "num_turns", "cost_usd", "timed_out", "patch_bytes")
                .merge("group" => tasks[iid]["group"], "resolved" => resolved, "graded" => File.exist?(report),
                       "tsc_runs" => tsc_runs(d))
                .merge(tool_use(d)).merge(lsp_debug(d))
                .merge(diagnostics_seen(d).transform_keys(&:to_s))
  end
end

FileUtils.mkdir_p(File.join(HERE, "results"))
File.write(File.join(HERE, "results", "#{opts[:run]}.json"), JSON.pretty_generate(rows))

median = ->(a) { s = a.compact.sort; s.empty? ? nil : (s.size.odd? ? s[s.size / 2] : (s[s.size / 2 - 1] + s[s.size / 2]) / 2.0) }
lines = ["# Claude Code with and without typescript-lsp: #{opts[:run]}", "",
         "| Condition | Group | Tasks | Solved | Median minutes | Median cost | Runs with an Edit/Write | Runs shown type errors | Runs that ran tsc |",
         "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
rows.group_by { [_1["condition"], _1["group"]] }.sort.each do |(c, g), rs|
  solved = rs.count { _1["resolved"] }
  lines << "| #{c} | #{g} | #{rs.size} | #{solved} (#{(100.0 * solved / rs.size).round}%) | " \
           "#{median.(rs.map { _1['duration_s'] })&./(60.0)&.round(1)} | $#{median.(rs.map { _1['cost_usd'] })&.round(2)} | " \
           "#{rs.count { _1['edit_tool_calls'].positive? }} | #{rs.count { _1['diagnostic_errors'].positive? }} | #{rs.count { _1['tsc_runs'].positive? }} |"
end
lines << "" << "| Instance | Condition | Group | Resolved | Minutes | Cost | Edit/Write calls | Hook blocks | Type errors shown | LSP sets reported / delivered | tsc runs |" << "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
rows.sort_by { [_1["instance_id"], _1["condition"]] }.each do |r|
  lines << "| #{r['instance_id']} | #{r['condition']} | #{r['group']} | #{r['graded'] ? r['resolved'] : 'not graded'} | " \
           "#{(r['duration_s'] / 60.0).round(1)} | $#{r['cost_usd']&.round(2)} | #{r['edit_tool_calls']} | #{r['hook_blocks']} | " \
           "#{r['diagnostic_errors']} | #{r['lsp_sets_reported']} / #{r['lsp_sets_delivered']} | #{r['tsc_runs']} |"
end
File.write(File.join(HERE, "results", "#{opts[:run]}.md"), lines.join("\n") + "\n")
puts lines.join("\n")
