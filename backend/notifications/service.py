"""
Notification & Reminder System — roadmap section 12.

Deliberately cron-free: instead of a background scheduler, reminders are
computed lazily the moment a user actually loads their notifications (see
routes/notifications.py's list endpoint), and achievement/course-completion
alerts are fired synchronously at the moment the triggering event happens
(a certificate is issued, a lesson-watch completes a course). This covers
all four notification types the roadmap calls for — practice reminders,
achievement alerts, course completion notifications, platform announcements
— without adding a task-queue dependency for a project at this scale.
"""
from datetime import datetime, timezone

from database import db

PRACTICE_REMINDER_DAYS = 3  # nudge if no gesture attempt logged in this many days


def notify_achievement(user_id: int, level: str, certificate_code: str):
    db.create_notification(
        user_id,
        "achievement",
        f"🎓 {level} Certificate Earned!",
        f"Congratulations — you've earned your {level} certificate ({certificate_code}). "
        f"View and download it from the Certifications page.",
    )


def notify_course_completion(user_id: int, course_title: str):
    db.create_notification(
        user_id,
        "course_completion",
        "✅ Course Completed",
        f"You've finished every lesson in \"{course_title}\". Nice work — check the Course Catalog "
        f"for what to learn next.",
    )


def maybe_create_practice_reminder(user_id: int):
    """
    Called opportunistically whenever a user's notifications are listed.
    Creates at most one practice_reminder per calendar day, and only if
    the learner's most recent gesture attempt is stale (or they've never
    practiced at all after having had a few days to start).
    """
    if db.has_practice_reminder_today(user_id):
        return

    last_attempt_at = db.get_last_gesture_attempt_time(user_id)
    if last_attempt_at is None:
        return  # brand-new account — don't nag before they've even started

    try:
        last_dt = datetime.fromisoformat(last_attempt_at.replace(" ", "T"))
    except ValueError:
        return
    if last_dt.tzinfo is None:
        last_dt = last_dt.replace(tzinfo=timezone.utc)

    days_since = (datetime.now(timezone.utc) - last_dt).days
    if days_since >= PRACTICE_REMINDER_DAYS:
        db.create_notification(
            user_id,
            "practice_reminder",
            "👋 Time to practice!",
            f"It's been {days_since} days since your last practice session. "
            f"A quick round of Gesture Practice keeps your accuracy trend climbing.",
        )


def create_announcement(title: str, message: str):
    """Admin-authored platform-wide announcement (user_id=NULL -> broadcast)."""
    return db.create_notification(None, "announcement", title, message)
