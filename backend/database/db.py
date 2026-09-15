"""SQLite connection & CRUD helpers (framework-agnostic, used by FastAPI routes)."""
import os
import sqlite3
from contextlib import contextmanager

from config import DB_PATH

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with open(SCHEMA_PATH, "r") as f:
        schema_sql = f.read()
    with get_connection() as conn:
        conn.executescript(schema_sql)
        _run_migrations(conn)


def _run_migrations(conn):
    """
    Lightweight, additive migrations for people who already had a
    `platform.db` from an earlier version of this project (CREATE TABLE IF
    NOT EXISTS in schema.sql doesn't add new columns to an existing table).
    Safe to run on every startup — each ALTER is wrapped so it's a no-op if
    the column already exists.
    """
    existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(learner_profiles)")}
    if "display_name" not in existing_cols:
        conn.execute("ALTER TABLE learner_profiles ADD COLUMN display_name TEXT")
    if "avatar_data" not in existing_cols:
        conn.execute("ALTER TABLE learner_profiles ADD COLUMN avatar_data TEXT")


# ---------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------
def create_user(username, email, password_hash, salt, role):
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO users (username, email, password_hash, salt, role) "
            "VALUES (?, ?, ?, ?, ?)",
            (username, email, password_hash, salt, role),
        )
        return cur.lastrowid


def get_user_by_username(username):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def update_password(user_id, password_hash, salt):
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
            (password_hash, salt, user_id),
        )


def username_or_email_exists(username, email):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?", (username, email)
        ).fetchone()
        return row is not None


def list_all_users():
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT u.id, u.username, u.email, u.role, u.created_at, u.is_active,
                      COALESCE(lp.learning_level, 'Not set') AS learning_level
               FROM users u
               LEFT JOIN learner_profiles lp ON lp.user_id = u.id
               ORDER BY u.created_at DESC"""
        ).fetchall()
        return [dict(r) for r in rows]


def set_learner_level(user_id, level):
    """Admin override of a learner's level (Admin Panel 'Set Learner Level').
    Creates a bare-defaults profile row first if the user has none yet, same
    pattern as update_profile_identity()."""
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM learner_profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE learner_profiles SET learning_level = ?, updated_at = datetime('now') WHERE user_id = ?",
                (level, user_id),
            )
        else:
            conn.execute(
                "INSERT INTO learner_profiles (user_id, learning_level) VALUES (?, ?)",
                (user_id, level),
            )


def update_user_role(user_id, new_role):
    with get_connection() as conn:
        conn.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))


def set_user_active(user_id, is_active: bool):
    with get_connection() as conn:
        conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (int(is_active), user_id))


# ---------------------------------------------------------------------
# Learner profiles
# ---------------------------------------------------------------------
def upsert_learner_profile(user_id, learning_level, preferred_language, learning_goals, bio):
    goals_str = ",".join(learning_goals) if isinstance(learning_goals, (list, tuple)) else (learning_goals or "")
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM learner_profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
        if existing:
            conn.execute(
                """UPDATE learner_profiles
                   SET learning_level = ?, preferred_language = ?,
                       learning_goals = ?, bio = ?, updated_at = datetime('now')
                   WHERE user_id = ?""",
                (learning_level, preferred_language, goals_str, bio, user_id),
            )
        else:
            conn.execute(
                """INSERT INTO learner_profiles
                   (user_id, learning_level, preferred_language, learning_goals, bio)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, learning_level, preferred_language, goals_str, bio),
            )


