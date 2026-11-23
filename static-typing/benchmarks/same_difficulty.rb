# SWE-bench Multilingual compared at the same difficulty level.
#
# The benchmark publishes no difficulty labels, so a task's level comes from
# the size of the human fix: the lines changed by the gold patch, split into
# terciles over all 300 tasks (small, medium, large). Each group's solve rate
# is computed within each level, then averaged with the same weights for both
# sides: each level's share of all the tasks being compared.
#
# Needs the downloads from ./run.sh (data/raw/experiments) and
# results/tasks.csv, which run.sh writes too.
#
# Usage (from static-typing/benchmarks): ruby same_difficulty.rb
# Writes results/same_difficulty.md and results/same_difficulty.json.
require "csv"
require "json"

ROOT = __dir__
TYPED = %w[Rust C Java C++ TypeScript Go]
DYNAMIC = %w[JavaScript PHP Ruby]
DRAWS = 4000

runs = Dir[File.join(ROOT, "data/raw/experiments/2026021*_mini-*/per_instance_details.json")] +
       Dir[File.join(ROOT, "data/raw/experiments/2026022*_mini-*/per_instance_details.json")]
abort "expected the 13 February 2026 runs in data/raw/experiments; run ./run.sh first (found #{runs.size})" unless runs.uniq.size == 13
results = runs.uniq.map { JSON.parse(File.read(_1)) }

tasks = CSV.read(File.join(ROOT, "results/tasks.csv"), headers: true).map(&:to_h)
tasks.each do |t|
  t["score"] = results.count { |r| r.dig(t["instance_id"], "resolved") } / 13.0
  t["typed"] = TYPED.include?(t["lang"])
  %w[lines files f2p].each { t[_1] = t[_1].to_i }
end

sorted = tasks.map { _1["lines"] }.sort
CUTS = [sorted[sorted.size / 3], sorted[2 * sorted.size / 3]]
LEVELS = %w[small medium large]
size_level = ->(t) { t["lines"] <= CUTS[0] ? "small" : t["lines"] <= CUTS[1] ? "medium" : "large" }
SCHEMES = {
  "fix size" => size_level,
  "fix size and files touched" => ->(t) { "#{size_level.(t)}/#{t['files'] > 1 ? 'multi' : 'single'}" },
  "fix size, files touched, and failing tests" => ->(t) { "#{size_level.(t)}/#{t['files'] > 1 ? 'm' : 's'}/#{t['f2p'] > 1 ? 'm' : 's'}" }
}

mean = ->(rows) { rows.sum { _1["score"] } / rows.size.to_f }

# Solve rate of `group`, reweighted to the level mix of `pool`.
# Levels the group has no tasks in are dropped and the weights renormalized.
def std_rate(group, pool, key)
  weights = pool.group_by(&key).transform_values { _1.size.to_f / pool.size }
  by_level = group.group_by(&key)
  covered = weights.select { |k, _| by_level[k] }
  total = covered.values.sum
  covered.sum { |k, w| w / total * by_level[k].sum { _1["score"] } / by_level[k].size }
end

# 95% interval: resample whole repositories within each language.
repos = tasks.group_by { _1["repo"] }
lang_repos = repos.keys.group_by { repos[_1].first["lang"] }
srand(20261116)
out = { "cuts" => { "small_max_lines" => CUTS[0], "medium_max_lines" => CUTS[1] }, "typed_vs_dynamic" => {}, "by_level" => [], "languages" => [], "js_vs_ts" => {} }

LEVELS.each do |lv|
  ty = tasks.select { _1["typed"] && size_level.(_1) == lv }
  dy = tasks.select { !_1["typed"] && size_level.(_1) == lv }
  out["by_level"] << { "level" => lv, "typed_tasks" => ty.size, "typed_solved" => (100 * mean.(ty)).round(1),
                       "dynamic_tasks" => dy.size, "dynamic_solved" => (100 * mean.(dy)).round(1) }
end

typed = tasks.select { _1["typed"] }
dynamic = tasks.reject { _1["typed"] }
out["raw"] = { "typed" => (100 * mean.(typed)).round(1), "dynamic" => (100 * mean.(dynamic)).round(1) }
SCHEMES.each do |name, key|
  gap = std_rate(dynamic, tasks, key) - std_rate(typed, tasks, key)
  draws = DRAWS.times.map do
    sample = lang_repos.flat_map { |_, rs| rs.size.times.map { rs.sample } }.flat_map { repos[_1] }
    std_rate(sample.reject { _1["typed"] }, sample, key) - std_rate(sample.select { _1["typed"] }, sample, key)
  end.sort
  out["typed_vs_dynamic"][name] = {
    "typed" => (100 * std_rate(typed, tasks, key)).round(1), "dynamic" => (100 * std_rate(dynamic, tasks, key)).round(1),
    "dynamic_minus_typed" => (100 * gap).round(1),
    "ci95" => [(100 * draws[(DRAWS * 0.025).to_i]).round(1), (100 * draws[(DRAWS * 0.975).to_i - 1]).round(1)]
  }
end

(TYPED + DYNAMIC).each do |lang|
  rows = tasks.select { _1["lang"] == lang }
  out["languages"] << { "language" => lang, "typed" => TYPED.include?(lang), "tasks" => rows.size,
                        "raw" => (100 * mean.(rows)).round(1), "same_mix" => (100 * std_rate(rows, tasks, size_level)).round(1),
                        "tasks_per_level" => LEVELS.map { |lv| rows.count { size_level.(_1) == lv } } }
