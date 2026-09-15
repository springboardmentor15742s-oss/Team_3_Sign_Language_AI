"""
Reporting routes — Milestone 4 ("Build Reporting Modules").

    GET /api/reports/learning                    JSON learning report (summary + gesture breakdown)
    GET /api/reports/learning/pdf                 Learning Report (PDF)
    GET /api/reports/accuracy/csv                 Accuracy Report (CSV)
    GET /api/reports/accuracy/pdf                 Accuracy Report (PDF)
    GET /api/reports/progress/csv                 Progress Report (CSV, chronological)
    GET /api/reports/progress/pdf                 Progress Report (PDF)
    GET /api/reports/certification/csv            Certification Report (CSV, this learner's certs)
    GET /api/reports/certification/pdf            Certification Report (PDF)
    GET /api/reports/class-overview               Instructor/Admin — JSON, one row per learner
    GET /api/reports/class-overview/csv           Instructor/Admin — same, as CSV
    GET /api/reports/class-overview/pdf           Instructor/Admin — same, as PDF
"""
from fastapi import APIRouter, Depends, Response
from fastapi.responses import PlainTextResponse

from database import db
from deps import get_current_user, require_roles
from intelligence.analytics import compute_analytics, compute_performance_trend
from reporting.reports import (
    ACCURACY_FIELDS,
    CERTIFICATION_FIELDS,
    CLASS_OVERVIEW_FIELDS,
    PROGRESS_FIELDS,
    accuracy_report_rows,
    certification_report_rows,
    class_overview_rows,
    progress_report_rows,
    to_csv,
)
from reporting.pdf_report import build_learning_report_pdf, build_table_pdf

router = APIRouter(prefix="/api/reports", tags=["reports"])

FIELD_LABELS = {
    "avg_accuracy": "Avg Accuracy", "best_accuracy": "Best Accuracy", "worst_accuracy": "Worst Accuracy",
    "skill_level": "Skill Level", "attempt_no": "Attempt #", "overall_accuracy": "Accuracy",
    "logged_at": "Logged At", "certificate_code": "Certificate Code", "gestures_certified": "Signs Certified",
    "issued_at": "Issued At", "learning_level": "Level", "total_attempts": "Total Attempts",
    "matched_count": "Matched", "display_name": "Sign",
}


def _csv_response(text: str, filename: str) -> PlainTextResponse:
    return PlainTextResponse(
        content=text,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _pdf_response(pdf_bytes: bytes, filename: str) -> Response:
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _learning_report_data(current_user: dict) -> dict:
    a = compute_analytics(current_user["id"])
    trend = compute_performance_trend(current_user["id"])
    return {
        "username": current_user["username"],
        "total_attempts": a["total_attempts"],
        "overall_accuracy": a["overall_accuracy"],
        "best_accuracy": a["best_accuracy"],
        "gestures_practiced": len(a["by_gesture"]),
        "weak_area_count": len(a["weak_areas"]),
        "strong_area_count": len(a["strong_areas"]),
        "trend": trend.get("trend"),
        "gesture_breakdown": a["by_gesture"],
    }


@router.get("/learning")
def learning_report(current_user=Depends(get_current_user)):
    """Learning Report — a JSON overview combining accuracy + consistency,
    the roadmap's 'Learning reports' outcome."""
    return _learning_report_data(current_user)


@router.get("/learning/pdf")
def learning_report_pdf(current_user=Depends(get_current_user)):
    report = _learning_report_data(current_user)
    pdf_bytes = build_learning_report_pdf(report)
    return _pdf_response(pdf_bytes, f"learning-report-{current_user['username']}.pdf")


@router.get("/accuracy/csv")
def accuracy_report_csv(current_user=Depends(get_current_user)):
    a = compute_analytics(current_user["id"])
    rows = accuracy_report_rows(a)
    csv_text = to_csv(rows, ACCURACY_FIELDS)
    return _csv_response(csv_text, f"accuracy-report-{current_user['username']}.csv")


@router.get("/accuracy/pdf")
def accuracy_report_pdf(current_user=Depends(get_current_user)):
    a = compute_analytics(current_user["id"])
    rows = accuracy_report_rows(a)
    pdf_bytes = build_table_pdf(
        "Accuracy Report", f"Learner: {current_user['username']}", rows, ACCURACY_FIELDS, FIELD_LABELS
    )
    return _pdf_response(pdf_bytes, f"accuracy-report-{current_user['username']}.pdf")


@router.get("/progress/csv")
def progress_report_csv(current_user=Depends(get_current_user)):
    trend = compute_performance_trend(current_user["id"])
    rows = progress_report_rows(trend.get("points", []))
    csv_text = to_csv(rows, PROGRESS_FIELDS)
    return _csv_response(csv_text, f"progress-report-{current_user['username']}.csv")


@router.get("/progress/pdf")
def progress_report_pdf(current_user=Depends(get_current_user)):
    trend = compute_performance_trend(current_user["id"])
    rows = progress_report_rows(trend.get("points", []))
    pdf_bytes = build_table_pdf(
        "Progress Report", f"Learner: {current_user['username']}", rows, PROGRESS_FIELDS, FIELD_LABELS
    )
    return _pdf_response(pdf_bytes, f"progress-report-{current_user['username']}.pdf")


@router.get("/certification/csv")
def certification_report_csv(current_user=Depends(get_current_user)):
    certs = db.get_user_certificates(current_user["id"])
    rows = certification_report_rows(certs)
    csv_text = to_csv(rows, CERTIFICATION_FIELDS)
    return _csv_response(csv_text, f"certification-report-{current_user['username']}.csv")


@router.get("/certification/pdf")
def certification_report_pdf(current_user=Depends(get_current_user)):
    certs = db.get_user_certificates(current_user["id"])
    rows = certification_report_rows(certs)
    pdf_bytes = build_table_pdf(
        "Certification Report", f"Learner: {current_user['username']}", rows, CERTIFICATION_FIELDS, FIELD_LABELS
    )
    return _pdf_response(pdf_bytes, f"certification-report-{current_user['username']}.pdf")


@router.get("/class-overview")
def class_overview(current_user=Depends(require_roles("Instructor", "Administrator", "Accessibility Trainer"))):
    return db.get_all_learners_overview()


@router.get("/class-overview/csv")
def class_overview_csv(current_user=Depends(require_roles("Instructor", "Administrator", "Accessibility Trainer"))):
    learners = db.get_all_learners_overview()
    rows = class_overview_rows(learners)
    csv_text = to_csv(rows, CLASS_OVERVIEW_FIELDS)
    return _csv_response(csv_text, "class-overview-report.csv")


@router.get("/class-overview/pdf")
def class_overview_pdf(current_user=Depends(require_roles("Instructor", "Administrator", "Accessibility Trainer"))):
    learners = db.get_all_learners_overview()
    rows = class_overview_rows(learners)
    pdf_bytes = build_table_pdf(
        "Class Overview Report", f"Prepared by: {current_user['username']}", rows, CLASS_OVERVIEW_FIELDS, FIELD_LABELS
    )
    return _pdf_response(pdf_bytes, "class-overview-report.pdf")
