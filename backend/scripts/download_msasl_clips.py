"""
Downloads the MS-ASL "Intermediate Conversational Fluency" YouTube
clips listed in backend/data/curriculum/manifests/msasl_intermediate_*.jsonl
and writes a manifest (data/external/msasl/intermediate_clips_manifest.csv)
mapping each clip to its gloss, split, and signer_id — the same shape
as data/asl-signs/subset_manifest.csv, so prepare_msasl_dataset.py can
follow the same pattern as prepare_word_dataset.py.

Uses yt-dlp's --download-sections to fetch ONLY each clip's labeled
[start_time, end_time] window directly, rather than downloading the
full source video first — several manifest rows have clips that start
minutes into their source video (one starts at 403s for a 2.8s clip),
so downloading whole videos would pull down far more than needed. The
787 intermediate clips average 3.05s each (min 0.43s, max 7.9s) across
392 unique source videos, so this keeps total downloaded footage close
to the ~40 minutes actually used, not the full length of every source
video. ffmpeg does the precise cut as yt-dlp's postprocessor
(--force-keyframes-at-cuts), so both tools are still required.

Requires yt-dlp and ffmpeg on PATH.

IMPORTANT — licence: MS-ASL is distributed under Microsoft's
Computational Use of Data Agreement (C-UDA 0.1) — research/computational
use only, no commercial use, no redistribution of clips. See
backend/data/curriculum/README.md. Downloaded clips are written under
data/external/, which is gitignored — never commit them.

Run from backend/:
    venv/bin/python scripts/download_msasl_clips.py
"""

import argparse
import csv
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_ROOT.parent
MANIFEST_DIR = BACKEND_ROOT / "data" / "curriculum" / "manifests"
COURSE = "intermediate"
SPLITS = ["train", "val", "test"]

CLIPS_DIR = REPO_ROOT / "data" / "external" / "msasl" / "clips" / COURSE
OUTPUT_MANIFEST = REPO_ROOT / "data" / "external" / "msasl" / f"{COURSE}_clips_manifest.csv"
FAILURES_LOG = REPO_ROOT / "data" / "external" / "msasl" / f"{COURSE}_download_failures.txt"

MAX_DOWNLOAD_ATTEMPTS = 3
# A little padding around the labeled window so ffmpeg's keyframe-aligned
# cut has room to land exactly on [start_time, end_time] rather than
# snapping to the nearest earlier keyframe.
SECTION_PADDING_SEC = 1.0


def check_tools():
    missing = [t for t in ("yt-dlp", "ffmpeg") if shutil.which(t) is None]
    if missing:
        print(f"Missing required tools: {missing}. Install them first, then re-run.")
        sys.exit(1)


def load_manifest_rows() -> list[dict]:
    rows = []
    for split in SPLITS:
        path = MANIFEST_DIR / f"msasl_{COURSE}_{split}.jsonl"
        if not path.exists():
            print(f"WARNING: manifest not found, skipping: {path}")
            continue
        with open(path) as f:
            for line in f:
                row = json.loads(line)
                row["split"] = split
                rows.append(row)
    return rows


