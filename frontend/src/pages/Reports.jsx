import { useEffect, useState } from "react";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import AssessmentReport from "../components/AssessmentReport";

const TABS = [
  { id: "assessment", label: "📄 Assessment Report" },
  { id: "learning", label: "📚 Learning Report" },
  { id: "accuracy", label: "🎯 Accuracy Report" },
  { id: "progress", label: "📈 Progress Report" },
  { id: "certification", label: "🎓 Certification Report" },
];

export default function Reports() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("assessment");
  const [learningReport, setLearningReport] = useState(null);
  const [classOverview, setClassOverview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const isStaff = user && ["Instructor", "Administrator", "Accessibility Trainer"].includes(user.role);
  const tabs = isStaff ? [...TABS, { id: "class", label: "🏫 Class Overview" }] : TABS;

  useEffect(() => {
    if (activeTab === "learning" && !learningReport) {
      setLoading(true);
      api
        .getLearningReport()
        .then(setLearningReport)
        .catch((err) => setError(err.message))
        .finally(() => setLoading(false));
    }
    if (activeTab === "class" && !classOverview) {
      setLoading(true);
      api
        .getClassOverview()
        .then(setClassOverview)
        .catch((err) => setError(err.message))
        .finally(() => setLoading(false));
    }
  }, [activeTab]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="page">
      <h1>🗂️ Reports & Export System</h1>
      <p className="muted">
        Every report below is generated live from your logged practice attempts and can be exported
        as CSV (opens directly in Excel/Sheets).
      </p>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="report-tabs">
        {tabs.map((t) => (
          <button
            key={t.id}
            className={`report-tab ${activeTab === t.id ? "active" : ""}`}
            onClick={() => setActiveTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {activeTab === "assessment" && (
        <div className="card">
          <h3>Assessment Report</h3>
          <p className="muted small">
            Combined analytics, AI feedback, recommendations, and learning plan snapshot.
          </p>
          <AssessmentReport />
        </div>
      )}

      {activeTab === "learning" && (
        <div className="card">
          <h3>Learning Report</h3>
          <div className="report-actions">
            <button className="btn-secondary" onClick={() => api.downloadAccuracyCsv(user.username)}>
              ⬇️ Download Accuracy CSV
            </button>
            <button className="btn-primary" onClick={() => api.downloadLearningPdf(user.username)}>
              ⬇️ Download PDF
            </button>
          </div>
          {loading && <p className="muted">Loading…</p>}
          {learningReport && (
            <>
              <div className="kpi-row">
                <div className="kpi-card">
                  <div className="kpi-value">{learningReport.total_attempts}</div>
                  <div className="kpi-label">Total Attempts</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-value">{learningReport.overall_accuracy}%</div>
                  <div className="kpi-label">Overall Accuracy</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-value">{learningReport.gestures_practiced}</div>
                  <div className="kpi-label">Gestures Practiced</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-value">{learningReport.strong_area_count}</div>
                  <div className="kpi-label">Strong Areas</div>
                </div>
              </div>
              {learningReport.trend && (
                <p className="trend-summary">
                  Trend: {learningReport.trend.direction} ({learningReport.trend.slope_per_attempt} pts/attempt)
                </p>
              )}
            </>
          )}
        </div>
      )}

      {activeTab === "accuracy" && (
        <div className="card">
          <h3>Accuracy Report</h3>
          <p className="muted small">Per-gesture accuracy, best/worst runs, and skill level.</p>
          <div className="report-actions">
            <button className="btn-secondary" onClick={() => api.downloadAccuracyCsv(user.username)}>
              ⬇️ Download CSV
            </button>
            <button className="btn-primary" onClick={() => api.downloadAccuracyPdf(user.username)}>
              ⬇️ Download PDF
            </button>
          </div>
        </div>
      )}

      {activeTab === "progress" && (
        <div className="card">
          <h3>Progress Report</h3>
          <p className="muted small">Every attempt in chronological order — accuracy changing over time.</p>
          <div className="report-actions">
            <button className="btn-secondary" onClick={() => api.downloadProgressCsv(user.username)}>
              ⬇️ Download CSV
            </button>
            <button className="btn-primary" onClick={() => api.downloadProgressPdf(user.username)}>
              ⬇️ Download PDF
            </button>
          </div>
        </div>
      )}

      {activeTab === "certification" && (
        <div className="card">
          <h3>Certification Report</h3>
          <p className="muted small">All certificates you've earned, with codes and status.</p>
          <div className="report-actions">
            <button className="btn-secondary" onClick={() => api.downloadCertificationCsv(user.username)}>
              ⬇️ Download CSV
            </button>
            <button className="btn-primary" onClick={() => api.downloadCertificationPdf(user.username)}>
              ⬇️ Download PDF
            </button>
          </div>
        </div>
      )}

      {activeTab === "class" && isStaff && (
        <div className="card">
          <h3>Class Overview</h3>
          <p className="muted small">One row per learner — accuracy, attempts, and level.</p>
          <div className="report-actions">
            <button className="btn-secondary" onClick={() => api.downloadClassOverviewCsv()}>
              ⬇️ Download CSV
            </button>
            <button className="btn-primary" onClick={() => api.downloadClassOverviewPdf()}>
              ⬇️ Download PDF
            </button>
          </div>
          {loading && <p className="muted">Loading…</p>}
          {classOverview && classOverview.length > 0 && (
            <table className="table">
              <thead>
                <tr>
                  <th>Learner</th>
                  <th>Level</th>
                  <th>Attempts</th>
                  <th>Accuracy</th>
                </tr>
              </thead>
              <tbody>
                {classOverview.map((l) => (
                  <tr key={l.user_id}>
                    <td>{l.username}</td>
                    <td>{l.learning_level}</td>
                    <td>{l.total_attempts}</td>
                    <td>{l.overall_accuracy}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {classOverview && classOverview.length === 0 && (
            <p className="muted small">No learners registered yet.</p>
          )}
        </div>
      )}
    </div>
  );
}
