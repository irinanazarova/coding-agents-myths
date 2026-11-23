# Compare typed variant trials (this repo's runs/) with plain baselines (ai-evals runs)
# Usage: ruby .agents/scripts/variants.rb TASK [TASK...]   (task names without the ft- prefix)
# RUNS_DIR and BASELINES (colon-separated) override the run directories.
require_relative "support"

REPO_RUNS = ENV.fetch("RUNS_DIR", File.join(ROOT, "runs"))
BASELINES = ENV.fetch("BASELINES", File.join(AI_EVALS, "2026-10-06-feature-tasks-revamped")).split(":")
VARIANTS = %w[hist plain rbs sorbet]

CHECK_CMD = /steep check|srb tc/
TYPE_TOOL = /steep|srb |tapioca|rbs:generate|rbs:rails|rbs:inline|rbs collection/
STEEP_ERR = /^(\S+\.rb):\d+:\d+: \[error\] (.*)$/
SRB_ERR = /^(\S+\.rb):\d+: (.*?) https:\/\/srb\.help\/(\d+)$/
ESCAPES = /steep:ignore|T\.unsafe|T\.untyped|\buntyped\b|T\.must|as !nil|#: as |T\.cast|T\.let/
ANNOT = /#: |# @rbs|# @type|# typed:|# @requires_ancestor/
EDIT = /File\.write|cat >|cat <<|sed -i|apply_patch|python3 -|>> /
# The line breaks of Python's str.splitlines()
LINE_BREAK = /\r\n|[\n\r\v\f\x1c\x1d\x1e\u0085  ]/

def agent_minutes(r)
  ph = (r["phases"] || []).find { _1["name"] == "agent" && _1["finished_at"] }
  ph && (ts(ph["finished_at"]) - ts(ph["started_at"])) / 60
end

def trial_checks(d) = load_json("#{d}/checks.json")&.fetch("checks", nil) || {}

# Added lines in app/ and lib/ Ruby files of the agent's patch
def hand_written(patch_path)
  return [] unless File.exist?(patch_path)
  keep = false
  read_text(patch_path).split(LINE_BREAK).each_with_object([]) do |line, out|
    if line.start_with?("diff --git")
      keep = line.split(" b/").last.match?(/\A(app|lib)\/.*\.rb\z/)
    elsif keep && line.start_with?("+") && !line.start_with?("+++")
      out << line[1..]
    end
  end
end

# What the agent did with the type tools, read from the trajectory
def type_activity(d)
  steps = load_json("#{d}/trajectory.json")&.fetch("steps", nil) or return
  act = { "checks" => 0, "failing_checks" => 0, "first_errors" => nil, "killed" => [], "typing_min" => 0.0,
          "errors" => [], "read_types_md" => false, "last_check_clean" => nil, "edits_after_last_check" => 0 }
  last_check_idx = nil
  steps.each_with_index do |s, i|
    nxt = steps[i + 1]&.dig("timestamp")
    dt = nxt && s["timestamp"] ? (ts(nxt) - ts(s["timestamp"])) / 60 : 0
    cmds = (s["tool_calls"] || []).map { _1["arguments"]["command"] || "" }
    results = s.dig("observation", "results") || []
    act["typing_min"] += dt if cmds.any? { TYPE_TOOL.match?(_1) } && dt < 30 # a restart leaves a gap of hours
    act["read_types_md"] = true if cmds.any? { _1.include?("TYPES.md") }
    cmds.zip(results).first(results.size).each do |c, r|
      o = JSON.parse(r["content"]) rescue next
      out = "#{o["output"]}#{o["output_head"]}#{o["output_tail"]}"
      rc = o["returncode"]
      if TYPE_TOOL.match?(c) && [124, 137].include?(rc)
        act["killed"] << "#{%w[steep srb tapioca rbs].find { c.include?(_1) }}:#{rc}"
      end
      next unless CHECK_CMD.match?(c)
      found = out.scan(STEEP_ERR).map { |f, m| "#{f}: #{m}" } + out.scan(SRB_ERR).map { |f, m, code| "#{f}: #{m} (#{code})" }
      clean = out.match?(/No type error detected|No errors! Great job/)
      next if !clean && found.empty? # the check didn't run to completion (killed, piped away, ...)
      act["checks"] += 1
      if found.any?
        act["failing_checks"] += 1
        act["errors"].concat(found)
      end
      act["first_errors"] ||= found.size
      act["last_check_clean"] = clean && found.empty?
      last_check_idx = i
    end
  end
  if last_check_idx
    act["edits_after_last_check"] = steps[(last_check_idx + 1)..].sum do |s|
      (s["tool_calls"] || []).count { EDIT.match?(_1["arguments"]["command"] || "") }
    end
  end
  act
end

def trial(d, model, task, variant)
  r = load_json("#{d}/result.json") or return
  u = r["usage"] || {}
  c = trial_checks(d)
  added = hand_written("#{d}/agent.patch")
  {
    "dir" => d, "restarted_from" => restarted_from(d), "superseded_by" => superseded_by(d.rpartition("__").last), "model" => model, "task" => task, "variant" => variant, "outcome" => r["outcome"]["name"],
    "scored" => r["outcome"]["scored"], "reward" => r["reward"], "credit" => r["credit"],
    "passed" => c.count { |_, v| v == "pass" }, "total" => c.size,
    "failed" => c.reject { |_, v| v == "pass" }.keys.map { _1.split("#test_")[1] },
    "minutes" => agent_minutes(r), "steps" => u["steps"], "out_tokens" => u["output_tokens"], "cost" => u["cost_usd"],
    "annotations" => added.count { ANNOT.match?(_1) },
    "escapes" => added.select { ESCAPES.match?(_1) }.map(&:strip),
    "ruby_lines" => added.size,
    "types" => %w[rbs sorbet].include?(variant) ? type_activity(d) : nil
  }
