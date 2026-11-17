# Rules that sort each agent step into an activity category.
# Categories follow the Agents on Rails "where agent time went" taxonomy,
# plus two Rust-only ones: compile and fix_ownership.
# A step is one shell command the agent ran, with its output and exit code.
require "csv"

GROUPS = {
  "Understand" => %w[read_code read_gems],
  "Build" => %w[write_code write_tests],
  "Verify" => %w[run_tests compile probe_runtime manual_verify lint git_wrap],
  "Recover" => %w[fix_logic fix_typing fix_ownership fix_wiring fix_schema fix_syntax],
  "Plumbing" => %w[env_setup shell_mechanics slow_timeouts logs_rerun internet],
  "Other" => %w[other]
}
NAMES = {
  "read_code" => "Read project code", "read_gems" => "Read framework and library source",
  "write_code" => "Write app code and docs", "write_tests" => "Write tests",
  "run_tests" => "Run tests and wait for them", "compile" => "Compile and type-check (Rust)",
  "probe_runtime" => "Throwaway scripts and runtime probes", "manual_verify" => "Start a server and try it by hand",
  "lint" => "Lint and static checks", "git_wrap" => "Git review and wrap-up",
  "fix_logic" => "Fix failing assertions", "fix_typing" => "Fix type errors",
  "fix_ownership" => "Fix borrow and lifetime errors (Rust)", "fix_wiring" => "Fix framework wiring and test-data errors",
  "fix_schema" => "Fix database and schema errors", "fix_syntax" => "Fix syntax errors",
  "env_setup" => "Environment wrangling", "shell_mechanics" => "Failed or hung shell and edit commands",
  "slow_timeouts" => "Commands killed at the time limit", "logs_rerun" => "Read logs, re-run with no change",
  "internet" => "Internet and upstream attempts", "other" => "Other"
}
# Hand-labeled Ruby type errors in app or kept test code: labels/ruby_error_steps.csv
RUBY_TYPE = CSV.read(File.join(__dir__, "..", "labels", "ruby_error_steps.csv"), headers: true)
  .select { %w[app_type_error test_type_error].include?(_1["label"]) }
  .group_by { _1["trial"] }.transform_values { |rs| rs.map { [_1["session"].to_i, _1["step"].to_i] } }
