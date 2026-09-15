import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../api";

function formatDuration(seconds) {
  if (!seconds) return "";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

export default function CourseWatch() {
  const { courseId, lessonId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const canManage = user && ["Instructor", "Accessibility Trainer", "Administrator"].includes(user.role);

  const [course, setCourse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [marking, setMarking] = useState(false);
  const [showAddLesson, setShowAddLesson] = useState(false);
  const [lessonForm, setLessonForm] = useState({ title: "", description: "", video_id: "", duration_seconds: 300 });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadCourse();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [courseId]);

  async function loadCourse() {
    setLoading(true);
    try {
      const c = await api.getCourse(courseId);
      setCourse(c);
      if (!c.is_enrolled) {
        api.enrollInCourse(courseId).catch(() => {});
      }
      if (!lessonId && c.lessons.length > 0) {
        navigate(`/courses/${courseId}/lesson/${c.lessons[0].id}`, { replace: true });
      }
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div className="page-center">Loading course…</div>;
  if (!course) return <div className="page-center">Course not found.</div>;

  const activeLesson = course.lessons.find((l) => String(l.id) === String(lessonId)) || course.lessons[0];
  const activeIndex = course.lessons.findIndex((l) => l.id === activeLesson?.id);
  const nextLesson = course.lessons[activeIndex + 1];

  async function handleMarkWatched() {
    if (!activeLesson) return;
    setMarking(true);
    try {
      await api.markLessonWatched(activeLesson.id);
      const refreshed = await api.getCourse(courseId);
      setCourse(refreshed);
      if (nextLesson) {
        navigate(`/courses/${courseId}/lesson/${nextLesson.id}`);
      }
    } finally {
      setMarking(false);
    }
  }

  async function handleAddLesson(e) {
    e.preventDefault();
    setError("");
    if (!lessonForm.title || !lessonForm.video_id) {
      setError("Title and YouTube video ID are required.");
      return;
    }
    setSaving(true);
    try {
      await api.addLesson(courseId, lessonForm);
      setLessonForm({ title: "", description: "", video_id: "", duration_seconds: 300 });
      setShowAddLesson(false);
      const refreshed = await api.getCourse(courseId);
      setCourse(refreshed);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="page watch-page">
      <div className="watch-breadcrumb">
        <Link to="/courses">← All Courses</Link>
      </div>

      <div className="watch-layout">
        <div className="watch-main">
          {activeLesson ? (
            <>
              <div className="video-frame">
                <iframe
                  key={activeLesson.id}
                  src={`https://www.youtube.com/embed/${activeLesson.video_id}?rel=0`}
                  title={activeLesson.title}
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                />
              </div>
              <h2 className="watch-title">{activeLesson.title}</h2>
              <p className="muted">{activeLesson.description}</p>
              <div className="watch-actions">
                <button className="btn-primary" onClick={handleMarkWatched} disabled={marking || activeLesson.watched}>
                  {activeLesson.watched ? "✅ Watched" : marking ? "Saving…" : "Mark as Watched"}
                </button>
                {nextLesson && (
                  <Link to={`/courses/${courseId}/lesson/${nextLesson.id}`} className="btn-secondary">
                    Next Lesson →
                  </Link>
                )}
              </div>
            </>
          ) : (
            <div className="alert alert-info">This course has no lessons yet.</div>
          )}
        </div>

        <aside className="watch-sidebar">
          <div className="course-progress-block">
            <div className="course-progress-header">
              <span>{course.title}</span>
              <span className="muted small">
                {course.watched_lessons}/{course.lesson_count} watched
              </span>
            </div>
            <div className="progress-bar-track">
              <div className="progress-bar-fill" style={{ width: `${course.progress_percent}%` }} />
            </div>
          </div>

          {canManage && (
            <div className="card">
              <button className="btn-secondary" onClick={() => setShowAddLesson((v) => !v)}>
                {showAddLesson ? "Cancel" : "+ Add Lesson"}
              </button>
              {showAddLesson && (
                <form className="lesson-form" onSubmit={handleAddLesson}>
                  {error && <div className="alert alert-error">{error}</div>}
                  <label>
                    Title
                    <input
                      value={lessonForm.title}
                      onChange={(e) => setLessonForm({ ...lessonForm, title: e.target.value })}
                    />
                  </label>
                  <label>
                    Description
                    <textarea
                      rows={2}
                      value={lessonForm.description}
                      onChange={(e) => setLessonForm({ ...lessonForm, description: e.target.value })}
                    />
                  </label>
                  <label>
                    YouTube video ID
                    <input
                      value={lessonForm.video_id}
                      placeholder="e.g. dQw4w9WgXcQ"
                      onChange={(e) => setLessonForm({ ...lessonForm, video_id: e.target.value })}
                    />
                  </label>
                  <label>
                    Duration (seconds)
                    <input
                      type="number"
                      min={0}
                      value={lessonForm.duration_seconds}
                      onChange={(e) =>
                        setLessonForm({ ...lessonForm, duration_seconds: Number(e.target.value) })
                      }
                    />
                  </label>
                  <button className="btn-primary" type="submit" disabled={saving}>
                    {saving ? "Adding…" : "Add Lesson"}
                  </button>
                </form>
              )}
            </div>
          )}

          <ul className="lesson-playlist">
            {course.lessons.map((l, i) => (
              <li key={l.id}>
                <Link
                  to={`/courses/${courseId}/lesson/${l.id}`}
                  className={`lesson-item ${l.id === activeLesson?.id ? "active" : ""}`}
                >
                  <span className="lesson-index">{l.watched ? "✅" : i + 1}</span>
                  <span className="lesson-item-body">
                    <span className="lesson-item-title">{l.title}</span>
                    <span className="lesson-item-duration">{formatDuration(l.duration_seconds)}</span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </aside>
      </div>
    </div>
  );
}
