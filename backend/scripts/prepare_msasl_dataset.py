"""
Reads data/external/msasl/intermediate_clips_manifest.csv (produced by
download_msasl_clips.py), extracts body-relative, fixed-length
trajectory features for each downloaded clip via
app.services.holistic_video_landmarks + app.services.word_landmark_features,
and writes them to data/processed/msasl_intermediate_landmarks.csv for
training — the same pipeline already validated on the Kaggle subset
(prepare_word_dataset.py / train_word_classifier.py), now pointed at
real MS-ASL video data for the actual Intermediate Conversational
Fluency vocabulary.

Keeps the dataset's own train/val/test split (assigned by MS-ASL's
creators) rather than re-splitting ourselves — a more rigorous held-out
evaluation than a self-constructed split.

--course selects which downloaded clip set to process (matches
download_msasl_clips.py's --course) — defaults to "intermediate" so
the original one-course invocation still works unchanged.

Run from backend/:
    venv/bin/python scripts/prepare_msasl_dataset.py
    venv/bin/python scripts/prepare_msasl_dataset.py --course professional
"""

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.holistic_video_landmarks import extract_raw_sequence_from_video
from app.services.word_landmark_features import (
    FIXED_FRAMES,
    feature_column_names,
    normalize_sequence,
    resample_sequence,
)

BACKEND_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_ROOT.parent
OUTPUT_DIR = BACKEND_ROOT / "data" / "processed"

PROGRESS_EVERY = 25


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--course", default="intermediate",
        help="Which downloaded clip set to process (matches download_msasl_clips.py's --course). "
             "Default: intermediate. Use 'professional' for Workplace Communication.",
    )
    args = parser.parse_args()
    course = args.course

    clips_manifest = REPO_ROOT / "data" / "external" / "msasl" / f"{course}_clips_manifest.csv"
    output_csv = OUTPUT_DIR / f"msasl_{course}_landmarks.csv"
    skipped_log = OUTPUT_DIR / f"skipped_msasl_{course}_clips.log"

    if not clips_manifest.exists():
        raise FileNotFoundError(f"Clip manifest not found: {clips_manifest}. Run download_msasl_clips.py first.")

    with open(clips_manifest, newline="") as f:
        rows = list(csv.DictReader(f))
    print(f"Loaded {len(rows)} downloaded clips covering {len(set(r['gloss'] for r in rows))} glosses")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    header = ["label", "split", "signer_id", "clip_id"] + feature_column_names(FIXED_FRAMES)

    # Resume support: extraction is slow enough (several seconds/clip) that
    # a killed run (session timeout, Mac sleep, etc.) shouldn't lose
    # already-computed features. Same pattern as download_msasl_clips.py's
    # resume support, applied here after a run got cut off mid-way with
    # its output CSV intact but incomplete.
    already_done: set[str] = set()
    output_is_new = not output_csv.exists() or output_csv.stat().st_size == 0
    if not output_is_new:
        with open(output_csv, newline="") as f:
            for existing_row in csv.DictReader(f):
                already_done.add(existing_row["clip_id"])
        print(f"Resuming: {len(already_done)} clips already extracted in an existing output file")

    kept = len(already_done)
    skipped = []
    per_class_counts: dict[str, int] = {}

    out_file = open(output_csv, "a" if not output_is_new else "w", newline="")
    writer = csv.writer(out_file)
    if output_is_new:
        writer.writerow(header)
        out_file.flush()

    try:
        for i, row in enumerate(rows, start=1):
            if row["clip_id"] in already_done:
                continue
            clip_path = REPO_ROOT / row["local_path"]
            try:
                raw = extract_raw_sequence_from_video(str(clip_path))
                if raw.shape[0] == 0:
                    skipped.append((row["clip_id"], row["gloss"], "no frames read from clip"))
                    continue
                normalized = normalize_sequence(raw)
                if normalized is None:
                    skipped.append((row["clip_id"], row["gloss"], "no pose/shoulders detected in any frame"))
                    continue
                features = resample_sequence(normalized, FIXED_FRAMES).flatten().tolist()
            except Exception as e:
                skipped.append((row["clip_id"], row["gloss"], f"error: {e}"))
                continue

            writer.writerow([row["gloss"], row["split"], row["signer_id"], row["clip_id"]] + features)
            out_file.flush()  # critical: survive a kill on the very next clip, same lesson as download_msasl_clips.py
            kept += 1
            per_class_counts[row["gloss"]] = per_class_counts.get(row["gloss"], 0) + 1

            if i % PROGRESS_EVERY == 0 or i == len(rows):
                print(f"Progress: {i}/{len(rows)} clips processed (kept {kept}, skipped {len(skipped)})")
    finally:
        out_file.close()

    if skipped:
        with open(skipped_log, "w") as log_file:
            for clip_id, gloss, reason in skipped:
                log_file.write(f"{clip_id}\t{gloss}\t{reason}\n")

    print("\n=== Summary ===")
    print(f"Total clips: {len(rows)}")
    print(f"Kept: {kept}")
    print(f"Skipped: {len(skipped)}")
    print("\nPer-class counts:")
    for label in sorted(per_class_counts):
        print(f"  {label}: {per_class_counts[label]}")
    if skipped:
        print(f"\nSkipped clip details logged to: {skipped_log}")
    print(f"Saved features to: {output_csv}")


if __name__ == "__main__":
    main()
