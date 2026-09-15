"""
PDF Certificate Generator — Milestone 4.

Renders an issued certificate (see certification/rules.py) as a polished,
single-page landscape PDF modeled on the "LinkedIn certificate of
completion" style: a bordered card, issuer branding, recipient name as the
visual focus, credential metadata in a footer strip, and a QR-free
plain-text verification line (since it must be readable when printed).

This is the "real" PDF export for certificates — the browser print-to-PDF
view in the frontend still exists as a quick preview, but this endpoint
(`GET /api/certification/{id}/download/pdf`) is what actually gets handed
to an employer.
"""
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

PURPLE = colors.HexColor("#6D28D9")
PURPLE_DARK = colors.HexColor("#5B21B6")
INK = colors.HexColor("#1F2430")
MUTED = colors.HexColor("#6B7280")
GOLD = colors.HexColor("#C99B2E")
PAGE_W, PAGE_H = landscape(A4)


def _centered_text(c, text, y, font, size, color=INK):
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawCentredString(PAGE_W / 2, y, text)


def build_certificate_pdf(cert: dict) -> bytes:
    """
    cert: the dict returned by db.create_certificate()/get_certificate_by_id(),
    i.e. {username, level, overall_accuracy, total_attempts,
    gestures_certified, certificate_code, issued_at, status}.
    Returns raw PDF bytes.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))

    margin = 14 * mm
    # Outer double-border frame, LinkedIn/traditional-certificate style
    c.setStrokeColor(PURPLE)
    c.setLineWidth(2.4)
    c.rect(margin, margin, PAGE_W - 2 * margin, PAGE_H - 2 * margin)
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.8)
    inner = margin + 5 * mm
    c.rect(inner, inner, PAGE_W - 2 * inner, PAGE_H - 2 * inner)

    # Header — issuer / brand
    _centered_text(c, "SIGN LANGUAGE LEARNING & ASSESSMENT PLATFORM",
                    PAGE_H - margin - 20 * mm, "Helvetica-Bold", 13, PURPLE_DARK)
    _centered_text(c, "Certificate of Achievement",
                    PAGE_H - margin - 30 * mm, "Helvetica", 12, MUTED)

    # Gold divider
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.2)
    line_w = 60 * mm
    y_div = PAGE_H - margin - 36 * mm
    c.line(PAGE_W / 2 - line_w / 2, y_div, PAGE_W / 2 + line_w / 2, y_div)

    # "This certifies that"
    _centered_text(c, "This certifies that", PAGE_H - margin - 48 * mm, "Helvetica", 12, MUTED)

    # Recipient name — the visual focus
    _centered_text(c, cert["username"], PAGE_H - margin - 62 * mm, "Helvetica-Bold", 30, INK)

    # Achievement line
    _centered_text(
        c,
        f"has successfully achieved the {cert['level']} level",
        PAGE_H - margin - 74 * mm, "Helvetica", 13, INK,
    )
    _centered_text(
        c,
        "in Sign Language Learning & Assessment",
        PAGE_H - margin - 82 * mm, "Helvetica", 13, INK,
    )

    # Stats row
    stats_y = PAGE_H - margin - 98 * mm
    stat_items = [
        (f"{cert['overall_accuracy']}%", "Overall Accuracy"),
        (f"{cert['total_attempts']}", "Practice Attempts"),
        (f"{cert['gestures_certified']}", "Signs Certified"),
    ]
    col_w = 60 * mm
    start_x = PAGE_W / 2 - (len(stat_items) * col_w) / 2
    for i, (value, label) in enumerate(stat_items):
        cx = start_x + col_w * i + col_w / 2
        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(PURPLE_DARK)
        c.drawCentredString(cx, stats_y, value)
        c.setFont("Helvetica", 9)
        c.setFillColor(MUTED)
        c.drawCentredString(cx, stats_y - 12, label)

    # Footer strip: issue date, credential code, verification, signature line
    footer_y = margin + 16 * mm
    c.setStrokeColor(colors.HexColor("#E5E5EE"))
    c.setLineWidth(0.6)
    c.line(inner + 10 * mm, footer_y + 14 * mm, PAGE_W - inner - 10 * mm, footer_y + 14 * mm)

    c.setFont("Helvetica", 9)
    c.setFillColor(MUTED)
    c.drawString(inner + 10 * mm, footer_y, f"Issued: {cert['issued_at']}")
    c.drawString(inner + 10 * mm, footer_y - 10, f"Credential ID: {cert['certificate_code']}")

    verify_text = f"Verify at: /api/certification/verify/{cert['certificate_code']}"
    c.drawRightString(PAGE_W - inner - 10 * mm, footer_y, verify_text)
    status_text = f"Status: {cert['status']}"
    c.drawRightString(PAGE_W - inner - 10 * mm, footer_y - 10, status_text)

    # Signature-style seal (text-based, no external image dependency)
    c.setFont("Helvetica-Oblique", 11)
    c.setFillColor(PURPLE)
    c.drawCentredString(PAGE_W / 2, footer_y + 22, "— AI Sign Language Learning & Assessment Platform —")

    c.showPage()
    c.save()
    return buffer.getvalue()
