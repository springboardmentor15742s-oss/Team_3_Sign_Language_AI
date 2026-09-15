"""
AI Feedback & Correction Engine — Milestone 3.

Milestone 2's accuracy.py already generates per-attempt feedback strings
("Curl your ring finger into your palm", etc.) and logs them to
gesture_attempts.feedback. This module is the Milestone-3 upgrade the
roadmap calls for: it looks *across* a learner's whole attempt history
(via analytics.compute_analytics) instead of one attempt at a time, and
produces:

    - which gestures the learner is doing well on (strengths)
    - which gestures need more work (weaknesses)
    - the single most common corrective note for each weak gesture, mined
      from the real feedback text already stored per attempt (the roadmap's
      "mistake identification")
    - a short natural-language summary tying it together

Nothing here is hard-coded per user — every message is built from that
learner's own logged practice attempts.
"""
import json
from collections import Counter

from database import db

_PRAISE_PREFIXES = ("great job",)


def _common_issue(user_id: int, target_label: str):
    """
    Mines the JSON-encoded feedback strings already stored per attempt
    (from gesture/accuracy.py) for the most frequent corrective note on a
    given gesture — i.e. the learner's recurring mistake, not just their
    last one.
    """
    rows = db.get_all_gesture_attempts(user_id)
    notes = []
    for r in rows:
        if r["target_label"] != target_label or not r.get("feedback"):
            continue
        try:
            items = json.loads(r["feedback"])
        except (TypeError, ValueError):
            continue
        notes.extend(items)

    # Praise strings aren't "issues" — filter them out before counting.
    notes = [n for n in notes if not n.lower().startswith(_PRAISE_PREFIXES)]
    if not notes:
        return None
    most_common, _count = Counter(notes).most_common(1)[0]
    return most_common


def generate_feedback(analytics: dict, user_id: int) -> dict:
    """
    Returns:
        {
            "summary": str,                # one-line AI feedback message
            "strengths": [display_name...],
            "weaknesses": [display_name...],
            "issues": [{"gesture", "display_name", "common_issue"}...],
            "messages": [str, ...],        # full multi-line feedback, dashboard-ready
        }
    """
    if not analytics["has_data"]:
        return {
            "summary": "No practice attempts yet — try a few gestures in Gesture Practice to unlock personalized feedback.",
            "strengths": [],
            "weaknesses": [],
            "issues": [],
            "messages": [],
        }

    strengths = [g["display_name"] for g in analytics["strong_areas"]]
    weak = analytics["weak_areas"]
    weaknesses = [g["display_name"] for g in weak]

    messages = []
    if strengths:
        messages.append(f"You are performing well on {', '.join(strengths)}.")

    issues = []
    if weak:
        messages.append(f"You need more practice with {', '.join(weaknesses)}.")
        for g in weak:
            issue = _common_issue(user_id, g["gesture"])
            if issue:
                issues.append(
                    {"gesture": g["gesture"], "display_name": g["display_name"], "common_issue": issue}
                )
                messages.append(f"{g['display_name']}: focus on this — {issue}")
    elif analytics["total_attempts"] > 0:
        messages.append("Great consistency — no weak areas detected right now. Keep it up!")

    summary = " ".join(messages) if messages else "Keep practicing to build your feedback profile."

    return {
        "summary": summary,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "issues": issues,
        "messages": messages,
    }
