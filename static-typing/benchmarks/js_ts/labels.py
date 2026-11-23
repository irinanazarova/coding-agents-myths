"""Label every JavaScript and TypeScript task in the three benchmarks by the
code its gold patch edits, at the task's base commit.

A benchmark labels a task by its repository's language. This script looks at
the files the reference fix actually changes and asks, for each one:

  ts          a .ts/.tsx/.mts/.cts source file (declaration files excluded)
  dts         a .d.ts declaration file
  checked_js  a .js/.jsx/.mjs/.cjs file the TypeScript compiler is configured
              to check: `// @ts-check` at the top of the file, or `checkJs: true`
              in the nearest tsconfig.json/jsconfig.json above it (following
              relative `extends`, respecting `include`/`exclude`/`files`), and
              no `// @ts-nocheck`
  plain_js    any other .js/.jsx/.mjs/.cjs file
  other       everything else (.vue, .svelte, .json, docs, ...)

and gives the task one label from its code files (ts, checked_js, plain_js):

  typed       every code file is ts or checked_js
  plain       every code file is plain_js
  mixed       both
  none        no JS/TS code file (only .d.ts, .vue, .json, ...)

It also records which package.json scripts run the TypeScript compiler (root,
and the nearest package.json above each edited code file), so a type check is
one `npm run` away, and how many .d.ts files the patch edits.

Inputs, read as data only:
  data/raw/js_ts/msb_tasks/*.jsonl, data/raw/js_ts/msb_svelte.jsonl   Multi-SWE-bench
  data/raw/js_ts/pb/hf/PBv_test.csv                                    SWE-PolyBench Verified
  data/raw/js_ts/multilingual/test.parquet + results/tasks.csv         SWE-bench Multilingual
Network: GitHub GraphQL (needs `gh auth token`), reading files at each task's
base commit, cached in data/raw/js_ts/gh_cache/ so reruns are offline.

Output: js_ts/results/task_labels.csv, plus a summary on stdout.

Usage: python -I js_ts/labels.py
"""
import csv
import hashlib
import json
import posixpath
import re
import sys
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "data" / "raw" / "js_ts"
CACHE = RAW / "gh_cache"
OUT = HERE / "results" / "task_labels.csv"

MSB_SHA = {  # Hugging Face ByteDance-Seed/Multi-SWE-bench@56ff018c
    "msb_tasks/Kong__insomnia.jsonl": "a12c192097969d351c1081cfb5728680864b0c7d8f3bf2a9e90c2f0a60c8836f",
    "msb_tasks/anuraghazra__github-readme-stats.jsonl": "4c3e85ffc054321e0a5aed272e010592eea8cd70ddf52cce0f953574285bcdc7",
    "msb_tasks/axios__axios.jsonl": "64217dadc28cf21cc3b4d0777eef8207f957a5f0edfc7de43e13bee680d76c64",
    "msb_tasks/darkreader__darkreader.jsonl": "350ddd200d2774be699d72062b356a9ceecdf38c3f9ab72e1ece3887626a93a8",
    "msb_tasks/expressjs__express.jsonl": "b409503d27b227982c8063b3735463899b7134afd7c3b712d75e04d50c442913",
    "msb_tasks/iamkun__dayjs.jsonl": "2385ad31059b7448d35aa2dba38c03c2cae9ed09f6e794d299649a22bef71c71",
    "msb_tasks/mui__material-ui.jsonl": "3e87ddc463f5193577cf7e3be25d9fd3bceebfbfbf717ba702ffd55208c56543",
    "msb_tasks/vuejs__core.jsonl": "10365ee2414d80b0985a1fda64588c06e260646b7f90b916551d0bfd00203b30",
    "msb_svelte.jsonl": "bd58d8e5348afcee93c1e9cb79398888c73b92b336ab09e1825068eb5fda1b09",
}
MSB_TS_REPOS = {"mui/material-ui", "vuejs/core", "darkreader/darkreader"}

