"""
PDF Reporting — Milestone 4 ("Build Reporting Modules", PDF export).

CSV covers Excel/Sheets; this module adds a polished PDF rendering of the
same report data using reportlab's Platypus layer (flowable tables), so
every report type in reports.py can also be handed out as a PDF, not just
downloaded as raw CSV rows.
"""
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

PURPLE = colors.HexColor("#6D28D9")
PURPLE_DARK = colors.HexColor("#5B21B6")
INK = colors.HexColor("#1F2430")
MUTED = colors.HexColor("#6B7280")
ROW_ALT = colors.HexColor("#F7F7FB")

_styles = getSampleStyleSheet()
_title_style = ParagraphStyle("ReportTitle", parent=_styles["Title"], textColor=PURPLE_DARK, fontSize=20)
_subtitle_style = ParagraphStyle("ReportSubtitle", parent=_styles["Normal"], textColor=MUTED, fontSize=10)
_section_style = ParagraphStyle("Section", parent=_styles["Heading2"], textColor=PURPLE_DARK, fontSize=13,
                                 spaceBefore=14, spaceAfter=6)
_body_style = ParagraphStyle("Body", parent=_styles["Normal"], textColor=INK, fontSize=10, leading=14)


def _header(title: str, subtitle: str) -> list:
    return [
        Paragraph("SIGN LANGUAGE LEARNING &amp; ASSESSMENT PLATFORM", _subtitle_style),
        Paragraph(title, _title_style),
        Paragraph(subtitle, _subtitle_style),
        Spacer(1, 10 * mm),
    ]


def build_table_pdf(title: str, subtitle: str, rows: list, fieldnames: list,
                     field_labels: dict = None) -> bytes:
    """
    Generic tabular report PDF — used for Accuracy / Progress / Certification
    / Class Overview reports. `field_labels` optionally maps a field key to
    a nicer column header (defaults to a title-cased version of the key).
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=18 * mm, bottomMargin=16 * mm, leftMargin=16 * mm, rightMargin=16 * mm,
    )
    field_labels = field_labels or {}
    header_row = [field_labels.get(f, f.replace("_", " ").title()) for f in fieldnames]

    story = _header(title, subtitle)

    if not rows:
        story.append(Paragraph("No data logged yet.", _body_style))
    else:
        table_data = [header_row]
        for row in rows:
            table_data.append([str(row.get(f, "")) for f in fieldnames])

        table = Table(table_data, repeatRows=1, hAlign="LEFT")
        style = [
            ("BACKGROUND", (0, 0), (-1, 0), PURPLE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E5EE")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]
        table.setStyle(TableStyle(style))
        story.append(table)

    doc.build(story)
    return buffer.getvalue()


def build_learning_report_pdf(report: dict) -> bytes:
    """Learning Report PDF — the summary-style report (not a flat table)."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=18 * mm, bottomMargin=16 * mm, leftMargin=16 * mm, rightMargin=16 * mm,
    )
    story = _header("Learning Report", f"Learner: {report['username']}")

    story.append(Paragraph("Overview", _section_style))
    overview_rows = [
        ["Total Attempts", str(report["total_attempts"])],
        ["Overall Accuracy", f"{report['overall_accuracy']}%"],
        ["Best Accuracy", f"{report['best_accuracy']}%"],
        ["Gestures Practiced", str(report["gestures_practiced"])],
        ["Strong Areas", str(report["strong_area_count"])],
        ["Weak Areas", str(report["weak_area_count"])],
    ]
    if report.get("trend"):
        overview_rows.append(["Performance Trend", report["trend"]["direction"].title()])
    overview_table = Table(overview_rows, colWidths=[65 * mm, 100 * mm])
    overview_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E5EE")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, ROW_ALT]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(overview_table)

    if report.get("gesture_breakdown"):
        story.append(Paragraph("Gesture Breakdown", _section_style))
        gb_header = ["Gesture", "Avg Accuracy", "Attempts", "Skill Level"]
        gb_rows = [gb_header] + [
            [g["display_name"], f"{g['avg_accuracy']}%", str(g["attempts"]), g["level"]]
            for g in report["gesture_breakdown"]
        ]
        gb_table = Table(gb_rows, repeatRows=1, hAlign="LEFT")
        gb_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PURPLE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E5EE")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(gb_table)

    doc.build(story)
    return buffer.getvalue()
