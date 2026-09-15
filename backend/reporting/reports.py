"""
Reporting Modules — Milestone 4 ("Build Reporting Modules").

Milestone 3 already has one report type (the combined Assessment Report in
intelligence/report.py). This module adds the other report types the
roadmap's "Reports & Export System" calls for — Accuracy Report, Progress
Report, Certification Report, and a cross-learner Class/Learning Report for
instructors — each exportable as CSV (opens directly in Excel/Sheets,
covering the roadmap's "Excel export" outcome without a binary dependency).

Every builder here takes data that's already been computed elsewhere
(analytics.py, certification/rules.py, db.py) — this module's only job is
turning that data into flat, exportable rows.
"""
import csv
import io


def to_csv(rows: list, fieldnames: list) -> str:
    """Renders a list of dicts as CSV text (Excel/Sheets-compatible)."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue()


def accuracy_report_rows(analytics: dict) -> list:
    """One row per gesture: how accurately the learner performs it."""
    return [
        {
            "gesture": g["gesture"],
            "display_name": g["display_name"],
            "avg_accuracy": g["avg_accuracy"],
            "best_accuracy": g["best_accuracy"],
            "worst_accuracy": g["worst_accuracy"],
            "attempts": g["attempts"],
            "skill_level": g["level"],
        }
        for g in analytics.get("by_gesture", [])
    ]


ACCURACY_FIELDS = ["gesture", "display_name", "avg_accuracy", "best_accuracy",
                    "worst_accuracy", "attempts", "skill_level"]


def progress_report_rows(trend_points: list) -> list:
    """One row per attempt, chronological — shows accuracy changing over time."""
    return [
        {
            "attempt_no": p["index"],
            "gesture": p["gesture"],
            "display_name": p["display_name"],
            "overall_accuracy": p["overall_accuracy"],
            "matched": "Yes" if p["matched"] else "No",
            "logged_at": p["created_at"],
        }
        for p in trend_points
    ]


PROGRESS_FIELDS = ["attempt_no", "gesture", "display_name", "overall_accuracy", "matched", "logged_at"]


def certification_report_rows(certificates: list) -> list:
    return [
        {
            "certificate_code": c["certificate_code"],
            "level": c["level"],
            "overall_accuracy": c["overall_accuracy"],
            "total_attempts": c["total_attempts"],
            "gestures_certified": c["gestures_certified"],
            "status": c["status"],
            "issued_at": c["issued_at"],
        }
        for c in certificates
    ]


CERTIFICATION_FIELDS = ["certificate_code", "level", "overall_accuracy", "total_attempts",
                         "gestures_certified", "status", "issued_at"]


def class_overview_rows(learners: list) -> list:
    """Instructor/Admin 'Class progress tracking' — one row per learner."""
    return [
        {
            "username": l["username"],
            "learning_level": l["learning_level"],
            "total_attempts": l["total_attempts"],
            "overall_accuracy": l["overall_accuracy"],
            "matched_count": l["matched_count"],
        }
        for l in learners
    ]


CLASS_OVERVIEW_FIELDS = ["username", "learning_level", "total_attempts", "overall_accuracy", "matched_count"]
