"""
Automated, skill-tiered feedback engine — Task 1 of the mentor-assigned
work (August 2026): generate feedback for completed activities covering
errors, performance, and areas requiring improvement, personalized to
the learner's current skill level so a beginner never receives
master-level critique.

Two layers, both required by the brief:

1. generate_activity_feedback() — immediate, tiered feedback for ONE
   just-completed activity (a single sign_assessment_service /
   motion_sign_service result), extending feedback_service's plain
   pass/fail message with a structured errors/performance/improvement
   breakdown, phrased for the learner's current tier.

2. get_learner_feedback() — an aggregate feedback report for the
   dashboard, built entirely from already-tested data
   (adaptive_learning_service's live-recomputed plan, confusion_service,
   learning_analytics_service / motion_sign_analytics_service) rather
   than a parallel aggregation — no new source of truth for accuracy
   numbers, just a tiered narrative + structuring layer on top.

Skill tiers reuse adaptive_learning_service's own beginner/intermediate/
advanced levels (same thresholds, same "insufficient evidence defaults
to beginner" rule) so a learner's tier here always matches what the
adaptive learning plan and dashboard already call them — no second,
disagreeing definition of "beginner".
"""

from sqlalchemy.orm import Session

from app.services.adaptive_learning_service import get_adaptive_learning_plan
from app.services.confusion_service import get_confusion_pairs
from app.services.feedback_service import generate_feedback
from app.services.learning_analytics_service import get_learner_analytics
from app.services.motion_sign_analytics_service import get_motion_sign_analytics

MAX_ERROR_ITEMS = 5
MAX_CONFUSION_ITEMS = 3
MAX_IMPROVEMENT_ITEMS = 3

_TIER_SUMMARY = {
    "beginner": "You're early in your practice — focus on getting the fundamentals right before speed or variety.",
    "intermediate": "You've built a real foundation. Focus your practice on the specific gaps below to keep leveling up.",
    "advanced": "Your accuracy is strong overall. What's left is fine-tuning the few remaining weak spots.",
}

_TOPIC_LABEL = {"letter": "handshape", "motion_sign": "motion sign"}


def generate_activity_feedback(assessment_result: dict, learner_level: str, topic_type: str = "letter") -> dict:
    """
    Structured, tiered feedback for ONE just-completed activity attempt.
    assessment_result is a sign_assessment_service / motion_sign_service
    -shaped dict with a "status" of pass/fail/no_attempt_detected and
    either "target_letter" or "target_sign". Same underlying facts as
    feedback_service.generate_feedback, restructured with explicit
    error/performance/improvement fields and tiered phrasing so a
    beginner gets encouragement-first wording and an advanced learner
    gets a more direct, technical note — never the reverse.
    """
    if learner_level not in ("beginner", "intermediate", "advanced"):
        raise ValueError(f"Unknown learner_level: {learner_level}")

    target = assessment_result.get("target_letter") or assessment_result.get("target_sign")
    status = assessment_result["status"]
    label = _TOPIC_LABEL.get(topic_type, "sign")

    error = None
    improvement_tip = None

    if status == "pass":
        performance_note = (
            f"Nice work! Your '{target}' {label} was correct."
            if learner_level == "beginner"
            else f"Correct — '{target}' matched at the expected standard."
        )
        message = performance_note
    elif status == "fail":
        if learner_level == "beginner":
            performance_note = f"That attempt at '{target}' wasn't quite right — that's normal this early."
            error = f"Your '{target}' {label} wasn't recognized correctly. Go slowly and double-check the reference image before retrying."
            improvement_tip = f"Practice '{target}' a few more times on its own before moving to a new {label}."
        elif learner_level == "intermediate":
            performance_note = f"'{target}' was marked incorrect."
            error = f"'{target}' didn't match — check hand orientation and finger position against the reference."
            improvement_tip = f"Add '{target}' to your next practice session and compare it against signs it's commonly confused with."
        else:
            performance_note = f"'{target}' did not match the expected {label}."
            error = f"'{target}' failed assessment — likely a fine positioning or orientation error given your overall accuracy."
            improvement_tip = f"Isolate '{target}' in a short, focused drill and review it closely before your next assessment."
        message = error
    else:  # no_attempt_detected
        performance_note = "No hand was detected for this attempt."
        error = "We couldn't detect your hand in frame."
        improvement_tip = "Make sure your hand is clearly visible and well lit, then try again."
        message = generate_feedback({**assessment_result, "target_letter": target}) if topic_type == "letter" else error

    return {
        "topic": target,
        "topic_type": topic_type,
        "status": status,
        "learner_level": learner_level,
        "message": message,
        "performance": performance_note,
        "error": error,
        "improvement_tip": improvement_tip,
    }


