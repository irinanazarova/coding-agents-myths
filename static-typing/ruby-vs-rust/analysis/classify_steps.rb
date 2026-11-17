# Reads every run listed in runs.csv and writes results/steps.csv:
# one row per agent step, with the seconds it took and its activity category.
#
# A step's time runs from its timestamp to the next step's timestamp: the
# command running plus the agent reading the output and deciding what to do.
# Gaps over 30 minutes are dropped as infrastructure stalls.
#
# Usage (from static-typing/ruby-vs-rust): ruby analysis/classify_steps.rb
require "csv"
require "json"
require "time"
require_relative "rules"

ROOT = File.expand_path("..", __dir__)
STALL = 1800

def output_text(step)
  (step.dig("observation", "results") || []).map do |r|
    c = r["content"].to_s
    d = (JSON.parse(c) rescue c)
    d.is_a?(Hash) ? d.values_at("output", "output_head", "output_tail", "error").compact.join("\n") : c
  end.join("\n")
end

def returncode(step)
  (step.dig("observation", "results") || []).filter_map { (JSON.parse(_1["content"].to_s)["returncode"] rescue nil) }.max
end

rows = []
CSV.foreach(File.join(ROOT, "runs.csv"), headers: true) do |run|
  stack = run["stack"] == "rust" ? "Rust" : "Ruby"
  Dir[File.join(ROOT, run["path"], "trajectory.*.json")].sort_by { _1[/\.(\d+)\.json/, 1].to_i }.each do |tp|
    session = tp[/\.(\d+)\.json/, 1].to_i
    steps = JSON.parse(File.read(tp))["steps"].select { _1["source"] == "agent" && _1["timestamp"] }
    times = steps.map { Time.parse(_1["timestamp"]).to_i }
    steps.each_with_index do |s, i|
      seconds = (times[i + 1] || times[i]) - times[i]
      next if seconds > STALL
      command = (s["tool_calls"] || []).map { _1.dig("arguments", "command") || _1["arguments"].to_json }.join(" ;; ")
      step = { "task" => run["task"], "model" => run["model"], "stack" => stack, "trial" => run["trial"],
               "session" => session, "step" => s["step_id"], "seconds" => seconds,
               "command" => command, "output_head" => output_text(s), "returncode" => returncode(s) }
      step["category"] = classify(step)
      step["test_loop"] = command.match?(stack == "Rust" ? /\bcargo\s+(?:\S+\s+)?(?:build|test|run|check|clippy|nextest)\b/ : /bin\/rails\s+test|rails\s+test|bundle exec (?:rspec|rake)/) ? 1 : 0
      step["cargo_check"] = command.match?(/\bcargo\s+(?:\S+\s+)?(?:check|clippy)\b/) ? 1 : 0
      rows << step
    end
  end
end

Dir.mkdir(File.join(ROOT, "results")) unless Dir.exist?(File.join(ROOT, "results"))
CSV.open(File.join(ROOT, "results", "steps.csv"), "w") do |csv|
  csv << %w[task model stack trial session step seconds category test_loop cargo_check command]
  rows.each { |r| csv << [*r.values_at(*%w[task model stack trial session step seconds category test_loop cargo_check]), r["command"][0, 300]] }
end
puts "#{rows.size} steps classified into results/steps.csv"