end

# JavaScript vs TypeScript, weighted to the JS+TS level mix.
[["all tasks", ->(_) { true }], ["without tasks no model solved", ->(t) { t["score"] > 0 }]].each do |name, keep|
  js = tasks.select { _1["lang"] == "JavaScript" && keep.(_1) }
  ts = tasks.select { _1["lang"] == "TypeScript" && keep.(_1) }
  pool = js + ts
  out["js_vs_ts"][name] = { "js_tasks" => js.size, "ts_tasks" => ts.size,
                            "raw_js_minus_ts" => (100 * (mean.(js) - mean.(ts))).round(1),
                            "same_mix_js_minus_ts" => (100 * (std_rate(js, pool, size_level) - std_rate(ts, pool, size_level))).round(1) }
end

# Preact's jsconfig.json turns on TypeScript checking for its JavaScript
# (js_ts/labels.py), so check that the typed-vs-dynamic result survives
# counting its tasks as typed, or leaving them out. Runs after the draws
# above, so it leaves their intervals unchanged.
out["preact"] = {}
{ "Preact counted as typed" => ->(ts) { ts.map { |x| x["repo"] == "preactjs/preact" ? x.merge("typed" => true, "lang" => "Preact") : x } },
  "Preact left out" => ->(ts) { ts.reject { _1["repo"] == "preactjs/preact" } } }.each do |name, f|
  v = f.(tasks)
  vrepos = v.group_by { _1["repo"] }
  vlang = vrepos.keys.group_by { vrepos[_1].first["lang"] }
  gap = std_rate(v.reject { _1["typed"] }, v, size_level) - std_rate(v.select { _1["typed"] }, v, size_level)
  draws = DRAWS.times.map do
    s = vlang.flat_map { |_, rs| rs.size.times.map { rs.sample } }.flat_map { vrepos[_1] }
    std_rate(s.reject { _1["typed"] }, s, size_level) - std_rate(s.select { _1["typed"] }, s, size_level)
  end.sort
  out["preact"][name] = { "dynamic_minus_typed" => (100 * gap).round(1),
                          "ci95" => [(100 * draws[(DRAWS * 0.025).to_i]).round(1), (100 * draws[(DRAWS * 0.975).to_i - 1]).round(1)] }
end

File.write(File.join(ROOT, "results/same_difficulty.json"), JSON.pretty_generate(out))

md = +"# SWE-bench Multilingual at the same difficulty\n\nGenerated by `same_difficulty.rb`. 13 February 2026 runs, mean over models. "
md << "Levels are terciles of gold-patch lines changed: small up to #{CUTS[0]}, medium up to #{CUTS[1]}, large above. "
md << "Intervals resample whole repositories within each language (#{DRAWS} draws).\n\n"
md << "## Typed vs dynamic, level by level\n\n| Level | Typed tasks | Typed solved | Dynamic tasks | Dynamic solved |\n|---|---|---|---|---|\n"
out["by_level"].each { |r| md << "| #{r['level']} | #{r['typed_tasks']} | #{r['typed_solved']}% | #{r['dynamic_tasks']} | #{r['dynamic_solved']}% |\n" }
md << "\nRaw (no matching): typed #{out['raw']['typed']}%, dynamic #{out['raw']['dynamic']}%.\n\n"
md << "## Typed vs dynamic at the same mix\n\n| Matched on | Typed | Dynamic | Dynamic minus typed | 95% interval |\n|---|---|---|---|---|\n"
out["typed_vs_dynamic"].each { |k, r| md << "| #{k} | #{r['typed']}% | #{r['dynamic']}% | #{format('%+.1f', r['dynamic_minus_typed'])} | #{format('%+.1f', r['ci95'][0])} to #{format('%+.1f', r['ci95'][1])} |\n" }
md << "\n## Each language at the same fix-size mix\n\n| Language | Typed | Tasks | Raw | Same mix | Tasks per level (S/M/L) |\n|---|---|---|---|---|---|\n"
out["languages"].each { |r| md << "| #{r['language']} | #{r['typed'] ? 'yes' : 'no'} | #{r['tasks']} | #{r['raw']}% | #{r['same_mix']}% | #{r['tasks_per_level'].join('/')} |\n" }
md << "\n## JavaScript vs TypeScript\n\n| Tasks | JS | TS | Raw JS minus TS | Same mix JS minus TS |\n|---|---|---|---|---|\n"
out["js_vs_ts"].each { |k, r| md << "| #{k} | #{r['js_tasks']} | #{r['ts_tasks']} | #{format('%+.1f', r['raw_js_minus_ts'])} | #{format('%+.1f', r['same_mix_js_minus_ts'])} |\n" }
md << "\n## Typed vs dynamic with Preact moved (fix size)\n\n| Variant | Dynamic minus typed | 95% interval |\n|---|---|---|\n"
out["preact"].each { |k, r| md << "| #{k} | #{format('%+.1f', r['dynamic_minus_typed'])} | #{format('%+.1f', r['ci95'][0])} to #{format('%+.1f', r['ci95'][1])} |\n" }
File.write(File.join(ROOT, "results/same_difficulty.md"), md)
puts md
