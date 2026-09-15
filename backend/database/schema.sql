-- Sign Language Learning & Assessment Platform
-- Milestone 1 database schema (SQLite)

CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT UNIQUE NOT NULL,
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    salt            TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN
                        ('Learner', 'Instructor', 'Accessibility Trainer', 'Administrator')),
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    is_active       INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS learner_profiles (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER UNIQUE NOT NULL,
    display_name        TEXT,
    avatar_data         TEXT,
    learning_level      TEXT NOT NULL DEFAULT 'Beginner',
    preferred_language  TEXT NOT NULL DEFAULT 'ASL (American Sign Language)',
    learning_goals      TEXT,
    bio                 TEXT,
    updated_at          TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS practice_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    activity    TEXT NOT NULL,
    logged_at   TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Milestone 2: logged results from the Gesture Recognition & Accuracy
-- Assessment engines (one row per practice attempt).
CREATE TABLE IF NOT EXISTS gesture_attempts (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL,
    target_label        TEXT NOT NULL,
    detected_label      TEXT,
    matched             INTEGER NOT NULL DEFAULT 0,
    hand_shape_accuracy REAL NOT NULL,
    position_accuracy   REAL NOT NULL,
    overall_accuracy    REAL NOT NULL,
    feedback            TEXT,          -- JSON-encoded list of feedback strings
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Milestone 3: a log entry every time a learner (or an instructor viewing
-- their profile) generates an Assessment Report from the Learning
-- Intelligence engine. Lets the Learner/Instructor dashboards show report
-- history without recomputing analytics for past snapshots.
CREATE TABLE IF NOT EXISTS assessment_reports (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL,
    total_attempts      INTEGER NOT NULL,
    overall_accuracy    REAL NOT NULL,
    weak_area_count     INTEGER NOT NULL DEFAULT 0,
    strong_area_count   INTEGER NOT NULL DEFAULT 0,
    generated_at        TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Milestone 4: issued certifications ("Implement Certification Workflows").
-- A certificate is only inserted after the eligibility rules in
-- backend/certification/rules.py pass against the learner's live analytics
-- at the moment of issue — this table is the permanent record + the
-- verifiable code used by /api/certification/verify/{code}.
CREATE TABLE IF NOT EXISTS certificates (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL,
    certificate_code    TEXT UNIQUE NOT NULL,
    level               TEXT NOT NULL CHECK (level IN
                            ('Beginner', 'Intermediate', 'Advanced', 'Professional')),
    overall_accuracy    REAL NOT NULL,
    total_attempts      INTEGER NOT NULL,
    gestures_certified  INTEGER NOT NULL DEFAULT 0,
    status              TEXT NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Revoked')),
    issued_at           TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Course & Content Service: sign-language course catalog + lessons
-- (video-based, YouTube-style watch experience) + per-learner enrollment
-- and lesson-watched progress tracking.
CREATE TABLE IF NOT EXISTS courses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL,
    description     TEXT NOT NULL DEFAULT '',
    category        TEXT NOT NULL CHECK (category IN
                        ('Beginner Sign Language', 'Intermediate Sign Language',
                         'Advanced Sign Language', 'Everyday Communication',
                         'Educational Vocabulary', 'Professional Communication')),
    level           TEXT NOT NULL CHECK (level IN
                        ('Beginner', 'Intermediate', 'Advanced', 'Professional')),
    thumbnail_emoji TEXT NOT NULL DEFAULT '🤟',
    created_by      INTEGER,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (created_by) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS lessons (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id           INTEGER NOT NULL,
    title               TEXT NOT NULL,
    description         TEXT NOT NULL DEFAULT '',
    video_id            TEXT NOT NULL,      -- YouTube video ID, embedded via iframe
    duration_seconds    INTEGER NOT NULL DEFAULT 0,
    sort_order          INTEGER NOT NULL DEFAULT 0,
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS enrollments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    course_id       INTEGER NOT NULL,
    enrolled_at     TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (user_id, course_id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS lesson_progress (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    lesson_id       INTEGER NOT NULL,
    watched         INTEGER NOT NULL DEFAULT 0,
    watched_at      TEXT,
    UNIQUE (user_id, lesson_id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (lesson_id) REFERENCES lessons (id) ON DELETE CASCADE
);

-- Notification & Reminder System (roadmap section 12): achievement alerts,
-- course completion notifications, and platform announcements are all
-- rows here. `user_id` is NULL for a broadcast platform announcement
-- (visible to everyone) and set for a personal notification.
CREATE TABLE IF NOT EXISTS notifications (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER,
    type            TEXT NOT NULL CHECK (type IN
                        ('achievement', 'course_completion', 'practice_reminder', 'announcement')),
    title           TEXT NOT NULL,
    message         TEXT NOT NULL,
    is_read         INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS dataset_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_name    TEXT NOT NULL,
    action          TEXT NOT NULL,
    details         TEXT,
    performed_by    INTEGER,
    performed_at    TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (performed_by) REFERENCES users (id)
);

-- Quiz / Knowledge-Check module (roadmap: "Quiz generation" + "Skill
-- evaluation" under the Assessment & Certification Module). Separate from
-- live gesture-practice assessment — these are multiple-choice knowledge
-- questions about ASL vocabulary, grammar, and Deaf culture.
CREATE TABLE IF NOT EXISTS quiz_questions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    level           TEXT NOT NULL CHECK (level IN
                        ('Beginner', 'Intermediate', 'Advanced', 'Professional')),
    topic           TEXT NOT NULL DEFAULT 'General',
    question_text   TEXT NOT NULL,
    option_a        TEXT NOT NULL,
    option_b        TEXT NOT NULL,
    option_c        TEXT NOT NULL,
    option_d        TEXT NOT NULL,
    correct_option  TEXT NOT NULL CHECK (correct_option IN ('a', 'b', 'c', 'd')),
    explanation     TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS quiz_attempts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    level           TEXT NOT NULL,
    score           INTEGER NOT NULL,
    total_questions INTEGER NOT NULL,
    taken_at        TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
