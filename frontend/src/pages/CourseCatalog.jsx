import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../api";

const LEVEL_COLOR = {
  Beginner: "level-beginner",
  Intermediate: "level-intermediate",
  Advanced: "level-advanced",
  Professional: "level-professional",
};

export default function CourseCatalog() {
  const { user } = useAuth();
  const canManage = user && ["Instructor", "Accessibility Trainer", "Administrator"].includes(user.role);

  const [meta, setMeta] = useState({ categories: [], levels: [] });
  const [courses, setCourses] = useState([]);
  const [category, setCategory] = useState("");
  const [level, setLevel] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [showNewCourse, setShowNewCourse] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    title: "",
    description: "",
    category: "",
    level: "",
    thumbnail_emoji: "🤟",
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.getCourseMeta().then(setMeta).catch(() => {});
  }, []);

  useEffect(() => {
    loadCourses();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [category, level]);

  function loadCourses() {
    setLoading(true);
    api
      .listCourses({ category: category || undefined, level: level || undefined, search: search || undefined })
      .then(setCourses)
      .finally(() => setLoading(false));
  }

  function handleSearchSubmit(e) {
    e.preventDefault();
    loadCourses();
  }

  async function handleCreateCourse(e) {
    e.preventDefault();
    setError("");
    if (!form.title || !form.category || !form.level) {
      setError("Title, category, and level are required.");
      return;
    }
    setSaving(true);
    try {
      await api.createCourse(form);
      setForm({ title: "", description: "", category: "", level: "", thumbnail_emoji: "🤟" });
      setShowNewCourse(false);
      loadCourses();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="page">
      <div className="courses-header">
        <div>
          <h1>📚 Sign Language Courses</h1>
          <p className="muted">
            Watch structured video lessons, track your progress, and move from Beginner to
            Professional-level sign language.
          </p>
        </div>
        {canManage && (
          <button className="btn-primary" onClick={() => setShowNewCourse((v) => !v)}>
            {showNewCourse ? "Cancel" : "+ New Course"}
          </button>
        )}
      </div>

      {showNewCourse && (
        <form className="card course-form" onSubmit={handleCreateCourse}>
          <h3>Create a new course</h3>
          {error && <div className="alert alert-error">{error}</div>}
          <div className="grid-2">
            <label>
              Title
              <input
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                placeholder="e.g. Restaurant & Food Vocabulary"
              />
            </label>
            <label>
              Thumbnail emoji
              <input
                value={form.thumbnail_emoji}
                maxLength={2}
                onChange={(e) => setForm({ ...form, thumbnail_emoji: e.target.value })}
              />
            </label>
          </div>
          <label>
            Description
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={2}
            />
          </label>
          <div className="grid-2">
            <label>
              Category
              <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
                <option value="">Select category…</option>
                {meta.categories.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Level
              <select value={form.level} onChange={(e) => setForm({ ...form, level: e.target.value })}>
                <option value="">Select level…</option>
                {meta.levels.map((l) => (
                  <option key={l} value={l}>
                    {l}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <button className="btn-primary" type="submit" disabled={saving}>
            {saving ? "Creating…" : "Create Course"}
          </button>
        </form>
      )}

      <form className="course-filters" onSubmit={handleSearchSubmit}>
        <input
          className="course-search-input"
          placeholder="Search courses…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="">All categories</option>
          {meta.categories.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <select value={level} onChange={(e) => setLevel(e.target.value)}>
          <option value="">All levels</option>
          {meta.levels.map((l) => (
            <option key={l} value={l}>
              {l}
            </option>
          ))}
        </select>
        <button className="btn-secondary" type="submit">
          Search
        </button>
      </form>

      {loading ? (
        <div className="page-center">Loading courses…</div>
      ) : courses.length === 0 ? (
        <div className="alert alert-info">No courses match your filters yet.</div>
      ) : (
        <div className="course-grid">
          {courses.map((c) => (
            <Link to={`/courses/${c.id}`} key={c.id} className="course-card">
              <div className="course-thumb">
                <span>{c.thumbnail_emoji}</span>
                <span className={`level-badge ${LEVEL_COLOR[c.level] || ""}`}>{c.level}</span>
              </div>
              <div className="course-card-body">
                <div className="course-category-tag">{c.category}</div>
                <div className="course-card-title">{c.title}</div>
                <div className="course-card-desc">{c.description}</div>
                <div className="course-card-meta">🎬 {c.lesson_count} lesson{c.lesson_count === 1 ? "" : "s"}</div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
