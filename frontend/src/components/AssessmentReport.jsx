import { useState } from "react";
import { api } from "../api";

const LEVEL_CLASS = {
  "Needs Improvement": "level-pill level-weak",
  "Developing": "level-pill level-developing",
  "Good": "level-pill level-good",
};

export default function AssessmentReport() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState("");

  async function handleGenerate() {
    setLoading(true);
    setError("");
    try {
      const data = await api.getAssessmentReport();
      setReport(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDownload() {
    setDownloading(true);
    setError("");
    try {
      await api.downloadAssessmentReport();
    } catch (err) {
      setError(err.message);
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div>
      <div className="report-actions">
        <button className="btn-primary" onClick={handleGenerate} disabled={loading}>
          {loading ? "Generating…" : report ? "🔄 Regenerate Report" : "📄 Generate Assessment Report"}
        </button>
        {report && (
          <button className="btn-secondary" onClick={handleDownload} disabled={downloading}>
            {downloading ? "Preparing…" : "⬇️ Download as text"}
          </button>
        )}
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {!report && !loading && (
        <p className="muted small">
          Generate a snapshot report combining your accuracy analytics, AI feedback, recommendations,
          and today's learning plan — for yourself or to share with an instructor.
        </p>
      )}

      {report && (
        <div className="report-body">
          <div className="report-meta muted small">
            <span>Report ID: {report.report_id}</span>
            <span>Generated: {new Date(report.generated_at).toLocaleString()}</span>
            <span>
              Learner: {report.learner.username} · {report.learner.learning_level}
            </span>
          </div>

          <div className="kpi-row">
            <div className="kpi-card">
              <div className="kpi-value">{report.overview.total_attempts}</div>
              <div className="kpi-label">Total Attempts</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-value">{report.overview.overall_accuracy}%</div>
              <div className="kpi-label">Overall Accuracy</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-value">{report.overview.best_accuracy}%</div>
              <div className="kpi-label">Best Accuracy</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-value">{report.overview.match_rate}%</div>
              <div className="kpi-label">Match Rate</div>
            </div>
          </div>

          {report.gesture_breakdown.length > 0 && (
            <table className="table">
              <thead>
                <tr>
                  <th>Gesture</th>
                  <th>Avg Accuracy</th>
                  <th>Attempts</th>
                  <th>Level</th>
                </tr>
              </thead>
              <tbody>
                {report.gesture_breakdown.map((g) => (
                  <tr key={g.gesture}>
                    <td>{g.display_name}</td>
                    <td>{g.avg_accuracy}%</td>
                    <td>{g.attempts}</td>
                    <td>
                      <span className={LEVEL_CLASS[g.level] || "level-pill"}>{g.level}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <p className="report-feedback">🧠 {report.feedback_summary}</p>

          {report.recommendations.length > 0 && (
            <>
              <h4>Recommendations</h4>
              <ul>
                {report.recommendations.map((r) => (
                  <li key={r.gesture}>
                    <strong>{r.display_name}</strong> — practice {r.practice_count}x.{" "}
                    <span className="muted small">{r.reason}</span>
                  </li>
                ))}
              </ul>
            </>
          )}

          {report.learning_plan?.items?.length > 0 && (
            <>
              <h4>Today's Plan</h4>
              <p className="muted small">{report.learning_plan.headline}</p>
            </>
          )}
        </div>
      )}
    </div>
  );
}
