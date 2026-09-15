export default function LearningInsights({ analytics, feedback }) {
  if (!analytics?.has_data) {
    return (
      <p className="muted small">
        No practice attempts yet — head to <strong>Gesture Practice</strong> to generate your first
        AI feedback.
      </p>
    );
  }

  return (
    <>
      <div className="kpi-row kpi-row-compact">
        <div className="kpi-card">
          <div className="kpi-value">{analytics.overall_accuracy}%</div>
          <div className="kpi-label">Overall Accuracy</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">{analytics.total_attempts}</div>
          <div className="kpi-label">Total Attempts</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">{analytics.best_accuracy}%</div>
          <div className="kpi-label">Best Accuracy</div>
        </div>
      </div>

      {feedback?.messages?.length > 0 && (
        <ul className="feedback-list">
          {feedback.messages.map((m, i) => (
            <li key={i}>{m}</li>
          ))}
        </ul>
      )}
    </>
  );
}
