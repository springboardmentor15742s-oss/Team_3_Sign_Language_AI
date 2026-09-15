import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../api";
import Avatar from "../components/Avatar";

const LEVEL_COLOR = {
  Beginner: "level-beginner",
  Intermediate: "level-intermediate",
  Advanced: "level-advanced",
  Professional: "level-professional",
};

const FEATURES = [
  {
    icon: "📚",
    title: "Sign Language Courses",
    desc: "Watch structured video lessons — from the alphabet to workplace ASL — and track every lesson you complete.",
    to: "/courses",
  },
  {
    icon: "🖐️",
    title: "Gesture Practice",
    desc: "Practice signs live with your webcam — real-time hand tracking and instant accuracy scoring.",
    to: "/gesture-practice",
  },
  {
    icon: "📊",
    title: "Performance Dashboard",
    desc: "See your accuracy trend, weak areas, AI feedback, recommendations, and a personalized learning plan.",
    to: "/dashboard",
  },
  {
    icon: "🎓",
    title: "Certifications",
    desc: "Earn Beginner to Professional certificates automatically as your practice results qualify.",
    to: "/certifications",
  },
  {
    icon: "📝",
    title: "Knowledge-Check Quiz",
    desc: "Multiple-choice questions on ASL vocabulary, grammar, and Deaf culture — a knowledge check alongside gesture practice.",
    to: "/quiz",
  },
  {
    icon: "🗂️",
    title: "Reports & Export",
    desc: "Download your learning, accuracy, progress, and certification reports as CSV — anytime.",
    to: "/reports",
  },
  {
    icon: "📚",
    title: "Dataset Explorer",
    desc: "Browse and preview the sign-language datasets that power gesture recognition.",
    to: "/datasets",
  },
  {
    icon: "👤",
    title: "Your Profile",
    desc: "Set your photo, learning level, goals, and preferred sign language.",
    to: "/profile",
  },
];

const STEPS = [
  { icon: "🎥", title: "Practice", desc: "Sign in front of your webcam." },
  { icon: "🧠", title: "Get Feedback", desc: "AI scores your accuracy and explains mistakes." },
  { icon: "📈", title: "Track Progress", desc: "Watch your trend improve, attempt after attempt." },
  { icon: "🏅", title: "Get Certified", desc: "Earn a verifiable certificate once you qualify." },
];

