# Run Claude Code headless on SWE-bench Multilingual tasks, inside each task's
# official image, with or without the typescript-lsp plugin.
#
#   ruby run_agent.rb --run pilot --conditions lsp,nolsp --ids axios__axios-4731,vuejs__core-11870 --jobs 2
#   ruby run_agent.rb --run full --conditions nolsp,lsp,nolsp-edit,lsp-edit --jobs 4
#
# Four conditions, all with the same image, Claude Code binary, prompt, and
# language server binary on PATH:
#   nolsp       Claude Code as installed
#   lsp         plus the typescript-lsp plugin, which starts the server and
#               attaches its diagnostics to the agent's next turn after an edit
#   *-edit      plus a PreToolUse hook (hook/block-shell-edits.mjs) that rejects
#               Bash commands writing files outside /tmp. In the pilot, Opus
#               edited only through Bash (sed -i, inline Python), and Claude Code
#               tells the language server only about Edit and Write changes, so
#               without the hook the plugin never saw an edit.
# lsp-edit vs nolsp-edit isolates the diagnostics loop; lsp vs nolsp shows what
# installing the plugin does by default.
#
# Output per task: runs/<run>/<condition>/<instance_id>/
#   stream.jsonl   the headless session (--output-format stream-json)
#   projects/      Claude Code's own session transcript from the container
#   debug/         Claude Code's --debug log (language server traffic)
#   patch.diff     git diff of /testbed against the base commit
#   meta.json      exit status, duration, cost, model, versions
#
# The subscription token is read from ~/.config/claude-bench/token and passed
# to docker through the environment, never on a command line or in a log.

require "json"
require "open3"
require "optparse"
require "fileutils"
require "time"

HERE = __dir__
CACHE = File.join(HERE, "cache")
CLAUDE_VERSION = "2.1.330"
MODEL = "claude-opus-5-5"
AGENT_TIMEOUT = 30 * 60
TOKEN_FILE = File.expand_path("~/.config/claude-bench/token")

PROMPT = <<~MD
  <issue>
  %<issue>s
  </issue>

  The repository for this issue is checked out at /testbed, with its dependencies installed. Make the minimal changes to non-test files in /testbed to resolve the issue. Hidden tests will check your fix, so don't modify existing tests. When you're done, stop.
MD

opts = { run: nil, conditions: %w[lsp nolsp], ids: nil, groups: nil, jobs: 2, model: MODEL }
OptionParser.new do |o|
  o.on("--run NAME") { |v| opts[:run] = v }
  o.on("--conditions LIST") { |v| opts[:conditions] = v.split(",") }
  o.on("--ids LIST") { |v| opts[:ids] = v.split(",") }
  o.on("--groups LIST") { |v| opts[:groups] = v.split(",") }
  o.on("--jobs N", Integer) { |v| opts[:jobs] = v }
  o.on("--model ID") { |v| opts[:model] = v }
end.parse!
abort "--run is required" unless opts[:run]
abort "token missing: #{TOKEN_FILE}" unless File.size?(TOKEN_FILE)
%w[claude lsp.tar.gz].each { |f| abort "cache/#{f} missing" unless File.exist?(File.join(CACHE, f)) }

TOKEN = File.read(TOKEN_FILE).strip
tasks = File.readlines(File.join(HERE, "data", "tasks.jsonl")).map { |l| JSON.parse(l) }
tasks.select! { |t| opts[:ids].include?(t["instance_id"]) } if opts[:ids]
tasks.select! { |t| opts[:groups].include?(t["group"]) } if opts[:groups]
abort "no tasks selected" if tasks.empty?

def sh(*cmd, env: {}, out: nil, allow_fail: false)
  stdout, stderr, status = Open3.capture3(env, *cmd)
  File.write(out, stdout) if out
  unless status.success? || allow_fail
    raise "#{cmd.first(3).join(' ')} failed (#{status.exitstatus}): #{stderr[-2000..] || stderr}"
  end
  [stdout, stderr, status]
end

def log(msg) = $stderr.puts("[#{Time.now.strftime('%H:%M:%S')}] #{msg}")

def ensure_image(image)
  _, _, st = sh("docker", "image", "inspect", image, allow_fail: true)
  return if st.success?
  log "pulling #{image}"
  sh("docker", "pull", "--platform", "linux/amd64", "-q", image)
end

