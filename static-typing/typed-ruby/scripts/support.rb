# Helpers shared by the scripts in .agents/scripts.
require "csv"
require "json"
require "time"
require "yaml"

ROOT = File.expand_path("../..", __dir__)
AI_EVALS = File.join(ROOT, "../../ai-evals/runs")
MODELS = %w[gpt-6.1-sol-xhigh gpt-6-luna-max glm-5.3-flash-max deepseek-v4.1-flash-max]
# This bench's trials; the deprecated ones (deprecated.yml) live in runs-deprecated/ and count only with DEPRECATED=1
RUN_DIRS = [File.join(ROOT, "runs"), *(File.join(ROOT, "runs-deprecated") if ENV["DEPRECATED"] == "1")]

def ts(s) = Time.iso8601(s)

def load_json(path) = (JSON.parse(File.read(path)) rescue nil)

def read_text(path) = File.read(path, encoding: "UTF-8").scrub

# Cells as the earlier (Python) scripts wrote them: True/False, nil as an empty cell
def cell(value) = { true => "True", false => "False" }.fetch(value) { value&.to_s }

def write_csv(path, rows)
  keys = rows.first.keys
  CSV.open(path, "w", quote_empty: false) do |csv|
    csv << keys
    rows.each { |row| csv << keys.map { cell(row[_1]) } }
  end
end

def median(xs) = xs.empty? ? nil : xs.sort.then { |s| (s[(s.size - 1) / 2] + s[s.size / 2]) / 2.0 }

# Exact, as Python's statistics.mean
def mean(xs) = (xs.sum { _1.to_r } / xs.size).to_f

# Half to even, as Python's round()
def rnd(x, digits) = x.to_r.round(digits, half: :even).to_f

# Sort by count, most frequent first; ties keep their first-seen order
def by_count(counts) = counts.each_with_index.sort_by { |(_, n), i| [-n, i] }.map(&:first)

# Kernel#format, but %f rounds as Python does: the exact binary value, ties to even
def pyformat(fmt, *args)
  i = -1
  values = fmt.scan(/%[-+ 0#]*\d*(?:\.(\d+))?([a-zA-Z%])/).reject { _2 == "%" }.map do |prec, conv|
    x = args[i += 1]
    conv == "f" && x.is_a?(Float) ? x.to_r.round((prec || 6).to_i, half: :even) : x
  end
  format(fmt, *values)
end

# Variant trials from before the instruction rework of 2026-11-01: trial ID => reason (deprecated.yml).
# Reports skip them unless DEPRECATED=1.
DEPRECATED = (YAML.load_file(File.join(__dir__, "deprecated.yml")) || {}).each_with_object({}) do |(_, group), ids|
  group["trials"].each { ids[_1] = group["reason"] }
end

# Restarts (`lemans restart`): result.json names the source run as restarted_from {trial, step, mode}.
# "ID/STEP/MODE" (MODE: recover, reverify, or none), nil for a trial that is not a restart.
def restarted_from(dir)
  r = load_json("#{dir}/result.json")&.dig("restarted_from") or return
  [r["trial"].to_s.rpartition("__").last, r["step"], r["mode"]].compact.join("/")
end

# Source trial ID => the ID of its restart, over all run directories (runs-deprecated/ and ../ai-evals too).
# A restart carries the source's settled steps (and the reverified step), so the source does not count again.
def superseded_by(trial)
  @superseded ||= Dir["{#{ROOT}/runs,#{ROOT}/runs-deprecated,#{AI_EVALS}/*}/*/*/result.json"].each_with_object({}) do |f, h|
    source = restarted_from(File.dirname(f)) or next
    h[source.split("/").first] = File.basename(File.dirname(f)).rpartition("__").last
  end
  @superseded[trial]
end

# Reports skip superseded restart sources always, and deprecated trials unless DEPRECATED=1
def keep_trial?(trial) = !superseded_by(trial) && (ENV["DEPRECATED"] == "1" || !DEPRECATED.key?(trial))

# ft-i18n-support #herb and #erbx: the instruction text of a trial. "how-to": the 3-step how-to (2026-10-28 to 10-31);
# "hook": the one-line hint and hook, with the limits in AGENTS.md (from 2026-11-01). nil for plain.
I18N_HOOK = /set up (?:Herb|erbx).{0,80}?\(it's in AGENTS\.md\)\.\s+Before\s+you\s+hand/m

def i18n_text(dir)
  return unless File.basename(dir).match?(/\Aft-i18n-support-(herb|erbx)__/)
  steps = load_json("#{dir}/trajectory.json")&.fetch("steps", nil) || []
  steps.first(3).any? { I18N_HOOK.match?(_1["message"].to_s) } ? "hook" : "how-to"
end
