# Compares the rules' categories with a blind labeler's on 60 steps.
#
# The 60 steps (labels/blind_check/sample.jsonl) were drawn at random with
# probability proportional to their time. A separate model labeled them from
# the command and output alone, without seeing rule_labels.json, and marked
# each label sure or unsure.
#
# Usage (from static-typing/ruby-vs-rust): ruby analysis/score_blind_check.rb
require "json"
require "csv"
require_relative "rules"

dir = File.join(__dir__, "..", "labels", "blind_check")
rules = JSON.parse(File.read(File.join(dir, "rule_labels.json")))
blind = JSON.parse(File.read(File.join(dir, "blind_labels.json")))
sure = JSON.parse(File.read(File.join(dir, "blind_confidence.json")))
group = GROUPS.flat_map { |g, cs| cs.map { [_1, g] } }.to_h
group.default = "Other"

ids = rules.keys
strict = ids.count { rules[_1] == blind[_1] }
grouped = ids.count { group[rules[_1]] == group[blind[_1]] }
sure_ids = ids.select { sure[_1] == "sure" }
puts "steps: #{ids.size}"
puts "same category: #{strict} (#{(100.0 * strict / ids.size).round}%)"
puts "same group: #{grouped} (#{(100.0 * grouped / ids.size).round}%)"
puts "when the labeler was sure (#{sure_ids.size}): category #{sure_ids.count { rules[_1] == blind[_1] }}, group #{sure_ids.count { group[rules[_1]] == group[blind[_1]] }}"
puts "\nGroup counts, rules vs blind:"
(GROUPS.keys).each { |g| puts format("  %-11s %2d  %2d", g, ids.count { group[rules[_1]] == g }, ids.count { group[blind[_1]] == g }) }
puts "\nDisagreements:"
ids.reject { rules[_1] == blind[_1] }.each { puts "  step #{_1}: rules #{rules[_1]}, blind #{blind[_1]} (#{sure[_1]})" }
