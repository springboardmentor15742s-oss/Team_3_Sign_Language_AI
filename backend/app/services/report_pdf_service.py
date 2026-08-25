from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas.report import LearnerReport

EM_DASH = "—"

_HEADER_BG = colors.HexColor("#f0f0f0")
_GRID_COLOR = colors.HexColor("#dddddd")
_STRIPE_COLOR = colors.HexColor("#fafafa")

_TABLE_HEADER_STYLE = [
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
    ("GRID", (0, 0), (-1, -1), 0.5, _GRID_COLOR),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]


def _format_percent(value) -> str:
    return f"{value}%" if value is not None else EM_DASH


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ReportTitle", parent=base["Title"], fontName="Helvetica-Bold", fontSize=18, spaceAfter=4
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle", parent=base["Normal"], fontName="Helvetica", fontSize=10, textColor=colors.grey
        ),
        "heading": ParagraphStyle(
            "SectionHeading",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            spaceBefore=18,
            spaceAfter=6,
        ),
        "body": ParagraphStyle("Body", parent=base["Normal"], fontName="Helvetica", fontSize=10, leading=14),
        "cell": ParagraphStyle("Cell", parent=base["Normal"], fontName="Helvetica", fontSize=9, leading=12),
    }


def render_learner_report_pdf(report: LearnerReport) -> bytes:
    """
    Renders a LearnerReport (assembled by report_service) to PDF bytes via
    reportlab's platypus flowables. Built-in Helvetica only (the 14
    standard fonts reportlab ships with AFM metrics for) — no font files,
    no FreeType, nothing beyond the pip package itself.
    """
    styles = _styles()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        title=f"Learner Progress Report - {report.learner_name}",
    )

    story = []

    # Title block
    story.append(Paragraph(f"Learner Progress Report — {report.learner_name}", styles["title"]))
    story.append(
        Paragraph(
            f"{report.learner_email} &nbsp;&middot;&nbsp; "
            f"Generated {report.generated_at.strftime('%Y-%m-%d %H:%M UTC')}",
            styles["subtitle"],
        )
    )
    story.append(Spacer(1, 0.25 * inch))

    # 4-stat summary row
    summary_header = ["Total attempts", "Scored attempts", "Overall accuracy", "Letters scored"]
    summary_values = [
        str(report.total_attempts),
        str(report.scored_attempts),
        _format_percent(report.overall_accuracy_percent),
        f"{report.letters_scored}/{report.total_letters}",
    ]
    summary_table = Table([summary_header, summary_values], colWidths=[1.6 * inch] * 4)
    summary_table.setStyle(
        TableStyle(
            _TABLE_HEADER_STYLE
            + [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTSIZE", (0, 1), (-1, 1), 14),
                ("TOPPADDING", (0, 1), (-1, 1), 8),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 0.3 * inch))

    # 28-row per-letter table
    story.append(Paragraph("Per-letter accuracy", styles["heading"]))
    letter_rows = [["Letter", "Attempts", "Accuracy"]]
    for entry in report.per_letter:
        letter_rows.append([entry.letter, str(entry.attempts), _format_percent(entry.accuracy_percent)])
    letter_table = Table(letter_rows, colWidths=[1.8 * inch, 1.8 * inch, 1.8 * inch], repeatRows=1)
    letter_table.setStyle(
        TableStyle(
            _TABLE_HEADER_STYLE
            + [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _STRIPE_COLOR]),
            ]
        )
    )
    story.append(letter_table)
    story.append(Spacer(1, 0.3 * inch))

    # Weak areas
    story.append(Paragraph("Weak areas", styles["heading"]))
    threshold = report.weak_area_accuracy_threshold
    min_attempts = report.weak_area_min_scored_attempts
    story.append(
        Paragraph(
            f"Letters below {threshold:.0f}% accuracy with at least {min_attempts} scored attempts are "
            "flagged as weak areas. Fewer attempts than that isn't enough to judge, so those letters "
            "are left off this list even if their accuracy so far is low.",
            styles["body"],
        )
    )
    story.append(Spacer(1, 0.12 * inch))
    if report.weak_areas:
        weak_rows = [["Letter", "Accuracy", "Attempts", "Note"]]
        for w in report.weak_areas:
            weak_rows.append(
                [w.letter, f"{w.accuracy_percent}%", str(w.scored_attempts), Paragraph(w.note, styles["cell"])]
            )
        weak_table = Table(weak_rows, colWidths=[0.7 * inch, 0.9 * inch, 0.9 * inch, 2.9 * inch])
        weak_table.setStyle(
            TableStyle(
                _TABLE_HEADER_STYLE
                + [
                    ("ALIGN", (0, 0), (2, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(weak_table)
    else:
        story.append(Paragraph("No weak areas identified yet.", styles["body"]))
    story.append(Spacer(1, 0.3 * inch))

    # Recommendations
    story.append(Paragraph("Practice next", styles["heading"]))
    if report.recommendations:
        rec_rows = [["#", "Topic", "Type", "Reason"]]
        for i, rec in enumerate(report.recommendations, start=1):
            topic_label = "Motion sign" if rec.topic_type == "motion_sign" else "Letter"
            rec_rows.append([str(i), rec.topic, topic_label, rec.reason])
        rec_table = Table(rec_rows, colWidths=[0.4 * inch, 0.9 * inch, 1.0 * inch, 3.1 * inch])
        rec_table.setStyle(
            TableStyle(_TABLE_HEADER_STYLE + [("ALIGN", (0, 0), (2, -1), "CENTER")])
        )
        story.append(rec_table)
    else:
        story.append(Paragraph("No recommendations available.", styles["body"]))

    # Confusion pairs — only if any exist
    if report.confusion_pairs:
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph("Where it slips", styles["heading"]))
        confusion_rows = [["Target", "Predicted as", "Count"]]
        for pair in report.confusion_pairs:
            confusion_rows.append([pair.target_letter, pair.predicted_letter, str(pair.count)])
        confusion_table = Table(confusion_rows, colWidths=[1.8 * inch, 1.8 * inch, 1.8 * inch])
        confusion_table.setStyle(
            TableStyle(_TABLE_HEADER_STYLE + [("ALIGN", (0, 0), (-1, -1), "CENTER")])
        )
        story.append(confusion_table)

    _append_analytics_workflow_sections(story, styles, report.analytics_workflow)

    doc.build(story)
    return buffer.getvalue()


def _append_analytics_workflow_sections(story, styles, workflow) -> None:
    """
    Task 2 — learning analytics workflow: completion rate, activity
    frequency patterns, commonly-missed/avoided topics, and a
    current-vs-previous performance comparison. Appended as its own
    section of flowables onto the same report `story` rather than a
    separate document, so there is exactly one downloadable report
    containing everything the brief asked for.
    """
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Learning analytics workflow", styles["heading"]))

    # Completion rate by course
    story.append(Paragraph("Completion rate", styles["body"]))
    story.append(Spacer(1, 0.08 * inch))
    completion_rows = [["Course", "Attempted", "Total", "Completion"]]
    for course in workflow.completion_rate.by_course:
        completion_rows.append([
            course.title,
            str(course.attempted_count) if course.attempted_count is not None else EM_DASH,
            str(course.total_count) if course.total_count is not None else EM_DASH,
            _format_percent(course.completion_percent),
        ])
    completion_table = Table(completion_rows, colWidths=[2.2 * inch, 1.2 * inch, 1.0 * inch, 1.4 * inch])
    completion_table.setStyle(
        TableStyle(_TABLE_HEADER_STYLE + [("ALIGN", (1, 0), (-1, -1), "CENTER")])
    )
    story.append(completion_table)
    story.append(Spacer(1, 0.25 * inch))

    # Frequency & activity patterns
    story.append(Paragraph("Activity frequency", styles["body"]))
    story.append(Spacer(1, 0.08 * inch))
    freq = workflow.frequency_patterns
    freq_rows = [
        ["Active days (total)", str(freq.days_active_total)],
        ["Active days (last 7)", str(freq.days_active_last_7)],
        ["Active days (last 30)", str(freq.days_active_last_30)],
        ["Avg. attempts / active day", str(freq.avg_attempts_per_active_day) if freq.avg_attempts_per_active_day is not None else EM_DASH],
        ["Last active", freq.last_active_date or "Never"],
        ["Most active day", freq.most_active_weekday or EM_DASH],
    ]
    freq_table = Table(freq_rows, colWidths=[2.4 * inch, 2.4 * inch])
    freq_table.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, _GRID_COLOR),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(freq_table)
    story.append(Spacer(1, 0.25 * inch))

    # Commonly missed topics
    story.append(Paragraph("Commonly missed topics", styles["body"]))
    story.append(Spacer(1, 0.08 * inch))
    if workflow.commonly_missed:
        missed_rows = [["Topic", "Type", "Times missed", "Accuracy"]]
        for item in workflow.commonly_missed:
            topic_label = "Motion sign" if item.topic_type == "motion_sign" else "Letter"
            missed_rows.append([item.topic, topic_label, str(item.incorrect_count), _format_percent(item.accuracy_percent)])
        missed_table = Table(missed_rows, colWidths=[1.6 * inch, 1.4 * inch, 1.4 * inch, 1.4 * inch])
        missed_table.setStyle(TableStyle(_TABLE_HEADER_STYLE + [("ALIGN", (1, 0), (-1, -1), "CENTER")]))
        story.append(missed_table)
    else:
        story.append(Paragraph("No missed topics recorded yet.", styles["body"]))
    story.append(Spacer(1, 0.2 * inch))

    # Avoided topics
    story.append(Paragraph("Avoided topics (never attempted)", styles["body"]))
    story.append(Spacer(1, 0.08 * inch))
    if workflow.avoided_topics:
        avoided_text = ", ".join(f"{t.topic} ({'motion sign' if t.topic_type == 'motion_sign' else 'letter'})" for t in workflow.avoided_topics)
        story.append(Paragraph(avoided_text, styles["body"]))
    else:
        story.append(Paragraph("Every topic has been attempted at least once.", styles["body"]))
    story.append(Spacer(1, 0.25 * inch))

    # Performance comparison: current vs previous period
    story.append(Paragraph("Current vs. previous performance", styles["body"]))
    story.append(Spacer(1, 0.08 * inch))
    comparison = workflow.performance_comparison
    if comparison.available:
        trend_word = {"improving": "improving", "declining": "declining", "steady": "steady"}.get(comparison.trend, comparison.trend)
        story.append(
            Paragraph(
                f"Current period accuracy: {_format_percent(comparison.current_period.accuracy_percent)} "
                f"({comparison.current_period.scored_attempts} scored attempts). "
                f"Previous period accuracy: {_format_percent(comparison.previous_period.accuracy_percent)} "
                f"({comparison.previous_period.scored_attempts} scored attempts). "
                f"Change: {comparison.accuracy_delta_percent:+.1f} percentage points — {trend_word}.",
                styles["body"],
            )
        )
    else:
        story.append(Paragraph(comparison.reason or "Not enough data yet to compare current and previous performance.", styles["body"]))
