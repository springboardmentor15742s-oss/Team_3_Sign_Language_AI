from sqlalchemy import Column, String, Text, Boolean, ForeignKey, DateTime
from datetime import datetime
from app.database import Base


class InstructorAssignment(Base):
    """
    A practice focus an instructor has pointed a specific learner at —
    e.g. "practice the letter M" or "practice the word 'answer'". This
    is the instructor's one real lever on a learner's experience: it
    doesn't touch recommendation_service's own weak-area/not-yet-tried
    logic (that stays fully automatic and learner-specific), it's a
    second, clearly-labeled source shown alongside it — same "don't
    blend two sources of truth" discipline as everywhere else in this
    codebase (see recommendation_service, history_service).

    completed/completed_at: earlier versions of this model deliberately
    left completion unmodeled, on the reasoning that inferring "done"
    from attempt history is guesswork. That's been superseded by an
    explicit choice to let the learner say so themselves — completed is
    a plain boolean the learner flips via
    PATCH /api/learner/{learner_id}/assignments/{id}/complete, never
    inferred from PracticeAttempt/etc. An instructor can still delete
    an assignment outright; completion is a separate, non-destructive
    signal that sits alongside deletion rather than replacing it.

    notes: optional freeform instructions from the instructor beyond
    just the topic name (e.g. "focus on hand orientation, not speed").

    due_date: optional ISO date string ("YYYY-MM-DD"). Kept as a plain
    validated string rather than a SQL Date column — nothing here does
    date arithmetic server-side; the frontend compares it to "today" for
    an overdue indicator, same "no more structure than something actually
    needs" approach as topic_type.

    reference_media_path/type: an optional photo or short video the
    instructor attaches showing the correct sign — real instructor-
    provided teaching material, not just a link to the learner's own
    practice page. Stored on disk under data/uploads/ (see
    media_upload_service) with only the relative path kept here; the
    router turns that into a /media/... URL when serving the row.
    """

    __tablename__ = "instructor_assignments"

    id = Column(String, primary_key=True)
    learner_id = Column(String, ForeignKey("users.id"), nullable=False)
    instructor_id = Column(String, ForeignKey("users.id"), nullable=False)
    topic = Column(String, nullable=False)
    topic_type = Column(String, nullable=False)  # letter, motion_sign, word_sign
    notes = Column(Text, nullable=True)
    due_date = Column(String, nullable=True)  # "YYYY-MM-DD"
    completed = Column(Boolean, nullable=False, default=False)
    completed_at = Column(DateTime, nullable=True)
    reference_media_path = Column(String, nullable=True)
    reference_media_type = Column(String, nullable=True)  # image, video
    created_at = Column(DateTime, default=datetime.utcnow)
