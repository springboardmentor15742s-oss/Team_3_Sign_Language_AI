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

Run from backend/:
    venv/bin/python scripts/prepare_msasl_dataset.py
"""

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
COURSE = "intermediate"
CLIPS_MANIFEST = REPO_ROOT / "data" / "external" / "msasl" / f"{COURSE}_clips_manifest.csv"
OUTPUT_DIR = BACKEND_ROOT / "data" / "processed"
OUTPUT_CSV = OUTPUT_DIR / f"msasl_{COURSE}_landmarks.csv"
SKIPPED_LOG = OUTPUT_DIR / f"skipped_msasl_{COURSE}_clips.log"

PROGRESS_EVERY = 25


def main():
    if not CLIPS_MANIFEST.exists():
        raise FileNotFoundError(f"Clip manifest not found: {CLIPS_MANIFEST}. Run download_msasl_clips.py first.")

    with open(CLIPS_MANIFEST, newline="") as f:
        rows = list(csv.DictReader(f))
    print(f"Loaded {len(rows)} downloaded clips covering {len(set(r['gloss'] for r in rows))} glosses")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    header = ["label", "split", "signer_id", "clip_id"] + feature_column_names(FIXED_FRAMES)

    kept = 0
    skipped = []
    per_class_counts: dict[str, int] = {}

    with open(OUTPUT_CSV, "w", newline="") as out_file:
        writer = csv.writer(out_file)
        writer.writerow(header)

        for i, row in enumerate(rows, start=1):
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
            kept += 1
            per_class_counts[row["gloss"]] = per_class_counts.get(row["gloss"], 0) + 1

            if i % PROGRESS_EVERY == 0 or i == len(rows):
                print(f"Progress: {i}/{len(rows)} clips processed (kept {kept}, skipped {len(skipped)})")

    if skipped:
        with open(SKIPPED_LOG, "w") as log_file:
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
        print(f"\nSkipped clip details logged to: {SKIPPED_LOG}")
    print(f"Saved features to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