TS_EXT = (".ts", ".tsx", ".mts", ".cts")
JS_EXT = (".js", ".jsx", ".mjs", ".cjs")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def patch_files(patch):
    """Paths the patch leaves behind (new side), skipping deletions."""
    out = []
    for block in re.split(r"^diff --git ", patch, flags=re.M)[1:]:
        m = re.match(r"a/(\S+) b/(\S+)", block)
        if not m:
            continue
        if re.search(r"^\+\+\+ /dev/null", block, re.M):
            continue  # deleted file
        out.append(m.group(2))
    return out


# ---------- tasks ----------
def msb_tasks():
    for rel, want in MSB_SHA.items():
        p = RAW / rel
        if not p.exists():
            sys.exit(f"missing {p}; see \"Relabeling tasks by edited files\" in js_ts/README.md")
        assert sha256(p) == want, f"sha256 mismatch: {p}"
        with open(p) as f:
            for line in f:
                d = json.loads(line)
                repo = f"{d['org']}/{d['repo']}"
                base = d["base"]
                if isinstance(base, str):  # stored as a Ruby-style hash string
                    base = {"sha": re.search(r'"sha" => "([0-9a-f]{40})"', base).group(1)}
                yield {
                    "benchmark": "Multi-SWE-bench",
                    "instance_id": d["instance_id"],
                    "repo": repo,
                    "bench_lang": "TS" if repo in MSB_TS_REPOS else "JS",
                    "base_sha": base["sha"],
                    "files": patch_files(d["fix_patch"]),
                }


def pb_tasks():
    d = pd.read_csv(RAW / "pb" / "hf" / "PBv_test.csv")
    d = d[d.language.isin(["JavaScript", "TypeScript"])]
    for r in d.itertuples():
        yield {
            "benchmark": "SWE-PolyBench",
            "instance_id": r.instance_id,
            "repo": r.repo,
            "bench_lang": "TS" if r.language == "TypeScript" else "JS",
            "base_sha": r.base_commit,
            "files": patch_files(r.patch),
        }


def ml_tasks():
    lang = {r["instance_id"]: r["lang"] for r in csv.DictReader(open(HERE / "results" / "tasks.csv"))}
    d = pd.read_parquet(RAW / "multilingual" / "test.parquet")
    d = d[d.instance_id.isin(lang)]
    assert len(d) == len(lang) == 43, (len(d), len(lang))
    for r in d.itertuples():
        yield {
            "benchmark": "SWE-bench Multilingual",
            "instance_id": r.instance_id,
            "repo": r.repo,
            "bench_lang": lang[r.instance_id],
            "base_sha": r.base_commit,
            "files": patch_files(r.patch),
        }


# ---------- GitHub fetch: GraphQL batches into an on-disk cache ----------
class Missing(Exception):
    pass


def cache_key(repo, sha, path):
    return CACHE / repo.replace("/", "__") / sha / path


def fetch(repo, sha, path):
    """File text at repo@sha, or None if it doesn't exist. Reads the cache only;
    raises Missing (and records the path) if it hasn't been fetched yet."""
    key = cache_key(repo, sha, path)
    if key.exists():
        return key.read_text(errors="replace")
    if key.with_name(key.name + ".404").exists():
        return None
    WANT.add((repo, sha, path))
    raise Missing


WANT = set()


def gh_token():
    import subprocess
    return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()


