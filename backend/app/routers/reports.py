import re
from io import BytesIO

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.auth_dependency import require_self_or_staff
from app.services.report_pdf_service import render_learner_report_pdf
from app.services.report_service import assemble_learner_report

router = APIRouter(prefix="/api/reports", tags=["Reports"])


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "learner"


@router.get("/learner/{learner_id}/pdf")
def get_learner_report_pdf(
    learner_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_self_or_staff),
):
    report = assemble_learner_report(db, learner_id)
    pdf_bytes = render_learner_report_pdf(report)

    filename = f"progress-report-{_slugify(report.learner_name)}-{report.generated_at.date().isoformat()}.pdf"

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
