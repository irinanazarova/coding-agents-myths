"""Download the inputs for the JavaScript vs TypeScript comparison into data/raw/js_ts/.

Part 1, SWE-bench Multilingual (same pins as scripts/fetch.py):
  * the test split parquet and every February 2026 per_instance_details.json
  * for each of the 43 JavaScript and TypeScript tasks and each of the 13
    February runs: the agent trajectory, the submitted patch, the harness
    report and the test output, from the public submissions bucket

Part 2 and 3 (Multi-SWE-bench, SWE-PolyBench) are defined in OTHER_SOURCES.

Every file's SHA-256 goes to data/raw/js_ts/MANIFEST.json and is compared with
js_ts/sources.lock.json. Files are read later as data only (JSON, YAML,
parquet, text); nothing downloaded is executed.

Usage: python -I js_ts/fetch_js_ts.py [--skip-existing]
"""

from __future__ import annotations

import hashlib
import io
import json
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "js_ts"
LOCK = Path(__file__).resolve().parent / "sources.lock.json"

EXPERIMENTS_REPO = "SWE-bench/experiments"
EXPERIMENTS_SHA = "40f164d5b8f1d249bf95a6df8b74b577fd8e519d"  # main, 2026-09-03
HF_DATASET = "SWE-bench/SWE-bench_Multilingual"
HF_SHA = "846e647b9f33c0b51b739d005d13d85493c9af09"  # 2026-08-17
S3 = "https://swe-bench-submissions.s3.amazonaws.com"

FEB_RUNS = [
    "20260213_mini-v2.0.0a0_claude-4-5-haiku", "20260213_mini-v2.0.0a0_claude-4-5-opus",
    "20260213_mini-v2.0.0a0_claude-4-5-sonnet", "20260213_mini-v2.0.0a0_claude-4-6-opus",
    "20260213_mini-v2.0.0a0_deepseek-3-2", "20260213_mini-v2.0.0a0_gemini-3-flash",
    "20260213_mini-v2.0.0a0_gemini-3-pro", "20260213_mini-v2.0.0a0_glm-5",
    "20260213_mini-v2.0.0a0_gpt-5-2-high", "20260213_mini-v2.0.0a0_gpt-5-mini",
    "20260213_mini-v2.0.0a0_kimi-k2-5", "20260216_mini-v2.0.0a0_minimax-2-5",
    "20260220_mini-v2.0.0_gpt-5-2-codex",
]
JS_TS_REPOS = {
    "axios/axios", "immutable-js/immutable-js", "mrdoob/three.js", "preactjs/preact",
    "babel/babel", "facebook/docusaurus", "vuejs/core",
}

# Multi-SWE-bench (ByteDance): per-submission resolved lists and difficulty
# indexes from multi-swe-bench/experiments at HEAD of 2026-07-21 (PR #25), plus
# the newest JS/TS submission, unmerged PR #28 (AiWork.Code + Claude Opus 5.5,
# opened 2026-10-26, self-reported), from the submitter's fork.
MSB_REPO = "multi-swe-bench/experiments"
MSB_SHA = "6a7d5566f62fa76f4192302cf763051b98e4facc"
MSB_PR28 = ("x4vierli/multi-swe-bench-experiments", "1c043915c4c36d0893c4dcce892bbdc4892f7e02")
# Unmerged PR #29 (CodeArts Agent + CodeArts-GLM-5.2, opened 2026-11-01, self-reported).
MSB_PR29 = ("cakeliang-cc/experiments", "d8b79c053c6dd2d639a889d1cbda886eb84baa68")

# Filled at run time from the GitHub tree listings: (relative path, url).
OTHER_SOURCES: list[tuple[str, str]] = []


