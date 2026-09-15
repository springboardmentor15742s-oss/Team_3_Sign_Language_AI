import LineChart from "./LineChart";

const DIRECTION_LABEL = {
  improving: "📈 Improving",
  declining: "📉 Declining",
  steady: "➡️ Steady",
};

export default function PerformanceTrend({ trendData }) {
  if (!trendData?.has_data) {
    return (
      <p className="muted small">
        No gesture attempts logged yet — your accuracy-over-time trend unlocks after you practice.
      </p>
    );
  }

  const { points, trend } = trendData;

  return (
    <>
      <LineChart points={points} />
      {trend ? (
        <p className="trend-summary">
          {DIRECTION_LABEL[trend.direction] || trend.direction} —{" "}
          <span className="muted small">
            {trend.slope_per_attempt > 0 ? "+" : ""}
            {trend.slope_per_attempt} pts/attempt, predicted next attempt ≈ {trend.predicted_next_accuracy}%
            (based on last {trend.attempts_used} attempts)
          </span>
        </p>
      ) : (
        <p className="muted small">
          Practice a few more times ({3 - points.length > 0 ? 3 - points.length : 0} more attempts) to
          unlock a trend forecast.
        </p>
      )}
    </>
  );
}
