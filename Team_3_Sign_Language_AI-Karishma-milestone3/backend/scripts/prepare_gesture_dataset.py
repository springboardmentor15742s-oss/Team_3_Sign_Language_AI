"""
Samples a subset of the ASL Alphabet training images, runs them through
MediaPipe hand tracking, normalizes the resulting landmarks, and writes
the feature vectors + labels to data/processed/gesture_landmarks.csv for
training the gesture recognition model. Run from backend/:

    venv/bin/python scripts/prepare_gesture_dataset.py
"""

import csv
import multiprocessing
import random
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.hand_tracking_service import detect_hand_landmarks_from_path, normalize_landmarks

BACKEND_ROOT = Path(__file__).resolve().parent.parent
TRAIN_DIR = BACKEND_ROOT / "data" / "asl_alphabet" / "asl_alphabet_train" / "asl_alphabet_train"
OUTPUT_DIR = BACKEND_ROOT / "data" / "processed"
OUTPUT_CSV = OUTPUT_DIR / "gesture_landmarks.csv"
SKIPPED_LOG = OUTPUT_DIR / "skipped_images.log"

SAMPLES_PER_CLASS = 200
RANDOM_SEED = 42
NUM_WORKERS = max(1, multiprocessing.cpu_count() - 1)
PROGRESS_EVERY = 500


def sample_class_images(class_dir: Path, n: int, rng: random.Random) -> list[Path]:
    images = sorted(
        f for f in class_dir.iterdir() if f.suffix.lower() in (".jpg", ".jpeg", ".png")
    )
    if len(images) <= n:
        return images
    return rng.sample(images, n)


def process_image(task: tuple[Path, str]) -> dict:
    image_path, label = task
    try:
        hands = detect_hand_landmarks_from_path(str(image_path))
    except Exception as e:
        return {"status": "error", "label": label, "path": str(image_path), "detail": str(e)}

    if not hands:
        return {"status": "no_hand", "label": label, "path": str(image_path), "detail": ""}

    best_hand = max(hands, key=lambda h: h["confidence"])
    features = normalize_landmarks(best_hand["landmarks"])
    return {"status": "ok", "label": label, "features": features}


def main():
    if not TRAIN_DIR.exists():
        raise FileNotFoundError(f"Training data not found: {TRAIN_DIR}")

    rng = random.Random(RANDOM_SEED)
    class_dirs = sorted(d for d in TRAIN_DIR.iterdir() if d.is_dir())
    print(f"Found {len(class_dirs)} classes in {TRAIN_DIR}")

    tasks: list[tuple[Path, str]] = []
    for class_dir in class_dirs:
        sampled = sample_class_images(class_dir, SAMPLES_PER_CLASS, rng)
        tasks.extend((path, class_dir.name) for path in sampled)

    print(f"Sampled {len(tasks)} images (~{SAMPLES_PER_CLASS} per class)")
    print(f"Running hand detection with {NUM_WORKERS} worker processes...\n")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    header = ["label"] + [f"{axis}{i}" for i in range(21) for axis in ("x", "y", "z")]

    processed = 0
    skipped = 0
    per_class_counts = {class_dir.name: 0 for class_dir in class_dirs}
    skipped_entries = []

    with open(OUTPUT_CSV, "w", newline="") as out_file:
        writer = csv.writer(out_file)
        writer.writerow(header)

        with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
            futures = [executor.submit(process_image, task) for task in tasks]

            for i, future in enumerate(as_completed(futures), start=1):
                result = future.result()

                if result["status"] == "ok":
                    writer.writerow([result["label"]] + result["features"])
                    per_class_counts[result["label"]] += 1
                    processed += 1
                else:
                    skipped += 1
                    skipped_entries.append(result)

                if i % PROGRESS_EVERY == 0 or i == len(tasks):
                    print(f"Progress: {i}/{len(tasks)} images processed (kept {processed}, skipped {skipped})")

    if skipped_entries:
        with open(SKIPPED_LOG, "w") as log_file:
            for entry in skipped_entries:
                log_file.write(f"{entry['status']}\t{entry['label']}\t{entry['path']}\t{entry['detail']}\n")

    print("\n=== Summary ===")
    print(f"Total images sampled: {len(tasks)}")
    print(f"Total processed (hand detected): {processed}")
    print(f"Total skipped (no hand / error): {skipped}")
    print("\nPer-class counts:")
    for label in sorted(per_class_counts):
        print(f"  {label}: {per_class_counts[label]}")

    if skipped_entries:
        print(f"\nSkipped image details logged to: {SKIPPED_LOG}")
    print(f"Saved feature vectors to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