def graphql_fetch(keys, token, per_query=150):
    """Fetch (repo, sha, path) blobs with GitHub GraphQL object(expression:)."""
    keys = sorted(keys)
    for i in range(0, len(keys), per_query):
        chunk = keys[i:i + per_query]
        by_repo = defaultdict(list)
        for j, k in enumerate(chunk):
            by_repo[k[0]].append((j, k))
        parts = []
        for r, (repo, items) in enumerate(by_repo.items()):
            owner, name = repo.split("/")
            objs = " ".join(f"o{j}: object(expression: {json.dumps(sha + ':' + path)}) {{ ... on Blob {{ text isBinary }} }}"
                            for j, (_, sha, path) in items)
            parts.append(f"r{r}: repository(owner: {json.dumps(owner)}, name: {json.dumps(name)}) {{ {objs} }}")
        q = "query { " + " ".join(parts) + " }"
        req = urllib.request.Request("https://api.github.com/graphql", data=json.dumps({"query": q}).encode(),
                                     headers={"Authorization": f"bearer {token}", "User-Agent": "coding-agents-myths-labels"})
        for attempt in range(5):
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    body = json.loads(resp.read())
                break
            except (urllib.error.URLError, TimeoutError):
                if attempt == 4:
                    raise
                import time; time.sleep(5 * (attempt + 1))
        if body.get("errors") and not body.get("data"):
            sys.exit(f"GraphQL error: {body['errors'][:2]}")
        data = body["data"]
        for r, (repo, items) in enumerate(by_repo.items()):
            node = data.get(f"r{r}") or {}
            for j, (_, sha, path) in items:
                o = node.get(f"o{j}")
                key = cache_key(repo, sha, path)
                key.parent.mkdir(parents=True, exist_ok=True)
                if o is None or "text" not in o:
                    key.with_name(key.name + ".404").write_text("")
                else:
                    key.write_text("" if o.get("isBinary") else (o.get("text") or ""))
        print(f"  fetched {min(i + per_query, len(keys))}/{len(keys)}", file=sys.stderr)


def prefetch(tasks):
    """Every path label_task can read on the first pass: package.json, each
    edited JS file, and tsconfig/jsconfig in every folder above it."""
    out = set()
    for t in tasks:
        repo, sha = t["repo"], t["base_sha"]
        out.add((repo, sha, "package.json"))
        for f in t["files"]:
            if f.endswith(TS_EXT + JS_EXT):
                d = posixpath.dirname(f)
                while d:
                    out.add((repo, sha, posixpath.join(d, "package.json")))
                    d = posixpath.dirname(d)
            if f.endswith(JS_EXT):
                out.add((repo, sha, f))
                d = posixpath.dirname(f)
                while True:
                    for name in ("tsconfig.json", "jsconfig.json"):
                        out.add((repo, sha, posixpath.join(d, name) if d else name))
                    if not d:
                        break
                    d = posixpath.dirname(d)
    return {k for k in out if not cache_key(*k).exists() and not cache_key(*k).with_name(cache_key(*k).name + ".404").exists()}


def jsonc(text):
    """Parse tsconfig-style JSON: comments and trailing commas allowed."""
    out, i, n, in_str = [], 0, len(text), False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == "\\":
                out.append(text[i + 1]); i += 2; continue
            if c == '"':
                in_str = False
            i += 1
        elif c == '"':
            in_str = True; out.append(c); i += 1
        elif text.startswith("//", i):
            j = text.find("\n", i); i = n if j < 0 else j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2); i = n if j < 0 else j + 2
        else:
            out.append(c); i += 1
    s = re.sub(r",(\s*[}\]])", r"\1", "".join(out))
    return json.loads(s)


def glob_re(pattern):
    """TypeScript include/exclude glob to regex (*, ?, **/)."""
    p = pattern.rstrip("/")
    while p.startswith("./"):
        p = p[2:]
    if p in ("", "."):
        p = "**"
    rx, i = "", 0
    while i < len(p):
        if p.startswith("**/", i):
            rx += "(?:.*/)?"; i += 3
        elif p.startswith("**", i):
            rx += ".*"; i += 2
        elif p[i] == "*":
            rx += "[^/]*"; i += 1
        elif p[i] == "?":
            rx += "[^/]"; i += 1
        else:
            rx += re.escape(p[i]); i += 1
    # a directory pattern matches everything below it
    return re.compile("^" + rx + "(?:/.*)?$")