def get_learner_profile(user_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM learner_profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None


def update_profile_identity(user_id, display_name, avatar_data):
    """
    Updates just the 'normal app profile' fields (display name + photo)
    without touching learning preferences. Creates a bare-defaults profile
    row first if the user hasn't set one up yet, so the Profile page's
    identity card always has something to save into.
    """
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM learner_profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
        if existing:
            conn.execute(
                """UPDATE learner_profiles
                   SET display_name = ?, avatar_data = ?, updated_at = datetime('now')
                   WHERE user_id = ?""",
                (display_name, avatar_data, user_id),
            )
        else:
            conn.execute(
                """INSERT INTO learner_profiles (user_id, display_name, avatar_data)
                   VALUES (?, ?, ?)""",
                (user_id, display_name, avatar_data),
            )
        row = conn.execute(
            "SELECT * FROM learner_profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
        return dict(row)


# ---------------------------------------------------------------------
# Practice history
# ---------------------------------------------------------------------
def log_practice_activity(user_id, activity):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO practice_history (user_id, activity) VALUES (?, ?)",
            (user_id, activity),
        )


def get_practice_history(user_id, limit=10):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM practice_history WHERE user_id = ? ORDER BY logged_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------
# Gesture attempts (Milestone 2 — Gesture Recognition & Accuracy Assessment)
# ---------------------------------------------------------------------
def log_gesture_attempt(user_id, target_label, detected_label, matched,
                         hand_shape_accuracy, position_accuracy, overall_accuracy, feedback_json):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO gesture_attempts
               (user_id, target_label, detected_label, matched,
                hand_shape_accuracy, position_accuracy, overall_accuracy, feedback)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, target_label, detected_label, int(matched),
             hand_shape_accuracy, position_accuracy, overall_accuracy, feedback_json),
        )


