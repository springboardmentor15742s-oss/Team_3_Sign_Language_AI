#!/usr/bin/env python3
"""Create reproducible Intermediate and Professional MS-ASL manifests.

This script deliberately builds metadata manifests only. MS-ASL references source
videos by URL; fetching those videos is a separate, reviewable step because links
can expire and its C-UDA restricts use. The manifests preserve MS-ASL's official
train/validation/test split to prevent accidental evaluation leakage.
"""

from __future__ import annotations

import argparse
import json
import zipfile
from collections import Counter
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE = BACKEND_ROOT / "data" / "external" / "msasl" / "MS-ASL.zip"
DEFAULT_LABELS = BACKEND_ROOT / "data" / "curriculum" / "msasl_curriculum_labels.json"
DEFAULT_OUTPUT = BACKEND_ROOT / "data" / "curriculum" / "manifests"
SPLITS = ("train", "val", "test")


def read_zip_json(archive: Path, member: str):
    with zipfile.ZipFile(archive) as package:
        return json.loads(package.read(member))


def build_course(archive: Path, course_id: str, course: dict, output_dir: Path) -> dict:
    wanted_glosses = set(course["glosses"])
    rows_by_split: dict[str, list[dict]] = {split: [] for split in SPLITS}

    for split in SPLITS:
        annotations = read_zip_json(archive, f"MS-ASL/MSASL_{split}.json")
        for sample in annotations:
            gloss = sample["text"]
            if gloss not in wanted_glosses:
                continue
            rows_by_split[split].append(
                {
                    "course": course_id,
                    "split": split,
                    "gloss": gloss,
                    "label": sample["label"],
                    "url": sample["url"],
                    "start_time": sample["start_time"],
                    "end_time": sample["end_time"],
                    "bbox_yxyx": sample["box"],
                    "signer_id": sample["signer_id"],
                    "fps": sample["fps"],
                    "width": sample["width"],
                    "height": sample["height"],
                }
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, dict[str, int]] = {}
    for split, rows in rows_by_split.items():
        destination = output_dir / f"msasl_{course_id}_{split}.jsonl"
        with destination.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        counts[split] = dict(sorted(Counter(row["gloss"] for row in rows).items()))

    all_present = set().union(*(set(counts[split]) for split in SPLITS))
    return {
        "course": course_id,
        "title": course["title"],
        "requested_glosses": course["glosses"],
        "available_glosses": sorted(all_present),
        "missing_glosses": sorted(wanted_glosses - all_present),
        "samples_per_split": {split: sum(counts[split].values()) for split in SPLITS},
        "samples_per_gloss": counts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if not args.archive.is_file():
        raise SystemExit(f"MS-ASL archive not found: {args.archive}")

    config = json.loads(args.labels.read_text(encoding="utf-8"))
    summaries = [
        build_course(args.archive, course_id, course, args.output)
        for course_id, course in config["courses"].items()
    ]
    summary_path = args.output / "msasl_curriculum_summary.json"
    summary_path.write_text(
        json.dumps({"source": config["source"], "courses": summaries}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote manifests and summary to {args.output}")
    for summary in summaries:
        print(f"{summary['course']}: {summary['samples_per_split']} samples; missing: {summary['missing_glosses']}")


if __name__ == "__main__":
    main()
