import { useEffect, useState } from "react";
import { api } from "../api";
import BarChart from "../components/BarChart";
import LearningInsights from "../components/LearningInsights";
import WeakAreas from "../components/WeakAreas";
import Recommendations from "../components/Recommendations";
import LearningPlan from "../components/LearningPlan";
import AssessmentReport from "../components/AssessmentReport";
import PerformanceTrend from "../components/PerformanceTrend";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [intelligence, setIntelligence] = useState(null);
  const [score, setScore] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      // Milestone 1/2 KPIs + Milestone 3 AI Feedback & Learning Intelligence,
      // fetched in parallel so one slow call doesn't block the other.
      const [dashboardData, intelligenceData, scoreData] = await Promise.all([
        api.getDashboard(),
        api.getIntelligenceSummary(),
        api.getPerformanceScore(),
      ]);
      setData(dashboardData);
      setIntelligence(intelligenceData);
      setScore(scoreData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleLogActivity() {
    await api.logActivity();
    load();
  }

  if (loading) return <div className="page">Loading dashboard...</div>;
  if (error) return <div className="page alert alert-error">{error}</div>;

  const gestureStats = data.gesture_stats;
  const gestureChartData = (gestureStats?.by_gesture || []).map((g) => ({
    label: g.display_name,
    count: g.avg_accuracy,
  }));

  const analytics = intelligence?.analytics;
  const feedback = intelligence?.feedback;
  const recommendations = intelligence?.recommendations;
  const learningPlan = intelligence?.learning_plan;
  const performanceTrend = intelligence?.performance_trend;

  return (
    <div className="page">
      <h1>📊 Learner Performance Dashboard</h1>
      <p className="muted">Here's your learning snapshot.</p>

      <div className="kpi-row">
        <div className="kpi-card">
          <div className="kpi-value">{data.learning_level || "Not set"}</div>
          <div className="kpi-label">Learning Level</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">{data.preferred_language ? data.preferred_language.split(" ")[0] : "Not set"}</div>
          <div className="kpi-label">Preferred Language</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">{data.goals.length}</div>
          <div className="kpi-label">Learning Goals Set</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">{data.logged_activities_count}</div>
          <div className="kpi-label">Logged Activities</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">{gestureStats?.total_attempts ?? 0}</div>
          <div className="kpi-label">Gesture Attempts</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">{gestureStats?.avg_accuracy ?? 0}%</div>
          <div className="kpi-label">Avg Gesture Accuracy</div>
        </div>
      </div>

      {!data.has_profile && (
        <div className="alert alert-info">
          You haven't set up your learner profile yet. Go to <strong>Learner Profile</strong> to
          get started.
        </div>
      )}

      {score && (
        <div className="card">
          <h3>🏆 Learning Performance Score</h3>
          <div className="score-headline">
            <div className="score-headline-value">{score.learning_performance_score}</div>
            <div className="score-headline-sub">
              out of 100 — Gesture Accuracy 40% + Assessment Performance 25% + Lesson Completion
              15% + Practice Consistency 10% + Skill Improvement Rate 10%
            </div>
          </div>
          <div className="score-breakdown">
            {score.components.map((c) => (
              <div className="score-row" key={c.key}>
                <div className="score-row-label">
                  {c.label} <span className="muted small">({c.weight_percent}%)</span>
                </div>
                <div className="score-row-bar">
                  <div className="score-row-bar-fill" style={{ width: `${c.value}%` }} />
                </div>
                <div className="score-row-value">{c.value}</div>
              </div>
            ))}
          </div>
          {!score.has_data && (
            <p className="muted small">
              Start practicing on <strong>Gesture Practice</strong> to bring this score to life.
            </p>
          )}
        </div>
      )}

      <hr />

      <div className="grid-2-1">
        <div>
          <div className="card">
            <h3>📈 Learning Progress — Avg Accuracy by Gesture</h3>
            {gestureChartData.length > 0 ? (
              <BarChart data={gestureChartData} />
            ) : (
              <p className="muted small">
                No gesture practice logged yet. Head to <strong>Gesture Practice</strong> to try the
                Milestone 2 Gesture Recognition & Accuracy Assessment engines.
              </p>
            )}
          </div>

          <div className="card">
            <h3>📉 Performance Trend — Accuracy Over Time</h3>
            <PerformanceTrend trendData={performanceTrend} />
          </div>

          <div className="section-divider">
            <h2>🧠 AI Feedback &amp; Learning Intelligence</h2>
            <p className="muted small">
              Powered by your logged practice attempts — analytics, feedback, recommendations, and
              your learning plan all update automatically as you practice.
            </p>
          </div>

          <div className="card">
            <h3>🧠 AI Feedback & Learning Insights</h3>
            <LearningInsights analytics={analytics} feedback={feedback} />
          </div>

          <div className="card">
            <h3>⚠️ Weak Areas</h3>
            <WeakAreas analytics={analytics} />
          </div>

          <div className="card">
            <h3>📄 Assessment Report</h3>
            <AssessmentReport />
          </div>

          <div className="card">
            <h3>🕘 Recent Activity Log</h3>
            {data.recent_activity.length > 0 ? (
              <table className="table">
                <thead>
                  <tr>
                    <th>Activity</th>
                    <th>Logged At</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent_activity.map((a) => (
                    <tr key={a.id}>
                      <td>{a.activity}</td>
                      <td>{a.logged_at}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <>
                <p>No activity logged yet.</p>
                <button className="btn-secondary" onClick={handleLogActivity}>
                  ➕ Log a sample practice activity (demo)
                </button>
              </>
            )}
          </div>
        </div>

        <div>
          <div className="card">
            <h3>🎯 Learning Goals</h3>
            {data.goals.length > 0 ? (
              <ul className="checklist">
                {data.goals.map((g) => (
                  <li key={g}>
                    <input type="checkbox" disabled /> {g}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="muted">No goals set yet.</p>
            )}
          </div>

          <div className="card">
            <h3>🎯 Recommended Practice</h3>
            <Recommendations recommendations={recommendations} />
          </div>

          <div className="card">
            <h3>🗓️ Today's Learning Plan</h3>
            <LearningPlan plan={learningPlan} />
          </div>
        </div>
      </div>
    </div>
  );
}