def get_gesture_history(user_id, limit=20):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM gesture_attempts WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def get_all_gesture_attempts(user_id, limit=1000):
    """
    Full (chronological, oldest-first) attempt history for a learner — used
    by the Milestone 3 Learning Intelligence engine for analytics, weak-area
    detection, and trend/forecast calculations. Unlike get_gesture_history()
    (newest-first, used for the recent-activity feed), this is ordered
    ascending so index position == attempt order for trend fitting.
    """
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM gesture_attempts WHERE user_id = ? ORDER BY created_at ASC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def get_last_gesture_attempt_time(user_id):
    """Most recent gesture_attempts.created_at for a learner, or None if
    they've never logged a single attempt. Used by the practice-reminder
    notification logic to decide if a learner has gone quiet."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT created_at FROM gesture_attempts WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            (user_id,),
        ).fetchone()
        return row["created_at"] if row else None


def get_gesture_stats(user_id):
    with get_connection() as conn:
        row = conn.execute(
            """SELECT COUNT(*) AS total_attempts,
                      COALESCE(AVG(overall_accuracy), 0) AS avg_accuracy,
                      COALESCE(SUM(matched), 0) AS matched_count,
                      COALESCE(MAX(overall_accuracy), 0) AS best_accuracy
               FROM gesture_attempts WHERE user_id = ?""",
            (user_id,),
        ).fetchone()
        by_gesture = conn.execute(
            """SELECT target_label,
                      COUNT(*) AS attempts,
                      COALESCE(AVG(overall_accuracy), 0) AS avg_accuracy,
                      COALESCE(SUM(matched), 0) AS matched_count
               FROM gesture_attempts WHERE user_id = ?
               GROUP BY target_label""",
            (user_id,),
        ).fetchall()
        return {
            "total_attempts": row["total_attempts"],
            "avg_accuracy": round(row["avg_accuracy"], 1),
            "matched_count": row["matched_count"],
            "best_accuracy": round(row["best_accuracy"], 1),
            "by_gesture": [dict(r) for r in by_gesture],
        }


# ---------------------------------------------------------------------
# Assessment reports (Milestone 3 — Learning Intelligence "Generate
# assessment reports" task)
# ---------------------------------------------------------------------
def log_assessment_report(user_id, total_attempts, overall_accuracy, weak_area_count, strong_area_count):
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO assessment_reports
               (user_id, total_attempts, overall_accuracy, weak_area_count, strong_area_count)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, total_attempts, overall_accuracy, weak_area_count, strong_area_count),
        )
        row = conn.execute(
            "SELECT * FROM assessment_reports WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return dict(row)


def get_report_history(user_id, limit=10):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM assessment_reports WHERE user_id = ? ORDER BY generated_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------
# Certificates (Milestone 4 — "Implement Certification Workflows")
# ---------------------------------------------------------------------
def create_certificate(user_id, certificate_code, level, overall_accuracy,
                        total_attempts, gestures_certified):
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO certificates
               (user_id, certificate_code, level, overall_accuracy, total_attempts, gestures_certified)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, certificate_code, level, overall_accuracy, total_attempts, gestures_certified),
        )
        row = conn.execute("SELECT * FROM certificates WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)


def get_certificate_by_code(code):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT c.*, u.username FROM certificates c JOIN users u ON u.id = c.user_id "
            "WHERE c.certificate_code = ?",
            (code,),
        ).fetchone()
        return dict(row) if row else None


def get_certificate_by_id(cert_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT c.*, u.username FROM certificates c JOIN users u ON u.id = c.user_id WHERE c.id = ?",
            (cert_id,),
        ).fetchone()
        return dict(row) if row else None


def get_user_certificates(user_id):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM certificates WHERE user_id = ? ORDER BY issued_at DESC", (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_all_certificates(limit=200):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT c.*, u.username FROM certificates c JOIN users u ON u.id = c.user_id "
            "ORDER BY c.issued_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def user_already_has_active_certificate(user_id, level):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM certificates WHERE user_id = ? AND level = ? AND status = 'Active'",
            (user_id, level),
        ).fetchone()
        return row is not None


def update_certificate_status(cert_id, status):
    """Admin certificate revocation / reactivation — the `certificates.status`
    column already supported 'Active'/'Revoked' (see schema.sql), this is
    the first write-path that actually flips it."""
    with get_connection() as conn:
        conn.execute("UPDATE certificates SET status = ? WHERE id = ?", (status, cert_id))
        row = conn.execute(
            "SELECT c.*, u.username FROM certificates c JOIN users u ON u.id = c.user_id WHERE c.id = ?",
            (cert_id,),
        ).fetchone()
        return dict(row) if row else None


# ---------------------------------------------------------------------
# Cross-learner overview (Milestone 4 — Instructor/Admin reporting:
# "Class progress tracking" / "Student performance")
# ---------------------------------------------------------------------
def get_all_learners_overview():
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT u.id AS user_id, u.username, u.role,
                      COALESCE(lp.learning_level, 'Not set') AS learning_level,
                      COUNT(ga.id) AS total_attempts,
                      COALESCE(AVG(ga.overall_accuracy), 0) AS overall_accuracy,
                      COALESCE(SUM(ga.matched), 0) AS matched_count
               FROM users u
               LEFT JOIN learner_profiles lp ON lp.user_id = u.id
               LEFT JOIN gesture_attempts ga ON ga.user_id = u.id
               WHERE u.role = 'Learner'
               GROUP BY u.id
               ORDER BY overall_accuracy DESC"""
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["overall_accuracy"] = round(d["overall_accuracy"], 1)
            result.append(d)
        return result


# ---------------------------------------------------------------------
# Course & Content Service (courses, lessons, enrollments, lesson progress)
# ---------------------------------------------------------------------
def create_course(title, description, category, level, thumbnail_emoji, created_by):
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO courses (title, description, category, level, thumbnail_emoji, created_by)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (title, description, category, level, thumbnail_emoji or "🤟", created_by),
        )
        return cur.lastrowid


def count_courses():
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM courses").fetchone()
        return row["c"]


def list_courses(category=None, level=None, search=None):
    query = """
        SELECT c.*,
               COUNT(l.id) AS lesson_count
        FROM courses c
        LEFT JOIN lessons l ON l.course_id = c.id
        WHERE 1=1
    """
    params = []
    if category:
        query += " AND c.category = ?"
        params.append(category)
    if level:
        query += " AND c.level = ?"
        params.append(level)
    if search:
        query += " AND (c.title LIKE ? OR c.description LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like])
    query += " GROUP BY c.id ORDER BY c.created_at DESC"
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_course(course_id):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
        return dict(row) if row else None