end

def collect(task, errors: false)
  rows = BASELINES.flat_map do |base|
    MODELS.flat_map { |m| Dir.glob("#{base}/#{m}/ft-#{task}__*").sort.map { trial(_1, m, task, "hist") } }
  end
  MODELS.each do |m|
    rows += Dir.glob("#{REPO_RUNS}/#{m}/ft-#{task}__*").sort.map { trial(_1, m, task, "plain") }
    %w[rbs sorbet].each { |v| rows += Dir.glob("#{REPO_RUNS}/#{m}/ft-#{task}-#{v}__*").sort.map { trial(_1, m, task, v) } }
  end
  # Infrastructure errors (provider 502s, credits) were restarted as new trials; a restarted source never counts
  rows.compact.select { !_1["superseded_by"] && (errors || _1["outcome"] != "agent_error") }
end

def fmt(x, spec) = x.is_a?(Numeric) ? pyformat("%#{spec}", x) : "-"

# str() of a Python value
def pystr(x) = { true => "True", false => "False", nil => "None" }.fetch(x) { x.to_s }

def main(tasks)
  tasks.each do |task|
    rows = collect(task)
    puts "\n#################### ft-#{task}"
    puts "#{"model".ljust(24)} #{"var".ljust(6)} #{"outcome".ljust(12)} #{"rew".rjust(4)} #{"cred".rjust(5)} #{"checks".rjust(6)} " \
         "#{"min".rjust(6)} #{"steps".rjust(5)} #{"out_k".rjust(6)} #{"cost".rjust(6)} #{"ann".rjust(4)} #{"esc".rjust(4)} " \
         "#{"tchk".rjust(4)} #{"tfail".rjust(5)} #{"1st".rjust(4)} #{"tmin".rjust(5)} #{"clean".rjust(5)} killed"
    rows.each do |r|
      t = r["types"] || {}
      puts "#{r["model"].ljust(24)} #{r["variant"].ljust(6)} #{r["outcome"].ljust(12)} #{fmt(r["reward"], "4.1f")} #{fmt(r["credit"], "5.2f")} " \
           "#{"#{r["passed"]}/#{r["total"]}".rjust(6)} #{fmt(r["minutes"], "6.1f")} #{fmt(r["steps"], "5d")} " \
           "#{fmt((r["out_tokens"] || 0) / 1000.0, "6.0f")} #{fmt(r["cost"], "6.3f")} #{r["annotations"].to_s.rjust(4)} #{r["escapes"].size.to_s.rjust(4)} " \
           "#{fmt(t["checks"], "4d")} #{fmt(t["failing_checks"], "5d")} #{fmt(t["first_errors"], "4d")} " \
           "#{fmt(t["typing_min"], "5.1f")} #{(t.key?("last_check_clean") ? pystr(t["last_check_clean"]) : "-").rjust(5)} #{(t["killed"] || []).join(",")}"
    end
    # Aggregates per variant (scored trials only)
    puts
    VARIANTS.each do |v|
      vs = rows.select { _1["variant"] == v && _1["scored"] }
      next if vs.empty?
      med = ->(k) { median(vs.filter_map { _1[k] }) }
      puts "  #{v.ljust(6)} n=#{vs.size.to_s.rjust(2)}  reward=#{pyformat("%.2f", mean(vs.map { _1["reward"] || 0 }))}  " \
           "credit=#{pyformat("%.2f", mean(vs.map { _1["credit"] || 0 }))}  median min=#{pyformat("%.1f", med.("minutes"))}  " \
           "median cost=$#{pyformat("%.3f", med.("cost"))}  median steps=#{pyformat("%.0f", med.("steps"))}"
    end
    # Per model and variant
    puts
    MODELS.each do |m|
      cells = VARIANTS.filter_map do |v|
        vs = rows.select { _1["model"] == m && _1["variant"] == v }
        next if vs.empty?
        mins = vs.map { _1["minutes"] }.select { _1 && _1 != 0 }
        cost = vs.map { _1["cost"] }.select { _1 && _1 != 0 }
        "#{v}: " + vs.map { _1["scored"] ? "#{_1["passed"]}/#{_1["total"]}" : _1["outcome"][0, 7] }.join(",") +
          pyformat(" %.0fm $%.2f", median(mins) || 0, median(cost) || 0)
      end
      puts "  #{m.ljust(24)} #{cells.join(" | ")}"
    end
    # Failing checks per variant
    puts
    VARIANTS.each do |v|
      vs = rows.select { _1["variant"] == v && _1["scored"] }
      next if vs.empty?
      puts "  #{v.ljust(6)} failing checks: " + by_count(vs.flat_map { _1["failed"] }.tally).map { |k, n| "#{k[0, 55]}×#{n}" }.join("; ")
    end
  end
end

main(ARGV.empty? ? %w[notification-bundle-window-overlap board-publish-unpublish-public-boundary] : ARGV) if __FILE__ == $0