def download_clip_section(url: str, start: float, end: float, out_path: Path) -> bool:
    """
    Downloads ONLY the [start, end] window of the source video (plus a
    little padding for keyframe alignment) directly via yt-dlp
    --download-sections, instead of pulling the full video and trimming
    locally. yt-dlp shells out to ffmpeg as a postprocessor to make the
    cut land exactly on [start, end] (--force-keyframes-at-cuts).
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    padded_start = max(0.0, start - SECTION_PADDING_SEC)
    padded_end = end + SECTION_PADDING_SEC
    section = f"*{padded_start}-{padded_end}"

    for attempt in range(1, MAX_DOWNLOAD_ATTEMPTS + 1):
        result = subprocess.run(
            [
                "yt-dlp",
                "-f", "mp4[height<=480]/mp4/best",
                "--download-sections", section,
                "--force-keyframes-at-cuts",
                "-o", str(out_path),
                "--no-playlist", "--quiet", "--no-warnings",
                url,
            ],
            capture_output=True, text=True,
        )
        if result.returncode == 0 and out_path.exists():
            return True
        time.sleep(min(20, 3 * attempt))
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Only download the first N manifest rows — useful for measuring real disk/bandwidth "
             "usage on a small sample before committing to the full run.",
    )
    args = parser.parse_args()

    check_tools()
    rows = load_manifest_rows()
    if args.limit:
        rows = rows[: args.limit]
    print(
        f"Loaded {len(rows)} manifest rows across {SPLITS} for course={COURSE}"
        + (f" (limited to {args.limit})" if args.limit else ""),
        flush=True,
    )

    # Resume support: if a prior run got killed mid-way (session torn down,
    # Mac slept, etc.), don't lose or duplicate its progress. Clip FILES
    # survive a crash fine (yt-dlp/ffmpeg write and close them
    # independently) — it's our own buffered manifest writes and progress
    # prints that don't, unless we flush explicitly, which is what caused
    # a previous run to leave 47 real downloaded clips with a 0-byte
    # manifest and no visible progress in its log.
    OUTPUT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    already_logged: set[str] = set()
    manifest_is_new = not OUTPUT_MANIFEST.exists() or OUTPUT_MANIFEST.stat().st_size == 0
    if not manifest_is_new:
        with open(OUTPUT_MANIFEST, newline="") as f:
            for existing_row in csv.DictReader(f):
                already_logged.add(existing_row["clip_id"])
        print(f"Resuming: {len(already_logged)} clips already logged in an existing manifest", flush=True)

    kept = len(already_logged)
    failures = []
    per_split_counts = {s: 0 for s in SPLITS}

    manifest_file = open(OUTPUT_MANIFEST, "a", newline="")
    writer = csv.writer(manifest_file)
    if manifest_is_new:
        writer.writerow(["clip_id", "gloss", "split", "signer_id", "local_path"])
        manifest_file.flush()

    try:
        for i, row in enumerate(rows, start=1):
            clip_id = f"{COURSE}_{row['split']}_{i:04d}"
            if clip_id in already_logged:
                per_split_counts[row["split"]] += 1
                continue

            out_path = CLIPS_DIR / row["split"] / f"{clip_id}.mp4"

            if not out_path.exists():
                ok = download_clip_section(row["url"], row["start_time"], row["end_time"], out_path)
                if not ok:
                    failures.append((clip_id, row["gloss"], "yt-dlp section download failed"))
                    continue
            # else: file already on disk from an earlier, interrupted run —
            # don't re-download, just record it in the manifest now.

            rel_path = out_path.relative_to(REPO_ROOT)
            writer.writerow([clip_id, row["gloss"], row["split"], row["signer_id"], str(rel_path)])
            manifest_file.flush()  # critical: survive a crash on the very next row
            kept += 1
            per_split_counts[row["split"]] += 1

            if i % 25 == 0 or i == len(rows):
                print(f"Progress: {i}/{len(rows)} (kept {kept}, failed {len(failures)})", flush=True)
    finally:
        manifest_file.close()

    if failures:
        with open(FAILURES_LOG, "w") as f:
            for clip_id, gloss, reason in failures:
                f.write(f"{clip_id}\t{gloss}\t{reason}\n")

    print("\n=== Summary ===", flush=True)
    print(f"Total manifest rows: {len(rows)}", flush=True)
    print(f"Kept (including resumed from prior runs): {kept}", flush=True)
    print(f"Failed this run: {len(failures)}", flush=True)
    print(f"Per-split counts: {per_split_counts}", flush=True)
    if failures:
        print(f"Failure details logged to: {FAILURES_LOG}", flush=True)
    print(f"Saved clip manifest to: {OUTPUT_MANIFEST}", flush=True)


if __name__ == "__main__":
    main()
