"""
Renders a Certificate row to a printable PDF — landscape, centered,
decorative border, unlike the data-table reports (report_pdf_service.py,
reporting_pdf_service.py) this deliberately doesn't share style constants
with: a certificate is meant to be printed/framed, not read as a table of
numbers, so it earns its own layout rather than forcing the reports'
table-first style onto a document that has none.

Helvetica-only (no external font files), same constraint as every other
PDF service in this codebase — reportlab's built-in fonts render
identically wherever this runs, with nothing to fetch or bundle.
"""

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import Paragraph

from app.schemas.certificate import CertificateResponse

_BORDER_COLOR = colors.HexColor("#1f6f5c")
_ACCENT_COLOR = colors.HexColor("#1f6f5c")
_MUTED_COLOR = colors.HexColor("#555555")
_FAINT_COLOR = colors.HexColor("#888888")

PAGE_SIZE = landscape(letter)
PAGE_WIDTH, PAGE_HEIGHT = PAGE_SIZE


def _styles():
    base = getSampleStyleSheet()
    return {
        "eyebrow": ParagraphStyle(
            "Eyebrow", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=12,
            textColor=_ACCENT_COLOR, alignment=TA_CENTER, tracking=2,
        ),
        "title": ParagraphStyle(
            "CertTitle", parent=base["Title"], fontName="Helvetica-Bold", fontSize=30,
            alignment=TA_CENTER, textColor=colors.HexColor("#1a1a1a"), spaceAfter=0,
        ),
        "presented_to": ParagraphStyle(
            "PresentedTo", parent=base["Normal"], fontName="Helvetica", fontSize=13,
            alignment=TA_CENTER, textColor=_MUTED_COLOR,
        ),
        "learner_name": ParagraphStyle(
            "LearnerName", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=26,
            alignment=TA_CENTER, textColor=colors.HexColor("#1a1a1a"),
        ),
        "body": ParagraphStyle(
            "Body", parent=base["Normal"], fontName="Helvetica", fontSize=13,
            alignment=TA_CENTER, textColor=_MUTED_COLOR, leading=18,
        ),
        "course": ParagraphStyle(
            "Course", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=17,
            alignment=TA_CENTER, textColor=_ACCENT_COLOR,
        ),
        "footer": ParagraphStyle(
            "Footer", parent=base["Normal"], fontName="Helvetica", fontSize=9,
            alignment=TA_CENTER, textColor=_FAINT_COLOR,
        ),
    }


def render_certificate_pdf(certificate: CertificateResponse, learner_name: str) -> bytes:
    styles = _styles()
    buffer = BytesIO()
    c = pdfcanvas.Canvas(buffer, pagesize=PAGE_SIZE)
    c.setTitle(f"Certificate of Completion - {certificate.course_title}")

    # Decorative double border, inset from the page edge — the one place
    # this file draws directly on the canvas rather than flowing
    # Paragraphs, since a certificate's frame is fixed layout, not
    # reflowable content.
    margin = 0.45 * inch
    c.setStrokeColor(_BORDER_COLOR)
    c.setLineWidth(2.4)
    c.rect(margin, margin, PAGE_WIDTH - 2 * margin, PAGE_HEIGHT - 2 * margin)
    inner_margin = margin + 0.12 * inch
    c.setLineWidth(0.8)
    c.rect(inner_margin, inner_margin, PAGE_WIDTH - 2 * inner_margin, PAGE_HEIGHT - 2 * inner_margin)

    content_width = PAGE_WIDTH - 2.2 * inch

    def draw_centered(paragraph_style_key: str, text: str, y: float, max_width: float = content_width) -> float:
        paragraph = Paragraph(text, styles[paragraph_style_key])
        w, h = paragraph.wrap(max_width, PAGE_HEIGHT)
        paragraph.drawOn(c, (PAGE_WIDTH - w) / 2, y - h)
        return y - h

    y = PAGE_HEIGHT - 1.35 * inch
    y = draw_centered("eyebrow", "SIGN LANGUAGE LEARNING PLATFORM", y) - 0.12 * inch
    y = draw_centered("title", "Certificate of Completion", y) - 0.32 * inch
    y = draw_centered("presented_to", "This certifies that", y) - 0.22 * inch
    y = draw_centered("learner_name", learner_name, y) - 0.3 * inch
    y = draw_centered(
        "body",
        "has successfully completed every sign in the course",
        y,
    ) - 0.16 * inch
    y = draw_centered("course", certificate.course_title, y) - 0.45 * inch

    issued_line = f"Issued {certificate.issued_at.strftime('%B %-d, %Y')} &middot; {certificate.issued_by_name}"
    draw_centered("body", issued_line, y)

    footer_y = margin + 0.32 * inch
    draw_centered(
        "footer",
        f"Verification code: {certificate.verification_code} &mdash; verify at /verify/{certificate.verification_code}",
        footer_y,
    )

    c.showPage()
    c.save()
    return buffer.getvalue()
