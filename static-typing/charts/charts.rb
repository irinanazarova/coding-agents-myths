# Renders the charts used in the blog post from the result files:
#   ruby-vs-rust/results/per_run.csv, ruby-vs-rust/results/activity.csv,
#   benchmarks/results/same_difficulty.json
# Usage (from static-typing): ruby charts/charts.rb
require "csv"
require "json"
require "base64"
ROOT = File.expand_path("..", __dir__)
OUT = __dir__
W = 960
FONT = %q('Martian Grotesk', 'Inter', Arial, sans-serif)
# Colors from the post's cover illustration: a cream clay world with the Ruby gem,
# the TS and JS cubes, and the orange of the Martian's sunglasses.
BG, INK, MUTED, GRID = "#F8ECD6", "#3A2A1C", "#9A846C", "#E9D9BF"
RUBY_RED, RUST_ORANGE = "#D63A5A", "#E8743B"   # Rails / Rust
TYPED_BLUE, DYN_YELLOW = "#3D86D6", "#F2C230"  # statically / dynamically typed
HIGHLIGHT = "#E8590C"
# Every chart carries its source, so it still points back when shared on its own.
POST_URL = "evilmartians.com/chronicles/type-errors-cost-our-coding-agents-under-one-percent-of-their-time"
PUBLISHED = "November 2026"
L0 = 330          # plot left edge
L1 = 860          # plot right edge

def esc(s) = s.to_s.gsub("&", "&amp;").gsub("<", "&lt;").gsub(">", "&gt;")
def shade(hex, f) = "#" + hex.delete("#").scan(/../).map { |c| (c.hex * f).round.clamp(0, 255).to_s(16).rjust(2, "0") }.join

# Language cubes, like the blocks on the cover's scale: face color, letter color, letters.
CUBES = {
  "Rust" => ["#E8743B", "#fff", "RS"], "Java" => ["#C8553D", "#fff", "JV"], "C" => ["#6C7FA8", "#fff", "C"],
  "C++" => ["#5B6FB5", "#fff", "C++"], "TypeScript" => ["#3D86D6", "#fff", "TS"], "Go" => ["#4FB7D6", "#fff", "GO"],
  "PHP" => ["#8A7FC8", "#fff", "PHP"], "Python" => ["#3A6EA5", "#FFD54A", "PY"], "JavaScript" => ["#F2C230", "#3A2A1C", "JS"]
}

