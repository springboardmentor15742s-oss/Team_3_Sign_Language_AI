"""
Reads the Kaggle ASL-signs subset (data/asl-signs/subset_manifest.csv +
the landmark parquet files it points to), extracts body-relative,
fixed-length trajectory features for each sign sequence via
app.services.word_landmark_features, and writes them to
data/processed/word_landmarks.csv for training the word-level temporal
classifier.

This is a scoped proof-of-concept vocabulary (18 everyday words from
the Kaggle "Google - Isolated Sign Language Recognition" competition
subset) used to validate the feature-extraction + training pipeline
before running the same pipeline against the real MS-ASL curriculum
data for the actual Intermediate/Professional course vocabulary — see
backend/data/curriculum/README.md. Results from this script are NOT
wired into the Courses page; "Intermediate Conversational Fluency"
stays "Not yet available" until the real MS-ASL vocabulary is built.

Run from backend/:
    venv/bin/python scripts/prepare_word_dataset.py
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.word_landmark_features import FIXED_FRAMES, extract_sequence_features, feature_column_names

BACKEND_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_ROOT.parent
MANIFEST_CSV = REPO_ROOT / "data" / "asl-signs" / "subset_manifest.csv"
ASL_SIGNS_DIR = REPO_ROOT / "data" / "asl-signs"
OUTPUT_DIR = BACKEND_ROOT / "data" / "processed"
OUTPUT_CSV = OUTPUT_DIR / "word_landmarks.csv"
SKIPPED_LOG = OUTPUT_DIR / "skipped_word_sequences.log"

PROGRESS_EVERY = 100


def main():
    if not MANIFEST_CSV.exists():
        raise FileNotFoundError(
            f"Manifest not found: {MANIFEST_CSV}. Download the Kaggle ASL-signs subset first."
        )

    with open(MANIFEST_CSV, newline="") as f:
        rows = list(csv.DictReader(f))
    print(f"Loaded {len(rows)} manifest rows covering {len(set(r['sign'] for r in rows))} signs")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    header = ["label", "participant_id", "sequence_id"] + feature_column_names(FIXED_FRAMES)

    kept = 0
    skipped = []
    per_class_counts: dict[str, int] = {}

    with open(OUTPUT_CSV, "w", newline="") as out_file:
        writer = csv.writer(out_file)
        writer.writerow(header)

        for i, row in enumerate(rows, start=1):
            parquet_path = ASL_SIGNS_DIR / row["local_path"]
            try:
                features = extract_sequence_features(str(parquet_path))
            except Exception as e:
                skipped.append((row["sequence_id"], row["sign"], f"error: {e}"))
                continue

            if features is None:
                skipped.append((row["sequence_id"], row["sign"], "no pose/shoulders detected in any frame"))
                continue

            writer.writerow([row["sign"], row["participant_id"], row["sequence_id"]] + features)
            kept += 1
            per_class_counts[row["sign"]] = per_class_counts.get(row["sign"], 0) + 1

            if i % PROGRESS_EVERY == 0 or i == len(rows):
                print(f"Progress: {i}/{len(rows)} sequences processed (kept {kept}, skipped {len(skipped)})")

    if skipped:
        with open(SKIPPED_LOG, "w") as log_file:
            for seq_id, sign, reason in skipped:
                log_file.write(f"{seq_id}\t{sign}\t{reason}\n")

    print("\n=== Summary ===")
    print(f"Total sequences: {len(rows)}")
    print(f"Kept: {kept}")
    print(f"Skipped: {len(skipped)}")
    print("\nPer-class counts:")
    for label in sorted(per_class_counts):
        print(f"  {label}: {per_class_counts[label]}")
    if skipped:
        print(f"\nSkipped sequence details logged to: {SKIPPED_LOG}")
    print(f"Saved features to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