# SWE-PolyBench (Amazon), Verified split: the only split with per-instance
# results for JavaScript and TypeScript. Four merged submissions on the
# `submission` branch and four open pull requests, read from each fork.
PB_HF = ("AmazonScience/SWE-PolyBench_Verified", "b3fca77b637379f0c01ad86d18753a7ac1998b53")
PB_MAIN = ("amazon-science/SWE-PolyBench", "9c836c5d7f3cb991934132b77d29e6941d912a07")
PB_SUBS = [  # (local prefix, repo, sha, submission folder)
    ("merged", "amazon-science/SWE-PolyBench", "e7062f4a848ca7775bc1c1313f7aa419bd6a3ec1", "20251130_prometheus_gpt-5"),
    ("merged", "amazon-science/SWE-PolyBench", "e7062f4a848ca7775bc1c1313f7aa419bd6a3ec1", "20251208_atlassian-rovo-dev"),
    ("merged", "amazon-science/SWE-PolyBench", "e7062f4a848ca7775bc1c1313f7aa419bd6a3ec1", "20260430_kodah_gpt-5-mini"),
    ("merged", "amazon-science/SWE-PolyBench", "e7062f4a848ca7775bc1c1313f7aa419bd6a3ec1", "20260623_migbot_claude-opus-4-8"),
    ("pr40", "WilliamRocketRen/SWE-PolyBench", "46905351979ebe9da1d0d82c0fff2871daddaf85", "20260901_mobile-coder_deepseek-v4-flash"),
    ("pr44", "sanjuatps/SWE-PolyBench-S1", "2c177685c6bf424badb6c3722aaf8c778a178a08", "20261006_sapientslingshot_gpt-5.6-sol"),
    ("pr46", "charliefrantowski/SWE-PolyBench", "30150b6f06d8e2acfdba897fe473726515baff92", "20261010_jitto-build_claude-opus-5-5"),
    ("pr47", "x4vierli/SWE-PolyBench", "828dadd0f9d284ead4e6b4acba4ec67936b03fba", "20261021_aiwork-code_claude-opus-5-5"),
]


def pb_sources(js_ts_ids: set[str]) -> list[tuple[str, str]]:
    out = []
    for prefix, repo, sha, folder in PB_SUBS:
        base = f"evaluation/PBVerified/{folder}"
        out.append((f"pb/{prefix}/{base}/metadata.yaml", f"https://raw.githubusercontent.com/{repo}/{sha}/{base}/metadata.yaml"))
        for i in sorted(js_ts_ids):
            out.append((f"pb/{prefix}/{base}/logs/{i}_result.json",
                        f"https://raw.githubusercontent.com/{repo}/{sha}/{base}/logs/{i}_result.json"))
    # AiWork.Code's own memorization audit, shipped with its submission (PR #47).
    _, repo, sha, folder = PB_SUBS[-1]
    out.append(("pb/pr47_audit/memorization_audit.json",
                f"https://raw.githubusercontent.com/{repo}/{sha}/evaluation/PBVerified/{folder}/memorization_audit.json"))
    return out