def run_one(task, condition, run, model)
  iid = task["instance_id"]
  dir = File.join(HERE, "runs", run, condition, iid)
  if File.exist?(File.join(dir, "meta.json"))
    log "skip #{condition} #{iid} (done)"
    return
  end
  FileUtils.mkdir_p(dir)
  name = "ccl-#{run}-#{condition}-#{iid}".gsub(/[^a-zA-Z0-9_.-]/, "-")
  sh("docker", "rm", "-f", name, allow_fail: true)
  ensure_image(task["image"])

  env = { "CLAUDE_CODE_OAUTH_TOKEN" => TOKEN }
  sh("docker", "run", "-d", "--platform", "linux/amd64", "--name", name,
     "-e", "CLAUDE_CODE_OAUTH_TOKEN", "-e", "IS_SANDBOX=1",
     "-e", "DISABLE_AUTOUPDATER=1", "-e", "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1",
     task["image"], "sleep", "infinity", env: env)
  begin
    sh("docker", "cp", File.join(CACHE, "claude"), "#{name}:/usr/local/bin/claude")
    sh("docker", "cp", File.join(CACHE, "lsp.tar.gz"), "#{name}:/tmp/lsp.tar.gz")
    sh("docker", "exec", name, "tar", "xzf", "/tmp/lsp.tar.gz", "-C", "/")

    if condition.start_with?("lsp")
      sh("docker", "exec", name, "bash", "-c",
         "claude plugin marketplace add anthropics/claude-plugins-official && " \
         "claude plugin install typescript-lsp@claude-plugins-official")
    end
    if condition.end_with?("-edit")
      sh("docker", "exec", name, "mkdir", "-p", "/opt/hook")
      sh("docker", "cp", File.join(HERE, "hook", "block-shell-edits.mjs"), "#{name}:/opt/hook/block-shell-edits.mjs")
      sh("docker", "exec", name, "/opt/lsp/bin/node", "-e", <<~JS)
        const fs = require("fs"), p = "/root/.claude/settings.json";
        fs.mkdirSync("/root/.claude", { recursive: true });
        const s = fs.existsSync(p) ? JSON.parse(fs.readFileSync(p)) : {};
        s.hooks = { PreToolUse: [{ matcher: "Bash", hooks: [{ type: "command", command: "/opt/lsp/bin/node /opt/hook/block-shell-edits.mjs" }] }] };
        fs.writeFileSync(p, JSON.stringify(s, null, 2));
      JS
    end
    plugins, = sh("docker", "exec", name, "claude", "plugin", "list", allow_fail: true)

    prompt_path = File.join(dir, "prompt.md")
    File.write(prompt_path, format(PROMPT, issue: task["problem_statement"]))
    sh("docker", "cp", prompt_path, "#{name}:/tmp/prompt.md")

    log "start #{condition} #{iid}"
    t0 = Time.now
    agent = <<~SH
      export PATH=/opt/lsp/wrap:$PATH
      cd /testbed
      timeout #{AGENT_TIMEOUT} claude -p "$(cat /tmp/prompt.md)" --model #{model} \
        --dangerously-skip-permissions --output-format stream-json --verbose --debug
    SH
    _, stderr, status = sh("docker", "exec", name, "bash", "-lc", agent,
                           out: File.join(dir, "stream.jsonl"), allow_fail: true)
    duration = Time.now - t0
    File.write(File.join(dir, "stderr.txt"), stderr)

    sh("docker", "exec", name, "bash", "-c", "cd /testbed && git add -A && git diff --cached --binary HEAD",
       out: File.join(dir, "patch.diff"))
    sh("docker", "cp", "#{name}:/root/.claude/projects", File.join(dir, "projects"), allow_fail: true)
    sh("docker", "cp", "#{name}:/root/.claude/debug", File.join(dir, "debug"), allow_fail: true)

    result = File.readlines(File.join(dir, "stream.jsonl")).filter_map do |l|
      JSON.parse(l) rescue nil
    end.reverse.find { |e| e["type"] == "result" } || {}

    meta = {
      instance_id: iid, group: task["group"], condition: condition, model: model,
      claude_code: CLAUDE_VERSION, typescript_language_server: "5.3.0", typescript_fallback: "5.9.3",
      plugins: plugins.strip, exit_status: status.exitstatus, timed_out: status.exitstatus == 124,
      duration_s: duration.round(1), num_turns: result["num_turns"], cost_usd: result["total_cost_usd"],
      result_subtype: result["subtype"], patch_bytes: File.size(File.join(dir, "patch.diff")),
      finished_at: Time.now.utc.iso8601
    }
    File.write(File.join(dir, "meta.json"), JSON.pretty_generate(meta))
    log "done  #{condition} #{iid}: exit #{status.exitstatus}, #{duration.round}s, $#{result['total_cost_usd']&.round(2)}, patch #{meta[:patch_bytes]}B"
  ensure
    sh("docker", "rm", "-f", name, allow_fail: true)
  end
rescue => e
  log "ERROR #{condition} #{task['instance_id']}: #{e.message}"
end

queue = Queue.new
tasks.each { |t| opts[:conditions].each { |c| queue << [t, c] } }
workers = Array.new(opts[:jobs]) do
  Thread.new do
    loop do
      t, c = queue.pop(true) rescue break
      run_one(t, c, opts[:run], opts[:model])
    end
  end
end
workers.each(&:join)
