# Finds every Rails-run step whose output mentions an error a type checker
# could catch, and checks that labels/ruby_error_steps.csv labels exactly
# those steps. The labels themselves were assigned by reading each step:
#   app_type_error       a type error in application code
#   test_type_error      a type error in a test the agent kept
#   deliberate_red_test  a test written to fail before the feature existed
#   throwaway_script     a browser script, one-off probe, or file-editing one-liner
#   not_a_type_error     a match for another reason (missing tool, syntax error, docs)
# Only the first two count as type errors in the post.
#
# Usage (from static-typing/ruby-vs-rust): ruby analysis/find_ruby_errors.rb
require "csv"
require "json"

ROOT = File.expand_path("..", __dir__)
TYPE_ERROR = /NoMethodError|undefined method [`'"]|undefined local variable or method|uninitialized constant|NameError|wrong number of arguments|no implicit conversion|TypeError \(|\(TypeError\)|ArgumentError/
JS_NOISE = /Cannot read propert|is not a function|Uncaught|is not defined/

def output_text(step)
  (step.dig("observation", "results") || []).map do |r|
    c = r["content"].to_s
    d = (JSON.parse(c) rescue c)
    d.is_a?(Hash) ? d.values_at("output", "output_head", "output_tail", "error").compact.join("\n") : c
  end.join("\n")
end

found = []
CSV.foreach(File.join(ROOT, "runs.csv"), headers: true) do |run|
  next unless run["stack"] == "rails"
  Dir[File.join(ROOT, run["path"], "trajectory.*.json")].each do |tp|
    session = tp[/\.(\d+)\.json/, 1].to_i
    JSON.parse(File.read(tp))["steps"].each do |s|
      next unless s["source"] == "agent"
      hit = output_text(s).lines.any? { |l| l.match?(TYPE_ERROR) && !l.match?(JS_NOISE) }
      found << [run["trial"], session, s["step_id"]] if hit
    end
  end
end

labels = CSV.read(File.join(ROOT, "labels", "ruby_error_steps.csv"), headers: true)
labeled = labels.map { [_1["trial"], _1["session"].to_i, _1["step"].to_i] }
missing = found - labeled
extra = labeled - found
puts "#{found.size} candidate steps found, #{labeled.size} labeled"
puts "labels: #{labels.map { _1['label'] }.tally.sort_by { -_2 }.map { "#{_1} #{_2}" }.join(', ')}"
abort "unlabeled steps: #{missing.inspect}" if missing.any?
abort "labels for steps no longer found: #{extra.inspect}" if extra.any?
puts "every candidate is labeled"
