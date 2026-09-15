"""
Assessment Report Generator — Milestone 3 ("Generate assessment reports").

Milestone 2 already logs one row per gesture attempt and Milestone 3's other
modules already turn that history into analytics, feedback, recommendations,
and a learning plan (see analytics.py / feedback.py / recommendations.py /
learning_plan.py). This module is the last step: it assembles all four into
one dated, shareable **Assessment Report** for a learner — the artifact an
instructor or the learner themselves would actually want to look back at or
hand off — and renders it as both JSON (for the dashboard) and plain text
(for download), matching the roadmap's "Assessment reports" / "Progress
reports" outcomes.

Nothing new is computed here: every figure is passed in from
analytics.compute_analytics(), feedback.generate_feedback(),
recommendations.generate_recommendations(), and
learning_plan.build_learning_plan(), so the report can never disagree with
what the dashboard already shows.
"""
from datetime import datetime, timezone


def build_assessment_report(user: dict, profile: dict | None, analytics: dict,
                             feedback: dict, recommendations: list, plan: dict) -> dict:
    """
    Returns a full, self-contained Assessment Report:

        {
            "report_id": "...",            # human-readable, time-based
            "generated_at": ISO timestamp,
            "learner": {username, role, learning_level, preferred_language},
            "overview": {
                total_attempts, overall_accuracy, best_accuracy,
                matched_count, match_rate, gestures_practiced,
            },
            "gesture_breakdown": [...],     # analytics.by_gesture, report-ready
            "strengths": [...],
            "weaknesses": [...],
            "feedback_summary": str,
            "feedback_messages": [...],
            "recommendations": [...],
            "learning_plan": {...},
        }
    """
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    report_id = f"AR-{user['id']}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    total_attempts = analytics.get("total_attempts", 0)
    matched_count = analytics.get("matched_count", 0)
    match_rate = round((matched_count / total_attempts) * 100, 1) if total_attempts else 0.0

    overview = {
        "total_attempts": total_attempts,
        "overall_accuracy": analytics.get("overall_accuracy", 0.0),
        "best_accuracy": analytics.get("best_accuracy", 0.0),
        "matched_count": matched_count,
        "match_rate": match_rate,
        "gestures_practiced": len(analytics.get("by_gesture", [])),
    }

    return {
        "report_id": report_id,
        "generated_at": generated_at,
        "learner": {
            "username": user.get("username"),
            "role": user.get("role"),
            "learning_level": (profile or {}).get("learning_level") or "Not set",
            "preferred_language": (profile or {}).get("preferred_language") or "Not set",
        },
        "overview": overview,
        "gesture_breakdown": analytics.get("by_gesture", []),
        "strengths": [g["display_name"] for g in analytics.get("strong_areas", [])],
        "weaknesses": [g["display_name"] for g in analytics.get("weak_areas", [])],
        "feedback_summary": feedback.get("summary", ""),
        "feedback_messages": feedback.get("messages", []),
        "recommendations": recommendations,
        "learning_plan": plan,
    }


def render_report_text(report: dict) -> str:
    """
    Renders the report as plain text — used for the downloadable
    `/api/intelligence/report/download` response. Deliberately plain text
    (not PDF/Excel — that binary export tooling is Milestone 4's Reports &
    Export System) but fully self-contained and readable on its own.
    """
    lines = []
    lines.append("=" * 60)
    lines.append("SIGN LANGUAGE LEARNING & ASSESSMENT PLATFORM")
    lines.append("Assessment Report")
    lines.append("=" * 60)
    lines.append(f"Report ID:     {report['report_id']}")
    lines.append(f"Generated at:  {report['generated_at']}")
    learner = report["learner"]
    lines.append(f"Learner:       {learner['username']} ({learner['role']})")
    lines.append(f"Learning level: {learner['learning_level']}")
    lines.append(f"Preferred language: {learner['preferred_language']}")
    lines.append("")

    ov = report["overview"]
    lines.append("-- Overview " + "-" * 47)
    lines.append(f"Total gesture attempts:  {ov['total_attempts']}")
    lines.append(f"Overall accuracy:        {ov['overall_accuracy']}%")
    lines.append(f"Best accuracy:           {ov['best_accuracy']}%")
    lines.append(f"Matched attempts:        {ov['matched_count']} ({ov['match_rate']}%)")
    lines.append(f"Distinct gestures tried: {ov['gestures_practiced']}")
    lines.append("")

    lines.append("-- Gesture Breakdown " + "-" * 38)
    if report["gesture_breakdown"]:
        for g in report["gesture_breakdown"]:
            lines.append(
                f"  {g['display_name']:<28} avg {g['avg_accuracy']:>5}%  "
                f"({g['attempts']} attempts)  [{g['level']}]"
            )
    else:
        lines.append("  No gesture attempts logged yet.")
    lines.append("")

    lines.append("-- Strengths / Weaknesses " + "-" * 33)
    lines.append(f"  Strengths: {', '.join(report['strengths']) or 'None yet'}")
    lines.append(f"  Weaknesses: {', '.join(report['weaknesses']) or 'None'}")
    lines.append("")

    lines.append("-- AI Feedback " + "-" * 45)
    lines.append(f"  {report['feedback_summary'] or 'No feedback yet.'}")
    lines.append("")

    lines.append("-- Recommendations " + "-" * 40)
    if report["recommendations"]:
        for r in report["recommendations"]:
            trend = r.get("trend")
            trend_note = f" (trend: {trend['direction']})" if trend else ""
            lines.append(
                f"  - {r['display_name']}: practice {r['practice_count']}x — {r['reason']}{trend_note}"
            )
    else:
        lines.append("  No recommendations yet — practice a few gestures first.")
    lines.append("")

    lines.append("-- Today's Learning Plan " + "-" * 34)
    plan = report["learning_plan"]
    lines.append(f"  {plan.get('headline', '')}")
    for item in plan.get("items", []):
        lines.append(f"    {item['order']}. {item['display_name']} — {item['practice_count']} attempts")
    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)