def load_config(repo, sha, path, depth=0):
    """Merged compilerOptions/include/exclude/files for a config file, following
    relative `extends`. Returns None if the file doesn't parse."""
    text = fetch(repo, sha, path)
    if text is None:
        return None
    try:
        cfg = jsonc(text)
    except (json.JSONDecodeError, IndexError):
        return {"opts": {}, "base": posixpath.dirname(path), "include": None, "exclude": None,
                "files": None, "parse_error": True}
    merged = {"opts": {}, "base": posixpath.dirname(path), "include": None, "exclude": None, "files": None}
    ext = cfg.get("extends")
    for e in ([ext] if isinstance(ext, str) else ext or []):
        if depth < 5 and e.startswith("."):
            ep = posixpath.normpath(posixpath.join(posixpath.dirname(path), e))
            if not ep.endswith(".json"):
                ep += ".json"
            parent = load_config(repo, sha, ep, depth + 1)
            if parent:
                merged["opts"].update(parent["opts"])
                for k in ("include", "exclude", "files"):
                    if parent[k] is not None:  # inherited, relative to the parent's folder
                        merged[k] = parent[k]; merged[k + "_base"] = parent.get(k + "_base", parent["base"])
    merged["opts"].update(cfg.get("compilerOptions") or {})
    for k in ("include", "exclude", "files"):
        if k in cfg:
            merged[k] = cfg[k]; merged[k + "_base"] = merged["base"]
    return merged


def covered(cfg, path):
    """Whether a config's include/files/exclude take in this file."""
    def rel(k):
        base = cfg.get(k + "_base", cfg["base"])
        return posixpath.relpath(path, base or ".")
    if cfg["files"] is not None and cfg["include"] is None:
        return any(posixpath.normpath(f) == rel("files") for f in cfg["files"])
    inc = cfg["include"] if cfg["include"] is not None else ["**/*"]
    if not any(glob_re(g).match(rel("include")) for g in inc):
        return False
    exc = cfg["exclude"] if cfg["exclude"] is not None else ["node_modules"]
    return not any(glob_re(g).match(rel("exclude")) for g in exc)


def nearest_config(repo, sha, path):
    d = posixpath.dirname(path)
    while True:
        for name in ("tsconfig.json", "jsconfig.json"):
            p = posixpath.join(d, name) if d else name
            if fetch(repo, sha, p) is not None:
                return p
        if not d:
            return None
        d = posixpath.dirname(d)


def js_checked(repo, sha, path):
    """(checked?, why) for a JS file at repo@sha."""
    text = fetch(repo, sha, path)
    head = "\n".join((text or "").splitlines()[:30])
    if re.search(r"^\s*//\s*@ts-nocheck", head, re.M):
        return False, "ts-nocheck"
    if re.search(r"^\s*//\s*@ts-check", head, re.M):
        return True, "ts-check"
    cp = nearest_config(repo, sha, path)
    if cp is None:
        return False, "no-config"
    cfg = load_config(repo, sha, cp)
    if cfg.get("parse_error"):
        return False, f"unparsed:{cp}"
    if not cfg["opts"].get("checkJs"):
        return False, f"no-checkJs:{cp}"
    if not covered(cfg, path):
        return False, f"not-included:{cp}"
    return True, f"checkJs:{cp}"


TSC_RX = re.compile(r"(^|[\s&;|/(])(tsc|vue-tsc|tsc-files)(\s|$)")


def nearest_package(repo, sha, path):
    d = posixpath.dirname(path)
    while True:
        p = posixpath.join(d, "package.json") if d else "package.json"
        if fetch(repo, sha, p) is not None:
            return p
        if not d:
            return None
        d = posixpath.dirname(d)


def tsc_scripts(repo, sha, files):
    """Scripts that run the TypeScript compiler, in the root package.json and in
    the nearest package.json above each edited code file: "path:script"."""
    pkgs = {"package.json"} | {nearest_package(repo, sha, f) for f in files if f.endswith(TS_EXT + JS_EXT)}
    out = []
    for p in sorted(x for x in pkgs if x):
        text = fetch(repo, sha, p)
        if not text:
            continue
        try:
            scripts = json.loads(text).get("scripts") or {}
        except json.JSONDecodeError:
            continue
        out += [f"{p}:{k}" for k, v in scripts.items() if TSC_RX.search(str(v))]
    return ";".join(out)