def list_lessons(course_id):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM lessons WHERE course_id = ? ORDER BY sort_order ASC, id ASC",
            (course_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_lesson(lesson_id):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,)).fetchone()
        return dict(row) if row else None


def create_lesson(course_id, title, description, video_id, duration_seconds, sort_order=None):
    with get_connection() as conn:
        if sort_order is None:
            row = conn.execute(
                "SELECT COALESCE(MAX(sort_order), -1) + 1 AS next_order FROM lessons WHERE course_id = ?",
                (course_id,),
            ).fetchone()
            sort_order = row["next_order"]
        cur = conn.execute(
            """INSERT INTO lessons (course_id, title, description, video_id, duration_seconds, sort_order)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (course_id, title, description, video_id, duration_seconds, sort_order),
        )
        return cur.lastrowid


def enroll_user(user_id, course_id):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO enrollments (user_id, course_id) VALUES (?, ?)",
            (user_id, course_id),
        )


def is_enrolled(user_id, course_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM enrollments WHERE user_id = ? AND course_id = ?",
            (user_id, course_id),
        ).fetchone()
        return row is not None


def list_my_enrollments(user_id):
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT c.*, e.enrolled_at,
                      COUNT(DISTINCT l.id) AS lesson_count,
                      COUNT(DISTINCT CASE WHEN lp.watched = 1 THEN lp.lesson_id END) AS watched_count
               FROM enrollments e
               JOIN courses c ON c.id = e.course_id
               LEFT JOIN lessons l ON l.course_id = c.id
               LEFT JOIN lesson_progress lp ON lp.lesson_id = l.id AND lp.user_id = e.user_id
               WHERE e.user_id = ?
               GROUP BY c.id
               ORDER BY e.enrolled_at DESC""",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_lesson_progress_map(user_id, course_id):
    """Returns {lesson_id: True} for every lesson in this course the user has watched."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT lp.lesson_id
               FROM lesson_progress lp
               JOIN lessons l ON l.id = lp.lesson_id
               WHERE lp.user_id = ? AND l.course_id = ? AND lp.watched = 1""",
            (user_id, course_id),
        ).fetchall()
        return {r["lesson_id"] for r in rows}


def mark_lesson_watched(user_id, lesson_id):
    """Marks a lesson watched and auto-enrolls the learner in its course if needed."""
    lesson = get_lesson(lesson_id)
    if not lesson:
        return None
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO enrollments (user_id, course_id) VALUES (?, ?)",
            (user_id, lesson["course_id"]),
        )
        existing = conn.execute(
            "SELECT id FROM lesson_progress WHERE user_id = ? AND lesson_id = ?",
            (user_id, lesson_id),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE lesson_progress SET watched = 1, watched_at = datetime('now') WHERE id = ?",
                (existing["id"],),
            )
        else:
            conn.execute(
                "INSERT INTO lesson_progress (user_id, lesson_id, watched, watched_at) "
                "VALUES (?, ?, 1, datetime('now'))",
                (user_id, lesson_id),
            )
    return get_course_progress(user_id, lesson["course_id"])


def get_course_progress(user_id, course_id):
    with get_connection() as conn:
        total = conn.execute(
            "SELECT COUNT(*) AS c FROM lessons WHERE course_id = ?", (course_id,)
        ).fetchone()["c"]
        watched = conn.execute(
            """SELECT COUNT(*) AS c FROM lesson_progress lp
               JOIN lessons l ON l.id = lp.lesson_id
               WHERE lp.user_id = ? AND l.course_id = ? AND lp.watched = 1""",
            (user_id, course_id),
        ).fetchone()["c"]
        percent = round((watched / total) * 100, 1) if total else 0.0
        return {"course_id": course_id, "total_lessons": total, "watched_lessons": watched, "percent": percent}


