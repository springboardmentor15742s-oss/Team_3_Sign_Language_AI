const TREND_ICON = {
  improving: "📈",
  declining: "📉",
  steady: "➖",
};

export default function Recommendations({ recommendations }) {
  if (!recommendations || recommendations.length === 0) {
    return (
      <p className="muted small">
        Complete a few practice attempts to unlock personalized recommendations.
      </p>
    );
  }

  return (
    <ul className="recommendation-list">
      {recommendations.map((r) => (
        <li key={r.gesture} className="recommendation-item">
          <div className="recommendation-head">
            <strong>{r.display_name}</strong>
            <span className="chip">
              Practice {r.practice_count}×
            </span>
          </div>
          <p className="muted small">{r.reason}</p>
          {r.trend && (
            <p className="muted small trend-line">
              {TREND_ICON[r.trend.direction] || ""} {r.trend.direction} — predicted next attempt ≈{" "}
              {r.trend.predicted_next_accuracy}%
            </p>
          )}
        </li>
      ))}
    </ul>
  );
}
