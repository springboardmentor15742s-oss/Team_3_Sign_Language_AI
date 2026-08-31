"""
Quick manual check that the full gesture recognition pipeline (hand
tracking -> normalization -> classifier) works end-to-end against real
images from the ASL Alphabet test set. Run from backend/:

    venv/bin/python scripts/test_gesture_recognition.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.gesture_recognition_service import recognize_gesture_from_path

TEST_DIR = (
    Path(__file__).resolve().parent.parent
    / "data" / "asl_alphabet" / "asl_alphabet_test" / "asl_alphabet_test"
)

# (image filename, expected label) — "nothing" has no hand in frame, so it
# should come back as None rather than a (wrong) prediction.
#
# Note: MediaPipe fails to detect a hand at all on some of these single
# test images (framing/crop differs from the training set) — that's a
# hand-tracking recall limitation, not a classifier error. See
# skipped_images.log from prepare_gesture_dataset.py for the base rate.
# The letters below are ones MediaPipe reliably tracks, so this script
# stays a meaningful smoke test of the full pipeline.
SAMPLES = [
    ("F_test.jpg", "F"),
    ("K_test.jpg", "K"),
    ("L_test.jpg", "L"),
    ("space_test.jpg", "space"),
    ("nothing_test.jpg", None),
]


def main():
    passed = 0
    for filename, expected in SAMPLES:
        image_path = TEST_DIR / filename
        result = recognize_gesture_from_path(str(image_path))

        if expected is None:
            ok = result is None
            outcome = "no hand detected (expected)" if ok else f"unexpectedly got {result}"
        else:
            ok = result is not None and result["letter"] == expected
            outcome = (
                f"predicted {result['letter']} (confidence {result['confidence']:.2f})"
                if result is not None
                else "no hand detected (unexpected)"
            )

        passed += ok
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {filename} (expected: {expected}) -> {outcome}")

    print(f"\n{passed}/{len(SAMPLES)} checks passed")


if __name__ == "__main__":
    main()
