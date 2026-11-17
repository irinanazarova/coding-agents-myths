"""Download the raw inputs at pinned revisions into data/raw/.

Sources (pinned):
  * github.com/SWE-bench/experiments, evaluation/multilingual/*/
    {metadata.yaml, per_instance_details.json}
  * huggingface.co/datasets/SWE-bench/SWE-bench_Multilingual, test split parquet
  * the matching SWE-bench Verified (Python) runs: evaluation/verified/<folder>/
    {metadata.yaml, per_instance_details.json} from the same commit, and
    huggingface.co/datasets/SWE-bench/SWE-bench_Verified, test split parquet
  * for two Verified runs (GPT-5.2 Codex, Gemini 3 Pro) the per-task
    report.json files come from the public submissions bucket (see REPORT_RUNS)
  * one agent trajectory per run (first task of each benchmark) from the
    public submissions bucket, read only for its recorded agent config

Every downloaded file's SHA-256 is written to data/raw/MANIFEST.json so a rerun
can be compared byte for byte. The script only reads the downloaded files as
data (JSON, YAML, parquet); it never executes anything from them.
"""

from __future__ import annotations

import hashlib
import io
import json
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

EXPERIMENTS_REPO = "SWE-bench/experiments"
# main as of 2026-09-03T01:24:30Z; the latest commit touching evaluation/multilingual
# is the Gemini 3.5 Flash submission merged 2026-09-02 (PR #476).
EXPERIMENTS_SHA = "40f164d5b8f1d249bf95a6df8b74b577fd8e519d"

HF_DATASET = "SWE-bench/SWE-bench_Multilingual"
# "Upload dataset", 2026-08-17. Instance ids, repos and gold patches match the
# original 2025-04-29 release; later commits added harness fields.
HF_SHA = "846e647b9f33c0b51b739d005d13d85493c9af09"
HF_FILE = "data/test-00000-of-00001.parquet"

HF_VERIFIED = "SWE-bench/SWE-bench_Verified"
# 2026-08-16; same 500 tasks as princeton-nlp/SWE-bench_Verified.
HF_VERIFIED_SHA = "78f471bf655a3137b2e8a75af1501690ec009ec3"

S3 = "https://swe-bench-submissions.s3.amazonaws.com"

# Multilingual run -> Verified run with the same model, mini-SWE-agent 2.x and
# date window (February 2026, bash-only leaderboard). See README for the checks.
PAIRS = {p["multilingual"]: p["verified"] for p in json.loads(
    (Path(__file__).resolve().parent / "pairs.json").read_text())}