def msb_sources() -> list[tuple[str, str]]:
    """Paths listed in js_ts/msb_files.txt (from the repo tree at MSB_SHA), so no
    GitHub API call is needed."""
    paths = (Path(__file__).resolve().parent / "msb_files.txt").read_text().split()
    out = [(f"msb/{p}", f"https://raw.githubusercontent.com/{MSB_REPO}/{MSB_SHA}/{p}") for p in paths]
    fork, sha = MSB_PR28
    for lang in ("javascript", "typescript"):
        for name in ("results/results.json", "metadata.yaml"):
            p = f"evaluation/{lang}/verified/20261026_AiWork-Code_Claude-Opus-5.5/{name}"
            out.append((f"msb_pr28/{lang}/{name}", f"https://raw.githubusercontent.com/{fork}/{sha}/{p}"))
    fork, sha = MSB_PR29
    for lang in ("javascript", "typescript"):
        p = f"evaluation/{lang}/verified/20261101_CodeArts-Agent_CodeArts-GLM-5.2/results/results.json"
        out.append((f"msb_pr29/{lang}.json", f"https://raw.githubusercontent.com/{fork}/{sha}/{p}"))
    return sorted(out)


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "swebench-multilingual-by-language"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def main() -> int:
    skip = "--skip-existing" in sys.argv
    RAW.mkdir(parents=True, exist_ok=True)
    files: dict = {}
    missing: dict = {}

    def save(rel: str, blob: bytes, url: str) -> None:
        p = RAW / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(blob)
        files[rel] = {"url": url, "sha256": hashlib.sha256(blob).hexdigest(), "bytes": len(blob)}

    def fetch(job):
        rel, url = job
        p = RAW / rel
        if skip and p.exists():
            return rel, url, p.read_bytes()
        try:
            return rel, url, get(url)
        except Exception as e:  # recorded, not fatal
            return rel, url, e

    jobs = [("multilingual/test.parquet",
             f"https://huggingface.co/datasets/{HF_DATASET}/resolve/{HF_SHA}/data/test-00000-of-00001.parquet")]
    for f in FEB_RUNS:
        jobs.append((f"multilingual/runs/{f}/per_instance_details.json",
                     f"https://raw.githubusercontent.com/{EXPERIMENTS_REPO}/{EXPERIMENTS_SHA}/evaluation/multilingual/{f}/per_instance_details.json"))
    print("get Multilingual dataset and run results")
    with ThreadPoolExecutor(8) as ex:
        for rel, url, blob in ex.map(fetch, jobs):
            if isinstance(blob, Exception):
                print("  missing", rel, blob, file=sys.stderr)
                missing[rel] = url
            else:
                save(rel, blob, url)

    import pyarrow.parquet as pq  # read as data only
    t = pq.read_table(io.BytesIO((RAW / "multilingual/test.parquet").read_bytes()),
                      columns=["instance_id", "repo"]).to_pylist()
    ids = sorted(r["instance_id"] for r in t if r["repo"] in JS_TS_REPOS)
    assert len(ids) == 43, len(ids)

    jobs = []
    for f in FEB_RUNS:
        for i in ids:
            jobs.append((f"multilingual/trajs/{f}/{i}.traj.json", f"{S3}/multilingual/{f}/trajs/{i}/{i}.traj.json"))
            for name in ("patch.diff", "report.json", "test_output.txt"):
                jobs.append((f"multilingual/logs/{f}/{i}/{name}", f"{S3}/multilingual/{f}/logs/{i}/{name}"))
    # SWE-PolyBench task file and annotations first; their JS/TS ids pick the logs.
    pb_meta = [("pb/hf/PBv_test.csv", f"https://huggingface.co/datasets/{PB_HF[0]}/resolve/{PB_HF[1]}/test.csv"),
               ("pb/gh/annotations.jsonl", f"https://raw.githubusercontent.com/{PB_MAIN[0]}/{PB_MAIN[1]}/data/annotations.jsonl")]
    for rel, url, blob in map(fetch, pb_meta):
        if isinstance(blob, Exception):
            raise SystemExit(f"cannot download {url}: {blob}")
        save(rel, blob, url)
    import csv
    csv.field_size_limit(1 << 30)
    with open(RAW / "pb/hf/PBv_test.csv", newline="") as fh:
        pb_ids = {r["instance_id"] for r in csv.DictReader(fh) if r["language"] in ("JavaScript", "TypeScript")}
    assert len(pb_ids) == 200, len(pb_ids)
    jobs += OTHER_SOURCES + msb_sources() + pb_sources(pb_ids)
    print(f"get {len(jobs)} files (trajectories, logs, other benchmarks)")
    with ThreadPoolExecutor(16) as ex:
        for rel, url, blob in ex.map(fetch, jobs):
            if isinstance(blob, Exception):
                missing[rel] = url
            else:
                save(rel, blob, url)
    if missing:
        print(f"  {len(missing)} files missing (listed in MANIFEST.json)", file=sys.stderr)

    manifest = {"files": files, "missing": missing}
    text = json.dumps(manifest, indent=1, sort_keys=True) + "\n"
    (RAW / "MANIFEST.json").write_text(text)
    print(f"saved {len(files)} files to {RAW}")
    if not LOCK.exists():
        LOCK.write_text(json.dumps({k: v["sha256"] for k, v in sorted(files.items())}, indent=0) + "\n")
        print(f"wrote {LOCK.name}; commit it to pin these bytes")
        return 0
    expected = json.loads(LOCK.read_text())
    bad = sorted(k for k in set(expected) | set(files) if expected.get(k) != files.get(k, {}).get("sha256"))
    if bad:
        print(f"{len(bad)} files differ from {LOCK.name}:", *bad[:20], sep="\n  ", file=sys.stderr)
        return 1
    print(f"all files match {LOCK.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