OWNERSHIP = /error\[E(?:0382|0499|0502|0505|0506|0507|0515|0597|0716|0521|0373|0106|0495|0621)\]|does not live long enough|borrowed value|use of moved value|cannot be sent between threads/
RUSTC = /error\[E\d{4}\]/
RUST_SYNTAX = /^error: (?:expected|unexpected|mismatched closing|this file contains an unclosed)/
SYNTAX = /SyntaxError|syntax error|unexpected end-of-input|syntax errors found/
SCHEMA = /StatementInvalid|PendingMigrationError|no such (?:column|table)|UnknownAttributeError|NOT NULL constraint|UNIQUE constraint|duplicate column|SQLITE_ERROR|migration/i
WIRING = /RoutingError|No route matches|ActionView::Template::Error|ActiveRecord::Fixture|FixtureSet|RecordNotFound|uninitialized constant|unresolved import|E0432|E0433|missing template/
TEST_FAIL = /\b[1-9]\d* (?:failures|errors)\b|test result: FAILED|\bFAILED\b|panicked at|Failure:|Error:\n/
TEST_CMD = /\b(?:bin\/rails|rails|rake)\s+test|bundle exec (?:rspec|rake)|\brspec\b|cargo\s+(?:\+\S+\s+)?(?:test|nextest)|bin\/ci\b|ruby -Itest/
COMPILE_CMD = /cargo\s+(?:\+\S+\s+)?(?:build|check)\b/
LINT_CMD = /rubocop|brakeman|cargo\s+clippy|cargo\s+fmt|rustfmt|ruby -c\b|erb_lint|standardrb/
SERVER_CMD = /bin\/serve|rails\s+s(?:erver)?\b|\bpuma\b|cargo\s+run|bin\/dev|curl[^|;]*(?:localhost|127\.0\.0\.1|:3000)/
PROBE_CMD = /ferrum|cuprite|capybara|chromium|rails runner|\bruby\s+(?:-e|-\s|<<|\/tmp)|python3?\s+(?:-c|\/tmp)|node\s+-e|\/tmp\/\S+\.(?:rb|py|js)/
ENV_CMD = /apt(?:-get)?\s+install|bundle\s+(?:install|add|update)|gem\s+install|cargo\s+(?:install|add|update|fetch)|rustup|npm\s+(?:install|i)\b|pip install|db:(?:create|setup|prepare)|\bwhich\b|--version|ulimit|df -h|chmod|mkdir -p|export PATH/
NET_CMD = /git\s+clone|curl[^|;]*https?:\/\/(?!localhost|127\.0\.0\.1)|wget|crates\.io|rubygems\.org/
GIT_CMD = /\bgit\s+(?:diff|status|log|show|add|commit|stash)/
LOG_CMD = /(?:cat|tail|less|grep)[^|;]*(?:\/tmp\/\S+\.log|log\/\S+\.log|\.log\b)/
WRITE_CMD = /write_text\(|open\([^)]*,\s*["']w|\.replace\(|cat\s*>|cat\s*<<|tee\s|sed\s+-i|apply_patch|File\.write|>\s*\S+\.(?:rb|rs|erb|js|css|yml|md|toml|html)|perl\s+-pi|patch\s+-p/
TEST_PATH = /(?:^|[\s\/'"])(?:test|tests|spec)\/|_test\.rb|_spec\.rb|tests?\.rs|\/tests\//
GEM_PATH = /\/usr\/local\/bundle|bundle\s+(?:show|info|exec gem contents)|gem\s+contents|Gem::Specification|\.cargo\/registry|~\/\.cargo|rustup doc|cargo doc|\/gems\//
READ_CMD = /\b(?:cat|sed\s+-n|head|tail|grep|rg|find|ls|tree|wc|nl|awk)\b/

def classify(r)
  cmd = r["command"].to_s; out = r["output_head"].to_s; rc = r["returncode"].to_i
  rust = r["stack"] == "Rust"
  failed = rc != 0 || out.match?(TEST_FAIL)
  # Recover: a run that surfaced an error of this family
  if rust && cmd.match?(/cargo|rustc/)
    return "fix_ownership" if out.match?(OWNERSHIP)
    return "fix_syntax" if out.match?(RUST_SYNTAX)
    return "fix_wiring" if out.match?(/E0432|E0433/) && !out.match?(/E0(?:308|599|061|277|609|560|063|004|425|412|614|369)/)
    return "fix_typing" if out.match?(RUSTC)
  end
  return "fix_typing" if !rust && (RUBY_TYPE[r["trial"]] || []).include?([r["session"].to_i, r["step"].to_i])
  if failed && cmd.match?(TEST_CMD)
    return "fix_syntax" if out.match?(SYNTAX)
    return "fix_schema" if out.match?(SCHEMA)
    return "fix_wiring" if out.match?(WIRING)
    return "fix_logic" if out.match?(TEST_FAIL)
  end
  # Plumbing
  return "shell_mechanics" if rc == 127 || out.match?(/command not found|No such file or directory \(os error|unterminated quoted string|bad substitution/)
  return "slow_timeouts" if [124, 137, 143].include?(rc)
  return "internet" if cmd.match?(NET_CMD)
  # Verify
  return "run_tests" if cmd.match?(TEST_CMD)
  return "compile" if cmd.match?(COMPILE_CMD)
  return "lint" if cmd.match?(LINT_CMD)
  return "env_setup" if cmd.match?(ENV_CMD) && !cmd.match?(WRITE_CMD)
  return "manual_verify" if cmd.match?(SERVER_CMD)
  return "probe_runtime" if cmd.match?(PROBE_CMD) && !cmd.match?(/File\.write|\.sub!?\(|\.gsub!?\(/)
  return "git_wrap" if cmd.match?(GIT_CMD) && !cmd.match?(WRITE_CMD)
  return "logs_rerun" if cmd.match?(LOG_CMD) && !cmd.match?(WRITE_CMD)
  # Build
  if cmd.match?(WRITE_CMD) || cmd.match?(/\.sub!?\(|\.gsub!?\(/)
    target = cmd[/(?:cat\s*>|tee\s|sed\s+-i\S*\s+(?:'[^']*'|"[^"]*"|\S+)\s+|File\.write\(|Path\(|p\s*=\s*)['"]?(\S+)/, 1].to_s
    return (target.match?(TEST_PATH) || (target.empty? && cmd.match?(TEST_PATH))) ? "write_tests" : "write_code"
  end
  # Understand
  return "read_gems" if cmd.match?(GEM_PATH)
  return "read_code" if cmd.match?(READ_CMD)
  return "env_setup" if cmd.match?(ENV_CMD)
  "other"
end

