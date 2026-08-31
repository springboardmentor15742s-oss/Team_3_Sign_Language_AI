from sqlalchemy import Column, String, ForeignKey, DateTime
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

    No status/completion field: deliberately not inferring "done" from
    attempt history here (which topic attempt would even count, and as
    of when?) — an instructor removes an assignment themselves once
    it's no longer relevant, which is honest rather than guessed.

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
    reference_media_path = Column(String, nullable=True)
    reference_media_type = Column(String, nullable=True)  # image, video
    created_at = Column(DateTime, default=datetime.utcnow)
