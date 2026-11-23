# Combines attempts: every task was run three times, once per run (full, full-a2, full-a3).
# Each run is one attempt at all 25 tasks in all four conditions. Rates are computed per
# attempt, then summarized as the median of the attempts and its standard error
# (sample standard deviation over the square root of the number of attempts).
# Reads results/<run>.json written by evaluate.rb and writes results/combined.md.
#
#   ruby aggregate.rb [RUN ...]   # default: full full-a2 full-a3

require "json"
require "csv"

HERE = __dir__
RUNS = ARGV.empty? ? %w[full full-a2 full-a3] : ARGV
CONDITIONS = [["nolsp", "No plugin"], ["lsp", "Plugin"], ["nolsp-edit", "Hook"], ["lsp-edit", "Plugin and hook"]]

rows = RUNS.flat_map do |run|
  path = File.join(HERE, "results", "#{run}.json")
  abort "missing #{path}: run evaluate.rb --run #{run} first" unless File.exist?(path)
  JSON.parse(File.read(path)).map { _1.merge("run" => run) }
end
abort "ungraded rows: #{rows.reject { _1['graded'] }.map { "#{_1['run']}/#{_1['condition']}/#{_1['instance_id']}" }.first(5)}" unless rows.all? { _1["graded"] }

# Difficulty levels from the size of the human fix, as in ../benchmarks/same_difficulty.rb.
lines = CSV.read(File.join(HERE, "..", "benchmarks", "results", "tasks.csv"), headers: true).to_h { [_1["instance_id"], _1["lines"].to_i] }
level = ->(iid) { n = lines.fetch(iid); n <= 6 ? :small : n <= 18 ? :medium : :large }
tasks = rows.map { _1["instance_id"] }.uniq
weights = tasks.group_by(&level).transform_values { _1.size.to_f / tasks.size }

median = ->(a) { s = a.sort; s.size.odd? ? s[s.size / 2] : (s[s.size / 2 - 1] + s[s.size / 2]) / 2.0 }
stderr = lambda do |a|
  return 0.0 if a.size < 2
  m = a.sum / a.size
  Math.sqrt(a.sum { (_1 - m)**2 } / (a.size - 1)) / Math.sqrt(a.size)
end
summary = ->(a) { format("%d%% ± %d", median.(a).round, stderr.(a).round) }
attempts = rows.map { _1["run"] }.uniq
per_attempt = lambda do |cond, group|
  attempts.map do |run|
    rs = rows.select { _1["run"] == run && _1["condition"] == cond && _1["group"] == group }
    100.0 * rs.count { _1["resolved"] } / rs.size
  end
end
gap_per_attempt = lambda do |cond|
  attempts.map do |run|
    only = rows.select { _1["run"] == run }
    rate = lambda do |group|
      ids = tasks.select { |i| rows.find { _1["instance_id"] == i }["group"] == group }
      by_level = ids.group_by(&level)
      covered = weights.select { |l, _| by_level[l] }
      total = covered.values.sum
      100 * covered.sum { |l, w| w / total * by_level[l].sum { |i| only.find { _1["condition"] == cond && _1["instance_id"] == i }["resolved"] ? 1.0 : 0.0 } / by_level[l].size }
    end
    rate.("ts") - rate.("plain")
  end
end

out = +"# Claude Code with and without typescript-lsp: attempts combined\n\n"
out << "Attempts: #{attempts.join(', ')}. Each cell is the median of the per-attempt values ± its standard error.\n\n"
out << "| | #{CONDITIONS.map(&:last).join(' | ')} |\n| --- |#{' --- |' * CONDITIONS.size}\n"
out << "| TypeScript solved (13 tasks) | #{CONDITIONS.map { |c, _| summary.(per_attempt.(c, 'ts')) }.join(' | ')} |\n"
out << "| Plain JavaScript solved (12 tasks) | #{CONDITIONS.map { |c, _| summary.(per_attempt.(c, 'plain')) }.join(' | ')} |\n"
out << "| TypeScript minus plain JavaScript, same fix-size mix | #{CONDITIONS.map { |c, _| g = gap_per_attempt.(c); format('%+d ± %d points', median.(g).round, stderr.(g).round) }.join(' | ')} |\n"
out << "| TypeScript runs shown type errors | #{CONDITIONS.map { |c, _| "#{rows.count { _1['condition'] == c && _1['group'] == 'ts' && _1['diagnostic_errors'].to_i.positive? }} of #{rows.count { _1['condition'] == c && _1['group'] == 'ts' }}" }.join(' | ')} |\n"
out << "| Runs that edited with Edit or Write | #{CONDITIONS.map { |c, _| "#{rows.count { _1['condition'] == c && _1['edit_tool_calls'].to_i.positive? }} of #{rows.count { _1['condition'] == c }}" }.join(' | ')} |\n\n"

out << "Per task, attempts solved (#{attempts.join(', ')}):\n\n| Task | Group | #{CONDITIONS.map(&:last).join(' | ')} |\n| --- | --- |#{' --- |' * CONDITIONS.size}\n"
tasks.sort_by { |i| [rows.find { _1["instance_id"] == i }["group"] == "ts" ? 0 : 1, i] }.each do |iid|
  cells = CONDITIONS.map do |c, _|
    rs = rows.select { _1["condition"] == c && _1["instance_id"] == iid }.sort_by { RUNS.index(_1["run"]) }
    "#{rs.count { _1['resolved'] }}/#{rs.size} #{rs.map { _1['resolved'] ? '✓' : '✗' }.join}"
  end
  out << "| #{iid} | #{rows.find { _1['instance_id'] == iid }['group']} | #{cells.join(' | ')} |\n"
end

File.write(File.join(HERE, "results", "combined.md"), out)
puts out
