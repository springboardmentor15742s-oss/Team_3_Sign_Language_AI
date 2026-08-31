"""
Quick manual check that assessment_report_service correctly summarizes a
practice session built from real sign_assessment_service results. Run
from backend/:

    venv/bin/python scripts/test_assessment_report.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.assessment_report_service import generate_session_report
from app.services.sign_assessment_service import assess_sign

# (target_letter, gesture_result) — gesture_result mirrors what
# gesture_recognition_service would return; None simulates no hand detected.
SESSION = [
    ("A", {"letter": "A", "confidence": 0.95}),  # pass
    ("A", {"letter": "A", "confidence": 0.88}),  # pass
    ("A", {"letter": "B", "confidence": 0.61}),  # fail
    ("B", {"letter": "B", "confidence": 0.90}),  # pass
    ("B", None),  # no_attempt_detected
    ("F", {"letter": "F", "confidence": 0.74}),  # pass
    ("L", None),  # no_attempt_detected
    ("L", {"letter": "L", "confidence": 0.83}),  # pass
    ("L", {"letter": "K", "confidence": 0.70}),  # fail
]


def main():
    results = [assess_sign(gesture_result, target_letter) for target_letter, gesture_result in SESSION]

    print("=== Assessment results ===")
    for r in results:
        print(r)

    report = generate_session_report(results)

    print("\n=== Session report ===")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
