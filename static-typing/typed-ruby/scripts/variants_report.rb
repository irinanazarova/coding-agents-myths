# Write the per-trial data of the rbs/sorbet experiment: a CSV and Markdown tables
# Usage: ruby .agents/scripts/variants_report.rb OUT.csv OUT_TABLES.md [TASK...]
# The tables go at the end of reports/YYYY-MM-DD-<topic>-runs.md, after the hand-written summary, setup and legend.
require_relative "variants"

TASKS = %w[card-reactions active-storage-tracking notification-bundle-window-overlap board-publish-unpublish-public-boundary]
SHORT_MODEL = { "gpt-6.1-sol-xhigh" => "sol", "gpt-6-luna-max" => "luna", "glm-5.3-flash-max" => "glm", "deepseek-v4.1-flash-max" => "deepseek" }
SOURCE = { "hist" => "ai-evals", "plain" => "here", "rbs" => "here", "sorbet" => "here" }

def meta(d)
  r = load_json("#{d}/result.json")
  [r.fetch("started_at", "")[0, 16].tr("T", " "), (r["outcome"]["detail"] || "").split("\n").first.to_s[0, 160]]
end

def error_kinds(t, n = 4)
  return [] unless t
  by_count(t["errors"].map { _1.include?(": ") ? _1.split(": ", 2)[1][0, 100] : _1 }.tally).first(n).map { |k, v| "#{k} ×#{v}" }
end

def all_checks(rows) = rows.flat_map { trial_checks(_1["dir"]).keys.map { |k| k.split("#test_")[1] } }.uniq

def mdfmt(x, spec) = x.is_a?(Numeric) ? pyformat("%#{spec}", x) : "–"

csv_rows, md = [], []
(ARGV[2..].empty? ? TASKS : ARGV[2..]).each do |task|
  rows = collect(task, errors: true)
  checks = all_checks(rows)
  ids = checks.each_with_index.to_h { |name, i| [name, "C#{i + 1}"] }
  md << "\n### ft-#{task}\n\nChecks:\n"
  md.concat(checks.each_with_index.map { |name, i| "- C#{i + 1}: `#{name}`" })
  md << "\n| model | var | src | trial | started (UTC) | outcome | reward | credit | passed | min | steps | out k | cost $ | ann | esc | tchk | tfail | 1st err | type min | clean | failed |"
  md << "|#{"---|" * 21}"
  rows.each do |r|
    started, detail = meta(r["dir"])
    t = r["types"] || {}
    trial = r["dir"].rpartition("__").last
    failed = r["failed"].map { ids.fetch(_1, _1) }
    md << "| " + [
      SHORT_MODEL[r["model"]], r["variant"], SOURCE[r["variant"]], "`#{trial}`", started, r["outcome"],
      mdfmt(r["reward"], ".1f"), mdfmt(r["credit"], ".2f"), r["total"].positive? ? "#{r["passed"]}/#{r["total"]}" : "–",
      mdfmt(r["minutes"], ".1f"), mdfmt(r["steps"], "d"), r["out_tokens"] && r["out_tokens"] != 0 ? mdfmt(r["out_tokens"] / 1000.0, ".0f") : "–",
      mdfmt(r["cost"], ".3f"), r["annotations"].to_s, r["escapes"].size.to_s,
      mdfmt(t["checks"], "d"), mdfmt(t["failing_checks"], "d"), mdfmt(t["first_errors"], "d"),
      mdfmt(t["typing_min"], ".1f"), { true => "yes", false => "no" }.fetch(t["last_check_clean"], "–"),
      failed.empty? ? "–" : failed.join(" ")
    ].join(" | ") + " |"
    csv_rows << {
      "task" => "ft-#{task}", "model" => r["model"], "variant" => r["variant"], "source" => SOURCE[r["variant"]], "trial" => trial,
      "restarted_from" => r["restarted_from"],
      "started_utc" => started, "outcome" => r["outcome"], "scored" => r["scored"], "detail" => r["scored"] ? "" : detail,
      "reward" => r["reward"], "credit" => r["credit"], "passed" => r["passed"], "total" => r["total"],
      "failed_checks" => r["failed"].join(";"), "agent_min" => r["minutes"] && r["minutes"] != 0 ? rnd(r["minutes"], 1) : nil,
      "steps" => r["steps"], "output_tokens" => r["out_tokens"], "cost_usd" => r["cost"], "ruby_lines_added" => r["ruby_lines"],
      "annotations" => r["annotations"], "escapes" => r["escapes"].size, "escape_lines" => r["escapes"].join(" | "),
      "type_checks" => t["checks"], "failing_type_checks" => t["failing_checks"], "first_check_errors" => t["first_errors"],
      "typing_min" => t.empty? ? nil : rnd(t["typing_min"], 1), "last_check_clean" => t["last_check_clean"],
      "edits_after_last_check" => t["edits_after_last_check"], "killed_type_tools" => (t["killed"] || []).join(","),
      "read_types_md" => t["read_types_md"], "top_type_errors" => error_kinds(r["types"]).join(" | ")
    }
  end
  # Aggregates per model and variant (scored trials only)
  md << "\nScored trials only:\n"
  md << "| model | var | n | solved | mean reward | mean credit | median passed | median min | median cost $ | median steps |"
  md << "|#{"---|" * 10}"
  aggregate = lambda do |vs|
    med = ->(k) { median(vs.filter_map { _1[k] }) }
    [vs.size, vs.count { (_1["reward"] || 0) >= 1 }, pyformat("%.2f", mean(vs.map { _1["reward"] || 0 })),
     pyformat("%.2f", mean(vs.map { _1["credit"] || 0 })), med]
  end
  MODELS.product(VARIANTS) do |m, v|
    vs = rows.select { _1["model"] == m && _1["variant"] == v && _1["scored"] }
    next if vs.empty?
    n, solved, reward, credit, med = aggregate.(vs)
    total = vs[0]["total"].positive? ? vs[0]["total"] : "–"
    md << "| #{SHORT_MODEL[m]} | #{v} | #{n} | #{solved} | #{reward} | #{credit} | #{pyformat("%.0f", med.("passed"))}/#{total} | " \
          "#{pyformat("%.1f", med.("minutes"))} | #{pyformat("%.3f", med.("cost"))} | #{pyformat("%.0f", med.("steps"))} |"
  end
  VARIANTS.each do |v|
    vs = rows.select { _1["variant"] == v && _1["scored"] }
    next if vs.empty?
    n, solved, reward, credit, med = aggregate.(vs)
    md << "| **all** | #{v} | #{n} | #{solved} | #{reward} | #{credit} | – | " \
          "#{pyformat("%.1f", med.("minutes"))} | #{pyformat("%.3f", med.("cost"))} | #{pyformat("%.0f", med.("steps"))} |"
  end
  # Type errors per typed trial
  md << "\nMost frequent type errors per typed trial:\n"
  rows.each do |r|
    kinds = error_kinds(r["types"])
    md << "- #{SHORT_MODEL[r["model"]]} #{r["variant"]} `#{r["dir"].rpartition("__").last}`: " + kinds.map { "`#{_1}`" }.join("; ") if kinds.any?
  end
end

write_csv(ARGV[0], csv_rows)
File.write(ARGV[1], md.join("\n") + "\n")
puts "#{csv_rows.size} rows"