def get_learner_feedback(db: Session, learner_id: str) -> dict:
    """
    Aggregate, dashboard-facing feedback report: errors, performance, and
    areas requiring improvement, tiered to the learner's current level.
    Rebuilt fresh on every call from the adaptive learning plan (itself
    always rebuilt from the latest attempts) plus confusion pairs and
    combined accuracy totals — never cached/stale, and never a second
    definition of accuracy that could disagree with the dashboard.
    """
    plan = get_adaptive_learning_plan(db, learner_id)
    analytics = get_learner_analytics(db, learner_id)
    motion_analytics = get_motion_sign_analytics(db, learner_id)
    confusion = get_confusion_pairs(db, learner_id)["pairs"]
    level = plan["learning_level"]

    combined_scored = analytics["scored_attempts"] + motion_analytics["scored_attempts"]

    # --- errors: concrete things that went wrong, tiered in tone and depth ---
    errors = []
    for topic in plan["weak_topics"][:MAX_ERROR_ITEMS]:
        label = _TOPIC_LABEL.get(topic["topic_type"], "topic")
        if level == "beginner":
            detail = (
                f"'{topic['topic']}' is still tricky — {topic['accuracy_percent']}% correct so far. "
                f"That's completely normal this early; slow down and focus on getting the {label} right, not fast."
            )
        elif level == "intermediate":
            detail = (
                f"'{topic['topic']}' sits at {topic['accuracy_percent']}% accuracy over "
                f"{topic['scored_attempts']} scored attempts — below the 70% consistency mark."
            )
        else:
            detail = (
                f"'{topic['topic']}' is your lowest-scoring {label} at {topic['accuracy_percent']}% — "
                f"likely a fine positioning or orientation issue given your overall accuracy."
            )
        errors.append({
            "topic": topic["topic"], "topic_type": topic["topic_type"],
            "accuracy_percent": topic["accuracy_percent"], "scored_attempts": topic["scored_attempts"],
            "detail": detail,
        })

    # Confusion-pair detail is a finer-grained diagnostic than a beginner
    # has the reps to act on yet — shown from intermediate up only. This
    # is the concrete mechanism behind "a beginner must not get
    # master-level feedback": the data exists, but it's withheld by tier.
    if level != "beginner":
        for pair in confusion[:MAX_CONFUSION_ITEMS]:
            errors.append({
                "topic": pair["target_letter"], "topic_type": "letter",
                "accuracy_percent": None, "scored_attempts": None,
                "detail": (
                    f"'{pair['target_letter']}' is most often mistaken for '{pair['predicted_letter']}' "
                    f"({pair['count']} time{'s' if pair['count'] != 1 else ''}) — compare the two hand shapes side by side."
                ),
            })

    # --- performance: the honest current standing; tiered in tone only,
    # the numbers themselves are identical at every tier ---
    performance = {
        "learning_level": level,
        "overall_accuracy_percent": plan["overall_accuracy_percent"],
        "scored_attempts": combined_scored,
        "summary": (
            _TIER_SUMMARY[level] if plan["overall_accuracy_percent"] is not None
            else "No scored attempts yet — complete a few practice attempts to get your first feedback."
        ),
    }

    # --- areas requiring improvement: the same weak/needs-practice topics
    # the adaptive plan already prioritizes, restated as improvement
    # actions with their suggested activities attached ---
    improvement_source = (plan["weak_topics"] or plan["needs_more_practice"])[:MAX_IMPROVEMENT_ITEMS]
    areas_for_improvement = []
    for topic in improvement_source:
        activities = next(
            (
                r["activities"] for r in plan["recommendations"]
                if r["topic"] == topic["topic"] and r["topic_type"] == topic["topic_type"]
            ),
            [],
        )
        areas_for_improvement.append({
            "topic": topic["topic"], "topic_type": topic["topic_type"],
            "accuracy_percent": topic["accuracy_percent"],
            "suggested_activities": activities,
        })

    return {
        "learner_id": learner_id,
        "learner_level": level,
        "generated_from_attempts": combined_scored,
        "errors": errors,
        "performance": performance,
        "areas_for_improvement": areas_for_improvement,
    }