def label_task(t):
    repo, sha = t["repo"], t["base_sha"]
    kinds, why = defaultdict(list), []
    for f in t["files"]:
        if f.endswith(".d.ts"):
            kinds["dts"].append(f)
        elif f.endswith(TS_EXT):
            kinds["ts"].append(f)
        elif f.endswith(JS_EXT):
            ok, w = js_checked(repo, sha, f)
            kinds["checked_js" if ok else "plain_js"].append(f)
            why.append(w)
        else:
            kinds["other"].append(f)
    typed = kinds["ts"] or kinds["checked_js"]
    if typed and kinds["plain_js"]:
        label = "mixed"
    elif typed:
        label = "typed"
    elif kinds["plain_js"]:
        label = "plain"
    else:
        label = "none"
    return {
        **{k: t[k] for k in ("benchmark", "instance_id", "repo", "bench_lang", "base_sha")},
        "label": label,
        "n_ts": len(kinds["ts"]), "n_checked_js": len(kinds["checked_js"]),
        "n_plain_js": len(kinds["plain_js"]), "n_dts": len(kinds["dts"]), "n_other": len(kinds["other"]),
        "js_check_reason": ";".join(sorted(set(why))),
        "tsc_scripts": tsc_scripts(repo, sha, t["files"]),
        "files": " ".join(t["files"]),
    }


def main():
    tasks = list(msb_tasks()) + list(pb_tasks()) + list(ml_tasks())
    token = None
    todo = prefetch(tasks)
    for rnd in range(10):  # later rounds follow `extends` chains
        if todo:
            token = token or gh_token()
            print(f"round {rnd}: fetching {len(todo)} files", file=sys.stderr)
            graphql_fetch(todo, token)
        WANT.clear()
        rows = []
        for t in tasks:
            try:
                rows.append(label_task(t))
            except Missing:
                pass
        if not WANT:
            break
        todo = set(WANT)
    assert len(rows) == len(tasks), "unresolved fetches remain"
    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["benchmark"], r["instance_id"])))

    for bench in ("SWE-bench Multilingual", "Multi-SWE-bench", "SWE-PolyBench"):
        rs = [r for r in rows if r["benchmark"] == bench]
        print(f"\n## {bench}: {len(rs)} tasks")
        print(f"{'repo':38s} {'bench':5s} {'n':>4s} {'typed':>6s} {'(ts':>4s} {'chkJS)':>6s} {'plain':>6s} {'mixed':>6s} {'none':>5s}  tsc script")
        by = defaultdict(list)
        for r in rs:
            by[(r["bench_lang"], r["repo"])].append(r)
        for (lang, repo), g in sorted(by.items(), key=lambda kv: (kv[0][0], -len(kv[1]))):
            c = Counter(r["label"] for r in g)
            ts_only = sum(r["label"] == "typed" and r["n_checked_js"] == 0 for r in g)
            chk = sum(r["label"] == "typed" and r["n_checked_js"] > 0 for r in g)
            tsc = sum(bool(r["tsc_scripts"]) for r in g)
            print(f"{repo:38s} {lang:5s} {len(g):4d} {c['typed']:6d} {ts_only:4d} {chk:6d} {c['plain']:6d} {c['mixed']:6d} {c['none']:5d}  {tsc}/{len(g)}")
        for lang in ("JS", "TS"):
            c = Counter(r["label"] for r in rs if r["bench_lang"] == lang)
            print(f"  all {lang}: " + ", ".join(f"{k} {c[k]}" for k in ("typed", "plain", "mixed", "none")))
    print(f"\nwrote {OUT.relative_to(HERE.parent)}")


if __name__ == "__main__":
    main()
