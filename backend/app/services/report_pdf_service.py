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
        rec_rows = [["#", "Letter", "Reason"]]
        for i, rec in enumerate(report.recommendations, start=1):
            rec_rows.append([str(i), rec.letter, rec.reason])
        rec_table = Table(rec_rows, colWidths=[0.4 * inch, 0.8 * inch, 4.2 * inch])
        rec_table.setStyle(
            TableStyle(_TABLE_HEADER_STYLE + [("ALIGN", (0, 0), (1, -1), "CENTER")])
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

    doc.build(story)
    return buffer.getvalue()
