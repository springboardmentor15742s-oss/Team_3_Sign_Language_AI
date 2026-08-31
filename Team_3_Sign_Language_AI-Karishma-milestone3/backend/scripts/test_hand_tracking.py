"""
Quick manual check that MediaPipe Hand Landmarker is working end-to-end
against a real image from the ASL Alphabet dataset. Run from backend/:

    venv/bin/python scripts/test_hand_tracking.py [optional/path/to/image.jpg]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.hand_tracking_service import detect_hand_landmarks_from_path

DEFAULT_IMAGE = (
    Path(__file__).resolve().parent.parent
    / "data" / "asl_alphabet" / "asl_alphabet_test" / "asl_alphabet_test" / "F_test.jpg"
)


def main():
    image_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_IMAGE
    print(f"Running hand detection on: {image_path}")

    hands = detect_hand_landmarks_from_path(str(image_path))

    if not hands:
        print("No hands detected.")
        return

    print(f"Detected {len(hands)} hand(s):\n")
    for i, hand in enumerate(hands):
        print(f"Hand {i + 1}: {hand['handedness']} (confidence: {hand['confidence']:.2f})")
        for j, lm in enumerate(hand["landmarks"]):
            print(f"  {j:2d}: x={lm['x']:.4f} y={lm['y']:.4f} z={lm['z']:.4f}")
        print()


if __name__ == "__main__":
    main()
