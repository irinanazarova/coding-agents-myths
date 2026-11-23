# Renders the charts used in the blog post from the result files:
#   ruby-vs-rust/results/per_run.csv, ruby-vs-rust/results/activity.csv,
#   benchmarks/results/same_difficulty.json
# Usage (from static-typing): ruby charts/charts.rb
require "csv"
require "json"
ROOT = File.expand_path("..", __dir__)
OUT = __dir__
W = 960
FONT = %q('Martian Grotesk', 'Inter', Arial, sans-serif)
GREEN = "#a8fe69" # Ruby / dynamic
PINK = "#ff6ec7"  # Rust / typed
L0 = 300          # plot left edge
L1 = 860          # plot right edge

def esc(s) = s.to_s.gsub("&", "&amp;").gsub("<", "&lt;").gsub(">", "&gt;")

def header(h, title, sub, legend)
  s = +%(<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 #{W} #{h}" font-family="#{FONT}">\n)
  s << %(<rect width="#{W}" height="#{h}" fill="#000000"/>\n)
  s << %(<text x="48" y="44" fill="#ffffff" font-size="22" font-weight="800" font-stretch="125%">#{esc title}</text>\n)
  s << %(<text x="48" y="68" fill="#777777" font-size="12" font-stretch="75%" letter-spacing="0.02em">#{esc sub.upcase}</text>\n)
  x = 48
  (legend.size > 1 ? legend : []).each do |name, color|
    s << %(<rect x="#{x}" y="84" width="12" height="12" rx="3" fill="#{color}"/>\n)
    s << %(<text x="#{x + 18}" y="94" fill="#bbbbbb" font-size="12" font-stretch="75%">#{esc name}</text>\n)
    x += 44 + name.length * 8
  end
  s
end

def axis(s, top, bottom, max, step, unit)
  (0..max).step(step).each do |v|
    x = L0 + (L1 - L0) * v / max.to_f
    s << %(<line x1="#{x}" y1="#{top}" x2="#{x}" y2="#{bottom}" stroke="#1f1f1f" stroke-width="1"/>\n)
    s << %(<text x="#{x}" y="#{bottom + 18}" fill="#555555" font-size="10" text-anchor="middle" font-stretch="75%">#{v}#{unit}</text>\n)
  end
end

def bar(s, x0, y, w, h, color, label)
  w = [w, 2].max
  s << %(<rect x="#{x0}" y="#{y}" width="#{w}" height="#{h}" rx="3" fill="#{color}"/>\n)
  s << %(<text x="#{x0 + w + 6}" y="#{y + h - 1}" fill="#bbbbbb" font-size="11" font-stretch="75%">#{esc label}</text>\n)
end

# panels: [[panel title, [[row label, [v1, v2, ...], [label1, label2, ...]?], ...]], ...]
WHOLE = ->(v) { v.zero? ? "0%" : v < 1 ? "<1%" : "#{v.round}%" }
HIGHLIGHT = "#ffd34d"

# A row label starting with "!" is drawn highlighted, without the "!".
def grouped(file, title, sub, series, panels, max:, step:, unit: "%", fmt: WHOLE, note: nil)
  bh = 11; gap = 2; nb = panels.flat_map { _2 }.map { _2.size }.max; row = nb * (bh + gap) + 12; ph = 34
  top = 120
  h = top + panels.sum { |_, rows| ph + rows.size * row } + 50 + (note ? 16 * Array(note).size + 8 : 0)
  s = header(h, title, sub, series)
  bottom = h - 50 - (note ? 16 * Array(note).size + 8 : 0)
  axis(s, top, bottom, max, step, unit)
  y = top
  panels.each do |ptitle, rows|
    s << %(<text x="48" y="#{y + 22}" fill="#ffffff" font-size="13" font-weight="700" font-stretch="100%">#{esc ptitle}</text>\n)
    y += ph
    rows.each do |label, vals, labels, colors|
      hl = label.start_with?("!")
      label = label.delete_prefix("!")
      s << %(<text x="#{L0 - 12}" y="#{y + row / 2 - 1}" fill="#{hl ? HIGHLIGHT : "#dddddd"}" font-size="12" font-weight="#{hl ? 700 : 400}" text-anchor="end" font-stretch="75%">#{esc label}</text>\n)
      vals.each_with_index do |v, i|
        bar(s, L0, y + i * (bh + gap), (L1 - L0) * v / max.to_f, bh, colors ? colors[i] : series[i][1], labels ? labels[i] : fmt.(v))
      end
      y += row
    end
  end
  Array(note).each_with_index { |ln, i| s << %(<text x="48" y="#{h - 16 * Array(note).size + 16 * i - 6}" fill="#666666" font-size="11" font-stretch="75%">#{esc ln}</text>\n) }
  s << "</svg>\n"
  File.write(File.join(OUT, file), s)
end

RR = [["Ruby on Rails", GREEN], ["Rust", PINK]]

NAMES = {
  "claude-opus-5.5" => "Claude Opus 5.5", "deepseek-v4.1-flash-max" => "DeepSeek V4.1 Flash",
  "gpt-6-astra-medium" => "GPT-6 Astra (medium)", "gpt-6-astra-xhigh" => "GPT-6 Astra (xhigh)",
  "gpt-6-luna-max" => "GPT-6 Luna", "gpt-6.1-sol-xhigh" => "GPT-6.1 Sol", "kimi-k3-max" => "Kimi K3",
  "muse-spark-1.3-max" => "Muse Spark 1.3", "gpt-6-astra" => "GPT-6 Astra", "muse-spark-1.3" => "Muse Spark 1.3",
  "gemini-3.8-flash" => "Gemini 3.8 Flash"
}
TASKS = [["quizzy", "Greenfield app: built from scratch"], ["campfire", "Campfire: a feature in an existing app"]]

per_run = CSV.read(File.join(ROOT, "ruby-vs-rust/results/per_run.csv"), headers: true).map(&:to_h)
pair = ->(task, &val) do
  models = per_run.select { _1["task"] == task }.map { _1["model"] }.uniq
  models.map do |m|
    ruby = per_run.find { _1["task"] == task && _1["model"] == m && _1["stack"] == "Ruby" }
    rust = per_run.find { _1["task"] == task && _1["model"] == m && _1["stack"] == "Rust" }
    [NAMES.fetch(m, m), ruby, rust]
  end
end

grouped("type-error-time.svg",
  "How much time did type errors cost?",
  "Share of agent time: Ruby type errors vs Rust compiler errors",
  RR,
  TASKS.map { |t, title| [title, pair.(t).map { |n, a, b| [n, [a["error_pct"].to_f, b["error_pct"].to_f]] }] },
  max: 5, step: 1, fmt: ->(v) { format("%.1f%%", v) },
  note: ["Ruby: NoMethodError, NameError, ArgumentError and TypeError in app or test code, each read by hand.", "Rust: any rustc diagnostic with an error code, including borrow errors. One run per model and stack."])

activity = CSV.read(File.join(ROOT, "ruby-vs-rust/results/activity.csv"), headers: true).to_h { [_1["category"], _1] }
# Concrete activities, largest groups first; "!" highlights the row the post is about.
ROWS = [
  ["Read the project's code", %w[read_code read_gems]],
  ["Run tests", %w[run_tests]],
  ["Try the app, by hand or with scripts", %w[manual_verify probe_runtime]],
  ["Write code and tests", %w[write_code write_tests]],
  ["Compile (Rust only)", %w[compile]],
  ["Lint and review the diff", %w[lint git_wrap]],
  ["Fix failing tests", %w[fix_logic]],
  ["!Fix type and borrow errors", %w[fix_typing fix_ownership]],
  ["Fix other errors", %w[fix_wiring fix_schema fix_syntax]],
  ["Plumbing: setup, hung commands, time limits", %w[env_setup shell_mechanics slow_timeouts logs_rerun internet]]
]
# Minutes, not shares: the same models ran both stacks (8 on the greenfield app, 4 on Campfire,
# one run each), so the average minutes per run compare like for like.
steps = CSV.read(File.join(ROOT, "ruby-vs-rust/results/steps.csv"), headers: true).map(&:to_h)
runs_of = ->(task, stack) { steps.select { _1["task"] == task && _1["stack"] == stack }.map { [_1["model"], _1["trial"]] }.uniq.size }
minutes = lambda do |task, stack, cats|
  steps.select { _1["task"] == task && _1["stack"] == stack && cats.include?(_1["category"]) }.sum { _1["seconds"].to_f } / 60.0 / runs_of.(task, stack)
end
total = ->(task, stack) { steps.select { _1["task"] == task && _1["stack"] == stack }.sum { _1["seconds"].to_f } / 60.0 / runs_of.(task, stack) }
MIN = ->(v) { v.zero? ? "0" : v < 1 ? "<1 min" : "#{v.round} min" }
grouped("agent-time-by-activity.svg",
  "Where did the agents spend their time?",
  "Average minutes per run, same models on both stacks",
  RR,
  TASKS.map { |t, title|
    ["#{title.split(':').first}: #{total.(t, 'Ruby').round} min per run on Rails, #{total.(t, 'Rust').round} on Rust",
     ROWS.map { |name, cats| [name, [minutes.(t, "Ruby", cats), minutes.(t, "Rust", cats)]] }]
  },
  max: 45, step: 15, unit: " min", fmt: MIN,
  note: ["Greenfield app: 8 model configurations, Campfire: 4 models, one run per stack. Each step is classified by rules over its command and output.",
         "Not a ranking of the stacks: the Rust Campfire port is an AI-written rewrite with nearly 13 times the code, and the Rust sandbox had twice the CPU and memory."])

grouped("cargo-check-sessions.svg",
  "How often did Rust agents run cargo check?",
  "Share of agent sessions that ran cargo check or cargo clippy",
  [["Rust sessions", PINK]],
  TASKS.map { |t, title| [title, pair.(t).map { |n, _, b| c, s = b["cargo_check_sessions"].to_i, b["sessions"].to_i; [n, [100.0 * c / s], ["#{c} of #{s}"]] }] },
  max: 100, step: 25,
  note: ["Every Rust session also ran cargo build or cargo test, which type-check too.", "A session is one of the task's consecutive feature requests."])

sd = JSON.parse(File.read(File.join(ROOT, "benchmarks/results/same_difficulty.json")))
mix = sd["typed_vs_dynamic"]["fix size"]
langs = ->(typed) { sd["languages"].select { _1["typed"] == typed }.sort_by { -_1["same_mix"] } }
label = ->(l, first) { first ? "#{l['language']} (#{l['tasks']} tasks)" : "#{l['language']} (#{l['tasks']})" }
# Python comes from SWE-bench Verified (scripts/python_same_mix.py): same agent and month, 11 of the 13 models.
py = JSON.parse(File.read(File.join(ROOT, "benchmarks/results/python_same_mix.json")))
py_row = { "language" => "Python, Verified*", "tasks" => py["groups"]["Python (SWE-bench Verified)"]["tasks"],
           "same_mix" => py["groups"]["Python (SWE-bench Verified)"]["same_mix"] }
py_typed = py["groups"]["Typed (Multilingual)"]["same_mix"].round
py_dynamic = py["groups"]["Dynamic (Multilingual)"]["same_mix"].round
grouped("swe-bench-multilingual-by-language.svg",
  "At the same difficulty, do typed languages win?",
  "SWE-bench Multilingual plus Python from SWE-bench Verified, same patch-size mix",
  [["Statically typed", PINK], ["Dynamically typed", GREEN]],
  [["Statically typed: #{(mix['dynamic'] - mix['dynamic_minus_typed']).round}% overall", langs.(true).each_with_index.map { |l, i| [label.(l, i.zero?), [l["same_mix"]]] }],
   ["Dynamically typed: #{mix['dynamic'].round}% overall", (langs.(false) + [py_row]).sort_by { -_1["same_mix"] }.map { |l| [label.(l, false), [l["same_mix"]], nil, [GREEN]] }]],
  max: 80, step: 20,
  note: ["Each language reweighted to the benchmark's mix of small (up to #{sd['cuts']['small_max_lines']} lines), medium (#{sd['cuts']['small_max_lines'] + 1} to #{sd['cuts']['medium_max_lines']}) and large fixes.",
         "Patch size is a proxy: the benchmark publishes no difficulty labels. C++ and TypeScript have 3 to 6 tasks per level.",
         "Mean of 13 models. *Python: SWE-bench Verified, the #{py['models'].size} of them that ran it with the same agent; with those #{py['models'].size}, typed #{py_typed}%, dynamic #{py_dynamic}%."])
puts "wrote #{Dir[File.join(OUT, '*.svg')].size} charts to charts/"