CODEX_VERIFIED = "20260219_mini-v2.0.0_gpt-5-2-codex"
# Verified runs whose per-task results are taken from the evaluation reports in
# the submissions bucket: Codex has no per_instance_details.json in the repo, and
# Gemini 3 Pro's file marks all 500 tasks unresolved against an official 69.6%.
REPORT_RUNS = [CODEX_VERIFIED, "20260226_mini-v2.0.0_gemini-3-pro-high"]
TRAJ_TASK = {"multilingual": "apache__druid-13704", "bash-only": "astropy__astropy-12907"}

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "swebench-multilingual-by-language"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def save(rel: str, blob: bytes, manifest: dict, url: str) -> None:
    path = RAW / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(blob)
    manifest[rel] = {"url": url, "sha256": hashlib.sha256(blob).hexdigest(), "bytes": len(blob)}


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    manifest: dict = {
        "experiments": {"repo": EXPERIMENTS_REPO, "sha": EXPERIMENTS_SHA},
        "dataset": {"repo": HF_DATASET, "sha": HF_SHA},
        "dataset_verified": {"repo": HF_VERIFIED, "sha": HF_VERIFIED_SHA},
        "files": {},
    }
    files = manifest["files"]

    tree_url = f"https://api.github.com/repos/{EXPERIMENTS_REPO}/git/trees/{EXPERIMENTS_SHA}?recursive=1"
    tree = json.loads(get(tree_url))
    if tree.get("truncated"):
        print("warning: GitHub tree listing truncated", file=sys.stderr)
    wanted = sorted(
        e["path"]
        for e in tree["tree"]
        if e["path"].startswith("evaluation/multilingual/")
        and e["path"].count("/") == 3
        and e["path"].rsplit("/", 1)[1] in ("metadata.yaml", "per_instance_details.json")
    )
    for p in wanted:
        url = f"https://raw.githubusercontent.com/{EXPERIMENTS_REPO}/{EXPERIMENTS_SHA}/{p}"
        rel = "experiments/" + p.removeprefix("evaluation/multilingual/")
        print("get", rel)
        save(rel, get(url), files, url)

    url = f"https://huggingface.co/datasets/{HF_DATASET}/resolve/{HF_SHA}/{HF_FILE}"
    print("get dataset parquet")
    save("dataset/test.parquet", get(url), files, url)

    # --- Python baseline: SWE-bench Verified runs matched to the Multilingual ones
    for vf in PAIRS.values():
        for name in ("metadata.yaml", "per_instance_details.json"):
            if vf == CODEX_VERIFIED and name == "per_instance_details.json":
                continue
            url = f"https://raw.githubusercontent.com/{EXPERIMENTS_REPO}/{EXPERIMENTS_SHA}/evaluation/verified/{vf}/{name}"
            print("get", f"verified/{vf}/{name}")
            save(f"experiments_verified/{vf}/{name}", get(url), files, url)

    url = f"https://huggingface.co/datasets/{HF_VERIFIED}/resolve/{HF_VERIFIED_SHA}/{HF_FILE}"
    print("get verified dataset parquet")
    blob = get(url)
    save("dataset/verified.parquet", blob, files, url)

    import pyarrow.parquet as pq  # parquet is read as data only
    ids = pq.read_table(io.BytesIO(blob), columns=["instance_id"]).column(0).to_pylist()
    jobs = [(f"bucket_reports/{run}/{i}.json", f"{S3}/bash-only/{run}/logs/{i}/report.json")
            for run in REPORT_RUNS for i in ids]
    for ml, vf in PAIRS.items():
        for bucket, folder in (("multilingual", ml), ("bash-only", vf)):
            t = TRAJ_TASK[bucket]
            jobs.append((f"trajs/{bucket}/{folder}.traj.json", f"{S3}/{bucket}/{folder}/trajs/{t}/{t}.traj.json"))

    def fetch(job):
        rel, u = job
        try:
            return rel, u, get(u)
        except Exception as e:  # missing objects are recorded, not fatal
            return rel, u, e

    # Python typing check: each Verified repo's config files at its newest task's base commit
    vt = pq.read_table(io.BytesIO(blob), columns=["repo", "base_commit", "created_at"]).to_pandas()
    for repo, g in vt.sort_values("created_at").groupby("repo"):
        sha = g.base_commit.iloc[-1]
        for name in ("setup.cfg", "pyproject.toml", "tox.ini", "mypy.ini", ".pre-commit-config.yaml"):
            jobs.append((f"typing_check/{repo.replace('/', '__')}/{name}",
                         f"https://raw.githubusercontent.com/{repo}/{sha}/{name}"))

    print(f"get {len(jobs)} files from the submissions bucket and GitHub")
    with ThreadPoolExecutor(16) as ex:
        for rel, u, blob in ex.map(fetch, jobs):
            if isinstance(blob, Exception):
                print("  missing", rel, blob, file=sys.stderr)
                manifest.setdefault("missing", {})[rel] = u
            else:
                save(rel, blob, files, u)

    text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    (RAW / "MANIFEST.json").write_text(text)
    print(f"saved {len(files)} files to {RAW}")

    lock = ROOT / "sources.lock.json"
    if not lock.exists():
        lock.write_text(text)
        print(f"wrote {lock.name}; commit it to pin these bytes")
        return 0
    expected = json.loads(lock.read_text())["files"]
    bad = sorted(k for k in set(expected) | set(files)
                 if expected.get(k, {}).get("sha256") != files.get(k, {}).get("sha256"))
    if bad:
        print("downloaded files differ from sources.lock.json:", *bad, sep="\n  ", file=sys.stderr)
        return 1
    print("all files match sources.lock.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