# ---------------------------------------------------------------------
# Notification & Reminder System
# ---------------------------------------------------------------------
def create_notification(user_id, type_, title, message):
    """user_id=None creates a broadcast platform announcement, visible to
    every user, instead of a personal notification."""
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO notifications (user_id, type, title, message)
               VALUES (?, ?, ?, ?)""",
            (user_id, type_, title, message),
        )
        row = conn.execute("SELECT * FROM notifications WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)


def list_notifications_for_user(user_id, limit=30):
    """Personal notifications merged with broadcast announcements, most
    recent first. A broadcast announcement shows as unread for a user
    until they explicitly dismiss it (tracked the same way as personal
    ones — is_read is per-row, and broadcasts are cheap enough at this
    scale that we don't need a separate per-user read-state table)."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT * FROM notifications
               WHERE user_id = ? OR user_id IS NULL
               ORDER BY created_at DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def count_unread_notifications(user_id):
    with get_connection() as conn:
        row = conn.execute(
            """SELECT COUNT(*) AS c FROM notifications
               WHERE (user_id = ? OR user_id IS NULL) AND is_read = 0""",
            (user_id,),
        ).fetchone()
        return row["c"]


def mark_notification_read(notification_id, user_id):
    with get_connection() as conn:
        conn.execute(
            """UPDATE notifications SET is_read = 1
               WHERE id = ? AND (user_id = ? OR user_id IS NULL)""",
            (notification_id, user_id),
        )


def mark_all_notifications_read(user_id):
    with get_connection() as conn:
        conn.execute(
            "UPDATE notifications SET is_read = 1 WHERE user_id = ? OR user_id IS NULL",
            (user_id,),
        )


def has_practice_reminder_today(user_id):
    """Avoid spamming duplicate reminders — checks if a practice_reminder
    notification was already created for this user today."""
    with get_connection() as conn:
        row = conn.execute(
            """SELECT id FROM notifications
               WHERE user_id = ? AND type = 'practice_reminder'
                 AND date(created_at) = date('now')""",
            (user_id,),
        ).fetchone()
        return row is not None


# ---------------------------------------------------------------------
# Dataset log
# ---------------------------------------------------------------------
def log_dataset_action(dataset_name, action, details, performed_by=None):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO dataset_log (dataset_name, action, details, performed_by)
               VALUES (?, ?, ?, ?)""",
            (dataset_name, action, details, performed_by),
        )


def get_dataset_log(limit=20):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM dataset_log ORDER BY performed_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------
# Quiz / Knowledge-Check module
# ---------------------------------------------------------------------
def count_quiz_questions():
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) AS c FROM quiz_questions").fetchone()["c"]


def create_quiz_question(level, topic, question_text, option_a, option_b, option_c, option_d,
                          correct_option, explanation):
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO quiz_questions
               (level, topic, question_text, option_a, option_b, option_c, option_d,
                correct_option, explanation)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (level, topic, question_text, option_a, option_b, option_c, option_d,
             correct_option, explanation),
        )
        return cur.lastrowid


def list_quiz_questions_for_taking(level, limit=5):
    """Random selection for a learner to *take* — deliberately excludes
    correct_option/explanation so the answer key never reaches the client
    before grading."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT id, level, topic, question_text, option_a, option_b, option_c, option_d
               FROM quiz_questions WHERE level = ? ORDER BY RANDOM() LIMIT ?""",
            (level, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def get_quiz_questions_by_ids(question_ids):
    """Full rows (including the answer key) — used server-side only, for grading."""
    if not question_ids:
        return []
    placeholders = ",".join("?" for _ in question_ids)
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT * FROM quiz_questions WHERE id IN ({placeholders})", question_ids
        ).fetchall()
        return [dict(r) for r in rows]


def create_quiz_attempt(user_id, level, score, total_questions):
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO quiz_attempts (user_id, level, score, total_questions)
               VALUES (?, ?, ?, ?)""",
            (user_id, level, score, total_questions),
        )
        row = conn.execute("SELECT * FROM quiz_attempts WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)


def get_quiz_attempts(user_id, limit=10):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM quiz_attempts WHERE user_id = ? ORDER BY taken_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
