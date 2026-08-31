"""
Quick manual check that sign_assessment_service correctly scores
gesture_recognition_service predictions end-to-end: a correct match, an
incorrect match, and a no-hand-detected case. Run from backend/:

    venv/bin/python scripts/test_sign_assessment.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.gesture_recognition_service import recognize_gesture_from_path
from app.services.sign_assessment_service import assess_sign

TEST_DIR = (
    Path(__file__).resolve().parent.parent
    / "data" / "asl_alphabet" / "asl_alphabet_test" / "asl_alphabet_test"
)

# (image filename, target_letter given to the learner, expected status)
CASES = [
    ("F_test.jpg", "F", "pass"),
    ("K_test.jpg", "Z", "fail"),
    ("nothing_test.jpg", "A", "no_attempt_detected"),
]


def main():
    passed = 0
    for filename, target_letter, expected_status in CASES:
        gesture_result = recognize_gesture_from_path(str(TEST_DIR / filename))
        assessment = assess_sign(gesture_result, target_letter)

        ok = assessment["status"] == expected_status
        passed += ok
        status = "PASS" if ok else "FAIL"
        print(
            f"[{status}] {filename} target={target_letter} -> "
            f"status={assessment['status']} correct={assessment['correct']} "
            f"predicted={assessment['predicted_letter']} confidence={assessment['confidence']}"
        )

    print(f"\n{passed}/{len(CASES)} checks passed")


if __name__ == "__main__":
    main()
