"""
Generates one still reference image per Conversational Fluency word,
so the practice page can show a learner what the target sign actually
looks like instead of only naming it.

The frame comes from a real MS-ASL training clip
(data/external/msasl/intermediate_clips_manifest.csv, the same clips
train_msasl_classifier.py trains on) — never a stand-in illustration —
picked from the TRAIN split specifically so the held-out val/test clips
the model's reported test_accuracy is measured on stay untouched by
anything else in the app.

For each of the 16 words the shipped classifier actually supports
(get_supported_word_signs() — the single source of truth also used to
validate assignments and drive the practice picker), this:
  1. Finds that word's first train-split clip in the manifest.
  2. Grabs the middle frame of the clip (roughly where the sign is
     mid-articulation, rather than a frame from a resting hand at the
     very start/end).
  3. Downscales it and writes a JPEG to
     backend/data/uploads/word-signs/<word_with_underscores>.jpg —
     inside the existing data/uploads tree main.py already serves at
     /media/..., so no new static mount is needed.

Run from backend/:
    python3 scripts/extract_word_sign_reference_images.py
"""

import csv
import sys
from pathlib import Path

import cv2

BACKEND_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_ROOT.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.word_sign_service import get_supported_word_signs  # noqa: E402

MANIFEST_PATH = REPO_ROOT / "data" / "external" / "msasl" / "intermediate_clips_manifest.csv"
OUTPUT_DIR = BACKEND_ROOT / "data" / "uploads" / "word-signs"
MAX_WIDTH = 480
JPEG_QUALITY = 85


def _slug(word: str) -> str:
    return word.replace(" ", "_").replace("'", "")


def _first_train_clip(rows: list[dict], word: str) -> dict | None:
    train_matches = [r for r in rows if r["gloss"] == word and r["split"] == "train"]
    if train_matches:
        return train_matches[0]
    any_matches = [r for r in rows if r["gloss"] == word]
    return any_matches[0] if any_matches else None


def _extract_middle_frame(video_path: Path):
    cap = cv2.VideoCapture(str(video_path))
    try:
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if frame_count > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count // 2)
        ok, frame = cap.read()
        if not ok or frame is None:
            # Some clips under-report frame count — fall back to just
            # reading frames from the start until one decodes.
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = cap.read()
        return frame if ok else None
    finally:
        cap.release()


def main():
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Clip manifest not found: {MANIFEST_PATH}")

    with open(MANIFEST_PATH, newline="") as f:
        rows = list(csv.DictReader(f))

    words = get_supported_word_signs()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    written = []
    missing = []
    for word in words:
        clip_row = _first_train_clip(rows, word)
        if clip_row is None:
            missing.append((word, "no clip in manifest"))
            continue

        clip_path = REPO_ROOT / clip_row["local_path"]
        if not clip_path.exists():
            missing.append((word, f"clip file missing on disk: {clip_path}"))
            continue

        frame = _extract_middle_frame(clip_path)
        if frame is None:
            missing.append((word, "could not decode any frame from clip"))
            continue

        height, width = frame.shape[:2]
        if width > MAX_WIDTH:
            scale = MAX_WIDTH / width
            frame = cv2.resize(frame, (MAX_WIDTH, round(height * scale)), interpolation=cv2.INTER_AREA)

        out_path = OUTPUT_DIR / f"{_slug(word)}.jpg"
        cv2.imwrite(str(out_path), frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
        written.append((word, clip_row["clip_id"], out_path.name))

    print(f"Wrote {len(written)}/{len(words)} reference images to {OUTPUT_DIR}")
    for word, clip_id, filename in written:
        print(f"  {word!r:<16} <- {clip_id}  ->  {filename}")
    if missing:
        print(f"\n{len(missing)} word(s) got no reference image:")
        for word, reason in missing:
            print(f"  {word!r}: {reason}")


if __name__ == "__main__":
    main()