def cube(x, y, lang)
  if lang == "Ruby" # the Ruby gem from the cover
    cx = x + 13; t = y + 4
    return %(<g filter="url(#clay)"><path d="M#{cx - 12} #{t + 6} l5 -6 h14 l5 6 l-12 16 z" fill="#{RUBY_RED}"/>) +
           %(<path d="M#{cx - 12} #{t + 6} h24 l-12 16 z" fill="#B82645"/><path d="M#{cx - 7} #{t} l3 6 h8 l3 -6 z" fill="#F07A92"/></g>)
  end
  face, txt, letters = CUBES.fetch(lang)
  sz = 22; d = 5
  %(<g filter="url(#clay)"><path d="M#{x} #{y + d} l#{d} -#{d} h#{sz} l-#{d} #{d} z" fill="#{shade(face, 1.25)}"/>) +
    %(<path d="M#{x + sz} #{y + d} l#{d} -#{d} v#{sz} l-#{d} #{d} z" fill="#{shade(face, 0.75)}"/>) +
    %(<rect x="#{x}" y="#{y + d}" width="#{sz}" height="#{sz}" rx="3" fill="#{face}"/>) +
    %(<text x="#{x + sz / 2.0}" y="#{y + d + sz / 2.0 + 4}" fill="#{txt}" font-size="#{letters.size > 2 ? 8 : 10}" font-weight="800" text-anchor="middle">#{esc letters}</text></g>)
end

# A character from charts/characters, embedded so the SVG works inside an <img>.
def character(name, x, y, w)
  path = File.join(OUT, "characters", "#{name}.webp")
  iw, ih = File.binread(path)[26, 4].unpack("v2") rescue [nil, nil]
  dims = `magick identify -format '%w %h' #{path} 2>/dev/null`.split.map(&:to_i)
  iw, ih = dims if dims.size == 2
  h = (w * ih.to_f / iw).round
  %(<image href="data:image/webp;base64,#{Base64.strict_encode64(File.binread(path))}" x="#{x}" y="#{y}" width="#{w}" height="#{h}"/>\n)
end

def header(h, title, sub, legend)
  s = +%(<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 #{W} #{h}" font-family="#{FONT}">\n)
  s << %(<defs><filter id="clay" x="-20%" y="-20%" width="140%" height="170%"><feDropShadow dx="0" dy="2.5" stdDeviation="1.6" flood-color="#7A5230" flood-opacity="0.28"/></filter>)
  s << %(<linearGradient id="sheen" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0.45"/><stop offset="0.55" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>\n)
  s << %(<rect width="#{W}" height="#{h}" rx="28" fill="#{BG}"/>\n)
  s << %(<text x="48" y="54" fill="#{INK}" font-size="26" font-weight="800" font-stretch="125%">#{esc title}</text>\n)
  s << %(<text x="48" y="80" fill="#{MUTED}" font-size="12" font-stretch="75%" letter-spacing="0.03em">#{esc sub.upcase}</text>\n)
  x = 48
  (legend.size > 1 ? legend : []).each do |name, color|
    s << %(<rect x="#{x}" y="96" width="14" height="14" rx="7" fill="#{color}" filter="url(#clay)"/>\n)
    s << %(<text x="#{x + 20}" y="108" fill="#{INK}" font-size="12" font-stretch="85%">#{esc name}</text>\n)
    x += 48 + name.length * 8
  end
  s
end

def axis(s, top, bottom, max, step, unit)
  (0..max).step(step).each do |v|
    x = L0 + (L1 - L0) * v / max.to_f
    s << %(<line x1="#{x}" y1="#{top}" x2="#{x}" y2="#{bottom}" stroke="#{GRID}" stroke-width="1.5" #{v.zero? ? '' : 'stroke-dasharray="2 5" '}stroke-linecap="round"/>\n)
    s << %(<text x="#{x}" y="#{bottom + 20}" fill="#{MUTED}" font-size="11" text-anchor="middle" font-stretch="75%">#{v}#{unit}</text>\n)
  end
end

def bar(s, x0, y, w, h, color, label)
  w = [w, h].max # a stub stays a round clay bead
  s << %(<g filter="url(#clay)"><rect x="#{x0}" y="#{y}" width="#{w}" height="#{h}" rx="#{h / 2.0}" fill="#{color}"/><rect x="#{x0}" y="#{y}" width="#{w}" height="#{h}" rx="#{h / 2.0}" fill="url(#sheen)"/></g>\n)
  s << %(<text x="#{x0 + w + 7}" y="#{y + h - 2}" fill="#{INK}" font-size="11.5" font-weight="700" font-stretch="85%">#{esc label}</text>\n)
end

# panels: [[panel title, [[row label, [v1, v2, ...], [label1, ...]?, [color1, ...]?, cube?], ...]], ...]
WHOLE = ->(v) { v.zero? ? "0%" : v < 1 ? "<1%" : "#{v.round}%" }

# A row label starting with "!" is drawn highlighted, without the "!".
# character: [name, x, y, width] places one of charts/characters on the card.
def grouped(file, title, sub, series, panels, max:, step:, unit: "%", fmt: WHOLE, note: nil, character: nil, data: nil)
  nb = panels.flat_map { _2 }.map { _2.size }.max
  bh = nb > 1 ? 13 : 18; gap = 3; row = nb * (bh + gap) + 14; ph = 40
  top = 124
  notes = Array(note)
  h = top + panels.sum { |_, rows| ph + rows.size * row } + 54 + (notes.empty? ? 0 : 17 * notes.size + 6) + 50
  s = header(h, title, sub, series)
  bottom = h - 50 - 54 - (notes.empty? ? 0 : 17 * notes.size + 6)
  axis(s, top, bottom, max, step, unit)
  y = top
  panels.each do |ptitle, rows|
    s << %(<text x="48" y="#{y + 26}" fill="#{INK}" font-size="15" font-weight="800">#{esc ptitle}</text>\n)
    y += ph
    rows.each do |label, vals, labels, colors, lang|
      hl = label.start_with?("!")
      label = label.delete_prefix("!")
      lx = lang ? L0 - 50 : L0 - 14
      s << %(<text x="#{lx}" y="#{y + row / 2 - 2}" fill="#{hl ? HIGHLIGHT : INK}" font-size="13" font-weight="#{hl ? 800 : 400}" text-anchor="end" font-stretch="85%">#{esc label}</text>\n)
      s << cube(L0 - 40, y + row / 2 - 20, lang) << "\n" if lang
      vals.each_with_index do |v, i|
        bar(s, L0, y + i * (bh + gap), (L1 - L0) * v / max.to_f, bh, colors ? colors[i] : series[i][1], labels ? labels[i] : fmt.(v))
      end
      y += row
    end
  end
  notes.each_with_index { |ln, i| s << %(<text x="48" y="#{h - 50 - 17 * notes.size + 17 * i - 14}" fill="#{MUTED}" font-size="11" font-stretch="80%">#{esc ln}</text>\n) }
  s << %(<line x1="48" y1="#{h - 56}" x2="#{W - 48}" y2="#{h - 56}" stroke="#{GRID}" stroke-width="1.5"/>\n)
  s << %(<text x="48" y="#{h - 34}" fill="#{INK}" font-size="11.5" font-weight="700" font-stretch="85%">Evil Martians, #{PUBLISHED}#{data ? %(<tspan fill="#{MUTED}" font-weight="400"> · data from #{esc data}</tspan>) : ""}</text>\n)
  s << %(<a href="https://#{POST_URL}"><text x="48" y="#{h - 16}" fill="#{MUTED}" font-size="11" font-stretch="80%">#{esc POST_URL}</text></a>\n)
  s << character(*character) if character
  s << "</svg>\n"
  File.write(File.join(OUT, file), s)
end

RR = [["Ruby on Rails", RUBY_RED], ["Rust", RUST_ORANGE]]

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
  note: ["Ruby: NoMethodError, NameError, ArgumentError and TypeError in app or test code, each read by hand.", "Rust: any rustc diagnostic with an error code, including borrow errors. One run per model and stack."],
  character: ["martian-bug", 742, 8, 190], data: "October 2026 runs")

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
         "Not a ranking of the stacks: the Rust Campfire port is an AI-written rewrite with nearly 13 times the code, and the Rust sandbox had twice the CPU and memory."],
  character: ["robot-printouts", 790, 10, 135], data: "October 2026 runs")

grouped("cargo-check-sessions.svg",
  "How often did Rust agents run cargo check?",
  "Share of agent sessions that ran cargo check or cargo clippy",
  [["Rust sessions", RUST_ORANGE]],
  TASKS.map { |t, title| [title, pair.(t).map { |n, _, b| c, s = b["cargo_check_sessions"].to_i, b["sessions"].to_i; [n, [100.0 * c / s], ["#{c} of #{s}"]] }] },
  max: 100, step: 25,
  note: ["Every Rust session also ran cargo build or cargo test, which type-check too.", "A session is one of the task's consecutive feature requests."])

sd = JSON.parse(File.read(File.join(ROOT, "benchmarks/results/same_difficulty.json")))
mix = sd["typed_vs_dynamic"]["fix size"]
langs = ->(typed) { sd["languages"].select { _1["typed"] == typed }.sort_by { -_1["same_mix"] } }
label = ->(l, first) { first ? "#{l['language']} (#{l['tasks']} tasks)" : "#{l['language']} (#{l['tasks']})" }
cube_of = ->(l) { l["language"].start_with?("Python") ? "Python" : l["language"] }
# Python comes from SWE-bench Verified (scripts/python_same_mix.py): same agent and month, 11 of the 13 models.
py = JSON.parse(File.read(File.join(ROOT, "benchmarks/results/python_same_mix.json")))
py_row = { "language" => "Python, Verified*", "tasks" => py["groups"]["Python (SWE-bench Verified)"]["tasks"],
           "same_mix" => py["groups"]["Python (SWE-bench Verified)"]["same_mix"] }
py_typed = py["groups"]["Typed (Multilingual)"]["same_mix"].round
py_dynamic = py["groups"]["Dynamic (Multilingual)"]["same_mix"].round
grouped("swe-bench-multilingual-by-language.svg",
  "Do typed languages win?",
  "At the same difficulty: SWE-bench Multilingual plus Python from SWE-bench Verified",
  [["Statically typed", TYPED_BLUE], ["Dynamically typed", DYN_YELLOW]],
  [["Statically typed: #{(mix['dynamic'] - mix['dynamic_minus_typed']).round}% overall", langs.(true).each_with_index.map { |l, i| [label.(l, i.zero?), [l["same_mix"]], nil, [TYPED_BLUE], cube_of.(l)] }],
   ["Dynamically typed: #{mix['dynamic'].round}% overall", (langs.(false) + [py_row]).sort_by { -_1["same_mix"] }.map { |l| [label.(l, false), [l["same_mix"]], nil, [DYN_YELLOW], cube_of.(l)] }]],
  max: 80, step: 20,
  note: ["Each language reweighted to the benchmark's mix of small (up to #{sd['cuts']['small_max_lines']} lines), medium (#{sd['cuts']['small_max_lines'] + 1} to #{sd['cuts']['medium_max_lines']}) and large fixes.",
         "Patch size is a proxy: the benchmark publishes no difficulty labels. C++ and TypeScript have 3 to 6 tasks per level.",
         "Mean of 13 models. *Python: SWE-bench Verified, the #{py['models'].size} of them that ran it with the same agent; with those #{py['models'].size}, typed #{py_typed}%, dynamic #{py_dynamic}%."],
  character: ["martian-magnifier", 800, 2, 140], data: "February 2026 runs")
puts "wrote #{Dir[File.join(OUT, '*.svg')].size} charts to charts/"
