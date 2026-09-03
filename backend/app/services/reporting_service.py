"""
Reporting module: exportable/viewable reports for instructors (their
own roster) and admins (the whole platform) — the same functions serve
both, since instructor_id=None already means "platform-wide" throughout
this codebase (see class_analytics_service, instructor_service). Which
scope a caller gets is entirely up to the router's _roster_scope()
helper; nothing in here special-cases a role.

Pure data assembly, same discipline as report_service.py's learner
report: every number here comes from an existing, already-trusted
service (class_analytics_service, learning_analytics_service) or a
direct, simple query — never a second copy of accuracy/weak-area math.
"""

from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models.instructor_assignment import InstructorAssignment
from app.models.user import User
from app.services.class_analytics_service import get_class_analytics, get_roster_learner_ids
from app.services.learning_analytics_service import get_learner_analytics


def _scope_label(instructor_id: str = None) -> str:
    return "platform" if instructor_id is None else "roster"


def assemble_class_report(db: Session, instructor_id: str = None) -> dict:
    """
    The class-analytics numbers (already shown live on the roster page)
    plus a printable/exportable roster listing — one learner per row,
    each with their own real accuracy, not just the class average.
    """
    analytics = get_class_analytics(db, instructor_id=instructor_id)
    learner_ids = get_roster_learner_ids(db, instructor_id)

    roster = []
    if learner_ids:
        users_by_id = {u.id: u for u in db.query(User).filter(User.id.in_(learner_ids)).all()}
        for learner_id in learner_ids:
            user = users_by_id.get(learner_id)
            if user is None:
                continue  # stale roster row pointing at a deleted user — skip, don't crash the report
            learner_analytics = get_learner_analytics(db, learner_id)
            roster.append({
                "learner_id": learner_id,
                "name": user.name,
                "email": user.email,
                "total_attempts": learner_analytics["total_attempts"],
                "overall_accuracy_percent": learner_analytics["overall_accuracy_percent"],
            })
    roster.sort(key=lambda entry: entry["name"].lower())

    return {
        "scope": _scope_label(instructor_id),
        "generated_at": datetime.utcnow(),
        "roster": roster,
        **analytics,
    }


def assemble_assignment_report(db: Session, instructor_id: str = None) -> dict:
    """
    Every assignment across the given scope (roster or platform), with
    completion/overdue status — the one report that's about the
    instructor's own lever on learners (assignments) rather than
    learners' own practice accuracy. overdue is computed the same way
    AssignedFocusPanel.tsx's isOverdue() does client-side (due_date in
    the past, string-compared against today, and not yet completed) —
    recomputed here rather than stored, so it's never stale.
    """
    learner_ids = get_roster_learner_ids(db, instructor_id)
    today = date.today().isoformat()

    rows = []
    if learner_ids:
        assignments = (
            db.query(InstructorAssignment)
            .filter(InstructorAssignment.learner_id.in_(learner_ids))
            .order_by(InstructorAssignment.created_at.desc())
            .all()
        )
        users_by_id = {u.id: u for u in db.query(User).filter(User.id.in_(learner_ids)).all()}
        for assignment in assignments:
            learner = users_by_id.get(assignment.learner_id)
            overdue = bool(assignment.due_date and assignment.due_date < today and not assignment.completed)
            rows.append({
                "learner_id": assignment.learner_id,
                "learner_name": learner.name if learner else "(unknown learner)",
                "learner_email": learner.email if learner else "",
                "topic": assignment.topic,
                "topic_type": assignment.topic_type,
                "notes": assignment.notes,
                "due_date": assignment.due_date,
                "completed": bool(assignment.completed),
                "completed_at": assignment.completed_at,
                "overdue": overdue,
                "created_at": assignment.created_at,
            })

    completed_count = sum(1 for row in rows if row["completed"])
    overdue_count = sum(1 for row in rows if row["overdue"])

    return {
        "scope": _scope_label(instructor_id),
        "generated_at": datetime.utcnow(),
        "total_count": len(rows),
        "completed_count": completed_count,
        "outstanding_count": len(rows) - completed_count,
        "overdue_count": overdue_count,
        "rows": rows,
    }