export default function Home() {
  const { user, profile } = useAuth();
  const [stats, setStats] = useState(null);
  const [certCount, setCertCount] = useState(null);
  const [allCourses, setAllCourses] = useState([]);
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    api.listCourses().then(setAllCourses).catch(() => {});
    api.getCourseMeta().then((m) => setCategories(m.categories)).catch(() => {});
  }, []);

  useEffect(() => {
    if (!user) return;
    api.getGestureStats().then(setStats).catch(() => {});
    api.getMyCertificates().then((c) => setCertCount(c.length)).catch(() => {});
  }, [user]);

  const displayName = profile?.display_name || user?.username;
  const featuredCourses = allCourses.slice(0, 4);
  const totalLessons = allCourses.reduce((sum, c) => sum + (c.lesson_count || 0), 0);

  return (
    <div className="page home-page">
      {/* ---------------- Hero ---------------- */}
      <section className="hero">
        <div className="hero-copy">
          <div className="hero-badge">🤟 AI-Powered Sign Language Learning</div>
          <h1 className="hero-title">Learn sign language with real-time AI feedback</h1>
          <p className="hero-subtitle">
            Watch structured video courses, practice with your webcam, get instant accuracy
            scoring, and earn verifiable certifications — all in one platform.
          </p>

          {user ? (
            <div className="hero-cta-row">
              <Link to="/gesture-practice" className="btn-primary btn-large">
                🖐️ Start Practicing
              </Link>
              <Link to="/courses" className="btn-secondary btn-large">
                📚 Browse Courses
              </Link>
            </div>
          ) : (
            <div className="hero-cta-row">
              <Link to="/login" className="btn-primary btn-large">
                🚀 Get Started
              </Link>
              <Link to="/courses" className="btn-secondary btn-large">
                📚 See the Courses
              </Link>
            </div>
          )}
        </div>

        <div className="hero-visual">
          <div className="hero-visual-row">
            <span className="hero-visual-title">Gesture Practice</span>
            <span className="hero-visual-live">
              <span className="hero-visual-dot" /> Live
            </span>
          </div>
          <div className="hero-visual-sign">🤟</div>
          <div className="hero-visual-score-row">
            <div className="hero-visual-score">
              <div className="hero-visual-score-value">94%</div>
              <div className="hero-visual-score-label">Hand shape</div>
            </div>
            <div className="hero-visual-score">
              <div className="hero-visual-score-value">89%</div>
              <div className="hero-visual-score-label">Motion</div>
            </div>
            <div className="hero-visual-score">
              <div className="hero-visual-score-value">91%</div>
              <div className="hero-visual-score-label">Overall</div>
            </div>
          </div>
        </div>
      </section>

      {/* ---------------- Platform stat band (real catalog data) ---------------- */}
      <div className="stat-band">
        <div className="stat-band-item">
          <div className="stat-band-value">{allCourses.length || "—"}</div>
          <div className="stat-band-label">Video courses</div>
        </div>
        <div className="stat-band-item">
          <div className="stat-band-value">{totalLessons || "—"}</div>
          <div className="stat-band-label">Lessons to watch</div>
        </div>
        <div className="stat-band-item">
          <div className="stat-band-value">4</div>
          <div className="stat-band-label">Certification levels</div>
        </div>
        <div className="stat-band-item">
          <div className="stat-band-value">Real-time</div>
          <div className="stat-band-label">AI gesture feedback</div>
        </div>
      </div>

      {/* ---------------- Welcome-back strip (logged in only) ---------------- */}
      {user && (
        <section className="welcome-strip card">
          <div className="welcome-identity">
            <Avatar name={displayName} photo={profile?.avatar_data} size={52} />
            <div>
              <div className="welcome-name">Welcome back, {displayName}!</div>
              <div className="muted small">{user.role} · Keep up the practice streak 🔥</div>
            </div>
          </div>
          <div className="welcome-stats">
            <div className="stat-chip">
              <div className="stat-chip-value">{stats?.total_attempts ?? "—"}</div>
              <div className="stat-chip-label">Attempts</div>
            </div>
            <div className="stat-chip">
              <div className="stat-chip-value">{stats ? `${stats.avg_accuracy}%` : "—"}</div>
              <div className="stat-chip-label">Avg Accuracy</div>
            </div>
            <div className="stat-chip">
              <div className="stat-chip-value">{stats ? `${stats.best_accuracy}%` : "—"}</div>
              <div className="stat-chip-label">Best Accuracy</div>
            </div>
            <div className="stat-chip">
              <div className="stat-chip-value">{certCount ?? "—"}</div>
              <div className="stat-chip-label">Certificates</div>
            </div>
          </div>
        </section>
      )}

      {!user && (
        <div className="alert alert-info">
          👋 You're not logged in yet.{" "}
          <Link to="/login">
            <strong>Login / Register</strong>
          </Link>{" "}
          to start practicing and tracking your progress.
        </div>
      )}

      {/* ---------------- Featured Courses (YouTube-style watch & learn) ---------------- */}
      {featuredCourses.length > 0 && (
        <>
          <div className="section-title-row">
            <h2 className="section-title">📚 Featured Courses</h2>
            <Link to="/courses" className="link-more">
              Browse all courses →
            </Link>
          </div>

          {categories.length > 0 && (
            <div className="category-chip-row">
              {categories.map((cat) => (
                <Link to="/courses" key={cat} className="category-chip">
                  {cat}
                </Link>
              ))}
            </div>
          )}

          <div className="course-grid">
            {featuredCourses.map((c) => (
              <Link to={user ? `/courses/${c.id}` : "/login"} key={c.id} className="course-card">
                <div className="course-thumb">
                  <span>{c.thumbnail_emoji}</span>
                  <span className={`level-badge ${LEVEL_COLOR[c.level] || ""}`}>{c.level}</span>
                </div>
                <div className="course-card-body">
                  <div className="course-category-tag">{c.category}</div>
                  <div className="course-card-title">{c.title}</div>
                  <div className="course-card-meta">🎬 {c.lesson_count} lesson{c.lesson_count === 1 ? "" : "s"}</div>
                </div>
              </Link>
            ))}
          </div>
        </>
      )}

      {/* ---------------- Feature grid ---------------- */}
      <h2 className="section-title">Explore the Platform</h2>
      <div className="feature-grid">
        {FEATURES.map((f) => (
          <Link to={user ? f.to : "/login"} key={f.title} className="feature-card">
            <div className="feature-icon">{f.icon}</div>
            <div className="feature-title">{f.title}</div>
            <div className="feature-desc">{f.desc}</div>
          </Link>
        ))}
        {user?.role === "Administrator" && (
          <Link to="/admin" className="feature-card">
            <div className="feature-icon">🛠️</div>
            <div className="feature-title">Admin Panel</div>
            <div className="feature-desc">Manage registered users, roles, and platform-wide access.</div>
          </Link>
        )}
      </div>

      {/* ---------------- How it works ---------------- */}
      <h2 className="section-title">How It Works</h2>
      <div className="steps-row">
        {STEPS.map((s, i) => (
          <div className="step" key={s.title}>
            <div className="step-number">{i + 1}</div>
            <div className="step-icon">{s.icon}</div>
            <div className="step-title">{s.title}</div>
            <div className="step-desc">{s.desc}</div>
          </div>
        ))}
      </div>

      {/* ---------------- Who it's for ---------------- */}
      <div className="card who-for-card">
        <h3>👥 Built for</h3>
        <div className="who-for-tags">
          <span className="tag">Students</span>
          <span className="tag">Hearing-impaired individuals</span>
          <span className="tag">Educators</span>
          <span className="tag">Language trainers</span>
          <span className="tag">Schools</span>
          <span className="tag">Accessibility organizations</span>
        </div>
      </div>
    </div>
  );
}
